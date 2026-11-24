# screens/favorite/favorite_detail_screen.py
"""
Экран детального просмотра избранной песни.
Наследует всю логику отображения, аккордов, плавающей панели и навигации от BaseSongDetailScreen.
"""
from kivy.clock import Clock
from screens.songs.base_song_detail_screen import BaseSongDetailScreen


class FavoriteDetailScreen(BaseSongDetailScreen):
    SCREEN_NAME = 'favorite_detail'
    DEFAULT_PREVIOUS_SCREEN = 'favorites'
    DEFAULT_IS_FAVORITE = True

    def _remove_from_favorites(self):
        super()._remove_from_favorites()
        Clock.schedule_once(lambda dt: self.go_back(), 0.3)
