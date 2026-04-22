import json
import os
from modules.utils.runtime_paths import app_root

BASE_PATH = app_root()
DB_PATH = BASE_PATH / "data" / "db"
CONFIG_PATH = DB_PATH / "song_api_config.json"


DEFAULT_CONFIG = {
    # 🔌 включение
    "enabled": False,

    # 🌐 API
    "api_url": "http://127.0.0.1:8001",

    # 💰 донаты
    "min_amount": 100,
    "max_amount": 100,

    # 🎵 ЖАНРЫ
    "genres": [
        "brutal deathcore, ultra heavy guitars, breakdowns",
        "dark cyberpunk synthwave, atmospheric, deep bass",
        "epic cinematic orchestral, trailer music"
    ],

    # 🧠 МОДЕЛИ
    "model": "acestep-v15-turbo",
    "lm_model": None,

    # 🎧 АУДИО
    "bpm_list": [180, 200, 220, 240],
    "timesignature": "4",

    # ⚙️ ПОВЕДЕНИЕ
    "think": True,

    # ⏱ ДЛИТЕЛЬНОСТЬ
    "duration_min": 30,
    "duration_max": 120
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

    merged = {**DEFAULT_CONFIG, **data}

    # =========================
    # TYPE FIXES
    # =========================

    # genres
    if not isinstance(merged.get("genres"), list):
        merged["genres"] = DEFAULT_CONFIG["genres"]

    # bpm
    if not isinstance(merged.get("bpm_list"), list):
        merged["bpm_list"] = DEFAULT_CONFIG["bpm_list"]

    # think
    merged["think"] = bool(merged.get("think"))

    # lm_model ("" → None)
    if not merged.get("lm_model"):
        merged["lm_model"] = None

    # duration
    try:
        merged["duration_min"] = int(merged.get("duration_min"))
    except:
        merged["duration_min"] = DEFAULT_CONFIG["duration_min"]

    try:
        merged["duration_max"] = int(merged.get("duration_max"))
    except:
        merged["duration_max"] = DEFAULT_CONFIG["duration_max"]

    # =========================

    if merged != data:
        save_config(merged)

    return merged


def save_config(data: dict):
    _ensure()

    # =========================
    # NORMALIZATION
    # =========================

    # genres textarea → list
    if "genres" in data and isinstance(data["genres"], str):
        data["genres"] = [
            g.strip()
            for g in data["genres"].split("\n")
            if g.strip()
        ]

    # bpm "180,200" → list[int]
    if "bpm_list" in data and isinstance(data["bpm_list"], str):
        try:
            data["bpm_list"] = [
                int(x.strip())
                for x in data["bpm_list"].split(",")
                if x.strip()
            ]
        except:
            data["bpm_list"] = DEFAULT_CONFIG["bpm_list"]

    # пустой lm → None
    if not data.get("lm_model"):
        data["lm_model"] = None

    # =========================

    tmp_path = CONFIG_PATH.with_suffix(".tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    os.replace(tmp_path, CONFIG_PATH)


# =========================
# HELPERS
# =========================

def get_random_genre(cfg: dict) -> str:
    import random
    genres = cfg.get("genres") or []
    if not genres:
        return "epic cinematic music"
    if len(genres) == 1:
        return genres[0]
    return random.choice(genres)


def get_random_bpm(cfg: dict) -> int:
    import random
    bpm_list = cfg.get("bpm_list") or DEFAULT_CONFIG["bpm_list"]
    if not bpm_list:
        bpm_list = DEFAULT_CONFIG["bpm_list"]
    return random.choice(bpm_list)


def calc_duration(cfg: dict, text: str) -> int:
    base = int(len(text) / 3)
    return max(
        cfg.get("duration_min", 30),
        min(cfg.get("duration_max", 120), base)
    )