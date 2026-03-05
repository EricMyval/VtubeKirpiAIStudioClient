from flask import Blueprint, render_template, request, jsonify
import requests

from modules.client.cabinet.service import get_api_key
from modules.client.donate_panel.donate_panel_service import donate_panel_service
from modules.client.donate_panel.repository import DonateRepository

from modules.utils.constant import DONATE_URL

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
            "reward": current.extra,
            "status": current.status,
            "image_url": current.raw_event and __import__("json").loads(current.raw_event).get("image_url")
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
                "reward": d.extra,
                "status": d.status,
                "image_url": d.raw_event and __import__("json").loads(d.raw_event).get("image_url")
            }
            for d in history
        ]

    })


# ==========================================================
# START EVENT FROM PANEL
# ==========================================================

@bp.route("/start/<int:donate_id>", methods=["POST"])
def start_event(donate_id):

    ok = donate_panel_service.start_event(donate_id)

    return jsonify({
        "ok": ok
    })


# ==========================================================
# IMAGE CONTINUE
# ==========================================================

@bp.route("/image/continue", methods=["POST"])
def image_continue():

    ws_url = request.json.get("ws_url")

    donate_panel_service.image_continue(ws_url)

    return jsonify({
        "ok": True
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

    donate = DonateRepository.get_by_id(donate_id)

    if not donate:
        return jsonify({"ok": False})

    try:

        api_key = get_api_key()

        requests.post(
            DONATE_URL,
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={
                "user": donate.username,
                "amount": donate.amount,
                "message": donate.message
            },
            timeout=10
        )

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        })

    return jsonify({"ok": True})


# ==========================================================
# SEND TEST DONATE
# ==========================================================

@bp.route("/send", methods=["POST"])
def send():

    data = request.json or {}

    username = data.get("user")
    amount = data.get("amount")
    message = data.get("message")

    if not username or not amount:
        return jsonify({
            "ok": False,
            "error": "user required"
        })

    try:

        api_key = get_api_key()

        requests.post(
            DONATE_URL,
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json"
            },
            json={
                "user": username,
                "amount": amount,
                "message": message
            },
            timeout=10
        )

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        })

    return jsonify({
        "ok": True
    })