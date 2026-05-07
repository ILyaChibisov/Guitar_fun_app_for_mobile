# utils/async_helper.py
"""
Вспомогательные функции для асинхронных операций
"""
from threading import Thread
from kivy.clock import Clock
from kivy.logger import Logger


def run_async(func, on_success=None, on_error=None, *args, **kwargs):
    """
    Запускает функцию в отдельном потоке

    Args:
        func: функция для выполнения
        on_success: callback при успехе (получает результат)
        on_error: callback при ошибке (получает исключение)
    """

    def worker():
        try:
            result = func(*args, **kwargs)
            if on_success:
                Clock.schedule_once(lambda dt: on_success(result), 0)
        except Exception as e:
            Logger.error(f"Async error in {func.__name__}: {e}")
            if on_error:
                Clock.schedule_once(lambda dt: on_error(e), 0)

    thread = Thread(target=worker, daemon=True)
    thread.start()
    return thread


class SafeAsyncCall:
    """Безопасный асинхронный вызов (предотвращает повторные вызовы)"""

    def __init__(self):
        self._running = False
        self._last_call = None

    def call(self, func, on_success=None, on_error=None, *args, **kwargs):
        """Вызывает функцию, если предыдущий вызов завершён"""
        if self._running:
            Logger.warning(f"Пропущен вызов {func.__name__} - предыдущий ещё выполняется")
            return None

        self._running = True

        def on_done(result):
            self._running = False
            if on_success:
                on_success(result)

        def on_fail(error):
            self._running = False
            if on_error:
                on_error(error)

        return run_async(func, on_done, on_fail, *args, **kwargs)