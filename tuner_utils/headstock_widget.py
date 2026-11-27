# tuner_utils/headstock_widget.py
import base64
import importlib
import io
import math

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout

from data.grifs import bass_4, bass_5, guitar_6, ukulele_4

try:
    from data.tuner import menu_assets
except ImportError:
    from tuner_utils.menu_generator import save_tuner_menu_assets
    save_tuner_menu_assets()
    from data.tuner import menu_assets

ASSETS_MAP = {
    "guitar_6": guitar_6,
    "bass_4": bass_4,
    "bass_5": bass_5,
    "ukulele_4": ukulele_4,
}

THEME_STYLES = {
    "green": {
        "glow": (0.18, 0.88, 0.28, 1.0),
        "string_active": (0.20, 0.95, 0.65, 1.0),
    },
    "dark": {
        "glow": (1.0, 0.50, 0.0, 1.0),
        "string_active": (1.0, 0.55, 0.10, 1.0),
    },
    "light": {
        "glow": (0.08, 0.58, 0.30, 1.0),
        "string_active": (0.10, 0.65, 0.35, 1.0),
    },
}


class PegNoteButton(ButtonBehavior, Widget):
    """Студийный триггер-пэд ноты сбоку от колка с неоновым световодом и звуком струны."""

    note_name = StringProperty("")
    display_name = StringProperty("")
    frequency = NumericProperty(0.0)
    string_index = NumericProperty(0)
    is_active = BooleanProperty(False)
    is_pressed = BooleanProperty(False)
    is_playing = BooleanProperty(False)

    _textures_loaded = False
    _well_dark = None
    _up_dark = None
    _down_dark = None
    _well_light = None
    _up_light = None
    _down_light = None

    def __init__(self, note_name, display_name, frequency, string_index, tuning_id="standard_6", theme_name="green", **kwargs):
        super().__init__(**kwargs)
        self.note_name = note_name
        self.display_name = display_name
        self.frequency = frequency
        self.string_index = string_index
        self.tuning_id = tuning_id
        self.theme_name = theme_name
        self._sound = None

        self.size_hint = (None, None)
        self.size = (dp(54), dp(46))

        if not PegNoteButton._textures_loaded:
            def _load_b64(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            PegNoteButton._well_dark = _load_b64(menu_assets.WELL_DARK_B64)
            PegNoteButton._up_dark = _load_b64(menu_assets.KEY_UP_DARK_B64)
            PegNoteButton._down_dark = _load_b64(menu_assets.KEY_DOWN_DARK_B64)

            PegNoteButton._well_light = _load_b64(menu_assets.WELL_LIGHT_B64)
            PegNoteButton._up_light = _load_b64(menu_assets.KEY_UP_LIGHT_B64)
            PegNoteButton._down_light = _load_b64(menu_assets.KEY_DOWN_LIGHT_B64)
            PegNoteButton._textures_loaded = True

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            is_active=self._redraw,
            is_pressed=self._redraw,
        )
        self._redraw()
        Clock.schedule_once(self._load_sound, 0.05)

    def _load_sound(self, dt):
        try:
            tuning_map = {
                "standard_6": "standard", "drop_d": "drop_d", "open_g": "open_g",
                "open_d": "open_d", "dadgad": "dadgad", "half_step_down": "half_step_down",
                "bass_4": "bass_4", "bass_5": "bass_5", "ukulele": "ukulele",
            }
            module_name = tuning_map.get(self.tuning_id, self.tuning_id)
            module = importlib.import_module(f"data.sounds.{module_name}")
            class_name = module_name.title().replace("_", "") + "Sounds"
            sound_class = getattr(module, class_name)
            self._sound = sound_class.get_sound(self.note_name)
        except Exception:
            self._sound = None

    def play_sound(self):
        if self.is_playing or not self._sound:
            return
        try:
            if self._sound.state == "play":
                self._sound.stop()
            self.is_playing = True
            self._sound.play()
            duration = self._sound.length if self._sound.length else 2.0
            Clock.schedule_once(lambda dt: setattr(self, "is_playing", False), duration + 0.1)
        except Exception:
            self.is_playing = False

    def on_press(self):
        Clock.unschedule(self._reset_press_state)
        self.is_pressed = True

    def on_release(self):
        Clock.schedule_once(self._reset_press_state, 0.14)
        super().on_release()

    def _reset_press_state(self, dt):
        self.is_pressed = False

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        is_light = self.theme_name == "light"
        pressed = self.is_pressed
        lit = pressed or self.is_active
        meta = menu_assets.DOWN_META if pressed else menu_assets.UP_META

        style = THEME_STYLES.get(self.theme_name, THEME_STYLES["green"])
        r, g, b, _ = style["glow"]

        well_tex = self._well_light if is_light else self._well_dark
        key_tex = (self._down_light if pressed else self._up_light) if is_light else (self._down_dark if pressed else self._up_dark)

        bx, by = round(self.x), round(self.y)
        btn_w, btn_h = round(self.width), round(self.height)

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
                Color(r, g, b, 0.32)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(2.5))
                Color(min(1.0, r + 0.2), min(1.0, g + 0.2), min(1.0, b + 0.2), 0.96)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.25))
            else:
                Color(r, g, b, 0.24 if is_light else 0.18)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.0))

            # 4. Контрастная буква ноты по центру клавиши
            font_px = max(sp(13), min(sp(17), btn_h * 0.44))
            if lit:
                txt_col = (min(1.0, r + 0.25), min(1.0, g + 0.25), min(1.0, b + 0.25), 1.0)
            else:
                txt_col = (0.18, 0.22, 0.20, 0.92) if is_light else (0.90, 0.93, 0.95, 0.90)

            lbl = CoreLabel(text=self.display_name, font_size=font_px, bold=True, color=txt_col)
            lbl.refresh()
            tex = lbl.texture
            if tex:
                tcx = bx + btn_w * 0.5
                tcy = by + meta["center_y_norm"] * btn_h
                Color(1, 1, 1, 1)
                Rectangle(
                    texture=tex,
                    pos=(round(tcx - tex.width * 0.5), round(tcy - tex.height * 0.5)),
                    size=tex.size,
                )


