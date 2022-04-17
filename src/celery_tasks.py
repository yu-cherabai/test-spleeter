from celery import Celery
from celery.signals import worker_init
from pydantic import parse_raw_as

from src.models import SeparateRequest
from src import celeryconfig


def get_celery() -> Celery:
    celery_app = Celery()
    celery_app.config_from_object(celeryconfig)
    return celery_app


celery = get_celery()


@celery.task(
    acks_late=True,
    max_retries=5
)
def process(request_json: str):
    request: SeparateRequest = parse_raw_as(SeparateRequest, request_json)
    print('START')
    raise Exception
    print('END')


def restore_all_unacknowledged_messages():
    conn = celery.connection(transport_options={'visibility_timeout': 0})
    qos = conn.channel().qos
    qos.restore_visible()


@worker_init.connect
def worker_init(sender=None, conf=None, **kwargs):
    restore_all_unacknowledged_messages()
