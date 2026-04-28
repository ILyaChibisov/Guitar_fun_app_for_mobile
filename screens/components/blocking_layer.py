# screens/components/blocking_layer.py
"""
Блокирующий слой - перехватывает все касания, кроме модального окна
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from config.logger_config import get_logger

logger = get_logger('UI')


class BlockingLayer(Widget):
    """Прозрачный слой, блокирующий все касания, кроме модального окна"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.pos = (0, 0)
        self.modal_widget = None
        self._active = False
        self._color_instruction = None  # Сохраняем ссылку на Color

        with self.canvas.before:
            self._color_instruction = Color(0, 0, 0, 0)  # Начинаем с прозрачного
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_rect, size=self._update_rect)

        self.register_event_type('on_touch_down')
        self.register_event_type('on_touch_move')
        self.register_event_type('on_touch_up')

        logger.info("Блокирующий слой создан")

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_active(self, active):
        """Активирует или деактивирует блокирующий слой"""
        self._active = active
        if active and self._color_instruction:
            self._color_instruction.rgba = (0, 0, 0, 0.5)  # Затемнение 50%
            logger.info("Блокирующий слой активирован")
        elif self._color_instruction:
            self._color_instruction.rgba = (0, 0, 0, 0)  # Прозрачный
            self.modal_widget = None
            logger.info("Блокирующий слой деактивирован")

    def set_modal_widget(self, widget):
        self.modal_widget = widget

    def clear_modal_widget(self):
        self.modal_widget = None

    def on_touch_down(self, touch):
        if not self._active:
            return False

        # Проверяем, не попал ли touch в модальное окно
        if self.modal_widget and self.modal_widget.collide_point(*touch.pos):
            return False

        logger.debug(f"Блокирующий слой перехватил касание: {touch.pos}")
        return True

    def on_touch_move(self, touch):
        if not self._active:
            return False

        if self.modal_widget and self.modal_widget.collide_point(*touch.pos):
            return False
        return True

    def on_touch_up(self, touch):
        if not self._active:
            return False

        if self.modal_widget and self.modal_widget.collide_point(*touch.pos):
            return False
        return True