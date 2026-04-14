from modules.tts.config import get_tts_config
from modules.tts.segmenter import split_text
from modules.tts.voice_f5 import tts_create_file as f5_create
from modules.tts.voice_vibevoice import tts_create_file as vibe_create
from modules.tts.voice_fishs2 import tts_create_file as fishs2_create
from modules.tts.voice_voxcpm2 import tts_create_file as voxcpm2_create
from modules.tts.voice_omnivoice import tts_create_file as omni_create

ENGINES = {
    "f5": f5_create,
    "vibevoice": vibe_create,
    "fishs2": fishs2_create,
    "voxcpm2": voxcpm2_create,
    "omnivoice": omni_create,
}

def tts_create(text, voice_file, voice_text):
    engine = get_tts_config().tts_engine
    if engine not in ENGINES:
        raise RuntimeError(f"Unknown TTS engine: {engine}")
    return ENGINES[engine](text, voice_file, voice_text)

def prepare_segments(text: str):
    engine = get_tts_config().tts_engine
    if engine == "f5":
        return split_text(text) or [text]
    return [text]