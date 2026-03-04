import queue
import threading
from pathlib import Path
import time

import numpy as np
import soundfile as sf
import sounddevice as sd

from modules.client.tts.service import tts_create_file
from modules.client.tts.tts_segmenter import split_text


class TTSRuntime:

    def __init__(self, device=None):

        self.device = device

        self.segment_queue = queue.Queue()

        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

        self.pause_event.set()

        self.generator_thread = None
        self.player_thread = None

    # =========================================
    # PUBLIC
    # =========================================

    def speak(self, text, voice_file_path, voice_reference_text):

        self.stop()

        self.pause_event.set()
        self.stop_event.clear()

        self.segment_queue = queue.Queue()

        self.generator_thread = threading.Thread(
            target=self._generator_loop,
            args=(text, voice_file_path, voice_reference_text),
            daemon=True
        )

        self.player_thread = threading.Thread(
            target=self._player_loop,
            daemon=True
        )

        self.generator_thread.start()
        self.player_thread.start()

        # блокируем поток пока все доиграет
        self.generator_thread.join()
        self.player_thread.join()

    # =========================================

    def pause(self):
        print("[TTS] pause")
        self.pause_event.clear()

    def resume(self):
        print("[TTS] resume")
        self.pause_event.set()

    def stop(self):
        print("[TTS] stop")
        self.stop_event.set()

        try:
            while True:
                self.segment_queue.get_nowait()
        except queue.Empty:
            pass

    # =========================================
    # GENERATOR
    # =========================================

    def _generator_loop(self, text, voice_file_path, voice_reference_text):

        segments = split_text(text)

        for i, segment in enumerate(segments):

            if self.stop_event.is_set():
                return

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

                self.segment_queue.put(file_path)

            except Exception as e:
                print("[TTS] generation error:", e)

        # сигнал что генерация закончилась
        self.segment_queue.put(None)

    # =========================================
    # PLAYER
    # =========================================

    def _player_loop(self):

        while True:

            if self.stop_event.is_set():
                return

            file_path = self.segment_queue.get()

            if file_path is None:
                return

            self._play_file(file_path)

            try:
                Path(file_path).unlink(missing_ok=True)
            except:
                pass

    # =========================================
    # PLAY FILE
    # =========================================

    def _play_file(self, wav_path):

        print("[TTS PLAYER] play:", wav_path)

        data, sr = sf.read(str(wav_path), dtype="float32")

        if data.ndim == 1:
            data = np.stack([data, data], axis=1)

        chunk = 1024
        pos = 0
        total = len(data)

        stream = sd.OutputStream(
            samplerate=sr,
            channels=2,
            dtype="float32",
            device=self.device
        )

        stream.start()

        try:

            while pos < total:

                if self.stop_event.is_set():
                    return

                while not self.pause_event.is_set():
                    time.sleep(0.05)

                end = min(pos + chunk, total)

                stream.write(data[pos:end])

                pos = end

        finally:
            stream.stop()
            stream.close()


tts_runtime = TTSRuntime()