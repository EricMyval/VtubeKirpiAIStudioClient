import time
import secrets
import urllib.parse

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from modules.config.config import cfg

twitch = Blueprint("twitch", __name__)

TWITCH_DEFAULT_REDIRECT = "http://localhost:27027/twitch/callback"
TWITCH_DEFAULT_SCOPES = "channel:read:redemptions"


def _get_twitch_cfg():
    t = cfg.data.get("twitch", {})
    if not isinstance(t, dict):
        t = {}

    t.setdefault("client_id", "")
    t.setdefault("client_secret", "")
    t.setdefault("redirect_uri", TWITCH_DEFAULT_REDIRECT)
    t.setdefault("scopes", TWITCH_DEFAULT_SCOPES)

    t.setdefault("access_token", "")
    t.setdefault("refresh_token", "")
    t.setdefault("token_obtained_at", 0)
    t.setdefault("expires_in", 0)

    cfg.data["twitch"] = t
    return t


def _save_twitch_cfg(t: dict):
    cfg.data["twitch"] = t
    cfg.save(cfg.data)


@twitch.route("/twitch", methods=["GET"])
def twitch_settings():
    try:
        t = _get_twitch_cfg()
        if not (t.get("redirect_uri") or "").strip():
            t["redirect_uri"] = TWITCH_DEFAULT_REDIRECT
        return render_template("twitch.html", twitch=t)
    except Exception as e:
        flash(f"Ошибка открытия Twitch страницы: {e}", "danger")
        return redirect(url_for("index"))


@twitch.route("/twitch/save", methods=["POST"])
def twitch_save():
    try:
        t = _get_twitch_cfg()

        t["client_id"] = (request.form.get("client_id") or "").strip()
        t["client_secret"] = (request.form.get("client_secret") or "").strip()

        redirect_uri = (request.form.get("redirect_uri") or "").strip()
        t["redirect_uri"] = redirect_uri or TWITCH_DEFAULT_REDIRECT

        scopes = (request.form.get("scopes") or "").strip()
        t["scopes"] = scopes or TWITCH_DEFAULT_SCOPES

        _save_twitch_cfg(t)
        flash("Twitch настройки сохранены", "success")

    except Exception as e:
        flash(f"Ошибка сохранения Twitch настроек: {e}", "danger")

    return redirect(url_for("twitch.twitch_settings"))


@twitch.route("/twitch/auth/start")
def twitch_auth_start():
    t = _get_twitch_cfg()

    if not (t.get("client_id") or "").strip():
        flash("Сначала укажи Client ID", "warning")
        return redirect(url_for("twitch.twitch_settings"))

    redirect_uri = t.get("redirect_uri") or TWITCH_DEFAULT_REDIRECT
    scopes = t.get("scopes") or TWITCH_DEFAULT_SCOPES

    state = secrets.token_urlsafe(16)
    session["twitch_oauth_state"] = state

    params = {
        "client_id": t["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
        "force_verify": "true",
    }

    url = "https://id.twitch.tv/oauth2/authorize?" + urllib.parse.urlencode(params)
    return redirect(url)


@twitch.route("/twitch/callback")
def twitch_callback():
    t = _get_twitch_cfg()

    err = request.args.get("error")
    if err:
        desc = request.args.get("error_description", "")
        flash(f"Twitch OAuth ошибка: {err} ({desc})", "danger")
        return redirect(url_for("twitch.twitch_settings"))

    code = request.args.get("code")
    state = request.args.get("state")
    expected = session.get("twitch_oauth_state")

    if not code or not state or state != expected:
        flash("Twitch OAuth: неверный state или отсутствует code", "danger")
        return redirect(url_for("twitch.twitch_settings"))

    if not t.get("client_id") or not t.get("client_secret"):
        flash("Нужны Client ID и Client Secret", "warning")
        return redirect(url_for("twitch.twitch_settings"))

    try:
        import requests

        r = requests.post(
            "https://id.twitch.tv/oauth2/token",
            data={
                "client_id": t["client_id"],
                "client_secret": t["client_secret"],
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": t["redirect_uri"],
            },
            timeout=20,
        )

        data = r.json()
        if "access_token" not in data:
            flash(f"Не удалось получить токен: {data}", "danger")
            return redirect(url_for("twitch.twitch_settings"))

        t["access_token"] = data.get("access_token", "")
        t["refresh_token"] = data.get("refresh_token", "")
        t["expires_in"] = int(data.get("expires_in", 0))
        t["token_obtained_at"] = int(time.time())

        _save_twitch_cfg(t)
        flash("✅ Twitch авторизация успешна", "success")

    except Exception as e:
        flash(f"Ошибка получения токена: {e}", "danger")

    return redirect(url_for("twitch.twitch_settings"))
