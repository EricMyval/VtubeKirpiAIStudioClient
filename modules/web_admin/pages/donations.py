from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    Response,
)

from modules.donation_image.donation_image_db import donation_image_db

donations = Blueprint("donations", __name__)

# ===== helpers =====

def _image_url_from_row(donation_row) -> str:
    if not donation_row:
        return ""

    try:
        donation_id = int(donation_row[0])
        has_image = int(donation_row[4] or 0)
    except Exception:
        return ""

    if has_image != 1:
        return ""

    return url_for("donations.donation_image", donation_id=donation_id)


# ===== image =====

@donations.route("/donation-image/<int:donation_id>")
def donation_image(donation_id: int):
    raw, mime = donation_image_db.get_image_payload(donation_id)
    if not raw:
        return Response(status=404)
    return Response(raw, mimetype=(mime or "image/jpeg"))


# ===== pages =====

@donations.route("/donations")
def donations_management():
    donations_list = donation_image_db.get_all_donations()
    return render_template("donations.html", donations=donations_list)


@donations.route("/donations_obs")
def donations_obs():
    donations_list = donation_image_db.get_all_donations()
    return render_template("donations_obs.html", donations=donations_list)


@donations.route("/donations/add", methods=["POST"])
def add_donation():
    try:
        user = (request.form.get("user") or "").strip()
        message = (request.form.get("message") or "").strip()
        amount_user = (request.form.get("amount_user") or "").strip()

        if not all([user, message, amount_user]):
            flash("Все поля обязательны для заполнения", "danger")
            return redirect(url_for("donations.donations_management"))

        donation_image_db.parse_and_add_donation(user, message, amount_user)
        flash("Донат успешно добавлен", "success")

    except Exception as e:
        flash(f"Ошибка при добавлении: {e}", "danger")

    return redirect(url_for("donations.donations_management"))


@donations.route("/donations/delete/<int:donation_id>", methods=["POST"])
def delete_donation(donation_id: int):
    try:
        donation_image_db.delete_donation(donation_id)
        flash("Донат успешно удалён", "success")
    except Exception as e:
        flash(f"Ошибка при удалении: {e}", "danger")

    return redirect(url_for("donations.donations_management"))

# ===== API =====

@donations.route("/api/donations/delete/<int:donation_id>", methods=["POST"])
def api_delete_donation(donation_id: int):
    try:
        donation_image_db.delete_donation(donation_id)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 400


@donations.route("/api/donations")
def get_donations_data():
    try:
        donations_list = donation_image_db.get_all_donations()
        out = []

        for d in donations_list:
            out.append([
                d[0],
                d[1],
                d[2],
                d[3],
                _image_url_from_row(d),
                d[5],
            ])

        return jsonify(success=True, donations=out, count=len(out))

    except Exception as e:
        return jsonify(success=False, error=str(e)), 400


@donations.route("/api/donations_page")
def get_donations_page():
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = max(1, min(100, int(request.args.get("page_size", 10))))

        items, total = donation_image_db.get_donations_page(page, page_size)

        out = []
        for d in items:
            out.append([
                d[0],
                d[1],
                d[2],
                d[3],
                _image_url_from_row(d),
                d[5],
            ])

        return jsonify(
            success=True,
            page=page,
            page_size=page_size,
            total=total,
            donations=out,
            has_more=(page * page_size) < total,
        )

    except Exception as e:
        return jsonify(success=False, error=str(e)), 400


# ===== trigger callback =====

_donation_listener = None

def register_donation_listener(func):
    global _donation_listener
    _donation_listener = func


@donations.route("/donations/trigger/<int:donation_id>/<string:mode>")
def trigger_donation(donation_id: int, mode: str):
    try:
        donation = donation_image_db.get_donation_by_id(donation_id)
        if not donation:
            return jsonify(success=False, error="Донат не найден")

        show_image = (mode == "with_image")

        if _donation_listener:
            _donation_listener(donation, show_image)

        return jsonify(
            success=True,
            message=f"Донат запущен (show_image={show_image})",
        )

    except Exception as e:
        return jsonify(success=False, error=str(e))
