# screens/parsers_screens/base_parser_screen.py
"""
Базовый класс для всех экранов парсеров с едиными отступами
"""
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView

from config.logger_config import screen_logger
from config.layout_config import layout_config

logger = screen_logger('BaseParserScreen')


class BaseParserScreen(MDScreen):
    """
    Базовый класс для экранов парсеров.
    Автоматически добавляет правильные отступы под системные панели.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0, 0, 0, 0]
        self._main_layout = None
        self._content_layout = None

    def build_ui(self, content_widget, scroll=True):
        """
        Строит UI с правильными отступами.

        Args:
            content_widget: Виджет с контентом (обычно MDBoxLayout)
            scroll: Обернуть ли в ScrollView
        """
        if scroll:
            scroll_view = MDScrollView(
                size_hint=(1, 1),
                do_scroll_x=False,
                bar_color=[1, 1, 1, 0.2],
                bar_width=dp(3)
            )
            scroll_view.add_widget(content_widget)
            final_widget = scroll_view
        else:
            final_widget = content_widget

        # Создаём основной контейнер с отступами
        self._main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0
        )

        # Добавляем верхний отступ (под статус-бар и TopNav)
        top_padding = layout_config.get_top_padding()
        self._main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Добавляем контент
        self._main_layout.add_widget(final_widget)

        # Добавляем нижний отступ (зазор перед BottomNav)
        bottom_padding = layout_config.get_bottom_padding()
        self._main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))

        self.add_widget(self._main_layout)

        logger.debug(f"BaseParserScreen UI построен для {self.name}, "
                     f"top_padding={top_padding}dp, bottom_padding={bottom_padding}dp")

    def get_content_layout(self):
        """Возвращает контейнер для добавления контента (если нужно)"""
        return self._content_layout