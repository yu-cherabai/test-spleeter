import math
import os

from pydub import AudioSegment
from spleeter.separator import Separator

from src.constants import SPLITTING_FREQUENCY, ONE_MINUTE_IN_MILLISECONDS, ONE_MINUTE_IN_SECONDS, SEGMENTS_EXTENSION

spleeter = Separator('spleeter:2stems')


def separate_by_chunks(file_to_separate_path, result_folder, input_format, output_format):
    song = AudioSegment.from_file(file_to_separate_path, input_format)
    segments_count = math.ceil(song.duration_seconds / (SPLITTING_FREQUENCY * ONE_MINUTE_IN_SECONDS))

    for i in range(segments_count):
        segment_start = i * SPLITTING_FREQUENCY * ONE_MINUTE_IN_MILLISECONDS
        segment_end = (i + 1) * SPLITTING_FREQUENCY * ONE_MINUTE_IN_MILLISECONDS
        segment = song[segment_start:segment_end]
        segment_path = f'{result_folder}/segment{i}.{SEGMENTS_EXTENSION}'
        segment.export(segment_path, format=SEGMENTS_EXTENSION)
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
