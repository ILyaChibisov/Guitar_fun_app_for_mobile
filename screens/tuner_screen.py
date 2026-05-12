# screens/tuner_screen.py
"""
Экран гитарного тюнера - режим разработки и тестирования
"""
from kivy.metrics import dp, sp
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.widget import Widget

from config.theme import theme
from config.logger_config import screen_logger
from screens.base_screen import BaseScreen

logger = screen_logger('Tuner')


class TunerScreen(BaseScreen):
    """Экран гитарного тюнера - режим разработки"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'

        self.init_ui()
        logger.info('Экран тюнера создан (режим разработки)')

    def init_ui(self):
        # Создаём контент
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        # Информационная карточка
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(200),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            radius=[theme.CORNER_RADIUS_MEDIUM, theme.CORNER_RADIUS_MEDIUM,
                    theme.CORNER_RADIUS_MEDIUM, theme.CORNER_RADIUS_MEDIUM],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        # Иконка тюнера (текстовая)
        icon_label = MDLabel(
            text="🎸",
            font_size=sp(64),
            halign="center",
            size_hint_y=None,
            height=dp(80),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9]
        )

        # Заголовок
        title_label = MDLabel(
            text="Гитарный тюнер",
            font_size=sp(24),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )

        # Статус разработки
        status_label = MDLabel(
            text="🚧 В РАЗРАБОТКЕ 🚧",
            font_size=sp(16),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[0.9, 0.6, 0.2, 1]
        )

        # Описание
        desc_label = MDLabel(
            text="Функция тюнера будет доступна в следующей версии приложения.\n\n"
                 "Планируемая функциональность:\n"
                 "• Точная настройка 6-струнной гитары\n"
                 "• Поддержка альтернативных строев\n"
                 "• Визуальный индикатор отклонения\n"
                 "• Звуковой сигнал для каждой струны",
            halign="center",
            font_size=sp(12),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            line_height=1.5,
            markup=True
        )

        info_card.add_widget(icon_label)
        info_card.add_widget(title_label)
        info_card.add_widget(status_label)
        info_card.add_widget(Widget(size_hint_y=None, height=dp(8)))
        info_card.add_widget(desc_label)

        content.add_widget(info_card)

        # Дополнительный отступ снизу
        content.add_widget(Widget(size_hint_y=None, height=dp(20)))

        # Строим UI с прокруткой
        self.build_ui(content_widget=content, use_scroll=True)