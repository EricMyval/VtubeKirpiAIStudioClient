import time
from pathlib import Path
import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
_model = None

def load_model():
    global _model
    if _model is not None:
        return
    _model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-Base", device_map="cuda:0", dtype=torch.bfloat16)

def generate_wav(text, voice_file, voice_text):
    global _model
    if _model is None:
        load_model()

    qwen3_do_sample=True
    qwen3_top_k = 40
    qwen3_top_p = 0.93
    qwen3_temperature = 1.1
    qwen3_repetition_penalty = 1.07
    qwen3_max_new_tokens = 1024
    qwen3_subtalker_dosample = True
    qwen3_subtalker_top_k = 30
    qwen3_subtalker_top_p = 0.9
    qwen3_subtalker_temperature = 1.08
    qwen3_no_repeat_ngram_size = 3
    qwen3_use_cache = True

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{int(time.time() * 1000)}.wav"
    with torch.inference_mode():
        wavs, sr = _model.generate_voice_clone(
            text=text,
            language="Russian",
            ref_audio=voice_file,
            ref_text=voice_text,
            do_sample=qwen3_do_sample,
            top_k=qwen3_top_k,
            top_p=qwen3_top_p,
            temperature=qwen3_temperature,
            repetition_penalty=qwen3_repetition_penalty,
            max_new_tokens=qwen3_max_new_tokens,
            subtalker_dosample=qwen3_subtalker_dosample,
            subtalker_top_k=qwen3_subtalker_top_k,
            subtalker_top_p=qwen3_subtalker_top_p,
            subtalker_temperature=qwen3_subtalker_temperature,
            no_repeat_ngram_size=qwen3_no_repeat_ngram_size,
            use_cache=qwen3_use_cache,
        )
    audio = wavs[0]
    if isinstance(audio, torch.Tensor):
        audio = audio.detach().cpu().numpy()
    sf.write(str(output_path), audio, sr)
    return output_path