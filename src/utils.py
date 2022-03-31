import os
import shutil

from src.constants import FOLDER_PROCESSING


def create_request_folder(request_folder_path):
    if not os.path.exists(FOLDER_PROCESSING):
        os.mkdir(FOLDER_PROCESSING)
    if os.path.exists(request_folder_path):
        delete_request_folder(request_folder_path)
    os.mkdir(request_folder_path)


def delete_request_folder(request_folder_path):
    shutil.rmtree(request_folder_path)
