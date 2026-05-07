# utils/thread_utils.py
"""Безопасные потоки для синхронных вызовов"""
from threading import Thread
from kivy.clock import Clock
from kivy.logger import Logger


def call_sync_in_thread(sync_func, on_result=None, on_error=None, show_progress=None, *args, **kwargs):
    """
    Вызывает синхронную функцию в отдельном потоке (UI не блокируется)

    Args:
        sync_func: синхронная функция API
        on_result: callback при успехе (получает результат)
        on_error: callback при ошибке (получает ошибку)
        show_progress: функция для показа прогресса (опционально)
    """

    def worker():
        try:
            if show_progress:
                Clock.schedule_once(lambda dt: show_progress(True), 0)

            result = sync_func(*args, **kwargs)

            if on_result:
                Clock.schedule_once(lambda dt: on_result(result), 0)

        except Exception as e:
            Logger.error(f"Thread error in {sync_func.__name__}: {e}")
            if on_error:
                Clock.schedule_once(lambda dt: on_error(e), 0)
        finally:
            if show_progress:
                Clock.schedule_once(lambda dt: show_progress(False), 0)

    thread = Thread(target=worker, daemon=True)
    thread.start()
    return thread


class SafeAsyncCall:
    """Безопасный асинхронный вызов (предотвращает повторные вызовы)"""

    def __init__(self):
        self._running = False
        self._last_call = None

    def call(self, sync_func, on_result=None, on_error=None, *args, **kwargs):
        """Вызывает функцию, если предыдущий вызов завершён"""
        if self._running:
            Logger.warning(f"Пропущен вызов {sync_func.__name__} - предыдущий ещё выполняется")
            return None

        self._running = True

        def on_done(result):
            self._running = False
            if on_result:
                on_result(result)

        def on_fail(error):
            self._running = False
            if on_error:
                on_error(error)

        return call_sync_in_thread(sync_func, on_done, on_fail, *args, **kwargs)