from flask import Blueprint, render_template, request, redirect, url_for, flash
from .service import get_api_key, set_api_key
from modules.roulette.runtime import roulette_runtime
from modules.timer.timer_bootstrap import bootstrap_timer
from modules.tts.config import bootstrap_tts

bp = Blueprint(
    "client_cabinet",
    __name__,
    url_prefix="/cabinet"
)


@bp.route("/", methods=["GET", "POST"])
def cabinet():

    if request.method == "POST":
        api_key = request.form.get("api_key", "")
        set_api_key(api_key)

        bootstrap_timer()
        bootstrap_tts()
        roulette_runtime.reload_config()

        flash("API ключ сохранён", "success")
        return redirect(url_for("client_cabinet.cabinet"))

    return render_template(
        "cabinet.html",
        api_key=get_api_key()
    )