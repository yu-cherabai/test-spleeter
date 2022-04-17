from pydantic import BaseModel

from src.enums import CodecsOut, CodecsIn


class SeparateRequest(BaseModel):
    path: str
    id: str
    output_sound_format: CodecsOut
    input_sound_format: CodecsIn


class SeparateResponse(BaseModel):
    path: str
    id: str
    output_folder_path: str
