import os
import subprocess
import sys
import shutil
import re
import hashlib

# ----------------------------
# CONFIG
# ----------------------------

SERVICES = ["omnivoice"]

BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
IS_WIN = sys.platform == "win32"

VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON = os.path.join(VENV_DIR, "Scripts" if IS_WIN else "bin", "python")


# ----------------------------
# UTILS
# ----------------------------

def is_torch_installed(py):
    try:
        subprocess.check_call(
            [py, "-c", "import torch"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except:
        return False

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


def get_file_hash(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# ----------------------------
# VENV
# ----------------------------

def is_venv_valid(py):
    try:
        subprocess.check_call([py, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False


def create_venv():
    if is_venv_valid(PYTHON):
        return

    if os.path.exists(VENV_DIR):
        print("🧹 Removing broken venv...")
        shutil.rmtree(VENV_DIR, ignore_errors=True)

    print("🐍 Creating venv...")
    run([sys.executable, "-m", "venv", VENV_DIR])
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

        cu = "cpu"

        if "rtx" in out:
            match = re.search(r"rtx\s*(\d{4})", out)
            if match:
                series = match.group(1)[0]

                if series == "5":
                    cu = "cu129"
                elif series == "4":
                    cu = "cu124"
                elif series == "3":
                    cu = "cu121"
                elif series == "2":
                    cu = "cu118"

        print("🎮 GPU:", out.strip())
        print("⚙️ Selected CUDA:", cu)

        return cu

    except Exception as e:
        print("⚠️ GPU detect failed:", e)

    return "cpu"


# ----------------------------
# INSTALL BASE (WITH CACHE)
# ----------------------------

def install_base():
    req = os.path.join(BASE_DIR, "requirements.txt")
    hash_file = os.path.join(VENV_DIR, ".req_hash")

    if not os.path.exists(req):
        return

    current_hash = get_file_hash(req)

    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            if f.read().strip() == current_hash:
                print("⚡ Base requirements up to date")
                return

    print("\n📦 Installing base requirements...")
    run([PYTHON, "-m", "pip", "install", "-r", req])

    with open(hash_file, "w") as f:
        f.write(current_hash)


# ----------------------------
# SERVICE SETUP
# ----------------------------

def create_service_venv(path):
    venv = os.path.join(path, "venv")
    py = os.path.join(venv, "Scripts" if IS_WIN else "bin", "python")

    if is_venv_valid(py):
        return py

    if os.path.exists(venv):
        print(f"🧹 Removing broken venv for {path}...")
        shutil.rmtree(venv, ignore_errors=True)

    print(f"\n🐍 Creating venv for {path}...")
    run([sys.executable, "-m", "venv", venv])
    run([py, "-m", "ensurepip"])

    return py


def install_service(path, py, cuda):
    req = os.path.join(path, "requirements.txt")
    hash_file = os.path.join(os.path.dirname(py), ".req_hash")

    print(f"\n=== INSTALL SERVICE: {path} ===")

    # ----------------------------
    # TORCH (FIX)
    # ----------------------------

    if not is_torch_installed(py):
        print(f"[Torch] installing for {cuda}...")

        torch_cmd = [
            py, "-m", "pip", "install",
            "torch", "torchvision", "torchaudio"
        ]

        installed = False

        if cuda != "cpu":
            installed = try_run(torch_cmd + [
                "--index-url",
                f"https://download.pytorch.org/whl/{cuda}"
            ])

        if not installed:
            print("[Torch] fallback → CPU")
            run(torch_cmd)
    else:
        print("[Torch] already installed")

    # ----------------------------
    # REQUIREMENTS (CACHE)
    # ----------------------------

    if os.path.exists(req):
        current_hash = get_file_hash(req)

        if os.path.exists(hash_file):
            try:
                with open(hash_file, "r") as f:
                    if f.read().strip() == current_hash:
                        print("[Requirements] up to date")
                        print("✅ Service ready")
                        return
            except:
                pass

        print("[Requirements] installing...")
        run([py, "-m", "pip", "install", "-r", req])

        try:
            with open(hash_file, "w") as f:
                f.write(current_hash)
        except:
            pass

    print("✅ Service ready")


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

    if not os.path.exists(PYTHON):
        print("❌ Python not found:", PYTHON)
        return

    print("\n🚀 Starting client...\n")

    process = subprocess.Popen(
        [PYTHON, main],
        cwd=BASE_DIR
    )

    # ⛔ проверяем умер ли сразу
    time.sleep(1)

    if process.poll() is not None:
        print("❌ Client crashed instantly (exit code:", process.returncode, ")")


# ----------------------------
# MAIN
# ----------------------------

def main():
    # ❗ защита: updater должен запускаться только через launcher
    if "--run" not in sys.argv:
        print("❌ updater launched incorrectly")
        return

    print("⚙️ Running updater...\n")

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