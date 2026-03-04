# modules/client/roulette/overlay_routes.py

from flask import Blueprint, render_template, jsonify, request
from modules.client.roulette.runtime import roulette_runtime


bp = Blueprint(
    "roulette_overlay",
    __name__,
    url_prefix="/overlay/roulette"
)

# =====================================================
# VIEW PAGES
# =====================================================

@bp.route("/")
def roulette_view():
    return render_template("roulette_view.html")


@bp.route("/progress")
def roulette_progress_view():
    return render_template("roulette_progress_view.html")


@bp.route("/tasks")
def roulette_tasks_view():
    return render_template("roulette_tasks_view.html")


@bp.route("/tasks-admin")
def roulette_tasks_admin_view():
    return render_template("roulette_tasks_admin.html")


# =====================================================
# API
# =====================================================

# -------------------------
# реальные items рулетки
# -------------------------

@bp.route("/api/items")
def api_items():

    items = roulette_runtime._repo.get_items()

    return jsonify([
        {
            "id": i.id,
            "title": i.title
        } for i in items
    ])


# -------------------------
# очередь прокруток
# -------------------------

@bp.route("/api/next-spin")
def api_next_spin():

    payload = roulette_runtime.pop_spin()

    if payload is None:
        return jsonify({"has": False})

    return jsonify({
        "has": True,
        "payload": payload
    })


# -------------------------
# список заданий
# -------------------------

@bp.route("/api/tasks")
def api_tasks():
    return jsonify(roulette_runtime.get_tasks())


@bp.route("/api/tasks/<task_id>/delete", methods=["POST"])
def api_task_delete(task_id):

    roulette_runtime.remove_task(task_id)
    return jsonify({"ok": True})


@bp.route("/api/spin-finished", methods=["POST"])
def api_spin_finished():

    data = request.get_json(silent=True) or {}
    title = data.get("title")

    if title:
        roulette_runtime.add_task(title)

    return jsonify({"ok": True})


# -------------------------
# прогресс накопления
# -------------------------

@bp.route("/api/progress")
def api_progress():

    settings = roulette_runtime._repo.get_settings()
    total = roulette_runtime.get_sum()

    base = max(1, settings.base_amount)

    current = total % base

    if current == 0 and total > 0:
        left = 0
        progress = 1.0
    else:
        left = base - current
        progress = current / base

    return jsonify({
        "current": current,
        "base": base,
        "left": left,
        "progress": progress
    })