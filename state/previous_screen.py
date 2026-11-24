# state/previous_screen.py
"""
Централизованный стек навигации приложения + pending chord.
"""
from kivy.logger import Logger

logger = Logger.getChild('State:Nav')

# Корневые экраны (сброс стека при переходе через нижнее или боковое меню)
ROOT_SCREENS = {
    'home', 'songs', 'chords', 'tuner', 'metronome',
    'favorites', 'dictionary', 'profile', 'search',
    'help', 'promo', 'feedback', 'admin'
}

# Жесткие маршруты возврата по умолчанию (если стек пуст)
DEFAULT_BACK_ROUTES = {
    'artist_songs': 'songs',
    'song_detail': 'artist_songs',
    'search_detail': 'songs',
    'search_screen_detail': 'search',
    'favorite_detail': 'favorites',
    'term_detail': 'dictionary',
    'search_term_detail': 'search',
    'chord_detail': 'chords',
}


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
        self._history: list[str] = []
        self._pending_chord = None

    def push(self, from_screen: str, to_screen: str):
        """Регистрирует переход между экранами."""
        if not from_screen or from_screen == to_screen:
            return

        # Если перешли на корневой экран — очищаем историю вложенности
        if to_screen in ROOT_SCREENS:
            self._history.clear()
            logger.debug(f"🏠 Переход на корневой экран {to_screen}, стек очищен")
            return

        # Если возвращаемся назад по стеку — не дублируем запись
        if self._history and self._history[-1] == to_screen:
            self._history.pop()
            return

        if not self._history or self._history[-1] != from_screen:
            self._history.append(from_screen)
        logger.info(f"📚 Стек навигации: {self._history} -> [{to_screen}]")

    def pop_previous(self, current_screen: str) -> str:
        """Возвращает экран для перехода назад и убирает его из стека."""
        while self._history:
            prev = self._history.pop()
            if prev != current_screen:
                logger.info(f"⬅️ Возврат по стеку: {current_screen} -> {prev}")
                return prev

        fallback = DEFAULT_BACK_ROUTES.get(current_screen, 'home')
        logger.info(f"⬅️ Возврат по маршруту по умолчанию: {current_screen} -> {fallback}")
        return fallback

    # Обратная совместимость со старыми вызовами
    def set_previous(self, screen_name: str):
        if screen_name and (not self._history or self._history[-1] != screen_name):
            self._history.append(screen_name)

    def get_previous(self) -> str | None:
        return self._history[-1] if self._history else None

    def clear_previous(self):
        self._history.clear()

    # -------- Pending chord --------
    def set_pending_chord(self, chord: str):
        self._pending_chord = chord

    def get_pending_chord(self):
        return self._pending_chord

    def clear_pending_chord(self):
        self._pending_chord = None


previous_screen_state = PreviousScreenState()
