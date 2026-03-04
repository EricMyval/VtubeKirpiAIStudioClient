from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from modules.web_admin.shared import twitch_alerts_store

bp = Blueprint("twitch_alerts", __name__)


@bp.route("/", methods=["GET"])
def twitch_alerts_page():
    settings = twitch_alerts_store.load()

    return render_template(
        "twitch_alerts.html",
        settings=settings,
        settings_path=str(twitch_alerts_store.file_path),
    )


@bp.route("/save", methods=["POST"])
def twitch_alerts_save():
    twitch_alerts_store.update_from_form(request.form)
    flash("✅ Настройки озвучки Twitch (follow/raid) сохранены", "success")
    return redirect(url_for("twitch_alerts.twitch_alerts_page"))
