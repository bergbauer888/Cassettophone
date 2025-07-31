# Cassettophone
A fully local self hosted Brainrot generator. No subscriptions (or internet) needed.
## Key Features:
- Producing Brainrot content with voice cloning, images and avatar overlays
- Customizable Aesthetics (backgrounds, fonts, background music, character avatars, etc)
- Prioritizing the usage of the GPU, especially in heavy operations such as audio generation.
- Processing and rendering done using ffmpeg instead of MoviePy.
- Ability to upload resources to a remote destination, facilitating working with a remote server.
## Demo
![Demo](https://github.com/bergbauer888/Cassettophone/blob/master/demo.gif?raw=true)
## Requirements
The application requires the end user to have Ollama, ffmpeg and uv installed (There is a docker image is on it's way! -- Note: MLX users are advised to run Ollama locally, in order to enable the full usage of GPU)

Useful links:
- [Installing ollama](https://github.com/ollama/ollama)
- [Installing ffmpeg](https://github.com/oop7/ffmpeg-install-guide)
- [Installing uv](https://docs.astral.sh/uv/getting-started/installation/)
## Steps to run the app:
Create a config.ini file (sample provided), then run the following commands:
``
uv venv --python 3.13.0
source .venv/bin/activate
uv sync
uv run brainrot_cli.py
alternatively*, just python3 brainrot_cli.py
```

After running the script, the video will be saved at the location specified by the OUTPUT_FOLDER configuration variable, and it will follow the naming pattern: *brainrot_kunst_**timestamp**.mp4* (example output path -> *culala/brainrot_kunst_08-07-09-16.mp4*)

Alternatively, if the GOKAPI_URL and GOKAPI_TOKEN configuration variables are set, the script will upload the resulting brainrot and display the download URL.
## Environment variables:
```
-- The app supports uploading to a remote source
GOKAPI_URL = link to [gokapi](https://github.com/Forceu/Gokapi) instance
GOKAPI_TOKEN = gokapi token
-- The app uses Zonos for audio cloning
AUDIO_MODEL_NAME = Zyphra/Zonos-v0.1-transformer
-- The app uses Ollama models
TEXT_MODEL_NAME = phi3:medium
OUTPUT_FOLDER = culala
-- The app downloads an image from a searx instance
SEARX_BASE_URL =
```
## Known bugs:
- While running the app, the script preview does not always fit on the screen
- The character avatar and voice get de-syncronyzed sometimes
- The "sentence" subtitle type might not work as expected with certain fonts
