from flask import Blueprint, render_template, jsonify

from modules.client.donate_panel.donate_panel_service import donate_panel_service
from modules.client.donate_panel.repository import DonateRepository
from modules.client.tts.tts_runtime import tts_runtime


bp = Blueprint(
    "client_donate_panel",
    __name__,
    url_prefix="/client/donate-panel"
)


# ==========================================================
# PAGE
# ==========================================================

@bp.route("/", methods=["GET"])
def page():

    return render_template(
        "donate_panel.html"
    )


# ==========================================================
# STATE
# ==========================================================

@bp.route("/state", methods=["GET"])
def state():

    current = donate_panel_service.get_current()
    history = donate_panel_service.get_history(30)
    paused = donate_panel_service.is_paused()

    return jsonify({

        "current": {
            "id": current.id,
            "username": current.username,
            "platform": current.platform,
            "amount": current.amount,
            "message": current.message,
            "status": current.status
        } if current else None,

        "paused": paused,

        "session_total":
            donate_panel_service.get_session_total(),

        "history": [
            {
                "id": d.id,
                "username": d.username,
                "platform": d.platform,
                "amount": d.amount,
                "message": d.message,
                "status": d.status
            }
            for d in history
        ]

    })


# ==========================================================
# SKIP
# ==========================================================

@bp.route("/skip", methods=["POST"])
def skip():

    donate_panel_service.skip()

    tts_runtime.stop()

    return jsonify({
        "ok": True
    })


# ==========================================================
# PAUSE / RESUME
# ==========================================================

@bp.route("/pause", methods=["POST"])
def pause():
    paused = donate_panel_service.toggle_pause()
    if paused:
        tts_runtime.pause()
    else:
        tts_runtime.resume()

    return jsonify({
        "ok": True,
        "paused": paused
    })


# ==========================================================
# REPEAT
# ==========================================================

@bp.route("/repeat/<int:donate_id>", methods=["POST"])
def repeat(donate_id):

    ok = DonateRepository.repeat(donate_id)

    return jsonify({
        "ok": ok
    })