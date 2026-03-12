from flask import render_template, request, redirect, url_for, flash
from modules.web_admin import app
from modules.cabinet.service import (
    get_api_key,
    set_api_key,
    get_audio_settings,
    get_output_devices,
    set_output_device
)
from modules.tts.config import bootstrap_tts


@app.route("/", methods=["GET"])
def index():
    audio_cfg = get_audio_settings()

    return render_template(
        "index.html",
        api_key=get_api_key(),
        output_devices=get_output_devices(),
        current_device=audio_cfg.get("output_device")
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