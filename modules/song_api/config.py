import json
import os
from modules.utils.runtime_paths import app_root

BASE_PATH = app_root()
DB_PATH = BASE_PATH / "data" / "db"
CONFIG_PATH = DB_PATH / "song_api_config.json"

DEFAULT_CONFIG = {
    "enabled": False,  # 🔥 по умолчанию выключено
    "api_url": "http://127.0.0.1:5858/generate",
    "min_amount": 100,
    "max_amount": 100
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
            data = json.load(f)
    except Exception:
        return DEFAULT_CONFIG.copy()

    # 🔥 авто-мерж новых полей
    merged = {**DEFAULT_CONFIG, **data}
    if merged != data:
        save_config(merged)

    return merged


def save_config(data: dict):
    _ensure()

    tmp_path = CONFIG_PATH.with_suffix(".tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    os.replace(tmp_path, CONFIG_PATH)