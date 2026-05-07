import threading
import queue
from pathlib import Path
import numpy as np
import soundfile as sf
import sounddevice as sd
from modules.tts.engine import generate_wav
from modules.utils.devices import resolve_output_device_index
from modules.cabinet.models import load_config
from modules.song_api.voice_acestep import tts_create_file

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
    # GENERATE (async → queue)
    # ======================================

    def generate(self, text, voice_file_path, voice_reference_text, event=None):
        result_queue = queue.Queue()
        if event and event.get("songs"):
            self.task_queue.put((
                text,
                voice_file_path,
                voice_reference_text,
                result_queue,
                event
            ))
            return result_queue
        self.task_queue.put((
            text,
            voice_file_path,
            voice_reference_text,
            result_queue,
            None
        ))
        return result_queue

    # ======================================
    # GENERATION WORKER (ONE THREAD)
    # ======================================

    def _generation_loop(self):
        while True:
            text, voice_file, voice_text, q, event = self.task_queue.get()
            try:
                file_path = None
                try:
                    if event is not None:
                        file_path = tts_create_file(event, voice_file)
                    else:
                        file_path = generate_wav(text, voice_file, voice_text)
                except Exception as e:
                    print("[TTS] generation error:", e)
                if file_path:
                    q.put(file_path)
                else:
                    print("[TTS] empty result")
            except Exception as e:
                print("[TTS] generator crash:", e)
            finally:
                self.task_queue.task_done()

    # ======================================
    # PLAY FILE (single)
    # ======================================

    def play_file(self, file_path):
        if not file_path:
            return
        if self.stop_event.is_set():
            self.stop_event.clear()
            return
        self._play_file(file_path)
        if "song_api_result" not in str(file_path):
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception:
                pass

    # ======================================
    # DEVICE RESOLVE
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
    # PLAY LOW LEVEL
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