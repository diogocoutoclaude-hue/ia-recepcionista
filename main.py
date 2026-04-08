import os
import struct
import wave
from dotenv import load_dotenv
load_dotenv()

import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from groq import Groq

import receptionist
import storage
import tts

app = FastAPI(title="AI Receptionist")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str


class SpeakRequest(BaseModel):
    text: str
    provider: str        # "piper" | "elevenlabs"
    voice_id: str = ""  # optional ElevenLabs voice override


# ---------------------------------------------------------------------------
# Audio normalization — boost quiet recordings before sending to Whisper
# ---------------------------------------------------------------------------

def normalize_wav(path: str, target_peak: float = 0.9) -> str:
    """Peak-normalize a 16-bit WAV file in-place and return the path."""
    try:
        with wave.open(path, "rb") as wf:
            params = wf.getparams()
            if params.sampwidth != 2:  # only handle 16-bit
                return path
            raw = wf.readframes(params.nframes)

        n_samples = len(raw) // 2
        if n_samples == 0:
            return path

        samples = list(struct.unpack(f"<{n_samples}h", raw))

        peak = max(abs(s) for s in samples) if samples else 0
        if peak == 0:
            return path

        gain = (32767 * target_peak) / peak
        if gain <= 1.05:  # already loud enough
            return path

        samples = [max(-32768, min(32767, int(s * gain))) for s in samples]
        normalized = struct.pack(f"<{n_samples}h", *samples)

        with wave.open(path, "wb") as wf:
            wf.setparams(params)
            wf.writeframes(normalized)
    except Exception:
        pass  # if normalization fails, just send the original
    return path


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY não configurada")
    try:
        reply = receptionist.chat([m.model_dump() for m in req.messages])
        return ChatResponse(reply=reply)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY não configurada")
    try:
        contents = await audio.read()
        suffix = ".wav" if "wav" in (audio.content_type or "") or (audio.filename or "").endswith(".wav") else ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        # Normalize audio volume (boosts quiet recordings)
        if suffix == ".wav":
            normalize_wav(tmp_path)

        # Domain prompt — guides Whisper vocabulary for pt-PT accent / dental terms
        from config import BUSINESS_NAME, FAQS
        faq_terms = " ".join(faq["question"] for faq in FAQS)
        whisper_prompt = (
            f"Transcrição de uma chamada para o {BUSINESS_NAME}. "
            f"O cliente fala em português de Portugal. "
            f"Termos frequentes: reserva, marcação, quarto, alojamento, estadia, check-in, check-out, "
            f"pequeno-almoço, piscina, spa, wi-fi, estacionamento, cancelamento, alterar, "
            f"receção, disponibilidade, noite, casal, individual, cama. "
            f"{faq_terms}"
        )

        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=(audio.filename or f"audio{suffix}", f),
                response_format="text",
                language="pt",
                prompt=whisper_prompt,
                temperature=0.0,
            )
        os.unlink(tmp_path)
        return {"text": result.strip() if isinstance(result, str) else result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat-speak/piper")
async def chat_speak_piper(req: ChatRequest):
    """Combined endpoint: LLM reply → Piper TTS (local, fast) in one round trip."""
    from urllib.parse import quote
    import asyncio

    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY não configurada")

    try:
        reply = receptionist.chat([m.model_dump() for m in req.messages])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        audio = await asyncio.get_event_loop().run_in_executor(None, tts.speak_piper, reply)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    headers = {"X-Reply-Text": quote(reply), "Access-Control-Expose-Headers": "X-Reply-Text"}
    return Response(content=audio, media_type="audio/wav", headers=headers)


@app.get("/appointments")
async def get_appointments():
    return storage.list_appointments()


@app.get("/leads")
async def get_leads():
    return storage.list_leads()


class ContactRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    company: str
    industry: str
    website: str = ""
    message: str = ""


@app.post("/contact")
async def contact_form(req: ContactRequest):
    """Handle contact form submissions from landing page"""
    import json
    from datetime import datetime

    # Log the contact to a file
    contact_data = {
        "timestamp": datetime.now().isoformat(),
        "first_name": req.first_name,
        "last_name": req.last_name,
        "email": req.email,
        "phone": req.phone,
        "company": req.company,
        "industry": req.industry,
        "website": req.website,
        "message": req.message
    }

    # Append to contacts log file
    try:
        with open("contacts.jsonl", "a") as f:
            f.write(json.dumps(contact_data, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Error logging contact: {e}")

    # TODO: Send email notification to comercial@ia-recepcionista.com
    # You can add email sending here later using SMTP or SendGrid

    return {"status": "success", "message": "Contacto recebido com sucesso"}


# ---------------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def index():
    """Serve the landing page"""
    return FileResponse("frontend/landing.html")


@app.get("/demo")
async def demo():
    """Serve the interactive demo (redirect to voice-only version)"""
    return FileResponse("frontend/demo-voice.html")


@app.get("/demo-voice")
async def demo_voice():
    """Serve the voice-only demo (public facing)"""
    return FileResponse("frontend/demo-voice.html")


@app.get("/demo-full")
async def demo_full():
    """Serve the full demo with text chat (for testing)"""
    return FileResponse("frontend/demo.html")
