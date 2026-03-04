from flask import Blueprint, jsonify, render_template, request
from modules.afk.afk_settings import afk_settings
from modules.afk.afk_state import afk_state
from modules.web_admin.shared import chat_to_donation_settings

bp = Blueprint("afk", __name__)


@bp.route("/afk", methods=["GET"])
def afk_page():
    return render_template(
        "afk.html",
        afk_enabled=afk_state.is_enabled(),
        settings={
            # AFK базовые настройки
            **afk_settings.get_all(),

            # Chat → Donation настройки
            "max_queue": chat_to_donation_settings.max_queue,
            "afk_intro_text": chat_to_donation_settings.afk_intro_text,
        }
    )


@bp.route("/afk/status", methods=["GET"])
def afk_status():
    return jsonify(
        afk_enabled=afk_state.is_enabled()
    )


@bp.route("/afk/toggle", methods=["POST"])
def afk_toggle():
    state = afk_state.toggle()
    return jsonify(afk_enabled=state)


@bp.route("/afk/settings", methods=["POST"])
def afk_update_settings():
    data = request.form.to_dict()

    # 🔹 AFK-настройки (ws_on_enable, ws_on_disable, etc.)
    afk_settings.update(data)

    # 🔹 Chat → Donation настройки (max_queue, afk_intro_text)
    chat_to_donation_settings.update_from_form(data)

    return render_template(
        "afk.html",
        afk_enabled=afk_state.is_enabled(),
        settings={
            **afk_settings.get_all(),
            "max_queue": chat_to_donation_settings.max_queue,
            "afk_intro_text": chat_to_donation_settings.afk_intro_text,
        }
    )
