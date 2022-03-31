from enum import Enum


class CodecsIn(Enum):
    aac = 'aac'
    ogg = 'ogg'
    wav = 'wav'
    flac = 'flac'
    mp3 = 'mp3'
    webm = 'webm'


class CodecsOut(Enum):
    wav = 'wav'
    mp3 = 'mp3'
