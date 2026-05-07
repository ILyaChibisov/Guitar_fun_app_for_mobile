# screens/dictionary_screen.py - исправленный
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from config.logger_config import screen_logger
from config.system_bars import get_status_bar_height
from config.theme import theme
from utils.kivy_imports import MDBoxLayout

logger = screen_logger('Dictionary')


class DictionaryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dictionary'
        self.md_bg_color = [0, 0, 0, 0]

        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20)
        )

        # Отступ под системные панели
        status_h = get_status_bar_height()
        total_top_padding = status_h + theme.TOP_NAV_HEIGHT
        top_spacer = Widget(size_hint_y=None, height=dp(total_top_padding))
        layout.add_widget(top_spacer)

        label = MDLabel(
            text="📚 Словарь терминов\n\nЗдесь будут определения музыкальных терминов",
            halign="center",
            font_size=sp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )

        layout.add_widget(label)
        self.add_widget(layout)

        logger.info('Экран словаря создан')