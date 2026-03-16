# screens/manager.py
"""
Настройка ScreenManager со всеми экранами
"""
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('ScreenManager')


class ObservableScreenManager(ScreenManager):
    """ScreenManager, который уведомляет о смене экрана"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observers = []

    def add_observer(self, callback):
        """Добавляет наблюдателя за сменой экрана"""
        if callback not in self.observers:
            self.observers.append(callback)

    def remove_observer(self, callback):
        """Удаляет наблюдателя"""
        if callback in self.observers:
            self.observers.remove(callback)

    def notify_observers(self, screen_name):
        """Уведомляет наблюдателей о смене экрана"""
        for callback in self.observers:
            try:
                callback(screen_name)
            except Exception as e:
                logger.error(f'Ошибка при уведомлении наблюдателя: {e}')

    def on_current(self, instance, value):
        """Переопределяем смену текущего экрана"""
        super().on_current(instance, value)
        self.notify_observers(value)


def setup_screen_manager():
    """Создаёт и настраивает менеджер экранов"""

    # Используем наш наблюдаемый менеджер
    sm = ObservableScreenManager()

    # Создаём переход
    transition = SlideTransition()
    transition.duration = theme.ANIMATION_DURATION
    transition.direction = 'left'
    sm.transition = transition

    # Импортируем все экраны
    from .home_screen import HomeScreen
    from .songs_screen import SongsScreen
    from .chords_screen import ChordsScreen
    from .dictionary_screen import DictionaryScreen
    from .tuner_screen import TunerScreen
    from .favorites_screen import FavoritesScreen

    # Добавляем экраны
    sm.add_widget(HomeScreen())
    sm.add_widget(SongsScreen())
    sm.add_widget(ChordsScreen())
    sm.add_widget(DictionaryScreen())
    sm.add_widget(TunerScreen())
    sm.add_widget(FavoritesScreen())

    logger.info(f'Загружено {len(sm.screens)} экранов')

    # Устанавливаем начальный экран
    sm.current = 'home'

    return sm