import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path


CONFIG_PATH = Path("data/db/tts_config.json")


@dataclass
class TTSRuntimeConfig:
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
    max_chunk_size=180,
    mel_spec_type="vocos",
    target_rms=0.15,
    cross_fade_duration=0.2,
    nfe_step=40,
    cfg_strength=2.5,
    sway_sampling_coef=-1,
    speed=1.0,
    fix_duration=None,
    enable_accent=True
)


_runtime_config: TTSRuntimeConfig | None = None


# =========================
# FILE IO
# =========================

def load_or_create_config() -> TTSRuntimeConfig:

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not CONFIG_PATH.exists():

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(DEFAULT_CONFIG), f, indent=2)

        print("[TTS] Default config created")

        return DEFAULT_CONFIG

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("[TTS] Config loaded")

    return TTSRuntimeConfig(**data)


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