# utils/notifications.py
"""
Упрощенная система уведомлений - временно отключена для отладки
"""
import logging

logger = logging.getLogger(__name__)


class NotificationManager:
    """Менеджер уведомлений - упрощенная версия (лог в консоль)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def show(self, message, bg_color=None, duration=2.5):
        """Показывает уведомление (лог в консоль)"""
        print(f"[NOTIFICATION] {message}")

    def success(self, message, duration=2.5):
        """Успешное уведомление"""
        print(f"[SUCCESS] ✅ {message}")

    def error(self, message, duration=3):
        """Уведомление об ошибке"""
        print(f"[ERROR] ❌ {message}")

    def warning(self, message, duration=2.5):
        """Предупреждение"""
        print(f"[WARNING] ⚠️ {message}")

    def info(self, message, duration=2):
        """Информационное уведомление"""
        print(f"[INFO] ℹ️ {message}")


# Создаем глобальный экземпляр
notify = NotificationManager()