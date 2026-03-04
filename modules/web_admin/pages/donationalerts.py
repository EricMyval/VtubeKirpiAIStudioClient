from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from modules.donation.donation_parser import (
    load_da_cfg,
    save_da_cfg,
    get_token,
    clear_token,
    TOKEN_FILE,
)

donationalerts = Blueprint("donationalerts", __name__)


@donationalerts.route("/donationalerts", methods=["GET"])
def donationalerts_settings():
    try:
        da = load_da_cfg()
        token_exists = TOKEN_FILE.exists()

        return render_template(
            "donationalerts.html",
            da=da,
            token_exists=token_exists,
        )

    except Exception as e:
        flash(f"Ошибка открытия DonationAlerts страницы: {e}", "danger")
        return redirect(url_for("index"))


@donationalerts.route("/donationalerts/save", methods=["POST"])
def donationalerts_save():
    try:
        client_id = request.form.get("client_id", "").strip()
        client_secret = request.form.get("client_secret", "").strip()
        redirect_uri = request.form.get("redirect_uri", "").strip()

        if not client_id or not client_secret:
            flash("CLIENT_ID и CLIENT_SECRET обязательны.", "warning")
            return redirect(url_for("donationalerts.donationalerts_settings"))

        save_da_cfg(client_id, client_secret, redirect_uri)
        flash("Настройки DonationAlerts сохранены ✅", "success")

    except Exception as e:
        flash(f"Ошибка сохранения DonationAlerts настроек: {e}", "danger")

    return redirect(url_for("donationalerts.donationalerts_settings"))


@donationalerts.route("/donationalerts/authorize", methods=["POST"])
def donationalerts_authorize():
    try:
        get_token(force_reauth=True)
        flash(
            "Авторизация успешна ✅ Токен сохранён в data/db/donation_token.json",
            "success",
        )

    except Exception as e:
        flash(f"Ошибка авторизации DonationAlerts: {e}", "danger")

    return redirect(url_for("donationalerts.donationalerts_settings"))


@donationalerts.route("/donationalerts/clear_token", methods=["POST"])
def donationalerts_clear_token():
    try:
        clear_token()
        flash("Токен удалён ✅", "success")

    except Exception as e:
        flash(f"Ошибка удаления токена: {e}", "danger")

    return redirect(url_for("donationalerts.donationalerts_settings"))
