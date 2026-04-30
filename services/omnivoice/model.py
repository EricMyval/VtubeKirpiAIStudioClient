import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

import time
from pathlib import Path
import torch
import soundfile as sf
from omnivoice import OmniVoice


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
MODEL_PATH = BASE_DIR / "models" / "omnivoice"
_model = None

def load_model():
    global _model

    if _model is not None:
        return

    print("[OmniVoice] loading...")

    for attempt in range(3):
        try:
            use_cuda = torch.cuda.is_available() and attempt < 2  # 👈 ключ

            device = "cuda:0" if use_cuda else "cpu"
            dtype = torch.float16 if use_cuda else torch.float32

            print(f"[OmniVoice] attempt {attempt + 1} → device={device}")

            _model = OmniVoice.from_pretrained(
                str(MODEL_PATH),
                device_map=device,
                dtype=dtype,
                local_files_only=True
            )

            print(f"[OmniVoice] ready on {device}")
            return

        except Exception as e:
            print(f"[OmniVoice] load error (attempt {attempt + 1}):", e)

            import gc
            gc.collect()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            time.sleep(1)

    raise RuntimeError("Model load failed")


def generate_wav(text, voice_file=None, voice_text=None, num_step=32, speed=1.0):
    global _model
    if _model is None:
        load_model()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{int(time.time()*1000)}.wav"
    try:
        with torch.inference_mode():
            if voice_file and voice_text:
                wav = _model.generate(
                    text=text,
                    ref_audio=voice_file,
                    ref_text=voice_text,
                    num_step=num_step,
                    speed=speed,
                )
            else:
                wav = _model.generate(
                    text=text,
                    instruct="male",
                    num_step=num_step,
                    speed=speed,
                )
        if isinstance(wav, torch.Tensor):
            wav = wav.detach().cpu().numpy()
        sf.write(str(output_path), wav[0], 24000)
        return output_path
    except Exception as e:
        print("[OmniVoice ERROR]", e)
        raise