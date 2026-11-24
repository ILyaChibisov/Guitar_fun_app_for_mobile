# metronome_utils/fader_widget.py
import base64
import io

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from data.metronome import fader_assets
from state.settings_state import settings_state as settings_manager


class _FaderTrackCanvas(Widget):
    """Внутренний холст с PNG-треком, неоновой шкалой и 3D-ручкой."""

    value = NumericProperty(120)
    min_value = NumericProperty(30)
    max_value = NumericProperty(250)
    step = NumericProperty(1)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    _track_tex = None
    _knob_tex = None

    def __init__(self, on_value_change=None, **kwargs):
        super().__init__(**kwargs)
        self.on_value_change = on_value_change
        self.is_dragging = False
        self._travel_y1 = 0.0
        self._travel_y2 = 1.0

        if _FaderTrackCanvas._track_tex is None:
            raw_t = base64.b64decode(fader_assets.TRACK_PNG_BASE64)
            _FaderTrackCanvas._track_tex = CoreImage(io.BytesIO(raw_t), ext="png").texture

        if _FaderTrackCanvas._knob_tex is None:
            raw_k = base64.b64decode(fader_assets.KNOB_PNG_BASE64)
            _FaderTrackCanvas._knob_tex = CoreImage(io.BytesIO(raw_k), ext="png").texture

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            value=self.update_canvas,
            accent_color=self.update_canvas,
        )

    def _get_percentage(self):
        span = max(1e-6, self.max_value - self.min_value)
        return max(0.0, min(1.0, (self.value - self.min_value) / span))

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        tw_src, th_src = fader_assets.TRACK_SIZE
        kw_src, kh_src = fader_assets.KNOB_SIZE
        t_meta = fader_assets.TRACK_META
        k_meta = fader_assets.KNOB_META

        # Растягиваем шкалу на всю доступную высоту колонки
        track_h = self.height
        track_w = track_h * (tw_src / th_src)
        if track_w > self.width * 1.18:
            track_w = self.width * 1.18
            track_h = track_w * (th_src / tw_src)

        tx = self.center_x - track_w * 0.5
        ty = self.center_y - track_h * 0.5

        sx1_n, sx2_n = t_meta["slot_x_norm"]
        sy1_n, sy2_n = t_meta["slot_y_norm"]
        ty1_n, ty2_n = t_meta["travel_y_norm"]

        slot_x = tx + sx1_n * track_w
        slot_w = (sx2_n - sx1_n) * track_w
        slot_y1 = ty + sy1_n * track_h
        slot_y2 = ty + sy2_n * track_h

        self._travel_y1 = ty + ty1_n * track_h
        self._travel_y2 = ty + ty2_n * track_h

        pct = self._get_percentage()
        knob_center_y = self._travel_y1 + pct * (self._travel_y2 - self._travel_y1)

        scale = track_w / tw_src
        knob_w = kw_src * scale
        knob_h = kh_src * scale
        knob_x = self.center_x - knob_w * 0.5
        knob_y = knob_center_y - k_meta["knob_center_y_norm"] * knob_h

        r, g, b, _ = self.accent_color
        fill_top = max(slot_y1, knob_center_y)
        fill_h = max(0.0, fill_top - slot_y1)
        slot_rad = slot_w * 0.5

        with self.canvas:
            # 1. Текстура утопленного паза и боковых рисок
            Color(1, 1, 1, 1)
            Rectangle(texture=self._track_tex, pos=(tx, ty), size=(track_w, track_h))

            # 2. Светящаяся цветная полоса снизу до ручки
            if fill_h > dp(2):
                Color(r, g, b, 0.25)
                RoundedRectangle(
                    pos=(slot_x - dp(1.5), slot_y1),
                    size=(slot_w + dp(3), fill_h),
                    radius=[slot_rad],
                )
                Color(r, g, b, 0.96)
                RoundedRectangle(
                    pos=(slot_x + dp(1), slot_y1 + dp(1)),
                    size=(max(dp(2), slot_w - dp(2)), max(dp(2), fill_h - dp(1))),
                    radius=[slot_rad * 0.85],
                )
                Color(min(1.0, r + 0.32), min(1.0, g + 0.32), min(1.0, b + 0.32), 0.65)
                RoundedRectangle(
                    pos=(slot_x + slot_w * 0.32, slot_y1 + dp(2)),
                    size=(slot_w * 0.36, max(dp(2), fill_h - dp(3))),
                    radius=[slot_rad * 0.4],
                )

            # 3. Металлическая 3D-ручка
            Color(1, 1, 1, 1)
            Rectangle(texture=self._knob_tex, pos=(knob_x, knob_y), size=(knob_w, knob_h))

            # 4. Светящийся светодиод в центре ручки
            lx_n, ly_n, lw_n, lh_n = k_meta["led_box_norm"]
            led_x = knob_x + lx_n * knob_w
            led_y = knob_y + ly_n * knob_h
            led_w = lw_n * knob_w
            led_h = lh_n * knob_h

            Color(r, g, b, 0.35)
            RoundedRectangle(
                pos=(led_x - dp(2), led_y - dp(2)),
                size=(led_w + dp(4), led_h + dp(4)),
                radius=[dp(3)],
            )
            Color(min(1.0, r + 0.2), min(1.0, g + 0.2), min(1.0, b + 0.2), 1.0)
            RoundedRectangle(
                pos=(led_x, led_y),
                size=(led_w, led_h),
                radius=[dp(2)],
            )

    def _y_to_value(self, touch_y):
        span_px = max(1.0, self._travel_y2 - self._travel_y1)
        pct = max(0.0, min(1.0, (touch_y - self._travel_y1) / span_px))
        raw = self.min_value + pct * (self.max_value - self.min_value)
        stepped = round(raw / self.step) * self.step
        return max(self.min_value, min(self.max_value, int(stepped)))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_dragging = True
            new_val = self._y_to_value(touch.y)
            if new_val != self.value:
                self.value = new_val
                if self.on_value_change:
                    self.on_value_change(self, new_val)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.is_dragging:
            new_val = self._y_to_value(touch.y)
            if new_val != self.value:
                self.value = new_val
                if self.on_value_change:
                    self.on_value_change(self, new_val)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.is_dragging:
            self.is_dragging = False
            return True
        return super().on_touch_up(touch)


