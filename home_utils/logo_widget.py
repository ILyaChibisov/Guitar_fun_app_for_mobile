# home_utils/logo_widget.py
import base64
import io

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, StencilPop, StencilPush, StencilUnUse, StencilUse
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget

from data.home import logo_assets
from state.settings_state import settings_state as settings_manager


class StudioFuturisticLogo(ButtonBehavior, Widget):
    """3D футуристичный логотип GUITARFANS с периодической анимацией подсветки и блика."""

    glow_pulse = NumericProperty(0.0)     # 0..1 общее неоновое свечение контура
    scan_progress = NumericProperty(-0.3) # -0.3..1.3 позиция светового блика слева направо
    neon_color = ListProperty([0.22, 0.96, 0.52, 1.0])

    _textures_loaded = False
    _tex_green = None
    _tex_dark = None
    _tex_light = None
    _tex_mask = None
    _tex_beam = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = dp(76)
        self._periodic_event = None

        if not StudioFuturisticLogo._textures_loaded:
            def _load(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            StudioFuturisticLogo._tex_green = _load(logo_assets.LOGO_GREEN_B64)
            StudioFuturisticLogo._tex_dark = _load(logo_assets.LOGO_DARK_B64)
            StudioFuturisticLogo._tex_light = _load(logo_assets.LOGO_LIGHT_B64)
            StudioFuturisticLogo._tex_mask = _load(logo_assets.LOGO_MASK_B64)
            StudioFuturisticLogo._tex_beam = _load(logo_assets.SCAN_BEAM_B64)
            StudioFuturisticLogo._textures_loaded = True

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            glow_pulse=self._redraw,
            scan_progress=self._redraw,
            neon_color=self._redraw,
        )
        self.update_theme_colors()

    @staticmethod
    def _get_theme_neon(theme_id):
        if theme_id == "light":
            return [0.06, 0.62, 0.32, 1.0]
        elif theme_id == "dark":
            return [1.0, 0.54, 0.04, 1.0]
        return [0.22, 0.96, 0.52, 1.0]

    def update_theme_colors(self):
        self.neon_color = self._get_theme_neon(settings_manager.theme)
        self._redraw()

    def start_periodic_animation(self):
        """Запускает периодический световой импульс, пока открыт главный экран."""
        self.stop_periodic_animation()
        Clock.schedule_once(lambda dt: self.trigger_shine(), 0.45)
        self._periodic_event = Clock.schedule_interval(lambda dt: self.trigger_shine(), 3.8)

    def stop_periodic_animation(self):
        """Останавливает периодическую анимацию при уходе с экрана."""
        if self._periodic_event is not None:
            self._periodic_event.cancel()
            self._periodic_event = None
        Animation.cancel_all(self, "glow_pulse", "scan_progress")
        self.glow_pulse = 0.0
        self.scan_progress = -0.3

    def trigger_shine(self):
        """Запускает один цикл неоновой подсветки и прохода блика по 3D-буквам."""
        Animation.cancel_all(self, "glow_pulse", "scan_progress")
        self.glow_pulse = 0.0
        self.scan_progress = -0.25

        pulse_anim = (
            Animation(glow_pulse=1.0, duration=0.38, t="out_quad")
            + Animation(glow_pulse=0.0, duration=0.65, t="out_cubic")
        )
        scan_anim = Animation(scan_progress=1.25, duration=0.95, t="in_out_quad")

        pulse_anim.start(self)
        scan_anim.start(self)

    def on_press(self):
        self.trigger_shine()

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        theme_id = settings_manager.theme
        if theme_id == "light":
            logo_tex = self._tex_light
        elif theme_id == "dark":
            logo_tex = self._tex_dark
        else:
            logo_tex = self._tex_green

        src_w, src_h = logo_assets.LOGO_SIZE
        aspect = src_w / src_h

        draw_h = self.height * 0.94
        draw_w = draw_h * aspect
        if draw_w > self.width * 0.98:
            draw_w = self.width * 0.98
            draw_h = draw_w / aspect

        lx = round(self.center_x - draw_w * 0.5)
        ly = round(self.center_y - draw_h * 0.5)
        lw = round(draw_w)
        lh = round(draw_h)

        r, g, b, _ = self.neon_color
        gp = float(self.glow_pulse)
        sp_val = float(self.scan_progress)

        with self.canvas:
            # 1. Периодический неоновый ореол позади 3D-букв
            if gp > 0.01 and self._tex_mask is not None:
                halo_w = round(lw * (1.03 + 0.03 * gp))
                halo_h = round(lh * (1.12 + 0.08 * gp))
                Color(r, g, b, 0.44 * gp)
                Rectangle(
                    texture=self._tex_mask,
                    pos=(round(self.center_x - halo_w * 0.5), round(self.center_y - halo_h * 0.5)),
                    size=(halo_w, halo_h),
                )

            # 2. Сам 3D футуристичный логотип GUITARFANS
            if logo_tex is not None:
                Color(1, 1, 1, 1)
                Rectangle(texture=logo_tex, pos=(lx, ly), size=(lw, lh))

            # 3. Проходящий световой блик строго по форме букв (через Stencil)
            if -0.2 < sp_val < 1.2 and self._tex_mask is not None and self._tex_beam is not None:
                StencilPush()
                Color(1, 1, 1, 1)
                Rectangle(texture=self._tex_mask, pos=(lx, ly), size=(lw, lh))
                StencilUse()

                beam_w = round(lw * 0.34)
                beam_h = round(lh * 1.3)
                beam_x = round(lx + sp_val * lw - beam_w * 0.5)
                beam_y = round(ly - (beam_h - lh) * 0.5)

                Color(min(1.0, r + 0.45), min(1.0, g + 0.45), min(1.0, b + 0.45), 0.72)
                Rectangle(texture=self._tex_beam, pos=(beam_x, beam_y), size=(beam_w, beam_h))

                StencilUnUse()
                Color(1, 1, 1, 1)
                Rectangle(texture=self._tex_mask, pos=(lx, ly), size=(lw, lh))
                StencilPop()