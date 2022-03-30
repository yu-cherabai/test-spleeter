import os
import math
import shutil

import requests
from google.cloud import storage
from spleeter.separator import Separator
from pydub import AudioSegment

from enum import Enum

from celery import Celery
from celery.signals import worker_init
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")

storage_client = storage.Client()
separator = Separator('spleeter:2stems')

input_files_path = '/tmp/input_files'
output_files_path = '/tmp/separation_results'
if not os.path.exists(input_files_path):
    os.mkdir(input_files_path)
if not os.path.exists(output_files_path):
    os.mkdir(output_files_path)


class CodecsIn(Enum):
    aac = 'aac'
    ogg = 'ogg'
    wav = 'wav'
    flac = 'flac'
    mp3 = 'mp3'
    webm = 'webm'


class CodecsOut(Enum):
    wav = 'wav'
    mp3 = 'mp3'


class SeparateRequest(BaseModel):
    path: str
    id: str
    outputSoundFormat: CodecsOut
    inputSoundFormat: CodecsIn


class SeparateResponse(BaseModel):
    path: str
    id: str
    outputFolderPath: str


@app.post("/separate", response_model=SeparateResponse)
async def separate(request: SeparateRequest):
    try:
        path_parts = request.path[5:].split('/', 1)
        bucket_name = path_parts[0]
        path_to_file = path_parts[1]
        file_ext = path_to_file.split('.', 1)[1]
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid path.')
    if request.inputSoundFormat.value != file_ext:
        raise HTTPException(status_code=400, detail='Invalid input sound format.')

    process.delay(request.id, request.outputSoundFormat.value, bucket_name, path_to_file, file_ext)

    return {
        "path": request.path,
        "id": request.id,
        "outputFolderPath": f"gs://{bucket_name}/results/{request.id}"
    }


@celery.task(
    acks_late=True
)
def process(request_id, output_sound_format, bucket_name, path_to_file, file_ext):
    bucket = storage_client.get_bucket(bucket_name)
    file = bucket.get_blob(path_to_file)
    request_input_path = f"{input_files_path}/{request_id}"
    request_output_path = f"{output_files_path}/{request_id}"
    if os.path.exists(request_input_path):
        shutil.rmtree(request_input_path)
    os.mkdir(request_input_path)
    if os.path.exists(request_output_path):
        shutil.rmtree(request_output_path)
    os.mkdir(request_output_path)
    with open(f"{request_input_path}/{request_id}.{file_ext}", "wb+") as file_in:
        file.download_to_file(file_in)

    song = AudioSegment.from_file(f"{request_input_path}/{request_id}.{file_ext}", file_ext)

    if 'SPLITTING_FREQUENCY' in os.environ:
        splitting_frequency = int(os.getenv('SPLITTING_FREQUENCY'))
    else:
        splitting_frequency = 10

    segments_count = math.ceil(song.duration_seconds / (splitting_frequency * 60))
    for i in range(segments_count):
        m1 = i * splitting_frequency * 60000
        m2 = (i + 1) * splitting_frequency * 60000
        segment = song[m1:m2]
        segment_path = f"{request_input_path}/{request_id}-segment{i}.mp3"
        segment.export(segment_path, format='mp3')
        separator.separate_to_file(segment_path, request_output_path, codec=output_sound_format, duration=splitting_frequency*60)

    speech_start_segment = AudioSegment.from_file(f"{request_output_path}/{request_id}-segment0/vocals.{output_sound_format}", output_sound_format)
    background_start_segment = AudioSegment.from_file(f"{request_output_path}/{request_id}-segment0/accompaniment.{output_sound_format}", output_sound_format)
    if segments_count > 1:
        for i in range(segments_count):
            speech_result = speech_start_segment + AudioSegment.from_file(
                f"{request_output_path}/{request_id}-segment{i}/vocals.{output_sound_format}", output_sound_format)
            background_result = background_start_segment + AudioSegment.from_file(
                f"{request_output_path}/{request_id}-segment{i}/accompaniment.{output_sound_format}", output_sound_format)
            speech_start_segment = speech_result
            background_start_segment = background_result
    else:
        speech_result = speech_start_segment
        background_result = background_start_segment
    speech_result.export(f"{request_output_path}/speech.{output_sound_format}", format=output_sound_format)
    background_result.export(f"{request_output_path}/background.{output_sound_format}", format=output_sound_format)

    vocal_blob = bucket.blob(f"results/{request_id}/speech.{output_sound_format}")
    vocal_blob.upload_from_filename(f"{request_output_path}/speech.{output_sound_format}")
    accompaniment_blob = bucket.blob(f"results/{request_id}/background.{output_sound_format}")
    accompaniment_blob.upload_from_filename(f"{request_output_path}/background.{output_sound_format}")
    if 'WEBHOOK_HOST' in os.environ:
        requests.post(f"{os.getenv('WEBHOOK_HOST')}/api/v1/orders/{request_id}/audio_split_finished")

    shutil.rmtree(f"{request_input_path}")
    shutil.rmtree(f"{request_output_path}")


def restore_all_unacknowledged_messages():
    conn = celery.connection(transport_options={'visibility_timeout': 0})
    qos = conn.channel().qos
    qos.restore_visible()


@worker_init.connect
def worker_init(sender=None, conf=None, **kwargs):
    restore_all_unacknowledged_messages()
