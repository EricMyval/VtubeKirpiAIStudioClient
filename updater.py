import os
import subprocess
import sys
import re

BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")


# ----------------------------
# UTILS
# ----------------------------

def get_installed_torch_cuda(py):
    try:
        out = subprocess.check_output(
            [py, "-c", "import torch; print(torch.version.cuda)"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        return out  # "12.4" или None
    except:
        return None

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


# ----------------------------
# CUDA DETECT (SAFE)
# ----------------------------

def detect_cuda():
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

    smi = find_nvidia_smi()

    if not smi:
        print("❌ NVIDIA GPU not found. This app requires RTX GPU.")
        sys.exit(1)

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
                print(f"⚙️ CUDA detected: {cuda}")
                return cuda

        print("❌ Unsupported GPU. RTX 20/30/40/50 required.")
        sys.exit(1)

    except Exception as e:
        print("❌ Failed to detect GPU:", e)
        sys.exit(1)


# ----------------------------
# RUN CLIENT (SAFE)
# ----------------------------

def run_client():
    print("\n🚀 Starting client (inline)...\n")
    try:
        import main
        main.run()
    except Exception as e:
        print("❌ Failed to start client:", e)


def install_torch(py, cuda):
    print("\n=== INSTALL TORCH ===")

    installed = is_torch_installed(py)
    installed_cuda = get_installed_torch_cuda(py)

    print(f"[Torch] installed={installed}, cuda={installed_cuda}")

    if installed:
        if installed_cuda:
            print("[Torch] CUDA already present → OK")
            return

        print("[Torch] wrong version → reinstalling...")
        run([py, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio"])

    print(f"[Torch] installing for {cuda}...")

    run([
        py, "-m", "pip", "install",
        "torch", "torchvision", "torchaudio",
        "--index-url",
        f"https://download.pytorch.org/whl/{cuda}"
    ])

# ----------------------------
# MAIN
# ----------------------------

def main():
    cuda = detect_cuda()
    py = PYTHON if os.path.exists(PYTHON) else sys.executable
    print(f"🐍 Using python: {py}")
    install_torch(py, cuda)
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