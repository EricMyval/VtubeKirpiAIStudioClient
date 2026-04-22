import json
from dataclasses import dataclass, asdict
from pathlib import Path

CONFIG_PATH = Path("data/db/config_tts.json")

@dataclass
class TTSRuntimeConfig:
    tts_engine: str
    max_chunk_size: int
    vibevoice_comfyui_url: str

DEFAULT_CONFIG = TTSRuntimeConfig(
    tts_engine="omnivoice",
    max_chunk_size=180,
    vibevoice_comfyui_url="http://127.0.0.1:8188"
)
_runtime_config: TTSRuntimeConfig | None = None

def load_or_create_config() -> TTSRuntimeConfig:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(DEFAULT_CONFIG), f, indent=2)
        print("[TTS] Default config created")
        return DEFAULT_CONFIG
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = {**asdict(DEFAULT_CONFIG), **data}
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

def init_tts_config(config: TTSRuntimeConfig):
    global _runtime_config
    _runtime_config = config

def get_tts_config() -> TTSRuntimeConfig:
    if _runtime_config is None:
        raise RuntimeError("TTS config не инициализирован")
    return _runtime_config

def bootstrap_tts():
    try:
        config = load_or_create_config()
        init_tts_config(config)
    except Exception as e:
        print("[TTS] Config load failed:", e)