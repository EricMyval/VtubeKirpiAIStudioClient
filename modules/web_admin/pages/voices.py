from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)
from modules.tts.tts_select import get_selected_tts, AVAILABLE_TTS
from modules.tts.tts_db import audio_db
from modules.gpt.gpt_characters_db import characters_db
from modules.config.config import cfg
from modules.voice_select.VoiceDB import voice_db

voices = Blueprint("voices", __name__)


# =========================
# MAIN PAGE
# =========================
@voices.route("/voices", methods=["GET", "POST"])
def voices_management():
    try:
        search_term = request.args.get("search", "")
        edit_id = request.args.get("edit")

        voice_db.add_direct_path_column()
        voice_db.ensure_afk_only_column()
        voice_db.ensure_tts_engine_column()

        if search_term:
            voices_list = voice_db.search_voices(search_term)
        else:
            voices_list = voice_db.get_all_voices()

        voice_to_edit = None
        if edit_id:
            voice_to_edit = voice_db.get_voice_by_id(int(edit_id))

        audio_voices = audio_db.get_all_records()

        audio_voice_map = {
            str(r["id"]): r["file_path"].replace("\\", "/").split("/")[-1]
            for r in audio_voices
        }

        characters = characters_db.list_characters()
        donation_config = cfg.get_donation_config()
        selected_tts = get_selected_tts()

        return render_template(
            "voices.html",
            voices=voices_list,
            search_term=search_term,
            voice=voice_to_edit,
            audio_voices=audio_voices,
            audio_voice_map=audio_voice_map,
            characters=characters,
            donation_config=donation_config,
            selected_tts=selected_tts,
            available_tts=AVAILABLE_TTS,
        )

    except Exception as e:
        flash(f"Ошибка при загрузке голосов: {e}", "danger")

        return render_template(
            "voices.html",
            voices=[],
            search_term="",
            voice=None,
            audio_voices=[],
            audio_voice_map={},
            characters=[],
            donation_config=None,
            selected_tts=get_selected_tts(),
            available_tts=AVAILABLE_TTS,
        )


# =========================
# ADD VOICE
# =========================
@voices.route("/voices/add", methods=["POST"])
def add_voice():
    try:
        voice_id = request.form.get("voice_id")
        description = request.form.get("description")

        ai_address = request.form.get("ai_address", "")
        direct_path = request.form.get("direct_path", "")
        tts_engine = request.form.get("tts_engine") or None

        afk_only = bool(request.form.get("afk_only"))

        min_price = int(request.form.get("min_price", 0))
        max_price = int(request.form.get("max_price", 0))

        exclude_prices = [
            int(x.strip())
            for x in request.form.get("exclude_prices", "").split(",")
            if x.strip().isdigit()
        ]

        voice_db.add_voice(
            voice_id=voice_id,
            description=description,
            ai_address=ai_address,
            direct_path=direct_path,
            tts_engine=tts_engine,
            afk_only=afk_only,
            min_price=min_price,
            max_price=max_price,
            exclude_prices=exclude_prices,
        )

        flash(f"Голос '{voice_id}' успешно добавлен", "success")

    except Exception as e:
        flash(f"Ошибка при добавлении: {e}", "danger")

    return redirect(url_for("voices.voices_management"))


# =========================
# EDIT VOICE (BY DB ID)
# =========================
@voices.route("/voices/edit", methods=["POST"])
def edit_voice():
    try:
        db_id = int(request.form.get("id"))
        voice_id = request.form.get("voice_id")

        tts_engine = request.form.get("tts_engine") or None

        exclude_prices = [
            int(x.strip())
            for x in request.form.get("exclude_prices", "").split(",")
            if x.strip().isdigit()
        ]

        afk_only = bool(request.form.get("afk_only"))

        voice_db.update_voice(
            db_id=db_id,
            voice_id=voice_id,
            description=request.form.get("description"),
            ai_address=request.form.get("ai_address", ""),
            direct_path=request.form.get("direct_path", ""),
            tts_engine=tts_engine,
            afk_only=afk_only,
            min_price=int(request.form.get("min_price", 0)),
            max_price=int(request.form.get("max_price", 0)),
            exclude_prices=exclude_prices,
        )

        flash(f"Голос '{voice_id}' успешно обновлён", "success")

    except Exception as e:
        flash(f"Ошибка при обновлении: {e}", "danger")

    return redirect(url_for("voices.voices_management"))


# =========================
# DELETE (BY DB ID)
# =========================
@voices.route("/voices/delete/<int:db_id>", methods=["POST"])
def delete_voice(db_id):
    try:
        voice_db.delete_voice(db_id)
        flash("Голос успешно удалён", "success")
    except Exception as e:
        flash(f"Ошибка при удалении: {e}", "danger")

    return redirect(url_for("voices.voices_management"))


# =========================
# FIND BY AMOUNT (UI)
# =========================
@voices.route("/voices/find_by_amount", methods=["POST"])
def find_voice_by_amount():
    try:
        amount = int(request.form.get("amount", 0))
        voice = voice_db.find_voice_by_amount(amount)

        if voice:
            flash(
                f"Найдено: Голос '{voice['voice_id']}' — {voice['description']}",
                "success",
            )
        else:
            flash("Голос для указанной суммы не найден", "warning")

    except Exception as e:
        flash(f"Ошибка при поиске: {e}", "danger")

    return redirect(url_for("voices.voices_management"))


# =========================
# API
# =========================
@voices.route("/api/voices/find", methods=["GET"])
def api_find_voice():
    try:
        amount = int(request.args.get("amount", 0))
        voice = voice_db.find_voice_by_amount(amount)

        if not voice:
            return jsonify(success=False, message="Голос не найден"), 404

        return jsonify(
            success=True,
            voice_id=voice["voice_id"],
            ai_address=voice["ai_address"],
            direct_path=voice["direct_path"],
            description=voice["description"],
            afk_only=voice.get("afk_only", False),
            tts_engine=voice.get("tts_engine"),
        )

    except Exception as e:
        return jsonify(success=False, message=str(e)), 400


# ======================================================
# DONATION SETTINGS (перенесены в voices blueprint)
# ======================================================

@voices.route("/voices/donation_settings/save", methods=["POST"])
def save_donation_settings_from_voices():
    try:
        ai_donation_min = int(request.form.get("ai_donation_min", 90))
        ai_donation_max = int(request.form.get("ai_donation_max", 90))
        if ai_donation_min > ai_donation_max:
            flash("Минимум ИИ больше максимума", "danger")
            return redirect(url_for("voices.voices_management"))
        cfg.update_donation_config(
            ai_donation_min=ai_donation_min,
            ai_donation_max=ai_donation_max
        )
        flash("Настройки донатов сохранены", "success")

    except Exception as e:
        flash(f"Ошибка: {e}", "danger")

    return redirect(url_for("voices.voices_management"))

# =========================
# SAVE TTS SELECTION
# =========================

from modules.tts.tts_select import set_selected_tts

@voices.route("/voices/tts/save", methods=["POST"])
def save_tts_selection():
    try:
        selected = request.form.get("tts")

        if not selected:
            flash("TTS не выбран", "warning")
            return redirect(url_for("voices.voices_management"))

        set_selected_tts(selected)

        flash(f"TTS переключён на: {selected}", "success")

    except Exception as e:
        flash(f"Ошибка при сохранении TTS: {e}", "danger")

    return redirect(url_for("voices.voices_management"))