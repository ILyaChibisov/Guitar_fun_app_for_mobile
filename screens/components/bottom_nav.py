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
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
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
    """Элемент нижней навигации с возможностью индивидуальной настройки"""

    icon_asset = StringProperty('')
    text = StringProperty('')
    active = BooleanProperty(False)

    # ===== ПАРАМЕТРЫ ДЛЯ ИНДИВИДУАЛЬНОЙ НАСТРОЙКИ =====
    icon_size = NumericProperty(0.75)  # Размер иконки (0.4-0.9)
    icon_offset_x = NumericProperty(0)  # Смещение иконки по X
    icon_offset_y = NumericProperty(0)  # Смещение иконки по Y
    text_offset_y = NumericProperty(0)  # Смещение текста по Y
    icon_container_height = NumericProperty(0.7)  # Высота контейнера иконки
    text_size = NumericProperty(7)  # Размер шрифта
    spacing_value = NumericProperty(0)  # Расстояние иконка-текст
    top_padding = NumericProperty(0)  # Верхний отступ

    # =================================================

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)

        # Применяем настройки
        self.spacing = dp(self.spacing_value)
        self.padding = [0, dp(self.top_padding), 0, 0]

        # Контейнер для иконки
        self.icon_container = MDBoxLayout(
            size_hint=(1, self.icon_container_height),
            orientation='vertical'
        )

        self.custom_image = None
        self._load_icon()

        # Текст
        self.text_label = Label(
            text=self.text,
            font_size=sp(self.text_size),
            size_hint=(1, 1 - self.icon_container_height),
            halign='center',
            valign='center',
            color=theme.TEXT_SECONDARY,
            bold=False,
            markup=False
        )
        self.text_label.bind(size=self._update_text_size)

        self.add_widget(self.icon_container)
        self.add_widget(self.text_label)

        # Привязываем изменения параметров к обновлению
        self.bind(icon_size=self._update_icon_size)
        self.bind(icon_offset_x=self._update_icon_position)
        self.bind(icon_offset_y=self._update_icon_position)
        self.bind(text_offset_y=self._apply_text_offset)
        self.bind(icon_container_height=self._update_container_height)
        self.bind(text_size=self._update_text_size_direct)
        self.bind(spacing_value=self._update_spacing)
        self.bind(top_padding=self._update_padding)

        self.update_state(None, self.active)
        self.bind(active=self.update_state)
        self.bind(icon_asset=self._on_icon_change)

    def _update_icon_size(self, *args):
        """Обновляет размер иконки при изменении icon_size"""
        if self.custom_image and hasattr(self.custom_image, 'size_hint'):
            self.custom_image.size_hint = (self.icon_size, self.icon_size)

    def _update_icon_position(self, *args):
        """Обновляет позицию иконки при изменении смещения"""
        if self.custom_image and hasattr(self.custom_image, 'pos_hint'):
            offset_x = self.icon_offset_x / 100
            offset_y = self.icon_offset_y / 100
            self.custom_image.pos_hint = {
                'center_x': 0.5 + offset_x,
                'center_y': 0.5 + offset_y
            }

    def _update_container_height(self, *args):
        """Обновляет высоту контейнера иконки"""
        self.icon_container.size_hint = (1, self.icon_container_height)
        self.text_label.size_hint = (1, 1 - self.icon_container_height)

    def _update_text_size_direct(self, *args):
        """Обновляет размер шрифта"""
        self.text_label.font_size = sp(self.text_size)

    def _update_spacing(self, *args):
        """Обновляет расстояние между иконкой и текстом"""
        self.spacing = dp(self.spacing_value)

    def _update_padding(self, *args):
        """Обновляет верхний отступ"""
        self.padding = [0, dp(self.top_padding), 0, 0]

    def _apply_text_offset(self, *args):
        """Применяет смещение к тексту"""
        offset = self.text_offset_y / 100
        self.text_label.pos_hint = {'y': 0 + offset}
        self.text_label.bind(size=self._update_text_size)

    def _update_text_size(self, instance, value):
        """Обновляет размер текстовой области"""
        instance.text_size = (instance.width, instance.height)

    def _reload_icon(self, *args):
        """Перезагружает иконку"""
        self._load_icon()

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

                    # Применяем размер и смещение
                    size = self.icon_size
                    offset_x = self.icon_offset_x / 100
                    offset_y = self.icon_offset_y / 100

                    self.custom_image = Image(
                        texture=texture,
                        size_hint=(size, size),
                        pos_hint={'center_x': 0.5 + offset_x, 'center_y': 0.5 + offset_y},
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    self.icon_container.add_widget(self.custom_image)
                    return
            except Exception as e:
                logger.error(f'Ошибка загрузки иконки {self.icon_asset}: {e}')

        # Заглушка
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
        """Обновляет внешний вид"""
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

        # ===== НАСТРОЙКИ ПАНЕЛИ =====
        self.height = dp(56)  # Высота панели
        self.padding = [dp(2), dp(1), dp(2), dp(2)]  # Отступы
        self.spacing = dp(0)  # Расстояние между кнопками
        # =============================

        # with self.canvas.before:
        #     Color(1, 1, 1, 1)
        #     self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        #
        # self.bind(pos=self.update_rect, size=self.update_rect)

        # ===== КОНФИГУРАЦИЯ КНОПОК =====
        self.nav_items = [
            {
                'icon_asset': 'songs_png',
                'text': 'Песни',
                'screen': 'songs',
                'icon_size': 0.9,
                'icon_offset_x': 0,
                'icon_offset_y': 0,
                'text_offset_y': 0,
                'icon_container_height': 0.9,
                'text_size': 9,
                'spacing_value': 2,
                'top_padding': 0
            },
            {
                'icon_asset': 'chords_png',
                'text': 'Аккорды',
                'screen': 'chords',
                'icon_size': 0.9,
                'icon_offset_x': 0,
                'icon_offset_y': 0,
                'text_offset_y': 0,
                'icon_container_height': 0.9,
                'text_size': 9,
                'spacing_value': 2,
                'top_padding': 0
            },
            {
                'icon_asset': 'tuner_png',
                'text': 'Тюнер',
                'screen': 'tuner',
                'icon_size': 0.9,
                'icon_offset_x': 0,
                'icon_offset_y': 0,
                'text_offset_y': 0,
                'icon_container_height': 0.9,
                'text_size': 9,
                'spacing_value': 2,
                'top_padding': 0
            },
            {
                'icon_asset': 'dictionary_png',
                'text': 'Словарь',
                'screen': 'dictionary',
                'icon_size': 0.9,
                'icon_offset_x': 0,
                'icon_offset_y': 0,
                'text_offset_y': 0,
                'icon_container_height': 0.9,
                'text_size': 9,
                'spacing_value': 2,
                'top_padding': 0
            },
            {
                'icon_asset': 'favorites_png',
                'text': 'Избранное',
                'screen': 'favorites',
                'icon_size': 0.9,
                'icon_offset_x': 0,
                'icon_offset_y': 0,
                'text_offset_y': 0,
                'icon_container_height': 0.9,
                'text_size': 9,
                'spacing_value': 2,
                'top_padding': 0
            }
        ]

        self.items = []

        for item_data in self.nav_items:
            item = NavItem(
                icon_asset=item_data['icon_asset'],
                text=item_data['text'],
                icon_size=item_data.get('icon_size', 0.75),
                icon_offset_x=item_data.get('icon_offset_x', 0),
                icon_offset_y=item_data.get('icon_offset_y', 0),
                text_offset_y=item_data.get('text_offset_y', 0),
                icon_container_height=item_data.get('icon_container_height', 0.7),
                text_size=item_data.get('text_size', 7),
                spacing_value=item_data.get('spacing_value', 0),
                top_padding=item_data.get('top_padding', 0)
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