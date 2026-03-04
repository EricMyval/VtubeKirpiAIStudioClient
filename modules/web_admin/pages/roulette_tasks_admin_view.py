from flask import Blueprint, render_template

bp = Blueprint(
    "roulette_tasks_admin_view",
    __name__,
    url_prefix="/overlay/roulette"
)


@bp.route("/tasks-admin")
def tasks_admin():
    return render_template("roulette_tasks_admin.html")