class StringsOverlay(Widget):
    """Холст для отрисовки и анимации вибрации струн поверх картинки грифа."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pegs_data = []
        self.img_rect = (0, 0, 1, 1)
        self.theme_name = "green"
        self.active_string = -1
        self.vibrations = {}
        self._anim_event = None
        self.bind(pos=self.redraw, size=self.redraw)

    def configure(self, pegs_data, img_rect, theme_name="green"):
        self.pegs_data = pegs_data
        self.img_rect = img_rect
        self.theme_name = theme_name
        self.redraw()

    def pluck_string(self, string_index, amplitude=dp(4.0)):
        self.vibrations[string_index] = {"amp": amplitude, "phase": 0.0}
        if self._anim_event is None:
            self._anim_event = Clock.schedule_interval(self._update_animation, 1.0 / 60.0)

    def _update_animation(self, dt):
        finished = []
        for idx, state in self.vibrations.items():
            state["phase"] += dt * 68.0
            state["amp"] *= math.exp(-dt * 3.0)
            if state["amp"] < 0.15:
                finished.append(idx)

        for idx in finished:
            del self.vibrations[idx]

        self.redraw()

        if not self.vibrations and self._anim_event is not None:
            self._anim_event.cancel()
            self._anim_event = None

    def redraw(self, *args):
        self.canvas.clear()
        if not self.pegs_data:
            return

        ix, iy, iw, ih = self.img_rect
        style = THEME_STYLES.get(self.theme_name, THEME_STYLES["green"])
        total_strings = len(self.pegs_data)

        with self.canvas:
            for peg in self.pegs_data:
                s_idx = peg["string_index"]
                px_norm, py_norm = peg["peg_pos"]
                nx_norm, ny_norm = peg["nut_pos"]

                peg_x = ix + px_norm * iw
                peg_y = iy + py_norm * ih
                nut_x = ix + nx_norm * iw
                nut_y = iy + ny_norm * ih
                bottom_y = iy + dp(1)

                ratio = s_idx / max(1, total_strings - 1)
                thickness = dp(2.1 - 1.0 * ratio)

                is_selected = (s_idx == self.active_string) or (s_idx in self.vibrations)
                if is_selected:
                    Color(*style["string_active"])
                else:
                    if ratio < 0.65:
                        Color(0.84, 0.72, 0.52, 0.92)
                    else:
                        Color(0.88, 0.90, 0.93, 0.92)

                Line(points=[nut_x, nut_y, peg_x, peg_y], width=thickness * 0.9)

                vib = self.vibrations.get(s_idx)
                if vib and vib["amp"] > 0.15:
                    offset = math.sin(vib["phase"]) * vib["amp"]
                    mid_y = (bottom_y + nut_y) * 0.5
                    Line(
                        bezier=[nut_x, bottom_y, nut_x + offset, mid_y, nut_x, nut_y],
                        width=thickness * 1.15,
                    )
                else:
                    Line(points=[nut_x, bottom_y, nut_x, nut_y], width=thickness)


class HeadstockWidget(FloatLayout):
    """Студийная рэковая карточка головы грифа с кнопками-пэдами по бокам и анимацией струн."""

    _bg_dark_tex = None
    _bg_green_tex = None
    _bg_light_tex = None

    def __init__(self, on_note_press=None, theme_name="green", **kwargs):
        super().__init__(**kwargs)
        self.on_note_press = on_note_press
        self.theme_name = theme_name
        self.current_asset_key = "guitar_6"
        self.note_buttons = {}
        self._textures_cache = {}

        if HeadstockWidget._bg_dark_tex is None:
            HeadstockWidget._bg_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.HEADSTOCK_DARK_B64)), ext="png"
            ).texture
            HeadstockWidget._bg_green_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.HEADSTOCK_GREEN_B64)), ext="png"
            ).texture
            HeadstockWidget._bg_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.HEADSTOCK_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._bg_dark_tex,
                pos=self.pos,
                size=self.size,
            )

        self.head_image = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(None, None),
        )
        self.add_widget(self.head_image)

        self.strings_overlay = StringsOverlay(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.add_widget(self.strings_overlay)

        self.left_col = MDBoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(56),
            spacing=dp(10),
        )
        self.add_widget(self.left_col)

        self.right_col = MDBoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(56),
            spacing=dp(10),
        )
        self.add_widget(self.right_col)

        self._update_bg_texture()
        self.bind(pos=self._sync_layout, size=self._sync_layout)
        self.head_image.bind(pos=self._sync_layout, size=self._sync_layout, texture=self._sync_layout)

    def _update_bg_texture(self):
        if self.theme_name == "light":
            self._bg_rect.texture = self._bg_light_tex
        elif self.theme_name == "green":
            self._bg_rect.texture = self._bg_green_tex
        else:
            self._bg_rect.texture = self._bg_dark_tex

    def _get_texture(self, asset_key):
        if asset_key not in self._textures_cache:
            module = ASSETS_MAP[asset_key]
            raw = base64.b64decode(module.PNG_BASE64)
            core_img = CoreImage(io.BytesIO(raw), ext="png")
            self._textures_cache[asset_key] = core_img.texture
        return self._textures_cache[asset_key]

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self._update_bg_texture()
        for btn in self.note_buttons.values():
            btn.set_theme(theme_name)
        self._sync_layout()

    def set_tuning(self, full_notes, display_names, freqs, tuning_id="standard_6", asset_key="guitar_6"):
        if asset_key not in ASSETS_MAP:
            asset_key = "guitar_6"
        self.current_asset_key = asset_key
        module = ASSETS_MAP[asset_key]

        self.left_col.clear_widgets()
        self.right_col.clear_widgets()
        self.note_buttons.clear()
        self.strings_overlay.active_string = -1

        left_pegs = [p for p in module.PEGS_DATA if p["side"] == "left"]
        right_pegs = [p for p in module.PEGS_DATA if p["side"] == "right"]

        for peg in reversed(left_pegs):
            idx = peg["string_index"]
            if idx < len(full_notes):
                btn = self._create_button(full_notes[idx], display_names[idx], freqs[idx], idx, tuning_id)
                self.left_col.add_widget(btn)
                self.note_buttons[idx] = btn

        for peg in right_pegs:
            idx = peg["string_index"]
            if idx < len(full_notes):
                btn = self._create_button(full_notes[idx], display_names[idx], freqs[idx], idx, tuning_id)
                self.right_col.add_widget(btn)
                self.note_buttons[idx] = btn

        has_right = len(self.right_col.children) > 0
        self.right_col.opacity = 1.0 if has_right else 0.0
        self.right_col.disabled = not has_right

        self.head_image.texture = self._get_texture(asset_key)
        self._sync_layout()
        Clock.schedule_once(self._sync_layout, 0)
        Clock.schedule_once(self._sync_layout, 0.05)

    def _create_button(self, full_name, disp_name, freq, string_index, tuning_id):
        btn = PegNoteButton(
            note_name=full_name,
            display_name=disp_name,
            frequency=freq,
            string_index=string_index,
            tuning_id=tuning_id,
            theme_name=self.theme_name,
        )
        btn.bind(on_release=lambda instance: self._handle_button_click(btn))
        return btn

    def _handle_button_click(self, btn):
        btn.play_sound()
        self.strings_overlay.pluck_string(btn.string_index)
        if callable(self.on_note_press):
            self.on_note_press(btn.note_name, btn.frequency)

    def reset_active(self):
        for btn in self.note_buttons.values():
            btn.is_active = False
        self.strings_overlay.active_string = -1
        self.strings_overlay.redraw()

    def set_active_note(self, note_name, pluck=False):
        target_idx = -1
        for idx, btn in self.note_buttons.items():
            active = (btn.note_name == note_name)
            btn.is_active = active
            if active:
                target_idx = idx

        self.strings_overlay.active_string = target_idx
        if pluck and target_idx >= 0:
            self.strings_overlay.pluck_string(target_idx, amplitude=dp(2.5))
        else:
            self.strings_overlay.redraw()

    def _sync_layout(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        module = ASSETS_MAP.get(self.current_asset_key)
        if not module or self.height <= dp(20):
            return

        # Координаты внутренней утопленной ниши консоли (bay_x1=56/960, bay_y1=26/480)
        bay_x = self.x + self.width * (56.0 / 960.0)
        bay_w = self.width * (848.0 / 960.0)
        bay_y = self.y + self.height * (26.0 / 480.0)
        bay_h = self.height * (428.0 / 480.0)
        bay_right = bay_x + bay_w
        bay_top = bay_y + bay_h

        has_right = len(self.right_col.children) > 0

        # Размещаем голову грифа строго внутри утопленной ниши, упирая основание в её нижнюю кромку
        target_h = max(dp(40), bay_h - dp(10))
        target_w = bay_w * (0.64 if has_right else 0.72)
        self.head_image.size = (target_w, target_h)
        self.head_image.center_x = bay_x + bay_w * (0.50 if has_right else 0.56)
        self.head_image.y = bay_y + dp(1)

        norm_w, norm_h = self.head_image.norm_image_size
        img_x = self.head_image.center_x - norm_w * 0.5
        img_y = self.head_image.y
        img_rect = (img_x, img_y, norm_w, norm_h)
        self.strings_overlay.configure(module.PEGS_DATA, img_rect, self.theme_name)

        pegs = module.PEGS_DATA
        if not pegs:
            return

        top_limit = bay_top - dp(8)
        bottom_limit = bay_y + dp(8)
        avail_h = max(dp(96), top_limit - bottom_limit)

        ys = [img_y + p["peg_pos"][1] * norm_h for p in pegs]
        min_y, max_y = min(ys), max(ys)
        pegs_center_y = (min_y + max_y) * 0.5

        for col, side_mult in ((self.left_col, -1), (self.right_col, 1)):
            count = len(col.children)
            if count == 0:
                continue

            if count >= 5:
                btn_h = min(dp(34), (avail_h - dp(16)) / 5.0)
                spacing = min(dp(6), max(dp(3), (avail_h - 5 * btn_h) / 4.0))
            elif count == 4:
                btn_h = min(dp(38), (avail_h - dp(18)) / 4.0)
                spacing = min(dp(8), max(dp(4), (avail_h - 4 * btn_h) / 3.0))
            else:
                btn_h = min(dp(44), (avail_h - dp(16)) / 3.0)
                if count > 1:
                    raw_sp = (max_y - min_y) / (count - 1) - btn_h
                    max_sp = (avail_h - count * btn_h) / (count - 1)
                    spacing = max(dp(6), min(raw_sp, max_sp))
                else:
                    spacing = 0

            btn_w = dp(56)
            col.width = btn_w

            for btn in col.children:
                btn.size = (btn_w, btn_h)

            exact_h = count * btn_h + max(0, count - 1) * spacing
            col.spacing = spacing
            col.height = exact_h

            half_h = exact_h * 0.5
            clamped_cy = max(bottom_limit + half_h, min(top_limit - half_h, pegs_center_y))
            col.center_y = clamped_cy

            if side_mult == -1:
                col.x = bay_x + dp(10)
            else:
                col.right = bay_right - dp(10)