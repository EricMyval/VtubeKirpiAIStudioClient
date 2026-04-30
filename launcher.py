import os
import subprocess
import sys
import zipfile
import shutil
import time
import hashlib

try:
    import requests
except:
    requests = None  # fallback если нет (но лучше включить в билд)

# ----------------------------
# CONFIG
# ----------------------------

BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))

UPDATER_PATH = os.path.join(BASE_DIR, "updater.py")

GITHUB_ZIP = "https://codeload.github.com/EricMyval/VtubeKirpiAIStudioClient/zip/refs/heads/master"
VERSION_URL = "https://raw.githubusercontent.com/EricMyval/VtubeKirpiAIStudioClient/master/version.txt"

LOCAL_VERSION_FILE = os.path.join(BASE_DIR, "version.txt")

VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON = os.path.join(VENV_DIR, "Scripts", "python.exe")

TIMEOUT_SHORT = 5
TIMEOUT_LONG = 60

# ----------------------------
# UTILS
# ----------------------------

def safe_print(*args):
    try:
        print(*args)
    except:
        pass


def run(cmd, cwd=None):
    safe_print(">>>", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)


def get_file_hash(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# ----------------------------
# NETWORK
# ----------------------------

def download(url, dest):
    if not requests:
        raise RuntimeError("requests not available")

    safe_print("⬇️ Downloading:", url)
    r = requests.get(url, timeout=TIMEOUT_LONG)
    r.raise_for_status()

    with open(dest, "wb") as f:
        f.write(r.content)


def get_remote_version():
    if not requests:
        return None

    try:
        url = VERSION_URL + "?t=" + str(int(time.time()))
        r = requests.get(url, timeout=TIMEOUT_SHORT)
        r.raise_for_status()
        return r.text.strip()
    except:
        return None


def get_local_version():
    if os.path.exists(LOCAL_VERSION_FILE):
        try:
            with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return None
    return None


# ----------------------------
# UPDATE CLIENT
# ----------------------------

def apply_update(repo_dir):
    safe_print("📦 Applying update...")

    for item in os.listdir(repo_dir):
        if item in ["venv", ".git", "data", "launcher.exe"]:
            continue

        src = os.path.join(repo_dir, item)
        dst = os.path.join(BASE_DIR, item)

        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                tmp_dst = dst + ".tmp"
                shutil.copy2(src, tmp_dst)
                os.replace(tmp_dst, dst)
        except Exception as e:
            safe_print(f"⚠️ Failed to copy {item}:", e)


def update_client():
    remote = get_remote_version()
    local = get_local_version()

    safe_print(f"📦 Local version: {local}")
    safe_print(f"🌐 Remote version: {remote}")

    if remote is None:
        safe_print("⚡ Offline mode — skipping update")
        return

    if local == remote:
        safe_print("✅ Already up to date")
        return

    safe_print("⬇️ Updating client...")

    tmp_zip = os.path.join(BASE_DIR, "_update.zip")
    tmp_dir = os.path.join(BASE_DIR, "_update")

    try:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)

        download(GITHUB_ZIP, tmp_zip)

        with zipfile.ZipFile(tmp_zip, "r") as z:
            z.extractall(tmp_dir)

        repo_dir = next((os.path.join(tmp_dir, d) for d in os.listdir(tmp_dir)), None)
        if not repo_dir:
            raise RuntimeError("Invalid archive")

        apply_update(repo_dir)

        if remote:
            with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(remote)

        safe_print("✅ Update complete")

    except Exception as e:
        safe_print("⚠️ Update failed:", e)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if os.path.exists(tmp_zip):
            os.remove(tmp_zip)


# ----------------------------
# VENV
# ----------------------------

def is_venv_valid():
    try:
        subprocess.check_call([PYTHON, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except:
        return False


def create_venv():
    if is_venv_valid():
        return

    if os.path.exists(VENV_DIR):
        safe_print("🧹 Removing broken venv...")
        shutil.rmtree(VENV_DIR, ignore_errors=True)

    safe_print("🐍 Creating venv...")
    run([sys.executable, "-m", "venv", VENV_DIR])
    run([PYTHON, "-m", "ensurepip"])


# ----------------------------
# BASE REQUIREMENTS
# ----------------------------

def install_base():
    req = os.path.join(BASE_DIR, "requirements.txt")
    hash_file = os.path.join(VENV_DIR, ".req_hash")

    if not os.path.exists(req):
        return

    current_hash = get_file_hash(req)

    if os.path.exists(hash_file):
        try:
            with open(hash_file, "r") as f:
                if f.read().strip() == current_hash:
                    safe_print("⚡ Base requirements up to date")
                    return
        except:
            pass

    safe_print("📦 Installing base requirements...")
    run([PYTHON, "-m", "pip", "install", "-r", req])

    with open(hash_file, "w") as f:
        f.write(current_hash)


# ----------------------------
# UPDATER
# ----------------------------

def ensure_updater():
    if os.path.exists(UPDATER_PATH):
        return

    safe_print("⬇️ Downloading updater.py...")

    try:
        download(
            "https://raw.githubusercontent.com/EricMyval/VtubeKirpiAIStudioClient/master/updater.py",
            UPDATER_PATH
        )
    except Exception as e:
        safe_print("❌ Failed to download updater:", e)


def run_updater():
    if not os.path.exists(UPDATER_PATH):
        safe_print("❌ updater.py not found")
        return

    safe_print("🚀 Starting updater...\n")

    subprocess.Popen(
        [sys.executable, UPDATER_PATH, "--run"],
        cwd=BASE_DIR
    )


# ----------------------------
# MAIN
# ----------------------------

def main():
    if "--run" in sys.argv:
        return

    safe_print("⚙️ Launcher started\n")

    update_client()
    create_venv()
    install_base()
    ensure_updater()
    run_updater()


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