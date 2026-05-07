import time
import requests
import random
from pathlib import Path
from modules.song_api.config import load_config
from modules.song_api.service import song_api_service

OUTPUT_DIR = Path("data/out_voice")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# API
# =========================

def _get_api():
    cfg = load_config()
    return "http://192.168.1.18:8001"


# =========================
# CREATE TASK
# =========================

def _create_task(song_payload: dict, voice_file=None):
    api = _get_api()
    files = {}
    file_handle = None
    try:
        if voice_file:
            file_handle = open(voice_file, "rb")
            files["reference_audio"] = file_handle
        songs = song_payload.get("songs") or {}
        text = song_payload.get("formatted_text") or ""
        caption = songs.get("genre") or "music"
        bpm = songs.get("bpm") or 120
        duration = songs.get("duration") or 60
        think = str(bool(songs.get("think"))).lower()
        timesignature = songs.get("timesignature") or "4"
        use_lm = songs.get("use_lm", False)
        data = {
            "caption": caption,
            "lyrics": text,
            "think": think,
            "bpm": str(bpm),
            "duration": str(duration),
            "timesignature": str(timesignature),
        }
        if use_lm:
            data["use_lm"] = "true"
        r = requests.post(
            f"{api}/release_task",
            data=data,
            files=files,
            timeout=60
        )
        result = r.json()
        if result.get("code") != 200:
            raise RuntimeError(f"ACE API error: {result}")
        return result["data"]["task_id"]
    finally:
        if file_handle:
            file_handle.close()


# =========================
# POLL RESULT
# =========================

def _poll_result(task_id, timeout=180):
    api = _get_api()
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError("ACE generation timeout")
        try:
            r = requests.post(
                f"{api}/query_result",
                json={"task_id_list": [task_id]},
                timeout=60
            )
            data = r.json()
        except Exception:
            time.sleep(1)
            continue
        if data.get("code") != 200:
            time.sleep(1)
            continue
        items = data.get("data", [])
        if not items:
            time.sleep(1)
            continue
        item = items[0]
        status = item.get("status")
        if status == 1:
            import json as _json
            try:
                songs = _json.loads(item.get("result", "[]"))
            except Exception:
                time.sleep(1)
                continue
            if songs:
                file_url = songs[0].get("file")

                if file_url:
                    return _download(file_url)
        elif status == 2:
            raise RuntimeError("ACE task failed")
        time.sleep(1)


# =========================
# DOWNLOAD
# =========================

def _download(url):
    api = _get_api()
    full_url = f"{api}{url}" if url.startswith("/") else url
    r = requests.get(full_url, timeout=60)
    if r.status_code != 200:
        raise RuntimeError("Download error")
    filename = f"ace_{int(time.time())}_{random.randint(1000,9999)}.mp3"
    path = OUTPUT_DIR / filename
    with open(path, "wb") as f:
        f.write(r.content)
    return path


# =========================
# MAIN ENTRY
# =========================

def tts_create_file(song_payload: dict, voice_file=None) -> Path:
    start = time.time()
    task_id = _create_task(song_payload, voice_file)
    path = _poll_result(task_id)
    print(f"[ACE TTS] done in {round(time.time() - start, 2)}s")
    return path


# =========================
# INIT
# =========================

def load_acetts():
    song_api_service.init_model()