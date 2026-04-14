# screens/components/bottom_nav.py
"""
Современная нижняя навигация
Активный пункт - мягкий зелёный (RGB: 118,179,182)
Иконки ТОЛЬКО из ассетов
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from io import BytesIO

from config.theme import theme
from config.logger_config import get_logger
from utils.kivy_imports import MDIconButton, MDBoxLayout

logger = get_logger('UI')

# Пытаемся импортировать ассеты
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    logger.warning("Модуль data не найден")


class NavItem(ButtonBehavior, BoxLayout):
    """Элемент нижней навигации с иконкой из ассета и текстом"""

    icon_asset = StringProperty('')
    text = StringProperty('')
    active = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(2)
        self.padding = [0, dp(4), 0, 0]

        # Контейнер для иконки
        self.icon_container = MDBoxLayout(
            size_hint=(1, 0.6),
            orientation='vertical'
        )

        self.custom_image = None
        self._load_icon()

        # Текст под иконкой
        self.text_label = Label(
            text=self.text,
            font_size=sp(9),
            size_hint=(1, 0.4),
            color=theme.TEXT_SECONDARY,
            bold=False,
            markup=False,
            halign='center',
            valign='top'
        )

        self.add_widget(self.icon_container)
        self.add_widget(self.text_label)

        self.update_state(None, self.active)
        self.bind(active=self.update_state)
        self.bind(icon_asset=self._on_icon_change)

        logger.debug(f'Создан элемент нижней навигации: {self.text}')

    def _load_icon(self):
        """Загружает иконку из ассета"""
        self.icon_container.clear_widgets()
        self.custom_image = None

        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    core_img = CoreImage(BytesIO(icon_data), ext="png")
                    texture = core_img.texture
                    self.custom_image = Image(
                        texture=texture,
                        size_hint=(0.65, 0.65),
                        pos_hint={'center_x': 0.5, 'center_y': 0.5},
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    self.icon_container.add_widget(self.custom_image)
                    return
            except Exception as e:
                logger.error(f'Ошибка загрузки иконки {self.icon_asset}: {e}')

        # Если иконка не загрузилась - показываем заглушку
        self.custom_image = Label(
            text="?",
            font_size=sp(18),
            size_hint=(1, 1),
            color=theme.TEXT_SECONDARY,
            halign='center',
            valign='center'
        )
        self.icon_container.add_widget(self.custom_image)

    def _on_icon_change(self, instance, value):
        self._load_icon()

    def update_state(self, instance, value):
        """Обновляет внешний вид - активный становится мягким зелёным"""
        if value:
            self.text_label.color = theme.PRIMARY
            self.text_label.bold = True
        else:
            self.text_label.color = theme.TEXT_SECONDARY
            self.text_label.bold = False

    def on_press(self):
        """Анимация нажатия"""
        anim = Animation(opacity=0.7, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)


class BottomNav(BoxLayout):
    """Нижняя панель навигации"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.size_hint = (1, None)
        self.height = dp(58)
        self.padding = [dp(6), dp(3), dp(6), dp(3)]
        self.spacing = dp(2)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        # НИЖНЕЕ МЕНЮ: ТОЛЬКО ИКОНКИ ИЗ АССЕТОВ
        self.nav_items = [
            {'icon_asset': 'songs_png', 'text': 'Песни', 'screen': 'songs'},
            {'icon_asset': 'chords_png', 'text': 'Аккорды', 'screen': 'chords'},
            {'icon_asset': 'tuner_png', 'text': 'Тюнер', 'screen': 'tuner'},
            {'icon_asset': 'dictionary_png', 'text': 'Словарь', 'screen': 'dictionary'},
            {'icon_asset': 'favorites_png', 'text': 'Избранное', 'screen': 'favorites'}
        ]

        self.items = []

        for item_data in self.nav_items:
            item = NavItem(
                icon_asset=item_data['icon_asset'],
                text=item_data['text']
            )
            item.active = (item_data['screen'] == 'songs')
            item.bind(on_press=lambda x, screen=item_data['screen']: self.switch_to(screen))
            self.add_widget(item)
            self.items.append(item)

        if hasattr(screen_manager, 'add_observer'):
            screen_manager.add_observer(self.on_screen_changed)

        logger.info('Нижняя навигация создана (иконки из ассетов)')

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def on_screen_changed(self, screen_name):
        for item, item_data in zip(self.items, self.nav_items):
            item.active = (item_data['screen'] == screen_name)

    def switch_to(self, screen_name):
        if not self.sm or self.sm.current == screen_name:
            return

        for item, item_data in zip(self.items, self.nav_items):
            item.active = (item_data['screen'] == screen_name)

        try:
            current_index = next(i for i, d in enumerate(self.nav_items) if d['screen'] == self.sm.current)
            new_index = next(i for i, d in enumerate(self.nav_items) if d['screen'] == screen_name)
            direction = 'left' if new_index > current_index else 'right'
        except StopIteration:
            direction = 'left'

        self.sm.transition.direction = direction
        self.sm.current = screen_name

    def switch_tab(self, screen_name):
        self.switch_to(screen_name)