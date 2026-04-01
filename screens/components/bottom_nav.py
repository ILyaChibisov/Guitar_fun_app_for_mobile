# screens/components/bottom_nav.py
"""
Современная нижняя навигация (как в Instagram)
Активный пункт - мягкий зелёный (RGB: 118,179,182)
Синхронизируется с верхней навигацией
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle

from config.theme import theme
from config.logger_config import get_logger
from utils.kivy_imports import MDIconButton, MDBoxLayout

logger = get_logger('UI')


class NavItem(ButtonBehavior, BoxLayout):
    """Элемент нижней навигации с иконкой и текстом"""

    icon = StringProperty('')
    text = StringProperty('')
    active = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(2)
        self.padding = [0, dp(5), 0, 0]

        # Иконка (эмодзи)
        self.icon_label = Label(
            text=self.icon,
            font_size=sp(24),
            size_hint=(1, 0.6),
            color=theme.TEXT_SECONDARY,
            markup=False,
            halign='center',
            valign='bottom'
        )

        # Текст под иконкой
        self.text_label = Label(
            text=self.text,
            font_size=sp(11),
            size_hint=(1, 0.4),
            color=theme.TEXT_SECONDARY,
            bold=False,
            markup=False,
            halign='center',
            valign='top'
        )

        self.add_widget(self.icon_label)
        self.add_widget(self.text_label)

        # Применяем активное состояние при создании
        self.update_state(None, self.active)

        # Биндим изменение active
        self.bind(active=self.update_state)
        logger.debug(f'Создан элемент нижней навигации: {self.text}')

    def update_state(self, instance, value):
        """Обновляет внешний вид - активный становится мягким зелёным"""
        if value:
            # Активное состояние - мягкий зелёный (с картинки)
            self.icon_label.color = theme.PRIMARY  # #76B3B6
            self.text_label.color = theme.PRIMARY  # #76B3B6
            self.text_label.bold = True
        else:
            # Неактивное состояние - серый
            self.icon_label.color = theme.TEXT_SECONDARY
            self.text_label.color = theme.TEXT_SECONDARY
            self.text_label.bold = False

    def on_press(self):
        """Анимация нажатия"""
        anim = Animation(opacity=0.7, duration=0.1)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)


class BottomNav(BoxLayout):
    """Нижняя панель навигации"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.size_hint = (1, None)
        self.height = dp(70)
        self.padding = [theme.PADDING, dp(5), theme.PADDING, dp(5)]
        self.spacing = dp(5)

        # Белый фон для нижней панели
        with self.canvas.before:
            Color(1, 1, 1, 1)  # Белый фон
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

            # Верхняя тонкая линия-разделитель
            Color(0, 0, 0, 0.05)  # Очень светлая линия
            self.top_line = Rectangle(
                pos=(self.x, self.y + self.height - dp(1)),
                size=(self.width, dp(1))
            )

        self.bind(pos=self.update_rect, size=self.update_rect)

        # Элементы навигации (без тюнера, он в FAB)
        self.nav_items = [
            {'icon': '🏠', 'text': 'Главная', 'screen': 'home'},
            {'icon': '🎵', 'text': 'Песни', 'screen': 'songs'},
            {'icon': '🎸', 'text': 'Аккорды', 'screen': 'chords'},
            {'icon': '📚', 'text': 'Словарь', 'screen': 'dictionary'},
            {'icon': '❤️', 'text': 'Избранное', 'screen': 'favorites'}
        ]

        self.items = []

        # Создаём элементы
        for item_data in self.nav_items:
            item = NavItem(
                icon=item_data['icon'],
                text=item_data['text']
            )
            # Устанавливаем активное состояние (Главная активна по умолчанию)
            item.active = (item_data['screen'] == 'home')
            # Привязываем обработчик нажатия
            item.bind(on_press=lambda x, screen=item_data['screen']: self.switch_to(screen))
            self.add_widget(item)
            self.items.append(item)

        # Подписываемся на изменения экрана, если менеджер поддерживает
        if hasattr(screen_manager, 'add_observer'):
            screen_manager.add_observer(self.on_screen_changed)
            logger.debug('BottomNav подписан на изменения экрана')

        logger.info('Нижняя навигация создана (активный пункт - мягкий зелёный #76B3B6)')

    def update_rect(self, *args):
        """Обновляет фон и разделитель при изменении размера"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.top_line.pos = (self.x, self.y + self.height - dp(1))
        self.top_line.size = (self.width, dp(1))

    def on_screen_changed(self, screen_name):
        """Вызывается при смене экрана из другого места (например, из верхней навигации)"""
        # Обновляем активные элементы
        for item, item_data in zip(self.items, self.nav_items):
            item.active = (item_data['screen'] == screen_name)

        logger.debug(f'BottomNav синхронизирован с экраном: {screen_name}')

    def switch_to(self, screen_name):
        """Переключает экран"""
        if not self.sm or self.sm.current == screen_name:
            return

        logger.debug(f'BottomNav: переключение на {screen_name}')

        # Обновляем активные элементы
        for item, item_data in zip(self.items, self.nav_items):
            item.active = (item_data['screen'] == screen_name)

        # Определяем направление анимации для красивого перехода
        current_index = next(i for i, d in enumerate(self.nav_items) if d['screen'] == self.sm.current)
        new_index = next(i for i, d in enumerate(self.nav_items) if d['screen'] == screen_name)

        # Анимация перехода
        if new_index > current_index:
            self.sm.transition.direction = 'left'
        elif new_index < current_index:
            self.sm.transition.direction = 'right'
        else:
            self.sm.transition.direction = 'left'  # По умолчанию

        # Переключаем экран
        self.sm.current = screen_name

    def switch_tab(self, screen_name):
        """Метод для совместимости с main.py"""
        self.switch_to(screen_name)