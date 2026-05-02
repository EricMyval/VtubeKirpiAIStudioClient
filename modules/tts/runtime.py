import threading
import queue
from pathlib import Path
import numpy as np
import soundfile as sf
import sounddevice as sd

from modules.song_api.service import song_api_service
from modules.tts.engine import generate_wav
from modules.utils.devices import resolve_output_device_index
from modules.cabinet.models import load_config

END = object()


class TTSRuntime:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.stop_event = threading.Event()

        threading.Thread(
            target=self._generation_loop,
            daemon=True
        ).start()

    # ======================================
    # SKIP
    # ======================================

    def stop(self):
        self.stop_event.set()

    # ======================================
    # PUBLIC GENERATE
    # ======================================

    def generate(self, text, voice_file_path, voice_reference_text, event=None):
        # 🔥 SONG API
        if event:
            if song_api_service.is_enabled_for_amount(event.get("amount")):
                print("[TTS] 🎵 switching to SONG API")

                segments = [event.get("message")]
                segment_queue = queue.Queue()

                self.task_queue.put((
                    segments,
                    voice_file_path,
                    voice_reference_text,
                    segment_queue,
                    "song_api"
                ))

                return segment_queue

        # =========================
        # обычная логика
        # =========================

        segment_queue = queue.Queue()

        self.task_queue.put((
            [text],
            voice_file_path,
            voice_reference_text,
            segment_queue,
            None
        ))

        return segment_queue

    # ======================================
    # GENERATION WORKER (ONE THREAD)
    # ======================================

    def _generation_loop(self):
        while True:
            segments, voice_file, voice_text, q, forced_engine = self.task_queue.get()

            try:
                for segment in segments:
                    try:
                        # 🔥 SONG API (оставляем как есть)
                        if forced_engine == "song_api":
                            from modules.song_api.voice_acestep import tts_create_file

                            file_path = tts_create_file(
                                segment,
                                voice_file,
                                voice_text
                            )

                        # 🔥 основной TTS (единый движок)
                        else:
                            file_path = generate_wav(
                                segment,
                                voice_file,
                                voice_text
                            )

                    except Exception as e:
                        print("[TTS] generation error:", e)
                        file_path = None

                    if file_path:
                        q.put(file_path)
                    else:
                        print("[TTS] empty result")

            except Exception as e:
                print("[TTS] generator crash:", e)

            finally:
                q.put(END)
                self.task_queue.task_done()

    # ======================================
    # PLAY
    # ======================================

    def play(self, first_segment, segment_queue):
        file_path = first_segment

        while True:
            if self.stop_event.is_set():
                self.stop_event.clear()
                return

            if file_path is END:
                return

            if file_path:
                self._play_file(file_path)

                # удаляем временные файлы (не song_api)
                if "song_api_result" not in str(file_path):
                    try:
                        Path(file_path).unlink(missing_ok=True)
                    except Exception:
                        pass

            try:
                file_path = segment_queue.get(timeout=1)
            except queue.Empty:
                continue

    # ======================================
    # DEVICE RESOLVE (dynamic)
    # ======================================

    def _get_device_index(self):
        try:
            cfg = load_config()
            device = cfg.get("output_device")
            if not device:
                return None
            return resolve_output_device_index(device)
        except Exception as e:
            print("[TTS] device resolve error:", e)
            return None

    # ======================================
    # PLAY FILE
    # ======================================

    def _play_file(self, wav_path):
        try:
            data, sr = sf.read(str(wav_path), dtype="float32")
        except Exception as e:
            print("[TTS] read error:", e)
            return
        if data.ndim == 1:
            data = np.repeat(data[:, None], 2, axis=1)
        device_index = self._get_device_index()
        try:
            sd.play(data, sr, device=device_index)
            while sd.get_stream().active:
                if self.stop_event.is_set():
                    sd.stop()
                    return
                sd.sleep(50)
        except Exception as e:
            print("[TTS] playback error:", e)


tts_runtime = TTSRuntime()