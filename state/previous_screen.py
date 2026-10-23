# state/previous_screen.py
"""
Глобальное состояние навигации: предыдущий экран + pending chord.
Используется в TopNav, Sidebar, экранах детального просмотра.
"""
from kivy.logger import Logger

logger = Logger.getChild('State:Nav')


class PreviousScreenState:
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
        self._previous_screen = None
        self._pending_chord = None

    # -------- Предыдущий экран --------

    def set_previous(self, screen_name: str):
        if screen_name == self._previous_screen:
            logger.debug(f"⏭️ Пропускаем сохранение: {screen_name}")
            return
        old = self._previous_screen
        self._previous_screen = screen_name
        logger.info(f"✅ предыдущий экран: {old} → {screen_name}")

    def get_previous(self) -> str | None:
        logger.debug(f"📌 предыдущий экран = {self._previous_screen}")
        return self._previous_screen

    def clear_previous(self):
        self._previous_screen = None

    # -------- Pending chord --------

    def set_pending_chord(self, chord: str):
        self._pending_chord = chord
        logger.debug(f"🎸 pending chord: {chord}")

    def get_pending_chord(self):
        return self._pending_chord

    def clear_pending_chord(self):
        self._pending_chord = None


previous_screen_state = PreviousScreenState()