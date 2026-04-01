# screens/components/buttons.py
"""
Современные кнопки с мягким зелёным цветом
"""
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.properties import ListProperty
from kivy.metrics import dp, sp
from config.theme import theme
from config.logger_config import get_logger
from utils.kivy_imports import MDRaisedButton, MDIconButton

logger = get_logger('UI')


class GradientButton(Button):
    """Кнопка с мягким зелёным фоном"""

    gradient_start = ListProperty([0.46, 0.70, 0.71, 1])  # RGB: 118,179,182
    gradient_end = ListProperty([0.35, 0.56, 0.57, 1])  # Тёмная версия

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.font_size = theme.FONT_SIZE_BODY if hasattr(theme, 'FONT_SIZE_BODY') else sp(14)
        self.color = theme.TEXT_PRIMARY if hasattr(theme, 'TEXT_PRIMARY') else [1, 1, 1, 1]
        self.bold = True
        self.size_hint = (None, None)
        self.size = (dp(200), dp(50))

        with self.canvas.before:
            # Мягкий зелёный фон
            Color(*self.gradient_start)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[theme.CORNER_RADIUS]
            )

        self.bind(pos=self.update_rect, size=self.update_rect)
        logger.debug('Создана кнопка с мягким зелёным цветом')

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class IconButton(ButtonBehavior, Image):
    """Кнопка-иконка"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(48), dp(48))
        self.mipmap = True

    def on_press(self):
        anim = Animation(opacity=0.5, duration=0.1)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)


class FloatingActionButton(GradientButton):
    """Плавающая кнопка действия (FAB) - мягкий зелёный"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (dp(60), dp(60))
        self.gradient_start = [0.46, 0.70, 0.71, 1]  # Мягкий зелёный
        self.gradient_end = [0.35, 0.56, 0.57, 1]  # Тёмная версия

        with self.canvas.before:
            Color(*self.gradient_start)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(30)]
            )

        logger.debug('Создана FAB кнопка с мягким зелёным цветом')