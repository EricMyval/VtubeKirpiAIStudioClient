from modules.tts.config import get_tts_config
from modules.tts.voice_f5 import load_tts
from modules.tts.voice_qwen3 import load_qwen3tts
from modules.tts.voice_vibevoice import load_vibevoicetts
from modules.tts.voice_fishs2 import load_fishs2tts

def load_engine():
    engine = get_tts_config().tts_engine
    if engine == "f5":
        print("[TTS] Engine F5")
        load_tts()
    elif engine == "qwen3":
        print("[TTS] Engine Qwen3")
        load_qwen3tts()
    elif engine == "vibevoice":
        print("[TTS] engine: VibeVoice")
        load_vibevoicetts()
    elif engine == "fishs2":
        print("[TTS] engine: Fish Audio S2 Pro")
        load_fishs2tts()
    else:
        raise RuntimeError(f"Unknown TTS engine: {engine}")