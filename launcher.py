import hashlib
import os
import subprocess
import sys
import shutil

# -------------------------------------------------
# base directory
# -------------------------------------------------
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VENV_DIR = os.path.join(BASE_DIR, "venv")

PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")

MARKER_FILE = os.path.join(VENV_DIR, ".kirpi_installed")
TORCH_MARKER = os.path.join(VENV_DIR, ".torch_installed")


# -------------------------------------------------
# helpers
# -------------------------------------------------
def run(cmd):
    subprocess.check_call(cmd)


# -------------------------------------------------
# find system python
# -------------------------------------------------
def find_python():

    python_cmd = shutil.which("python")

    if python_cmd:
        return python_cmd

    python_cmd = shutil.which("py")

    if python_cmd:
        return python_cmd

    raise RuntimeError("Python not found on system.")


# -------------------------------------------------
# add ffmpeg
# -------------------------------------------------
def add_ffmpeg_to_path():

    ffmpeg_dir = os.path.join(BASE_DIR, "data", "ff_exe")

    if not os.path.exists(ffmpeg_dir):
        return

    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

    if sys.platform == "win32":
        try:
            os.add_dll_directory(ffmpeg_dir)
        except Exception:
            pass

    print("🎬 FFmpeg path added:", ffmpeg_dir)


# -------------------------------------------------
# create venv
# -------------------------------------------------
def create_venv():

    if os.path.exists(PYTHON):
        return

    print("📦 Creating virtual environment...")

    python_cmd = find_python()

    run([python_cmd, "-m", "venv", VENV_DIR])


# -------------------------------------------------
# detect GPU
# -------------------------------------------------
def detect_gpu():

    try:

        gpu = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]
        ).decode().strip().lower()

        print("🎮 GPU detected:", gpu)

        if "50" in gpu:
            return "cu129"

        if "40" in gpu:
            return "cu129"

        if "30" in gpu:
            return "cu121"

        if "20" in gpu:
            return "cu118"

    except Exception:
        pass

    print("⚠️ GPU not detected, installing CPU torch")

    return "cpu"


# -------------------------------------------------
# install torch
# -------------------------------------------------
def install_torch(cuda):

    if os.path.exists(TORCH_MARKER):
        return

    print("🔥 Installing PyTorch:", cuda)

    if cuda == "cpu":

        run([
            PYTHON,
            "-m",
            "pip",
            "install",
            "torch==2.8.0",
            "torchvision==0.23.0",
            "torchaudio==2.8.0"
        ])

    else:

        index = f"https://download.pytorch.org/whl/{cuda}"

        run([
            PYTHON,
            "-m",
            "pip",
            "install",
            "torch==2.8.0",
            "torchvision==0.23.0",
            "torchaudio==2.8.0",
            "--index-url",
            index
        ])

    open(TORCH_MARKER, "w").close()


# -------------------------------------------------
# install requirements
# -------------------------------------------------
def install_requirements():

    req_file = os.path.join(BASE_DIR, "requirements.txt")

    with open(req_file, "rb") as f:
        req_hash = hashlib.sha256(f.read()).hexdigest()

    if os.path.exists(MARKER_FILE):

        with open(MARKER_FILE, "r") as f:
            saved_hash = f.read()

        if saved_hash == req_hash:
            return

    print("📦 Installing requirements...")

    run([PYTHON, "-m", "pip", "install", "--upgrade", "pip"])

    run([PYTHON, "-m", "pip", "install", "-r", req_file])

    with open(MARKER_FILE, "w") as f:
        f.write(req_hash)


# -------------------------------------------------
# run client
# -------------------------------------------------
def run_client():

    print("🚀 Starting Kirpi AI Client")

    env = os.environ.copy()

    subprocess.call(
        [PYTHON, "main.py"],
        cwd=BASE_DIR,
        env=env
    )


# -------------------------------------------------
# main
# -------------------------------------------------
def main():

    add_ffmpeg_to_path()

    create_venv()

    add_ffmpeg_to_path()

    cuda = detect_gpu()

    install_torch(cuda)

    install_requirements()

    run_client()


# -------------------------------------------------
# entry
# -------------------------------------------------
if __name__ == "__main__":

    try:
        main()

    except Exception:
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")