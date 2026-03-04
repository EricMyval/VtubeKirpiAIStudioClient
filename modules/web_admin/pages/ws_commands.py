from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from modules.config.config import cfg
from modules.ws_commands.ws_commands_db import ws_db

bp = Blueprint("ws_commands", __name__)


# =========================================================
# ⚙ Сохранение адреса WebSocket
# =========================================================

@bp.route("/save_websocket_settings", methods=["POST"])
def save_websocket_settings():
    websocket_address = request.form.get("websocket_address")

    if websocket_address:
        try:
            cfg.update_websocket_config(websocket_address)
            flash("Адрес вебсокета сохранен", "success")
        except Exception as e:
            flash(f"Ошибка при сохранении: {str(e)}", "danger")
    else:
        flash("Адрес не может быть пустым", "danger")

    return redirect(url_for("ws_commands.index"))


# =========================================================
# 📋 Список команд
# =========================================================

@bp.route("/ws_commands", endpoint="index")
def ws_commands_page():
    search_term = request.args.get("search", "")

    if search_term:
        commands = ws_db.search_commands(search_term)
    else:
        commands = ws_db.get_all_commands()

    websocket_address = (
        cfg.get_websocket_config().get("address", "ws://127.0.0.1:19190/")
    )

    return render_template(
        "ws_commands.html",
        commands=commands,
        search_term=search_term,
        command=None,
        websocket_address=websocket_address
    )


# =========================================================
# ✏ Редактирование
# =========================================================

@bp.route("/ws_commands/edit/<int:command_id>")
def edit(command_id):
    command = ws_db.get_command_by_id(command_id)

    if not command:
        flash("Команда не найдена", "danger")
        return redirect(url_for("ws_commands.index"))

    commands = ws_db.get_all_commands()

    return render_template(
        "ws_commands.html",
        commands=commands,
        command=command,
        search_term="",
        websocket_address=cfg.get_websocket_config().get("address", "ws://127.0.0.1:19190/")
    )


# =========================================================
# 💾 Сохранение
# =========================================================

@bp.route("/ws_commands/save", methods=["POST"])
def save():
    command_id = request.form.get("command_id")
    price = request.form.get("price")
    command_text = request.form.get("command")
    text = request.form.get("text")
    delay_seconds = request.form.get("delay_seconds", 30)

    try:
        price = int(price)
        delay_seconds = int(delay_seconds)

        if command_id:
            success = ws_db.update_command(
                int(command_id),
                price,
                command_text,
                text,
                delay_seconds
            )

            if success:
                flash("Команда успешно обновлена", "success")
            else:
                flash("Команда не найдена", "danger")
        else:
            ws_db.add_command(price, command_text, text, delay_seconds)
            flash("Команда успешно добавлена", "success")

    except ValueError:
        flash("Неверный формат цены или задержки", "danger")
    except Exception as e:
        flash(f"Ошибка при сохранении: {str(e)}", "danger")

    return redirect(url_for("ws_commands.index"))


# =========================================================
# 🗑 Удаление
# =========================================================

@bp.route("/ws_commands/delete/<int:command_id>", methods=["POST"])
def delete(command_id):
    success = ws_db.delete_command(command_id)

    if success:
        flash("Команда успешно удалена", "success")
    else:
        flash("Команда не найдена", "danger")

    return redirect(url_for("ws_commands.index"))