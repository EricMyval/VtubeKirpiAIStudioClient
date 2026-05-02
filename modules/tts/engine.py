# modules/tts/engine.py

from pathlib import Path
import time
import torch
import soundfile as sf
from omnivoice import OmniVoice

MODEL_PATH = Path("services/omnivoice/models/omnivoice")
OUTPUT_DIR = Path("data/output")
_model = None


def load_model():
    global _model
    if _model is not None:
        return _model
    print("[TTS] loading model...")
    for attempt in range(3):
        try:
            use_cuda = torch.cuda.is_available() and attempt < 2

            device = "cuda:0" if use_cuda else "cpu"
            dtype = torch.float16 if use_cuda else torch.float32

            _model = OmniVoice.from_pretrained(
                str(MODEL_PATH),
                device_map=device,
                dtype=dtype,
                local_files_only=True
            )

            print(f"[TTS] ready on {device}")
            return _model
        except Exception as e:
            print(f"[TTS] load error {attempt+1}:", e)

            import gc
            gc.collect()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            time.sleep(1)

    raise RuntimeError("TTS model load failed")


def generate_wav(text, voice_file=None, voice_text=None):
    global _model

    if _model is None:
        print("[TTS] not ready...")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{int(time.time()*1000)}.wav"

    start_time = time.time()

    with torch.inference_mode():
        if voice_file and voice_text:
            wav = _model.generate(
                text=text,
                ref_audio=voice_file,
                ref_text=voice_text
            )
        else:
            wav = _model.generate(
                text=text,
                instruct="male"
            )

    gen_time = time.time() - start_time

    if isinstance(wav, torch.Tensor):
        wav = wav.detach().cpu().numpy()

    # сохраняем
    sf.write(str(path), wav[0], 24000)

    # ===== метрики =====
    text_len = len(text)

    audio_duration = len(wav[0]) / 24000  # секунды аудио
    chars_per_sec = text_len / gen_time if gen_time > 0 else 0
    realtime_factor = audio_duration / gen_time if gen_time > 0 else 0

    print(
        f"[TTS] done | "
        f"time={gen_time:.2f}s | "
        f"chars={text_len} | "
        f"chars/sec={chars_per_sec:.2f} | "
        f"audio={audio_duration:.2f}s | "
        f"RTF={realtime_factor:.2f}"
    )

    return path