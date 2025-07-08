from assets_params import (
    characters_map,
    video_paths,
    subtitle_types,
    fonts,
    music_choices,
    text_color_pixel,
)
from datetime import datetime
from generators import *
import questionary
from utils import *
import configparser

from video_utils import convert_subtitle_file, snip_video, get_mediafile_duration


def runner(video_params, characters_map):
    print_logo()
    print(f"{text_color_pixel}\n" + "[*] Generating Script. This will take a bit\n")
    script = generate_script(
        video_params["script_gen_model_name"],
        video_params["topic"],
        [
            characters_map[character_id]["display_name"]
            for character_id in video_params["characters"]
        ],
    )
    print(f"{text_color_pixel}\n" + "[*] Script Generated\n")
    print(
        f"{text_color_pixel}\n" + "[*] Generating audio clips. This will take a while\n"
    )
    generate_audio(
        video_params["audio_gen_model_name"],
        script,
        characters_map,
        video_params["audio_output_folder"],
    )
    print(f"{text_color_pixel}\n" + "[*] Dialogue Voices Generated\n")
    print(f"{text_color_pixel}\n" + "[*] Equalizing audio clips.\n")
    mix_audio_files(video_params["audio_output_folder"])
    print(f"{text_color_pixel}\n" + "[*] Audio clips equalized.\n")
    print(f"{text_color_pixel}\n" + "[*] Merging audio clips.\n")
    merge_audio_files(video_params["audio_output_folder"])
    print(f"{text_color_pixel}\n" + "[*] Audio clips merged.\n")
    print(f"{text_color_pixel}\n" + "[*] Generating subtitle.\n")
    generate_subtitle(
        f"{video_params["audio_output_folder"]}/video_audio.wav",
        video_params["subtitle_type"],
        f"{video_params["subtitle_output_folder"]}/transcript.srt",
        f"{video_params["output_folder"]}/lines_map.json",
    )
    print(f"{text_color_pixel}\n" + "[*] Subtitle Generated\n")
    print(f"{text_color_pixel}\n" + "[*] Generating Character Lines Map.\n")
    generate_lines_map(
        script,
        f"{video_params["output_folder"]}/lines_map.json",
    )
    print(f"{text_color_pixel}\n" + "[*] Character Lines Map Generated\n")
    print(f"{text_color_pixel}\n" + "[*] Generate Suggestive Image for Topic.\n")
    summary_output_paths = download_suggestive_images(
        script, f'{video_params["output_folder"]}'
    )
    print(f"{text_color_pixel}\n" + "[*] Suggestive Image Generated\n")
    print(f"{text_color_pixel}\n" + "[*] Mixing Audio\n")
    mix_audiofiles(
        f'{video_params["audio_output_folder"]}/video_audio.wav',
        video_params["music"],
        f'{video_params["audio_output_folder"]}/F_output.wav',
    )
    print(f"{text_color_pixel}\n" + "[*] Audio Mixed\n")
    print(f"{text_color_pixel}\n" + "[*] Generating background video.\n")
    snip_video(
        video_params["backdrop"],
        get_mediafile_duration(f'{video_params["audio_output_folder"]}/F_output.wav'),
        f"{video_params['output_folder']}/backdrop.mp4",
    )
    print(f"{text_color_pixel}\n" + "[*] Background video Generated\n")

    print(f"{text_color_pixel}\n" + "[*] Processing assets\n")
    processed_avatars_paths = process_avatar_images(
        extract_agent_ids_from_line_file(
            f'{video_params["output_folder"]}/lines_map.json'
        ),
        characters_map,
        video_params["output_folder"],
    )
    process_summaries_paths = process_summaries_images(
        summary_output_paths,
        video_params["output_folder"],
    )
    print(f"{text_color_pixel}\n" + "[*] Assets processed\n")

    print(f"{text_color_pixel}\n" + "[*] Processing Captions\n")
    convert_subtitle_file(
        f"{video_params["subtitle_output_folder"]}/transcript.srt",
        video_params["font"],
        f"{video_params['output_folder']}/subtitle.ass",
    )
    print(f"{text_color_pixel}\n" + "[*] Captions Processed\n")
    print(f"{text_color_pixel}\n" + "[*] Generating Reel\n")
    processed_subtitle_path = f"{video_params['output_folder']}/subtitle.ass"
    assets_list = [
        f"{video_params['output_folder']}/backdrop.mp4",
        *processed_avatars_paths,
        *process_summaries_paths,
        processed_subtitle_path,
        f'{video_params["audio_output_folder"]}/F_output.wav',
    ]
    generate_brainrot_clip(
        assets_list,
        f'{video_params["output_folder"]}/lines_map.json',
        video_params["characters"],
        process_summaries_paths,
        processed_subtitle_path,
        video_params["reel_path"],
    )
    print(f"{text_color_pixel}\n" + "[*] Reel Generated\n")
    if config['settings']['GOKAPI_URL']:
        print(f"{text_color_pixel}\n" + "[*] Uploading Video\n")
        video_url = upload_video(video_params["reel_path"])
        print(f"{text_color_pixel}\n" + "[*] Video Uploaded\n")
        print(f"{text_color_pixel}\n" + "[*] Download URL: " + video_url + "\n")
    print("\n[*] Job Finished")


def main():
    print_logo()
    video_params = questionary.form(
        topic=questionary.text(
            "1. Enter a topic:",
            validate=lambda text: len(text.strip()) > 0 or "Topic cannot be empty.",
            style=cli_styling,
            qmark=qmark_styling,
        ),
        music=questionary.select(
            "2. Pick Background music",
            choices=music_choices,
            style=cli_styling,
            qmark=qmark_styling,
        ),
        characters=questionary.checkbox(
            "3. Pick the character list (min. 1)",
            choices=[
                questionary.Choice(
                    character["display_name"],
                    value=fix_agent_casing(character["display_name"]),
                )
                for character in characters_map.values()
            ],
            validate=lambda a: len(a) > 0 or "Select at least one character.",
            style=cli_styling,
            qmark=qmark_styling,
        ),
        backdrop=questionary.select(
            "4. Pick a background gameplay",
            choices=video_paths,
            style=cli_styling,
            qmark=qmark_styling,
        ),
        subtitle_type=questionary.select(
            "5. Pick subtitle type",
            choices=subtitle_types,
            style=cli_styling,
            qmark=qmark_styling,
        ),
        font=questionary.select(
            "6. Pick a font", choices=fonts, style=cli_styling, qmark=qmark_styling
        ),
    ).ask()
    video_params["script_gen_model_name"] = config["settings"]["TEXT_MODEL_NAME"]
    video_params["audio_gen_model_name"] = config["settings"]["AUDIO_MODEL_NAME"]
    video_params["output_folder"] = config["settings"]["OUTPUT_FOLDER"]
    video_params["audio_output_folder"] = f"{video_params['output_folder']}/samples"
    video_params["subtitle_output_folder"] = (
        f"{video_params['output_folder']}/subtitles"
    )
    video_params["reel_path"] = (
        f'{video_params["output_folder"]}/brainrot_kunst_{datetime.now().strftime("%d-%m-%H-%M")}.mp4'
    )
    prepare_fs(
        video_params["output_folder"],
        video_params["audio_output_folder"],
        video_params["subtitle_output_folder"],
    )
    runner(video_params, characters_map)


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config.ini")
    main()
