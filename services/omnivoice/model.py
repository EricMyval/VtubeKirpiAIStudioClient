import time
from pathlib import Path
import torch
import soundfile as sf
from omnivoice import OmniVoice

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
_model = None

def load_model():
    global _model
    if _model is not None:
        return
    print("[OmniVoice] loading...")
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    _model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map=device,
        dtype=dtype
    )
    print(f"[OmniVoice] ready on {device}")


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