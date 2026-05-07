import json
import re
import threading
import time
import wave

from modules.utils.ws_client import send_ws_command


TAG_PATTERN = re.compile(r"\{([^{}]*)\}")
TAG_CLEAN_PATTERN = re.compile(r"\{.*?\}")

DEFAULT_CHAR_WEIGHT = 1.0
SPACE_WEIGHT = 0.3

PAUSE_WEIGHTS = {
    ",": 2.0,
    ".": 2.5,
    "!": 2.5,
    "?": 2.5,
    "…": 3.0,
    ":": 2.0,
    ";": 2.0,
    "\n": 3.0,
}


def parse_tagged_text(text: str):
    """
    Возвращает список (tag, spoken_prefix)
    """
    result = []

    for match in TAG_PATTERN.finditer(text or ""):
        tag = match.group(1).strip()
        if not tag:
            continue

        spoken_prefix = clean_text_from_tags(text[:match.start()])
        result.append((tag, spoken_prefix))

    return result


def build_emotion_timeline(formatted_text: str, audio_duration: float):
    tag_positions = parse_tagged_text(formatted_text)

    if not tag_positions:
        return []

    spoken_text = clean_text_from_tags(formatted_text)
    total_weight = calculate_text_weight(spoken_text)

    if total_weight <= 0:
        return []

    timeline = []

    for tag, spoken_prefix in tag_positions:
        prefix_weight = calculate_text_weight(spoken_prefix)
        if prefix_weight >= total_weight:
            continue

        delay = audio_duration * (prefix_weight / total_weight)
        timeline.append((delay, tag))

    return timeline


def calculate_text_weight(text: str) -> float:
    """
    Считает условный вес текста для расчета таймингов TTS.

    Обычные символы весят 1.
    Пробелы весят меньше.
    Пунктуация и переносы строк весят больше, потому что TTS делает паузы.
    """
    weight = 0.0

    for ch in text:
        if ch in PAUSE_WEIGHTS:
            weight += PAUSE_WEIGHTS[ch]
        elif ch.isspace():
            weight += SPACE_WEIGHT
        else:
            weight += DEFAULT_CHAR_WEIGHT

    return weight


def get_audio_duration(file_path):
    """
    Получаем длительность wav файла
    """
    with wave.open(str(file_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def schedule_emotions_ws(formatted_text: str, audio_file, ws_address: str):
    """
    Запускает поток, который отправляет WS команды эмоций по рассчитанным таймингам
    """
    audio_duration = get_audio_duration(audio_file)
    timeline = build_emotion_timeline(formatted_text, audio_duration)

    if not timeline:
        return

    def worker():
        start_time = time.time()

        for delay, tag in timeline:
            sleep_time = (start_time + delay) - time.time()

            if sleep_time > 0:
                time.sleep(sleep_time)

            command = json.dumps(
                {
                    "action": "emotion",
                    "data": tag,
                },
                ensure_ascii=False,
            )

            send_ws_command(command, ws_address)

    threading.Thread(target=worker, daemon=True).start()


def clean_text_from_tags(text: str) -> str:
    """
    Удаляет все {теги} из текста и нормализует пробелы
    """
    if not text:
        return ""

    cleaned = TAG_CLEAN_PATTERN.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s+([.,!?…])", r"\1", cleaned)

    return cleaned.strip()
