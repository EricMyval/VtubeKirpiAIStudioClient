from flask import Blueprint, render_template, request, redirect, url_for, flash

from modules.gpt.gpt_db import user_history_db as db

bp = Blueprint("user_history", __name__)


@bp.route("/user_history")
def user_history():
    users = db.get_all_users()
    selected_user = request.args.get("user", "")
    history = []

    if selected_user:
        history = db.get_user_history(selected_user)

    return render_template(
        "user_history.html",
        users=users,
        selected_user=selected_user,
        history=history,
        max_messages=db.max_messages_per_user
    )


@bp.route("/user_history/clear", methods=["POST"])
def clear_user_history():
    username = request.form.get("username")

    if username:
        db.clear_user_history(username)
        flash(f"История пользователя {username} очищена", "success")
    else:
        flash("Не указано имя пользователя", "danger")

    return redirect(url_for("user_history.user_history"))


@bp.route("/user_history/update_settings", methods=["POST"])
def update_history_settings():
    max_messages = request.form.get("max_messages")

    if max_messages and max_messages.isdigit():
        max_messages = int(max_messages)
        db.set_max_messages(max_messages)
        flash(f"Максимум сообщений установлен: {max_messages}", "success")
    else:
        flash("Некорректное значение", "danger")

    return redirect(url_for("user_history.user_history"))