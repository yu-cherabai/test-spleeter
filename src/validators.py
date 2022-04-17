from src.models import SeparateRequest


def is_separate_request_valid(request: SeparateRequest) -> bool:
    if '.' not in request.path:
        return False

    file_ext = request.path.split('.', 1)[1]
    if file_ext != request.inputSoundFormat.value:
        return False

    return True
