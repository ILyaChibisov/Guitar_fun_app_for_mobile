# screens/components/bottom_nav.py
"""
Нижняя навигация - полностью адаптивная (Material Design стиль)
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.core.image import Image as CoreImage
from kivy.utils import platform
from kivy.core.window import Window
from io import BytesIO
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from config.bottom_nav_config import BottomNavConfig
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from utils.kivy_imports import MDBoxLayout

logger = get_logger('UI')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    logger.warning("Модуль data не найден")


class NavItem(ButtonBehavior, BoxLayout):
    """Элемент нижней навигации - адаптивный"""

    icon_asset = StringProperty('')
    text = StringProperty('')
    active = BooleanProperty(False)

    def __init__(self, icon_asset, text, screen_name, **kwargs):
        super().__init__(**kwargs)
        self.icon_asset = icon_asset
        self.text = text
        self.screen_name = screen_name
        self.config = BottomNavConfig.get_button_config(screen_name)

        self.orientation = 'vertical'
        self.size_hint = (1, 1)  # растягивается на всю высоту панели
        self.spacing = dp(2)

        # Контейнер иконки (процент от высоты кнопки)
        icon_height_ratio = self.config.get('icon_height', 0.68)
        self.icon_container = MDBoxLayout(
            size_hint=(1, icon_height_ratio),
            orientation='vertical'
        )

        # Иконка
        self.icon_image = None
        self._load_icon()

        # Текст
        font_size = self.config.get('font_size', sp(11))
        self.text_label = Label(
            text=self.config.get('text', text),
            font_size=font_size,
            size_hint=(1, 1 - icon_height_ratio),
            color=theme.TEXT_SECONDARY,
            bold=False,
            halign='center',
            valign='top'
        )
        self.text_label.bind(size=self.text_label.setter('text_size'))

        self.add_widget(self.icon_container)
        self.add_widget(self.text_label)

        # Обновляем состояние
        self.update_state(None, self.active)
        self.bind(active=self.update_state)
        self.bind(icon_asset=self._reload_icon)

    def _reload_icon(self, *args):
        self._load_icon()

    def _load_icon(self):
        """Загружает иконку с адаптивным размером"""
        self.icon_container.clear_widgets()

        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    core_img = CoreImage(BytesIO(icon_data), ext="png")
                    # Иконка центрируется и занимает 75% контейнера
                    self.icon_image = Image(
                        texture=core_img.texture,
                        size_hint=(0.75, 0.75),
                        pos_hint={'center_x': 0.5, 'center_y': 0.5},
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    self.icon_container.add_widget(self.icon_image)
                    return
            except Exception as e:
                logger.error(f'Ошибка загрузки иконки {self.icon_asset}: {e}')

        # Заглушка
        self.icon_image = Label(
            text="?",
            font_size=sp(18),
            size_hint=(1, 1),
            color=theme.TEXT_SECONDARY,
            halign='center',
            valign='center'
        )
        self.icon_container.add_widget(self.icon_image)

    def update_state(self, instance, value):
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
    """Нижняя панель навигации - полностью адаптивная"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.size_hint = (1, None)

        # Получаем адаптивную высоту из конфига
        self.nav_height = layout_config.get_bottom_nav_height()
        nav_bar_height = get_navigation_bar_height()

        # Общая высота = панель + системная навигация
        self.height = self.nav_height + nav_bar_height

        # Паддинги
        self.padding = [dp(8), 0, dp(8), nav_bar_height]
        self.spacing = dp(4)
        self.md_bg_color = [0, 0, 0, 0]

        logger.info(f"BottomNav: высота={self.height}dp, панель={self.nav_height}dp, системная нав={nav_bar_height}dp")

        # Меню
        self.nav_items = [
            ('home_png', 'Главная', 'home'),
            ('songs_png', 'Песни', 'songs'),
            ('chords_png', 'Аккорды', 'chords'),
            ('tuner_png', 'Тюнер', 'tuner'),
            ('favorites_png', 'Избранное', 'favorites')
        ]

        self.items = []
        for icon, text, screen in self.nav_items:
            item = NavItem(icon, text, screen)
            item.active = (screen == 'home')
            item.bind(on_press=lambda x, s=screen: self.switch_to(s))
            self.add_widget(item)
            self.items.append(item)

        if hasattr(screen_manager, 'add_observer'):
            screen_manager.add_observer(self.on_screen_changed)

    def on_screen_changed(self, screen_name):
        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item.active = (screen == screen_name)

    def switch_to(self, screen_name):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

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
        """Алиас для switch_to"""
        self.switch_to(screen_name)

    def reload_config(self):
        """Обновляет конфигурацию панели при изменении размера экрана"""
        self.nav_height = layout_config.get_bottom_nav_height()
        nav_bar_height = get_navigation_bar_height()
        self.height = self.nav_height + nav_bar_height
        self.padding = [dp(8), 0, dp(8), nav_bar_height]

        # Обновляем каждую кнопку
        for item in self.items:
            item._reload_icon()

        logger.info(f"BottomNav обновлена: высота={self.height}dp")