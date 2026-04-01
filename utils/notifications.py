# utils/notifications.py
"""
Универсальная система уведомлений для KivyMD 2.0
"""
from kivy.clock import Clock
from config.theme import theme
from utils.kivy_imports import Snackbar


class NotificationManager:
    """Менеджер уведомлений"""

    _instance = None
    _current_snack = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self._queue = []
        self._is_showing = False

    def show(self, message, bg_color=None, duration=2.5):
        """
        Показывает уведомление

        Args:
            message: Текст уведомления
            bg_color: Цвет фона (опционально)
            duration: Длительность показа в секундах
        """

        def _show(dt):
            if self._current_snack:
                try:
                    self._current_snack.dismiss()
                except:
                    pass

            snack = Snackbar(
                text=message,
                bg_color=bg_color if bg_color else theme.INFO,
                duration=duration
            )
            snack.open()
            self._current_snack = snack

        Clock.schedule_once(_show, 0)

    def success(self, message, duration=2.5):
        """Успешное уведомление"""
        self.show(f"✅ {message}", bg_color=theme.SUCCESS, duration=duration)

    def error(self, message, duration=3):
        """Уведомление об ошибке"""
        self.show(f"❌ {message}", bg_color=theme.ERROR, duration=duration)

    def warning(self, message, duration=2.5):
        """Предупреждение"""
        self.show(f"⚠️ {message}", bg_color=theme.WARNING, duration=duration)

    def info(self, message, duration=2):
        """Информационное уведомление"""
        self.show(f"ℹ️ {message}", bg_color=theme.INFO, duration=duration)


# Создаем глобальный экземпляр
notify = NotificationManager()