import json
import uuid
import time
from pathlib import Path

import requests

from modules.tts.config import get_tts_config

WORKFLOW_PATH = Path(
    "modules/tts/vibevoice_api.json"
)

OUTPUT_DIR = Path("data/out_voice")

_client_url = None
_loaded = False


def _load_workflow():

    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_url():

    cfg = get_tts_config()

    return cfg.vibevoice_comfyui_url


def tts_create_file(text: str, voice_file, voice_text) -> Path:

    comfy_url = _get_url()

    workflow = _load_workflow()

    workflow["11"]["inputs"]["text"] = text
    workflow["4"]["inputs"]["audio"] = Path(voice_file).name

    out_prefix = "audio/vibevoice_" + str(int(time.time()))

    workflow["3"]["inputs"]["filename_prefix"] = out_prefix

    client_id = str(uuid.uuid4())

    r = requests.post(
        f"{comfy_url}/prompt",
        json={"prompt": workflow, "client_id": client_id},
        timeout=30
    )

    if r.status_code != 200:
        raise RuntimeError(
            f"ComfyUI error {r.status_code}: {r.text}"
        )

    prompt_id = r.json()["prompt_id"]

    start = time.time()

    while True:

        if time.time() - start > 300:
            raise TimeoutError("VibeVoice generation timeout")

        h = requests.get(
            f"{comfy_url}/history/{prompt_id}",
            timeout=30
        )

        if h.status_code != 200:
            time.sleep(0.3)
            continue

        data = h.json()

        if prompt_id not in data:
            time.sleep(0.3)
            continue

        prompt_data = data[prompt_id]

        if "outputs" not in prompt_data:
            time.sleep(0.3)
            continue

        node = prompt_data["outputs"].get("3")

        if node and "audio" in node:

            audio_info = node["audio"][0]

            return _download_audio(
                comfy_url,
                audio_info
            )

        time.sleep(0.3)


def _download_audio(comfy_url, audio_info):

    params = {
        "filename": audio_info["filename"],
        "subfolder": audio_info.get("subfolder", ""),
        "type": audio_info.get("type", "output"),
    }

    r = requests.get(
        f"{comfy_url}/view",
        params=params,
        timeout=60
    )

    if r.status_code != 200:
        raise RuntimeError("ComfyUI audio download error")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename = audio_info["filename"]

    final_path = OUTPUT_DIR / filename

    with open(final_path, "wb") as f:
        f.write(r.content)

    return final_path


def load_vibevoicetts():

    global _loaded

    if not _loaded:

        print("[VibeVoiceTTS] ready")

        _loaded = True


def unload_vibevoicetts():

    global _loaded

    if _loaded:

        print("[VibeVoiceTTS] unloaded")

        _loaded = False

    return True