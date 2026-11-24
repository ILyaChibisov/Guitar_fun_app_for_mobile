# screens/search/find_song_detail_screen.py
"""
Экран просмотра песни, открытой из глобального поиска.
Наследует всю логику отображения, аккордов и плавающей панели от BaseSongDetailScreen.
"""
from kivymd.app import MDApp

from config.logger_config import screen_logger
from screens.songs.base_song_detail_screen import BaseSongDetailScreen

logger = screen_logger('SearchScreenDetail')


class SearchScreenDetail(BaseSongDetailScreen):
    SCREEN_NAME = 'search_screen_detail'
    DEFAULT_PREVIOUS_SCREEN = 'search'
    DEFAULT_IS_FAVORITE = False

    def go_back(self, instance=None):
        logger.info(f"Нажата кнопка назад на SearchScreenDetail -> {self.previous_screen}")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('search')

        if self.manager:
            target = self.previous_screen if self.manager.has_screen(self.previous_screen) else 'search'
            self.manager.current = target if self.manager.has_screen(target) else 'home'
