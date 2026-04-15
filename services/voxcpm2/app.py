from fastapi import FastAPI
from pydantic import BaseModel
import traceback
import os
from model import load_model, generate_wav

app = FastAPI()
load_model()

class TTSRequest(BaseModel):
    text: str
    voice_file: str | None = None
    voice_text: str | None = None

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/generate")
def generate(req: TTSRequest):
    voice_file = os.path.abspath(req.voice_file) if req.voice_file else None
    try:
        path = generate_wav(text=req.text, voice_file=voice_file, voice_text=req.voice_text)
        return { "wav_path": str(path) }
    except Exception as e:
        print("[TTS] ❌ ERROR:", e)
        traceback.print_exc()
        return { "error": str(e)}