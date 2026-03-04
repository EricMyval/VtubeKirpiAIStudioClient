from dataclasses import dataclass
from typing import Optional, Dict, Any


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


_runtime_config: TTSRuntimeConfig | None = None


def init_tts_config(data: dict):
    global _runtime_config

    _runtime_config = TTSRuntimeConfig(**data)


def get_tts_config() -> TTSRuntimeConfig:
    if _runtime_config is None:
        raise RuntimeError("TTS config не инициализирован")
    return _runtime_config