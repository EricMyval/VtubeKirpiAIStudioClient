# modules/web_admin/timer_routes.py
from flask import Blueprint, render_template, request
from modules.timer.timer import timer

bp = Blueprint("timer", __name__)


def get_timer():
    """
    Возвращает общий (shared) таймер приложения.
    НИКОГДА не создаёт новый.
    """
    return timer


@bp.route("/timer/status")
def timer_status():
    t = get_timer()
    return {
        "current_time": t.get_formatted_time(),
        "remaining_seconds": t.get_remaining_time(),
        "subtract_per_tick": t.subtract_per_tick,
        "is_running": t.is_running,
        "success": True,
    }


@bp.route("/timer")
def timer_page():
    t = get_timer()
    return render_template(
        "timer.html",
        current_time=t.get_formatted_time(),
        remaining_seconds=t.get_remaining_time(),
        subtract_per_tick=t.subtract_per_tick,
        is_running=t.is_running,
    )


@bp.route("/timer/start", methods=["POST"])
def timer_start():
    t = get_timer()
    t.start()
    return {"success": True, "message": "Таймер запущен"}


@bp.route("/timer/stop", methods=["POST"])
def timer_stop():
    t = get_timer()
    t.stop()
    return {"success": True, "message": "Таймер остановлен"}


@bp.route("/timer/set_time", methods=["POST"])
def timer_set_time():
    t = get_timer()

    hours = int(request.form.get("hours", 0))
    minutes = int(request.form.get("minutes", 0))
    seconds = int(request.form.get("seconds", 0))

    total_seconds = hours * 3600 + minutes * 60 + seconds

    with t.lock:
        t.current_time = total_seconds
        t.total_seconds = total_seconds

    t.send_ws_command(
        f'{{"action":"timer","data":"{t.format_time()}"}}'
    )

    return {"success": True}


@bp.route("/timer/add_time", methods=["POST"])
def timer_add_time():
    t = get_timer()
    seconds_to_add = int(request.form.get("seconds", 0))
    t.add_time(seconds_to_add)
    return {"success": True}


@bp.route("/timer/set_speed", methods=["POST"])
def timer_set_speed():
    """
    Ручная установка тика из UI.
    Пет может потом переопределить это значение.
    """
    t = get_timer()
    speed = int(request.form.get("speed", 1))

    t.apply_pets_influence({
        "tick": speed,
        "freeze": False,
    })

    return {"success": True}


@bp.route("/timer/reset", methods=["POST"])
def timer_reset():
    t = get_timer()
    total_seconds = 30 * 60
    with t.lock:
        t.current_time = total_seconds
        t.total_seconds = total_seconds
    t.send_ws_command(
        f'{{"action":"timer","data":"{t.format_time()}"}}'
    )
    return {"success": True}

@bp.route("/timer/obs")
def timer_obs_page():
    t = get_timer()
    return render_template(
        "timer_obs.html",
        current_time=t.get_formatted_time(),
    )
