# Voice Launcher

A small Python voice assistant for Windows. Say a command, and it transcribes your speech **locally** with [faster-whisper](https://github.com/SYSTRAN/faster-whisper), launches the matching app or website, and talks back using a neural text-to-speech voice.

```
You:      "Open Notepad"
Launcher: (says "Opening Notepad" out loud, then opens Notepad)
```

## Features

- **Offline speech recognition** with faster-whisper (no API key, no audio leaves your PC)
- **Two ways to talk to it**: press Enter to speak, or turn on a wake word ("Jarvis, open Notepad")
- **Easy command system**: add an app or a link in one line
- **Open apps and web links** (`os.startfile` and the `webbrowser` module)
- **YouTube search by voice**: "youtube play lofi beats" opens the results page
- **Google search by voice**: "search for python tutorials"
- **Spoken replies** using Microsoft's neural voices through `edge-tts`, with a British "Jarvis"-style voice
- **CPU or NVIDIA GPU** support with a single setting
- **Forgiving matching**: punctuation and capitalisation are stripped, and a command can appear anywhere in the sentence
- **No hardcoded usernames.** App paths are built from Windows environment variables, so nothing personal ends up in the repo

## How it works

```
Enter key (or wake word) → record from mic → faster-whisper (speech to text)
                         → normalise text → handle() → run the action
                         → speak a reply (edge-tts → pygame)
```

1. `sounddevice` records a few seconds of mono 16 kHz audio from your default microphone.
2. faster-whisper transcribes it. `vad_filter=True` skips silence, which stops Whisper inventing text on quiet audio.
3. The text is lowercased and stripped of punctuation (`"Open Notepad."` becomes `"open notepad"`).
4. `handle()` checks for `youtube play ...` and `search for ...` first, then looks for the first phrase from your commands that appears in the text.
5. If nothing matches, the assistant says it didn't catch that.

## Requirements

- Windows 10/11
- Python 3.10 or newer
- A working microphone
- Internet connection for the spoken replies (edge-tts generates audio online). Speech recognition itself works offline once the model has downloaded.
- Optional: an NVIDIA GPU for faster transcription with larger models

## Installation

```
git clone https://github.com/YOUR_USERNAME/voice-launcher.git
cd voice-launcher

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

The first run downloads the Whisper model (about 150 MB for `base.en`) from Hugging Face and caches it.

> Larger models need more storage and take longer to download.

## Usage

```
python main.py
```

By default it's push-to-talk:

1. Press **Enter** when you see `Press Enter to speak...`
2. Speak when it says `Listening...` (you have 3 seconds)
3. Watch the `heard:` line to see what it understood

### Built-in commands

| Say | What happens |
|---|---|
| "open notepad" | Opens Notepad |
| "open spotify" | Opens Spotify (default install path) |
| "open youtube" | Opens youtube.com |
| "youtube play `<anything>`" | Searches YouTube for it |
| "search for `<anything>`" | Searches Google for it |

### Wake word mode

Set `USE_WAKE_WORD = True` and the assistant listens continuously instead of waiting for Enter. Say the wake word followed by a command:

- "Jarvis, open Notepad" (all in one go), or
- "Jarvis" and wait for it to say "Yes?", then say the command

The wake word is `NAME` in the settings (default `Jarvis`), so you can call it whatever you like. Whisper only transcribes sound above a volume threshold, which keeps GPU/CPU use down while it's idle.

## Settings

Everything you'll want to change is near the top of `main.py`:

| Setting | Default | What it does |
|---|---|---|
| `NAME` | `"Jarvis"` | Wake word, used when `USE_WAKE_WORD` is on |
| `VOICE` | `"en-GB-RyanNeural"` | Text-to-speech voice (see `voices.md`) |
| `USE_GPU` | `False` | Run Whisper on an NVIDIA GPU |
| `USE_WAKE_WORD` | `False` | `False` = press Enter, `True` = say the wake word |
| `WHISPER_MODEL` | `base.en` (CPU) / `medium` (GPU) | Which Whisper model to load |
| `RECORD_SECONDS` | `3` | How long to record after pressing Enter. Raise it if commands get cut off |

| Model | Speed | Accuracy | Notes |
|---|---|---|---|
| `tiny.en` / `base.en` | Very fast | Good for short commands | Fine on CPU |
| `small.en` | Fast | Better | Still fine on CPU |
| `medium` / `large-v3` | Slower | Best | Wants a GPU |

## Adding your own commands

Apps and websites are plain dictionaries in `main.py`. The key is the phrase to listen for, and the value is `(what it says, what it opens)`.

```python
APPS = {
    "open notepad": ("Opening Notepad", "notepad.exe"),
    "open calculator": ("Opening calculator", "calc.exe"),
    "open steam": ("Opening Steam", r"C:\Program Files (x86)\Steam\steam.exe"),
}

LINKS = {
    "open github": ("Opening GitHub", "https://www.github.com"),
}
```

- Use lowercase phrases with no punctuation.
- Use a raw string (`r"C:\..."`) for Windows paths so backslashes aren't treated as escape characters.
- For paths inside your user folder, use `LOCAL` (`%LOCALAPPDATA%`) or `ROAMING` (`%APPDATA%`) instead of typing your username:

```python
"open vs code": ("Opening Visual Studio Code", rf"{LOCAL}\Programs\Microsoft VS Code\Code.exe"),
```

- For anything more complicated than opening one thing, write a normal function and add it to `COMMANDS` after the dictionaries are built:

```python
def open_project():
    speak("Opening your project")
    os.startfile(r"C:\Projects")

COMMANDS["open projects"] = open_project
```

### Keeping personal settings out of the repo

Rename the file called `default_personal.py` to `personal.py`. If it exists, anything defined in it overrides the defaults, and its `APPS` and `LINKS` are added to the built-in ones.

```python
# personal.py
# Personal settings. Add this file to .gitignore.
# Anything defined here overrides the defaults in main.py.
import os

LOCAL = os.environ["LOCALAPPDATA"]

VOICE = "en-GB-ThomasNeural"
USE_GPU = True
WHISPER_MODEL = "medium"
NAME = "Python"
USE_WAKE_WORD = True
RECORD_SECONDS = 3

# phrase -> (what it says, what it opens)
APPS = {
    "open vs code": ("Opening Visual Studio Code", rf"{LOCAL}\Programs\Microsoft VS Code\Code.exe"),
    "open visual studio code": ("Opening Visual Studio Code", rf"{LOCAL}\Programs\Microsoft VS Code\Code.exe"),
}

LINKS = {
    "open the repository": ("Opening my repo on github", "https://www.github.com/xktech/VoiceLauncher-WINDOWS/"),
}
```

## Voices

Good options for a butler / "Jarvis" feel:

| Voice | Accent | Gender |
|---|---|---|
| `en-GB-RyanNeural` | British | Male |
| `en-GB-ThomasNeural` | British | Male |
| `en-US-GuyNeural` | American | Male |
| `en-US-AndrewNeural` | American | Male |

See `voices.md` for the full list, or run:

```
edge-tts --list-voices
```

You can also tune how it sounds with `rate` and `pitch` in `_generate()`:

```python
edge_tts.Communicate(text, VOICE, rate="-5%", pitch="-3Hz")
```

## GPU setup (optional)

1. Install the CUDA libraries into your venv:

```
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

2. Set `USE_GPU = True` (in `main.py` or your `personal.py`).

That's it. When `USE_GPU` is on, `main.py` points Windows at the pip-installed CUDA DLLs before loading Whisper, so you don't need to do anything with your PATH. If it still fails, update your NVIDIA driver.

## Troubleshooting

| Problem | Fix |
|---|---|
| `RuntimeError: Library cublas64_12.dll is not found` | `USE_GPU` is on but the CUDA libraries aren't installed. Run the `pip install` in the GPU setup above, or set `USE_GPU = False`. |
| Command never triggers | Check the `heard:` line. Whisper may have misheard you, or the phrase doesn't match. Phrases must be lowercase with no punctuation. Adding the misheard version as a second phrase works fine. |
| `heard: ''` (empty) | The mic isn't picking up audio. Run `python -c "import sounddevice as sd; print(sd.query_devices())"` and set `sd.default.device = <index>`. |
| Wake word isn't picked up | Check what Whisper heard (turn on the print in wake mode) and say it clearly. Unusual names get misheard more often. |
| `Warning: unauthenticated requests to the HF Hub` | Harmless. Set a free `HF_TOKEN` for faster downloads, or ignore it. |
| Symlink warning from `huggingface_hub` | Harmless on Windows. Set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` to hide it. |


## Tech used

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for speech-to-text
- [sounddevice](https://python-sounddevice.readthedocs.io/) for microphone recording
- [edge-tts](https://github.com/rany2/edge-tts) for text-to-speech
- [pygame](https://www.pygame.org/) for audio playback

## Ideas for later

- Push-to-talk with a global hotkey
- A dedicated wake word detector (like openWakeWord) instead of using Whisper
- Fuzzy matching so misheard commands still work
- Say-to-switch voices
- Caching common replies so they play instantly

## License

MIT. See [LICENSE](LICENSE).