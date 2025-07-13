from random import randint
import subprocess

from utils import (
    time_to_seconds,
    add_subtitle_styling,
    get_number_of_filters,
    get_random_snippet_interval,
)


def snip_video(media_path, length, output_file_path):
    video_duration = get_mediafile_duration(media_path)
    s_time, e_time = get_random_snippet_interval(length, video_duration)
    command = [
        "ffmpeg",
        "-i",
        media_path,
        "-ss",
        str(s_time),
        "-t",
        str(e_time - s_time),
        "-c",
        "copy",
        output_file_path,
    ]
    subprocess.run(command)


def get_mediafile_duration(mediafile_path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        mediafile_path,
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    video_duration = float(result.stdout.decode().strip())
    return video_duration


def compute_summary_overlay_filters(
    summary_paths, media_stream_indexes, chain_index_padding
):
    summary_filters = []
    current_time = 0

    for index, summary_path in enumerate(summary_paths):
        overlay_length = randint(10, 15)
        summary_start_time = current_time + randint(0, 5)
        summary_end_time = summary_start_time + overlay_length

        summary_filters.append(
            get_overlay_filter_string(
                summary_start_time,
                summary_end_time,
                media_stream_indexes[index],
                chain_index_padding + index,
                get_position("top-middle"),
            )
        )
        current_time = summary_end_time
    return ";".join(summary_filters)


def get_filter_chain(
    filter_complex,
):
    filters = []
    if not filter_complex:
        return filters
    filters += ["-filter_complex", filter_complex]
    return filters


def get_map_chain(audio_stream_index):
    return [
        "-map",
        "[vout]",
        "-map",
        f"{audio_stream_index}:a",
    ]


def get_formatting_params(rendering_codec, output_path):
    return [
        "-c:v",
        rendering_codec,
        "-c:a",
        "aac",
        output_path,
    ]


def get_position(position):
    if position == "bottom-left":
        return "W-w-300:H-h-0"
    elif position == "top-middle":
        return "(W-w)/2:10"
    elif position == "bottom-right":
        return "W-w-10:H-h-0"
    else:
        return "0:0"


def get_overlay_filter_string(
    overlap_start_time,
    overlap_end_time,
    media_stream_index,
    chain_index,
    position,
):
    chain_join_index = (
        f"[v{chain_index-1}][{media_stream_index + 1}:v]"
        if chain_index > 0
        else "[0:v][1:v]"
    )
    return f"{chain_join_index}overlay={position}:enable='between(t,{overlap_start_time},{overlap_end_time})'[v{chain_index}]"


def compute_avatars_overlay_filter(agent_ids, lines_data):
    filter_complex_parts = []
    for line_index, entry in enumerate(lines_data):
        overlap_start_time = time_to_seconds(entry["start"])
        overlap_end_time = time_to_seconds(entry["end"])
        position = (
            get_position("bottom-left")
            if line_index % 2 == 0
            else get_position("bottom-right")
        )
        filter_complex_parts.append(
            get_overlay_filter_string(
                overlap_start_time,
                overlap_end_time,
                agent_ids.index(entry["agentId"]),
                line_index,
                position,
            )
        )
    return ",".join(filter_complex_parts)


def get_subtitle_filter(chain_index, subtitle_path):
    return f"[v{chain_index-1}]subtitles={subtitle_path}[vout]"


def compose_ffmpeg_command(
    inputs_path_list,
    overlay_filters,
    subtitle_path,
    rendering_codec,
    output_path,
    enable_map=True,
):
    command = ["ffmpeg"]
    maps = []

    inputs_chain = create_input_chain(inputs_path_list)
    overlay_filters = get_filter_chain(overlay_filters)
    if subtitle_path:
        overlay_filters[-1] += get_subtitle_filter(
            get_number_of_filters(overlay_filters[-1]), subtitle_path
        )
    if enable_map:
        maps = get_map_chain(len(inputs_path_list) - 1)
    rendering_params = get_formatting_params(rendering_codec, output_path)

    return command + inputs_chain + overlay_filters + maps + rendering_params


def create_input_chain(input_paths_list):
    inputs_chain = []
    for input_path in input_paths_list:
        inputs_chain += ["-i", input_path]
    return inputs_chain


def convert_subtitle_file(file_path, font, output_path):
    command = compose_ffmpeg_command(
        [file_path], [], "", "", output_path, enable_map=False
    )
    execute_ffmpeg_command(command)
    add_subtitle_styling(output_path, font)


def execute_ffmpeg_command(command):
    subprocess.run(command)
