# modules/utils/runtime_paths.py
from pathlib import Path
import sys

def app_root() -> Path:
    """
    Корень приложения:
    - dev: папка проекта
    - exe: временная папка PyInstaller (_MEIPASS)
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]