class StudioVerticalSlider(MDBoxLayout):
    """Колонка студийного фейдера: значение сверху, удлинённая шкала и название снизу."""

    value = NumericProperty(60)
    min_value = NumericProperty(30)
    max_value = NumericProperty(240)
    step = NumericProperty(1)

    def __init__(self, label_text="BPM", min_value=30, max_value=240, initial=60, step=1, on_value_change=None, **kwargs):
        super().__init__(**kwargs)
        self.label_text = label_text
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial
        self.step = step
        self._external_callback = on_value_change
        self._custom_text = None

        self.orientation = "vertical"
        self.size_hint = (None, 1)
        self.width = dp(74)
        self.spacing = dp(2)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]

        # Показание шкалы сверху
        self.value_label = MDLabel(
            text=str(int(initial)),
            font_size=sp(17),
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(22),
            theme_text_color="Custom",
            bold=True,
        )
        self.value_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))

        # Удлинённый трек фейдера (занимает всё освободившееся место)
        self.fader = _FaderTrackCanvas(
            value=initial,
            min_value=min_value,
            max_value=max_value,
            step=step,
            size_hint=(1, 1),
            on_value_change=self._handle_fader_change,
        )

        # Название шкалы снизу (BPM, BEAT, SUB, VOL)
        self.label = MDLabel(
            text=label_text,
            font_size=sp(11),
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(18),
            theme_text_color="Custom",
            bold=True,
        )
        self.label.bind(size=lambda inst, val: setattr(inst, "text_size", val))

        self.add_widget(self.value_label)
        self.add_widget(self.fader)
        self.add_widget(self.label)

        self.update_theme_colors()

    @staticmethod
    def _get_fader_glow_color(theme_id):
        """Цвет подсветки самой полосы и светодиода на ручке."""
        if theme_id == "light":
            return [0.1, 0.55, 0.3, 1.0]
        elif theme_id == "dark":
            return [1.0, 0.5, 0.0, 1.0]
        return [0.18, 0.88, 0.28, 1.0]

    @staticmethod
    def _get_labels_color(theme_id):
        """Цвет показаний и названий шкал по темам."""
        if theme_id == "light":
            # На светлой теме — зелёные
            return [0.1, 0.55, 0.3, 1.0]
        elif theme_id == "dark":
            # На тёмной теме — оранжевые
            return [1.0, 0.5, 0.0, 1.0]
        # На зелёной теме — светлые
        return [0.94, 0.98, 0.95, 0.96]

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        glow_color = self._get_fader_glow_color(theme_id)
        labels_color = self._get_labels_color(theme_id)

        self.value_label.text_color = labels_color
        self.label.text_color = labels_color
        self.fader.accent_color = glow_color

    def _handle_fader_change(self, instance, new_val):
        self.value = new_val

        if self._custom_text is None:
            self.value_label.text = str(int(new_val))
        if self._external_callback:
            self._external_callback(self, new_val)

    def set_display_text(self, text):
        self._custom_text = text
        self.value_label.text = str(text)

    def set_value(self, new_value):
        new_value = max(self.min_value, min(self.max_value, new_value))
        rounded = round(new_value / self.step) * self.step
        self.value = rounded
        self.fader.value = rounded
        if self._custom_text is None:
            self.value_label.text = str(int(rounded))

    def get_value(self):
        return self.value