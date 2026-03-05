import json
from pathlib import Path

CONFIG_PATH = Path("web_admin_config.json")

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 27027
}


def load_config():

    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)

        return DEFAULT_CONFIG.copy()

    except Exception as e:
        print(f"[WEB_ADMIN] config load error: {e}")
        return DEFAULT_CONFIG.copy()


def get_host():
    return load_config().get("host", DEFAULT_CONFIG["host"])


def get_port():
    return load_config().get("port", DEFAULT_CONFIG["port"])


def get_base_url():

    cfg = load_config()

    host = cfg.get("host", DEFAULT_CONFIG["host"])
    port = cfg.get("port", DEFAULT_CONFIG["port"])

    return f"http://{host}:{port}"