import time
import re
from pathlib import Path
import torch
import soundfile as sf

OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "output"
_MODEL = None
_VOCODER = None
_ACCENT = None
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

F5_PARAMS = dict(
    mel_spec_type="vocos",
    target_rms=0.15,
    cross_fade_duration=0.2,
    nfe_step=40,
    cfg_strength=2.5,
    sway_sampling_coef=-1,
    speed=1.0,
    fix_duration=None
)

def _normalize_text(text: str):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace(":", ": ")
    if len(text) < 10:
        text += "..."
    words = text.split()
    if words and len(words[-1]) <= 4:
        text += "..."
    return text

def load_model():
    global _MODEL, _VOCODER, _ACCENT
    if _MODEL is not None:
        return
    print(f"[F5] loading on {_DEVICE}")
    from omegaconf import OmegaConf
    from hydra.utils import get_class
    from ruaccent import RUAccent
    from f5_tts.infer.utils_infer import load_model, load_vocoder
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    MODEL_FILE = str(PROJECT_ROOT / "data" / "f5_tts" / "model_last_inference.safetensors")
    CONFIG_FILE = str(PROJECT_ROOT / "data" / "f5_tts" / "F5TTS_Myval.yaml")
    cfg = OmegaConf.load(CONFIG_FILE)
    backbone = cfg.model.backbone
    model_cls = get_class(f"f5_tts.model.{backbone}")
    model_arc = OmegaConf.to_container(cfg.model.arch, resolve=True)
    mel_spec_type = cfg.model.mel_spec.mel_spec_type
    _MODEL = load_model(
        model_cls,
        model_arc,
        ckpt_path=MODEL_FILE,
        ode_method="euler",
        use_ema=True,
        device=_DEVICE,
    )
    _VOCODER = load_vocoder(
        vocoder_name=mel_spec_type,
        device=_DEVICE
    )
    _ACCENT = RUAccent()
    _ACCENT.load(
        omograph_model_size="turbo3.1",
        use_dictionary=True,
        tiny_mode=False
    )
    print("[F5] ready")

def generate_wav(text, voice_file, voice_text):
    global _MODEL, _VOCODER, _ACCENT
    if _MODEL is None:
        load_model()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    text = _normalize_text(text)
    text = transliterate_lower(text)
    if _ACCENT:
        try:
            text = _ACCENT.process_all(text)
            text = text.replace("+ ", "+")
        except Exception as e:
            print("[F5 Accent error]", e)
    from f5_tts.infer.utils_infer import infer_process
    try:
        wave, sr, _ = infer_process(
            ref_audio=voice_file,
            ref_text=voice_text,
            gen_text=text,
            model_obj=_MODEL,
            vocoder=_VOCODER,
            **F5_PARAMS,
        )
    except Exception as e:
        print("[F5 ERROR]", e)
        return None
    output_path = OUTPUT_DIR / f"{int(time.time()*1000)}.wav"
    if isinstance(wave, torch.Tensor):
        wave = wave.detach().cpu().numpy()
    sf.write(str(output_path), wave, sr)
    return output_path

def transliterate_lower(text: str) -> str:
    text = text.lower()
    rules = [
        ("shch", "щ"),
        ("sch", "щ"),
        ("ya", "я"),
        ("yo", "ё"),
        ("yu", "ю"),
        ("ye", "е"),
        ("yi", "и"),
        ("ee", "и"),
        ("zh", "ж"),
        ("ch", "ч"),
        ("sh", "ш"),
        ("th", "т"),
        ("kh", "х"),
        ("ph", "ф"),
        ("ts", "ц"),
        ("a", "а"), ("b", "б"), ("v", "в"), ("g", "г"), ("d", "д"),
        ("e", "е"), ("z", "з"), ("i", "и"), ("j", "ж"), ("k", "к"),
        ("l", "л"), ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"),
        ("r", "р"), ("s", "с"), ("t", "т"), ("u", "у"), ("f", "ф"),
        ("h", "х"), ("c", "к"), ("q", "к"), ("w", "в"), ("x", "кс"),
        ("y", "й"),
    ]
    for latin, cyr in rules:
        text = text.replace(latin, cyr)
    return text

def transliterate_cyr_to_lat(text: str) -> str:
    lat = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
        "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
        "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
        "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
        "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
        "ш": "sh", "щ": "sch", "ы": "y", "э": "e",
        "ю": "yu", "я": "ya",
    }
    text = text.lower()
    result = []
    for ch in text:
        if ch in lat:
            result.append(lat[ch])
        else:
            result.append(ch)
    return "".join(result)