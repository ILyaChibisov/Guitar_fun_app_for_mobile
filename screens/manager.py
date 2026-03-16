# screens/manager.py
"""
Настройка ScreenManager со всеми экранами
"""
from kivy.uix.screenmanager import ScreenManager, SlideTransition, FadeTransition
from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('ScreenManager')


def setup_screen_manager():
    """Создаёт и настраивает менеджер экранов"""

    # Создаём менеджер
    sm = ScreenManager()

    # Создаём переход отдельно и настраиваем его свойства
    transition = SlideTransition()
    transition.duration = theme.ANIMATION_DURATION
    transition.direction = 'left'  # или 'up', 'down', 'right'

    # Применяем переход
    sm.transition = transition

    # Импортируем все экраны (импорты внутри функции чтобы избежать циклов)
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

    logger.info(f'Загружено {len(sm.screens)} экранов: home, songs, chords, dictionary, tuner, favorites')

    # Устанавливаем начальный экран
    sm.current = 'home'

    return sm