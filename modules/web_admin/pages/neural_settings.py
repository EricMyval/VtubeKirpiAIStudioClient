from flask import Blueprint, render_template, request, redirect, url_for, flash

from modules.gpt.gpt_db import gpt_settings

bp = Blueprint("neural_settings", __name__)


@bp.route("/neural_settings", methods=["GET", "POST"])
def neural_settings():
    lm_config = gpt_settings.get_lm_studio_config()

    if request.method == "POST":

        new_config = {
            "url": request.form.get("url", "").strip(),
            "temperature": float(request.form.get("temperature", 1.4)),
            "top_p": float(request.form.get("top_p", 0.95)),
            "top_k": int(request.form.get("top_k", 50)),
            "repetition_penalty": float(request.form.get("repetition_penalty", 1.1)),
            "max_tokens": int(request.form.get("max_tokens", 2000)),
        }

        gpt_settings.set_lm_studio(**new_config)
        flash("Настройки нейронки сохранены", "success")

        return redirect(url_for("neural_settings.neural_settings"))

    return render_template(
        "neural_settings.html",
        config=lm_config
    )