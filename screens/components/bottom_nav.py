# screens/components/bottom_nav.py
"""
Современная нижняя навигация
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from io import BytesIO

from config.theme import theme
from config.logger_config import get_logger
from config.bottom_nav_config import BottomNavConfig
from utils.kivy_imports import MDBoxLayout

logger = get_logger('UI')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    logger.warning("Модуль data не найден")


class NavItem(ButtonBehavior, BoxLayout):
    """Элемент нижней навигации"""

    icon_asset = StringProperty('')
    text = StringProperty('')
    active = BooleanProperty(False)

    # Делаем параметры свойствами Kivy для автоматического обновления
    icon_size = NumericProperty(BottomNavConfig.ICON_SIZE)
    icon_height = NumericProperty(BottomNavConfig.ICON_CONTAINER_HEIGHT)
    font_size = NumericProperty(BottomNavConfig.FONT_SIZE)
    spacing_val = NumericProperty(BottomNavConfig.SPACING)
    top_padding = NumericProperty(BottomNavConfig.TOP_PADDING)

    def __init__(self, icon_asset, text, **kwargs):
        super().__init__(**kwargs)
        self.icon_asset = icon_asset
        self.text = text

        self.orientation = 'vertical'
        self.size_hint = (1, 1)

        # Применяем начальные настройки
        self.spacing = dp(self.spacing_val)
        self.padding = [0, dp(self.top_padding), 0, 0]

        # Создаём контейнер
        self.icon_container = MDBoxLayout(
            size_hint=(1, self.icon_height),
            orientation='vertical'
        )

        self.custom_image = None
        self._load_icon()

        # Текст
        self.text_label = Label(
            text=self.text,
            font_size=sp(self.font_size),
            size_hint=(1, 1 - self.icon_height),
            color=theme.TEXT_SECONDARY,
            bold=False,
            markup=False,
            halign='center',
            valign='top'
        )

        self.add_widget(self.icon_container)
        self.add_widget(self.text_label)

        # Привязываем обновление при изменении свойств
        self.bind(icon_size=self._reload_icon)
        self.bind(icon_height=self._update_container)
        self.bind(font_size=self._update_font)
        self.bind(spacing_val=self._update_spacing)
        self.bind(top_padding=self._update_padding)

        self.update_state(None, self.active)
        self.bind(active=self.update_state)
        self.bind(icon_asset=self._reload_icon)

    def _reload_icon(self, *args):
        """Перезагружает иконку с новым размером"""
        self._load_icon()

    def _update_container(self, *args):
        """Обновляет контейнер"""
        self.icon_container.size_hint = (1, self.icon_height)
        self.text_label.size_hint = (1, 1 - self.icon_height)
        self._reload_icon()

    def _update_font(self, *args):
        """Обновляет шрифт"""
        self.text_label.font_size = sp(self.font_size)

    def _update_spacing(self, *args):
        """Обновляет расстояние"""
        self.spacing = dp(self.spacing_val)

    def _update_padding(self, *args):
        """Обновляет отступ"""
        self.padding = [0, dp(self.top_padding), 0, 0]

    def _load_icon(self):
        """Загружает иконку с текущим размером"""
        self.icon_container.clear_widgets()

        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    core_img = CoreImage(BytesIO(icon_data), ext="png")

                    self.custom_image = Image(
                        texture=core_img.texture,
                        size_hint=(self.icon_size, self.icon_size),
                        pos_hint={'center_x': 0.5, 'center_y': 0.5},
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    self.icon_container.add_widget(self.custom_image)
                    return
            except Exception as e:
                logger.error(f'Ошибка загрузки иконки: {e}')

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

    def update_state(self, instance, value):
        """Обновляет внешний вид"""
        if value:
            self.text_label.color = theme.PRIMARY
            self.text_label.bold = True
        else:
            self.text_label.color = theme.TEXT_SECONDARY
            self.text_label.bold = False

    def on_press(self):
        anim = Animation(opacity=0.7, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)


class BottomNav(BoxLayout):
    """Нижняя панель навигации"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.size_hint = (1, None)

        # Берём настройки из конфига
        self.height = dp(BottomNavConfig.PANEL_HEIGHT)
        self.padding = [dp(x) for x in BottomNavConfig.PANEL_PADDING]
        self.spacing = dp(BottomNavConfig.PANEL_SPACING)
        self.md_bg_color = BottomNavConfig.PANEL_BG_COLOR

        # Меню
        self.nav_items = [
            ('songs_png', 'Песни', 'songs'),
            ('chords_png', 'Аккорды', 'chords'),
            ('tuner_png', 'Тюнер', 'tuner'),
            ('dictionary_png', 'Словарь', 'dictionary'),
            ('favorites_png', 'Избранное', 'favorites')
        ]

        self.items = []

        for icon, text, screen in self.nav_items:
            item = NavItem(icon, text)
            item.active = (screen == 'songs')
            item.bind(on_press=lambda x, s=screen: self.switch_to(s))
            self.add_widget(item)
            self.items.append(item)

        if hasattr(screen_manager, 'add_observer'):
            screen_manager.add_observer(self.on_screen_changed)

        logger.info('Нижняя навигация создана')

    def on_screen_changed(self, screen_name):
        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item.active = (screen == screen_name)

    def switch_to(self, screen_name):
        if not self.sm or self.sm.current == screen_name:
            return

        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item.active = (screen == screen_name)

        try:
            current_index = next(i for i, (_, _, s) in enumerate(self.nav_items) if s == self.sm.current)
            new_index = next(i for i, (_, _, s) in enumerate(self.nav_items) if s == screen_name)
            direction = 'left' if new_index > current_index else 'right'
        except StopIteration:
            direction = 'left'

        self.sm.transition.direction = direction
        self.sm.current = screen_name

    def switch_tab(self, screen_name):
        self.switch_to(screen_name)