import threading
import queue
from pathlib import Path
import numpy as np
import soundfile as sf
import sounddevice as sd

from modules.song_api.service import song_api_service
from modules.tts.engine_router import tts_create, prepare_segments
from modules.utils.devices import resolve_output_device_index
from modules.cabinet.models import load_config

END = object()

class TTSRuntime:
    def __init__(self):
        cfg = load_config()
        self.device = cfg.get("output_device")

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

        segments = prepare_segments(text)
        segment_queue = queue.Queue()

        self.task_queue.put((
            segments,
            voice_file_path,
            voice_reference_text,
            segment_queue,
            None  # 🔥 ВАЖНО
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
                    file_path = None

                    try:
                        if forced_engine:
                            from modules.tts.engine_router import ENGINES
                            file_path = ENGINES[forced_engine](
                                segment,
                                voice_file,
                                voice_text
                            )
                        else:
                            file_path = tts_create(
                                segment,
                                voice_file,
                                voice_text
                            )

                    except Exception as e:
                        print("[TTS] generation error:", e)

                    if file_path:
                        q.put(file_path)
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
                if file_path and "song_api_result" not in str(file_path):
                    try:
                        Path(file_path).unlink(missing_ok=True)
                    except:
                        pass
            try:
                file_path = segment_queue.get(timeout=1)
            except queue.Empty:
                continue

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

        device_index = None

        if self.device:
            try:
                device_index = resolve_output_device_index(self.device)
            except Exception as e:
                print("[TTS] device resolve error:", e)

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