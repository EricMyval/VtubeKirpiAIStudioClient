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

from modules.client.runtime.playback_state import playback_state


class TTSRuntime:

    def __init__(self, device=None):

        if device is None:
            cfg = load_config()
            device = cfg.get("output_device")

        self.device = device

        self.segment_queue = queue.Queue()
        self.stop_event = threading.Event()

        self.generator_thread = None
        self.player_thread = None

        # текущий stream чтобы можно было мгновенно остановить
        self.current_stream = None

    # =========================================

    def reload_device(self):
        cfg = load_config()
        self.device = cfg.get("output_device")
        print("[TTS] device reloaded:", self.device)

    # =========================================
    # PREPARE
    # =========================================

    def prepare(self, text, voice_file_path, voice_reference_text):

        self.stop()

        self.stop_event.clear()
        self.segment_queue = queue.Queue()

        self.generator_thread = threading.Thread(
            target=self._generator_loop,
            args=(text, voice_file_path, voice_reference_text),
            daemon=True
        )
        self.generator_thread.start()

        try:
            first_segment = self.segment_queue.get(timeout=10)
        except queue.Empty:
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

        while True:

            if self.stop_event.is_set() or playback_state.is_skip():
                break

            if not self.player_thread.is_alive():
                break

            time.sleep(0.05)

    # =========================================
    # STOP
    # =========================================

    def stop(self):

        self.stop_event.set()

        # мгновенно останавливаем stream
        if self.current_stream:
            try:
                self.current_stream.abort()
            except:
                pass

        # очищаем очередь сегментов
        try:
            while True:
                file = self.segment_queue.get_nowait()
                if file:
                    try:
                        Path(file).unlink(missing_ok=True)
                    except:
                        pass
        except queue.Empty:
            pass

        # будим player_loop
        try:
            self.segment_queue.put_nowait(None)
        except:
            pass

    # =========================================
    # GENERATOR
    # =========================================

    def _generator_loop(self, text, voice_file_path, voice_reference_text):

        segments = split_text(text)

        for i, segment in enumerate(segments):

            if self.stop_event.is_set() or playback_state.is_skip():
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

                if self.stop_event.is_set() or playback_state.is_skip():
                    try:
                        Path(file_path).unlink(missing_ok=True)
                    except:
                        pass
                    return

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

            if self.stop_event.is_set() or playback_state.is_skip():
                return

            if file_path is None:
                return

            # если skip — не открываем файл
            if playback_state.is_skip():
                return

            self._play_file(file_path)

            try:
                Path(file_path).unlink(missing_ok=True)
            except:
                pass

            try:
                file_path = self.segment_queue.get(timeout=0.5)
            except queue.Empty:
                continue

    # =========================================
    # PLAY FILE
    # =========================================

    def _play_file(self, wav_path):

        if self.stop_event.is_set() or playback_state.is_skip():
            return

        try:
            data, sr = sf.read(str(wav_path), dtype="float32")
        except Exception:
            return

        print("[TTS PLAYER] play:", wav_path)

        if data.ndim == 1:
            data = np.stack([data, data], axis=1)

        total_frames = len(data)
        position = 0
        finished = False

        device_index = None

        if self.device:
            try:
                device_index = resolve_output_device_index(self.device)
                print(f"[TTS] using device: {self.device} -> {device_index}")
            except Exception as e:
                print("[TTS] device resolve error:", e)

        def callback(outdata, frames, time_info, status):
            nonlocal position, finished

            if self.stop_event.is_set() or playback_state.is_skip():
                finished = True
                raise sd.CallbackStop()

            if not playback_state.pause_event.is_set():
                outdata.fill(0)
                return

            end = position + frames
            chunk = data[position:end]

            if len(chunk) < frames:
                outdata[:len(chunk)] = chunk
                outdata[len(chunk):].fill(0)
                finished = True
                raise sd.CallbackStop()

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
            ) as stream:

                self.current_stream = stream

                while not finished:

                    if self.stop_event.is_set() or playback_state.is_skip():
                        break

                    time.sleep(0.02)

        except Exception as e:
            print("[TTS] playback error:", e)

        finally:
            self.current_stream = None


tts_runtime = TTSRuntime()