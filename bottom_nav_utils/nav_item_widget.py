# bottom_nav_utils/nav_item_widget.py
import base64
import io

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.utils import platform
from kivymd.app import MDApp

from data.bottom_nav import nav_assets
from state.settings_state import settings_state as settings_manager
from utils.localization import get_text


class StudioBottomNavItem(ButtonBehavior, FloatLayout):
    """Металлизированная иконка навигации без кнопки и подчёркивания с анимацией подсветки."""

    text = StringProperty("")
    active = BooleanProperty(False)
    icon_scale = NumericProperty(1.0)
    icon_lift = NumericProperty(0.0)
    press_glow = NumericProperty(0.0)
    glow_color = ListProperty([1.0, 0.95, 0.30, 1.0])

    _textures_loaded = False
    _glow_orb_tex = None
    _metal_dark_textures = {}
    _metal_light_textures = {}
    _mask_textures = {}

    def __init__(self, icon_name, text_key, screen_name, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.text_key = text_key
        self.screen_name = screen_name
        self.text = get_text(text_key, text_key.capitalize())

        self.size_hint = (1, 1)

        if not StudioBottomNavItem._textures_loaded:
            def _load_b64(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            StudioBottomNavItem._glow_orb_tex = _load_b64(nav_assets.GLOW_ORB_B64)

            for name, b64_str in nav_assets.ICONS_METAL_DARK_B64.items():
                StudioBottomNavItem._metal_dark_textures[name] = _load_b64(b64_str)
            for name, b64_str in nav_assets.ICONS_METAL_LIGHT_B64.items():
                StudioBottomNavItem._metal_light_textures[name] = _load_b64(b64_str)
            for name, b64_str in nav_assets.ICONS_GLOW_MASK_B64.items():
                StudioBottomNavItem._mask_textures[name] = _load_b64(b64_str)

            StudioBottomNavItem._textures_loaded = True

        base_font = sp(11) if platform == "android" else sp(10)
        self.text_label = Label(
            text=self.text,
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(15),
            bold=False,
            shorten=True,
            shorten_from="right",
            font_size=base_font,
            pos_hint={"center_x": 0.5, "y": 0.06},
        )
        self.add_widget(self.text_label)

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            active=self._on_state_changed,
            icon_scale=self._redraw,
            icon_lift=self._redraw,
            press_glow=self._redraw,
            glow_color=self._redraw,
        )
        self.text_label.bind(width=self._adjust_font_size, text=self._adjust_font_size)

        self.update_state(self, self.active)
        Clock.schedule_once(lambda dt: self._adjust_font_size(), 0.05)

    @staticmethod
    def _get_theme_colors(theme_id):
        if theme_id == "light":
            return {
                "active": [0.06, 0.54, 0.28, 1.0],
                "inactive_text": [0.16, 0.22, 0.19, 0.88],
            }
        elif theme_id == "dark":
            return {
                "active": [1.0, 0.56, 0.05, 1.0],
                "inactive_text": [0.82, 0.85, 0.88, 0.80],
            }
        return {
            "active": [1.0, 0.95, 0.30, 1.0],
            "inactive_text": [0.86, 0.94, 0.90, 0.84],
        }

    def _adjust_font_size(self, *args):
        if not hasattr(self, "text_label") or not self.text_label:
            return
        text = self.text_label.text
        if not text:
            return

        available_width = self.width - dp(6)
        if available_width < dp(16):
            self.text_label.font_size = sp(7.5)
            return

        test_sizes = [11, 10.5, 10, 9.5, 9, 8.5, 8, 7.5]
        for size in test_sizes:
            lbl = CoreLabel(
                text=text,
                font_size=sp(size),
                font_name=self.text_label.font_name,
                bold=self.active,
            )
            lbl.refresh()
            if lbl.texture.width <= available_width:
                self.text_label.font_size = sp(size)
                self.text_label.text_size = (available_width, None)
                return

        self.text_label.font_size = sp(7)
        self.text_label.text_size = (available_width, None)

    def _on_state_changed(self, instance, value):
        self.update_state(instance, value)
        if value:
            Animation.cancel_all(self, "icon_scale", "icon_lift")
            (
                Animation(icon_scale=1.18, icon_lift=dp(2.0), duration=0.11, t="out_quad")
                + Animation(icon_scale=1.06, icon_lift=dp(1.0), duration=0.16, t="out_back")
            ).start(self)
        else:
            Animation.cancel_all(self, "icon_scale", "icon_lift")
            Animation(icon_scale=1.0, icon_lift=0.0, duration=0.14, t="out_quad").start(self)

    def update_state(self, instance, value):
        theme_id = settings_manager.theme
        palette = self._get_theme_colors(theme_id)
        self.glow_color = palette["active"]

        if value:
            self.text_label.color = palette["active"]
            self.text_label.bold = True
            self.icon_scale = 1.06
            self.icon_lift = dp(1.0)
        else:
            self.text_label.color = palette["inactive_text"]
            self.text_label.bold = False
            self.icon_scale = 1.0
            self.icon_lift = 0.0

        self._adjust_font_size()
        self._redraw()

    def on_press(self):
        Animation.cancel_all(self, "icon_scale", "icon_lift", "press_glow")
        Animation(
            icon_scale=0.86,
            icon_lift=-dp(1.0),
            press_glow=1.0,
            duration=0.07,
            t="out_quad",
        ).start(self)

    def on_release(self):
        app = MDApp.get_running_app()
        if hasattr(app, "is_auth_blocking") and app.is_auth_blocking:
            Animation(icon_scale=1.0, icon_lift=0.0, press_glow=0.0, duration=0.15).start(self)
            return

        Animation.cancel_all(self, "icon_scale", "icon_lift", "press_glow")
        target_scale = 1.06 if self.active else 1.0
        target_lift = dp(1.0) if self.active else 0.0

        (
            Animation(icon_scale=1.22, icon_lift=dp(2.5), press_glow=1.0, duration=0.10, t="out_quad")
            + Animation(
                icon_scale=target_scale,
                icon_lift=target_lift,
                press_glow=0.0,
                duration=0.28,
                t="out_cubic",
            )
        ).start(self)

        if hasattr(self.parent, "switch_to"):
            self._update_top_nav_before_switch(self.screen_name)
            self.parent.switch_to(self.screen_name)

    def _update_top_nav_before_switch(self, screen_name):
        app = MDApp.get_running_app()
        if app and hasattr(app, "top_nav"):
            titles = {
                "songs": get_text("songs", "Песни"),
                "chords": get_text("chords", "Аккорды"),
                "tuner": get_text("tuner", "Тюнер"),
                "metronome": get_text("metronome", "Метроном"),
                "favorites": get_text("favorites", "Избранное"),
            }
            if screen_name in titles:
                app.top_nav.set_custom_title(titles[screen_name])

    def _redraw(self, *args):
        self.canvas.before.clear()
        if self.width <= 4 or self.height <= 4:
            return

        is_light = settings_manager.theme == "light"
        metal_tex = (
            self._metal_light_textures.get(self.icon_name)
            if is_light
            else self._metal_dark_textures.get(self.icon_name)
        )
        mask_tex = self._mask_textures.get(self.icon_name)

        r, g, b, _ = self.glow_color
        glow_strength = max(0.55 if self.active else 0.0, float(self.press_glow))

        icx = self.center_x
        icy = self.y + self.height * 0.59 + float(self.icon_lift)
        base_ico = min(self.width * 0.58, self.height * 0.56)
        ico_size = round(base_ico * float(self.icon_scale))

        with self.canvas.before:
            # 1. Радиальный неоновый прожектор при нажатии и у активной вкладки
            if glow_strength > 0.01 and self._glow_orb_tex is not None:
                orb_size = round(ico_size * (1.85 + 0.45 * float(self.press_glow)))
                Color(r, g, b, 0.52 * glow_strength)
                Rectangle(
                    texture=self._glow_orb_tex,
                    pos=(round(icx - orb_size * 0.5), round(icy - orb_size * 0.5)),
                    size=(orb_size, orb_size),
                )

            # 2. Объёмная металлизированная иконка (без подчёркивания под текстом)
            if metal_tex is not None and mask_tex is not None:
                Color(0, 0, 0, 0.28 if is_light else 0.65)
                Rectangle(
                    texture=mask_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5 - dp(1.4))),
                    size=(ico_size, ico_size),
                )

                if glow_strength > 0.01:
                    halo_s = round(ico_size * (1.10 + 0.08 * float(self.press_glow)))
                    Color(r, g, b, 0.42 * glow_strength)
                    Rectangle(
                        texture=mask_tex,
                        pos=(round(icx - halo_s * 0.5), round(icy - halo_s * 0.5)),
                        size=(halo_s, halo_s),
                    )

                Color(1, 1, 1, 1.0 if (self.active or self.press_glow > 0.1) else 0.88)
                Rectangle(
                    texture=metal_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5)),
                    size=(ico_size, ico_size),
                )

                if glow_strength > 0.01:
                    tint_alpha = (0.38 if self.active else 0.0) + 0.45 * float(self.press_glow)
                    Color(r, g, b, min(0.85, tint_alpha))
                    Rectangle(
                        texture=mask_tex,
                        pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5)),
                        size=(ico_size, ico_size),
                    )