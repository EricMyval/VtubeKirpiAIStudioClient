import os
import subprocess
import sys
import zipfile
import shutil
import time
import hashlib
import urllib.request
import ssl

# ----------------------------
# CONFIG
# ----------------------------

BASE_DIR = os.path.dirname(
    sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
)

UPDATER_PATH = os.path.join(BASE_DIR, "updater.py")

GITHUB_ZIP = "https://codeload.github.com/EricMyval/VtubeKirpiAIStudioClient/zip/refs/heads/master"
VERSION_URL = "https://raw.githubusercontent.com/EricMyval/VtubeKirpiAIStudioClient/master/version.txt"

LOCAL_VERSION_FILE = os.path.join(BASE_DIR, "version.txt")

VENV_DIR = os.path.join(BASE_DIR, "venv")

TIMEOUT = 10

# ----------------------------
# UTILS
# ----------------------------

def log(*args):
    try:
        print(*args)
    except:
        pass


def run(cmd, cwd=None):
    log(">>>", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)


def safe_remove(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)
    except:
        pass


def get_file_hash(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# ----------------------------
# PYTHON DETECT
# ----------------------------

def get_system_python():
    for cmd in ["python", "python3"]:
        try:
            subprocess.check_call(
                [cmd, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return cmd
        except:
            continue
    return None


def get_venv_python():
    return os.path.join(VENV_DIR, "Scripts", "python.exe")


# ----------------------------
# NETWORK
# ----------------------------

def download(url, dest):
    log("⬇️ Downloading:", url)

    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            data = r.read()
    except:
        log("⚠️ SSL failed → retry without verification")
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(url, context=ctx, timeout=TIMEOUT) as r:
            data = r.read()

    if not data:
        raise RuntimeError("Download returned empty data")

    with open(dest, "wb") as f:
        f.write(data)


def get_remote_version():
    try:
        url = VERSION_URL + "?t=" + str(int(time.time()))

        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                return r.read().decode().strip()
        except:
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(url, context=ctx, timeout=5) as r:
                return r.read().decode().strip()

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
    log("📦 Applying update...")

    for item in os.listdir(repo_dir):
        if item in ["venv", ".git", "data", "launcher.exe"]:
            continue

        src = os.path.join(repo_dir, item)
        dst = os.path.join(BASE_DIR, item)

        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                tmp = dst + ".tmp"
                shutil.copy2(src, tmp)
                os.replace(tmp, dst)
        except Exception as e:
            log("⚠️ Copy failed:", item, e)


def update_client():
    remote = get_remote_version()
    local = get_local_version()

    log(f"📦 Local version: {local}")
    log(f"🌐 Remote version: {remote}")

    if remote is None:
        log("⚡ Offline mode — skip update")
        return False

    if local == remote:
        log("✅ Already up to date")
        return False

    tmp_zip = os.path.join(BASE_DIR, "_update.zip")
    tmp_dir = os.path.join(BASE_DIR, "_update")

    try:
        safe_remove(tmp_dir)

        download(GITHUB_ZIP, tmp_zip)

        if not os.path.exists(tmp_zip):
            raise RuntimeError("Download failed")

        with zipfile.ZipFile(tmp_zip, "r") as z:
            z.extractall(tmp_dir)

        repo_dir = next((os.path.join(tmp_dir, d) for d in os.listdir(tmp_dir)), None)
        if not repo_dir:
            raise RuntimeError("Bad archive")

        apply_update(repo_dir)

        with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(remote)

        log("✅ Update complete")
        return True

    except Exception as e:
        log("⚠️ Update failed:", e)
        return False

    finally:
        safe_remove(tmp_dir)
        safe_remove(tmp_zip)


# ----------------------------
# VENV
# ----------------------------

def create_venv():
    py = get_venv_python()

    try:
        subprocess.check_call([py, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except:
        pass

    safe_remove(VENV_DIR)

    log("🐍 Creating venv...")

    python_bin = get_system_python()

    if not python_bin:
        log("❌ Python not found")
        input("Install Python and press Enter...")
        sys.exit(1)

    run([python_bin, "-m", "venv", VENV_DIR])

    py = get_venv_python()
    run([py, "-m", "ensurepip"])


# ----------------------------
# INSTALL BASE
# ----------------------------

def install_base():
    py = get_venv_python()

    if not os.path.exists(py):
        log("❌ venv python missing")
        return

    req = os.path.join(BASE_DIR, "requirements.txt")
    hash_file = os.path.join(VENV_DIR, ".req_hash")

    if not os.path.exists(req):
        return

    current_hash = get_file_hash(req)

    if os.path.exists(hash_file):
        try:
            with open(hash_file) as f:
                if f.read().strip() == current_hash:
                    log("⚡ Base requirements up to date")
                    return
        except:
            pass

    log("📦 Installing base requirements...")
    run([py, "-m", "pip", "install", "-r", req])

    with open(hash_file, "w") as f:
        f.write(current_hash)


# ----------------------------
# UPDATER
# ----------------------------

def run_updater():
    py = get_venv_python()

    if not os.path.exists(UPDATER_PATH):
        log("❌ updater missing")

        main_py = os.path.join(BASE_DIR, "main.py")

        if os.path.exists(main_py):
            log("⚠️ Fallback → running main.py")

            subprocess.Popen([py, main_py], cwd=BASE_DIR)
            return

        log("👉 No updater and no main.py → cannot continue")
        input("Press Enter...")
        return

    log("🚀 Starting updater...\n")

    subprocess.Popen(
        [py, UPDATER_PATH, "--run"],
        cwd=BASE_DIR
    )


# ----------------------------
# MAIN
# ----------------------------

def main():
    if "--run" in sys.argv:
        return

    log("⚙️ Launcher started\n")

    updated = update_client()

    if updated:
        log("🔁 Restarting launcher...\n")
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)

    create_venv()
    install_base()
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