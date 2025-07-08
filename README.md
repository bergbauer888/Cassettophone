# Cassettophone
A fully local self hosted Brainrot generator. No subscriptions (or internet) needed.
##### README is WIP
## Steps to run the app:
- Create a config.ini file (sample provided)
- uv venv --python 3.13.0
- source .venv/bin/activate
- uv sync
- uv run main.py
- alternatively*, just python3 main.py


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
- When creating a reel, the video script does not always fit on the screen
- The character avatar and voice get de-syncronyzed sometimes
