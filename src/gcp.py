from google.cloud import storage

from src.constants import GCP_UPLOAD_CHUNK_SIZE, GOOGLE_AUDIO_SPLIT_STORAGE_BUCKET

storage_client = storage.Client()


def download_file(gs_path, save_path):
    bucket = storage_client.bucket(GOOGLE_AUDIO_SPLIT_STORAGE_BUCKET)
    file = bucket.get_blob(gs_path)
    with open(save_path, 'wb+') as downloaded_file:
        file.download_to_file(downloaded_file)


def upload_file(file_path, file_path_in_bucket):
    bucket = storage_client.bucket(GOOGLE_AUDIO_SPLIT_STORAGE_BUCKET)
    file_blob = bucket.blob(file_path_in_bucket)
    file_blob.chunk_size = GCP_UPLOAD_CHUNK_SIZE
    file_blob.upload_from_filename(file_path)
