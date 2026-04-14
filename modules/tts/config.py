import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path


CONFIG_PATH = Path("data/db/tts_config.json")


@dataclass
class TTSRuntimeConfig:

    # ===== ENGINE =====
    tts_engine: str

    # ===== F5 =====
    max_chunk_size: int
    mel_spec_type: str
    target_rms: float
    cross_fade_duration: float
    nfe_step: int
    cfg_strength: float
    sway_sampling_coef: float
    speed: float
    fix_duration: Optional[float]
    enable_accent: bool

    # ===== QWEN3 =====
    qwen3_do_sample: bool
    qwen3_top_k: int
    qwen3_top_p: float
    qwen3_temperature: float
    qwen3_repetition_penalty: float
    qwen3_max_new_tokens: int

    qwen3_subtalker_dosample: bool
    qwen3_subtalker_top_k: int
    qwen3_subtalker_top_p: float
    qwen3_subtalker_temperature: float

    qwen3_no_repeat_ngram_size: int
    qwen3_use_cache: bool

    # ===== VIBEVOICE =====
    vibevoice_comfyui_url: str

    # ===== FISH AUDIO S2 =====
    fishs2_url: str

    # ===== VOXCPM2 =====
    voxcpm2_cfg_value: float
    voxcpm2_inference_steps: int

    # ===== OMNIVOICE =====
    omni_num_step: int
    omni_inference_speed: float

    def to_infer_params(self, device: str) -> Dict[str, Any]:
        return {
            "mel_spec_type": self.mel_spec_type,
            "target_rms": self.target_rms,
            "cross_fade_duration": self.cross_fade_duration,
            "nfe_step": self.nfe_step,
            "cfg_strength": self.cfg_strength,
            "sway_sampling_coef": self.sway_sampling_coef,
            "speed": self.speed,
            "fix_duration": self.fix_duration,
            "device": device
        }


# =========================
# DEFAULT CONFIG (со скрина)
# =========================

DEFAULT_CONFIG = TTSRuntimeConfig(

    # ENGINE
    tts_engine="f5",

    # ===== F5 =====
    max_chunk_size=180,
    mel_spec_type="vocos",
    target_rms=0.15,
    cross_fade_duration=0.2,
    nfe_step=40,
    cfg_strength=2.5,
    sway_sampling_coef=-1,
    speed=1.0,
    fix_duration=None,
    enable_accent=True,

    # ===== QWEN3 =====
    qwen3_do_sample=True,
    qwen3_top_k = 40,
    qwen3_top_p = 0.93,
    qwen3_temperature = 1.1,
    qwen3_repetition_penalty = 1.07,
    qwen3_max_new_tokens = 1024,

    qwen3_subtalker_dosample = True,
    qwen3_subtalker_top_k = 30,
    qwen3_subtalker_top_p = 0.9,
    qwen3_subtalker_temperature = 1.08,

    qwen3_no_repeat_ngram_size = 3,
    qwen3_use_cache = True,

    # ===== VIBEVOICE =====
    vibevoice_comfyui_url="http://127.0.0.1:8188",

    # ===== FISH AUDIO S2 =====
    fishs2_url="http://127.0.0.1:8080",

    # ===== VOXCPM2 =====
    voxcpm2_cfg_value=1.8,
    voxcpm2_inference_steps = 16,

    # ===== OMNIVOICE =====
    omni_num_step=32,
    omni_inference_speed=1.0,
)


_runtime_config: TTSRuntimeConfig | None = None


# =========================
# FILE IO
# =========================

def load_or_create_config() -> TTSRuntimeConfig:

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # если файла нет — создаём
    if not CONFIG_PATH.exists():

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(DEFAULT_CONFIG), f, indent=2)

        print("[TTS] Default config created")

        return DEFAULT_CONFIG

    # читаем существующий
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # MERGE со значениями по умолчанию
    merged = {**asdict(DEFAULT_CONFIG), **data}

    # если появились новые поля — пересохраняем
    if merged != data:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2)
        print("[TTS] Config updated with new defaults")

    print("[TTS] Config loaded")

    return TTSRuntimeConfig(**merged)


def update_tts_engine(engine: str):
    data = asdict(load_or_create_config())
    data["tts_engine"] = engine

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    init_tts_config(TTSRuntimeConfig(**data))

# =========================
# INIT
# =========================

def init_tts_config(config: TTSRuntimeConfig):
    global _runtime_config
    _runtime_config = config


def get_tts_config() -> TTSRuntimeConfig:
    if _runtime_config is None:
        raise RuntimeError("TTS config не инициализирован")
    return _runtime_config


# =========================
# BOOTSTRAP
# =========================

def bootstrap_tts():
    try:
        config = load_or_create_config()
        init_tts_config(config)
    except Exception as e:
        print("[TTS] Config load failed:", e)