import hashlib
import os
import subprocess
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VENV_DIR = os.path.join(BASE_DIR, "venv")

PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
PIP = os.path.join(VENV_DIR, "Scripts", "pip.exe")

MARKER_FILE = os.path.join(VENV_DIR, ".kirpi_installed")


# -----------------------------
# helpers
# -----------------------------
def run(cmd):
    subprocess.check_call(cmd)


def add_ffmpeg_to_path():
    ffmpeg_dir = os.path.join(BASE_DIR, "data", "ff_exe")

    if os.path.exists(ffmpeg_dir):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
        print("🎬 FFmpeg path added:", ffmpeg_dir)

# -----------------------------
# create venv
# -----------------------------
def create_venv():

    if os.path.exists(PYTHON):
        return

    print("📦 Creating virtual environment...")

    run(["python", "-m", "venv", VENV_DIR])


# -----------------------------
# detect GPU
# -----------------------------
def detect_gpu():

    try:
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]
        ).decode()

        gpu = result.strip()

        print("🎮 GPU detected:", gpu)

        if "50" in gpu:
            return "cu130"

        if "40" in gpu:
            return "cu128"

        if "30" in gpu:
            return "cu121"

        if "20" in gpu:
            return "cu118"

    except Exception:
        pass

    print("⚠️ GPU not detected, installing CPU torch")

    return "cpu"


# -----------------------------
# install torch
# -----------------------------
def install_torch(cuda):

    print("🔥 Installing PyTorch:", cuda)

    if cuda == "cpu":

        run([
            PIP,
            "install",
            "torch",
            "torchvision",
            "torchaudio"
        ])

        return

    index = f"https://download.pytorch.org/whl/{cuda}"

    run([
        PIP,
        "install",
        "torch",
        "torchvision",
        "torchaudio",
        "--index-url",
        index
    ])


# -----------------------------
# install requirements
# -----------------------------
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

    run([PIP, "install", "-r", req_file])

    with open(MARKER_FILE, "w") as f:
        f.write(req_hash)


# -----------------------------
# run client
# -----------------------------
def run_client():

    print("🚀 Starting Kirpi AI Client")

    subprocess.call([PYTHON, "main.py"])


# -----------------------------
# main
# -----------------------------
def main():
    create_venv()
    cuda = detect_gpu()
    install_torch(cuda)
    install_requirements()
    add_ffmpeg_to_path()
    run_client()


if __name__ == "__main__":
    main()