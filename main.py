import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"  # has to be before the pygame import or the banner still shows

import asyncio
import glob
import io
import re
import site
import webbrowser
from urllib.parse import quote_plus

import numpy as np
import sounddevice as sd
import edge_tts
import pygame

# personal.py is optional, it overrides stuff below and isn't on github
try:
    import personal
except ImportError:
    personal = None


def setting(name, default):
    return getattr(personal, name, default)


NAME = setting("NAME", "Jarvis")  # wake word
VOICE = setting("VOICE", "en-GB-RyanNeural")  # other voices are in voices.md
USE_GPU = setting("USE_GPU", False)  # needs nvidia + the cuda libs
USE_WAKE_WORD = setting("USE_WAKE_WORD", False)  # off = press enter to talk
WHISPER_MODEL = setting("WHISPER_MODEL", "medium" if USE_GPU else "base.en")
RECORD_SECONDS = setting("RECORD_SECONDS", 3)
SAMPLE_RATE = 16000  # whisper wants 16k

LOCAL = os.environ["LOCALAPPDATA"]
ROAMING = os.environ["APPDATA"]

# phrase: (what it says, what it opens)
APPS = {
    "open notepad": ("Opening Notepad", "notepad.exe"),
    "open spotify": ("Opening Spotify", rf"{ROAMING}\Spotify\Spotify.exe"),
    **setting("APPS", {}),
}

LINKS = {
    "open youtube": ("Opening YouTube", "https://www.youtube.com"),
    **setting("LINKS", {}),
}

# windows can't find the pip cuda dlls by itself so point it at them
# needs to happen before faster_whisper gets imported
if USE_GPU:
    for sp in site.getsitepackages():
        for bin_dir in glob.glob(os.path.join(sp, "nvidia", "*", "bin")):
            os.add_dll_directory(bin_dir)
            os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]

from faster_whisper import WhisperModel  # noqa: E402

if USE_GPU:
    model = WhisperModel(WHISPER_MODEL, device="cuda", compute_type="float16")
else:
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

pygame.mixer.init()


async def _generate(text):
    buf = io.BytesIO()
    communicate = edge_tts.Communicate(text, VOICE, rate="-5%", pitch="-3Hz")
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf


def speak(text):
    buf = asyncio.run(_generate(text))
    pygame.mixer.music.load(buf, "mp3")
    pygame.mixer.music.play()
    # wait until it's done talking so the mic doesn't hear it
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


def record(seconds=RECORD_SECONDS, quiet=False):
    # uses the default windows mic
    if not quiet:
        print("Listening...")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()


def is_loud(audio, threshold=0.01):
    return np.abs(audio).max() > threshold


def transcribe(audio):
    segments, _ = model.transcribe(audio, language="en", beam_size=5, vad_filter=True)
    return " ".join(s.text.strip() for s in segments)


# whisper adds capitals and punctuation, this gets rid of it so matching works
def normalize(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def _open_app(say, path):
    speak(say)
    os.startfile(path)


def _open_link(say, url):
    speak(say)
    webbrowser.open(url)


COMMANDS = {}
for _phrase, (_say, _path) in APPS.items():
    COMMANDS[_phrase] = lambda s=_say, p=_path: _open_app(s, p)  # s=/p= so each lambda keeps its own values
for _phrase, (_say, _url) in LINKS.items():
    COMMANDS[_phrase] = lambda s=_say, u=_url: _open_link(s, u)


def handle(user_said):
    if user_said.startswith("youtube search "):
        query = user_said.removeprefix("youtube play ")
        speak(f"Searching {query} on YouTube")
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
        return

    if user_said.startswith("search for "):
        query = user_said.removeprefix("search for ")
        speak(f"Searching for {query}")
        webbrowser.open(f"https://www.google.com/search?q={quote_plus(query)}")
        return

    for phrase, action in COMMANDS.items():
        if phrase in user_said:
            action()
            return

    speak("Sorry, I didn't catch that.")


def main():
    if USE_WAKE_WORD:
        wake = NAME.lower()
        print(f"Say '{NAME}' to wake me. Ctrl+C to quit.")
        while True:
            chunk = record(2, quiet=True)
            if not is_loud(chunk):
                continue  # nothing said, skip it

            heard = normalize(transcribe(chunk))
            if wake not in heard:
                continue

            # works for "jarvis open notepad" or just "jarvis" and then the command
            command = heard.split(wake, 1)[1].strip()
            if not command:
                speak("Yes?")
                command = normalize(transcribe(record(4)))

            print("command:", repr(command))
            handle(command)
    else:
        while True:
            input("Press Enter to speak...")
            user_said = normalize(transcribe(record()))
            print("heard:", repr(user_said))  # for debugging, delete if you want
            handle(user_said)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye!")