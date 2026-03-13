import threading
import queue
from pathlib import Path
import numpy as np
import soundfile as sf
import sounddevice as sd
from modules.tts.service import tts_create_file
from modules.tts.tts_segmenter import split_text
from modules.utils.devices import resolve_output_device_index
from modules.cabinet.models import load_config

END = object()

class TTSRuntime:
    def __init__(self):
        cfg = load_config()
        self.device = cfg.get("output_device")
        self.task_queue = queue.Queue()
        threading.Thread(
            target=self._generation_loop,
            daemon=True
        ).start()

    # ======================================
    # PUBLIC GENERATE
    # ======================================

    def generate(self, text, voice_file_path, voice_reference_text):
        segments = split_text(text) or [text]
        segment_queue = queue.Queue()
        self.task_queue.put((
            segments,
            voice_file_path,
            voice_reference_text,
            segment_queue
        ))
        return segment_queue

    # ======================================
    # GENERATION WORKER (ONE THREAD)
    # ======================================

    def _generation_loop(self):
        while True:
            segments, voice_file, voice_text, q = self.task_queue.get()
            try:
                for segment in segments:
                    file_path = None
                    try:
                        file_path = tts_create_file(
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
            if file_path is END:
                return
            if file_path:
                self._play_file(file_path)
                try:
                    Path(file_path).unlink(missing_ok=True)
                except Exception:
                    pass
            file_path = segment_queue.get()

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
            sd.wait()
        except Exception as e:
            print("[TTS] playback error:", e)


tts_runtime = TTSRuntime()