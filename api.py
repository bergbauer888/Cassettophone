import configparser

from flask import Flask, render_template, jsonify, request
from brainrot_cli import runner

from assets_params import (
    characters_map, music_choices, video_paths, subtitle_types, fonts
)
from threading import Thread

app = Flask('brainrot', template_folder='templates')
form_inputs_template = 'choices.html'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_music_choices')
def get_music_choices():
    choices = [{"value": choice, "label": choice} for choice in music_choices]
    return render_template(form_inputs_template, choices=choices)

@app.route('/get_characters')
def get_characters():
    characters = [character["display_name"] for character in characters_map.values()]
    choices = [{"value": character, "label": character} for character in characters]
    return render_template(form_inputs_template, choices=choices)

@app.route('/get_backdrops')
def get_backdrops():
    choices = [{"value": backdrop, "label": backdrop} for backdrop in video_paths]
    return render_template(form_inputs_template, choices=choices)

@app.route('/get_subtitle_types')
def get_subtitle_types():
    choices = [{"value": subtype, "label": subtype} for subtype in subtitle_types]
    return render_template(form_inputs_template, choices=choices)

@app.route('/get_fonts')
def get_fonts():
    choices = [{"value": font, "label": font} for font in fonts]
    return render_template(form_inputs_template, choices=choices)

@app.route('/run', methods=['POST'])
def run():
    video_params = request.form.to_dict()
    thread = Thread(target=runner, args=(video_params,characters_map))
    thread.start()
    return jsonify({"status": "started"})

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.ini")
    app.run(debug=True)