import sounddevice as sd
from faster_whisper import WhisperModel
import os, io, asyncio, glob, site
import edge_tts
import re

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" # Hides pygame support message
import pygame

pygame.mixer.init()

COMMANDS = {
    "open notepad": lambda: (speak("Opening Notepad"), os.startfile("notepad.exe")),
}

SAMPLE_RATE = 16000 # 16 KHz 
VOICE = "en-IE-ConnorNeural" # Voice. more in voices.md

# CPU is reccomended for smaller use (or no NVIDIA GPU)
model = WhisperModel("base.en", device="cpu", compute_type="int8") # CPU
# model = WhisperModel("medium", device="cuda", compute_type="float16") # GPU


# Generates text
async def _generate(text2):
    buf = io.BytesIO()
    communicate = edge_tts.Communicate(text2, VOICE, rate="-5%", pitch="-3Hz")
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    buf.seek(0)
    return buf

# Speaks the generated text
def speak(text2):
    buf = asyncio.run(_generate(text2))
    pygame.mixer.music.load(buf, "mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

# You can change seconds to record how long
def record(seconds=3):
    print("Listening...")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                   channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()

# Transcribes the audio from your microphone
# This uses your default windows microphone
def transcribe(audio):
    segments, _ = model.transcribe(audio, language="en", beam_size=5, vad_filter=True)
    return " ".join(s.text.strip() for s in segments)

# Removes "." from the transcripted text
def normalize(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


# Main loop
if __name__ == "__main__":
    while True:
        input("Press Enter to speak...")

        userSaid = normalize(transcribe(record()))
        print("heard:", repr(userSaid)) # DEBUG LINE - You can remove it if you want to

        for phrase, action in COMMANDS.items():
            if phrase in userSaid:
                action()
                break
        else:
            speak("Sorry, I didn't catch that.")
            