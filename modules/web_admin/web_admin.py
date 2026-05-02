import threading
import webbrowser
import time
import logging

from flask import render_template, request, redirect, url_for, flash, Flask

from modules.song_api.service import song_api_service
from modules.web_admin.config import get_host, get_port, get_base_url
from modules.cabinet.service import (
    get_api_key,
    set_api_key,
    get_audio_settings,
    get_output_devices,
    set_output_device
)
from modules.utils.runtime_paths import app_root
from modules.alerts.routes import bp as alerts_bp


log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

BASE_PATH = app_root()

app = Flask(
    __name__,
    template_folder=str(BASE_PATH / "templates"),
    static_folder=str(BASE_PATH / "static")
)

app.secret_key = "4e0f9d3d7c7c9a9c4f0e4a5e1e7d5c4e8f7c6a2b1d9f0a3c7e8b2d1f6a9c4e0b"

app.register_blueprint(alerts_bp)


@app.context_processor
def inject_base_url():
    return {"BASE_URL": get_base_url()}


# ======================================
# START WEB ADMIN
# ======================================

def start_web_admin():
    host = get_host()
    port = get_port()

    def _run():
        print(f"🌐 Web Admin running: http://{host}:{port}/")
        app.run(host=host, port=port, debug=False, use_reloader=False)

    th = threading.Thread(target=_run, daemon=True)
    th.start()

    time.sleep(1)

    try:
        webbrowser.open(f"http://{host}:{port}/")
    except Exception as e:
        print("Не удалось открыть браузер:", e)

    return th


# ======================================
# INDEX
# ======================================

@app.route("/", methods=["GET"])
def index():
    audio_cfg = get_audio_settings()
    song_api = song_api_service.get_settings()
    models_data = song_api_service.get_models_inventory()

    return render_template(
        "index.html",
        api_key=get_api_key(),
        output_devices=get_output_devices(),
        current_device=audio_cfg.get("output_device"),

        # 🔥 теперь всегда один TTS
        tts_engine="default",

        song_api=song_api,
        models_data=models_data
    )


# ======================================
# API KEY
# ======================================

@app.route("/save-api", methods=["POST"])
def save_api():
    api_key = request.form.get("api_key", "").strip()

    if not api_key:
        flash("API ключ не может быть пустым", "danger")
        return redirect(url_for("index"))

    set_api_key(api_key)
    flash("API ключ сохранён!", "success")
    return redirect(url_for("index"))


# ======================================
# AUDIO
# ======================================

@app.route("/save-audio", methods=["POST"])
def save_audio():
    device = (request.form.get("output_device") or "").strip()

    if not device:
        flash("Не выбрано устройство вывода", "danger")
        return redirect(url_for("index"))

    try:
        set_output_device(device)
    except Exception as e:
        flash(f"Ошибка сохранения: {e}", "danger")
        return redirect(url_for("index"))

    flash("Аудио устройство сохранено", "success")
    return redirect(url_for("index"))


# ======================================
# SONG API
# ======================================

@app.route("/save-song-api", methods=["POST"])
def save_song_api():
    try:
        enabled = request.form.get("enabled") == "on"
        api_url = (request.form.get("api_url") or "").strip()

        # 💰 донаты
        try:
            min_amount = float(request.form.get("min_amount") or 0)
        except:
            min_amount = 0

        try:
            max_amount = float(request.form.get("max_amount") or 0)
        except:
            max_amount = 999999

        # 🎵 жанры
        genres_raw = request.form.get("genres") or ""
        genres = [g.strip() for g in genres_raw.split("\n") if g.strip()]

        # 🎧 bpm
        bpm_raw = request.form.get("bpm_list") or ""
        try:
            bpm_list = [int(x.strip()) for x in bpm_raw.split(",") if x.strip()]
        except:
            bpm_list = []

        # ⏱ duration
        try:
            duration_min = int(request.form.get("duration_min") or 30)
        except:
            duration_min = 30

        try:
            duration_max = int(request.form.get("duration_max") or 120)
        except:
            duration_max = 120

        data = {
            "enabled": enabled,
            "api_url": api_url,
            "min_amount": min_amount,
            "max_amount": max_amount,

            # 🎵
            "genres": genres,

            # 🧠
            "model": (request.form.get("model") or "").strip(),
            "lm_model": (request.form.get("lm_model") or "").strip() or None,

            # 🎧
            "bpm_list": bpm_list,
            "timesignature": request.form.get("timesignature") or "4",

            # ⚙️
            "think": request.form.get("think") == "on",

            # ⏱
            "duration_min": duration_min,
            "duration_max": duration_max,
        }

        # 🔥 сохраняем
        song_api_service.update_settings(data)

        # 🔥 инициализируем модель
        song_api_service.init_model()

        flash("Song API сохранён 🎵🔥", "success")

    except Exception as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))