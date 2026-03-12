import threading
import queue
from pathlib import Path
import numpy as np
import soundfile as sf
import sounddevice as sd

from modules.utils.devices import resolve_output_device_index
from modules.tts.service import tts_create_file
from modules.tts.tts_segmenter import split_text
from modules.cabinet.models import load_config


END = object()


class TTSRuntime:

    def __init__(self):
        cfg = load_config()
        self.device = cfg.get("output_device")

        self.segment_queue = queue.Queue()
        self.lock = threading.Lock()

    # ======================================
    # PREPARE
    # ======================================

    def prepare(self, text, voice_file_path, voice_reference_text):

        with self.lock:

            segments = split_text(text) or [text]

            self.segment_queue = queue.Queue()

            thread = threading.Thread(
                target=self._generator,
                args=(segments, voice_file_path, voice_reference_text),
                daemon=True
            )
            thread.start()

            try:
                first_segment = self.segment_queue.get(timeout=60)
            except queue.Empty:
                print("[TTS] prepare timeout")
                return None

            if first_segment is END:
                return None

            return first_segment

    # ======================================
    # PLAY
    # ======================================

    def play(self, first_segment):

        file_path = first_segment

        while True:

            if file_path is END:
                return

            if file_path:

                self._play_file(file_path)

                try:
                    Path(file_path).unlink(missing_ok=True)
                except Exception as e:
                    print("[TTS] delete error:", e)

            try:
                file_path = self.segment_queue.get(timeout=60)
            except queue.Empty:
                print("[TTS] queue timeout")
                return

    # ======================================
    # GENERATOR
    # ======================================

    def _generator(self, segments, voice_file_path, voice_reference_text):

        try:

            for i, segment in enumerate(segments):

                file_path = None

                for attempt in range(2):

                    try:

                        file_path = tts_create_file(
                            segment,
                            voice_file_path,
                            voice_reference_text
                        )

                        if file_path:
                            break

                    except Exception as e:

                        print(
                            f"[TTS] generation error "
                            f"(attempt {attempt + 1}): {e}"
                        )

                if not file_path and i == 0:
                    print("[TTS] first segment failed")
                    self.segment_queue.put(END)
                    return

                if file_path:
                    self.segment_queue.put(file_path)

        except Exception as e:

            print("[TTS] generator crashed:", e)

        finally:

            self.segment_queue.put(END)

    # ======================================
    # PLAY FILE
    # ======================================

    def _play_file(self, wav_path):

        try:
            data, sr = sf.read(str(wav_path), dtype="float32")
        except Exception as e:
            print("[TTS] read error:", e)
            return

        if len(data) == 0:
            print("[TTS] empty audio")
            return

        # mono -> stereo
        if data.ndim == 1:
            data = np.repeat(data[:, None], 2, axis=1)

        # fade-out (10ms)
        fade_len = int(sr * 0.01)
        fade = np.linspace(1, 0, fade_len)
        data[-fade_len:] *= fade[:, None]

        # tail silence (30ms)
        tail = np.zeros((int(sr * 0.03), data.shape[1]), dtype="float32")
        data = np.concatenate([data, tail], axis=0)

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