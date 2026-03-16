# screens/components/buttons.py
"""
Современные кнопки в стиле Material Design
"""
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.properties import ListProperty, StringProperty, NumericProperty
from kivy.metrics import dp, sp
from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('UI')


class GradientButton(Button):
    """Кнопка с градиентным фоном"""

    gradient_start = ListProperty([0.4, 0.2, 0.9, 1])  # PRIMARY
    gradient_end = ListProperty([0.2, 0.1, 0.5, 1])  # PRIMARY_VARIANT

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.font_size = theme.FONT_SIZE_BODY
        self.color = theme.TEXT_ON_PRIMARY
        self.bold = True
        self.size_hint = (None, None)
        self.size = (dp(200), dp(50))

        with self.canvas.before:
            # Градиент (упрощённо - сплошной цвет)
            Color(*self.gradient_start)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[theme.CORNER_RADIUS]
            )

        self.bind(pos=self.update_rect, size=self.update_rect)
        logger.debug('Создана градиентная кнопка')

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
    """Плавающая кнопка действия (FAB)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (dp(56), dp(56))

        with self.canvas.before:
            Color(*theme.SECONDARY)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(28)]
            )

        logger.debug('Создана FAB кнопка')