# screens/dictionary_screen.py
"""
Экран словаря терминов
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from config.logger_config import screen_logger
from utils.kivy_imports import MDBoxLayout

logger = screen_logger('Dictionary')


class DictionaryScreen(MDScreen):
    """Экран словаря"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dictionary'

        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20)
        )

        label = MDLabel(
            text="📚 Словарь терминов\n\nЗдесь будут определения музыкальных терминов",
            halign="center",
            font_style="H5"
        )

        layout.add_widget(label)
        self.add_widget(layout)

        logger.info('Экран словаря создан')