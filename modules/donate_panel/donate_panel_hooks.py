from typing import Callable, List

_handlers: List[Callable[[], None]] = []


def register_on_update(handler: Callable[[], None]):
    """
    Регистрирует обработчик обновления панели донатов
    """
    if handler not in _handlers:
        _handlers.append(handler)


def unregister_on_update(handler: Callable[[], None]):
    """
    Удаляет обработчик
    """
    if handler in _handlers:
        _handlers.remove(handler)


def emit_update():
    """
    Вызывает все обработчики обновления
    """
    for handler in list(_handlers):
        try:
            handler()
        except Exception as e:
            print(f"[DonatePanelEvents] handler error: {e}")