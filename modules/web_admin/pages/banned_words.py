import sqlite3
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response
)
from modules.banned_words.banned_words_db import banned_words_db

bp = Blueprint("banned_words", __name__)


# ========= Страница =========

@bp.route("/banned_words")
def banned_words_page():
    search_term = request.args.get("search", "")

    if search_term:
        words = banned_words_db.search_words(search_term)
    else:
        words = banned_words_db.get_all_words()

    return render_template(
        "banned_words.html",
        words=words,
        search_term=search_term
    )


# ========= Добавление =========

@bp.route("/banned_words/add", methods=["POST"])
def banned_words_add():
    word = request.form.get("word", "").strip()

    if not word:
        flash("Слово не может быть пустым", "danger")
        return redirect(url_for("banned_words.banned_words_page"))

    if banned_words_db.add_word(word):
        flash(f"Слово '{word}' добавлено", "success")
    else:
        flash(f"Слово '{word}' уже существует", "warning")

    return redirect(url_for("banned_words.banned_words_page"))


# ========= Удаление =========

@bp.route("/banned_words/delete/<int:word_id>", methods=["POST"])
def banned_words_delete(word_id):
    if banned_words_db.delete_word(word_id):
        flash("Слово удалено", "success")
    else:
        flash("Слово не найдено", "danger")

    return redirect(url_for("banned_words.banned_words_page"))


# ========= Редактирование =========

@bp.route("/banned_words/edit/<int:word_id>", methods=["POST"])
def banned_words_edit(word_id):
    new_word = request.form.get("new_word", "").strip()

    if not new_word:
        flash("Слово не может быть пустым", "danger")
        return redirect(url_for("banned_words.banned_words_page"))

    if banned_words_db.update_word(word_id, new_word):
        flash("Слово обновлено", "success")
    else:
        flash("Не удалось обновить слово (возможно, такое слово уже существует)", "danger")

    return redirect(url_for("banned_words.banned_words_page"))


# ========= Экспорт =========

@bp.route("/banned_words/export", methods=["POST"])
def banned_words_export():
    words = banned_words_db.get_words_list()
    words_text = "\n".join(words)

    return Response(
        words_text,
        mimetype="text/plain",
        headers={
            "Content-Disposition": "attachment;filename=banned_words.txt"
        }
    )


# ========= Очистка =========

@bp.route("/banned_words/clear", methods=["POST"])
def banned_words_clear():
    try:
        conn = sqlite3.connect("data/db/banned_words.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM banned_words")
        conn.commit()
        conn.close()
        flash("Все слова удалены", "success")
    except Exception as e:
        flash(f"Ошибка при очистке: {str(e)}", "danger")

    return redirect(url_for("banned_words.banned_words_page"))