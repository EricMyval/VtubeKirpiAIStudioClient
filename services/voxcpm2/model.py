import time
from pathlib import Path
import torch
import soundfile as sf
from voxcpm import VoxCPM

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
_model = None

def load_model():
    global _model
    if _model is not None:
        return
    _model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)

def generate_wav(text, voice_file=None, voice_text=None):
    global _model
    if _model is None:
        load_model()

    cfg = 2.0
    steps = 10

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{int(time.time() * 1000)}.wav"
    try:
        with torch.inference_mode():
            if voice_file and voice_text:
                wav = _model.generate(
                    text=text,
                    prompt_wav_path=voice_file,
                    prompt_text=voice_text,
                    reference_wav_path=voice_file,
                    cfg_value=cfg,
                    inference_timesteps=steps,
                )
            elif voice_file:
                wav = _model.generate(
                    text=text,
                    reference_wav_path=voice_file,
                    cfg_value=cfg,
                    inference_timesteps=steps,
                )
            else:
                wav = _model.generate(
                    text=text,
                    cfg_value=cfg,
                    inference_timesteps=steps,
                )
        sf.write(str(output_path), wav, _model.tts_model.sample_rate)
        return output_path

    except Exception as e:
        print("[VoxCPM2 ERROR]", e)
        raise