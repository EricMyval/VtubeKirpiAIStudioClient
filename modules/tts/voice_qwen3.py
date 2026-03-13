import time
import re
from pathlib import Path

import torch
import soundfile as sf

from modules.tts.config import get_tts_config

OUTPUT_DIR = Path("data/out_voice")

_model = None
_loaded = False
_number_file = 0


# =========================================
# INIT
# =========================================

def init_tts(model_id="Qwen/Qwen3-TTS-12Hz-0.6B-Base"):

    global _model

    from qwen_tts import Qwen3TTSModel

    print("[Qwen3TTS] loading...")

    _model = Qwen3TTSModel.from_pretrained(
        model_id,
        device_map="cuda:0",
        dtype=torch.bfloat16
    )

    print("[Qwen3TTS] ready")


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

def tts_create_file(text, file_path, file_text):

    global _number_file

    if _model is None:
        raise RuntimeError("Qwen3 TTS not loaded")

    settings = get_tts_config()

    text = _normalize_text(text)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    _number_file += 1

    output_path = OUTPUT_DIR / f"qwen3_{int(time.time())}_{_number_file}.wav"

    with torch.inference_mode():

        wavs, sr = _model.generate_voice_clone(

            text=text,
            language="Russian",

            ref_audio=file_path,
            ref_text=file_text,

            do_sample=settings.qwen3_do_sample,
            top_k=settings.qwen3_top_k,
            top_p=settings.qwen3_top_p,
            temperature=settings.qwen3_temperature,
            repetition_penalty=settings.qwen3_repetition_penalty,
            max_new_tokens=settings.qwen3_max_new_tokens,

            subtalker_dosample=settings.qwen3_subtalker_dosample,
            subtalker_top_k=settings.qwen3_subtalker_top_k,
            subtalker_top_p=settings.qwen3_subtalker_top_p,
            subtalker_temperature=settings.qwen3_subtalker_temperature,

            no_repeat_ngram_size=settings.qwen3_no_repeat_ngram_size,
            use_cache=settings.qwen3_use_cache,
        )

    audio = wavs[0]

    if isinstance(audio, torch.Tensor):
        audio = audio.detach().cpu().numpy()

    sf.write(str(output_path), audio, sr)

    return output_path


# =========================================
# LOAD
# =========================================

def load_qwen3tts():

    global _loaded

    if not _loaded:

        init_tts()

        _loaded = True


# =========================================
# UNLOAD
# =========================================

def unload_qwen3tts():

    global _model, _loaded

    if not _loaded:
        return True

    try:

        if _model:

            try:
                _model.to("cpu")
            except:
                pass

            del _model

            _model = None

        if torch.cuda.is_available():

            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        _loaded = False

        print("[Qwen3TTS] unloaded")

        return True

    except Exception as e:

        print("[Qwen3TTS unload error]", e)

        return False