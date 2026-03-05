# modules/utils/runtime_paths.py
from pathlib import Path
import sys

def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]
