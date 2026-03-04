import json
import os
from threading import Lock

DB_PATH = "data/db/afk_settings.json"


class AFKSettings:
    def __init__(self):
        self._lock = Lock()
        self._data = {
            "auto_reply": True,
            "pause_alerts": True,
            "pause_tts": True
        }
        self._load()

    def _load(self):
        if not os.path.exists(DB_PATH):
            self._save()
            return

        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                self._data.update(json.load(f))
        except Exception:
            pass  # намеренно тихо, чтобы не валить сервис

    def _save(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with open(DB_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_all(self) -> dict:
        with self._lock:
            return dict(self._data)

    def set(self, key: str, value):
        with self._lock:
            self._data[key] = value
            self._save()

    def update(self, data: dict):
        with self._lock:
            self._data.update(data)
            self._save()

    def get(self, key: str, default=None):
        with self._lock:
            return self._data.get(key, default)


afk_settings = AFKSettings()
