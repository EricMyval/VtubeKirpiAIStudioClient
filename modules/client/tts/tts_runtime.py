import queue
import threading
from pathlib import Path
import time

import numpy as np
import soundfile as sf
import sounddevice as sd

from modules.client.audio.devices import resolve_output_device_index
from modules.client.audio.models import load_config
from modules.client.tts.service import tts_create_file
from modules.client.tts.tts_segmenter import split_text


class TTSRuntime:

    def __init__(self, device=None):

        if device is None:
            cfg = load_config()
            device = cfg.get("output_device")

        self.device = device

        self.segment_queue = queue.Queue()

        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

        self.pause_event.set()

        self.generator_thread = None
        self.player_thread = None

    def reload_device(self):
        cfg = load_config()
        self.device = cfg.get("output_device")
        print("[TTS] device reloaded:", self.device)

    # =========================================
    # PREPARE (генерируем первый сегмент)
    # =========================================

    def prepare(self, text, voice_file_path, voice_reference_text):

        self.stop()

        self.pause_event.set()
        self.stop_event.clear()

        self.segment_queue = queue.Queue()

        self.generator_thread = threading.Thread(
            target=self._generator_loop,
            args=(text, voice_file_path, voice_reference_text),
            daemon=True
        )

        self.generator_thread.start()

        first_segment = self.segment_queue.get()

        if first_segment is None:
            return None

        return first_segment

    # =========================================
    # PLAY
    # =========================================

    def play(self, first_segment):

        self.player_thread = threading.Thread(
            target=self._player_loop,
            args=(first_segment,),
            daemon=True
        )

        self.player_thread.start()

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

        self.segment_queue.put(None)

    # =========================================
    # PLAYER
    # =========================================

    def _player_loop(self, first_segment):

        file_path = first_segment

        while True:

            if self.stop_event.is_set():
                return

            if file_path is None:
                return

            self._play_file(file_path)

            try:
                Path(file_path).unlink(missing_ok=True)
            except:
                pass

            file_path = self.segment_queue.get()

    # =========================================
    # OPEN AUDIO STREAM (WASAPI + fallback)
    # =========================================

    def _open_stream(self, sr, device_index):

        try:
            stream = sd.OutputStream(
                samplerate=sr,
                channels=2,
                dtype="float32",
                device=device_index,
                extra_settings=sd.WasapiSettings(exclusive=False)
            )
            print("[TTS] stream opened with WASAPI")
            return stream

        except Exception as e:

            print("[TTS] WASAPI failed, fallback:", e)

            stream = sd.OutputStream(
                samplerate=sr,
                channels=2,
                dtype="float32",
                device=device_index
            )

            print("[TTS] stream opened without WASAPI")

            return stream

    # =========================================
    # PLAY FILE
    # =========================================

    def _play_file(self, wav_path):

        print("[TTS PLAYER] play:", wav_path)

        data, sr = sf.read(str(wav_path), dtype="float32")

        if data.ndim == 1:
            data = np.stack([data, data], axis=1)

        total_frames = len(data)
        position = 0

        device_index = None

        if self.device:
            try:
                device_index = resolve_output_device_index(self.device)
                print(f"[TTS] using device: {self.device} -> {device_index}")
            except Exception as e:
                print("[TTS] device resolve error:", e)

        def callback(outdata, frames, time_info, status):
            nonlocal position

            if self.stop_event.is_set():
                raise sd.CallbackStop()

            if not self.pause_event.is_set():
                outdata.fill(0)
                return

            end = position + frames
            chunk = data[position:end]

            if len(chunk) < frames:
                outdata[:len(chunk)] = chunk
                outdata[len(chunk):].fill(0)
                raise sd.CallbackStop()
            else:
                outdata[:] = chunk

            position = end

        try:

            with sd.OutputStream(
                    samplerate=sr,
                    channels=2,
                    dtype="float32",
                    device=device_index,
                    callback=callback,
                    blocksize=2048
            ):

                duration_ms = int((total_frames / sr) * 1000) + 100
                sd.sleep(duration_ms)

        except Exception as e:
            print("[TTS] playback error:", e)


tts_runtime = TTSRuntime()