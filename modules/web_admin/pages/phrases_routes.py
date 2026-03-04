from flask import Blueprint, render_template, request, redirect, url_for, flash
from modules.phrases.phrases import phrases_manager
from pathlib import Path
import json

phrases_bp = Blueprint(
    "phrases",
    __name__,
    url_prefix="/phrases"
)

PHRASES_PATH = Path("data/db/phrases.json")

PHRASE_TYPES = {
    "donation_voice": "Донат — озвучка",
    "donation_ai": "Донат — озвучка + ИИ",
    "points_voice": "Баллы — озвучка",
    "points_ai": "Баллы — озвучка + ИИ"
}


@phrases_bp.route("/", methods=["GET"])
def phrases_page():
    data = phrases_manager.data
    return render_template(
        "phrases.html",
        phrases=data,
        phrase_types=PHRASE_TYPES
    )

@phrases_bp.route("/edit", methods=["POST"])
def edit_phrase():
    phrase_type = request.form.get("phrase_type")
    index = int(request.form.get("index", -1))
    before = request.form.get("before", "").strip()
    after = request.form.get("after", "").strip()

    try:
        phrases_manager.data[phrase_type][index] = {
            "before": before,
            "after": after
        }

        PHRASES_PATH.write_text(
            json.dumps(phrases_manager.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        flash("Фраза обновлена", "success")
    except Exception as e:
        flash("Ошибка редактирования фразы", "error")

    return redirect(url_for("phrases.phrases_page"))


@phrases_bp.route("/add", methods=["POST"])
def add_phrase():
    phrase_type = request.form.get("phrase_type")
    before = request.form.get("before", "").strip()
    after = request.form.get("after", "").strip()

    if not phrase_type:
        flash("Не выбран тип фразы", "error")
        return redirect(url_for("phrases.phrases_page"))

    phrases_manager.data.setdefault(phrase_type, []).append({
        "before": before,
        "after": after
    })

    PHRASES_PATH.write_text(
        json.dumps(phrases_manager.data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    flash("Фраза добавлена", "success")
    return redirect(url_for("phrases.phrases_page"))


@phrases_bp.route("/delete", methods=["POST"])
def delete_phrase():
    phrase_type = request.form.get("phrase_type")
    index = int(request.form.get("index", -1))

    try:
        phrases_manager.data[phrase_type].pop(index)

        PHRASES_PATH.write_text(
            json.dumps(phrases_manager.data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        flash("Фраза удалена", "success")
    except Exception:
        flash("Ошибка удаления фразы", "error")

    return redirect(url_for("phrases.phrases_page"))
