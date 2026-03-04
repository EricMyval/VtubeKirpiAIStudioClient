from flask import Blueprint, jsonify, render_template, request
from modules.afk.chat_message_filter_settings import chat_message_filter_settings

bp = Blueprint(
    "chat_message_filter",
    __name__,
    url_prefix="/chat-message-filter"
)

# =========================
# Страница
# =========================

@bp.route("/", methods=["GET"])
def page():
    return render_template(
        "chat_message_filter.html",
        settings=chat_message_filter_settings.get_all()
    )

# =========================
# Получить настройки (AJAX)
# =========================

@bp.route("/settings", methods=["GET"])
def get_settings():
    return jsonify(
        chat_message_filter_settings.get_all()
    )

# =========================
# Обновить настройки
# =========================

@bp.route("/settings", methods=["POST"])
def update_settings():
    data = request.form.to_dict()
    chat_message_filter_settings.update_from_form(data)

    return render_template(
        "chat_message_filter.html",
        settings=chat_message_filter_settings.get_all()
    )
