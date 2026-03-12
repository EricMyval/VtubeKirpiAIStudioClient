# modules/client/audio/devices.py

from typing import List, Dict
import sounddevice as sd

_cached_name = None
_cached_index = None


def clear_device_cache():
    global _cached_name, _cached_index
    _cached_name = None
    _cached_index = None


def list_output_devices() -> List[Dict[str, object]]:
    devices = sd.query_devices()
    result = []
    seen = set()

    for i, d in enumerate(devices):

        if int(d.get("max_output_channels", 0)) <= 0:
            continue

        name = str(d.get("name", "")).strip()
        lowered = name.lower()

        if "asio" in lowered:
            continue
        if "wdm-ks" in lowered:
            continue
        if "loopback" in lowered:
            continue

        if name in seen:
            continue

        seen.add(name)

        result.append({
            "index": i,
            "name": name
        })

    return result


def resolve_output_device_index(name: str) -> int:
    global _cached_name, _cached_index

    if not name:
        raise RuntimeError("Не выбрано устройство вывода")

    if _cached_name == name and _cached_index is not None:
        return _cached_index

    devices = sd.query_devices()
    name_l = name.lower()

    best = None

    for i, d in enumerate(devices):
        if int(d.get("max_output_channels", 0)) <= 0:
            continue

        dname = str(d.get("name", "")).strip()

        if dname.lower() == name_l:
            best = i
            break

        if best is None and name_l in dname.lower():
            best = i

    if best is None:
        raise RuntimeError(f"Устройство '{name}' не найдено")

    _cached_name = name
    _cached_index = best

    return best