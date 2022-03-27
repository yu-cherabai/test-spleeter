import os
import shutil

import requests
from google.cloud import storage
from spleeter.separator import Separator

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
    with open(f"{input_files_path}/{request.id}.{file_ext}", "wb+") as file_in:
        file.download_to_file(file_in)
    if file_ext == CodecsIn.webm.value:
        new_ext = CodecsIn.wav.value
        os.system(f"ffmpeg -i \"{input_files_path}/{request.id}.{file_ext}\" -vn -y \"{input_files_path}/{request.id}.{new_ext}\"")
        os.remove(f"{input_files_path}/{request.id}.{file_ext}")
        file_ext = new_ext

    separator.separate_to_file(f"{input_files_path}/{request.id}.{file_ext}", output_files_path, codec=request.outputSoundFormat.value, duration=36000)

    vocal_blob = bucket.blob(f"{result_folder}/speech.{request.outputSoundFormat.value}")
    vocal_blob.upload_from_filename(f"{output_files_path}/{request.id}/vocals.{request.outputSoundFormat.value}")
    accompaniment_blob = bucket.blob(f"{result_folder}/background.{request.outputSoundFormat.value}")
    accompaniment_blob.upload_from_filename(f"{output_files_path}/{request.id}/accompaniment.{request.outputSoundFormat.value}")
    shutil.rmtree(f"{output_files_path}/{request.id}")
    os.remove(f"{input_files_path}/{request.id}.{file_ext}")

    if 'WEBHOOK_HOST' in os.environ:
        requests.post(f"{os.getenv('WEBHOOK_HOST')}/api/v1/orders/{request.id}/audio_split_finished")
