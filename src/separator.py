import math
import os

from spleeter.separator import Separator

from src.constants import SPLITTING_FREQUENCY, ONE_MINUTE_IN_MILLISECONDS, ONE_MINUTE_IN_SECONDS, SEGMENTS_EXTENSION
from src.enums import CodecsIn

spleeter = Separator('spleeter:2stems')


def separate_by_chunks(file_to_separate_path, file_name, result_folder, input_format, output_format):
    if input_format == CodecsIn.webm.value:
        os.system(f'ffmpeg -i "{file_to_separate_path}" -vn -y "{result_folder}/{file_name}.{SEGMENTS_EXTENSION}"')
        file_to_separate_path = f"{result_folder}/{file_name}.{SEGMENTS_EXTENSION}"

    audio_duration = float(os.popen(f'ffprobe -i "{file_to_separate_path}" -show_entries format=duration -v quiet -of csv="p=0"').read())
    segments_count = math.ceil(audio_duration / (SPLITTING_FREQUENCY * ONE_MINUTE_IN_SECONDS))

    for i in range(segments_count):
        segment_start = i * SPLITTING_FREQUENCY * ONE_MINUTE_IN_MILLISECONDS
        segment_path = f'{result_folder}/segment{i}.{input_format}'
        os.system(f'ffmpeg -ss {segment_start} -i "{file_to_separate_path}" -c copy -t {SPLITTING_FREQUENCY * ONE_MINUTE_IN_SECONDS} "{segment_path}"')
        spleeter.separate_to_file(segment_path, result_folder,
                                  codec=output_format, duration=SPLITTING_FREQUENCY * ONE_MINUTE_IN_SECONDS)

    join_separated_segments(segments_count, result_folder, output_format)


def join_separated_segments(segments_count, folder, file_format):

    generate_segments_list_files(segments_count, folder, file_format)

    os.system(f"ffmpeg -f concat -safe 0 -i {folder}/speach_segments.txt -c copy {folder}/speach.{file_format}")
    os.system(f"ffmpeg -f concat -safe 0 -i {folder}/background_segments.txt -c copy {folder}/background.{file_format}")


def generate_segments_list_files(segments_count, folder, file_format):
    with open(f'{folder}/speach_segments.txt', 'a+') as speach_segments:
        for i in range(segments_count):
            speach_segments.write(f"file '{folder}/segment{i}/vocals.{file_format}'\n")
    with open(f'{folder}/background_segments.txt', 'a+') as background_segments:
        for i in range(segments_count):
            background_segments.write(f"file '{folder}/segment{i}/accompaniment.{file_format}'\n")

