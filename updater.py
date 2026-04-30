import json
import os
import subprocess
import sys
import shutil
import re
import hashlib
import time

# ----------------------------
# CONFIG
# ----------------------------

SERVICES = ["omnivoice"]

BASE_DIR = os.path.dirname(
    sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
)

IS_WIN = sys.platform == "win32"
CUDA_CONFIG_FILE = os.path.join(BASE_DIR, "cuda_config.json")
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON = os.path.join(VENV_DIR, "Scripts" if IS_WIN else "bin", "python")


# ----------------------------
# UTILS
# ----------------------------

def load_cuda_choice():
    VALID = {"cu129", "cu124", "cu121", "cu118", "cpu"}

    if os.path.exists(CUDA_CONFIG_FILE):
        try:
            with open(CUDA_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cuda = data.get("cuda")

                if cuda in VALID:
                    return cuda
                else:
                    print("⚠️ Invalid CUDA config → ignoring")

        except Exception as e:
            print("⚠️ Failed to read CUDA config:", e)

    return None


def save_cuda_choice(cuda):
    try:
        tmp_file = CUDA_CONFIG_FILE + ".tmp"

        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump({"cuda": cuda}, f, indent=2)

        os.replace(tmp_file, CUDA_CONFIG_FILE)

        print(f"💾 CUDA config saved: {cuda}")

    except Exception as e:
        print("⚠️ Failed to save CUDA config:", e)

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
# VENV CHECK
# ----------------------------

def is_venv_valid(py):
    try:
        subprocess.check_call(
            [py, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except:
        return False


# ----------------------------
# CUDA DETECT (SAFE)
# ----------------------------

def detect_cuda():
    VALID = {"cu129", "cu124", "cu121", "cu118", "cpu"}

    # ----------------------------
    # LOAD SAVED
    # ----------------------------
    saved = load_cuda_choice()
    if saved:
        print(f"⚙️ Using saved CUDA config: {saved}")
        return saved

    # ----------------------------
    # NVIDIA-SMI FIND
    # ----------------------------
    def find_nvidia_smi():
        paths = [
            "nvidia-smi",
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe",
            r"C:\Windows\System32\nvidia-smi.exe",
        ]

        for p in paths:
            try:
                subprocess.check_output(
                    [p, "-h"],
                    stderr=subprocess.DEVNULL,
                    timeout=2
                )
                return p
            except:
                continue

        return None

    # ----------------------------
    # NVIDIA-SMI DETECT
    # ----------------------------
    smi = find_nvidia_smi()

    if smi:
        try:
            out = subprocess.check_output(
                [smi, "--query-gpu=name", "--format=csv,noheader"],
                stderr=subprocess.DEVNULL,
                timeout=3
            ).decode().lower()

            print("🎮 GPU:", out.strip())

            match = re.search(r"rtx\s*(\d{4})", out)
            if match:
                series = match.group(1)[0]

                cuda_map = {
                    "5": "cu129",
                    "4": "cu124",
                    "3": "cu121",
                    "2": "cu118",
                }

                cuda = cuda_map.get(series)

                if cuda:
                    print(f"⚙️ Auto-detected CUDA: {cuda}")
                    save_cuda_choice(cuda)
                    return cuda

            print("⚠️ Неизвестная серия GPU → fallback")

        except Exception as e:
            print("⚠️ Ошибка nvidia-smi:", e)

    else:
        print("⚠️ nvidia-smi не найден")

    # ----------------------------
    # TORCH FALLBACK (SAFE)
    # ----------------------------
    try:
        import torch
        if torch.cuda.is_available():
            print("🔥 CUDA доступна, но модель GPU неизвестна → fallback cu121 (safe)")
            save_cuda_choice("cu121")
            return "cu121"
    except:
        pass

    # ----------------------------
    # NO CONSOLE → CPU
    # ----------------------------
    if not sys.stdin or not sys.stdin.isatty():
        print("⚠️ Нет консоли → fallback CPU")
        save_cuda_choice("cpu")
        return "cpu"

    # ----------------------------
    # MANUAL SELECT
    # ----------------------------
    print("\n❓ Не удалось определить видеокарту. Выбери вручную:")
    print("1) RTX 50xx (cu129)")
    print("2) RTX 40xx (cu124)")
    print("3) RTX 30xx (cu121)")
    print("4) RTX 20xx (cu118)")
    print("5) CPU")

    try:
        choice = input("👉 Введи 1-5: ").strip()
    except:
        print("⚠️ Ошибка ввода → CPU")
        save_cuda_choice("cpu")
        return "cpu"

    mapping = {
        "1": "cu129",
        "2": "cu124",
        "3": "cu121",
        "4": "cu118",
        "5": "cpu"
    }

    cuda = mapping.get(choice, "cpu")

    print("⚙️ Выбрано:", cuda)

    save_cuda_choice(cuda)

    return cuda

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

    # 🔥 фикс для exe / PyInstaller
    python_bin = sys.executable if not getattr(sys, "frozen", False) else "python"

    run([python_bin, "-m", "venv", venv])
    run([py, "-m", "ensurepip"])

    return py


def install_service(path, py, cuda):
    req = os.path.join(path, "requirements.txt")
    hash_file = os.path.join(os.path.dirname(py), ".req_hash")

    print(f"\n=== INSTALL SERVICE: {path} ===")

    # ----------------------------
    # TORCH
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
# RUN CLIENT (SAFE)
# ----------------------------

def run_client():
    main = os.path.join(BASE_DIR, "main.py")

    if not os.path.exists(main):
        print("❌ main.py not found")
        return

    # 🔥 fallback python
    if os.path.exists(PYTHON):
        py = PYTHON
    else:
        print("⚠️ venv python missing → fallback to system python")
        py = sys.executable

    print("\n🚀 Starting client...\n")

    try:
        process = subprocess.Popen(
            [py, main],
            cwd=BASE_DIR
        )

        # ⛔ проверка на мгновенный краш
        time.sleep(1)

        if process.poll() is not None:
            print("❌ Client crashed instantly (exit code:", process.returncode, ")")

    except Exception as e:
        print("❌ Failed to start client:", e)


# ----------------------------
# MAIN
# ----------------------------

def main():
    if "--run" not in sys.argv:
        print("❌ updater launched incorrectly")
        return

    print("⚙️ Running updater...\n")

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