# modules/web_admin/pages/characters.py

from flask import Blueprint, render_template, request, redirect, url_for, flash

from modules.gpt.gpt_characters_db import characters_db
from modules.gpt.gpt_db import (
    gpt_settings,
    get_prompt_mode,
    set_prompt_mode,
)

bp = Blueprint("characters", __name__)


@bp.route("/prompt", methods=["GET", "POST"])
def prompt():

    characters = characters_db.list_characters()

    selected_character = request.values.get("character", "default")

    # ------------------------
    # create character
    # ------------------------
    if request.method == "POST" and request.form.get("action") == "create_character":

        name = request.form.get("new_character_name", "").strip()

        if not name:
            flash("Имя персонажа пустое", "danger")
            return redirect(url_for("characters.prompt"))

        try:
            characters_db.create_character(name=name)
            flash(f"Персонаж '{name}' создан", "success")
            return redirect(
                url_for("characters.prompt", character=name)
            )
        except Exception as e:
            flash(f"Ошибка создания персонажа: {e}", "danger")
            return redirect(url_for("characters.prompt"))

    # ------------------------
    # save prompts
    # ------------------------
    if request.method == "POST" and request.form.get("action") == "save_prompts":

        selected_character = request.form.get("character", "default")

        system_prompt = request.form.get("prompt_body", "")
        refinement_prompt = request.form.get("refinement_prompt_body", "")

        characters_db.update_prompts(
            name=selected_character,
            system_prompt=system_prompt,
            refinement_prompt=refinement_prompt
        )

        # общие настройки
        refinement_enabled = bool(request.form.get("refinement_enabled"))
        gpt_settings.set_assistant(
            refinement_enabled=refinement_enabled
        )

        mode_raw = request.form.get("prompt_mode", "4")
        try:
            set_prompt_mode(int(mode_raw))
        except Exception:
            pass

        flash("Промпты сохранены", "success")
        return redirect(
            url_for("characters.prompt", character=selected_character)
        )

    # ------------------------
    # load character
    # ------------------------

    character = characters_db.get_character(selected_character)

    if not character:
        selected_character = "default"
        character = characters_db.get_character("default")

    assistant_cfg = gpt_settings.get_assistant_config()

    return render_template(
        "prompt.html",

        characters=characters,
        selected_character=selected_character,

        content=character["system_prompt"],
        refinement_content=character["refinement_prompt"],

        prompt_mode=get_prompt_mode(),
        refinement_enabled=assistant_cfg["refinement_enabled"],
    )