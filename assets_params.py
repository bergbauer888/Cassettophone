from utils import list_files_in_dir
from questionary import Style

characters_map = {
    "joe_biden": {
        "display_name": "Joe Biden",
        "audio_sample_path": "audio_samples/joebidenaudio.mp3",
        "avatar_path": "characters/JOE_BIDEN.png",
    },
    "kamala_harris": {
        "display_name": "Kamala Harris",
        "audio_sample_path": "audio_samples/kamala.mp3",
        "avatar_path": "characters/KAMALA_HARRIS.png",
    },
    "donald_trump": {
        "display_name": "Donald Trump",
        "audio_sample_path": "audio_samples/trumpaudio.mp3",
        "avatar_path": "characters/DONALD_TRUMP.png",
    },
}

video_paths = [f"backdrop/{video}" for video in list_files_in_dir("backdrop")]

subtitle_types = ["word", "sentence"]

results_store = {}

fonts = [
    "Wiener Melange",
    "Permanent Marker",
    "Archivo Black",
    "Bebas Neue",
    "Jersey 10",
    "VT323",
]

music_choices = [f"music/{music}" for music in list_files_in_dir("music")]

text_color = "fg:#CCFFFF"
text_color_pixel = "\033[96m"

cli_styling = Style(
    [
        ("qmark", text_color),
        ("question", text_color),
        ("answer", text_color),
        ("pointer", text_color),
        ("selected", text_color),
        ("highlighted", text_color),
        ("checkbox", text_color),
        ("separator", text_color),
        ("instruction", text_color),
        ("text", text_color),
        ("disabled", text_color),
        ("choice", text_color),
    ]
)
qmark_styling = ""
