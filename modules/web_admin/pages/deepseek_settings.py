from flask import Blueprint, render_template, request
from modules.gpt.deepseek_settings import deepseek_settings

bp = Blueprint("deepseek_settings", __name__)


@bp.route("/deepseek", methods=["GET"])
def deepseek_page():
    return render_template(
        "deepseek_settings.html",
        settings=deepseek_settings.get_all()
    )


@bp.route("/deepseek/settings", methods=["POST"])
def deepseek_update():
    data = request.form.to_dict()
    deepseek_settings.update(data)

    return render_template(
        "deepseek_settings.html",
        settings=deepseek_settings.get_all()
    )