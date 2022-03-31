import math

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
    speach_next_segment = AudioSegment.from_file(f'{folder}/segment0/vocals.{file_format}', file_format)
    background_next_segment = AudioSegment.from_file(f'{folder}/segment0/accompaniment.{file_format}', file_format)
    if segments_count > 1:
        for i in range(1, segments_count):
            speach_result = speach_next_segment + AudioSegment.from_file(
                f'{folder}/segment{i}/vocals.{file_format}', file_format)
            background_result = background_next_segment + AudioSegment.from_file(
                f'{folder}/segment{i}/accompaniment.{file_format}', file_format)
            speach_next_segment = speach_result
            background_next_segment = background_result
    speach_next_segment.export(f'{folder}/speach.{file_format}', format=file_format)
    background_next_segment.export(f'{folder}/background.{file_format}', format=file_format)
