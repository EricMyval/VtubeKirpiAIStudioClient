import time
from pathlib import Path
import torch
import soundfile as sf
#from omnivoice import OmniVoice
from modules.tts.config import get_tts_config

OUTPUT_DIR = Path("data/out_voice")

_model = None
_loaded = False
_number_file = 0


# =========================================
# INIT
# =========================================

def init_tts(model_id="k2-fsa/OmniVoice"):
    global _model
    print("[OmniVoice] loading...")
    #_model = OmniVoice.from_pretrained(model_id, device_map="cuda:0", dtype=torch.float16)
    print("[OmniVoice] ready")


# =========================================
# GENERATION
# =========================================

def tts_create_file(text, file_path=None, file_text=None):
    global _number_file
    if _model is None:
        raise RuntimeError("OmniVoice not loaded")
    settings = get_tts_config()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _number_file += 1
    output_path = OUTPUT_DIR / f"omni_{int(time.time())}_{_number_file}.wav"
    num_step = getattr(settings, "omni_num_step", 32)
    speed = getattr(settings, "omni_inference_speed", 1.0)
    try:
        with torch.inference_mode():
            if file_path and file_text:
                wav = _model.generate(
                    text=text,
                    ref_audio=file_path,
                    ref_text=file_text,
                    num_step=num_step,
                    speed=speed,
                )
            else:
                wav = _model.generate(
                    text=text,
                    instruct="male",
                    num_step=num_step,
                    speed=speed,
                )
        if isinstance(wav, torch.Tensor):
            wav = wav.detach().cpu().numpy()
        sf.write(str(output_path), wav[0], 24000)
        return output_path
    except Exception as e:
        print("[OmniVoice ERROR]", e)
        return None


# =========================================
# LOAD
# =========================================

def load_omni():
    global _loaded
    if not _loaded:
        init_tts()
        _loaded = True


# =========================================
# UNLOAD
# =========================================

def unload_omni():
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
        print("[OmniVoice] unloaded")
        return True
    except Exception as e:
        print("[OmniVoice unload error]", e)
        return False