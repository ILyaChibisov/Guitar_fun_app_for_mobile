# screens/tuner_screen.py
"""
Экран тюнера
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivy.metrics import dp, sp
from config.logger_config import screen_logger
from utils.kivy_imports import MDBoxLayout

logger = screen_logger('Tuner')


class TunerScreen(MDScreen):
    """Экран тюнера"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'

        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20)
        )

        label = MDLabel(
            text="🎤 Тюнер\n\nЗдесь будет гитарный тюнер",
            halign="center",
            font_size=sp(20),
            theme_text_color="Primary"
        )

        layout.add_widget(label)
        self.add_widget(layout)

        logger.info('Экран тюнера создан')