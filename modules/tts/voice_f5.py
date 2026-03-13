# modules/client/tts/voice_f5.py

import time
import re
from pathlib import Path

import torch
import soundfile as sf

from modules.tts.config import get_tts_config

OUTPUT_DIR = Path("data/out_voice")
MODEL_FILE = str(Path("data/f5_tts/model_last_inference.safetensors"))
CONFIG_FILE = str(Path("data/f5_tts/F5TTS_Myval.yaml"))

# фиксируем device один раз
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

_model = None
_vocoder = None
_accent = None
_number_file = 0


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def _normalize_text(text: str):

    text = text.strip()

    text = re.sub(r"\s+", " ", text)

    # пробел после :
    text = text.replace(":", ": ")

    # если короткая фраза
    if len(text) < 10:
        text += "..."

    words = text.split()

    # короткое последнее слово
    if words and len(words[-1]) <= 4:
        text += "..."

    return text


# ==========================================================
# INTERNAL LOAD
# ==========================================================

def _init_f5():
    global _model, _vocoder, _accent

    try:

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        from omegaconf import OmegaConf
        from hydra.utils import get_class
        from ruaccent import RUAccent
        from f5_tts.infer.utils_infer import load_model, load_vocoder

        cfg = OmegaConf.load(CONFIG_FILE)

        backbone = cfg.model.backbone
        model_cls = get_class(f"f5_tts.model.{backbone}")
        model_arc = OmegaConf.to_container(cfg.model.arch, resolve=True)

        mel_spec_type = cfg.model.mel_spec.mel_spec_type

        print(f"[TTS] loading model on {_DEVICE}")

        _model = load_model(
            model_cls,
            model_arc,
            ckpt_path=MODEL_FILE,
            ode_method="euler",
            use_ema=True,
            device=_DEVICE,
        )

        _vocoder = load_vocoder(
            vocoder_name=mel_spec_type,
            device=_DEVICE
        )

        # Accent
        _accent = RUAccent()
        _accent.load(
            omograph_model_size="turbo3.1",
            use_dictionary=True,
            tiny_mode=False
        )

        print("[TTS] model loaded")

    except Exception as e:

        print("[TTS ERROR]:", e)

        _model = None
        _vocoder = None
        _accent = None


# ==========================================================
# PUBLIC LOAD
# ==========================================================

def load_tts():
    print("[TTS] loading TTS model...")
    _init_f5()


# ==========================================================
# GENERATION
# ==========================================================

def tts_create_file(text, file_path, file_text: str) -> Path | None:

    global _number_file

    if _model is None:
        raise RuntimeError("TTS не загружен. Вызовите load_tts().")

    settings = get_tts_config()

    # ------------------------------------------------------
    # normalize text
    # ------------------------------------------------------

    text = _normalize_text(text)

    # ------------------------------------------------------
    # Accent
    # ------------------------------------------------------

    if settings.enable_accent and _accent is not None:

        try:

            text = _accent.process_all(text)

            # ruaccent иногда ломает пробелы
            text = text.replace("+ ", "+")

        except Exception as e:

            print("[RuAccent error]:", e)

    params = settings.to_infer_params(_DEVICE)

    from f5_tts.infer.utils_infer import infer_process

    # ------------------------------------------------------
    # GENERATION (с fallback)
    # ------------------------------------------------------

    try:

        wave, sr, _ = infer_process(
            ref_audio=file_path,
            ref_text=file_text,
            gen_text=text,
            model_obj=_model,
            vocoder=_vocoder,
            **params,
        )

    except Exception as e:

        print("[TTS] generation error:", e)

        # fallback — пробуем безопасный текст
        safe_text = text + "..."

        try:

            wave, sr, _ = infer_process(
                ref_audio=file_path,
                ref_text=file_text,
                gen_text=safe_text,
                model_obj=_model,
                vocoder=_vocoder,
                **params,
            )

        except Exception as e2:

            print("[TTS] fallback failed:", e2)
            return None

    # ------------------------------------------------------
    # SAVE FILE
    # ------------------------------------------------------

    _number_file += 1

    output_path = OUTPUT_DIR / f"donation_{int(time.time())}_{_number_file}.wav"

    audio = wave

    if isinstance(audio, torch.Tensor):
        audio = audio.detach().cpu().numpy()

    sf.write(str(output_path), audio, sr)

    return output_path