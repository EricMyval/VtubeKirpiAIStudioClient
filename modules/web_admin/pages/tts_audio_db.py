import time
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify
from modules.tts.tts_db import audio_db


bp = Blueprint("tts_audio_db", __name__)


# ---------------- helpers ----------------

def cleanup_old_files():
    voice_dir = Path("data/out_voice")
    if not voice_dir.exists():
        return

    now = time.time()
    for file in voice_dir.glob("*.wav"):
        if file.stat().st_mtime < now - 3600:
            try:
                file.unlink()
            except:
                pass


# ---------------- Страница ----------------

@bp.route("/tts/audio_db", methods=["GET"])
def audio_db_management():
    cleanup_old_files()
    return render_template("audio_db.html")


# ---------------- API: база ----------------

@bp.route("/api/tts/audio_db", methods=["GET"])
def api_get_audio_files():
    try:
        records = audio_db.get_all_records()
        return jsonify({"success": True, "data": records})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/tts/audio_db", methods=["POST"])
def api_add_audio_file():
    try:
        data = request.json or request.form
        file_path = (data.get("file_path") or "").strip()
        text = (data.get("text") or "").strip()

        if not file_path or not text:
            return jsonify({"success": False, "error": "file_path и text обязательны"}), 400

        if audio_db.add_record(file_path, text):
            return jsonify({"success": True, "message": "Запись добавлена"})
        else:
            return jsonify(
                {"success": False, "error": "Не удалось добавить запись (возможно, путь уже существует)"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/tts/audio_db/<int:record_id>", methods=["PUT"])
def api_update_audio_file(record_id):
    try:
        data = request.json or request.form
        file_path = (data.get("file_path") or "").strip()
        text = (data.get("text") or "").strip()

        if not file_path or not text:
            return jsonify({"success": False, "error": "file_path и text обязательны"}), 400

        existing_record = audio_db.get_record_by_id(record_id)
        if not existing_record:
            return jsonify({"success": False, "error": "Запись не найдена"}), 404

        if audio_db.update_record(record_id, file_path, text):
            return jsonify({"success": True, "message": "Запись обновлена"})
        else:
            return jsonify(
                {"success": False, "error": "Не удалось обновить запись (возможно, путь уже существует)"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/tts/audio_db/<int:record_id>", methods=["DELETE"])
def api_delete_audio_file(record_id):
    try:
        existing_record = audio_db.get_record_by_id(record_id)
        if not existing_record:
            return jsonify({"success": False, "error": "Запись не найдена"}), 404

        if audio_db.delete_record(record_id):
            return jsonify({"success": True, "message": "Запись удалена"})
        else:
            return jsonify({"success": False, "error": "Не удалось удалить запись"}), 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/tts/audio_db/<int:record_id>", methods=["GET"])
def api_get_audio_file(record_id):
    try:
        record = audio_db.get_record_by_id(record_id)
        if record:
            return jsonify({"success": True, "data": record})
        else:
            return jsonify({"success": False, "error": "Запись не найдена"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500