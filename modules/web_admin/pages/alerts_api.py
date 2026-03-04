from flask import Blueprint, request, jsonify, send_from_directory

from modules.client.alerts.alert_engine import engine
from modules.client.alerts.alert_queue import push_alert, pull_alert
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
import sys

from modules.client.alerts.alert_storage import storage

bp_alerts_api = Blueprint("alerts_api", __name__)


# -------------------------------------------------
# Правильная папка для сохранения медиа в EXE
# -------------------------------------------------

def _get_app_data_root() -> Path:
    """
    В режиме exe — рядом с exe.
    В обычном режиме — корень проекта.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return Path.cwd()


ALERTS_MEDIA_DIR = _get_app_data_root() / "data" / "alerts_media"
ALERTS_MEDIA_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------
# profiles
# -------------------------------------------------

@bp_alerts_api.get("/alerts/profiles")
def get_profiles():
    return jsonify(storage.list_profiles())


@bp_alerts_api.post("/alerts/profile")
def create_profile():
    data = request.get_json(force=True)
    profile = storage.create(data)
    return jsonify(profile)


@bp_alerts_api.put("/alerts/profile/<profile_id>")
def update_profile(profile_id):

    data = request.get_json(force=True)

    profile = storage.update(profile_id, data)

    if not profile:
        return jsonify({"error": "not found"}), 404

    return jsonify(profile)


@bp_alerts_api.delete("/alerts/profile/<profile_id>")
def delete_profile(profile_id):

    ok = storage.delete(profile_id)
    return jsonify({"ok": ok})


# -------------------------------------------------
# Тест
# -------------------------------------------------

@bp_alerts_api.post("/alerts/test/<profile_id>")
def test_alert(profile_id):

    profile = storage.get(profile_id)

    if not profile:
        return jsonify({"error": "not found"}), 404

    payload = engine.build_alert_payload(
        profile=profile,
        user="Тестовый енот",
        amount=123,
        message="Это тестовое оповещение 🦝"
    )

    push_alert(payload)

    return {"ok": True}


# -------------------------------------------------
# OBS-виджет забирает алерты
# -------------------------------------------------

@bp_alerts_api.get("/alerts/pull")
def pull_alert_api():

    alert = pull_alert()

    if not alert:
        return jsonify({"ok": False})

    return jsonify({
        "ok": True,
        "data": alert
    })


# -------------------------------------------------
# upload media / sound
# -------------------------------------------------

@bp_alerts_api.post("/alerts/upload_media")
def upload_alert_media():

    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400

    f = request.files["file"]

    if not f.filename:
        return jsonify({"error": "empty filename"}), 400

    filename = secure_filename(f.filename)
    ext = Path(filename).suffix.lower()

    new_name = f"{uuid.uuid4().hex}{ext}"
    full_path = ALERTS_MEDIA_DIR / new_name

    try:
        f.save(full_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "url": f"/alerts/media/{new_name}"
    })


# -------------------------------------------------
# раздача файлов
# -------------------------------------------------

@bp_alerts_api.get("/alerts/media/<path:filename>")
def get_alert_media(filename):
    return send_from_directory(
        ALERTS_MEDIA_DIR,
        filename,
        as_attachment=False
    )