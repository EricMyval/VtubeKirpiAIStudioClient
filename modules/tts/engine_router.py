import requests
from modules.tts.config import get_tts_config
from modules.tts.voice_vibevoice import tts_create_file as vibe_create
from modules.tts.voice_acestep import tts_create_file as ace_create
import time

def call_tts_service(text, voice_file, voice_text):
    try:
        r = requests.post(
            "http://127.0.0.1:5001/generate",
            json={ "text": text, "voice_file": voice_file, "voice_text": voice_text},
            timeout=120,
            proxies={"http": None, "https": None}
        )
        return r.json().get("wav_path")
    except Exception as e:
        print("[TTS SERVICE ERROR]", e)
        return None

ENGINES = {
    "vibevoice": vibe_create,
    "omnivoice": call_tts_service,
    "song_api": ace_create,
}

def tts_create(text, voice_file, voice_text):
    engine = get_tts_config().tts_engine
    if engine not in ENGINES:
        raise RuntimeError(f"Unknown TTS engine: {engine}")
    start = time.time()
    path = ENGINES[engine](text, voice_file, voice_text)
    elapsed = time.time() - start
    print(f"[TTS] engine={engine} time={elapsed:.2f}s")
    return path