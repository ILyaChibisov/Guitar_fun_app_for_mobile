# screens/base_screen.py
"""
Базовый класс для всех экранов с автоматическими отступами
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window

from config.layout_config import layout_config
from config.logger_config import screen_logger
from config.system_bars import get_navigation_bar_height

logger = screen_logger('BaseScreen')


class BaseScreen(MDScreen):
    """
    Базовый экран с автоматическими отступами для контента.
    Все экраны должны наследоваться от этого класса.
    """

    # Текущая высота BottomNav (должна совпадать с bottom_nav.py)
    BOTTOM_NAV_HEIGHT = dp(44)
    # Отступ между контентом и BottomNav
    BOTTOM_NAV_GAP = dp(8)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = [0, 0, 0, 0]
        self._content_container = None
        self._main_layout = None
        self._top_spacer = None
        self._bottom_spacer = None
        self._scroll_view = None
        self._scroll_content = None
        self._content_widget = None
        self._use_scroll = False
        self._custom_padding = None

        # ============ ФЛАГ: ЭКРАН САМ УПРАВЛЯЕТ ОТСТУПАМИ ============
        # Если True - BaseScreen НЕ создаёт и НЕ обновляет отступы
        # Используется в экранах детального просмотра (song_detail, favorite_detail, etc.)
        self._manage_padding_manually = False

        # Привязываемся к изменению размера окна (поворот экрана)
        Window.bind(on_resize=self._on_window_resize)

    def _on_window_resize(self, window, width, height):
        """Обработчик изменения размера окна - обновляем отступы"""
        Clock.schedule_once(lambda dt: self._update_layout(), 0.1)

    def _update_layout(self):
        """Обновляет layout при изменении размеров (поворот экрана)"""
        if not hasattr(self, '_main_layout') or not self._main_layout:
            return

        # ============ ЕСЛИ ЭКРАН САМ УПРАВЛЯЕТ ОТСТУПАМИ — НЕ ТРОГАЕМ ============
        if self._manage_padding_manually:
            logger.debug(f"{self.name}: ручное управление отступами, пропускаем _update_layout")
            return

        logger.debug(f"{self.name}: обновление layout после поворота")

        # Используем include_top_nav=True для всех экранов (TopNav прозрачный)
        top_padding = layout_config.get_top_padding(include_top_nav=True)
        bottom_padding = self._get_bottom_padding()

        if self._top_spacer:
            self._top_spacer.height = top_padding

        if self._bottom_spacer:
            self._bottom_spacer.height = bottom_padding

        # Обновляем отступ в ScrollView
        if self._scroll_view and self._use_scroll and self._scroll_content:
            nav_bar_height = get_navigation_bar_height()
            extra_bottom = self.BOTTOM_NAV_HEIGHT + nav_bar_height + self.BOTTOM_NAV_GAP
            self._scroll_content.padding = [0, 0, 0, extra_bottom]

        # Обновляем padding контента
        if self._content_container and self._custom_padding is None:
            padding = layout_config.get_content_padding()
            self._content_container.padding = padding

        logger.debug(f"{self.name}: layout обновлён, top={top_padding}dp, bottom={bottom_padding}dp")

    def _get_bottom_padding(self):
        """Возвращает правильный нижний отступ с учётом BottomNav"""
        nav_bar_height = get_navigation_bar_height()
        return self.BOTTOM_NAV_HEIGHT + nav_bar_height + self.BOTTOM_NAV_GAP

    def on_enter(self):
        """Вызывается при входе на экран - можно переопределить в дочерних классах"""
        self._update_layout()

    def on_leave(self):
        """Вызывается при выходе с экрана - можно переопределить в дочерних классах"""
        pass

    def build_ui(self, content_widget=None, top_widget=None, bottom_widget=None,
                 use_scroll=False, custom_padding=None, bottom_offset=0):
        """
        Строит UI с правильными отступами.

        Args:
            content_widget: Основной виджет с контентом (RecycleView, MDBoxLayout и т.д.)
            top_widget: Дополнительный виджет над контентом (счётчик, заголовок и т.д.)
            bottom_widget: Дополнительный виджет под контентом
            use_scroll: Использовать ли ScrollView для контента
            custom_padding: Свои отступы [left, top, right, bottom] (в dp)
            bottom_offset: Дополнительный отступ снизу (для экранов с панелью настроек)
        """
        self._use_scroll = use_scroll
        self._custom_padding = custom_padding
        self._content_widget = content_widget

        # Создаём основной контейнер
        self._main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ (под статус-бар и TopNav)
        top_padding = layout_config.get_top_padding()
        self._top_spacer = Widget(size_hint_y=None, height=top_padding)
        self._main_layout.add_widget(self._top_spacer)

        # Дополнительный виджет сверху (если есть)
        if top_widget:
            self._main_layout.add_widget(top_widget)

        # Контейнер для контента
        if custom_padding:
            padding = custom_padding
        else:
            padding = layout_config.get_content_padding()

        self._content_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=padding
        )

        # Добавляем основной контент (с ScrollView или без)
        if use_scroll:
            # Получаем правильный нижний отступ
            nav_bar_height = get_navigation_bar_height()
            extra_bottom = self.BOTTOM_NAV_HEIGHT + nav_bar_height + self.BOTTOM_NAV_GAP + dp(bottom_offset)

            # Создаём ScrollView со СКРЫТЫМ скроллбаром
            self._scroll_view = ScrollView(
                size_hint=(1, 1),
                do_scroll_x=False,
                bar_width=0,
                bar_color=[0, 0, 0, 0],
                bar_inactive_color=[0, 0, 0, 0],
                bar_margin=0
            )

            # Создаём внутренний контейнер для отступов
            self._scroll_content = MDBoxLayout(
                orientation='vertical',
                size_hint_y=None,
                adaptive_height=True,
                padding=[0, 0, 0, extra_bottom]
            )

            if content_widget:
                if hasattr(content_widget, 'minimum_height'):
                    content_widget.size_hint_y = None
                    content_widget.bind(minimum_height=content_widget.setter('height'))
                self._scroll_content.add_widget(content_widget)

            self._scroll_view.add_widget(self._scroll_content)
            self._content_container.add_widget(self._scroll_view)
        else:
            if content_widget:
                self._content_container.add_widget(content_widget)

        self._main_layout.add_widget(self._content_container)

        # Дополнительный виджет снизу (если есть)
        if bottom_widget:
            self._main_layout.add_widget(bottom_widget)

        # Нижний отступ (зазор перед BottomNav)
        bottom_padding = self._get_bottom_padding()
        self._bottom_spacer = Widget(size_hint_y=None, height=bottom_padding)
        self._main_layout.add_widget(self._bottom_spacer)

        self.add_widget(self._main_layout)

        logger.debug(f"BaseScreen UI построен для {self.name}, "
                     f"top_padding={top_padding}dp, bottom_padding={bottom_padding}dp, "
                     f"use_scroll={use_scroll}")

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

    def reset_ui(self):
        """Сбрасывает UI (очищает контент и убирает сообщения)"""
        self.clear_content()

    def on_orientation_changed(self):
        """Вызывается при повороте экрана - можно переопределить в дочерних экранах"""
        self._update_layout()
        logger.debug(f"{self.name}: ориентация изменена, layout обновлён")