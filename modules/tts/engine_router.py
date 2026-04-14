from modules.tts.config import get_tts_config
from modules.tts.segmenter import split_text
from modules.tts.voice_f5 import tts_create_file as f5_create
from modules.tts.voice_qwen3 import tts_create_file as qwen_create
from modules.tts.voice_vibevoice import tts_create_file as vibe_create
from modules.tts.voice_fishs2 import tts_create_file as fishs2_create
from modules.tts.voice_voxcpm2 import tts_create_file as voxcpm2_create

def tts_create(text, voice_file, voice_text):
    engine = get_tts_config().tts_engine
    if engine == "f5":
        return f5_create(text, voice_file, voice_text)
    if engine == "qwen3":
        return qwen_create(text, voice_file, voice_text)
    if engine == "vibevoice":
        return vibe_create(text, voice_file, voice_text)
    if engine == "fishs2":
        return fishs2_create(text, voice_file, voice_text)
    if engine == "voxcpm2":
        return voxcpm2_create(text, voice_file, voice_text)
    raise RuntimeError(f"Unknown TTS engine: {engine}")

def prepare_segments(text: str):
    engine = get_tts_config().tts_engine
    if engine == "f5":
        return split_text(text) or [text]
    return [text]