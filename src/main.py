import os
import math
import shutil

import requests
from google.cloud import storage
from spleeter.separator import Separator
from pydub import AudioSegment

from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel


app = FastAPI()

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
async def separate(request: SeparateRequest, background_tasks: BackgroundTasks):
    try:
        path_parts = request.path[5:].split('/', 1)
        bucket_name = path_parts[0]
        path_to_file = path_parts[1]
        file_ext = path_to_file.split('.', 1)[1]
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid path.')
    if request.inputSoundFormat.value != file_ext:
        raise HTTPException(status_code=400, detail='Invalid input sound format.')

    result_folder = f"results/{request.id}"

    background_tasks.add_task(process, request, bucket_name, path_to_file, file_ext, result_folder)

    return {
        "path": request.path,
        "id": request.id,
        "outputFolderPath": f"gs://{bucket_name}/{result_folder}"
    }


def process(request, bucket_name, path_to_file, file_ext, result_folder):
    bucket = storage_client.get_bucket(bucket_name)
    file = bucket.get_blob(path_to_file)
    request_input_path = f"{input_files_path}/{request.id}"
    request_output_path = f"{output_files_path}/{request.id}"
    if not os.path.exists(request_input_path):
        os.mkdir(request_input_path)
    if not os.path.exists(request_output_path):
        os.mkdir(request_output_path)
    with open(f"{request_input_path}/{request.id}.{file_ext}", "wb+") as file_in:
        file.download_to_file(file_in)

    song = AudioSegment.from_file(f"{request_input_path}/{request.id}.{file_ext}", file_ext)

    if 'SPLITTING_FREQUENCY' in os.environ:
        splitting_frequency = int(os.getenv('SPLITTING_FREQUENCY'))
    else:
        splitting_frequency = 10

    segments_count = math.ceil(song.duration_seconds / (splitting_frequency * 60))
    for i in range(segments_count):
        m1 = i * splitting_frequency * 60000
        m2 = (i + 1) * splitting_frequency * 60000
        segment = song[m1:m2]
        segment_path = f"{request_input_path}/{request.id}-segment{i}.wav"
        segment.export(segment_path, format='wav')
        separator.separate_to_file(segment_path, request_output_path, codec=request.outputSoundFormat.value, duration=splitting_frequency*60)

    speech_start_segment = AudioSegment.from_file(f"{request_output_path}/{request.id}-segment0/vocals.{request.outputSoundFormat.value}", request.outputSoundFormat.value)
    background_start_segment = AudioSegment.from_file(f"{request_output_path}/{request.id}-segment0/accompaniment.{request.outputSoundFormat.value}", request.outputSoundFormat.value)
    if segments_count > 1:
        for i in range(segments_count):
            speech_result = speech_start_segment + AudioSegment.from_file(
                f"{request_output_path}/{request.id}-segment{i}/vocals.{request.outputSoundFormat.value}",
                request.outputSoundFormat.value)
            background_result = background_start_segment + AudioSegment.from_file(
                f"{request_output_path}/{request.id}-segment{i}/accompaniment.{request.outputSoundFormat.value}",
                request.outputSoundFormat.value)
            speech_start_segment = speech_result
            background_start_segment = background_result
    else:
        speech_result = speech_start_segment
        background_result = background_start_segment
    speech_result.export(f"{request_output_path}/speech.{request.outputSoundFormat.value}",
                         format=request.outputSoundFormat.value)
    background_result.export(f"{request_output_path}/background.{request.outputSoundFormat.value}",
                             format=request.outputSoundFormat.value)

    vocal_blob = bucket.blob(f"{result_folder}/speech.{request.outputSoundFormat.value}")
    vocal_blob.upload_from_filename(f"{request_output_path}/speech.{request.outputSoundFormat.value}")
    accompaniment_blob = bucket.blob(f"{result_folder}/background.{request.outputSoundFormat.value}")
    accompaniment_blob.upload_from_filename(f"{request_output_path}/background.{request.outputSoundFormat.value}")
    if 'WEBHOOK_HOST' in os.environ:
        requests.post(f"{os.getenv('WEBHOOK_HOST')}/api/v1/orders/{request.id}/audio_split_finished")

    shutil.rmtree(f"{request_input_path}")
    shutil.rmtree(f"{request_output_path}")
