"""
Optional voice input/output.
- Speech-to-text: uses SpeechRecognition (Google Web Speech API by default, free/no key).
- Text-to-speech: uses gTTS to produce an MP3 the frontend can play back.

These are optional convenience features - the app works fully without them.
"""
import io
import uuid
import os
import speech_recognition as sr
from gtts import gTTS

from backend.config import settings

TTS_OUTPUT_DIR = os.path.join(settings.UPLOAD_DIR, "..", "tts_output")
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


def transcribe_audio(audio_bytes: bytes, filename_hint: str = "audio.wav") -> str:
    """
    Transcribe uploaded audio bytes to text.
    Expects WAV format for best compatibility (frontend should record/convert to WAV).
    """
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        raise RuntimeError(f"Speech recognition service error: {e}")


def synthesize_speech(text: str, lang: str = "en") -> str:
    """
    Convert text to speech and save as an MP3 file. Returns the file path.
    """
    tts = gTTS(text=text, lang=lang)
    out_path = os.path.join(TTS_OUTPUT_DIR, f"{uuid.uuid4().hex}.mp3")
    tts.save(out_path)
    return out_path
