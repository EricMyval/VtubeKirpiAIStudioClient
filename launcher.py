import hashlib
import os
import subprocess
import sys
import shutil
import zipfile
import urllib.request
import ssl
import time
import threading
import itertools

SERVICES = ["voxcpm2", "qwen3", "omnivoice", "f5",]

GITHUB_REPO = "https://github.com/EricMyval/VtubeKirpiAIStudioClient"
GITHUB_ZIP = "https://codeload.github.com/EricMyval/VtubeKirpiAIStudioClient/zip/refs/heads/master"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PIP_CACHE_DIR = os.path.join(BASE_DIR, ".pip_cache")
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")
MARKER_FILE = os.path.join(VENV_DIR, ".kirpi_installed")

QUIET = True

def log(*args, **kwargs):
    if not QUIET:
        print(*args, **kwargs)

def run_silent(cmd):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    process.wait()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)

def progress_bar(title):
    state = {"percent": 0, "stop": False}

    def run():
        width = 30

        while not state["stop"]:
            p = state["percent"]
            filled = int(width * p / 100)
            bar = "█" * filled + "░" * (width - filled)

            print(f"\r{title} [{bar}] {p:3d}%", end="", flush=True)
            time.sleep(0.1)

    t = threading.Thread(target=run)
    t.daemon = True
    t.start()

    return state

def run_with_progress(cmd, pb, start=0, end=100):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    total_size = None

    for line in process.stdout:
        line = line.strip()

        # Пример:
        # Downloading ... (3571.8 MB)
        if "Downloading" in line and "(" in line and "MB" in line:
            try:
                size_str = line.split("(")[-1].split(")")[0]
                total_size = float(size_str.replace("MB", "").strip())
            except:
                pass

        # Пример:
        # 1234.5/3571.8 MB
        if "/" in line and "MB" in line:
            try:
                part = line.split()
                for p in part:
                    if "/" in p and "MB" in line:
                        current, total = p.split("/")
                        current = float(current)
                        total = float(total.replace("MB", ""))

                        percent = int((current / total) * 100)

                        pb["percent"] = start + int((end - start) * percent / 100)
                        break
            except:
                pass

        # fallback — обычные %
        elif "%" in line:
            try:
                percent = int(line.split("%")[0].split()[-1])
                pb["percent"] = start + int((end - start) * percent / 100)
            except:
                pass

    process.wait()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)

def download_file(url, dest):
    ssl._create_default_https_context = ssl._create_unverified_context
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "KirpiAIStudio"}
    )
    with urllib.request.urlopen(req) as response, open(dest, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

# -------------------------------------------------
# update client
# -------------------------------------------------

def update_client():
    zip_path = os.path.join(BASE_DIR, "client_update.zip")
    extract_dir = os.path.join(BASE_DIR, "_update")

    try:
        download_file(GITHUB_ZIP, zip_path)

        if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1000:
            raise RuntimeError("Downloaded archive is invalid")

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        repo_dir = None
        for name in os.listdir(extract_dir):
            path = os.path.join(extract_dir, name)
            if os.path.isdir(path):
                repo_dir = path
                break

        if not repo_dir:
            raise RuntimeError("Repository folder not found in archive")

        for item in os.listdir(repo_dir):
            if item in ["venv", ".git"]:
                continue

            src = os.path.join(repo_dir, item)
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

    except Exception as e:
        print(f"\n⚠️ Update failed: {e}")

# -------------------------------------------------
# find system python
# -------------------------------------------------

def find_python():

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

    python = shutil.which("python")

    if python and "WindowsApps" not in python:
        return python

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

    log("🎬 FFmpeg path added:", ffmpeg_dir)

# -------------------------------------------------
# create venv
# -------------------------------------------------

def create_venv():
    if os.path.exists(PYTHON):
        return

    python_cmd = find_python()

    run_silent([python_cmd, "-m", "venv", VENV_DIR])
    run_silent([PYTHON, "-m", "ensurepip"])

# -------------------------------------------------
# detect GPU
# -------------------------------------------------

def detect_gpu():

    try:

        gpu = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]
        ).decode().strip().lower()

        log("🎮 GPU detected:", gpu)

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

    log("⚠️ GPU not detected, installing CPU torch")

    return "cpu"

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

    run_silent([PYTHON, "-m", "pip", "install", "-r", req_file])

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
    log("🚀 Starting Kirpi AI Client")
    env = os.environ.copy()
    subprocess.call(
        [PYTHON, main_file],
        cwd=BASE_DIR,
        env=env
    )

