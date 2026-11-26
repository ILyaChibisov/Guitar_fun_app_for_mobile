# metronome_utils/button_widget.py
import base64
import io

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget

from data.metronome import button_assets
from state.settings_state import settings_state as settings_manager


class StudioHardwareButton(ButtonBehavior, Widget):
    """Студийный триггер-пэд (MPC / Elektron стиль) с неоновым контуром и HD-иконкой."""

    icon_type = StringProperty("play")  # 'play', 'stop', 'reset', 'accent', 'tone'
    is_active = BooleanProperty(False)
    is_pressed = BooleanProperty(False)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])
    custom_glow_color = ListProperty([])

    _textures_loaded = False
    _well_dark = None
    _up_dark = None
    _down_dark = None
    _well_light = None
    _up_light = None
    _down_light = None
    _icon_textures = {}

    def __init__(self, icon_type="play", on_press=None, is_active=False, **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        self.is_active = is_active
        self._callback = on_press
        self.size_hint = (1, 1)

        if not StudioHardwareButton._textures_loaded:
            def _load_b64(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            StudioHardwareButton._well_dark = _load_b64(button_assets.WELL_DARK_B64)
            StudioHardwareButton._up_dark = _load_b64(button_assets.KEY_UP_DARK_B64)
            StudioHardwareButton._down_dark = _load_b64(button_assets.KEY_DOWN_DARK_B64)

            StudioHardwareButton._well_light = _load_b64(button_assets.WELL_LIGHT_B64)
            StudioHardwareButton._up_light = _load_b64(button_assets.KEY_UP_LIGHT_B64)
            StudioHardwareButton._down_light = _load_b64(button_assets.KEY_DOWN_LIGHT_B64)

            for name, b64_str in button_assets.ICONS_PNG_BASE64.items():
                StudioHardwareButton._icon_textures[name] = _load_b64(b64_str)

            StudioHardwareButton._textures_loaded = True

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            icon_type=self.update_canvas,
            is_active=self.update_canvas,
            is_pressed=self.update_canvas,
            accent_color=self.update_canvas,
            custom_glow_color=self.update_canvas,
        )
        self.update_theme_colors()

    @staticmethod
    def _get_theme_glow(theme_id):
        if theme_id == "light":
            return [0.08, 0.58, 0.30, 1.0]
        elif theme_id == "dark":
            return [1.0, 0.50, 0.0, 1.0]
        return [0.18, 0.88, 0.28, 1.0]

    def update_theme_colors(self):
        self.accent_color = self._get_theme_glow(settings_manager.theme)
        self.update_canvas()

    def _active_glow(self):
        if self.custom_glow_color and len(self.custom_glow_color) >= 3:
            c = self.custom_glow_color
            return [float(c[0]), float(c[1]), float(c[2]), 1.0]
        c = self.accent_color
        return [float(c[0]), float(c[1]), float(c[2]), 1.0]

    def on_press(self):
        Clock.unschedule(self._reset_press_state)
        self.is_pressed = True

    def on_release(self):
        Clock.schedule_once(self._reset_press_state, 0.14)
        if self._callback:
            self._callback()

    def _reset_press_state(self, dt):
        self.is_pressed = False

    def _resolve_icon_texture(self):
        if self.icon_type == "accent" and not self.is_active:
            return self._icon_textures.get("accent_off") or self._icon_textures.get("accent")
        return self._icon_textures.get(self.icon_type)

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        bw_src, bh_src = button_assets.BUTTON_SIZE
        aspect = bw_src / bh_src

        btn_h = self.height * 0.98
        btn_w = btn_h * aspect
        if btn_w > self.width * 0.98:
            btn_w = self.width * 0.98
            btn_h = btn_w / aspect

        bx = round(self.center_x - btn_w * 0.5)
        by = round(self.center_y - btn_h * 0.5)
        btn_w = round(btn_w)
        btn_h = round(btn_h)

        is_light = settings_manager.theme == "light"
        pressed = self.is_pressed
        meta = button_assets.DOWN_META if pressed else button_assets.UP_META

        if is_light:
            well_tex = self._well_light
            key_tex = self._down_light if pressed else self._up_light
        else:
            well_tex = self._well_dark
            key_tex = self._down_dark if pressed else self._up_dark

        r, g, b, _ = self._active_glow()
        lit = pressed

        with self.canvas:
            # 1. Гнездо пэда
            Color(1, 1, 1, 1)
            Rectangle(texture=well_tex, pos=(bx, by), size=(btn_w, btn_h))

            # 2. Клавиша пэда
            Rectangle(texture=key_tex, pos=(bx, by), size=(btn_w, btn_h))

            # 3. Неоновый контур-световод (Light-Pipe Rim) по периметру клавиши
            rx_n, ry_n, rw_n, rh_n = meta["rim_box_norm"]
            rim_x = bx + rx_n * btn_w
            rim_y = by + ry_n * btn_h
            rim_w = rw_n * btn_w
            rim_h = rh_n * btn_h
            rim_r = meta["rim_radius_norm"] * btn_h

            if lit:
                # Внешний мягкий ореол световода
                Color(r, g, b, 0.28)
                Line(
                    rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r),
                    width=dp(2.6),
                )
                # Яркая неоновая жила световода
                Color(
                    min(1.0, r + 0.18),
                    min(1.0, g + 0.18),
                    min(1.0, b + 0.18),
                    0.95,
                )
                Line(
                    rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r),
                    width=dp(1.25),
                )
            else:
                # В неактивном состоянии — тонкий приглушённый контур в тон темы
                Color(r, g, b, 0.22 if is_light else 0.18)
                Line(
                    rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r),
                    width=dp(1.0),
                )

            # 4. Крупная центральная гравировка иконки
            ico_tex = self._resolve_icon_texture()
            if ico_tex is not None:
                icx = bx + btn_w * 0.5
                icy = by + meta["center_y_norm"] * btn_h
                ico_size = round(min(btn_w, btn_h) * 0.54)

                # Тень/фаска гравировки
                if is_light:
                    Color(1, 1, 1, 0.70)
                    Rectangle(
                        texture=ico_tex,
                        pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5 - dp(1))),
                        size=(ico_size, ico_size),
                    )
                else:
                    Color(0, 0, 0, 0.55)
                    Rectangle(
                        texture=ico_tex,
                        pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5 - dp(1.2))),
                        size=(ico_size, ico_size),
                    )

                # Свечение иконки при активности
                if lit:
                    Color(r, g, b, 0.26)
                    glow_s = round(ico_size * 1.12)
                    Rectangle(
                        texture=ico_tex,
                        pos=(round(icx - glow_s * 0.5), round(icy - glow_s * 0.5)),
                        size=(glow_s, glow_s),
                    )

                # Основная заливка иконки
                if lit:
                    Color(
                        min(1.0, r + 0.22),
                        min(1.0, g + 0.22),
                        min(1.0, b + 0.22),
                        0.98,
                    )
                else:
                    if is_light:
                        Color(0.22, 0.26, 0.24, 0.85)
                    else:
                        Color(0.84, 0.87, 0.90, 0.78)

                Rectangle(
                    texture=ico_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5)),
                    size=(ico_size, ico_size),
                )