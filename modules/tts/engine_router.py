from modules.tts.config import get_tts_config
from modules.tts.segmenter import split_text
from modules.tts.voice_f5 import tts_create_file as f5_create
from modules.tts.voice_qwen3 import tts_create_file as qwen_create
from modules.tts.voice_vibevoice import tts_create_file as vibe_create

def tts_create(text, voice_file, voice_text):

    engine = get_tts_config().tts_engine

    if engine == "f5":
        return f5_create(text, voice_file, voice_text)

    if engine == "qwen3":
        return qwen_create(text, voice_file, voice_text)

    if engine == "vibevoice":
        return vibe_create(text, voice_file, voice_text)

    raise RuntimeError(f"Unknown TTS engine: {engine}")

def prepare_segments(text: str):
    engine = get_tts_config().tts_engine
    if engine == "f5":
        return split_text(text) or [text]
    # для Qwen3 и будущих TTS
    return [text]