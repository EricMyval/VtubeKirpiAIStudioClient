from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3

from modules.pets.pets_db import pets_db
from modules.pets.pets_manager import pets_manager

bp = Blueprint("pets", __name__)


@bp.route("/pets")
def pets_page():
    pets = pets_db.get_all()

    edit_id = request.args.get("edit", "").strip()
    pet = None
    if edit_id.isdigit():
        pet = pets_db.get_by_id(int(edit_id))

    active_name = None
    remaining = 0
    defaults = {"donate_boost": 1.0, "tick": 1, "freeze": False}
    influence = defaults

    try:
        defaults = pets_manager.get_defaults()
        active_name, remaining = pets_manager.get_active_name_and_remaining()
        influence = pets_manager.get_timer_influence()
    except Exception:
        pass

    return render_template(
        "pets.html",
        pets=pets,
        pet=pet,
        active_name=active_name,
        remaining=remaining,
        influence=influence,
        defaults=defaults,
    )


@bp.route("/pets/defaults/save", methods=["POST"])
def pets_defaults_save():
    try:
        tick = request.form.get("tick", "1").strip()
        donate_boost = request.form.get("donate_boost", "1.0").strip()
        freeze = bool(request.form.get("freeze"))

        new_def = pets_manager.save_defaults(
            donate_boost=float(donate_boost),
            tick=int(tick),
            freeze=freeze,
        )

        flash(
            f"Дефолты сохранены: tick={new_def['tick']}, donate_boost={new_def['donate_boost']}, freeze={'true' if new_def['freeze'] else 'false'}",
            "success",
        )
    except Exception as e:
        flash(f"Ошибка сохранения дефолтов: {e}", "danger")

    return redirect(url_for("pets.pets_page"))


@bp.route("/pets/save", methods=["POST"])
def pets_save():
    try:
        pet_id = request.form.get("pet_id", "").strip()

        name = request.form.get("name", "").strip()
        ws_show_cmd = request.form.get("ws_show_cmd", "").strip()
        ws_hide_cmd = request.form.get("ws_hide_cmd", "").strip()

        display_seconds = request.form.get("display_seconds", "10").strip()
        tick_value = request.form.get("tick_value", "1").strip()
        donate_boost = request.form.get("donate_boost", "1.0").strip()

        tick_enabled = bool(request.form.get("tick_enabled"))
        donate_boost_enabled = bool(request.form.get("donate_boost_enabled"))
        freeze_timer = bool(request.form.get("freeze_timer"))

        if not all([name, ws_show_cmd, ws_hide_cmd]):
            flash("name / ws_show_cmd / ws_hide_cmd — обязательны", "danger")
            return redirect(
                url_for("pets.pets_page", edit=pet_id)
                if pet_id else url_for("pets.pets_page")
            )

        if pet_id.isdigit():
            pets_db.update_pet(
                int(pet_id),
                name=name,
                ws_show_cmd=ws_show_cmd,
                ws_hide_cmd=ws_hide_cmd,
                display_seconds=int(display_seconds),
                tick_value=int(tick_value),
                tick_enabled=tick_enabled,
                donate_boost=float(donate_boost),
                donate_boost_enabled=donate_boost_enabled,
                freeze_timer=freeze_timer,
            )
            flash("Питомец обновлён", "success")
        else:
            pets_db.add_pet(
                name=name,
                ws_show_cmd=ws_show_cmd,
                ws_hide_cmd=ws_hide_cmd,
                display_seconds=int(display_seconds),
                tick_value=int(tick_value),
                tick_enabled=tick_enabled,
                donate_boost=float(donate_boost),
                donate_boost_enabled=donate_boost_enabled,
                freeze_timer=freeze_timer,
            )
            flash("Питомец добавлен", "success")

    except sqlite3.IntegrityError:
        flash("ws_show_cmd должен быть уникальным", "danger")
        return redirect(url_for("pets.pets_page"))
    except Exception as e:
        flash(f"Ошибка: {e}", "danger")
        return redirect(url_for("pets.pets_page"))

    return redirect(url_for("pets.pets_page"))


@bp.route("/pets/delete/<int:pet_id>", methods=["POST"])
def pets_delete(pet_id: int):
    try:
        pets_db.delete_pet(pet_id)
        flash("Питомец удалён", "success")
    except Exception as e:
        flash(f"Ошибка: {e}", "danger")
    return redirect(url_for("pets.pets_page"))


@bp.route("/pets/hide_active", methods=["POST"])
def pets_hide_active():
    try:
        pets_manager.force_hide_active()
        flash("Активный питомец скрыт", "success")
    except Exception as e:
        flash(f"Ошибка: {e}", "danger")
    return redirect(url_for("pets.pets_page"))


@bp.route("/pets/status")
def pets_status():
    try:
        return jsonify(pets_manager.get_status())
    except Exception as e:
        defaults = {"donate_boost": 1.0, "tick": 1, "freeze": False}
        try:
            defaults = pets_manager.get_defaults()
        except Exception:
            pass

        return jsonify({
            "active": False,
            "active_name": None,
            "remaining": 0,
            "expires_at": 0,
            "activated_at": 0,
            "defaults": defaults,
            "influence": defaults,
            "pet": None,
            "error": str(e),
        }), 200
