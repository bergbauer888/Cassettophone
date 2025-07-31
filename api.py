import configparser
from datetime import datetime

from flask import Flask, render_template, jsonify, request
from brainrot_cli import runner

from assets_params import (
    characters_map,
    music_choices,
    video_paths,
    subtitle_types,
    fonts, results_store,
)
import uuid
from threading import Thread

from utils import fix_agent_casing

app = Flask("brainrot", template_folder="templates")
form_inputs_template = "choices.html"
characters_template = "characters.html"
result_template = "result.html"

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_music_choices")
def get_music_choices():
    choices = [{"value": choice, "label": choice} for choice in music_choices]
    return render_template(form_inputs_template, choices=choices)


@app.route("/get_characters")
def get_characters():
    characters = [character["display_name"] for character in characters_map.values()]
    choices = [{"value": character, "id": fix_agent_casing(character)} for character in characters]
    return render_template(characters_template, characters=choices)


@app.route("/get_backdrops")
def get_backdrops():
    choices = [{"value": backdrop, "label": backdrop} for backdrop in video_paths]
    return render_template(form_inputs_template, choices=choices)


@app.route("/get_subtitle_types")
def get_subtitle_types():
    choices = [{"value": subtype, "label": subtype} for subtype in subtitle_types]
    return render_template(form_inputs_template, choices=choices)


@app.route("/get_fonts")
def get_fonts():
    choices = [{"value": font, "label": font} for font in fonts]
    return render_template(form_inputs_template, choices=choices)


@app.route("/run", methods=["POST"])
def run():
    video_params = generate_video_params_dict(request.form)
    thread = Thread(target=runner, args=(video_params, characters_map))
    thread.start()

    unique_id = video_params['video_id']
    results_store[unique_id] = {"status": "started"}

    return render_template(result_template, result= results_store[unique_id])


def generate_video_params_dict(form_data):
    return {
        "video_id": str(uuid.uuid4()),
        "topic": form_data["topic"],
        "music": form_data["music"],
        "characters": [form_data["characters"]],
        "backdrop": form_data["backdrop"],
        "subtitle_type": form_data["subtitle_type"],
        "font": form_data["font"],
        "script_gen_model_name": config["settings"]["TEXT_MODEL_NAME"],
        "audio_gen_model_name": config["settings"]["AUDIO_MODEL_NAME"],
        "output_folder": config["settings"]["OUTPUT_FOLDER"],
        "audio_output_folder": f"{config["settings"]["OUTPUT_FOLDER"]}/samples",
        "subtitle_output_folder": f"{config["settings"]["OUTPUT_FOLDER"]}/subtitles",
        "reel_path": f'{config["settings"]["OUTPUT_FOLDER"]}/brainrot_kunst_{datetime.now().strftime("%d-%m-%H-%M")}.mp4',
    }


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config.ini")
    app.run()
