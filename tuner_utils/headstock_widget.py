import base64
import importlib
import io
import math

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from data.grifs import bass_4, bass_5, guitar_6, ukulele_4

ASSETS_MAP = {
    "guitar_6": guitar_6,
    "bass_4": bass_4,
    "bass_5": bass_5,
    "ukulele_4": ukulele_4,
}

THEME_STYLES = {
    "green": {
        "btn_bg": (0.0, 0.0, 0.0, 0.22),
        "btn_border": (0.46, 0.70, 0.71, 0.55),
        "btn_active_bg": (0.46, 0.70, 0.71, 0.85),
        "btn_active_border": (0.65, 0.95, 0.85, 1.0),
        "btn_text": (1.0, 1.0, 1.0, 0.95),
        "btn_active_text": (1.0, 1.0, 1.0, 1.0),
        "string_active": (0.2, 0.95, 0.65, 1.0),
    },
    "dark": {
        "btn_bg": (0.15, 0.15, 0.15, 0.90),
        "btn_border": (1.0, 0.5, 0.0, 0.55),
        "btn_active_bg": (1.0, 0.5, 0.0, 0.85),
        "btn_active_border": (1.0, 0.75, 0.3, 1.0),
        "btn_text": (1.0, 1.0, 1.0, 0.95),
        "btn_active_text": (1.0, 1.0, 1.0, 1.0),
        "string_active": (1.0, 0.55, 0.1, 1.0),
    },
    "light": {
        "btn_bg": (1.0, 1.0, 1.0, 0.95),
        "btn_border": (0.1, 0.55, 0.3, 0.55),
        "btn_active_bg": (0.1, 0.55, 0.3, 0.88),
        "btn_active_border": (0.08, 0.45, 0.24, 1.0),
        "btn_text": (0.1, 0.1, 0.1, 1.0),
        "btn_active_text": (1.0, 1.0, 1.0, 1.0),
        "string_active": (0.1, 0.65, 0.35, 1.0),
    },
}


