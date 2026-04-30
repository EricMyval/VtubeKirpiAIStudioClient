import requests
import time

from modules.tts.config import get_tts_config
from modules.tts.engine_loader import get_url
from modules.tts.voice_vibevoice import tts_create_file as vibe_create
from modules.tts.voice_acestep import tts_create_file as ace_create


# =========================
# SERVICE CALL
# =========================

def call_tts_service(text, voice_file, voice_text):
    url = get_url() + "/generate"

    try:
        r = requests.post(
            url,
            json={
                "text": text,
                "voice_file": voice_file,
                "voice_text": voice_text
            },
            timeout=120,
            proxies={"http": None, "https": None}
        )

        if r.status_code != 200:
            print(f"[TTS SERVICE ERROR] HTTP {r.status_code}")
            return None

        data = r.json()
        return data.get("wav_path")

    except Exception as e:
        print("[TTS SERVICE ERROR]", e)
        return None


# =========================
# ENGINES
# =========================

ENGINES = {
    "vibevoice": vibe_create,
    "omnivoice": call_tts_service,
    "song_api": ace_create,
}


# =========================
# MAIN ENTRY
# =========================

def tts_create(text, voice_file, voice_text):
    engine = get_tts_config().tts_engine

    if engine not in ENGINES:
        raise RuntimeError(f"Unknown TTS engine: {engine}")

    start = time.time()

    path = ENGINES[engine](text, voice_file, voice_text)

    elapsed = time.time() - start
    print(f"[TTS] engine={engine} time={elapsed:.2f}s")

    return path