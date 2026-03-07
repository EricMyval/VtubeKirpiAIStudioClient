from flask import Blueprint, render_template, request, redirect, url_for, flash

from modules.audio.service import get_audio_settings, get_output_devices, set_output_device

bp = Blueprint(
    "client_audio",
    __name__,
    url_prefix="/client/audio"
)


@bp.route("/", methods=["GET"])
def page():
    audio_cfg = get_audio_settings()
    devices = get_output_devices()

    return render_template(
        "client_audio.html",
        output_devices=devices,
        current_device=audio_cfg.get("output_device", "")
    )


@bp.route("/save", methods=["POST"])
def save():
    device = (request.form.get("output_device") or "").strip()

    if not device:
        flash("Не выбрано устройство вывода", "danger")
        return redirect(url_for("client_audio.page"))

    try:
        set_output_device(device)
        flash("Настройки аудио сохранены", "success")
    except Exception as e:
        flash(f"Ошибка сохранения: {e}", "danger")

    return redirect(url_for("client_audio.page"))