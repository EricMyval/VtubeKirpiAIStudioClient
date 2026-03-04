from flask import Blueprint, render_template

bp = Blueprint(
    "roulette_tasks_view",
    __name__,
    url_prefix="/overlay/roulette"
)


@bp.route("/tasks")
def tasks_view():
    return render_template("roulette_tasks_view.html")
