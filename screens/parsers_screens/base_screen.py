# screens/base_screen.py
"""
Базовый класс для всех экранов с учётом системных панелей
"""
from kivymd.uix.screen import MDScreen
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from config.logger_config import get_logger

logger = get_logger('BaseScreen')


class BaseScreen(MDScreen):
    """
    Базовый экран с автоматическим отступом под системные панели.
    Все экраны должны наследоваться от этого класса.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0, 0, 0, 0]

        # Добавляем отступы при инициализации
        self.bind(pos=self._update_padding, size=self._update_padding)

    def _update_padding(self, *args):
        """Обновляет отступы экрана (может быть переопределён)"""
        pass

    def get_top_padding(self):
        """
        Возвращает отступ сверху для контента.
        Вызывается в init_ui() каждого экрана для создания top_spacer.
        """
        from config.system_bars import get_status_bar_height
        from config.theme import theme

        status_h = get_status_bar_height()
        # Возвращаем отступ = статус-бар + высота TopNav
        return status_h + theme.TOP_NAV_HEIGHT


class BaseScreenWithTopSpacer(BaseScreen):
    """
    Базовый экран с автоматическим top_spacer.
    Экран автоматически добавит отступ под системные панели и TopNav.
    """

    def add_top_spacer(self, layout):
        """
        Добавляет верхний отступ в переданный layout.

        Args:
            layout: MDBoxLayout или другой контейнер, куда добавить spacer
        """
        from config.system_bars import get_status_bar_height
        from config.theme import theme

        status_h = get_status_bar_height()
        total_padding = status_h + theme.TOP_NAV_HEIGHT

        top_spacer = Widget(size_hint_y=None, height=dp(total_padding))
        layout.add_widget(top_spacer)
        return top_spacer