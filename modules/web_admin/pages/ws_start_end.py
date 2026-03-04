import json

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from modules.start_ends.ws_start_end_db import WSStartEndDB

bp = Blueprint("ws_start_end", __name__)

start_end_db = WSStartEndDB()


@bp.route("/ws_start_end", methods=["GET"])
def ws_start_end_page():
    start_commands = start_end_db.get_all_start_commands()
    end_commands = start_end_db.get_all_end_commands()

    edit_type = (request.args.get("edit_type") or "").strip()
    edit_id = request.args.get("edit_id", type=int)

    edit = None
    form = {
        "command_type": "start",
        "ws_command": "",
        "time_sleep": "0",
        "priority": "0",
        "min_price": "",
        "max_price": "",
        "exclude_prices": "",
        "afk_enabled": False,
    }

    if edit_type in ("start", "end") and edit_id:
        try:
            if edit_type == "start":
                command = start_end_db.get_start_command_by_id(edit_id)
            else:
                command = start_end_db.get_end_command_by_id(edit_id)

            if command:
                edit = {"command_type": edit_type, "command_id": command[0]}
                form["command_type"] = edit_type
                form["ws_command"] = command[1] or ""
                form["time_sleep"] = str(command[2] if command[2] is not None else 0)
                form["min_price"] = "" if command[3] is None else str(command[3])
                form["max_price"] = "" if command[4] is None else str(command[4])
                form["priority"] = str(command[6] if command[6] is not None else 0)
                form["afk_enabled"] = bool(command[7])

                exclude_raw = command[5]
                if exclude_raw:
                    try:
                        arr = json.loads(exclude_raw)
                        if isinstance(arr, list):
                            form["exclude_prices"] = ", ".join(str(x) for x in arr)
                        else:
                            form["exclude_prices"] = str(exclude_raw)
                    except Exception:
                        form["exclude_prices"] = str(exclude_raw)

        except Exception as e:
            flash(f"Ошибка загрузки команды: {e}", "danger")

    return render_template(
        "ws_start_end.html",
        start_commands=start_commands,
        end_commands=end_commands,
        edit=edit,
        form=form,
    )


@bp.route("/ws_start_end/add", methods=["POST"])
def ws_start_end_add():
    command_type = (request.form.get("command_type") or "start").strip()
    ws_command = (request.form.get("ws_command") or "").strip()
    time_sleep = float(request.form.get("time_sleep", 0) or 0)
    priority = int(request.form.get("priority", 0) or 0)

    afk_enabled = bool(request.form.get("afk_enabled"))

    min_price_raw = (request.form.get("min_price") or "").strip()
    max_price_raw = (request.form.get("max_price") or "").strip()
    exclude_prices = (request.form.get("exclude_prices") or "").strip()

    min_price = int(min_price_raw) if min_price_raw != "" else None
    max_price = int(max_price_raw) if max_price_raw != "" else None

    exclude_list = None
    if exclude_prices:
        try:
            exclude_list = [int(x.strip()) for x in exclude_prices.split(",") if x.strip()]
        except Exception:
            exclude_list = None

    try:
        if command_type == "start":
            start_end_db.add_start_command(
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_list,
                priority,
                afk_enabled,
            )
        else:
            start_end_db.add_end_command(
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_list,
                priority,
                afk_enabled,
            )

        flash("Команда добавлена ✅", "success")
    except Exception as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("ws_start_end.ws_start_end_page"))


@bp.route("/ws_start_end/delete/<command_type>/<int:command_id>", methods=["POST"])
def ws_start_end_delete(command_type, command_id):
    try:
        if command_type == "start":
            success = start_end_db.delete_start_command(command_id)
        else:
            success = start_end_db.delete_end_command(command_id)

        flash(
            "Команда удалена ✅" if success else "Команда не найдена ❌",
            "success" if success else "danger",
        )

    except Exception as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("ws_start_end.ws_start_end_page"))


@bp.route("/ws_start_end/update_inline", methods=["POST"])
def ws_start_end_update_inline():
    try:
        command_id = int(request.form.get("command_id"))
        command_type = (request.form.get("command_type") or "").strip()

        ws_command = (request.form.get("ws_command") or "").strip()
        time_sleep = float(request.form.get("time_sleep", 0) or 0)
        priority = int(request.form.get("priority", 0) or 0)

        afk_enabled = bool(request.form.get("afk_enabled"))

        min_price_raw = (request.form.get("min_price") or "").strip()
        max_price_raw = (request.form.get("max_price") or "").strip()
        exclude_prices = (request.form.get("exclude_prices") or "").strip()

        min_price = int(min_price_raw) if min_price_raw != "" else None
        max_price = int(max_price_raw) if max_price_raw != "" else None

        exclude_list = None
        if exclude_prices:
            try:
                exclude_list = [int(x.strip()) for x in exclude_prices.split(",") if x.strip()]
            except Exception:
                exclude_list = None

        if command_type == "start":
            success = start_end_db.update_start_command(
                command_id,
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_list,
                priority,
                afk_enabled,
            )
        else:
            success = start_end_db.update_end_command(
                command_id,
                ws_command,
                time_sleep,
                min_price,
                max_price,
                exclude_list,
                priority,
                afk_enabled,
            )

        flash(
            "Команда обновлена ✅" if success else "Команда не найдена ❌",
            "success" if success else "danger",
        )

    except Exception as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("ws_start_end.ws_start_end_page"))
