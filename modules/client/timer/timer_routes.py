from flask import Blueprint, render_template

from modules.client.pets.pet_runtime import init_pet_defaults
from modules.client.timer.timer_bootstrap import bootstrap_timer
from modules.client.timer.timer_service import TimerService
from modules.client.timer.timer_state import timer_state

bp = Blueprint("client_timer", __name__, url_prefix="/client/timer")


# ---------- CONTROL PANEL ----------

@bp.route("/")
def page():
    return render_template("timer_control.html")


# ---------- OBS WIDGET ----------

@bp.route("/obs")
def obs():
    return render_template(
        "timer_obs.html",
        current_time=TimerService.get_formatted_time()
    )


# ---------- STATUS ----------

@bp.route("/status")
def status():

    return {
        "time": TimerService.get_formatted_time(),
        "remaining": TimerService.get_remaining_seconds(),
        "is_running": timer_state.is_running,
        "tick": timer_state.tick,
        "donate_boost": timer_state.donate_boost
    }


# ---------- START ----------

@bp.route("/start", methods=["POST"])
def start():

    TimerService.start()

    return {"success": True}


# ---------- STOP ----------

@bp.route("/stop", methods=["POST"])
def stop():

    TimerService.stop()

    return {"success": True}


# ---------- RESET ----------

@bp.route("/reset", methods=["POST"])
def reset():

    TimerService.stop()
    TimerService.set_time(30 * 60)

    return {"success": True}


# ---------- +5 MIN ----------

@bp.route("/add5", methods=["POST"])
def add5():

    TimerService.add_time(300)

    return {"success": True}


# ---------- -5 MIN ----------

@bp.route("/minus5", methods=["POST"])
def minus5():

    TimerService.add_time(-300)

    return {"success": True}


# ---------- BOOTSTRAP ----------

bootstrap_timer()
init_pet_defaults()