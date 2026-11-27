# tuner_utils/menu_widget.py
import base64
import io

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout

from state.settings_state import settings_state as settings_manager

try:
    from data.tuner import menu_assets
except ImportError:
    from tuner_utils.menu_generator import save_tuner_menu_assets
    save_tuner_menu_assets()
    from data.tuner import menu_assets


class TunerHardwareButton(ButtonBehavior, Widget):
    """Студийный триггер-пэд тюнера с неоновым световодом и 4x SSAA иконкой."""

    icon_type = StringProperty("play")  # 'play', 'stop', 'reset', 'tune', 'guitar', 'bass', 'ukulele'
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

        if not TunerHardwareButton._textures_loaded:
            def _load_b64(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            TunerHardwareButton._well_dark = _load_b64(menu_assets.WELL_DARK_B64)
            TunerHardwareButton._up_dark = _load_b64(menu_assets.KEY_UP_DARK_B64)
            TunerHardwareButton._down_dark = _load_b64(menu_assets.KEY_DOWN_DARK_B64)

            TunerHardwareButton._well_light = _load_b64(menu_assets.WELL_LIGHT_B64)
            TunerHardwareButton._up_light = _load_b64(menu_assets.KEY_UP_LIGHT_B64)
            TunerHardwareButton._down_light = _load_b64(menu_assets.KEY_DOWN_LIGHT_B64)

            for name, b64_str in menu_assets.ICONS_PNG_BASE64.items():
                TunerHardwareButton._icon_textures[name] = _load_b64(b64_str)

            TunerHardwareButton._textures_loaded = True

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

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        bw_src, bh_src = menu_assets.BUTTON_SIZE
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
        meta = menu_assets.DOWN_META if pressed else menu_assets.UP_META

        if is_light:
            well_tex = self._well_light
            key_tex = self._down_light if pressed else self._up_light
        else:
            well_tex = self._well_dark
            key_tex = self._down_dark if pressed else self._up_dark

        r, g, b, _ = self._active_glow()
        lit = pressed or self.is_active

        with self.canvas:
            # 1. Шахта пэда
            Color(1, 1, 1, 1)
            Rectangle(texture=well_tex, pos=(bx, by), size=(btn_w, btn_h))

            # 2. Клавиша пэда
            Rectangle(texture=key_tex, pos=(bx, by), size=(btn_w, btn_h))

            # 3. Неоновый световод по периметру
            rx_n, ry_n, rw_n, rh_n = meta["rim_box_norm"]
            rim_x = bx + rx_n * btn_w
            rim_y = by + ry_n * btn_h
            rim_w = rw_n * btn_w
            rim_h = rh_n * btn_h
            rim_r = meta["rim_radius_norm"] * btn_h

            if lit:
                Color(r, g, b, 0.28)
                Line(
                    rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r),
                    width=dp(2.6),
                )
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
                Color(r, g, b, 0.22 if is_light else 0.18)
                Line(
                    rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r),
                    width=dp(1.0),
                )

            # 4. Центральная иконка
            ico_tex = self._icon_textures.get(self.icon_type)
            if ico_tex is not None:
                icx = bx + btn_w * 0.5
                icy = by + meta["center_y_norm"] * btn_h
                # Для силуэтов инструментов даём чуть больший масштаб для читаемости
                scale = 0.62 if self.icon_type in ("guitar", "bass", "ukulele") else 0.54
                ico_size = round(min(btn_w, btn_h) * scale)

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

                if lit:
                    Color(r, g, b, 0.26)
                    glow_s = round(ico_size * 1.12)
                    Rectangle(
                        texture=ico_tex,
                        pos=(round(icx - glow_s * 0.5), round(icy - glow_s * 0.5)),
                        size=(glow_s, glow_s),
                    )

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
                        Color(0.84, 0.87, 0.90, 0.82)

                Rectangle(
                    texture=ico_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5)),
                    size=(ico_size, ico_size),
                )


