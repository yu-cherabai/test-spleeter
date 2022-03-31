from pydantic import BaseModel

from src.enums import CodecsOut, CodecsIn


class SeparateRequest(BaseModel):
    path: str
    id: str
    outputSoundFormat: CodecsOut
    inputSoundFormat: CodecsIn


class SeparateResponse(BaseModel):
    path: str
    id: str
    outputFolderPath: str
