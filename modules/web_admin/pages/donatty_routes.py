from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from modules.donatty.client import fetch_access_token
from modules.donatty.sse_listener import start_donatty_sse
from modules.donatty.storage import donatty_config
from urllib.parse import urlparse, parse_qs


bp = Blueprint("donatty", __name__)


@bp.route("/donatty")
def donatty_page():
    return render_template(
        "donatty.html",
        config=donatty_config
    )


@bp.route("/donatty/connect", methods=["POST"])
def donatty_connect():
    try:
        widget_url = request.form.get("widget_url", "").strip()

        if not widget_url:
            flash("Ссылка виджета обязательна", "danger")
            return redirect(url_for("donatty.donatty_page"))

        parsed = urlparse(widget_url)
        qs = parse_qs(parsed.query)

        widget_token = (qs.get("token") or [None])[0]
        reference = (qs.get("ref") or [None])[0]

        if not widget_token or not reference:
            flash("В ссылке не найден token или ref", "danger")
            return redirect(url_for("donatty.donatty_page"))

        fetch_access_token(widget_token, reference)
        start_donatty_sse()

        flash("Donatty подключён", "success")
        print("Donatty подключён")
        return redirect(url_for("donatty.donatty_page"))

    except Exception as e:
        flash(f"Ошибка подключения Donatty: {e}", "danger")
        print(f"Ошибка подключения Donatty: {e}")
        return redirect(url_for("donatty.donatty_page"))


@bp.route("/donatty/status")
def donatty_status():
    return jsonify({
        "connected": bool(donatty_config.get("access_token")),
        "expire_at": donatty_config.get("expire_at"),
    })
