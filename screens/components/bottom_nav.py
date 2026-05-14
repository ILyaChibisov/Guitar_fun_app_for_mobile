# screens/components/bottom_nav.py
"""
Нижняя панель навигации - индивидуальные настройки для каждой кнопки
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
from config.system_bars import get_navigation_bar_height, get_screen_density
from utils.kivy_imports import MDBoxLayout

logger = get_logger('BottomNav')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    logger.warning("Модуль data не найден")


class NavItem(ButtonBehavior, BoxLayout):
    """Элемент нижней навигации - индивидуальные настройки"""

    icon_asset = StringProperty('')
    text = StringProperty('')
    active = BooleanProperty(False)

    def __init__(self, icon_asset, text, screen_name, **kwargs):
        super().__init__(**kwargs)
        self.icon_asset = icon_asset
        self.text = text
        self.screen_name = screen_name

        self.orientation = 'vertical'
        self.size_hint = (1, 1)

        if platform == 'android':
            # ============ ИНДИВИДУАЛЬНЫЕ НАСТРОЙКИ ДЛЯ КАЖДОЙ КНОПКИ ============

            # Общие настройки
            self.spacing = dp(8)
            self.padding = [0, dp(8), 0, dp(8)]
            self.icon_container_ratio = 0.70
            self.text_ratio = 0.30

            # ИНДИВИДУАЛЬНЫЕ РАЗМЕРЫ ИКОНОК И ШРИФТОВ
            if screen_name == 'home':
                self.icon_size = 0.92  # Главная
                self.font_size = sp(13)
            elif screen_name == 'songs':
                self.icon_size = 0.92  # Песни
                self.font_size = sp(13)
            elif screen_name == 'chords':
                self.icon_size = 0.92  # Аккорды
                self.font_size = sp(13)
            elif screen_name == 'tuner':
                self.icon_size = 0.92  # Тюнер
                self.font_size = sp(13)
            elif screen_name == 'favorites':
                self.icon_size = 0.75  # Избранное (меньше на ~18%)
                self.font_size = sp(10)  # Шрифт тоже меньше
            else:
                self.icon_size = 0.92
                self.font_size = sp(13)
        else:
            # Windows
            self.spacing = dp(4)
            self.padding = [0, dp(4), 0, dp(6)]
            self.icon_container_ratio = 0.72
            self.text_ratio = 0.28

            if screen_name == 'favorites':
                self.icon_size = 0.80
                self.font_size = sp(13)
            else:
                self.icon_size = 0.88
                self.font_size = sp(15)

        # Контейнер иконки
        self.icon_container = MDBoxLayout(
            size_hint=(1, self.icon_container_ratio),
            orientation='vertical'
        )

        self.custom_image = None
        self._load_icon()

        # Текст
        self.text_label = Label(
            text=self.text,
            font_size=self.font_size,
            size_hint=(1, None),
            height=dp(24),
            color=theme.TEXT_SECONDARY,
            bold=False,
            halign='center',
            valign='middle'
        )
        self.text_label.bind(size=self.text_label.setter('text_size'))

        self.add_widget(self.icon_container)
        self.add_widget(self.text_label)

        self.update_state(None, self.active)
        self.bind(active=self.update_state)
        self.bind(icon_asset=self._reload_icon)

        logger.info(f"[NavItem] {screen_name}: icon_size={self.icon_size}, font={self.font_size}")

    def _reload_icon(self, *args):
        self._load_icon()

    def _load_icon(self):
        self.icon_container.clear_widgets()

        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    core_img = CoreImage(BytesIO(icon_data), ext="png")

                    # Используем индивидуальный размер иконки
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
                logger.error('Ошибка загрузки иконки: ' + str(e))

        fallback_font = sp(24) if platform == 'android' else sp(26)
        self.custom_image = Label(
            text="?",
            font_size=fallback_font,
            size_hint=(1, 1),
            color=theme.TEXT_SECONDARY,
            halign='center',
            valign='center'
        )
        self.icon_container.add_widget(self.custom_image)

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
    """Нижняя панель навигации"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.size_hint = (1, None)
        self.pos_hint = {'y': 0}

        nav_bar_height = get_navigation_bar_height()

        if platform == 'android':
            self.nav_height = dp(80)
            bottom_padding = 0
            button_spacing = dp(6)
        else:
            self.nav_height = dp(72)
            bottom_padding = nav_bar_height + dp(8)
            button_spacing = dp(4)

        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height

        self.padding = [dp(8), 0, dp(8), bottom_padding]
        self.spacing = button_spacing
        self.md_bg_color = [0, 0, 0, 0]

        logger.info("=" * 70)
        logger.info(f"📱 BOTTOM NAV - {platform.upper()}")
        logger.info(f"📱 Высота панели: {self.nav_height}dp")
        logger.info(f"📱 Системная навигация: {nav_bar_height:.1f}dp")
        logger.info(f"📱 Индивидуальные размеры иконок:")
        logger.info(f"   - Главная: 0.92")
        logger.info(f"   - Песни: 0.92")
        logger.info(f"   - Аккорды: 0.92")
        logger.info(f"   - Тюнер: 0.92")
        logger.info(f"   - Избранное: 0.75 (на 18% меньше)")
        logger.info("=" * 70)

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
        self.switch_to(screen_name)

    def reload_config(self):
        nav_bar_height = get_navigation_bar_height()

        if platform == 'android':
            self.nav_height = dp(80)
            bottom_padding = 0
            button_spacing = dp(6)
        else:
            self.nav_height = dp(72)
            bottom_padding = nav_bar_height + dp(8)
            button_spacing = dp(4)

        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height
        self.padding = [dp(8), 0, dp(8), bottom_padding]
        self.spacing = button_spacing