# screens/components/loading_spinner.py
"""
Универсальный компонент загрузки с круговым спиннером - строго по центру
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.spinner import MDSpinner

from config.logger_config import get_logger

logger = get_logger('LoadingSpinner')


class LoadingSpinner(FloatLayout):
    """Анимированный круговой спиннер с подписью - строго по центру"""

    def __init__(self, text="Загрузка...", **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)

        # Сохраняем базовый текст
        self._base_text = text

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
            active=True
        )

        # ============ ТЕКСТ ПОД СПИННЕРОМ ============
        self.label = MDLabel(
            text=text,
            halign="center",
            font_size=sp(16),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
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
        # Плавное исчезновение
        anim = Animation(opacity=0, duration=0.2)
        anim.start(self)

    def set_text(self, text):
        """Обновляет текст под спиннером"""
        self._base_text = text
        self.label.text = text