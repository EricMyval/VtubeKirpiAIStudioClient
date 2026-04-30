import os
import subprocess
import sys
import requests
import zipfile
import shutil
import time

# ----------------------------
# CONFIG
# ----------------------------

BASE_DIR = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__))

UPDATER_PATH = os.path.join(BASE_DIR, "updater.py")

GITHUB_ZIP = "https://codeload.github.com/EricMyval/VtubeKirpiAIStudioClient/zip/refs/heads/master"
VERSION_URL = "https://raw.githubusercontent.com/EricMyval/VtubeKirpiAIStudioClient/master/version.txt"

LOCAL_VERSION_FILE = os.path.join(BASE_DIR, "version.txt")

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


def download(url, dest):
    safe_print("⬇️ Downloading:", url)
    r = requests.get(url, timeout=TIMEOUT_LONG)
    r.raise_for_status()

    with open(dest, "wb") as f:
        f.write(r.content)


def get_remote_version():
    try:
        url = VERSION_URL + "?t=" + str(int(time.time()))
        r = requests.get(url, timeout=TIMEOUT_SHORT)
        r.raise_for_status()
        return r.text.strip()
    except Exception:
        # ❗ тихо — это нормальный оффлайн режим
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
                # атомарная замена
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

    # ❗ ОФФЛАЙН → НИЧЕГО НЕ ДЕЛАЕМ
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
            raise RuntimeError("Invalid update archive")

        apply_update(repo_dir)

        # сохраняем версию
        try:
            with open(LOCAL_VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(remote)
        except:
            pass

        safe_print("✅ Update complete")

    except Exception as e:
        safe_print("⚠️ Update failed:", e)

    finally:
        try:
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)
            if os.path.exists(tmp_zip):
                os.remove(tmp_zip)
        except:
            pass


# ----------------------------
# UPDATER
# ----------------------------

def ensure_updater():
    if os.path.exists(UPDATER_PATH):
        return

    safe_print("⬇️ updater.py missing, downloading...")

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

    safe_print("🚀 Launching updater...\n")

    try:
        subprocess.call([sys.executable, UPDATER_PATH], cwd=BASE_DIR)
    except Exception as e:
        safe_print("❌ Failed to launch updater:", e)


# ----------------------------
# MAIN
# ----------------------------

def main():
    safe_print("⚙️ Checking for updates...\n")

    update_client()
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