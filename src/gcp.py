from google.cloud import storage

storage_client = storage.Client()


def download_file(gs_path, save_path):
    bucket_name = extract_bucket_name_from_gs_path(gs_path)
    file_path_in_bucket = gs_path[5:].split('/', 1)[1]
    bucket = storage_client.get_bucket(bucket_name)
    file = bucket.get_blob(file_path_in_bucket)
    with open(save_path, 'wb+') as downloaded_file:
        file.download_to_file(downloaded_file)


def upload_file(bucket_name, file_path, file_path_in_bucket):
    bucket = storage_client.get_bucket(bucket_name)
    file_blob = bucket.blob(file_path_in_bucket)
    file_blob.upload_from_filename(file_path)


def extract_bucket_name_from_gs_path(path: str) -> str:
    return path[5:].split('/', 1)[0]
