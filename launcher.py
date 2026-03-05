import hashlib
import os
import subprocess
import sys
import shutil
import zipfile
import urllib.request
import ssl
# -------------------------------------------------
# GITHUB
# -------------------------------------------------

GITHUB_REPO = "https://github.com/EricMyval/VtubeKirpiAIStudioClient"
GITHUB_ZIP = "https://codeload.github.com/EricMyval/VtubeKirpiAIStudioClient/zip/refs/heads/master"

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
# update client from github
# -------------------------------------------------

def update_client():

    print("🌐 Checking for client updates...")

    zip_path = os.path.join(BASE_DIR, "client_update.zip")
    extract_dir = os.path.join(BASE_DIR, "_update")

    try:

        ssl._create_default_https_context = ssl._create_unverified_context

        urllib.request.urlretrieve(GITHUB_ZIP, zip_path)

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        extracted_root = os.path.join(
            extract_dir,
            os.listdir(extract_dir)[0]
        )

        for item in os.listdir(extracted_root):

            if item in ["venv", ".git"]:
                continue

            src = os.path.join(extracted_root, item)
            dst = os.path.join(BASE_DIR, item)

            if os.path.isdir(src):

                if not os.path.exists(dst):
                    shutil.copytree(src, dst)

                else:
                    for root, dirs, files in os.walk(src):
                        rel = os.path.relpath(root, src)
                        dst_root = os.path.join(dst, rel)

                        os.makedirs(dst_root, exist_ok=True)

                        for f in files:
                            shutil.copy2(
                                os.path.join(root, f),
                                os.path.join(dst_root, f)
                            )

            else:
                shutil.copy2(src, dst)

        shutil.rmtree(extract_dir)
        os.remove(zip_path)

        print("✅ Client updated")

    except Exception as e:

        print("⚠️ Update failed:", e)

# -------------------------------------------------
# find system python (FIXED)
# -------------------------------------------------

def find_python():

    # 1️⃣ сначала проверяем py launcher
    py = shutil.which("py")

    if py:
        try:
            out = subprocess.check_output(
                [py, "-3", "-c", "import sys;print(sys.executable)"],
                text=True
            ).strip()

            if os.path.exists(out):
                return out

        except Exception:
            pass

    # 2️⃣ обычный python
    python = shutil.which("python")

    if python and "WindowsApps" not in python:
        return python

    # 3️⃣ проверяем стандартные папки Python
    possible = [

        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",

        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python310\python.exe"),
    ]

    for p in possible:
        if os.path.exists(p):
            return p

    raise RuntimeError("Python not found.")

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

    # ensure pip exists
    run([PYTHON, "-m", "ensurepip"])

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

    run([PYTHON, "-m", "pip", "install", "--upgrade", "pip"])

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

    run([PYTHON, "-m", "pip", "install", "-r", req_file])

    with open(MARKER_FILE, "w") as f:
        f.write(req_hash)

# -------------------------------------------------
# run client
# -------------------------------------------------

def run_client():

    main_file = os.path.join(BASE_DIR, "main.py")

    if not os.path.exists(main_file):

        print("❌ main.py not found")
        print("Client files are missing or update failed.")
        input("\nPress Enter to exit...")
        return

    print("🚀 Starting Kirpi AI Client")

    env = os.environ.copy()

    subprocess.call(
        [PYTHON, main_file],
        cwd=BASE_DIR,
        env=env
    )

# -------------------------------------------------
# main
# -------------------------------------------------

def main():

    update_client()

    add_ffmpeg_to_path()

    create_venv()

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