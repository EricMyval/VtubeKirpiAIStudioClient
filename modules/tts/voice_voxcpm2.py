import time
import re
from pathlib import Path
import torch
import soundfile as sf
from voxcpm import VoxCPM
from modules.tts.config import get_tts_config

OUTPUT_DIR = Path("data/out_voice")

_model = None
_loaded = False
_number_file = 0


# =========================================
# INIT
# =========================================

def init_tts(model_id="openbmb/VoxCPM2"):
    global _model
    print("[VoxCPM2] loading...")
    _model = VoxCPM.from_pretrained(
        model_id,
        load_denoiser=False
    )
    print("[VoxCPM2] ready")


# =========================================
# TEXT NORMALIZE
# =========================================

def _normalize_text(text: str):
    text = text.strip()
    if not text:
        return ""
    text = re.sub(r"\s*\.{2,}\s*", " ... ", text)
    text = re.sub(r"\s+", " ", text)
    if not re.search(r"[.!?]$", text):
        text += "."
    return text


# =========================================
# GENERATION
# =========================================

def tts_create_file(text, file_path=None, file_text=None):
    global _number_file
    if _model is None:
        raise RuntimeError("VoxCPM2 not loaded")
    settings = get_tts_config()
    text = _normalize_text(text)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _number_file += 1
    output_path = OUTPUT_DIR / f"voxcpm2_{int(time.time())}_{_number_file}.wav"
    cfg_value = getattr(settings, "voxcpm2_cfg_value", 2.0)
    steps = getattr(settings, "voxcpm2_inference_steps", 10)
    try:
        with torch.inference_mode():
            if file_path and file_text:
                wav = _model.generate(
                    text=text,
                    prompt_wav_path=file_path,
                    prompt_text=file_text,
                    reference_wav_path=file_path,
                    cfg_value=cfg_value,
                    inference_timesteps=steps,
                )
            elif file_path:
                wav = _model.generate(
                    text=text,
                    reference_wav_path=file_path,
                    cfg_value=cfg_value,
                    inference_timesteps=steps,
                )
            else:
                wav = _model.generate(
                    text=text,
                    cfg_value=cfg_value,
                    inference_timesteps=steps,
                )
        if isinstance(wav, torch.Tensor):
            wav = wav.detach().cpu().numpy()
        sf.write(str(output_path), wav, _model.tts_model.sample_rate)
        return output_path
    except Exception as e:
        print("[VoxCPM2 ERROR]", e)
        return None


# =========================================
# LOAD
# =========================================

def load_voxcpm2():
    global _loaded
    if not _loaded:
        init_tts()
        _loaded = True


# =========================================
# UNLOAD
# =========================================

def unload_voxcpm2():
    global _model, _loaded
    if not _loaded:
        return True
    try:
        if _model:
            try:
                pass
            except:
                pass
            del _model
            _model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        _loaded = False
        print("[VoxCPM2] unloaded")
        return True
    except Exception as e:
        print("[VoxCPM2 unload error]", e)
        return False