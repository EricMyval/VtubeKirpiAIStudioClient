import re

from modules.tts.config import get_tts_config


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

    # ======================================
    # SPLIT BY PUNCTUATION
    # ======================================

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

    # ======================================
    # BUILD CHUNKS
    # ======================================

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

    # ======================================
    # FIX 1: MERGE TOO SHORT CHUNKS
    # ======================================

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

    # ======================================
    # FIX 2: FORCE ENDING PAUSE FOR TTS
    # ======================================

    final_chunks = []

    for chunk in merged:

        chunk = chunk.strip()

        # если уже заканчивается ...
        if chunk.endswith("..."):
            final_chunks.append(chunk)
            continue

        # если заканчивается . ! ?
        if re.search(r"[.!?]$", chunk):
            chunk += "..."
        else:
            chunk += "..."

        final_chunks.append(chunk)

    return final_chunks