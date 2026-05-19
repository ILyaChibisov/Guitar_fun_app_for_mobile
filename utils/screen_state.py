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


# Глобальный экземпляр
screen_state = ScreenStateManager()