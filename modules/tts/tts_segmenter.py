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

    while i < length:
        ch = text[i]
        buffer.append(ch)

        if ch in ".!?":
            j = i + 1

            while j < length and text[j] in ".!?":
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

    return chunks