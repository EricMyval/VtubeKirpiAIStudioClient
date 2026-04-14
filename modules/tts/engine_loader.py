from modules.tts.config import get_tts_config
from modules.tts.voice_f5 import load_tts
from modules.tts.voice_qwen3 import load_qwen3tts
from modules.tts.voice_vibevoice import load_vibevoicetts
from modules.tts.voice_fishs2 import load_fishs2tts
from modules.tts.voice_voxcpm2 import load_voxcpm2
from modules.tts.voice_omnivoice  import load_omni

LOADERS = {
    "f5": load_tts,
    "qwen3": load_qwen3tts,
    "vibevoice": load_vibevoicetts,
    "fishs2": load_fishs2tts,
    "voxcpm2": load_voxcpm2,
    "omnivoice": load_omni,
}

def load_engine():
    engine = get_tts_config().tts_engine
    if engine not in LOADERS:
        raise RuntimeError(f"Unknown TTS engine: {engine}")
    print(f"[TTS] Engine {engine}")
    LOADERS[engine]()