import os

from src.enums import CodecsIn

# ENV CONSTANTS
GOOGLE_AUDIO_SPLIT_STORAGE_BUCKET = os.environ.get('GOOGLE_AUDIO_SPLIT_STORAGE_BUCKET', 'vidby-test')

SPLITTING_FREQUENCY = int(os.environ.get('SPLITTING_FREQUENCY', "2"))

os.environ['CELERY_BROKER_URL'] = os.environ.get(
    'AUDIO_SPLIT_SERVICE_CELERY_BROKER_URL', 'redis://localhost:6379/5'
)

WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST', None)

# NOT ENV CONSTANTS
FOLDER_PROCESSING = '/tmp/spleeter_processing'

ONE_MINUTE_IN_MILLISECONDS = 60000

ONE_MINUTE_IN_SECONDS = 60

# 50Mb
GCP_UPLOAD_CHUNK_SIZE = 1024 * 1024 * 50

SEGMENTS_EXTENSION = CodecsIn.wav.value
