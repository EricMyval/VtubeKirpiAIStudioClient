from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.config.config import cfg
from modules.client.audio.runtime import list_output_devices, clear_device_cache

bp = Blueprint("audio_settings", __name__)


@bp.route("/audio_settings", methods=["GET"])
def audio_settings_page():
    audio_config = cfg.get_audio_config()

    output_devices = list_output_devices()
    current_device_name = audio_config.get("output_device", "")

    return render_template(
        "audio_settings.html",
        output_devices=output_devices,
        current_device=current_device_name,
    )


@bp.route("/audio_settings/save", methods=["POST"])
def save_audio_settings():
    new_output_device = (request.form.get("output_device") or "").strip()

    if not new_output_device:
        flash("Не выбрано устройство вывода", "danger")
        return redirect(url_for("audio_settings.audio_settings_page"))

    try:
        cfg.update_audio_config(output_device=new_output_device)
        cfg.save(cfg.data)
        clear_device_cache()
        flash("Настройки аудио сохранены", "success")
    except Exception as e:
        flash(f"Ошибка при сохранении настроек: {e}", "danger")

    return redirect(url_for("audio_settings.audio_settings_page"))
