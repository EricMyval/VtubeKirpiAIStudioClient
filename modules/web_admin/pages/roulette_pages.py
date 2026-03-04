from flask import Blueprint, render_template, request, redirect, url_for, jsonify

from modules.client.roulette.config_repo import RouletteConfigRepository
from modules.client.roulette.engine import RouletteEngine
from modules.client.roulette.models import RouletteSettings, RouletteItem
from modules.client.roulette.runtime import roulette_runtime


bp = Blueprint(
    "roulette_pages",
    __name__,
    url_prefix="/web-admin/roulette"
)

repo = RouletteConfigRepository()


# ----------------------------
# Главная страница
# ----------------------------

@bp.route("/", methods=["GET"])
def page():

    settings = repo.get_settings()
    items = repo.get_items()

    return render_template(
        "roulette_admin.html",
        settings=settings,
        items=items
    )


# ----------------------------
# Настройки
# ----------------------------

@bp.route("/settings", methods=["POST"])
def update_settings():

    base_amount = int(request.form.get("base_amount", 200))
    increment = int(request.form.get("increment_per_spin", 0))

    repo.update_settings(
        RouletteSettings(
            base_amount=base_amount,
            increment_per_spin=increment
        )
    )

    return redirect(url_for("roulette_pages.page"))


# ----------------------------
# Items
# ----------------------------

@bp.route("/item/add", methods=["POST"])
def add_item():

    title = request.form.get("title", "").strip()
    weight = int(request.form.get("weight", 1))
    payload = request.form.get("payload", "")

    if title:
        repo.add_item(
            RouletteItem(
                id=None,
                title=title,
                weight=weight,
                payload=payload
            )
        )

    return redirect(url_for("roulette_pages.page"))


@bp.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):

    repo.delete_item(item_id)

    return redirect(url_for("roulette_pages.page"))


@bp.route("/item/<int:item_id>/update", methods=["POST"])
def update_item(item_id):

    title = request.form.get("title", "").strip()
    weight = int(request.form.get("weight", 1))
    payload = request.form.get("payload", "")

    repo.update_item(
        RouletteItem(
            id=item_id,
            title=title,
            weight=weight,
            payload=payload
        )
    )

    return redirect(url_for("roulette_pages.page"))


# ----------------------------
# JSON (удобно для фронта)
# ----------------------------

@bp.route("/api/state", methods=["GET"])
def api_state():

    settings = repo.get_settings()
    items = repo.get_items()

    return jsonify({
        "settings": {
            "base_amount": settings.base_amount,
            "increment_per_spin": settings.increment_per_spin
        },
        "items": [
            {
                "id": i.id,
                "title": i.title,
                "weight": i.weight,
                "payload": i.payload
            } for i in items
        ]
    })

@bp.route("/test-spin", methods=["POST"])
def test_spin():

    engine = RouletteEngine(repo)

    result = engine.spin_once_force()

    if not result:
        return redirect(url_for("roulette_pages.page"))

    win_item, items = result

    visual_items = [{"title": i.title} for i in items]

    win_index = next(
        (idx for idx, i in enumerate(items) if i.id == win_item.id),
        0
    )

    roulette_runtime.push_spin({
        "items": visual_items,
        "win_index": win_index
    })

    return redirect(url_for("roulette_pages.page"))


