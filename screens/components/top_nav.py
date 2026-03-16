# screens/components/top_nav.py
"""
Верхняя навигационная панель с названиями разделов
Адаптируется под размер экрана
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, BooleanProperty, ListProperty, NumericProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.utils import rgba
from kivy.core.window import Window

from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('UI')


class NavTab(ButtonBehavior, BoxLayout):
    """Вкладка верхней навигации"""

    title = StringProperty('')
    active = BooleanProperty(False)
    tab_width = NumericProperty(0)  # Будет вычисляться автоматически

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.padding = [dp(15), 0, dp(15), 0]

        # Название раздела
        self.title_label = Label(
            text=self.title,
            font_size=theme.FONT_SIZE_BODY,
            color=theme.TEXT_SECONDARY,
            bold=False,
            size_hint=(1, 1),
            valign='middle',
            halign='center'
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))

        self.add_widget(self.title_label)

        # Индикатор активной вкладки (зелёная полоска снизу)
        with self.canvas.after:
            # Полоска будет видна только когда active=True
            Color(*rgba(theme.PRIMARY))
            self.active_line = RoundedRectangle(
                pos=(self.x, self.y + dp(3)),
                size=(self.width, dp(3)),
                radius=[dp(1.5)]
            )

        self.bind(pos=self.update_active_line, size=self.update_active_line)
        self.bind(active=self.update_state)
        self.bind(width=self.update_active_line)

        self.update_state(None, self.active)
        logger.debug(f'Создана вкладка: {self.title}')

    def update_state(self, instance, value):
        """Обновляет внешний вид при активации"""
        if value:
            # Активная вкладка
            self.title_label.color = theme.PRIMARY  # Зелёный текст
            self.title_label.bold = True
            self.active_line.size = (self.width, dp(3))
            self.active_line.pos = (self.x, self.y + dp(3))
        else:
            # Неактивная вкладка
            self.title_label.color = theme.TEXT_SECONDARY  # Серый текст
            self.title_label.bold = False
            self.active_line.size = (0, 0)  # Прячем полоску

    def update_active_line(self, *args):
        """Обновляет позицию индикатора"""
        if hasattr(self, 'active_line'):
            if self.active:
                self.active_line.pos = (self.x, self.y + dp(3))
                self.active_line.size = (self.width, dp(3))
            else:
                self.active_line.size = (0, 0)

    def on_press(self):
        """Анимация нажатия"""
        anim = Animation(opacity=0.7, duration=0.1)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self.title_label)


class TopNav(BoxLayout):
    """Верхняя навигационная панель с адаптивными вкладками"""

    # Список разделов
    tabs = ListProperty([
        {'title': 'Главная', 'screen': 'home'},
        {'title': 'Песни', 'screen': 'songs'},
        {'title': 'Аккорды', 'screen': 'chords'},
        {'title': 'Словарь', 'screen': 'dictionary'},
        {'title': 'Избранное', 'screen': 'favorites'}
    ])

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(60)  # Высота верхней панели

        # Фон верхней панели (белый с лёгкой тенью)
        with self.canvas.before:
            Color(1, 1, 1, 1)  # Белый фон
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

            # Лёгкая тень снизу
            Color(0, 0, 0, 0.05)
            self.shadow = Rectangle(
                pos=(self.x, self.y - dp(2)),
                size=(self.width, dp(2))
            )

        self.bind(pos=self.update_rect, size=self.update_rect)

        # Контейнер для вкладок (горизонтальный скролл если не помещаются)
        scroll_view = ScrollView(
            size_hint=(1, 1),
            bar_width=0,  # Прячем полосу прокрутки
            do_scroll_x=True,
            do_scroll_y=False
        )

        self.tabs_container = BoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            height=dp(60),
            spacing=0
        )
        self.tabs_container.bind(minimum_width=self.tabs_container.setter('width'))

        # Создаём вкладки
        self.tab_widgets = []
        for tab_data in self.tabs:
            tab = NavTab(
                title=tab_data['title'],
                active=(tab_data['screen'] == 'home'),  # Главная активна по умолчанию
                size_hint_y=1
            )
            tab.bind(on_press=lambda x, screen=tab_data['screen']: self.switch_to(screen))
            self.tabs_container.add_widget(tab)
            self.tab_widgets.append(tab)

        # Центрируем вкладки, если они не занимают всю ширину
        self.center_tabs()

        scroll_view.add_widget(self.tabs_container)
        self.add_widget(scroll_view)

        # Привязываем изменение размера окна
        Window.bind(on_resize=self.on_window_resize)

        logger.info(f'Верхняя навигация создана с {len(self.tabs)} разделами')

    def update_rect(self, *args):
        """Обновляет фон и тень"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.shadow.pos = (self.x, self.y - dp(2))
        self.shadow.size = (self.width, dp(2))

    def on_window_resize(self, instance, width, height):
        """Вызывается при изменении размера окна"""
        self.center_tabs()

    def center_tabs(self):
        """Центрирует вкладки, если они не занимают всю ширину"""
        # Вычисляем общую ширину всех вкладок
        total_width = 0
        for tab in self.tab_widgets:
            # Устанавливаем ширину вкладки на основе текста
            from kivy.core.text import Label as CoreLabel
            label = CoreLabel(text=tab.title, font_size=theme.FONT_SIZE_BODY)
            label.refresh()
            text_width = label.texture.size[0]
            tab.width = text_width + dp(30)  # Добавляем отступы
            total_width += tab.width

        # Если общая ширина меньше ширины окна, добавляем отступы для центрирования
        if total_width < self.width:
            padding = (self.width - total_width) / 2
            self.tabs_container.padding = [padding, 0, padding, 0]
        else:
            self.tabs_container.padding = [dp(10), 0, dp(10), 0]

    def switch_to(self, screen_name):
        """Переключает экран"""
        if not self.sm or self.sm.current == screen_name:
            return

        logger.debug(f'Верхняя навигация: переключение на {screen_name}')

        # Обновляем активные вкладки
        for tab, tab_data in zip(self.tab_widgets, self.tabs):
            tab.active = (tab_data['screen'] == screen_name)

        # Анимация перехода
        current_index = next(i for i, d in enumerate(self.tabs) if d['screen'] == self.sm.current)
        new_index = next(i for i, d in enumerate(self.tabs) if d['screen'] == screen_name)
        self.sm.transition.direction = 'left' if new_index > current_index else 'right'

        self.sm.current = screen_name

    def update_active_from_screen(self, screen_name):
        """Обновляет активную вкладку при смене экрана из другого места"""
        for tab, tab_data in zip(self.tab_widgets, self.tabs):
            tab.active = (tab_data['screen'] == screen_name)