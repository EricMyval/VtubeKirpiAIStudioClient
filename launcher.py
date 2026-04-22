import hashlib
import os
import subprocess
import sys
import shutil
import zipfile
import urllib.request
import time
import threading

# ----------------------------
# CONFIG
# ----------------------------

SERVICES = ["omnivoice"]

GITHUB_ZIP = "https://codeload.github.com/EricMyval/VtubeKirpiAIStudioClient/zip/refs/heads/master"

BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))

IS_WIN = sys.platform == "win32"
VENV_DIR = os.path.join(BASE_DIR, "venv")
PIP_CACHE_DIR = os.path.join(BASE_DIR, ".pip_cache")
MARKER_FILE = os.path.join(VENV_DIR, ".installed")

PYTHON = os.path.join(VENV_DIR, "Scripts" if IS_WIN else "bin", "python")

# ----------------------------
# UTILS
# ----------------------------

def run(cmd, cwd=None):
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")

def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Kirpi"})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)

# ----------------------------
# PROGRESS
# ----------------------------

def progress(title):
    state = {"p": 0, "stop": False}

    def loop():
        while not state["stop"]:
            bar = "█" * (state["p"] // 3) + "░" * (30 - state["p"] // 3)
            print(f"\r{title} [{bar}] {state['p']:3d}%", end="", flush=True)
            time.sleep(0.1)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return state, t

# ----------------------------
# UPDATE CLIENT
# ----------------------------

def update_client():
    tmp_zip = os.path.join(BASE_DIR, "_update.zip")
    tmp_dir = os.path.join(BASE_DIR, "_update")

    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir, ignore_errors=True)

    download(GITHUB_ZIP, tmp_zip)

    with zipfile.ZipFile(tmp_zip, "r") as z:
        z.extractall(tmp_dir)

    repo_dir = next((os.path.join(tmp_dir, d) for d in os.listdir(tmp_dir)), None)

    if not repo_dir:
        raise RuntimeError("Invalid update archive")

    for item in os.listdir(repo_dir):
        if item in ["venv", ".git"]:
            continue

        src = os.path.join(repo_dir, item)
        dst = os.path.join(BASE_DIR, item)

        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    os.remove(tmp_zip)

# ----------------------------
# PYTHON DETECT (FIXED)
# ----------------------------

def find_python():
    candidates = []

    py = shutil.which("py")
    if py:
        try:
            out = subprocess.check_output(
                [py, "-3", "-c", "import sys;print(sys.executable)"],
                text=True
            ).strip()
            candidates.append(out)
        except:
            pass

    for name in ["python", "python3"]:
        p = shutil.which(name)
        if p:
            candidates.append(p)

    if sys.platform == "win32":
        candidates += [
            r"C:\Python311\python.exe",
            r"C:\Python310\python.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python310\python.exe"),
        ]

    for p in candidates:
        if not p:
            continue
        if "WindowsApps" in p:
            continue
        if os.path.exists(p):
            return p

    raise RuntimeError("❌ Normal Python not found (install from python.org)")

# ----------------------------
# VENV
# ----------------------------

def create_venv():
    if os.path.exists(PYTHON):
        return

    py = find_python()
    run([py, "-m", "venv", VENV_DIR])
    run([PYTHON, "-m", "ensurepip"])

# ----------------------------
# GPU DETECT
# ----------------------------

def detect_cuda():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL
        ).decode().lower()

        if "rtx 50" in out or "rtx 40" in out:
            return "cu129"
        if "rtx 30" in out:
            return "cu121"
        if "rtx 20" in out:
            return "cu118"

    except:
        pass

    return "cpu"

# ----------------------------
# INSTALL BASE
# ----------------------------

def install_base():
    req = os.path.join(BASE_DIR, "requirements.txt")

    with open(req, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()

    if os.path.exists(MARKER_FILE):
        if open(MARKER_FILE).read() == h:
            return

    run([PYTHON, "-m", "pip", "install", "-r", req])

    with open(MARKER_FILE, "w") as f:
        f.write(h)

# ----------------------------
# SERVICE SETUP
# ----------------------------

def create_service_venv(path):
    venv = os.path.join(path, "venv")
    py = os.path.join(venv, "Scripts" if IS_WIN else "bin", "python")

    if os.path.exists(py):
        return py

    base_py = find_python()
    run([base_py, "-m", "venv", venv])
    run([py, "-m", "ensurepip"])

    return py

def install_service(path, py, cuda):
    req = os.path.join(path, "requirements.txt")
    marker = os.path.join(path, ".hash")

    with open(req, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()

    if os.path.exists(marker) and open(marker).read() == h:
        return

    os.makedirs(PIP_CACHE_DIR, exist_ok=True)

    pb, t = progress(os.path.basename(path))

    pb["p"] = 10

    torch = [
        py, "-m", "pip", "install",
        "torch==2.8.0",
        "torchvision==0.23.0",
        "torchaudio==2.8.0",
        "--cache-dir", PIP_CACHE_DIR,
        "--prefer-binary"
    ]

    if cuda != "cpu":
        torch += ["--index-url", f"https://download.pytorch.org/whl/{cuda}"]

    run(torch)
    pb["p"] = 70

    run([
        py, "-m", "pip", "install",
        "-r", req,
        "--cache-dir", PIP_CACHE_DIR,
        "--prefer-binary"
    ])

    pb["p"] = 100
    pb["stop"] = True
    t.join(timeout=1)

    print(f"\r{os.path.basename(path)} [██████████████████████████████] 100%")

    with open(marker, "w") as f:
        f.write(h)

# ----------------------------
# SERVICES
# ----------------------------

def setup_services(cuda):
    for name in SERVICES:
        path = os.path.join(BASE_DIR, "services", name)
        if not os.path.exists(path):
            continue

        py = create_service_venv(path)
        install_service(path, py, cuda)

# ----------------------------
# RUN CLIENT
# ----------------------------

def run_client():
    main = os.path.join(BASE_DIR, "main.py")
    if not os.path.exists(main):
        print("❌ main.py not found")
        return

    subprocess.call([PYTHON, main], cwd=BASE_DIR)

# ----------------------------
# MAIN (FIXED)
# ----------------------------

def main():
    pb, t = progress("Setup")

    update_client()
    pb["p"] = 25

    create_venv()
    pb["p"] = 50

    install_base()
    pb["p"] = 75

    # 🔥 ВАЖНО — останавливаем Setup progress
    pb["p"] = 100
    pb["stop"] = True
    t.join(timeout=1)

    print("\rSetup [██████████████████████████████] 100%")

    cuda = detect_cuda()

    # теперь можно безопасно запускать сервисы
    setup_services(cuda)

    print("\n🚀 Starting client...")
    run_client()

# ----------------------------
# ENTRY
# ----------------------------

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")