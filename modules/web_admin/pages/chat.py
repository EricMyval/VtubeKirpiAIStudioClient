import time
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify

from modules.donation.donation_monitor import donation_monitor
from modules.gpt.gpt_sender import assistant, gpt_send_message
from modules.gpt.gpt_db import user_history_db as db
from modules.gpt.gpt_characters_db import characters_db
from modules.phrases.phrases import MESSAGE_FROM_VOICE

bp = Blueprint("chat", __name__)


# ----------------------------
# page
# ----------------------------

@bp.route("/")
def index():
    characters = characters_db.list_characters()

    return render_template(
        "index.html",
        characters=characters,
        selected_character="default"
    )


# ----------------------------
# api
# ----------------------------

@bp.route("/api/chat/send", methods=["POST"])
def api_chat_send():
    try:
        response = ""
        generation_time_ms = 0
        username = request.form.get("username", "Гость")
        message = (request.form.get("message") or "").strip()
        character = request.form.get("character", "default")
        image_file = request.files.get("image")

        if not message and not (image_file and image_file.filename):
            return jsonify({
                "success": False,
                "error": "empty message"
            }), 400

        if image_file and image_file.filename:

            upload_dir = Path("uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)

            suffix = Path(image_file.filename).suffix or ".jpg"
            image_path = upload_dir / f"{int(time.time())}{suffix}"

            image_file.save(image_path)

            try:
                response = assistant.ask_with_image(
                    character=character,
                    image_path=str(image_path),
                    message=message,
                    username=username
                )
            finally:
                if image_path.exists():
                    try:
                        image_path.unlink()
                    except Exception:
                        pass
        else:
            start_time = time.perf_counter()

            response = gpt_send_message(
                username,
                message,
                character=character
            )

            end_time = time.perf_counter()
            generation_time_ms = int((end_time - start_time) * 1000)

        donation_monitor.db.add_donate(username, response, MESSAGE_FROM_VOICE)

        response = f"[GPT: генерация ответа за {generation_time_ms} мсек]: {response}"
        return jsonify({
            "success": True,
            "response": response,
            "username": username,
            "character": character,
            "timestamp": time.time()
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route("/api/chat/history")
def api_chat_history():
    username = request.args.get("username", "Гость")

    history = db.get_user_history(username)

    formatted = []
    for msg in history[-50:]:
        formatted.append({
            "role": msg["role"],
            "content": msg["content"],
            "timestamp": msg.get("timestamp", "")
        })

    return jsonify(formatted)


@bp.route("/api/chat/clear", methods=["POST"])
def api_chat_clear():
    data = request.json or {}
    username = data.get("username", "Гость")

    db.clear_user_history(username)

    return jsonify({"success": True})