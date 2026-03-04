# modules/web_admin/pages/donate_admin.py
from flask import Blueprint, render_template, redirect, url_for
from modules.donate_admin.donation_hooks import emit_donation
from modules.player.playback_controller import playback_controller
from modules.donate_admin.repository import DonateRepository
from modules.donate_admin.session_stats import donation_session_stats
from flask import jsonify

bp = Blueprint("donate_admin", __name__)


# ==========================================================
# Главная страница — ИСТОРИЯ донатов
# ==========================================================

@bp.route("/donate_admin", methods=["GET"])
def donate_admin_page():
    donations = DonateRepository.get_all()

    return render_template(
        "donate_admin.html",
        donations=donations,
    )


# ==========================================================
# ⛔ Принудительное завершение ТЕКУЩЕГО доната
# ==========================================================

@bp.route("/donate_admin/force_stop", methods=["POST"])
def force_stop_donation():
    if playback_controller.is_active():
        playback_controller.force_stop()
        print("[donate_admin] Текущий донат принудительно завершён")
    else:
        print("[donate_admin] Нет активного доната")

    return redirect(url_for("donate_admin.donate_admin_page"))


# ==========================================================
# 🔁 Повтор доната
# (создаёт НОВУЮ запись и уходит в очередь)
# ==========================================================

@bp.route("/donate_admin/repeat/<int:donate_id>", methods=["POST"])
def repeat_donate(donate_id):
    donate = DonateRepository.get_by_id(donate_id)
    if not donate:
        return redirect(url_for("donate_admin.donate_admin_page"))

    # 1️⃣ Добавляем НОВЫЙ донат в историю (очередь)
    DonateRepository.add_donate(
        username=donate.username,
        amount=donate.amount,
        message=donate.message,
        extra="admin-repeat",
    )

    # 2️⃣ Пускаем в ОБЩИЙ поток донатов
    emit_donation(
        donate.username,
        donate.message or "",
        int(donate.amount),
        True,  # не реальный, а повтор
    )

    print("[donate_admin] repeat donation emitted")

    return redirect(url_for("donate_admin.donate_admin_page"))

# ==========================================================
# 🔄 Partial — HTML карточки донатов (для live-обновления)
# ==========================================================

@bp.route("/donate_admin/partial", methods=["GET"])
def donate_admin_partial():
    """
    HTML карточки донатов для live-обновления
    """

    donations = DonateRepository.get_all()

    # БЕРЁМ первые 100 — они уже новые → старые
    donations = donations[:100]

    return render_template(
        "donate_admin/_cards.html",
        donations=donations,
    )


@bp.route("/donate_admin/session_stats")
def donate_admin_session_stats():
    return jsonify(
        total_amount=donation_session_stats.get_total()
    )

# ==========================================================
# 🧪 Тестовый донат из админки
# ==========================================================

@bp.route("/donate_admin/test_donate", methods=["POST"])
def test_donate():
    from flask import request

    username = request.form.get("username", "").strip()
    message = request.form.get("message", "").strip()
    amount = request.form.get("amount", "").strip()

    if not username or not amount:
        return redirect(url_for("donate_admin.donate_admin_page"))

    try:
        amount = int(amount)
    except ValueError:
        return redirect(url_for("donate_admin.donate_admin_page"))

    # 1️⃣ Добавляем в историю / очередь
    DonateRepository.add_donate(
        username=username,
        amount=amount,
        message=message,
        extra="admin-test",
    )

    # 2️⃣ Эмитим в общий поток донатов
    emit_donation(
        username,
        message,
        str(amount),
        False,  # не реальный донат
    )

    print("[donate_admin] test donation emitted")

    return redirect(url_for("donate_admin.donate_admin_page"))