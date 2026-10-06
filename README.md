# Voice Launcher

A small Python voice assistant for Windows. Press Enter, say a command, and it transcribes your speech **locally** with [faster-whisper](https://github.com/SYSTRAN/faster-whisper), launches the matching app, and talks back using a neural text-to-speech voice.

```
You:      "Open Notepad"
Launcher: (replies "Opening Notepad" out loud, then opens Notepad)
```

## Features

- **Offline speech recognition** with faster-whisper (no API key, no audio leaves your PC)
- **Easy command system**: add a phrase and an action in one line
- **Spoken replies** using Microsoft's neural voices through `edge-tts`, with a British "Jarvis"-style voice
- **CPU or NVIDIA GPU** support
- **Forgiving matching**: punctuation and capitalisation are stripped, and a command can appear anywhere in the sentence

## How it works

```
Enter key → record 3s from mic → faster-whisper (speech to text)
          → normalise text → match against COMMANDS → run action
          → speak a reply (edge-tts → pygame)
```

1. `sounddevice` records a few seconds of mono 16 kHz audio.
2. faster-whisper transcribes it. `vad_filter=True` skips silence, which stops Whisper inventing text on quiet audio.
3. The text is lowercased and stripped of punctuation (`"Open Notepad."` becomes `"open notepad"`).
4. The first phrase in `COMMANDS` found inside the text runs its action.
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

pip install faster-whisper sounddevice numpy edge-tts pygame
```

The first run downloads the Whisper model (about 150 MB for `base.en`) from Hugging Face and caches it.

> **Tip:** keep the project outside OneDrive-synced folders (for example `C:\Projects\voice-launcher`). OneDrive can break `git init` and constantly tries to sync the `venv` folder.

## Usage

```
python main.py
```

Then:

1. Press **Enter** when you see `Press Enter to speak...`
2. Speak when it says `Listening...` (you have 3 seconds)
3. Watch the `heard:` line to see what it understood

## Adding your own commands

Commands live in the `COMMANDS` dictionary in `main.py`. The key is the phrase to listen for, and the value is a function to run.

```python
COMMANDS = {
    "open notepad":     lambda: (speak("Opening Notepad"), os.startfile("notepad.exe")),
    "open calculator":  lambda: (speak("Opening calculator"), os.startfile("calc.exe")),
    "launch minecraft": lambda: (speak("Launching Minecraft."), os.startfile(r"C:\Path\To\Launcher.exe")),
    "hello":            lambda: speak("Hello! How can I help?"),
}
```

- Use lowercase phrases with no punctuation.
- `os.startfile()` opens an app or file with its default handler.
- Use a raw string (`r"C:\..."`) for Windows paths so backslashes aren't treated as escape characters.
- For anything longer than one line, write a normal function and put its name in the dictionary:

```python
def open_project():
    speak("Opening your project")
    os.startfile(r"C:\Projects")

COMMANDS["open projects"] = open_project
```

## Configuration

### Whisper model and device

```python
# CPU (works everywhere)
model = WhisperModel("base.en", device="cpu", compute_type="int8")

# NVIDIA GPU
model = WhisperModel("small.en", device="cuda", compute_type="float16")
```

| Model | Speed | Accuracy | Notes |
|---|---|---|---|
| `tiny.en` / `base.en` | Very fast | Good for short commands | Fine on CPU |
| `small.en` | Fast | Better | Still fine on CPU |
| `medium` / `large-v3` | Slower | Best | Wants a GPU |

### Recording length

```python
def record(seconds=3):
```

Increase `seconds` if your commands get cut off.

### Voice

Set the voice at the top of the speech code:

```python
VOICE = "en-GB-RyanNeural"
```

Good options for a butler / "Jarvis" feel:

| Voice | Accent | Gender |
|---|---|---|
| `en-GB-RyanNeural` | British | Male |
| `en-GB-ThomasNeural` | British | Male |
| `en-US-GuyNeural` | American | Male |
| `en-US-AndrewNeural` | American | Male |

List every available voice:

```
edge-tts --list-voices
```

You can also tune the sound with `rate` and `pitch`:

```python
edge_tts.Communicate(text, VOICE, rate="-5%", pitch="-3Hz")
```

## GPU setup (optional)

To run Whisper on an NVIDIA GPU, install the CUDA libraries into your venv:

```
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

Windows won't find the DLLs automatically, so add this to the **very top** of `main.py`, before importing `faster_whisper`:

```python
import os, glob, site

for sp in site.getsitepackages():
    for bin_dir in glob.glob(os.path.join(sp, "nvidia", "*", "bin")):
        os.add_dll_directory(bin_dir)
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]
```

Then switch the model line to `device="cuda"`. If it still fails, update your NVIDIA driver.

## Troubleshooting

| Problem | Fix |
|---|---|
| `RuntimeError: Library cublas64_12.dll is not found` | You're running on `cuda` without the CUDA libraries. Use `device="cpu"` or follow the GPU setup above. |
| Command never triggers | Check the `heard:` line. Whisper may have misheard you, or the phrase in `COMMANDS` doesn't match. Phrases must be lowercase with no punctuation. |
| `heard: ''` (empty) | The mic isn't picking up audio. Run `python -c "import sounddevice as sd; print(sd.query_devices())"` and set `sd.default.device = <index>`. |
| Phrases lose their spaces (`launchminecraft`) | Your `normalize()` regex is deleting spaces. It should be `[^a-z0-9 ]` (note the space). |
| `Warning: unauthenticated requests to the HF Hub` | Harmless. Set a free `HF_TOKEN` for faster downloads, or ignore it. |
| Symlink warning from `huggingface_hub` | Harmless on Windows. Set `HF_HUB_DISABLE_SYMLINKS_WARNING=1` to hide it. |
| `pip` warning about `click` versions | Harmless. Neither package's command-line tools are used here. |
| `git init` fails inside OneDrive | Move the project out of OneDrive (see the install tip). |

## Project structure

```
voice-launcher/
├── main.py          # recording, transcription, commands, speech
├── .gitignore       # keeps venv/ and secrets out of git
└── README.md
```

## Tech used

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for speech-to-text
- [sounddevice](https://python-sounddevice.readthedocs.io/) for microphone recording
- [edge-tts](https://github.com/rany2/edge-tts) for text-to-speech
- [pygame](https://www.pygame.org/) for audio playback

## Ideas for later

- Push-to-talk with a global hotkey instead of pressing Enter
- A wake word ("Jarvis, ...")
- Fuzzy matching with `difflib.get_close_matches` for misheard commands
- Say-to-switch voices
- Caching common replies so they play instantly

## License

Add a license of your choice (for example MIT) before publishing.