# -------------------------------------------------
# SERVICE: create venv
# -------------------------------------------------

def create_service_venv(service_name):
    service_dir = os.path.join(BASE_DIR, "services", service_name)
    venv_dir = os.path.join(service_dir, "venv")
    python_path = os.path.join(venv_dir, "Scripts", "python.exe")

    if os.path.exists(python_path):
        return python_path

    if os.path.exists(venv_dir):
        shutil.rmtree(venv_dir, ignore_errors=True)

    python_cmd = find_python()

    run_silent([python_cmd, "-m", "venv", venv_dir, "--without-pip"])

    python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    get_pip_path = os.path.join(service_dir, "get-pip.py")

    if not os.path.exists(get_pip_path):
        download_file("https://bootstrap.pypa.io/get-pip.py", get_pip_path)

    run_silent([python_path, get_pip_path])

    return python_path


# -------------------------------------------------
# SERVICE: install requirements
# -------------------------------------------------

def install_service_requirements(service_name, python_path, cuda):
    service_dir = os.path.join(BASE_DIR, "services", service_name)
    req_file = os.path.join(service_dir, "requirements.txt")
    marker_file = os.path.join(service_dir, ".req_hash")

    os.makedirs(PIP_CACHE_DIR, exist_ok=True)

    with open(req_file, "rb") as f:
        req_hash = hashlib.sha256(f.read()).hexdigest()

    if os.path.exists(marker_file):
        with open(marker_file, "r") as f:
            if f.read() == req_hash:
                return

    pb = progress_bar(f"{service_name}")

    # 0–10% pip upgrade
    run_silent([
        python_path, "-m", "pip", "install", "--upgrade", "pip",
        "--cache-dir", PIP_CACHE_DIR
    ])
    pb["percent"] = 10

    # 10–80% torch
    torch_cmd = [
        python_path, "-m", "pip", "install",
        "torch==2.8.0",
        "torchvision==0.23.0",
        "torchaudio==2.8.0",
        "--cache-dir", PIP_CACHE_DIR,
        "--prefer-binary",
        "--progress-bar", "on",
    ]

    if cuda != "cpu":
        torch_cmd += ["--index-url", f"https://download.pytorch.org/whl/{cuda}"]

    run_with_progress(torch_cmd, pb, 10, 80)

    # 80–100% requirements
    run_with_progress([
        python_path, "-m", "pip", "install",
        "-r", req_file,
        "--cache-dir", PIP_CACHE_DIR,
        "--prefer-binary",
        "--progress-bar", "on",
    ], pb, 80, 100)

    pb["percent"] = 100
    pb["stop"] = True
    time.sleep(0.1)

    print(f"\r{service_name} [██████████████████████████████] 100%")

    with open(marker_file, "w") as f:
        f.write(req_hash)


# -------------------------------------------------
# SERVICE: setup all
# -------------------------------------------------

def setup_services(cuda):
    for service in SERVICES:
        service_dir = os.path.join(BASE_DIR, "services", service)
        if not os.path.exists(service_dir):
            continue

        python_path = create_service_venv(service)
        install_service_requirements(service, python_path, cuda)


# -------------------------------------------------
# main
# -------------------------------------------------

def main():
    steps = [
        ("Updating client", update_client),
        ("Preparing environment", add_ffmpeg_to_path),
        ("Creating venv", create_venv),
        ("Installing base requirements", install_requirements),
    ]

    pb = progress_bar("Setup")

    total = len(steps)

    for i, (name, func) in enumerate(steps, 1):
        func()
        pb["percent"] = int((i / total) * 100)

    pb["stop"] = True
    print("\rSetup [██████████████████████████████] 100%")

    cuda = detect_gpu()

    setup_services(cuda)

    print("\n🚀 Starting client...")
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