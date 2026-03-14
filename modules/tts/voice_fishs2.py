import re
import time
from pathlib import Path
import requests
from modules.tts.config import get_tts_config
from modules.utils.constant import transliterate_cyr_to_lat

OUTPUT_DIR = Path("data/out_voice")
_loaded = False
_added_references = set()

def _get_url():
    cfg = get_tts_config()
    return cfg.fishs2_url.rstrip("/")

def _get_reference_id(voice_file: str) -> str:
    name = Path(voice_file).stem
    name = transliterate_cyr_to_lat(name)
    name = name.replace(" ", "_")
    name = re.sub(r"[^a-z0-9\-_]", "", name)
    return name

def ensure_reference(voice_file):
    reference_id = _get_reference_id(voice_file)
    if reference_id in _added_references:
        return
    url = _get_url()
    with open(voice_file, "rb") as f:
        files = {
            "audio": f
        }
        data = {
            "id": reference_id,
            "text": "Привет, это мой голос"
        }
        r = requests.post(
            f"{url}/v1/references/add",
            files=files,
            data=data,
            timeout=60
        )
    if r.status_code == 200:
        print(f"[FishS2] reference added: {reference_id}")
    else:
        txt = r.text.lower()
        if "already exists" in txt:
            print(f"[FishS2] reference exists: {reference_id}")
        else:
            raise RuntimeError(r.text)
    _added_references.add(reference_id)

def tts_create_file(text, voice_file, voice_text):
    url = _get_url()
    text = format_tts(text)
    reference_id = _get_reference_id(voice_file)
    ensure_reference(voice_file)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"fishs2_{int(time.time())}.wav"
    payload = {
        "text": text,
        "reference_id": reference_id,
        "format": "wav",
        "temperature": 0.7,
        "top_p": 0.9,
        "repetition_penalty": 1.05,
        "chunk_length": 100,
        "use_memory_cache": "on"
    }
    r = requests.post(
        f"{url}/v1/tts",
        json=payload,
        timeout=300
    )
    if r.status_code != 200:
        raise RuntimeError(r.text)
    with open(output_path, "wb") as f:
        f.write(r.content)
    return output_path

def load_fishs2tts():
    global _loaded
    if not _loaded:
        print("[FishS2 TTS] ready")
        _loaded = True

def unload_fishs2tts():
    global _loaded
    if _loaded:
        print("[FishS2 TTS] unloaded")
        _loaded = False
    return True

def format_tts(text: str) -> str:
    text = text.strip()
    if not re.match(r'^\[[^\]]+voice\]', text):
        text = "[playful soft voice] " + text
    text = re.sub(r'\s*(\[[^\]]+voice\])', r'\n\1', text)
    return text.strip()