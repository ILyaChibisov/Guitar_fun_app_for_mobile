# screens/base_screen.py
"""
Базовый класс для всех экранов с едиными отступами
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from config.layout_config import layout_config
from config.logger_config import screen_logger

logger = screen_logger('BaseScreen')


class BaseScreen(MDScreen):
    """
    Базовый экран с автоматическими отступами для контента.
    Все экраны должны наследоваться от этого класса.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0, 0, 0, 0]
        self._content_container = None
        self._main_layout = None

    def on_enter(self):
        """Вызывается при входе на экран - можно переопределить в дочерних классах"""
        pass

    def on_leave(self):
        """Вызывается при выходе с экрана - можно переопределить в дочерних классах"""
        pass

    def build_ui(self, content_widget=None, top_widget=None):
        """
        Строит UI с правильными отступами.

        Args:
            content_widget: Основной виджет с контентом (RecycleView, ScrollView и т.д.)
            top_widget: Дополнительный виджет над контентом (счётчик, заголовок и т.д.)
        """
        # Создаём основной контейнер
        self._main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ
        top_padding = layout_config.get_top_padding()
        self._main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Дополнительный виджет сверху (если есть)
        if top_widget:
            self._main_layout.add_widget(top_widget)

        # Контейнер для контента с нижним отступом
        bottom_padding = layout_config.get_bottom_padding()
        side_padding = layout_config.SIDE_PADDING

        self._content_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[side_padding, dp(4), side_padding, bottom_padding]
        )

        # Добавляем основной контент
        if content_widget:
            self._content_container.add_widget(content_widget)

        self._main_layout.add_widget(self._content_container)
        self.add_widget(self._main_layout)

        logger.debug(f"BaseScreen UI построен для {self.name}, "
                     f"top_padding={top_padding}dp, bottom_padding={bottom_padding}dp")

    def get_content_container(self):
        """Возвращает контейнер для добавления контента"""
        return self._content_container

    def add_content_widget(self, widget, index=None):
        """Добавляет виджет в контейнер контента"""
        if self._content_container:
            if index is None:
                self._content_container.add_widget(widget)
            else:
                self._content_container.add_widget(widget, index)

    def clear_content(self):
        """Очищает контейнер контента"""
        if self._content_container:
            self._content_container.clear_widgets()

    def show_loading(self, text="Загрузка..."):
        """Показывает индикатор загрузки"""
        self.clear_content()
        loading_label = MDLabel(
            text=text,
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_y=None,
            height=dp(60)
        )
        self.add_content_widget(loading_label)
        return loading_label

    def show_empty(self, text="Нет данных"):
        """Показывает сообщение о пустом списке"""
        self.clear_content()
        empty_label = MDLabel(
            text=text,
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4],
            size_hint_y=None,
            height=dp(60)
        )
        self.add_content_widget(empty_label)
        return empty_label

    def show_error(self, text="Ошибка загрузки"):
        """Показывает сообщение об ошибке"""
        self.clear_content()
        error_label = MDLabel(
            text=text,
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None,
            height=dp(60)
        )
        self.add_content_widget(error_label)
        return error_label