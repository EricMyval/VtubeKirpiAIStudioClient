from flask import Blueprint, render_template, request, redirect, url_for, flash

from modules.gpt.gpt_knowledge_db import KnowledgeBase

bp = Blueprint("faq", __name__)

kb = KnowledgeBase("data/db/knowledge.db")


@bp.route("/faq")
def faq_list():
    rows = kb.list_all()
    return render_template("faq_list.html", rows=rows)


@bp.route("/faq/new", methods=["GET", "POST"])
def faq_new():
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        answer = request.form.get("answer", "").strip()

        if question and answer:
            kb.add_entry(question, answer)
            flash("Добавлено", "success")
            return redirect(url_for("faq.faq_list"))

        flash("Не заполнены поля", "danger")

    return render_template("faq_edit.html", row=None)


@bp.route("/faq/<int:faq_id>/edit", methods=["GET", "POST"])
def faq_edit(faq_id):
    row = kb.get(faq_id)

    if not row:
        flash("Не найдено", "danger")
        return redirect(url_for("faq.faq_list"))

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        answer = request.form.get("answer", "").strip()

        if question and answer:
            kb.update_entry(faq_id, question, answer)
            flash("Сохранено", "success")
            return redirect(url_for("faq.faq_list"))

        flash("Не заполнены поля", "danger")

    return render_template("faq_edit.html", row=row)


@bp.route("/faq/<int:faq_id>/delete", methods=["POST"])
def faq_delete(faq_id):
    kb.delete_entry(faq_id)
    flash("Удалено", "success")
    return redirect(url_for("faq.faq_list"))