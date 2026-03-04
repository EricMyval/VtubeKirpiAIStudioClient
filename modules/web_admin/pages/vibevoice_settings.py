from flask import Blueprint, render_template, request, jsonify

from modules.tts.tts_vibevoice_settings import (
    load_vibevoice_workflow,
    save_vibevoice_workflow,
    extract_vibevoice_inputs,
    apply_vibevoice_inputs,
    get_comfyui_url,
    set_comfyui_url,
    load_vibevoice_runtime_settings,
    set_vibevoice_max_chunk_size
)
bp = Blueprint(
    "vibevoice_settings",
    __name__,
)

# ---------------- Page ----------------

@bp.route("/vibevoice_settings")
def vibevoice_settings_page():
    return render_template("vibevoice_settings.html")


# ---------------- API ----------------

@bp.route("/api/vibevoice_settings", methods=["GET"])
def api_get_vibevoice_settings():
    try:
        workflow = load_vibevoice_workflow()
        inputs = extract_vibevoice_inputs(workflow)

        inputs["_comfyui_url"] = get_comfyui_url()

        runtime = load_vibevoice_runtime_settings()
        inputs["_max_chunk_size"] = runtime.get("max_chunk_size", 1000)

        return jsonify({"success": True, "data": inputs})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/api/vibevoice_settings", methods=["POST", "PUT"])
def api_update_vibevoice_settings():
    try:
        patch = request.json or {}

        # --- runtime chunk size ---
        max_chunk_size = patch.pop("_max_chunk_size", None)
        if max_chunk_size is not None:
            set_vibevoice_max_chunk_size(max_chunk_size)

        # --- comfy url ---
        comfy_url = patch.pop("_comfyui_url", None)
        if comfy_url is not None:
            set_comfyui_url(comfy_url)

        # запрещаем runtime поля
        patch.pop("text", None)
        patch.pop("speaker_1_voice", None)

        workflow = load_vibevoice_workflow()
        apply_vibevoice_inputs(workflow, patch)
        save_vibevoice_workflow(workflow)

        inputs = extract_vibevoice_inputs(workflow)
        inputs["_comfyui_url"] = get_comfyui_url()

        runtime = load_vibevoice_runtime_settings()
        inputs["_max_chunk_size"] = runtime.get("max_chunk_size", 1000)

        return jsonify({"success": True, "data": inputs})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500