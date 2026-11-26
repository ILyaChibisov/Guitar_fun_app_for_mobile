# screens/components/bottom_nav.py
"""
Нижняя панель навигации с единым фоном как в TopNav (до самого нижнего края)
и металлической верхней планкой отделения.
"""
import base64
import io

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform
from kivymd.app import MDApp

from bottom_nav_utils.nav_item_widget import StudioBottomNavItem
from config.logger_config import get_logger
from config.system_bars import get_navigation_bar_height
from data.bottom_nav import nav_assets
from state.settings_state import settings_state as settings_manager
from utils.localization import get_text

logger = get_logger("BottomNav")


class BottomNav(BoxLayout):
    """Нижняя панель навигации с верхней металлической рамкой и фоном в стиле TopNav."""

    NAV_SCREENS = ["songs", "chords", "tuner", "metronome", "favorites"]

    _top_bar_dark_tex = None
    _top_bar_light_tex = None

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.screen_manager = screen_manager
        self.orientation = "horizontal"
        self.size_hint = (1, None)

        if BottomNav._top_bar_dark_tex is None:
            BottomNav._top_bar_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(nav_assets.TOP_BAR_DARK_B64)), ext="png"
            ).texture
            BottomNav._top_bar_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(nav_assets.TOP_BAR_LIGHT_B64)), ext="png"
            ).texture

        nav_bar_height = get_navigation_bar_height()
        self.nav_height = dp(56)
        bottom_padding = 0 if platform == "android" else nav_bar_height
        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height

        self.bar_height = dp(5)
        self.padding = [dp(4), self.bar_height + dp(2), dp(4), dp(2) + bottom_padding]
        self.spacing = dp(2)

        with self.canvas.before:
            # 1. Единый фон от верхней рамки до самого нижнего края экрана (как в TopNav)
            self.bg_color_inst = Color(0.0, 0.05, 0.03, 0.26)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

            # 2. Металлическая верхняя планка отделения (только сверху, снизу рамки нет)
            self.top_bar_color = Color(1, 1, 1, 1)
            self.top_bar_rect = Rectangle(
                texture=self._top_bar_dark_tex,
                pos=(self.x, self.top - self.bar_height),
                size=(self.width, self.bar_height),
            )

        self.bind(pos=self._update_graphics, size=self._update_graphics)

        self.nav_items = [
            ("songs", "songs", "songs"),
            ("chords", "chords", "chords"),
            ("tuner", "tuner", "tuner"),
            ("metronome", "metronome", "metronome"),
            ("favorites", "favorites", "favorites"),
        ]

        self.items = []
        current_sm_screen = getattr(screen_manager, "current", "")
        for icon, text_key, screen in self.nav_items:
            item = StudioBottomNavItem(icon, text_key, screen)
            item.active = screen == current_sm_screen
            item.size_hint = (1, 1)
            self.add_widget(item)
            self.items.append(item)

        if hasattr(screen_manager, "bind"):
            screen_manager.bind(current=self._on_sm_current_changed)
        if hasattr(screen_manager, "add_observer"):
            screen_manager.add_observer(self.on_screen_changed)

        self.update_theme_colors()

    def _get_bottom_padding(self):
        return 0 if platform == "android" else get_navigation_bar_height()

    def _update_graphics(self, *args):
        if hasattr(self, "bg_rect"):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
        if hasattr(self, "top_bar_rect"):
            self.top_bar_rect.pos = (self.x, self.top - self.bar_height)
            self.top_bar_rect.size = (self.width, self.bar_height)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        is_light = theme_id == "light"

        # Палитра фона 1-в-1 как в TopNav
        if is_light:
            self.bg_color_inst.rgba = (0.97, 0.99, 0.98, 0.96)
        elif theme_id == "dark":
            self.bg_color_inst.rgba = (0.09, 0.09, 0.11, 0.96)
        else:  # green
            self.bg_color_inst.rgba = (0.0, 0.05, 0.03, 0.26)

        if hasattr(self, "top_bar_rect"):
            self.top_bar_rect.texture = (
                self._top_bar_light_tex if is_light else self._top_bar_dark_tex
            )

        for item in self.items:
            item.update_state(item, item.active)

    def update_language(self):
        for item, (_, text_key, _) in zip(self.items, self.nav_items):
            translated_text = get_text(text_key, text_key.capitalize())
            item.text = translated_text
            item.text_label.text = translated_text
            item._adjust_font_size()

    def _on_sm_current_changed(self, instance, screen_name):
        self._update_active_state(screen_name)

    def on_screen_changed(self, screen_name):
        self._update_active_state(screen_name)

    def _update_active_state(self, screen_name):
        if screen_name in self.NAV_SCREENS:
            for item, (_, _, screen) in zip(self.items, self.nav_items):
                item.active = screen == screen_name
        else:
            self.clear_active()

    def clear_active(self):
        for item in self.items:
            item.active = False
        logger.debug("🔽 Все иконки BottomNav сброшены")

    def switch_to(self, screen_name):
        app = MDApp.get_running_app()
        if hasattr(app, "is_auth_blocking") and app.is_auth_blocking:
            return

        if not self.sm or self.sm.current == screen_name:
            return

        self._update_active_state(screen_name)

        try:
            current_index = next(
                i for i, (_, _, s) in enumerate(self.nav_items) if s == self.sm.current
            )
            new_index = next(
                i for i, (_, _, s) in enumerate(self.nav_items) if s == screen_name
            )
            direction = "left" if new_index > current_index else "right"
        except StopIteration:
            direction = "left"

        self.sm.transition.direction = direction
        self.sm.current = screen_name

    def switch_tab(self, screen_name):
        self.switch_to(screen_name)

    def reload_config(self):
        bottom_padding = self._get_bottom_padding()
        self.nav_height = dp(56)
        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height

        self.padding = [dp(4), self.bar_height + dp(2), dp(4), dp(2) + bottom_padding]
        self.spacing = dp(2)
        self._update_graphics()
