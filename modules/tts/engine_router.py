import requests
import re
from modules.tts.config import get_tts_config
from modules.tts.voice_vibevoice import tts_create_file as vibe_create

def call_tts_service(text, voice_file, voice_text):
    try:
        r = requests.post(
            "http://127.0.0.1:5001/generate",
            json={ "text": text, "voice_file": voice_file, "voice_text": voice_text},
            timeout=120,
            proxies={"http": None, "https": None}
        )
        return r.json().get("wav_path")
    except Exception as e:
        print("[TTS SERVICE ERROR]", e)
        return None

def song_api_create(text, voice_file, voice_text):
    from modules.song_api.service import song_api_service
    return song_api_service.generate_song(
        text=text,
        voice_path=voice_file,
        gender="male"
    )

ENGINES = {
    "f5": call_tts_service,
    "qwen3": call_tts_service,
    "vibevoice": vibe_create,
    "voxcpm2": call_tts_service,
    "omnivoice": call_tts_service,
    "song_api": song_api_create,
}

def tts_create(text, voice_file, voice_text):
    engine = get_tts_config().tts_engine
    if engine not in ENGINES:
        raise RuntimeError(f"Unknown TTS engine: {engine}")
    return ENGINES[engine](text, voice_file, voice_text)


def split_text(text: str) -> list[str]:
    max_chunk_size = get_tts_config().max_chunk_size
    if not text:
        return []
    text = text.strip()
    if not text:
        return []
    sentences = []
    buffer = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        buffer.append(ch)
        if ch in ".!?,":
            j = i + 1
            while j < length and text[j] in ".!?,":  # типа "!!!"
                buffer.append(text[j])
                j += 1
            sentence = "".join(buffer).strip()
            buffer.clear()
            if re.search(r"[a-zA-Zа-яА-Я0-9]", sentence):
                sentences.append(sentence)
            i = j - 1
        i += 1
    if buffer:
        tail = "".join(buffer).strip()
        if re.search(r"[a-zA-Zа-яА-Я0-9]", tail):
            sentences.append(tail)
    chunks = []
    current = ""
    for sentence in sentences:
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if len(sentence) > max_chunk_size:
            words = re.split(r"(\s+)", sentence)
            part = ""
            for word in words:
                if len(part) + len(word) <= max_chunk_size:
                    part += word
                else:
                    if part:
                        chunks.append(part.strip())
                    part = word
                    while len(part) > max_chunk_size:
                        chunks.append(part[:max_chunk_size])
                        part = part[max_chunk_size:]
            if part.strip():
                chunks.append(part.strip())
            current = ""
            continue
        if not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chunk_size:
            current += " " + sentence
        else:
            chunks.append(current.strip())
            current = sentence
    if current.strip():
        chunks.append(current.strip())
    merged = []
    buffer = ""
    for chunk in chunks:
        if len(chunk) < 15:
            buffer += " " + chunk
        else:
            if buffer:
                merged.append((buffer + " " + chunk).strip())
                buffer = ""
            else:
                merged.append(chunk)
    if buffer:
        merged.append(buffer.strip())
    final_chunks = []
    for chunk in merged:
        chunk = chunk.strip()
        if chunk.endswith("..."):
            final_chunks.append(chunk)
            continue
        if re.search(r"[.!?]$", chunk):
            chunk += "..."
        else:
            chunk += "..."
        final_chunks.append(chunk)
    return final_chunks

def prepare_segments(text: str):
    engine = get_tts_config().tts_engine
    if engine == "f5":
        return split_text(text) or [text]
    return [text]