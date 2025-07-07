# Cassettophone
##### WIP
## Steps to run the app:

- uv venv --python 3.11.0
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
