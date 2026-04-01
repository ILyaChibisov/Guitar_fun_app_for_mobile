# screens/favorites_screen.py
"""
Экран избранного
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from config.logger_config import screen_logger
from utils.kivy_imports import MDBoxLayout

logger = screen_logger('Favorites')


class FavoritesScreen(MDScreen):
    """Экран избранного"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'

        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20)
        )

        label = MDLabel(
            text="❤️ Избранное\n\nЗдесь будут сохранённые песни и аккорды",
            halign="center",
            font_style="H5"
        )

        layout.add_widget(label)
        self.add_widget(layout)

        logger.info('Экран избранного создан')