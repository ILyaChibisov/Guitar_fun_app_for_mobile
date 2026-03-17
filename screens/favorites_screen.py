from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from config.logger_config import screen_logger

logger = screen_logger('Favorites')

class FavoritesScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        label = MDLabel(
            text="❤️ Экран избранного",
            halign="center",
            font_style="H4"
        )
        self.add_widget(label)
        logger.info('Экран избранного создан')