from flask import Blueprint, render_template, request, redirect, url_for, flash
from .service import get_api_key, set_api_key

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
        flash("API ключ сохранён", "success")
        return redirect(url_for("client_cabinet.cabinet"))

    return render_template(
        "cabinet.html",
        api_key=get_api_key()
    )