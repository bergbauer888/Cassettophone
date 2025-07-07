from ollama import chat

import torchaudio

from video_utils import (
    compute_avatars_overlay_filter,
    compose_ffmpeg_command,
    execute_ffmpeg_command,
    compute_summary_overlay_filters,
)
from utils import *
from zonos.conditioning import make_cond_dict
from zonos.model import Zonos
from zonos.utils import DEFAULT_DEVICE as device

import questionary
from assets_params import cli_styling, qmark_styling


def generate_draft_script(model_name, topic, characters_list):
    no_characters = len(characters_list)
    if no_characters == 1:
        agent_names = characters_list[0]
    else:
        agent_names = ", ".join(characters_list[:-1])
        agent_names += f" and {characters_list[-1]}"

    template = config["prompt"]["template"]
    content = template.format(
        topic=topic, no_characters=no_characters, agent_names=agent_names
    )
    response = chat(model=model_name, messages=[{"role": "system", "content": content}])
    return response.message.content


def generate_script(script_gen_model_name, topic, characters_list):
    while True:
        script = generate_draft_script(script_gen_model_name, topic, characters_list)
        answer = questionary.confirm(
            f"{script}\nKeep the script?", style=cli_styling, qmark=qmark_styling
        ).ask()
        if answer:
            return script


def generate_audio(
    audio_gen_model_name, video_script_json, characters_map, output_folder
):
    script_data = parse_json(video_script_json)
    model = Zonos.from_pretrained(audio_gen_model_name, device=device)
    entries = script_data["transcript"]
    for index in range(len(entries)):
        entry = entries[index]
        generate_audioclip(
            model,
            entry["text"],
            characters_map[fix_agent_casing(entry["agentId"])]["audio_sample_path"],
            f"{output_folder}/line{index}.wav",
        )


def generate_audioclip(model, text, audio_sample_path, output_path):
    wav, sampling_rate = torchaudio.load(audio_sample_path)
    speaker = model.make_speaker_embedding(wav, sampling_rate)

    torch.manual_seed(421)

    cond_dict = make_cond_dict(text=text, speaker=speaker, language="en-us")
    conditioning = model.prepare_conditioning(cond_dict)

    codes = model.generate(conditioning)

    wavs = model.autoencoder.decode(codes).cpu()
    torchaudio.save(output_path, wavs[0], model.autoencoder.sampling_rate)


def generate_brainrot_clip(
    processed_assets_paths,
    lines_map_path,
    agent_ids,
    summary_paths,
    subtitle_path,
    output_path,
):
    with open(lines_map_path, "r") as json_data:
        lines_data = json.load(json_data)
    avatars_overlay = compute_avatars_overlay_filter(
        agent_ids,
        lines_data,
    )
    overlay_stream_indexes = [
        processed_assets_paths.index(summary_path) - 1 for summary_path in summary_paths
    ]
    summary_overlay = compute_summary_overlay_filters(
        summary_paths, overlay_stream_indexes, len(lines_data)
    )
    overlay_filters = (
        f"{avatars_overlay};{summary_overlay};"
        if summary_overlay
        else f"{avatars_overlay};"
    )
    command = compose_ffmpeg_command(
        processed_assets_paths,
        overlay_filters,
        subtitle_path,
        config["settings"]["VIDEO_RENDERING_CODEC"],
        output_path,
    )
    execute_ffmpeg_command(command)


def generate_lines_map(script, map_output_path):
    subtitles = parse_subtitles(map_output_path)
    lines_array = []
    sub_index = 0
    for line in parse_json(script)["transcript"]:
        cleaned_script_line = remove_non_alphabetic(line["text"])
        sub_index, starting_index = find_matching_subtitle(
            subtitles, cleaned_script_line, sub_index
        )
        if sub_index < len(subtitles):
            lines_array.append(
                {
                    "agentId": fix_agent_casing(line["agentId"]),
                    "start": subtitles[starting_index]["start"],
                    "end": subtitles[sub_index]["end"],
                }
            )
        sub_index += 1
    with open(map_output_path, "w") as outfile:
        json.dump(lines_array, outfile, indent=4)


def generate_srt_content(transcription, subtitle_type):
    if subtitle_type == "sentence":
        return convert_to_line_srt_file(transcription.segments)
    srt_content = transcription.to_srt_vtt(word_level=True)
    return process_subtitle(srt_content, word_limit=3)


def generate_subtitle(
    audio_file_path,
    subtitle_type,
    subtitle_output_path,
    lines_map_output_path,
    model_type="turbo",
):
    model = get_subtitle_model(device, model_type)
    result = model.transcribe(audio=audio_file_path)
    srt_content = generate_srt_content(result, subtitle_type)
    lines_map_content = generate_srt_content(result, "sentence")
    with open(subtitle_output_path, "w") as outfile:
        outfile.write(srt_content)
    with open(lines_map_output_path, "w") as outfile:
        outfile.write(lines_map_content)
