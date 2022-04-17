import os

CELERY_BROKER_URL = os.environ.get(
    'AUDIO_SPLIT_SERVICE_CELERY_BROKER_URL', 'redis://localhost:6379/5'
)
