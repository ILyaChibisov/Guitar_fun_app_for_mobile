# screens/search_song_detail_screen.py
"""
Экран просмотра песни ИЗ ПОИСКА (songs_screen).
Возврат только в SongsScreen с сохранением результатов поиска.
Наследует всю логику отображения, аккордов и плавающей панели от BaseSongDetailScreen.
"""
from kivy.clock import Clock
from kivymd.app import MDApp

from config.logger_config import screen_logger
from screens.songs.base_song_detail_screen import BaseSongDetailScreen

logger = screen_logger('SearchDetail')


class SearchDetailScreen(BaseSongDetailScreen):
    SCREEN_NAME = 'search_detail'
    DEFAULT_PREVIOUS_SCREEN = 'songs'
    DEFAULT_IS_FAVORITE = False

    def go_back(self, instance=None):
        """Возврат ТОЛЬКО в SongsScreen с сохранением результатов поиска."""
        logger.info("Возврат из поискового просмотра в SongsScreen")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('songs')

        if self.manager and self.manager.has_screen('songs'):
            songs_screen = self.manager.get_screen('songs')
            if hasattr(songs_screen, 'restore_search_state'):
                Clock.schedule_once(
                    lambda dt: songs_screen.restore_search_state(), 0.1
                )
            self.manager.current = 'songs'
        else:
            self.manager.current = 'home'
