# modules/player/player_thread.py

import threading
import time
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import Tuple, Any

from modules.client.alerts.alert_engine import engine
from modules.client.alerts.alert_queue import push_alert
from modules.donation_image.donation_image import show_message_image
from modules.pets.pets_manager import pets_manager
from modules.phrases.phrases import message_non_commands
from modules.player.playback_controller import playback_controller
from modules.client.audio.runtime import play
from modules.player.donation_runtime import (
    donations_enabled,
    inc_stats,
    register_donation,
    finish_donation,
)
from modules.client.roulette.runtime import roulette_runtime
from modules.start_ends.start_end_sender import (
    execute_start_commands,
    execute_end_commands,
)
from modules.timer.timer import timer
from modules.tts.tts_router import tts_get_file
from modules.tts.tts_db import audio_db
from modules.utils.filtered_message import (
    split_text,
    transliterate_lower,
    censor_message,
    numbers_ru,
)
from modules.voice_select.VoiceDB import voice_db
from modules.web_sockets.sender import send_ws_command
from modules.ws_commands.ws_commands_db import ws_db


DATA_DIR = Path("data")
OUTPUT_DIR = DATA_DIR / "out_voice"

Task = Tuple[str, Any, Any, Any, float]
task_queue: "Queue[Task]" = Queue()
playback_lock = Lock()


# ==========================================================
# Worker
# ==========================================================

def speak_and_play_worker():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        task = task_queue.get()
        if task is None:
            task_queue.task_done()
            break

        donations_enabled.wait()

        kind, a, b, c, message_id = task

        try:
            with playback_lock:

                if kind == "action":
                    if a:
                        a()
                    finish_donation(message_id)

                elif kind == "audio":
                    output_path = a
                    first_callback = b
                    last_callback = c

                    if first_callback:
                        playback_controller.start_donation(last_callback)
                        first_callback()

                    play(
                        output_path,
                        True,
                        stop_event=playback_controller.stop_event,
                        pause_event=donations_enabled,
                    )

                    if last_callback and playback_controller.is_active():
                        last_callback()
                        playback_controller.finish_donation()
                        finish_donation(message_id)

        except Exception as e:
            print(f"[player_thread] Ошибка в задаче: {e}")

        finally:
            task_queue.task_done()


# ==========================================================
# Public API
# ==========================================================

def donate_play(user: str, message: str, amount_user: str, original_message: str = ""):
    amount = int(float(amount_user))
    message_id = time.time()

    register_donation(message_id)

    user = censor_message(user)
    original_message = censor_message(original_message)

    spoken_message = message_non_commands(message)
    spoken_message = transliterate_lower(spoken_message)
    spoken_message = censor_message(spoken_message)
    spoken_message = numbers_ru(spoken_message)

    message_split = split_text(spoken_message)

    voice_row = voice_db.find_voice_by_amount(amount)
    voice_id = voice_row["voice_id"] if voice_row else None
    voice_tts = voice_row["tts_engine"] if voice_row else None

    def first_playback_actions():
        inc_stats()

        try:
            if original_message:
                show_message_image(original_message, amount)
        except Exception as e:
            print(f"[player_thread] show_message_image error: {e}")

        execute_start_commands(amount, user, spoken_message)

        if amount > 0:
            roulette_runtime.add_amount(amount)

            profile = engine.find_profile(amount)
            payload = engine.build_alert_payload(
                profile=profile,
                user=user,
                amount=amount,
                message=original_message,
            )

            if payload:
                push_alert(payload)

            timer.add_donate_with_pets(
                pets_manager.get_timer_influence(),
                amount_user,
            )

    def last_playback_actions():
        execute_end_commands(amount, user, spoken_message)

        commands = ws_db.get_command_by_price(amount)

        for command, delay_seconds in commands:
            try:
                send_ws_command(command)
                pets_manager.trigger_by_ws_command(command)

                if delay_seconds and delay_seconds > 0:
                    time.sleep(delay_seconds)

            except Exception as e:
                print(f"[player_thread] WS error '{command}': {e}")

    for i, segment in enumerate(message_split):
        output_path = None

        if voice_row:
            try:
                file_path, file_text = audio_db.get_record_data(voice_id)

                start_time = time.perf_counter()
                output_path = tts_get_file(segment, file_path, file_text, voice_tts)
                elapsed = time.perf_counter() - start_time

                print(
                    f"[TTS] Segment {i + 1}/{len(message_split)} "
                    f"({len(segment)} chars) → {elapsed:.3f}s"
                )

            except Exception as e:
                print(f"[Ошибка TTS]: {e}")

        first_cb = first_playback_actions if i == 0 else None
        last_cb = last_playback_actions if i == len(message_split) - 1 else None

        if output_path:
            task_queue.put(("audio", output_path, first_cb, last_cb, message_id))


def donate_play_twitch_points(command: str, delay_seconds: int):
    message_id = time.time()
    register_donation(message_id)
    inc_stats()
    def action():
        try:
            send_ws_command(command)

            if delay_seconds and delay_seconds > 0:
                time.sleep(delay_seconds)
        except Exception as e:
            print(f"[player_thread] Twitch points WS error '{command}': {e}")
    task_queue.put(("action", action, None, None, message_id))

threading.Thread(target=speak_and_play_worker, daemon=True).start()