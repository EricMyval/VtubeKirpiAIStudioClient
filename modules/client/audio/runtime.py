# modules/client/audio/runtime.py

from pathlib import Path
from typing import Optional
import numpy as np
import sounddevice as sd
import soundfile as sf
from threading import Event

from .devices import resolve_output_device_index

PREFERRED_SR = 48_000


def _to_float32_stereo(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x)

    if x.ndim == 1:
        x = x[:, None]

    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)

    if np.issubdtype(x.dtype, np.integer):
        info = np.iinfo(x.dtype)
        x = x.astype(np.float32) / float(max(abs(info.min), info.max))
    else:
        x = x.astype(np.float32, copy=False)

    return x


def _resample_linear(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    if sr_in == sr_out:
        return x

    n_in = x.shape[0]
    n_out = int(round(n_in * (sr_out / sr_in)))

    t_in = np.linspace(0.0, 1.0, n_in, endpoint=False)
    t_out = np.linspace(0.0, 1.0, n_out, endpoint=False)

    y = np.empty((n_out, x.shape[1]), dtype=np.float32)

    for ch in range(x.shape[1]):
        y[:, ch] = np.interp(t_out, t_in, x[:, ch]).astype(np.float32)

    return y


def play(
    wav_path: Path,
    device_name: str,
    file_delete: bool = False,
    stop_event: Optional[Event] = None,
    pause_event: Optional[Event] = None,
) -> bool:

    try:
        device_idx = resolve_output_device_index(device_name)

        data, sr = sf.read(str(wav_path), always_2d=False)
        data = _to_float32_stereo(data)

        if sr != PREFERRED_SR:
            data = _resample_linear(data, sr, PREFERRED_SR)
            sr = PREFERRED_SR

        total_frames = len(data)
        position = 0

        def callback(outdata, frames, time_info, status):
            nonlocal position

            if stop_event and stop_event.is_set():
                raise sd.CallbackStop()

            if pause_event and not pause_event.is_set():
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

        with sd.OutputStream(
            samplerate=sr,
            channels=2,
            dtype="float32",
            device=device_idx,
            callback=callback,
            blocksize=2048,
        ):
            sd.sleep(int((total_frames / sr) * 1000) + 100)

        return True

    except Exception as e:
        print("[Audio]", e)
        return False

    finally:
        if file_delete:
            Path(wav_path).unlink(missing_ok=True)