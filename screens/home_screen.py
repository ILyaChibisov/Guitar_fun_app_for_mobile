# screens/home_screen.py
"""
Главный экран
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from config.theme import theme
from config.logger_config import screen_logger

logger = screen_logger('Home')


class HomeScreen(MDScreen):
    """Главный экран"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Главный контейнер
        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20)
        )

        # Заголовок
        title = MDLabel(
            text="🎸 GuitarApp",
            font_style="H3",
            halign="center",
            size_hint_y=None,
            height=dp(100),
            theme_text_color="Primary"
        )

        # Подзаголовок
        subtitle = MDLabel(
            text="Твоё приложение для гитаристов",
            font_style="Subtitle1",
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Secondary"
        )

        # Кнопки быстрого доступа
        buttons_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(200),
            pos_hint={"center_x": 0.5}
        )

        tuner_btn = MDRaisedButton(
            text="🎤 Открыть тюнер",
            size_hint=(0.8, None),
            height=dp(50),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            on_release=lambda x: setattr(self.manager, 'current', 'tuner')
        )

        songs_btn = MDRaisedButton(
            text="🎵 Список песен",
            size_hint=(0.8, None),
            height=dp(50),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            on_release=lambda x: setattr(self.manager, 'current', 'songs')
        )

        chords_btn = MDRaisedButton(
            text="🎸 Аккорды",
            size_hint=(0.8, None),
            height=dp(50),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            on_release=lambda x: setattr(self.manager, 'current', 'chords')
        )

        buttons_layout.add_widget(tuner_btn)
        buttons_layout.add_widget(songs_btn)
        buttons_layout.add_widget(chords_btn)

        # Собираем всё вместе
        layout.add_widget(title)
        layout.add_widget(subtitle)
        layout.add_widget(buttons_layout)

        self.add_widget(layout)

        logger.info('Главный экран создан')