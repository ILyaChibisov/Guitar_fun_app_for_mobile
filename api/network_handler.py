# api/network_handler.py
"""
Обработчик сетевых ошибок и повторных попыток
"""
import time
import threading
from functools import wraps
from kivy.clock import Clock
from kivy.logger import Logger


def retry_on_failure(max_retries=3, delay=1):
    """
    Декоратор для повторных попыток при сетевых ошибках
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        Logger.warning(f"Network: Ошибка {e}, попытка {attempt + 1}/{max_retries}")
                        time.sleep(delay * (attempt + 1))
                    else:
                        Logger.error(f"Network: Все попытки исчерпаны: {e}")
                        raise
            raise last_error

        return wrapper

    return decorator


class NetworkManager:
    """Управление сетевыми запросами"""

    def __init__(self):
        self.is_online = True
        self._check_interval = None
        self._callbacks = []

    def start_monitoring(self):
        """Начинает мониторинг сети"""
        if not self._check_interval:
            self._check_interval = Clock.schedule_interval(self.check_connection, 30)

    def stop_monitoring(self):
        """Останавливает мониторинг сети"""
        if self._check_interval:
            self._check_interval.cancel()
            self._check_interval = None

    def check_connection(self, dt=None):
        """Проверяет доступность сети"""

        def check():
            import socket
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=3)
                if not self.is_online:
                    self.is_online = True
                    Clock.schedule_once(lambda dt: self._notify_online(), 0)
            except:
                if self.is_online:
                    self.is_online = False
                    Clock.schedule_once(lambda dt: self._notify_offline(), 0)

        threading.Thread(target=check, daemon=True).start()

    def add_listener(self, callback):
        """Добавляет слушатель изменения статуса сети"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_listener(self, callback):
        """Удаляет слушатель"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_offline(self):
        Logger.warning("Network: Нет подключения к интернету")
        for callback in self._callbacks:
            try:
                callback(False)
            except:
                pass

    def _notify_online(self):
        Logger.info("Network: Подключение восстановлено")
        for callback in self._callbacks:
            try:
                callback(True)
            except:
                pass


network_manager = NetworkManager()