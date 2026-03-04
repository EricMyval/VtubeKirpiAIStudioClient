from flask import Blueprint, render_template, request
from modules.tts.tts_qwen3_settings import qwen3_settings

bp = Blueprint("qwen3_settings", __name__)


@bp.route("/qwen3", methods=["GET"])
def qwen3_page():
    return render_template(
        "qwen3_settings.html",
        settings=qwen3_settings.get_all()
    )


@bp.route("/qwen3/settings", methods=["POST"])
def qwen3_update_settings():
    data = request.form.to_dict()
    qwen3_settings.update(data)

    return render_template(
        "qwen3_settings.html",
        settings=qwen3_settings.get_all()
    )