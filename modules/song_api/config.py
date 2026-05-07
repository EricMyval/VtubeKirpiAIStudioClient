import json
import os
from modules.utils.runtime_paths import app_root

BASE_PATH = app_root()
DB_PATH = BASE_PATH / "data" / "db"
CONFIG_PATH = DB_PATH / "song_api_config.json"


# =========================
# DEFAULT
# =========================

DEFAULT_CONFIG = {
    "api_url": "http://127.0.0.1:8001",
    "model": "acestep-v15-turbo",
    "lm_model": None,
}


# =========================
# INTERNAL
# =========================

def _ensure():
    DB_PATH.mkdir(parents=True, exist_ok=True)


# =========================
# LOAD
# =========================

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

    # merge с дефолтом
    merged = {**DEFAULT_CONFIG, **data}

    # =========================
    # FIXES
    # =========================

    # api_url fallback
    if not merged.get("api_url"):
        merged["api_url"] = DEFAULT_CONFIG["api_url"]

    # lm_model → None если пусто
    if not merged.get("lm_model"):
        merged["lm_model"] = None

    # model fallback (на всякий)
    if not merged.get("model"):
        merged["model"] = DEFAULT_CONFIG["model"]

    # =========================

    if merged != data:
        save_config(merged)

    return merged


# =========================
# SAVE
# =========================

def save_config(data: dict):
    _ensure()

    clean = {
        "api_url": (data.get("api_url") or DEFAULT_CONFIG["api_url"]).strip(),
        "model": (data.get("model") or DEFAULT_CONFIG["model"]).strip(),
        "lm_model": (data.get("lm_model") or None),
    }

    tmp_path = CONFIG_PATH.with_suffix(".tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=4, ensure_ascii=False)

    os.replace(tmp_path, CONFIG_PATH)