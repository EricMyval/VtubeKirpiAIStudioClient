from fastapi import FastAPI
from pydantic import BaseModel
import traceback
import os
import time

from model import load_model, generate_wav

app = FastAPI()


# ======================================
# STARTUP (FIX: безопасная загрузка модели)
# ======================================

@app.on_event("startup")
def startup_event():
    print("[OmniVoice] startup loading...")

    for attempt in range(3):
        try:
            load_model()
            print("[OmniVoice] startup OK")
            return
        except Exception as e:
            print(f"[OmniVoice] startup failed (attempt {attempt+1}):", e)
            time.sleep(1)

    # если даже после retry не загрузилось — падаем
    raise RuntimeError("Model failed to load on startup")


# ======================================
# REQUEST MODEL
# ======================================

class TTSRequest(BaseModel):
    text: str
    voice_file: str | None = None
    voice_text: str | None = None


# ======================================
# HEALTHCHECK
# ======================================

@app.get("/")
def health():
    return {"status": "ok"}


# ======================================
# GENERATE
# ======================================

@app.post("/generate")
def generate(req: TTSRequest):
    voice_file = os.path.abspath(req.voice_file) if req.voice_file else None

    try:
        path = generate_wav(
            text=req.text,
            voice_file=voice_file,
            voice_text=req.voice_text
        )

        return {"wav_path": str(path)}

    except Exception as e:
        print("[TTS] ❌ ERROR:", e)
        traceback.print_exc()
        return {"error": str(e)}