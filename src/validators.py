from src.enums import CodecsIn
from src.models import SeparateRequest


def is_separate_request_valid(request: SeparateRequest) -> bool:
    if not request.path.startswith('gs://'):
        return False

    path_parts = request.path[5:].split('/', 1)
    if len(path_parts) != 2:
        return False

    if '.' not in path_parts[1]:
        return False

    file_ext = path_parts[1].split('.', 1)[1]
    if file_ext not in [item.value for item in CodecsIn]:
        return False

    if file_ext != request.inputSoundFormat.value:
        return False

    return True
