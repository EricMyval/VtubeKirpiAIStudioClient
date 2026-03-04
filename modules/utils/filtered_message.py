import os
import re
from num2words import num2words

from modules.banned_words.banned_words_db import banned_words_db
from modules.tts.tts_f5_settings import load_voice_settings
from modules.tts.tts_qwen3_settings import qwen3_settings
from modules.tts.tts_select import get_selected_tts
from modules.tts.tts_vibevoice_settings import get_vibevoice_max_chunk_size

# ------------------------------------------------------------
# config for max_chunk_size
# ------------------------------------------------------------

_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

# ------------------------------------------------------------
# censor
# ------------------------------------------------------------

def censor_message(message: str) -> str:
    forbidden_words = banned_words_db.get_words_list()
    if not forbidden_words or not message:
        return message

    pattern = r'\b(' + '|'.join(re.escape(word) for word in forbidden_words) + r')\b'
    censored_message = re.sub(pattern, '', message, flags=re.IGNORECASE)
    return censored_message


# ------------------------------------------------------------
# split text
# ------------------------------------------------------------

def get_current_max_chunk_size() -> int:
    try:
        selected = get_selected_tts()
        if selected == "Qwen3 TTS":
            settings = qwen3_settings.get_all()
            return int(settings.get("max_chunk_size", 1000))
        elif selected == "F5 TTS":
            return int(load_voice_settings().max_chunk_size)
        elif selected == "Vibe Voice TTS":
            return int(get_vibevoice_max_chunk_size())
    except Exception:
        pass
    return 1000

def split_text(text: str) -> list[str]:
    max_chunk_size = get_current_max_chunk_size()

    if not text:
        return []

    text = text.strip()
    if not text:
        return []

    sentences: list[str] = []
    buffer = []

    i = 0
    length = len(text)

    # ===== 1. Ручной разбор предложений =====
    while i < length:
        ch = text[i]
        buffer.append(ch)

        if ch in '.!?':
            j = i + 1
            while j < length and text[j] in '.!?':
                buffer.append(text[j])
                j += 1

            sentence = ''.join(buffer).strip()
            buffer.clear()
            i = j - 1

            if re.search(r'[a-zA-Zа-яА-Я0-9]', sentence):
                sentences.append(sentence)

        i += 1

    # Хвост без знака конца предложения
    if buffer:
        tail = ''.join(buffer).strip()
        if re.search(r'[a-zA-Zа-яА-Я0-9]', tail):
            sentences.append(tail)

    # ===== 2. Сбор чанков с ограничением длины =====
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = re.sub(r'\s+', ' ', sentence).strip()

        # Если предложение само по себе слишком длинное
        if len(sentence) > max_chunk_size:
            words = re.split(r'(\s+)', sentence)
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


# ------------------------------------------------------------
# transliteration
# ------------------------------------------------------------

def transliterate_lower(text: str) -> str:
    text = text.lower()

    rules = [
        ("shch", "щ"),
        ("sch", "щ"),
        ("ya", "я"),
        ("yo", "ё"),
        ("yu", "ю"),
        ("ye", "е"),
        ("yi", "и"),
        ("ee", "и"),
        ("zh", "ж"),
        ("ch", "ч"),
        ("sh", "ш"),
        ("th", "т"),
        ("kh", "х"),
        ("ph", "ф"),
        ("ts", "ц"),

        ("a", "а"), ("b", "б"), ("v", "в"), ("g", "г"), ("d", "д"),
        ("e", "е"), ("z", "з"), ("i", "и"), ("j", "ж"), ("k", "к"),
        ("l", "л"), ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"),
        ("r", "р"), ("s", "с"), ("t", "т"), ("u", "у"), ("f", "ф"),
        ("h", "х"), ("c", "к"), ("q", "к"), ("w", "в"), ("x", "кс"),
        ("y", "й"),
    ]

    for latin, cyr in rules:
        text = text.replace(latin, cyr)

    return text


# ==========================================================
# Numbers
# ==========================================================

def _normalize_numbers_ru(text: str) -> str:
    def repl(m):
        s = m.group(0)
        if ',' in s or '.' in s:
            sep = ',' if ',' in s else '.'
            a, b = s.split(sep, 1)
            try:
                left = num2words(int(a), lang='ru')
                right = ' '.join(num2words(int(d), lang='ru') for d in b)
                if right == '':
                    return f"{left}"
                else:
                    return f"{left} целых {right}"
            except Exception:
                return s
        try:
            return num2words(int(s), lang='ru')
        except Exception:
            return s

    return re.sub(r'\d+[.,]?\d*', repl, text)


def numbers_ru(text: str) -> str:
    processed = re.sub(r'\s+', ' ', text).strip()
    if not processed:
        return ""
    processed = _normalize_numbers_ru(processed)
    processed = processed.replace('…', '...')
    return processed