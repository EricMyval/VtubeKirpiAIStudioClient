from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from modules.awards.awards_db import awards_db

bp = Blueprint("awards", __name__)


# =========================
# Page
# =========================

@bp.route("/", methods=["GET"])
def awards_page():
    try:
        items = awards_db.list_all_with_children_names()
        all_items = awards_db.list_all()

        edit_item = None
        edit_children_ids = []

        edit_id = (request.args.get("edit") or "").strip()
        if edit_id:
            try:
                edit_item = awards_db.get(int(edit_id))
                if not edit_item:
                    flash(f"Запись #{edit_id} не найдена", "warning")
                else:
                    if edit_item.is_group:
                        edit_children_ids = awards_db.get_children_ids(edit_item.id)
            except Exception:
                flash("Некорректный ID для редактирования", "warning")

        return render_template(
            "awards.html",
            items=items,
            all_items=all_items,
            edit_item=edit_item,                 # содержит award_text
            edit_children_ids=edit_children_ids,
        )

    except Exception as e:
        flash(f"Ошибка открытия страницы наград: {e}", "danger")
        return redirect(url_for("index"))


# =========================
# Save (create / update)
# =========================

@bp.route("/save", methods=["POST"])
def awards_save():
    try:
        # award_text автоматически попадёт сюда из form
        awards_db.upsert_from_form(request.form)
        flash("Запись сохранена", "success")

    except Exception as e:
        flash(f"Ошибка сохранения: {e}", "danger")

    return redirect(url_for("awards.awards_page"))


# =========================
# Delete
# =========================

@bp.route("/delete/<int:item_id>", methods=["POST"])
def awards_delete(item_id: int):
    try:
        awards_db.delete(item_id)
        flash(f"Запись #{item_id} удалена", "success")

    except Exception as e:
        flash(f"Ошибка удаления: {e}", "danger")

    return redirect(url_for("awards.awards_page"))
