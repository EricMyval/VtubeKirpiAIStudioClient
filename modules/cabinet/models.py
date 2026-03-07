import json
from modules.utils.runtime_paths import app_root

BASE_PATH = app_root()

DB_PATH = BASE_PATH / "data" / "db"
CONFIG_PATH = DB_PATH / "client_config.json"

DEFAULT_CONFIG = {
    "api_key": ""
}


def _ensure_db_folder():
    DB_PATH.mkdir(parents=True, exist_ok=True)


def load_config():
    _ensure_db_folder()

    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Ошибка загрузки client_config:", e)
        return DEFAULT_CONFIG.copy()


def save_config(data: dict):
    _ensure_db_folder()

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)