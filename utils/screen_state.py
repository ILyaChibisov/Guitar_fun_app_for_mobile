# utils/screen_state.py
"""
Управление состояниями экранов
Позволяет сохранять и восстанавливать состояние экрана при переходах
"""
import time
from kivy.logger import Logger

logger = Logger.getChild('ScreenState')


class ScreenStateManager:
    """Менеджер состояний экранов"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._states = {}
        self._previous_screen = None
        self._pending_chord = None

        # ============ КЭШ СОСТОЯНИЙ ЭКРАНОВ ============
        self._screen_cache = {}
        self._last_update = {}

    def save_state(self, screen_name, state):
        self._states[screen_name] = state
        logger.debug(f"Сохранено состояние для {screen_name}: {state.keys() if state else 'None'}")

    def get_state(self, screen_name):
        return self._states.get(screen_name)

    def clear_state(self, screen_name):
        if screen_name in self._states:
            del self._states[screen_name]
            logger.debug(f"Очищено состояние для {screen_name}")

    def clear_all(self):
        self._states.clear()
        logger.debug("Очищены все состояния")

    def set_previous_screen(self, screen_name):
        self._previous_screen = screen_name
        logger.debug(f"✅ screen_state: установлен предыдущий экран = {screen_name}")

    def get_previous_screen(self):
        return self._previous_screen

    def set_pending_chord(self, chord_name):
        self._pending_chord = chord_name
        logger.debug(f"Установлен ожидающий аккорд: {chord_name}")

    def get_pending_chord(self):
        return self._pending_chord

    def clear_pending_chord(self):
        self._pending_chord = None

    # ============ НОВЫЕ МЕТОДЫ ДЛЯ КЭША СОСТОЯНИЙ ============

    def cache_screen_data(self, screen_name, data):
        """
        Сохраняет данные экрана в кэш (например, список избранного)

        Args:
            screen_name: имя экрана
            data: данные для сохранения
        """
        self._screen_cache[screen_name] = data
        self._last_update[screen_name] = time.time()
        logger.debug(f"📦 Закэшированы данные для {screen_name}: {len(data) if data else 0} элементов")

    def get_cached_screen_data(self, screen_name, max_age=60):
        """
        Возвращает кэшированные данные экрана, если они не устарели

        Args:
            screen_name: имя экрана
            max_age: максимальный возраст кэша в секундах (по умолчанию 60)

        Returns:
            данные или None, если кэш устарел или отсутствует
        """
        if screen_name in self._screen_cache:
            age = time.time() - self._last_update.get(screen_name, 0)
            if age < max_age:
                logger.debug(f"📦 Данные для {screen_name} из кэша (возраст: {age:.1f}с)")
                return self._screen_cache[screen_name]
            else:
                logger.debug(f"⏳ Кэш для {screen_name} устарел (возраст: {age:.1f}с)")
        return None

    def invalidate_screen_cache(self, screen_name=None):
        """
        Инвалидирует кэш экрана (или всех экранов)

        Args:
            screen_name: имя экрана или None для всех
        """
        if screen_name:
            if screen_name in self._screen_cache:
                del self._screen_cache[screen_name]
                if screen_name in self._last_update:
                    del self._last_update[screen_name]
                logger.debug(f"🗑️ Инвалидирован кэш для {screen_name}")
        else:
            self._screen_cache.clear()
            self._last_update.clear()
            logger.debug("🗑️ Инвалидирован кэш всех экранов")

    def is_cache_valid(self, screen_name, max_age=60):
        """Проверяет, валиден ли кэш для экрана"""
        if screen_name in self._last_update:
            return (time.time() - self._last_update[screen_name]) < max_age
        return False


# Глобальный экземпляр
screen_state = ScreenStateManager()