class StudioTunerMenu(MDBoxLayout):
    """Студийная рэковая панель тюнера: Play/Stop -> Reset -> Tuning -> Instrument."""

    _panel_dark_tex = None
    _panel_light_tex = None

    def __init__(
        self,
        on_play=None,
        on_reset=None,
        on_tune=None,
        on_instrument=None,
        current_instrument="guitar",
        is_listening=False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (1, None)
        self.height = dp(74)
        self.padding = [dp(22), dp(9), dp(22), dp(9)]
        self.spacing = dp(8)

        self.on_play_press = on_play
        self.on_reset_press = on_reset
        self.on_tune_press = on_tune
        self.on_instrument_press = on_instrument
        self.current_instrument = current_instrument
        self.is_listening = is_listening

        if StudioTunerMenu._panel_dark_tex is None:
            StudioTunerMenu._panel_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.PANEL_DARK_B64)), ext="png"
            ).texture
            StudioTunerMenu._panel_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.PANEL_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._panel_dark_tex,
                pos=self.pos,
                size=self.size,
            )

        self.bind(pos=self._update_bg, size=self._update_bg)
        self._build_ui()
        self.update_theme_colors()

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _build_ui(self):
        # 1. Play / Stop
        self.play_item = TunerHardwareButton(
            icon_type="stop" if self.is_listening else "play",
            is_active=self.is_listening,
            on_press=self._on_play,
        )

        # 2. Сброс
        self.reset_item = TunerHardwareButton(
            icon_type="reset",
            is_active=False,
            on_press=self._on_reset,
        )

        # 3. Выбор строя
        self.tune_item = TunerHardwareButton(
            icon_type="tune",
            is_active=False,
            on_press=self._on_tune,
        )

        # 4. Выбор инструмента (guitar / bass / ukulele)
        self.instrument_item = TunerHardwareButton(
            icon_type=self._resolve_instrument_icon(self.current_instrument),
            is_active=False,
            on_press=self._on_instrument,
        )

        self.add_widget(self.play_item)
        self.add_widget(self.reset_item)
        self.add_widget(self.tune_item)
        self.add_widget(self.instrument_item)

    @staticmethod
    def _resolve_instrument_icon(instrument):
        if instrument in ("guitar", "bass", "ukulele"):
            return instrument
        return "guitar"

    def _on_play(self):
        if self.on_play_press:
            self.on_play_press()

    def _on_reset(self):
        if self.on_reset_press:
            self.on_reset_press()

    def _on_tune(self):
        if self.on_tune_press:
            self.on_tune_press()

    def _on_instrument(self):
        if self.on_instrument_press:
            self.on_instrument_press()

    def update_state(self, is_listening):
        self.is_listening = is_listening
        self.play_item.icon_type = "stop" if is_listening else "play"
        self.play_item.is_active = is_listening
        self.play_item.custom_glow_color = [0.95, 0.28, 0.28, 1.0] if is_listening else []

    def update_instrument(self, instrument):
        self.current_instrument = instrument
        self.instrument_item.icon_type = self._resolve_instrument_icon(instrument)

    def update_theme_colors(self):
        is_light = settings_manager.theme == "light"
        self._bg_rect.texture = self._panel_light_tex if is_light else self._panel_dark_tex
        for btn in (self.play_item, self.reset_item, self.tune_item, self.instrument_item):
            btn.update_theme_colors()

class StudioTunerCard(MDBoxLayout):
    """Студийная металлическая карточка тюнера (высота dp(330)) с полупрозрачной нишей для зелёной темы."""

    _card_dark_tex = None
    _card_green_tex = None
    _card_light_tex = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = dp(330)
        self.padding = [dp(22), dp(14), dp(22), dp(14)]
        self.spacing = dp(0)

        if StudioTunerCard._card_dark_tex is None:
            StudioTunerCard._card_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.CARD_DARK_B64)), ext="png"
            ).texture
            StudioTunerCard._card_green_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.CARD_GREEN_B64)), ext="png"
            ).texture
            StudioTunerCard._card_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.CARD_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._card_dark_tex,
                pos=self.pos,
                size=self.size,
            )

        self.bind(pos=self._update_bg, size=self._update_bg)
        self.update_theme_colors()

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        if theme_id == "light":
            self._bg_rect.texture = self._card_light_tex
        elif theme_id == "green":
            self._bg_rect.texture = self._card_green_tex
        else:
            self._bg_rect.texture = self._card_dark_tex

