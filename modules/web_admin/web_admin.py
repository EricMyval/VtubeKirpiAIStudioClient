# modules/web_admin.py
import json
import threading
from pathlib import Path
from flask import render_template
from modules.web_admin import app

CONFIG_PATH = Path("web_admin_config.json")
DEFAULT_CONFIG = {"host": "127.0.0.1","port": 27027}

@app.route("/")
def index():
    return render_template("index.html")

def _load_config():
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"Ошибка загрузки конфига: {e}, используются настройки по умолчанию")
        return DEFAULT_CONFIG.copy()


def start_web_admin():
    config = _load_config()
    host = config.get("host", "127.0.0.1")
    port = config.get("port", 27027)
    def _run():
        print(f"🌐 Веб-интерфейс доступен по адресу: http://{host}:{port}/")
        app.run(host=host, port=port, debug=False, use_reloader=False)
    th = threading.Thread(target=_run, daemon=True)
    th.start()
    return th
