# screens/components/bottom_nav.py
"""
Современная нижняя навигация (как в Instagram)
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

        # Иконка
        self.icon_label = Label(
            text=self.icon,
            font_size=sp(24),
            size_hint=(1, 0.6),
            color=theme.TEXT_SECONDARY,
            markup=True
        )

        # Текст
        self.text_label = Label(
            text=self.text,
            font_size=sp(12),
            size_hint=(1, 0.4),
            color=theme.TEXT_SECONDARY,
            bold=False,
            markup=True
        )

        self.add_widget(self.icon_label)
        self.add_widget(self.text_label)

        # Применяем активное состояние при создании
        self.update_state(None, self.active)

        # Биндим изменение active
        self.bind(active=self.update_state)
        logger.debug(f'Создан элемент навигации: {self.text}')

    def update_state(self, instance, value):
        """Обновляет внешний вид при активации"""
        if value:
            self.icon_label.color = theme.PRIMARY
            self.text_label.color = theme.PRIMARY
            self.text_label.bold = True
        else:
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
        self.padding = [theme.PADDING, theme.PADDING_SMALL]
        self.spacing = dp(10)

        # Элементы навигации
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
            # Устанавливаем активное состояние
            item.active = (item_data['screen'] == 'home')
            # Привязываем обработчик нажатия
            item.bind(on_press=lambda x, screen=item_data['screen']: self.switch_to(screen))
            self.add_widget(item)
            self.items.append(item)

        logger.info('Нижняя навигация создана')

    def switch_to(self, screen_name):
        """Переключает экран"""
        if not self.sm or self.sm.current == screen_name:
            return

        logger.debug(f'Навигация: переключение на {screen_name}')

        # Обновляем активные элементы
        for item, item_data in zip(self.items, self.nav_items):
            item.active = (item_data['screen'] == screen_name)

        # Переключаем экран
        self.sm.current = screen_name