# RENAME THIS TO "personal.py"
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