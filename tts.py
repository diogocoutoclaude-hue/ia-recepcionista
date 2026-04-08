import io
import os
import wave
import httpx
from piper.voice import PiperVoice

PIPER_MODEL = os.path.join(os.path.dirname(__file__), "voices", "pt_PT-tugao-medium.onnx")

# Load once at import time — avoids reloading on every request
_piper_voice: PiperVoice | None = None

def _get_piper() -> PiperVoice:
    global _piper_voice
    if _piper_voice is None:
        _piper_voice = PiperVoice.load(PIPER_MODEL)
    return _piper_voice


def speak_piper(text: str) -> bytes:
    """Local Piper TTS — no network, near-instant, returns WAV bytes."""
    voice = _get_piper()
    buf = io.BytesIO()
    wav = wave.open(buf, "wb")
    voice.synthesize_wav(text, wav)
    wav.close()
    return buf.getvalue()