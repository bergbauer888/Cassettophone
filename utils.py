from math import ceil
from sys import platform
from os import system, listdir, path, mkdir
from difflib import SequenceMatcher
from shutil import rmtree
from pydub import AudioSegment
import random
from PIL import Image
import soundfile as sf
import torch
import stable_whisper

import numpy as np
import librosa
import re
import os
import requests
import json
import configparser
from datetime import timedelta
import subprocess

config = configparser.ConfigParser()
config.read("config.ini")


def print_logo(text_color="\033[44m"):
    if platform.startswith("win"):
        system("cls")
    else:
        system("clear")
    print(
        f"""{text_color}
░░░░░░░░░░░░░░▒▒▒▒▒▒▒▒▒▒▒▒▓▓▓▓▓▓▓▓▓▓▓▓█████████████
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓
▒░█▀▀░█▀█░█▀▀░█▀▀░▀█▀░▀█▀░█▀█░█▀█░█░█░█▀█░█▀█░█▀▀░▓
▒░█░░░█▀█░▀▀█░█▀▀░░█░░░█░░█░█░█▀▀░█▀█░█░█░█░█░█▀▀░▒
▓░▀▀▀░▀░▀░▀▀▀░▀▀▀░░▀░░░▀░░▀▀▀░▀░░░▀░▀░▀▀▀░▀░▀░▀▀▀░▒
▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
████████████▓▓▓▓▓▓▓▓▓▓▓▓▒▒▒▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░
"""
    )


def fix_agent_casing(agent_name):
    return agent_name.lower().replace(" ", "_")


def list_files_in_dir(directory, include_directory=False):
    entities = [
        entry
        for entry in listdir(directory)
        if path.isfile(path.join(directory, entry))
    ]
    if include_directory:
        entities = [os.path.join(directory, entry) for entry in entities]
    return entities


