import threading
import queue
import time
from pathlib import Path
import numpy as np
import soundfile as sf
import sounddevice as sd
from modules.audio.devices import resolve_output_device_index
from modules.audio.models import load_config
from modules.tts.service import tts_create_file
from modules.tts.tts_segmenter import split_text


class TTSRuntime:

    def __init__(self):

        cfg = load_config()
        self.device = cfg.get("output_device")

        self.segment_queue = queue.Queue()

    # ======================================
    # PREPARE (WAIT FIRST SEGMENT)
    # ======================================

    def prepare(self, text, voice_file_path, voice_reference_text):

        segments = split_text(text)

        if not segments:
            segments = [text]

        self.segment_queue = queue.Queue()

        threading.Thread(
            target=self._generator,
            args=(segments, voice_file_path, voice_reference_text),
            daemon=True
        ).start()

        try:
            first_segment = self.segment_queue.get(timeout=60)
        except queue.Empty:
            return None

        return first_segment

    # ======================================
    # PLAY ALL SEGMENTS
    # ======================================

    def play(self, first_segment):

        file_path = first_segment

        while True:

            if file_path is None:
                return

            self._play_file(file_path)

            try:
                Path(file_path).unlink(missing_ok=True)
            except:
                pass

            file_path = self.segment_queue.get()

    # ======================================
    # GENERATOR
    # ======================================

    def _generator(self, segments, voice_file_path, voice_reference_text):

        for i, segment in enumerate(segments):

            start = time.perf_counter()

            try:

                file_path = tts_create_file(
                    segment,
                    voice_file_path,
                    voice_reference_text
                )

                elapsed = time.perf_counter() - start

                print(
                    f"[TTS] segment {i+1}/{len(segments)} "
                    f"{len(segment)} chars → {elapsed:.2f}s"
                )

                if file_path:
                    self.segment_queue.put(file_path)

            except Exception as e:

                print("[TTS] generation error:", e)

        self.segment_queue.put(None)

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
            data = np.stack([data, data], axis=1)

        device_index = None

        if self.device:
            try:
                device_index = resolve_output_device_index(self.device)
            except Exception as e:
                print("[TTS] device resolve error:", e)

        try:

            sd.play(
                data,
                sr,
                device=device_index
            )

            sd.wait()

        except Exception as e:

            print("[TTS] playback error:", e)


tts_runtime = TTSRuntime()