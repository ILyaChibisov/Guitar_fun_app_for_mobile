# screens/components/bottom_nav.py
"""
Современная нижняя навигация
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
        self.size_hint = (1, 1)
        self.spacing = dp(self.config['spacing'])
        self.padding = [0, dp(self.config['top_padding']), 0, 0]

        self.icon_container = MDBoxLayout(
            size_hint=(1, self.config['icon_height']),
            orientation='vertical'
        )

        self.custom_image = None
        self._load_icon()

        self.text_label = Label(
            text=self.text,
            font_size=sp(self.config['font_size']),
            size_hint=(1, 1 - self.config['icon_height']),
            color=theme.TEXT_SECONDARY,
            bold=False,
            halign='center',
            valign='top'
        )

        self.add_widget(self.icon_container)
        self.add_widget(self.text_label)

        self.update_state(None, self.active)
        self.bind(active=self.update_state)
        self.bind(icon_asset=self._reload_icon)

    def _reload_icon(self, *args):
        self._load_icon()

    def _load_icon(self):
        self.icon_container.clear_widgets()

        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    core_img = CoreImage(BytesIO(icon_data), ext="png")
                    self.custom_image = Image(
                        texture=core_img.texture,
                        size_hint=(self.config['icon_size'], self.config['icon_size']),
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

        # Для Windows всегда используем пресет 'large'
        if platform == 'win':
            preset = 'large'
            BottomNavConfig.apply_preset(preset)
            logger.info(f"Windows: принудительно применён пресет '{preset}'")
        else:
            screen_width = Window.width
            screen_height = Window.height
            preset = BottomNavConfig.get_preset_for_screen(screen_width, screen_height)
            BottomNavConfig.apply_preset(preset)
            logger.info(f"Нижняя навигация: применён пресет '{preset}' (экран {screen_width}x{screen_height})")

        # Высота панели из конфига
        self.panel_height = dp(BottomNavConfig.PANEL_HEIGHT)

        # Получаем высоту системной навигации в dp
        nav_bar_height_dp = get_navigation_bar_height()

        if platform == 'android':
            # Android: иконки прилегают к системной навигации
            self.height = self.panel_height + nav_bar_height_dp
            bottom_padding = nav_bar_height_dp
            top_padding = dp(BottomNavConfig.PANEL_PADDING[1])
            logger.info(f"Android: высота={self.height}dp, иконки={self.panel_height}dp, системная нав={nav_bar_height_dp}dp")
        else:
            # Windows: большие иконки для удобной отладки
            self.height = self.panel_height + nav_bar_height_dp
            top_padding = dp(BottomNavConfig.PANEL_PADDING[1])
            bottom_padding = nav_bar_height_dp
            logger.info(f"Windows: высота={self.height}dp, иконки={self.panel_height}dp")

        # Паддинги
        panel_padding = [dp(x) for x in BottomNavConfig.PANEL_PADDING]
        self.padding = [
            panel_padding[0],  # левый
            top_padding,       # верхний
            panel_padding[2],  # правый
            bottom_padding     # нижний
        ]
        self.spacing = dp(BottomNavConfig.PANEL_SPACING)
        self.md_bg_color = [0, 0, 0, 0]

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

        logger.info(f"Нижняя навигация инициализирована: высота={self.height}dp, "
                   f"верхний отступ={self.padding[1]}dp, нижний отступ={self.padding[3]}dp")

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
        self.panel_height = dp(BottomNavConfig.PANEL_HEIGHT)
        nav_bar_height_dp = get_navigation_bar_height()

        if platform == 'android':
            self.height = self.panel_height + nav_bar_height_dp
            bottom_padding = nav_bar_height_dp
            top_padding = dp(BottomNavConfig.PANEL_PADDING[1])
        else:
            self.height = self.panel_height + nav_bar_height_dp
            top_padding = dp(BottomNavConfig.PANEL_PADDING[1])
            bottom_padding = nav_bar_height_dp

        panel_padding = [dp(x) for x in BottomNavConfig.PANEL_PADDING]
        self.padding = [
            panel_padding[0],
            top_padding,
            panel_padding[2],
            bottom_padding
        ]
        self.spacing = dp(BottomNavConfig.PANEL_SPACING)

        for item, (_, _, screen) in zip(self.items, self.nav_items):
            new_config = BottomNavConfig.get_button_config(screen)
            item.config = new_config
            item.spacing = dp(new_config['spacing'])
            item.padding = [0, dp(new_config['top_padding']), 0, 0]
            item.icon_container.size_hint = (1, new_config['icon_height'])
            item.text_label.font_size = sp(new_config['font_size'])
            item.text_label.size_hint = (1, 1 - new_config['icon_height'])
            item._reload_icon()

        logger.info(f"Нижняя навигация обновлена: высота={self.height}dp")