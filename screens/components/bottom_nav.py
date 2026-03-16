# screens/components/bottom_nav.py
"""
Современная нижняя навигация
Активный пункт - мягкий зелёный (RGB: 118,179,182)
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('UI')


class NavItem(ButtonBehavior, BoxLayout):
    """Элемент навигации с иконкой и текстом"""

    icon = StringProperty('')
    text = StringProperty('')
    active = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(2)
        self.padding = [0, dp(5), 0, 0]

        # Иконка
        self.icon_label = Label(
            text=self.icon,
            font_size=sp(24),
            size_hint=(1, 0.6),
            color=theme.TEXT_SECONDARY
        )

        # Текст
        self.text_label = Label(
            text=self.text,
            font_size=sp(11),
            size_hint=(1, 0.4),
            color=theme.TEXT_SECONDARY,
            bold=False
        )

        self.add_widget(self.icon_label)
        self.add_widget(self.text_label)

        self.update_state(None, self.active)
        self.bind(active=self.update_state)
        logger.debug(f'Создан элемент навигации: {self.text}')

    def update_state(self, instance, value):
        """Обновляет внешний вид - активный становится мягким зелёным"""
        if value:
            # Активное состояние - мягкий зелёный
            self.icon_label.color = theme.PRIMARY  # #76B3B6
            self.text_label.color = theme.PRIMARY  # #76B3B6
            self.text_label.bold = True
        else:
            # Неактивное состояние - серый
            self.icon_label.color = theme.TEXT_SECONDARY
            self.text_label.color = theme.TEXT_SECONDARY
            self.text_label.bold = False

    def on_press(self):
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
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        # Элементы навигации
        self.nav_items = [
            {'icon': '🏠', 'text': 'Главная', 'screen': 'home'},
            {'icon': '🎵', 'text': 'Песни', 'screen': 'songs'},
            {'icon': '🎸', 'text': 'Аккорды', 'screen': 'chords'},
            {'icon': '📚', 'text': 'Словарь', 'screen': 'dictionary'},
            {'icon': '❤️', 'text': 'Избранное', 'screen': 'favorites'}
        ]

        self.items = []

        for item_data in self.nav_items:
            item = NavItem(
                icon=item_data['icon'],
                text=item_data['text']
            )
            item.active = (item_data['screen'] == 'home')
            item.bind(on_press=lambda x, screen=item_data['screen']: self.switch_to(screen))
            self.add_widget(item)
            self.items.append(item)

        logger.info('Нижняя навигация создана (активный пункт - мягкий зелёный #76B3B6)')

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def switch_to(self, screen_name):
        if not self.sm or self.sm.current == screen_name:
            return

        logger.debug(f'Навигация: переключение на {screen_name}')

        for item, item_data in zip(self.items, self.nav_items):
            item.active = (item_data['screen'] == screen_name)

        # Анимация перехода
        if self.sm.current == 'home' and screen_name != 'home':
            self.sm.transition.direction = 'left'
        elif self.sm.current != 'home' and screen_name == 'home':
            self.sm.transition.direction = 'right'
        else:
            current_index = next(i for i, d in enumerate(self.nav_items) if d['screen'] == self.sm.current)
            new_index = next(i for i, d in enumerate(self.nav_items) if d['screen'] == screen_name)
            self.sm.transition.direction = 'left' if new_index > current_index else 'right'

        self.sm.current = screen_name