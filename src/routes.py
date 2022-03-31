from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from src.celery_tasks import process
from src.gcp import extract_bucket_name_from_gs_path
from src.models import SeparateResponse, SeparateRequest
from src.validators import is_separate_request_valid

router = APIRouter()


@router.post('/separate', response_model=SeparateResponse)
async def separate(request: SeparateRequest):
    if not is_separate_request_valid(request):
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid path to file')

    process.delay(request.json())

    return {
        'path': request.path,
        'id': request.id,
        'outputFolderPath': f'gs://{extract_bucket_name_from_gs_path(request.path)}/results/{request.id}'
    }
