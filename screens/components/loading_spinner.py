# screens/components/loading_spinner.py
"""
Универсальный компонент загрузки с круговым спиннером - строго по центру.
Цвета автоматически подстраиваются под текущую тему.
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.spinner import MDSpinner

from config.logger_config import get_logger
from state.settings_state import settings_state

logger = get_logger('LoadingSpinner')


def get_theme_colors():
    """Возвращает (цвет_спиннера, цвет_текста, цвет_фона_оверлея) для текущей темы."""
    theme_id = settings_state.theme

    if theme_id == 'light':
        # Светлая тема: тёмный спиннер, тёмный текст, светлый фон оверлея
        return (
            [0.1, 0.55, 0.3, 1],  # спиннер: зелёный
            [0.2, 0.2, 0.2, 1],  # текст: тёмно-серый
            [1, 1, 1, 0.6],  # фон: белый полупрозрачный
        )
    elif theme_id == 'dark':
        # Тёмная тема: оранжевый спиннер, светлый текст, тёмный фон
        return (
            [1.0, 0.5, 0.0, 1],  # спиннер: оранжевый
            [1, 1, 1, 0.85],  # текст: белый
            [0, 0, 0, 0.5],  # фон: чёрный полупрозрачный
        )
    else:  # green
        # Зелёная тема: белый спиннер, белый текст, тёмный фон
        return (
            [1, 1, 1, 1],  # спиннер: белый
            [1, 1, 1, 0.85],  # текст: белый
            [0, 0, 0, 0.4],  # фон: чёрный полупрозрачный
        )


class LoadingSpinner(FloatLayout):
    """Анимированный круговой спиннер с подписью - строго по центру"""

    def __init__(self, text="Загрузка...", **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self._base_text = text

        # ✅ Берём цвета под текущую тему
        spinner_color, text_color, bg_color = get_theme_colors()
        self._spinner_color = spinner_color
        self._text_color = text_color
        self._bg_color = bg_color

        # ============ КОНТЕЙНЕР ДЛЯ ЦЕНТРИРОВАНИЯ ============
        self.container = MDBoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            size=(dp(200), dp(120)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            spacing=dp(16)
        )

        # ============ КРУГОВОЙ СПИННЕР ============
        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5},
            active=True,
            palette=[
                self._spinner_color,  # цвет полного круга
                self._spinner_color,  # цвет фона (можно полупрозрачный)
            ]
        )

        # ============ ТЕКСТ ПОД СПИННЕРОМ ============
        self.label = MDLabel(
            text=text,
            halign="center",
            font_size=sp(16),
            theme_text_color="Custom",
            text_color=self._text_color,
            size_hint=(1, None),
            height=dp(40),
            pos_hint={'center_x': 0.5}
        )

        self.container.add_widget(self.spinner)
        self.container.add_widget(self.label)
        self.add_widget(self.container)

        self._is_loading = True

    def start_animation(self):
        """Запускает анимацию спиннера"""
        self._is_loading = True
        self.spinner.active = True
        self.opacity = 1

    def stop_animation(self):
        """Останавливает анимацию и скрывает спиннер"""
        self._is_loading = False
        self.spinner.active = False
        anim = Animation(opacity=0, duration=0.2)
        anim.start(self)

    def set_text(self, text):
        """Обновляет текст под спиннером"""
        self._base_text = text
        self.label.text = text

    def get_overlay_color(self):
        """Возвращает цвет фона оверлея для текущей темы."""
        return self._bg_color