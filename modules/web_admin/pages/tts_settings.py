from flask import Blueprint, render_template, request, jsonify

from modules.tts.tts_f5_settings import (
    load_voice_settings,
    update_voice_settings,
    reset_voice_settings
)

bp = Blueprint("tts_settings", __name__)


# ---------------- Страница ----------------

@bp.route("/tts/voice_settings", methods=["GET"])
def tts_voice_settings_page():
    return render_template("voice_settings.html")


# ---------------- API ----------------

@bp.route("/api/tts/voice_settings", methods=["GET"])
def api_get_voice_settings():
    try:
        s = load_voice_settings()
        return jsonify({"success": True, "data": s.__dict__})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/tts/voice_settings", methods=["PUT", "POST"])
def api_update_voice_settings():
    try:
        data = request.json or request.form or {}
        s = update_voice_settings(dict(data))
        return jsonify({"success": True, "data": s.__dict__})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/tts/voice_settings/reset", methods=["POST"])
def api_reset_voice_settings():
    try:
        s = reset_voice_settings()
        return jsonify({"success": True, "data": s.__dict__})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500