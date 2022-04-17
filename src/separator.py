import logging
import math
import os

from spleeter.separator import Separator

from src.constants import SPLITTING_FREQUENCY, ONE_MINUTE_IN_SECONDS, CONVERTED_CODEC_EXT
from src.enums import CodecsIn

spleeter = Separator('spleeter:2stems')


def separate_by_chunks(file_to_separate_path, file_name, result_folder, input_format, output_format):
    file_to_separate_path = convert_audio(file_to_separate_path, file_name, result_folder, input_format)
    audio_duration = float(os.popen(f'ffprobe -i "{file_to_separate_path}" -show_entries format=duration -v quiet -of csv="p=0"').read())
    segments_count = math.ceil(audio_duration / (SPLITTING_FREQUENCY * ONE_MINUTE_IN_SECONDS))

    for i in range(segments_count):
        segment_start = i * SPLITTING_FREQUENCY * ONE_MINUTE_IN_SECONDS
        segment_path = f'{result_folder}/segment{i}.{CONVERTED_CODEC_EXT}'
        os.system(f'ffmpeg -ss {segment_start} -i "{file_to_separate_path}" -c copy -t {SPLITTING_FREQUENCY * ONE_MINUTE_IN_SECONDS} "{segment_path}"')
        spleeter.separate_to_file(segment_path, result_folder,
                                  codec=output_format, duration=SPLITTING_FREQUENCY * ONE_MINUTE_IN_SECONDS)

    join_separated_segments(segments_count, result_folder, output_format)


def join_separated_segments(segments_count, folder, file_format):

    generate_segments_list_files(segments_count, folder, file_format)

    logging.info('Starting join of separated segments.')
    os.system(f"ffmpeg -f concat -safe 0 -i {folder}/speach_segments.txt -c copy {folder}/speach.{file_format}")
    os.system(f"ffmpeg -f concat -safe 0 -i {folder}/background_segments.txt -c copy {folder}/background.{file_format}")
    logging.info('End join of separated segments.')


def generate_segments_list_files(segments_count, folder, file_format):
    with open(f'{folder}/speach_segments.txt', 'a+') as speach_segments:
        for i in range(segments_count):
            speach_segments.write(f"file '{folder}/segment{i}/vocals.{file_format}'\n")
    with open(f'{folder}/background_segments.txt', 'a+') as background_segments:
        for i in range(segments_count):
            background_segments.write(f"file '{folder}/segment{i}/accompaniment.{file_format}'\n")


def convert_audio(file_path, file_name, result_folder, input_format) -> str:
    if input_format == CONVERTED_CODEC_EXT:
        return file_path
    elif input_format == CodecsIn.webm.value:
        os.system(f'ffmpeg -i "{file_path}" -vn -y "{result_folder}/{file_name}.{CONVERTED_CODEC_EXT}"')
    else:
        os.system(f'ffmpeg -i "{file_path}" "{result_folder}/{file_name}.{CONVERTED_CODEC_EXT}"')
    return f"{result_folder}/{file_name}.{CONVERTED_CODEC_EXT}"
