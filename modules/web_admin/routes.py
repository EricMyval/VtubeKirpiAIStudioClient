from flask import render_template, request, redirect, url_for, flash

from modules.web_admin import app

from modules.audio.service import (
    get_audio_settings,
    get_output_devices,
    set_output_device
)

from modules.cabinet.service import (
    get_api_key,
    set_api_key
)

from modules.tts.config import bootstrap_tts


# ==========================================================
# MAIN PAGE
# ==========================================================

@app.route("/", methods=["GET"])
def index():

    audio_cfg = get_audio_settings()

    return render_template(
        "index.html",
        api_key=get_api_key(),
        output_devices=get_output_devices(),
        current_device=audio_cfg.get("output_device", "")
    )


# ==========================================================
# SAVE API KEY
# ==========================================================

@app.route("/save-api", methods=["POST"])
def save_api():

    api_key = request.form.get("api_key", "").strip()

    set_api_key(api_key)

    bootstrap_tts()

    flash("API ключ сохранён", "success")

    return redirect(url_for("index"))


# ==========================================================
# SAVE AUDIO DEVICE
# ==========================================================

@app.route("/save-audio", methods=["POST"])
def save_audio():

    device = (request.form.get("output_device") or "").strip()

    if not device:
        flash("Не выбрано устройство вывода", "danger")
        return redirect(url_for("index"))

    try:
        set_output_device(device)
        flash("Аудио устройство сохранено", "success")

    except Exception as e:
        flash(f"Ошибка сохранения: {e}", "danger")

    return redirect(url_for("index"))