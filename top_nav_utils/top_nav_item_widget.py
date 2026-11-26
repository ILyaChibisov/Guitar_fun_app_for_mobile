# top_nav_utils/top_nav_item_widget.py
import base64
import io

from kivy.animation import Animation
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget

from data.top_nav import top_nav_assets
from state.settings_state import settings_state as settings_manager


class StudioTopNavButton(ButtonBehavior, Widget):
    """Металлизированная кнопка TopNav без рамки с неоновой подсветкой при нажатии."""

    icon = StringProperty("home")
    icon_scale = NumericProperty(1.0)
    press_glow = NumericProperty(0.0)
    glow_color = ListProperty([1.0, 0.95, 0.30, 1.0])
    custom_tint = ListProperty([])  # Если задан (например, золотая звезда), подсвечивает постоянно

    _textures_loaded = False
    _glow_orb_tex = None
    _metal_dark_textures = {}
    _metal_light_textures = {}
    _mask_textures = {}

    def __init__(self, icon="home", on_release=None, **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.size_hint = (None, None)
        self.size = (dp(44), dp(44))
        if on_release is not None:
            self.bind(on_release=on_release)

        if not StudioTopNavButton._textures_loaded:
            def _load(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            StudioTopNavButton._glow_orb_tex = _load(top_nav_assets.GLOW_ORB_B64)

            for name, b64_str in top_nav_assets.ICONS_METAL_DARK_B64.items():
                StudioTopNavButton._metal_dark_textures[name] = _load(b64_str)
            for name, b64_str in top_nav_assets.ICONS_METAL_LIGHT_B64.items():
                StudioTopNavButton._metal_light_textures[name] = _load(b64_str)
            for name, b64_str in top_nav_assets.ICONS_GLOW_MASK_B64.items():
                StudioTopNavButton._mask_textures[name] = _load(b64_str)

            StudioTopNavButton._textures_loaded = True

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            icon=self._redraw,
            icon_scale=self._redraw,
            press_glow=self._redraw,
            glow_color=self._redraw,
            custom_tint=self._redraw,
        )
        self.update_theme_colors()

    @staticmethod
    def _get_theme_accent(theme_id):
        """Палитра 1-в-1 как в BottomNav."""
        if theme_id == "light":
            return [0.06, 0.54, 0.28, 1.0]
        elif theme_id == "dark":
            return [1.0, 0.56, 0.05, 1.0]
        return [1.0, 0.95, 0.30, 1.0]

    def update_theme_colors(self):
        self.glow_color = self._get_theme_accent(settings_manager.theme)
        self._redraw()

    def on_press(self):
        Animation.cancel_all(self, "icon_scale", "press_glow")
        Animation(icon_scale=0.84, press_glow=1.0, duration=0.07, t="out_quad").start(self)

    def on_release(self):
        Animation.cancel_all(self, "icon_scale", "press_glow")
        (
            Animation(icon_scale=1.20, press_glow=1.0, duration=0.10, t="out_quad")
            + Animation(icon_scale=1.0, press_glow=0.0, duration=0.26, t="out_cubic")
        ).start(self)

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        is_light = settings_manager.theme == "light"
        metal_tex = (
            self._metal_light_textures.get(self.icon)
            if is_light
            else self._metal_dark_textures.get(self.icon)
        )
        mask_tex = self._mask_textures.get(self.icon)
        if metal_tex is None or mask_tex is None:
            return

        has_tint = bool(self.custom_tint and len(self.custom_tint) >= 3)
        if has_tint:
            r, g, b = float(self.custom_tint[0]), float(self.custom_tint[1]), float(self.custom_tint[2])
        else:
            r, g, b, _ = self.glow_color

        glow_strength = max(0.50 if has_tint else 0.0, float(self.press_glow))

        icx, icy = self.center
        base_ico = min(self.width, self.height) * 0.58
        ico_size = round(base_ico * float(self.icon_scale))

        with self.canvas:
            # 1. Радиальный неоновый прожектор при нажатии
            if glow_strength > 0.01 and self._glow_orb_tex is not None:
                orb_size = round(ico_size * (1.85 + 0.45 * float(self.press_glow)))
                Color(r, g, b, 0.50 * glow_strength)
                Rectangle(
                    texture=self._glow_orb_tex,
                    pos=(round(icx - orb_size * 0.5), round(icy - orb_size * 0.5)),
                    size=(orb_size, orb_size),
                )

            # 2. Глубокая тень гравировки
            Color(0, 0, 0, 0.28 if is_light else 0.65)
            Rectangle(
                texture=mask_tex,
                pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5 - dp(1.3))),
                size=(ico_size, ico_size),
            )

            # 3. Неоновый ореол по контуру при нажатии
            if glow_strength > 0.01:
                halo_s = round(ico_size * (1.12 + 0.08 * float(self.press_glow)))
                Color(r, g, b, 0.44 * glow_strength)
                Rectangle(
                    texture=mask_tex,
                    pos=(round(icx - halo_s * 0.5), round(icy - halo_s * 0.5)),
                    size=(halo_s, halo_s),
                )

            # 4. Шлифованная металлическая иконка
            Color(1, 1, 1, 0.96 if glow_strength > 0.05 else 0.90)
            Rectangle(
                texture=metal_tex,
                pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5)),
                size=(ico_size, ico_size),
            )

            # 5. Световая тонировка в акцентный цвет при нажатии / для активной звезды
            if glow_strength > 0.01:
                tint_alpha = (0.55 if has_tint else 0.0) + 0.45 * float(self.press_glow)
                Color(r, g, b, min(0.88, tint_alpha))
                Rectangle(
                    texture=mask_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5)),
                    size=(ico_size, ico_size),
                )
