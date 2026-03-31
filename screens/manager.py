# screens/manager.py
from kivy.uix.screenmanager import ScreenManager
from config.logger_config import get_logger
from .home_screen import HomeScreen
from .songs_screen import SongsScreen
from .artists_by_letter_screen import ArtistsByLetterScreen  # Новый экран
from .artist_songs_screen import ArtistSongsScreen
from .chords_screen import ChordsScreen
from .dictionary_screen import DictionaryScreen
from .tuner_screen import TunerScreen
from .favorites_screen import FavoritesScreen
from .profile_screen import ProfileScreen
from .song_detail_screen import SongDetailScreen
from .admin_screen import AdminScreen

logger = get_logger('ScreenManager')


def setup_screen_manager():
    sm = ScreenManager()

    print("🔴 manager: добавляем HomeScreen")
    sm.add_widget(HomeScreen(name='home'))
    print("🔴 manager: добавляем SongsScreen")
    sm.add_widget(SongsScreen(name='songs'))
    sm.add_widget(ArtistsByLetterScreen(name='artists_by_letter'))
    sm.add_widget(ArtistSongsScreen(name='artist_songs'))
    sm.add_widget(ChordsScreen(name='chords'))
    sm.add_widget(DictionaryScreen(name='dictionary'))
    sm.add_widget(TunerScreen(name='tuner'))
    sm.add_widget(FavoritesScreen(name='favorites'))
    print("🔴 manager: добавляем ProfileScreen")
    sm.add_widget(ProfileScreen(name='profile'))
    sm.add_widget(SongDetailScreen(name='song_detail'))
    sm.add_widget(AdminScreen(name='admin'))

    print(f"🔴 manager: текущий экран после добавления: {sm.current}")
    return sm