from flask import Blueprint, render_template

bp = Blueprint(
    "roulette_progress_view",
    __name__,
    url_prefix="/overlay/roulette"
)


@bp.route("/progress")
def progress_view():
    return render_template("roulette_progress_view.html")
