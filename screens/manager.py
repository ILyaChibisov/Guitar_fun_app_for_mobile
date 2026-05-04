# screens/manager.py
from kivy.uix.screenmanager import ScreenManager
from config.logger_config import get_logger
from .home_screen import HomeScreen
from .songs_screen import SongsScreen
from .artists_by_letter_screen import ArtistsByLetterScreen
from .artist_songs_screen import ArtistSongsScreen
from .chords_screen import ChordsScreen
from .dictionary_screen import DictionaryScreen
from .tuner_screen import TunerScreen
from .favorites_screen import FavoritesScreen
from .profile_screen import ProfileScreen
from .song_detail_screen import SongDetailScreen
from .admin_screen import AdminScreen
from .search_results_screen import SearchResultsScreen
from .search_screen import SearchScreen
from .parsers_screens.amdm_parser_screen import AMDMParserScreen

logger = get_logger('ScreenManager')


def setup_screen_manager():
    sm = ScreenManager()

    sm.add_widget(HomeScreen(name='home'))
    sm.add_widget(SongsScreen(name='songs'))
    sm.add_widget(ArtistsByLetterScreen(name='artists_by_letter'))
    sm.add_widget(ArtistSongsScreen(name='artist_songs'))
    sm.add_widget(ChordsScreen(name='chords'))
    sm.add_widget(DictionaryScreen(name='dictionary'))
    # sm.add_widget(TunerScreen(name='tuner'))
    sm.add_widget(FavoritesScreen(name='favorites'))
    sm.add_widget(ProfileScreen(name='profile'))
    sm.add_widget(SongDetailScreen(name='song_detail'))
    sm.add_widget(AdminScreen(name='admin'))
    sm.add_widget(SearchResultsScreen(name='search_results'))
    sm.add_widget(SearchScreen(name='search'))
    sm.add_widget(AMDMParserScreen(name='amdm_parser'))

    logger.info('ScreenManager настроен, добавлено 15 экранов')
    return sm