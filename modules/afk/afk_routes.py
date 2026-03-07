from flask import Blueprint

from .afk_service import AFKService

bp = Blueprint(
    "client_afk",
    __name__,
    url_prefix="/client/afk"
)


# ============================
# STATUS
# ============================

@bp.route("/status")
def status():
    return AFKService.status()


# ============================
# ENABLE
# ============================

@bp.route("/enable")
def enable():
    return AFKService.enable()


# ============================
# DISABLE
# ============================

@bp.route("/disable")
def disable():
    return AFKService.disable()