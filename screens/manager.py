# screens/manager.py
"""
Настройка ScreenManager
"""
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from config.logger_config import get_logger

logger = get_logger('ScreenManager')


def setup_screen_manager():
    """Создаёт и настраивает менеджер экранов"""

    sm = ScreenManager()

    # Создаём переход
    transition = SlideTransition()
    transition.duration = 0.25
    transition.direction = 'left'
    sm.transition = transition

    # Импортируем все экраны
    from .home_screen import HomeScreen
    from .songs_screen import SongsScreen
    from .chords_screen import ChordsScreen
    from .dictionary_screen import DictionaryScreen
    from .tuner_screen import TunerScreen
    from .favorites_screen import FavoritesScreen

    # Создаём экземпляры с именами
    sm.add_widget(HomeScreen(name='home'))
    sm.add_widget(SongsScreen(name='songs'))
    sm.add_widget(ChordsScreen(name='chords'))
    sm.add_widget(DictionaryScreen(name='dictionary'))
    sm.add_widget(TunerScreen(name='tuner'))
    sm.add_widget(FavoritesScreen(name='favorites'))

    logger.info(f'Загружено {len(sm.screens)} экранов')

    return sm