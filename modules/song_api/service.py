import os
import uuid
import requests
from pathlib import Path

from modules.song_api.config import load_config, save_config


BASE_DIR = Path("data") / "song_api"
BASE_DIR.mkdir(parents=True, exist_ok=True)


class SongAPIService:

    def __init__(self):
        self.config = load_config()

    # =========================
    # 🔄 RELOAD CONFIG
    # =========================
    def reload(self):
        self.config = load_config()
        print("[SongAPI] 🔄 Config reloaded:", self.config)

    # =========================
    # ⚙️ GET SETTINGS
    # =========================
    def get_settings(self):
        return self.config

    # =========================
    # 💾 UPDATE SETTINGS (ВАЖНО)
    # =========================
    def update_settings(self, data: dict):
        try:
            # дефолты
            data.setdefault("enabled", False)
            data.setdefault("api_url", "")
            data.setdefault("min_amount", 0)
            data.setdefault("max_amount", 999999)

            # нормализация типов
            data["enabled"] = bool(data.get("enabled"))

            try:
                data["min_amount"] = float(data.get("min_amount", 0))
            except:
                data["min_amount"] = 0

            try:
                data["max_amount"] = float(data.get("max_amount", 999999))
            except:
                data["max_amount"] = 999999

            save_config(data)
            self.reload()

            print("[SongAPI] ✅ Settings saved:", data)

        except Exception as e:
            print("[SongAPI] ❌ Save failed:", e)

    # =========================
    # 🎯 CHECK ENABLED
    # =========================
    def is_enabled_for_amount(self, amount):
        try:
            amount = float(amount)
        except:
            return False

        if not self.config.get("enabled"):
            return False

        return self.config["min_amount"] <= amount <= self.config["max_amount"]

    # =========================
    # 🎵 GENERATE SONG
    # =========================
    def generate_song(self, text, voice_path=None, gender="male"):
        url = self.config.get("api_url")

        if not url:
            print("[SongAPI] ❌ No API URL")
            return None

        data = {
            "text": text,
            "gender": gender
        }

        files = None

        try:
            # =========================
            # 🎤 VOICE FILE
            # =========================
            if voice_path and os.path.exists(voice_path):
                files = {
                    "voice": open(voice_path, "rb")
                }

            print("[SongAPI] 🚀 Request to:", url)

            r = requests.post(
                url,
                data=data,
                files=files,
                timeout=300
            )

            # =========================
            # ❌ JSON ERROR
            # =========================
            if "application/json" in r.headers.get("content-type", ""):
                print("[SongAPI] ❌ API error:", r.text)
                return None

            # =========================
            # 💾 SAVE FILE
            # =========================
            filename = f"song_{uuid.uuid4().hex}.mp3"
            save_path = BASE_DIR / filename

            with open(save_path, "wb") as f:
                f.write(r.content)

            # =========================
            # 🧪 VALIDATION
            # =========================
            if not save_path.exists() or save_path.stat().st_size < 5000:
                print("[SongAPI] ❌ Broken file:", save_path)

                try:
                    save_path.unlink(missing_ok=True)
                except:
                    pass

                return None

            print("[SongAPI] ✅ File saved:", save_path)

            return str(save_path)

        except Exception as e:
            print("[SongAPI] ❌ Request failed:", e)
            return None

        finally:
            # 🔥 обязательно закрываем файл
            if files and "voice" in files:
                try:
                    files["voice"].close()
                except:
                    pass


# =========================
# 🚀 SINGLETON
# =========================
song_api_service = SongAPIService()