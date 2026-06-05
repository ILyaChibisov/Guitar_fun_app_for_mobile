# utils/screen_state.py
"""
Управление состояниями экранов
Позволяет сохранять и восстанавливать состояние экрана при переходах
"""
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
        self._states = {}  # {screen_name: state_dict}
        self._previous_screen = None  # Добавляем хранение предыдущего экрана
        self._pending_chord = None  # Аккорд, который нужно показать

    def save_state(self, screen_name, state):
        """Сохраняет состояние экрана"""
        self._states[screen_name] = state
        logger.debug(f"Сохранено состояние для {screen_name}: {state.keys() if state else 'None'}")

    def get_state(self, screen_name):
        """Возвращает сохранённое состояние экрана"""
        return self._states.get(screen_name)

    def clear_state(self, screen_name):
        """Очищает состояние экрана"""
        if screen_name in self._states:
            del self._states[screen_name]
            logger.debug(f"Очищено состояние для {screen_name}")

    def clear_all(self):
        """Очищает все состояния"""
        self._states.clear()
        logger.debug("Очищены все состояния")


    def set_previous_screen(self, screen_name):
        """Устанавливает предыдущий экран"""
        self._previous_screen = screen_name
        logger.debug(f"✅ screen_state: установлен предыдущий экран = {screen_name}")

    def get_previous_screen(self):
        """Возвращает предыдущий экран"""
        return self._previous_screen

    def set_pending_chord(self, chord_name):
        """Устанавливает аккорд, который нужно показать"""
        self._pending_chord = chord_name
        logger.debug(f"Установлен ожидающий аккорд: {chord_name}")

    def get_pending_chord(self):
        """Возвращает ожидающий аккорд"""
        return self._pending_chord

    def clear_pending_chord(self):
        """Очищает ожидающий аккорд"""
        self._pending_chord = None


# Глобальный экземпляр
screen_state = ScreenStateManager()