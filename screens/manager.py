# screens/manager.py
from kivy.uix.screenmanager import ScreenManager
from config.logger_config import get_logger
from .home_screen import HomeScreen
from .songs_screen import SongsScreen
from .chords_screen import ChordsScreen
from .dictionary_screen import DictionaryScreen
from .tuner_screen import TunerScreen
from .favorites_screen import FavoritesScreen
from .profile_screen import ProfileScreen

logger = get_logger('ScreenManager')


def setup_screen_manager():
    sm = ScreenManager()

    sm.add_widget(HomeScreen(name='home'))
    sm.add_widget(SongsScreen(name='songs'))
    sm.add_widget(ChordsScreen(name='chords'))
    sm.add_widget(DictionaryScreen(name='dictionary'))
    sm.add_widget(TunerScreen(name='tuner'))
    sm.add_widget(FavoritesScreen(name='favorites'))
    sm.add_widget(ProfileScreen(name='profile'))

    logger.info(f'Загружено {len(sm.screens)} экранов')

    return sm