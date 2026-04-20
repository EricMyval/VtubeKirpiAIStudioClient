import threading
import webbrowser
import time

from modules.song_api.service import song_api_service
from modules.tts.engine_loader import load_engine
from modules.web_admin.config import get_host, get_port, get_base_url
from flask import render_template, request, redirect, url_for, flash, Flask
from modules.cabinet.service import get_api_key, set_api_key, get_audio_settings, get_output_devices, set_output_device
from modules.tts.config import bootstrap_tts
from modules.utils.runtime_paths import app_root
from modules.tts.config import get_tts_config
from modules.alerts.routes import bp as alerts_bp
import logging

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
BASE_PATH = app_root()
app = Flask(__name__, template_folder=str(BASE_PATH / "templates"), static_folder=str(BASE_PATH / "static"))
app.secret_key = "4e0f9d3d7c7c9a9c4f0e4a5e1e7d5c4e8f7c6a2b1d9f0a3c7e8b2d1f6a9c4e0b"
app.register_blueprint(alerts_bp)

@app.context_processor
def inject_base_url():
    return {"BASE_URL": get_base_url() }

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

@app.route("/", methods=["GET"])
def index():
    audio_cfg = get_audio_settings()
    tts_cfg = get_tts_config()
    song_api = song_api_service.get_settings()
    return render_template(
        "index.html",
        api_key=get_api_key(),
        output_devices=get_output_devices(),
        current_device=audio_cfg.get("output_device"),
        tts_engine=tts_cfg.tts_engine,
        song_api=song_api
    )

@app.route("/save-api", methods=["POST"])
def save_api():
    api_key = request.form.get("api_key", "").strip()
    if not api_key:
        flash("API ключ не может быть пустым", "danger")
        return redirect(url_for("index"))
    set_api_key(api_key)
    try:
        bootstrap_tts()
    except Exception as e:
        flash(f"TTS ошибка: {e}", "warning")
    flash("API ключ сохранён", "success")
    return redirect(url_for("index"))


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

@app.route("/save-tts", methods=["POST"])
def save_tts():
    engine = (request.form.get("tts_engine") or "").strip()
    available_tts_engines = ["f5", "qwen3", "vibevoice", "voxcpm2", "omnivoice"]
    if engine not in available_tts_engines:
        flash("Неверный TTS движок", "danger")
        return redirect(url_for("index"))
    try:
        from modules.tts.config import update_tts_engine
        update_tts_engine(engine)
        load_engine()
        flash("TTS успешно переключен 🚀", "success")
    except Exception as e:
        flash(f"Ошибка переключения: {e}", "danger")
    return redirect(url_for("index"))

@app.route("/save-song-api", methods=["POST"])
def save_song_api():
    try:
        enabled = request.form.get("enabled") == "on"

        api_url = (request.form.get("api_url") or "").strip()

        try:
            min_amount = float(request.form.get("min_amount") or 0)
        except:
            min_amount = 0

        try:
            max_amount = float(request.form.get("max_amount") or 0)
        except:
            max_amount = 999999

        data = {
            "enabled": enabled,
            "api_url": api_url,
            "min_amount": min_amount,
            "max_amount": max_amount,
        }

        song_api_service.update_settings(data)

        flash("Song API сохранён 🎵", "success")

    except Exception as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("index"))