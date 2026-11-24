# screens/songs/song_detail_screen.py
"""
Экран просмотра песни из каталога исполнителей / списка песен.
Наследует всю логику отображения, аккордов и плавающей панели от BaseSongDetailScreen.
"""
from kivy.clock import Clock
from kivymd.app import MDApp

from config.logger_config import screen_logger
from screens.songs.base_song_detail_screen import BaseSongDetailScreen
from state.artist_songs_state import artist_songs_state
from state.previous_screen import previous_screen_state
from config.navigation_config import navigate_back
logger = screen_logger('SongDetail')


class SongDetailScreen(BaseSongDetailScreen):
    SCREEN_NAME = 'song_detail'
    DEFAULT_PREVIOUS_SCREEN = 'artist_songs'
    DEFAULT_IS_FAVORITE = False


    def go_back(self, instance=None):
        if self.manager and self.manager.has_screen('artist_songs'):
            artist_data = artist_songs_state.get_artist_songs_data()
            artist_name = artist_data.get('artist_name', '')
            scroll_pos = artist_data.get('scroll_position', 1.0)
            artist_screen = self.manager.get_screen('artist_songs')
            if artist_name:
                artist_screen.artist_name = artist_name
                artist_screen._saved_scroll_position = scroll_pos
        previous_screen_state.clear_pending_chord()
        navigate_back(self.manager, self.SCREEN_NAME)

