# modules/client/audio/models.py

import json
from modules.utils.runtime_paths import app_root

BASE_PATH = app_root()
DB_PATH = BASE_PATH / "data" / "db"
CONFIG_PATH = DB_PATH / "client_audio.json"

DEFAULT_CONFIG = {
    "output_device": ""
}


def _ensure():
    DB_PATH.mkdir(parents=True, exist_ok=True)


def load_config():
    _ensure()

    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(data: dict):
    _ensure()

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)