def time_to_srt(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def time_to_seconds(time_str):
    hours, minutes, seconds_milliseconds = time_str.split(":")
    seconds = seconds_milliseconds.split(",")[0]
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def merge_audio_files(audio_root_folder):
    combined_audio = AudioSegment.silent()
    for file_name in sorted(
        list_files_in_dir(audio_root_folder, include_directory=True)
    ):
        audio_segment = AudioSegment.from_wav(file_name)
        combined_audio += audio_segment

    combined_audio.export(f"{audio_root_folder}/video_audio.wav", format="wav")


def mix_audio_files(audio_root_folder):
    file_paths = list_files_in_dir(audio_root_folder, include_directory=True)
    audio_intensities = [
        np.sqrt(np.mean(y**2)) for y, _ in map(librosa.load, file_paths)
    ]
    average_intensity = np.mean(audio_intensities)
    for file_path in file_paths:
        y, sr = librosa.load(file_path)
        current_rms = np.sqrt(np.mean(y**2))
        scale_factor = average_intensity / current_rms
        normalized_audio = y * scale_factor

        output_file_path = os.path.join(audio_root_folder, os.path.basename(file_path))
        sf.write(output_file_path, normalized_audio, sr)


def mix_audiofiles(
    audio_file_path, bg_music_file_path, output_path, bg_volume_reduction=6
):
    sound1 = AudioSegment.from_file(bg_music_file_path, format="mp3")
    sound2 = AudioSegment.from_file(audio_file_path, format="mp3")

    sound1_adjusted = sound1 - bg_volume_reduction

    overlay = sound2.overlay(sound1_adjusted, position=0)
    overlay.export(output_path, format="wav")


def add_subtitle_styling(subtitle_path, font, weight=18, color="&H0099ff"):
    new_style_definition = f"Style: Default,{font},{weight},{color},&Hffffff,&H0,&H0,1,0,0,0,100,100,0,0,1,1,2,5,50,50,50,1\n"

    with open(subtitle_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    for line in lines:
        if line.strip().startswith("Style:"):
            lines[(lines.index(line))] = new_style_definition
    with open(subtitle_path, "w") as file:
        file.write("".join(lines))


def prepare_fs(output_folder, audio_output_folder, subtitle_output_folder):
    if path.exists(audio_output_folder):
        rmtree(audio_output_folder)
    if path.exists(subtitle_output_folder):
        rmtree(subtitle_output_folder)
    if path.exists(output_folder):
        rmtree(output_folder)

    mkdir(output_folder)
    mkdir(audio_output_folder)
    mkdir(subtitle_output_folder)


def parse_json(json_string):
    try:
        return json.loads(json_string)
    except Exception as e:
        return json.loads(
            json_string[json_string.find("\n") + 1 : json_string.rfind("\n")]
        )


def convert_to_line_srt_file(segments):
    srt_content = []

    for i, segment in enumerate(segments):
        start_time = timedelta(seconds=segment.start).__str__()
        end_time = timedelta(seconds=segment.end).__str__()

        start_time = start_time.replace(".", ",")
        end_time = end_time.replace(".", ",")

        subtitle_entry = (
            f"{i + 1}\n{start_time} --> {end_time}\n{segment.text.strip()}\n\n"
        )
        srt_content.append(subtitle_entry)

    return "".join(srt_content)


def parse_subtitles(subtitle_file_path):
    with open(subtitle_file_path, "r") as file:
        subtitles = file.read().strip().split("\n\n")

    subtitle_entries = []
    for entry in subtitles:
        lines = entry.split("\n")
        if len(lines) < 3:
            continue
        index = lines[0]
        time_range = lines[1]
        text = " ".join(lines[2:])

        start, end = time_range.split(" --> ")
        subtitle_entries.append(
            {"index": index, "start": start, "end": end, "text": text}
        )

    return subtitle_entries


def remove_non_alphabetic(text):
    text = text.lower()
    return re.sub(r"[^a-zA-Z]", "", text)


def download_image(image_url, output_path):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(output_path, "wb") as file:
                file.write(response.content)
            print(f"Image downloaded and saved to {output_path}")
        else:
            print(f"Failed to download image: {response.status_code}")
    except Exception as e:
        print(f"Error downloading image: {e}")


def fetch_search_image_url(query):
    params = {"q": query, "categories": "images", "format": "json"}
    if not config['settings']["SEARX_BASE_URL"]:
        print("No searx instance has been set.")
        return None
    response = requests.get(
        config["settings"]["SEARX_BASE_URL"] + "/search", params=params
    )
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            first_result = results[0]
            return first_result.get("img_src")
        else:
            print("No image results found.")
            return None
    else:
        print(f"Failed to retrieve results: {response.status_code}")
        return None


def limit_line_rows(line, word_limit):
    token_pattern = re.compile(r"(<[^>]+>[^<]+</[^>]+>|[^<\s]+)")
    if "<font" in line:
        tokens = [token for token in token_pattern.split(line) if token.strip()]
        highlighted_word_index = next(
            (index for index, token in enumerate(tokens) if "<font" in token), None
        )

        if highlighted_word_index is not None:
            segment_start = (highlighted_word_index // word_limit) * word_limit
            segment_end = segment_start + word_limit
            line = " ".join(tokens[segment_start:segment_end])

    return line


"""
Sometimes the generated subtitles will contain lines have no highlighted words, ex:
3
00:00:01,760 --> 00:00:01,840
Challenge accepted, Donald.
instead of <font color="#00ff00">Challenge</font> accepted, Donald. 
In order to avoid a visual tweaking effect, we need to replace the ending timestamp
of the previous row with the one of the faulty line.
"""


def fix_subtitle_twitching(lines_array):
    fixed_lines = []
    prev_line_index = -1

    for index in range(0, len(lines_array), 4):
        line_number = lines_array[index].strip()
        timestamps = lines_array[index + 1].strip().split(" --> ")
        text = lines_array[index + 2].strip()

        if "<font" in text:
            if prev_line_index != -1:
                fixed_lines[prev_line_index] = "{}\n{} --> {}\n{}\n".format(
                    fixed_lines[prev_line_index].split("\n")[0],
                    fixed_lines[prev_line_index].split("\n")[1].split(" --> ")[0],
                    timestamps[0],
                    fixed_lines[prev_line_index].split("\n")[2],
                )

            fixed_lines.append(
                "{}\n{}\n{}".format(line_number, " --> ".join(timestamps), text)
            )

            prev_line_index = len(fixed_lines) - 1
        else:
            if prev_line_index != -1:
                fixed_lines[prev_line_index] = "{}\n{} --> {}\n{}".format(
                    fixed_lines[prev_line_index].split("\n")[0],
                    fixed_lines[prev_line_index].split("\n")[1].split(" --> ")[0],
                    timestamps[1],
                    fixed_lines[prev_line_index].split("\n")[2],
                )
    return " ".join(fixed_lines)


def process_subtitle(srt_content, word_limit):
    lines = srt_content.split("\n")
    result_lines = [limit_line_rows(line, word_limit) for line in lines]
    result_lines = fix_subtitle_twitching(result_lines)

    return "".join(result_lines)


def process_option_string(entry):
    if "/" in entry and "." in entry:
        entry = entry.split("/")[-1].split(".")[0]
    return entry.capitalize().replace("_", " ")


def download_suggestive_images(script, output_folder):
    output_paths = []
    for index, summary in enumerate(parse_json(script)["summary"]):
        image_url = fetch_search_image_url(summary)
        if image_url:
            output_path = f"{output_folder}/summary{index}.png"
            download_image(image_url, output_path)
            output_paths.append(output_path)
    return output_paths


def get_rendering_device():
    if torch.cuda.is_available():
        return torch.device(torch.cuda.current_device())
    if torch.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def get_subtitle_model(device, model_type):
    if device == torch.device("mps"):
        return stable_whisper.load_mlx_whisper(model_type)
    return stable_whisper.load_model(model_type, device=device)


def resize_image(image_path, output_path, size=(800, 800)):
    with Image.open(image_path) as img:
        img = img.convert("RGBA")
        img = img.resize(size=size)
        img.save(output_path)


def extract_agent_ids_from_line_file(lines_map_path):
    with open(lines_map_path, "r") as json_data:
        lines_data = json.load(json_data)
        entries = []
        for item in lines_data:
            if item["agentId"] not in entries:
                entries.append(item["agentId"])
        return entries


def parse_time_from_filter(filter, position):
    pattern = r"between\(t,(\d+),(\d+)\)"
    matches = list(re.finditer(pattern, filter))
    if position >= len(matches):
        return None, None
    match = matches[position]
    start, end = map(int, match.groups())
    return start, end


def get_number_of_filters(filter_string):
    pattern = r"between\(t,(\d+),(\d+)\)"
    matches = list(re.finditer(pattern, filter_string))
    return len(matches)


def process_avatar_images(agents_list, characters_map, output_folder):
    processed_assets_paths = []
    for agent_id in agents_list:
        resize_image(
            characters_map[agent_id]["avatar_path"],
            f"{output_folder}/resized_{agent_id}.png",
        )
        processed_assets_paths.append(f"{output_folder}/resized_{agent_id}.png")
    return processed_assets_paths


def process_summaries_images(summary_output_paths, output_folder):
    processed_assets_paths = []

    for index, summary_image_path in enumerate(summary_output_paths):
        if os.path.exists(summary_image_path):
            # aici am pus index, de modificat in filtre
            resized_summary_path = f"{output_folder}/resized_summary{index}.png"
            resize_image(summary_image_path, resized_summary_path)
            processed_assets_paths.append(resized_summary_path)

    return processed_assets_paths


def get_random_snippet_interval(length, media_duration, ending_padding=5):
    s_time = random.randint(0, ceil(media_duration - (length + ending_padding)))
    e_time = s_time + length
    return s_time, e_time


def get_lines_map_file_length(lines_map_path):
    with open(lines_map_path, "r") as json_data:
        return len(json.load(json_data))


def find_matching_subtitle(subtitles, cleaned_script_line, sub_index):
    base_text = ""
    starting_index = sub_index
    while sub_index < len(subtitles):
        base_text += remove_non_alphabetic(subtitles[sub_index]["text"])
        similarity_ratio = SequenceMatcher(None, base_text, cleaned_script_line).ratio()
        if similarity_ratio >= 0.95:
            break
        if len(base_text) > len(cleaned_script_line):
            sub_index -= 1
            break
        sub_index += 1
    return sub_index, starting_index


def upload_video(file_path):

    command = [
        "curl",
        "-X",
        "POST",
        f"{config['settings']['GOKAPI_URL']}/api/files/add",
        "-H",
        "accept: application/json",
        "-H",
        f"apikey: {config['settings']['GOKAPI_TOKEN']}",
        "-H",
        "Content-Type: multipart/form-data",
        "-F",
        "allowedDownloads=100",
        "-F",
        "expiryDays=1",
        "-F",
        f"file=@{file_path}",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        try:
            response_json = json.loads(result.stdout)
            return response_json["FileInfo"]["UrlHotlink"]
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
        except KeyError as e:
            print(f"Key not found in JSON: {e}")
    else:
        print(f"Command failed with return code: {result.returncode}")
