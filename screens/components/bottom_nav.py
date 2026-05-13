# screens/components/bottom_nav.py
"""
Современная нижняя навигация - оптимизирована для Android с крупными иконками
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
from kivy.graphics import Color, Line, Rectangle
from io import BytesIO
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from config.bottom_nav_config import BottomNavConfig
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
    """Элемент нижней навигации"""

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
        self.padding = [0, dp(2), 0, dp(2)]

        # Контейнер иконки - растягивается
        self.icon_container = MDBoxLayout(
            size_hint=(1, 0.70),  # 70% высоты для иконки
            orientation='vertical'
        )

        self.custom_image = None
        self._load_icon()

        # Текст
        self.text_label = Label(
            text=self.text,
            font_size=sp(10),
            size_hint=(1, 0.30),  # 30% высоты для текста
            color=theme.TEXT_SECONDARY,
            bold=False,
            halign='center',
            valign='top'
        )
        self.text_label.bind(size=self.text_label.setter('text_size'))

        self.add_widget(self.icon_container)
        self.add_widget(self.text_label)

        self.update_state(None, self.active)
        self.bind(active=self.update_state)
        self.bind(icon_asset=self._reload_icon)

        # ВРЕМЕННО: красная рамка для отладки (только на ПК)
        if platform == 'win':
            self.bind(pos=self._update_outline, size=self._update_outline)

    def _update_outline(self, *args):
        """ВРЕМЕННО: красная рамка вокруг каждой кнопки (только ПК)"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 0, 0, 0.8)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1)

    def _reload_icon(self, *args):
        self._load_icon()

    def _load_icon(self):
        self.icon_container.clear_widgets()

        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    core_img = CoreImage(BytesIO(icon_data), ext="png")
                    # На Андроид иконки крупнее
                    icon_size = 0.80 if platform == 'android' else self.config['icon_size']
                    self.custom_image = Image(
                        texture=core_img.texture,
                        size_hint=(icon_size, icon_size),
                        pos_hint={'center_x': 0.5, 'center_y': 0.5},
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    self.icon_container.add_widget(self.custom_image)
                    return
            except Exception as e:
                logger.error('Ошибка загрузки иконки: ' + str(e))

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

        # Получаем высоту системной навигации
        nav_bar_height_dp = get_navigation_bar_height()

        if platform == 'android':
            # Android: панель 60dp + системная навигация
            self.panel_height = dp(60)
            self.height = self.panel_height + nav_bar_height_dp
            bottom_padding = nav_bar_height_dp  # отступ под системную навигацию
            top_padding = 0

            # Размеры для Android
            icon_size_android = 0.75
            font_size_android = sp(11)

            logger.info(f"Android: панель={self.panel_height}dp, + нав={nav_bar_height_dp}dp, всего={self.height}dp")
            logger.info(f"Android: иконки будут крупнее ({icon_size_android}), шрифт {font_size_android}")
        else:
            # Windows: панель 76dp + имитация навигации
            self.panel_height = dp(76)
            self.height = self.panel_height + nav_bar_height_dp
            bottom_padding = nav_bar_height_dp
            top_padding = dp(4)

            icon_size_android = 0.70
            font_size_android = sp(11)

            logger.info(f"Windows: панель={self.panel_height}dp, всего={self.height}dp")

        # Обновляем конфиг для текущей платформы
        BottomNavConfig.PANEL_HEIGHT = self.panel_height
        BottomNavConfig.DEFAULT_FONT_SIZE = 11

        # Паддинги панели
        self.padding = [dp(4), top_padding, dp(4), bottom_padding]
        self.spacing = dp(4)

        # ВРЕМЕННО: чёрный фон для отладки
        self.md_bg_color = [0, 0, 0, 1]

        # Белая рамка вокруг всей панели (только на ПК)
        if platform == 'win':
            self.bind(pos=self._update_panel_outline, size=self._update_panel_outline)

        logger.info("=" * 60)
        logger.info(f"Платформа: {platform}")
        logger.info(f"  - Высота панели: {self.panel_height}dp")
        logger.info(f"  - Общая высота: {self.height}dp")
        logger.info(f"  - Нижний отступ (под нав): {bottom_padding}dp")
        logger.info("=" * 60)

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

    def _update_panel_outline(self, *args):
        """ВРЕМЕННО: белая рамка вокруг всей панели (только ПК)"""
        self.canvas.before.remove_group('panel_outline')
        with self.canvas.before:
            Color(1, 1, 1, 1)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=2, group='panel_outline')

    def on_screen_changed(self, screen_name):
        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item.active = (screen == screen_name)

    def switch_to(self, screen_name):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            logger.debug("Навигация заблокирована")
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
        """Обновляет конфигурацию панели"""
        nav_bar_height_dp = get_navigation_bar_height()

        if platform == 'android':
            self.panel_height = dp(60)
            self.height = self.panel_height + nav_bar_height_dp
            bottom_padding = nav_bar_height_dp
            top_padding = 0
        else:
            self.panel_height = dp(76)
            self.height = self.panel_height + nav_bar_height_dp
            bottom_padding = nav_bar_height_dp
            top_padding = dp(4)

        self.padding = [dp(4), top_padding, dp(4), bottom_padding]
        self.spacing = dp(4)

        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item._reload_icon()

        logger.info(f"Нижняя навигация обновлена: высота={self.height}dp")