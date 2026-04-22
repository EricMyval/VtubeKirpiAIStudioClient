import os
import subprocess
import sys
import shutil
import zipfile
import requests

# ----------------------------
# CONFIG
# ----------------------------

SERVICES = ["omnivoice"]
GITHUB_ZIP = "https://codeload.github.com/EricMyval/VtubeKirpiAIStudioClient/zip/refs/heads/master"
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
IS_WIN = sys.platform == "win32"
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON = os.path.join(VENV_DIR, "Scripts" if IS_WIN else "bin", "python")

# ----------------------------
# UTILS
# ----------------------------

def run(cmd, cwd=None):
    print("\n>>>", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)


def try_run(cmd):
    try:
        run(cmd)
        return True
    except Exception as e:
        print("❌ Failed:", e)
        return False


def download(url, dest):
    print("⬇️ Downloading:", url)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)


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
    print("📦 Applying update...")
    for item in os.listdir(repo_dir):
        if item in ["venv", ".git", "data"]:
            continue

        src = os.path.join(repo_dir, item)
        dst = os.path.join(BASE_DIR, item)

        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    os.remove(tmp_zip)

    print("✅ Update complete")


# ----------------------------
# PYTHON DETECT
# ----------------------------

def find_python():
    for name in ["python", "python3"]:
        p = shutil.which(name)
        if p and os.path.exists(p):
            return p

    raise RuntimeError("❌ Python not found")


# ----------------------------
# VENV
# ----------------------------

def create_venv():
    if os.path.exists(PYTHON):
        return

    py = find_python()

    print("🐍 Creating venv...")
    run([py, "-m", "venv", VENV_DIR])
    run([PYTHON, "-m", "ensurepip"])


# ----------------------------
# CUDA DETECT
# ----------------------------

def detect_cuda():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL
        ).decode().lower()

        print("🎮 GPU:", out.strip())

        if "rtx 50" in out or "rtx 40" in out:
            return "cu129"

        if "rtx 30" in out:
            return "cu121"

        if "rtx 20" in out:
            return "cu118"

    except Exception as e:
        print("⚠️ GPU detect failed:", e)

    return "cpu"


# ----------------------------
# INSTALL BASE
# ----------------------------

def install_base():
    req = os.path.join(BASE_DIR, "requirements.txt")

    if not os.path.exists(req):
        return

    print("\n📦 Installing base requirements...")
    run([PYTHON, "-m", "pip", "install", "-r", req])


# ----------------------------
# SERVICE SETUP
# ----------------------------

def create_service_venv(path):
    venv = os.path.join(path, "venv")
    py = os.path.join(venv, "Scripts" if IS_WIN else "bin", "python")

    if os.path.exists(py):
        return py

    base_py = find_python()

    print(f"\n🐍 Creating venv for {path}...")
    run([base_py, "-m", "venv", venv])
    run([py, "-m", "ensurepip"])

    return py


def install_service(path, py, cuda):
    req = os.path.join(path, "requirements.txt")

    print(f"\n=== INSTALL SERVICE: {path} ===")

    # ----------------------------
    # TORCH INSTALL
    # ----------------------------

    print(f"\n[Torch] installing for {cuda}...")

    torch_cmd = [
        py, "-m", "pip", "install",
        "torch", "torchvision", "torchaudio"
    ]

    installed = False

    if cuda != "cpu":
        installed = try_run(torch_cmd + ["--index-url", f"https://download.pytorch.org/whl/{cuda}"])

    if not installed:
        print("\n[Torch] fallback → CPU")
        run(torch_cmd)

    # ----------------------------
    # REQUIREMENTS
    # ----------------------------

    if os.path.exists(req):
        print("\n[Requirements] installing...")
        run([py, "-m", "pip", "install", "-r", req])

    print("\n✅ Service ready")


# ----------------------------
# SERVICES
# ----------------------------

def setup_services(cuda):
    for name in SERVICES:
        path = os.path.join(BASE_DIR, "services", name)

        if not os.path.exists(path):
            print(f"⚠️ Service not found: {name}")
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

    print("\n🚀 Starting client...\n")
    subprocess.call([PYTHON, main], cwd=BASE_DIR)


# ----------------------------
# MAIN
# ----------------------------

def main():
    update_client()

    create_venv()
    install_base()

    cuda = detect_cuda()

    setup_services(cuda)

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