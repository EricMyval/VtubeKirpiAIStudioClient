from typing import Callable, Optional

_on_donate_update: Optional[Callable] = None


def register_on_update(handler: Callable):

    global _on_donate_update
    _on_donate_update = handler


def emit_update():

    if _on_donate_update:
        _on_donate_update()