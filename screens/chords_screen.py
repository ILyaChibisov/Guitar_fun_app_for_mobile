# screens/chords_screen.py
"""
Экран аккордов
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from config.logger_config import screen_logger
from utils.kivy_imports import MDBoxLayout

logger = screen_logger('Chords')


class ChordsScreen(MDScreen):
    """Экран аккордов"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chords'

        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20)
        )

        label = MDLabel(
            text="🎸 Экран аккордов\n\nЗдесь будут аппликатуры аккордов",
            halign="center",
            font_style="H5"
        )

        layout.add_widget(label)
        self.add_widget(layout)

        logger.info('Экран аккордов создан')