class PegNoteButton(ButtonBehavior, MDBoxLayout):
    """Кнопка ноты сбоку от колка с воспроизведением эталонного звука."""

    note_name = StringProperty("")
    display_name = StringProperty("")
    frequency = NumericProperty(0.0)
    string_index = NumericProperty(0)
    is_active = BooleanProperty(False)
    is_playing = BooleanProperty(False)

    def __init__(self, note_name, display_name, frequency, string_index, tuning_id="standard_6", theme_name="green", **kwargs):
        super().__init__(**kwargs)
        self.note_name = note_name
        self.display_name = display_name
        self.frequency = frequency
        self.string_index = string_index
        self.tuning_id = tuning_id
        self.theme_name = theme_name
        self._sound = None

        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.size = (dp(48), dp(42))
        self.padding = [dp(4), dp(2)]

        self.label = MDLabel(
            text=display_name,
            halign="center",
            valign="middle",
            font_size=sp(16),
            bold=True,
        )
        self.add_widget(self.label)

        self.bind(pos=self._redraw, size=self._redraw, is_active=self._redraw)
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

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self._redraw()

    def _redraw(self, *args):
        style = THEME_STYLES.get(self.theme_name, THEME_STYLES["green"])
        bg = style["btn_active_bg"] if self.is_active else style["btn_bg"]
        border = style["btn_active_border"] if self.is_active else style["btn_border"]
        self.label.theme_text_color = "Custom"
        self.label.text_color = style["btn_active_text"] if self.is_active else style["btn_text"]

        self.canvas.before.clear()
        with self.canvas.before:
            Color(*bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(11)] * 4)
            Color(*border)
            Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(11)),
                width=dp(1.5) if self.is_active else dp(1.2),
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
                bottom_y = iy + dp(2)

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
    """Виджет головы грифа с кнопками нот по бокам и анимацией струн."""

    def __init__(self, on_note_press=None, theme_name="green", **kwargs):
        super().__init__(**kwargs)
        self.on_note_press = on_note_press
        self.theme_name = theme_name
        self.current_asset_key = "guitar_6"
        self.note_buttons = {}
        self._textures_cache = {}

        self.head_image = Image(
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.76, 0.94),
            pos_hint={"center_x": 0.5, "y": 0.02},
        )

        self.add_widget(self.head_image)

        self.strings_overlay = StringsOverlay(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        self.add_widget(self.strings_overlay)

        self.left_col = MDBoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(50),
            spacing=dp(12),
        )
        self.add_widget(self.left_col)

        self.right_col = MDBoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(50),
            spacing=dp(12),
        )
        self.add_widget(self.right_col)

        # Жесткая привязка перерисовки струн и кнопок к реальным координатам картинки
        self.bind(pos=self._sync_layout, size=self._sync_layout)
        self.head_image.bind(pos=self._sync_layout, size=self._sync_layout, texture=self._sync_layout)

    def _get_texture(self, asset_key):
        if asset_key not in self._textures_cache:
            module = ASSETS_MAP[asset_key]
            raw = base64.b64decode(module.PNG_BASE64)
            core_img = CoreImage(io.BytesIO(raw), ext="png")
            self._textures_cache[asset_key] = core_img.texture
        return self._textures_cache[asset_key]

    def set_theme(self, theme_name):
        self.theme_name = theme_name
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

        # Обновляем pos_hint ДО смены текстуры, чтобы Kivy сразу пересчитал геометрию
        self.head_image.pos_hint = {"center_x": 0.50 if has_right else 0.55, "y": 0.02}
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
        module = ASSETS_MAP.get(self.current_asset_key)
        if not module or self.height <= dp(20):
            return

        has_right = len(self.right_col.children) > 0

        # Вычисляем точный прямоугольник отрисованной текстуры внутри self.head_image
        norm_w, norm_h = self.head_image.norm_image_size
        img_x = self.head_image.center_x - norm_w * 0.5
        img_y = self.head_image.center_y - norm_h * 0.5
        img_rect = (img_x, img_y, norm_w, norm_h)

        self.strings_overlay.configure(module.PEGS_DATA, img_rect, self.theme_name)

        pegs = module.PEGS_DATA
        if not pegs:
            return

        # Жесткие границы внутри виджета, чтобы кнопки НИКОГДА не наползали на верхнее меню
        top_limit = self.top - dp(10)
        bottom_limit = self.y + dp(8)
        avail_h = max(dp(110), top_limit - bottom_limit)

        ys = [img_y + p["peg_pos"][1] * norm_h for p in pegs]
        min_y, max_y = min(ys), max(ys)
        pegs_center_y = (min_y + max_y) * 0.5

        for col, side_mult in ((self.left_col, -1), (self.right_col, 1)):
            count = len(col.children)
            if count == 0:
                continue

            # Подбираем высоту кнопки и интервал строго под доступную высоту
            if count >= 5:
                btn_h = min(dp(34), (avail_h - dp(16)) / 5.0)
                spacing = min(dp(7), max(dp(3), (avail_h - 5 * btn_h) / 4.0))
            elif count == 4:
                btn_h = min(dp(38), (avail_h - dp(18)) / 4.0)
                spacing = min(dp(10), max(dp(4), (avail_h - 4 * btn_h) / 3.0))
            else:
                btn_h = dp(42)
                if count > 1:
                    raw_sp = (max_y - min_y) / (count - 1) - btn_h
                    max_sp = (avail_h - count * btn_h) / (count - 1)
                    spacing = max(dp(8), min(raw_sp, max_sp))
                else:
                    spacing = 0

            for btn in col.children:
                btn.size = (dp(48), btn_h)

            exact_h = count * btn_h + max(0, count - 1) * spacing
            col.spacing = spacing
            col.height = exact_h

            # Центрируем по колкам, но зажимаем внутри [bottom_limit, top_limit]
            half_h = exact_h * 0.5
            clamped_cy = max(bottom_limit + half_h, min(top_limit - half_h, pegs_center_y))
            col.center_y = clamped_cy

            if side_mult == -1:
                col.right = max(self.x + dp(52), img_x - dp(6))
            else:
                col.x = min(self.right - dp(52), img_x + norm_w + dp(6))