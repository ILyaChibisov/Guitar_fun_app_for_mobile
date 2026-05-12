# screens/dictionary_screen.py
"""
Экран словаря терминов - переведён на BaseScreen
"""
from kivymd.uix.label import MDLabel
from kivy.metrics import dp, sp

from config.logger_config import screen_logger
from screens.base_screen import BaseScreen
from utils.kivy_imports import MDBoxLayout, MDCard

logger = screen_logger('Dictionary')


class DictionaryScreen(BaseScreen):
    """Экран словаря музыкальных терминов"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dictionary'

        self.init_ui()
        logger.info('Экран словаря создан (BaseScreen)')

    def init_ui(self):
        # Создаём контент
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        # Заголовок
        title_label = MDLabel(
            text="📚 Словарь музыкальных терминов",
            halign="center",
            font_size=sp(20),
            bold=True,
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )
        content.add_widget(title_label)

        # Информационная карточка
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(150),
            padding=[dp(20), dp(16), dp(20), dp(16)],
            radius=[14, 14, 14, 14],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        info_label = MDLabel(
            text="Здесь будут определения музыкальных терминов\n\n"
                 "• Аккорд\n"
                 "• Арпеджио\n"
                 "• Баррэ\n"
                 "• Гамма\n"
                 "• Интервал\n"
                 "• И многое другое...\n\n"
                 "Функционал в разработке",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            line_height=1.5
        )
        info_card.add_widget(info_label)
        content.add_widget(info_card)

        # Строим UI с прокруткой
        self.build_ui(content_widget=content, use_scroll=True)