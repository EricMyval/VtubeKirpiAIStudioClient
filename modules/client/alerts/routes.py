from flask import Blueprint, jsonify, send_from_directory
from modules.utils.runtime_paths import app_root
from modules.client.alerts.alert_queue import pull_alert

BASE_PATH = app_root()

bp = Blueprint(
    "client_alerts",
    __name__,
    url_prefix="/alerts"
)


@bp.route("/widget")
def alerts_widget():
    return open(
        BASE_PATH / "templates/alerts_widget.html",
        encoding="utf-8"
    ).read()


@bp.route("/pull")
def alerts_pull():
    data = pull_alert()

    if not data:
        return jsonify({"ok": False})

    return jsonify({
        "ok": True,
        "data": data
    })


@bp.route("/media/<path:filename>")
def alerts_media(filename):
    print("MEDIA REQUEST:", filename)
    return send_from_directory(
        BASE_PATH / "data/alerts_media",
        filename
    )