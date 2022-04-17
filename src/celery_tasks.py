import logging

import requests

from celery import Celery
from celery.signals import worker_init
from pydantic import parse_raw_as

from src import celeryconfig
from src.constants import FOLDER_PROCESSING, WEBHOOK_HOST
from src.gcp import download_file, upload_file
from src.models import SeparateRequest
from src.separator import separate_by_chunks
from src.utils import create_request_folder, delete_request_folder


def get_celery() -> Celery:
    celery_app = Celery()
    celery_app.config_from_object(celeryconfig)
    return celery_app


celery = get_celery()


@celery.task(
    autoretry_for=(Exception,),
    default_retry_delay=5,
    acks_late=True,
    max_retries=5
)
def process(request_json: str):
    request: SeparateRequest = parse_raw_as(SeparateRequest, request_json)
    request_folder = f'{FOLDER_PROCESSING}/{request.id}'
    downloaded_file_path = f'{request_folder}/{request.id}.{request.input_sound_format.value}'

    create_request_folder(request_folder)
    logging.info('Start downloading a file from the bucket.')
    download_file(request.path, downloaded_file_path)
    logging.info('File downloaded from the bucket.')

    separate_by_chunks(
        downloaded_file_path, request.id, request_folder, request.input_sound_format.value, request.output_sound_format.value)

    logging.info('Start uploading results of separation.')
    upload_file(
        f'{request_folder}/speach.{request.output_sound_format.value}',
        f'results/{request.id}/speach.{request.output_sound_format.value}')
    upload_file(
        f'{request_folder}/background.{request.output_sound_format.value}',
        f'results/{request.id}/background.{request.output_sound_format.value}'
    )
    logging.info('Results uploaded.')

    send_notification(request.id)

    delete_request_folder(request_folder)


def send_notification(request_id):
    if WEBHOOK_HOST:
        logging.info('Send notification of successful file separation.')
        requests.post(f'{WEBHOOK_HOST}/api/v1/orders/{request_id}/audio_split_finished')


def restore_all_unacknowledged_messages():
    conn = celery.connection(transport_options={'visibility_timeout': 0})
    qos = conn.channel().qos
    qos.restore_visible()


@worker_init.connect
def worker_init(sender=None, conf=None, **kwargs):
    restore_all_unacknowledged_messages()
