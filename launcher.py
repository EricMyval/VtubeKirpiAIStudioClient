import hashlib
import os
import subprocess
import sys
import shutil
import zipfile
import urllib.request
import ssl

SERVICES = [
    "voxcpm2",
    "qwen3",
    "omnivoice",
    "f5",
]
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
# download file
# -------------------------------------------------

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

    print("🌐 Checking for client updates...")

    zip_path = os.path.join(BASE_DIR, "client_update.zip")
    extract_dir = os.path.join(BASE_DIR, "_update")

    try:

        print("⬇ Downloading client...")

        download_file(GITHUB_ZIP, zip_path)

        if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1000:
            raise RuntimeError("Downloaded archive is invalid")

        print("📦 Extracting update...")

        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # find repo folder
        repo_dir = None

        for name in os.listdir(extract_dir):
            path = os.path.join(extract_dir, name)
            if os.path.isdir(path):
                repo_dir = path
                break

        if not repo_dir:
            raise RuntimeError("Repository folder not found in archive")

        print("📂 Repository folder:", repo_dir)

        # copy files
        for item in os.listdir(repo_dir):

            if item in ["venv", ".git"]:
                continue

            src = os.path.join(repo_dir, item)
            dst = os.path.join(BASE_DIR, item)

            print("🔄 Updating:", item)

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
# SERVICE: create venv
# -------------------------------------------------

def create_service_venv(service_name):
    service_dir = os.path.join(BASE_DIR, "services", service_name)
    venv_dir = os.path.join(service_dir, "venv")
    python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    if os.path.exists(python_path):
        return python_path
    if os.path.exists(venv_dir):
        print(f"⚠️ Removing broken venv for {service_name}")
        shutil.rmtree(venv_dir, ignore_errors=True)
    print(f"📦 Creating venv for {service_name}...")
    python_cmd = find_python()
    run([python_cmd, "-m", "venv", venv_dir, "--without-pip"])
    python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    get_pip_path = os.path.join(service_dir, "get-pip.py")
    if not os.path.exists(get_pip_path):
        print("⬇ Downloading get-pip.py...")
        download_file("https://bootstrap.pypa.io/get-pip.py", get_pip_path)
    print("📦 Installing pip...")
    try:
        run([python_path, get_pip_path])
    except Exception as e:
        print("⚠️ get-pip failed:", e)
    try:
        subprocess.check_call([python_path, "-m", "pip", "--version"])
        print("✅ pip installed")
    except:
        raise RuntimeError("❌ pip installation failed completely")
    return python_path


# -------------------------------------------------
# SERVICE: install requirements
# -------------------------------------------------

def install_service_requirements(service_name, python_path):
    service_dir = os.path.join(BASE_DIR, "services", service_name)
    req_file = os.path.join(service_dir, "requirements.txt")
    marker_file = os.path.join(service_dir, ".req_hash")

    # считаем хеш requirements
    with open(req_file, "rb") as f:
        req_hash = hashlib.sha256(f.read()).hexdigest()

    # проверка — уже ставили или нет
    if os.path.exists(marker_file):
        with open(marker_file, "r") as f:
            saved_hash = f.read()

        if saved_hash == req_hash:
            print(f"✅ {service_name} requirements already installed")
            return

    print(f"📦 Installing {service_name} requirements...")

    run([python_path, "-m", "pip", "install", "--upgrade", "pip"])

    cuda = detect_gpu()
    print(f"🔥 Installing Torch for {service_name}: {cuda}")

    if cuda == "cpu":
        run([
            python_path, "-m", "pip", "install",
            "torch==2.8.0",
            "torchvision==0.23.0",
            "torchaudio==2.8.0"
        ])
    else:
        index = f"https://download.pytorch.org/whl/{cuda}"
        run([
            python_path, "-m", "pip", "install",
            "torch==2.8.0",
            "torchvision==0.23.0",
            "torchaudio==2.8.0",
            "--index-url", index
        ])

    run([python_path, "-m", "pip", "install", "-r", req_file])

    # сохраняем хеш
    with open(marker_file, "w") as f:
        f.write(req_hash)


# -------------------------------------------------
# SERVICE: setup all
# -------------------------------------------------

def setup_services():
    for service in SERVICES:
        service_dir = os.path.join(BASE_DIR, "services", service)
        if not os.path.exists(service_dir):
            print(f"⚠️ Service folder not found: {service_dir}")
            continue
        python_path = create_service_venv(service)
        install_service_requirements(service, python_path)


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
    setup_services()
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