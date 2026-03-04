from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from modules.config.config import cfg
from modules.vkplay.vkplay_tokens import vkplay_tokens
from modules.vkplay.vkplay_alerts_voice_settings import SETTINGS_FILE as VKPLAY_ALERTS_SETTINGS_FILE, \
    vkplay_alerts_store

bp = Blueprint("vkplay", __name__)

# =========================================================
# 🔵 Основная страница настроек
# =========================================================

@bp.route("/vkplay", endpoint="index")
def vkplay_settings():
    try:
        v = cfg.data.get("vkplay") or {}
        if not isinstance(v, dict):
            v = {}
            cfg.data["vkplay"] = v

        v.setdefault("client_id", "")
        v.setdefault("client_secret", "")
        v.setdefault("redirect_uri", "http://localhost:27027/vkplay/callback")
        v.setdefault("scopes", vkplay_tokens.scopes_from_cfg() or "channel:points")
        v.setdefault("access_token", "")
        v.setdefault("refresh_token", "")

        return render_template("vkplay.html", vkplay=v)

    except Exception as e:
        print(f"Ошибка открытия страницы VK Play Live: {e}")
        return redirect(url_for("index"))


# =========================================================
# 💾 Сохранение настроек
# =========================================================

@bp.route("/vkplay/save", methods=["POST"])
def save():
    try:
        v = cfg.data.get("vkplay")
        if not isinstance(v, dict):
            v = {}
            cfg.data["vkplay"] = v

        v["client_id"] = (request.form.get("client_id") or "").strip()
        v["client_secret"] = (request.form.get("client_secret") or "").strip()
        v["redirect_uri"] = (
            (request.form.get("redirect_uri") or "").strip()
            or "http://localhost:27027/vkplay/callback"
        )
        v["scopes"] = (request.form.get("scopes") or "").strip()

        cfg.save(cfg.data)

        flash("VK Play Live: настройки сохранены", "success")
        return redirect(url_for("vkplay.index"))

    except Exception as e:
        flash(f"Ошибка сохранения VK Play Live: {e}", "danger")
        return redirect(url_for("vkplay.index"))


# =========================================================
# 🔐 OAuth Start
# =========================================================

@bp.route("/vkplay/auth/start")
def auth_start():
    try:
        url = vkplay_tokens.build_authorize_url(state="")
        return redirect(url)

    except Exception as e:
        flash(f"VK Play Live: не удалось открыть авторизацию: {e}", "danger")
        return redirect(url_for("vkplay.index"))


# =========================================================
# 🔁 OAuth Callback
# =========================================================

@bp.route("/vkplay/callback")
def callback():
    try:
        err = (request.args.get("error") or "").strip()
        if err:
            desc = (request.args.get("error_description") or "").strip()
            flash(f"VK Play Live: авторизация отменена/ошибка: {err} {desc}".strip(), "warning")
            return redirect(url_for("vkplay.index"))

        code = (request.args.get("code") or "").strip()
        if not code:
            flash("VK Play Live: в callback нет параметра code", "warning")
            return redirect(url_for("vkplay.index"))

        vkplay_tokens.exchange_code_for_token(code)

        flash("VK Play Live: токены успешно получены и сохранены", "success")
        return redirect(url_for("vkplay.index"))

    except Exception as e:
        flash(f"VK Play Live: ошибка обработки callback: {e}", "danger")
        return redirect(url_for("vkplay.index"))


# =========================================================
# 🔊 Alerts
# =========================================================

@bp.route("/vkplay/alerts", endpoint="alerts")
def alerts_page():
    try:
        settings = vkplay_alerts_store.load()

        return render_template(
            "vkplay_alerts.html",
            settings=settings,
            settings_path=str(VKPLAY_ALERTS_SETTINGS_FILE),
        )

    except Exception as e:
        flash(f"Ошибка открытия страницы VK Play Live alerts: {e}", "danger")
        return redirect(url_for("index"))


@bp.route("/vkplay/alerts/save", methods=["POST"])
def alerts_save():
    try:
        vkplay_alerts_store.update_from_form(request.form)
        flash("VK Play Live: тексты озвучки сохранены", "success")
        return redirect(url_for("vkplay.alerts"))

    except Exception as e:
        flash(f"VK Play Live: ошибка сохранения alerts: {e}", "danger")
        return redirect(url_for("vkplay.alerts"))