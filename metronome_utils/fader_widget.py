# metronome_utils/fader_widget.py
import base64
import io

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from data.metronome import fader_assets
from state.settings_state import settings_state as settings_manager


class FaderTrackArea(Widget):
    """Интерактивная область трека с рендерингом паза, индикатора и 3D-ползунка."""

    value = NumericProperty(0.0)
    min_value = NumericProperty(0.0)
    max_value = NumericProperty(100.0)
    step = NumericProperty(1.0)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    _track_tex = None
    _track_light_tex = None
    _knob_tex = None
    _knob_light_tex = None

    def __init__(self, on_change=None, **kwargs):
        super().__init__(**kwargs)
        self.on_change = on_change
        self._dragging = False
        self._knob_bounds = (0, 0, 0, 0)

        if FaderTrackArea._track_tex is None:
            raw_t = base64.b64decode(fader_assets.TRACK_PNG_BASE64)
            FaderTrackArea._track_tex = CoreImage(io.BytesIO(raw_t), ext="png").texture

            raw_tl = base64.b64decode(fader_assets.TRACK_LIGHT_B64)
            FaderTrackArea._track_light_tex = CoreImage(io.BytesIO(raw_tl), ext="png").texture

            raw_k = base64.b64decode(fader_assets.KNOB_PNG_BASE64)
            FaderTrackArea._knob_tex = CoreImage(io.BytesIO(raw_k), ext="png").texture

            raw_kl = base64.b64decode(fader_assets.KNOB_LIGHT_B64)
            FaderTrackArea._knob_light_tex = CoreImage(io.BytesIO(raw_kl), ext="png").texture

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            value=self.update_canvas,
            min_value=self.update_canvas,
            max_value=self.update_canvas,
            accent_color=self.update_canvas,
        )

    def _norm(self):
        span = float(self.max_value - self.min_value)
        if span <= 0:
            return 0.0
        return max(0.0, min(1.0, (float(self.value) - float(self.min_value)) / span))

    def _set_from_touch_y(self, touch_y):
        tw, th = fader_assets.TRACK_SIZE
        aspect = tw / th
        track_h = self.height
        track_w = track_h * aspect
        if track_w > self.width:
            track_w = self.width
            track_h = track_w / aspect

        ty = self.center_y - track_h * 0.5
        y_min_norm, y_max_norm = fader_assets.TRACK_META["travel_y_norm"]
        y_bottom = ty + y_min_norm * track_h
        y_top = ty + y_max_norm * track_h

        travel = y_top - y_bottom
        if travel <= 1:
            return

        norm = max(0.0, min(1.0, (touch_y - y_bottom) / travel))
        raw_val = self.min_value + norm * (self.max_value - self.min_value)

        if self.step > 0:
            steps = round((raw_val - self.min_value) / self.step)
            new_val = self.min_value + steps * self.step
        else:
            new_val = raw_val

        new_val = max(self.min_value, min(self.max_value, new_val))
        if isinstance(self.step, int) and isinstance(self.min_value, int):
            new_val = int(round(new_val))
        else:
            new_val = round(new_val, 2)

        if new_val != self.value:
            self.value = new_val
            if self.on_change:
                self.on_change(self.value)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        self._dragging = True
        self._set_from_touch_y(touch.y)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self._set_from_touch_y(touch.y)
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._dragging = False
            self.update_canvas()
            return True
        return False

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 2 or self.height <= 2:
            return

        is_light = (settings_manager.theme == "light")
        track_tex = self._track_light_tex if is_light else self._track_tex
        knob_tex = self._knob_light_tex if is_light else self._knob_tex

        tw_src, th_src = fader_assets.TRACK_SIZE
        aspect = tw_src / th_src

        track_h = self.height
        track_w = track_h * aspect
        if track_w > self.width:
            track_w = self.width
            track_h = track_w / aspect

        tx = self.center_x - track_w * 0.5
        ty = self.center_y - track_h * 0.5

        sx1_n, sx2_n = fader_assets.TRACK_META["slot_x_norm"]
        sy1_n, sy2_n = fader_assets.TRACK_META["slot_y_norm"]
        ty1_n, ty2_n = fader_assets.TRACK_META["travel_y_norm"]

        slot_x = tx + sx1_n * track_w
        slot_w = (sx2_n - sx1_n) * track_w
        slot_bottom = ty + sy1_n * track_h

        travel_bottom = ty + ty1_n * track_h
        travel_top = ty + ty2_n * track_h

        norm = self._norm()
        knob_center_y = travel_bottom + norm * (travel_top - travel_bottom)

        r, g, b, _ = self.accent_color

        with self.canvas:
            # 1. Текстура паза трека с рисками шкалы
            Color(1, 1, 1, 1)
            Rectangle(texture=track_tex, pos=(tx, ty), size=(track_w, track_h))

            # 2. Неоновая полоска заполнения внутри паза до положения ручки
            fill_top = max(slot_bottom + slot_w * 0.5, knob_center_y)
            fill_h = fill_top - slot_bottom
            if fill_h > dp(2) and norm > 0.001:
                pad = slot_w * 0.22
                fx = slot_x + pad
                fw = max(dp(2), slot_w - pad * 2)
                fy = slot_bottom + pad
                fh = max(dp(2), fill_h - pad)

                Color(r, g, b, 0.35)
                RoundedRectangle(
                    pos=(fx - dp(1.5), fy),
                    size=(fw + dp(3), fh),
                    radius=[fw * 0.5],
                )
                Color(r, g, b, 0.92)
                RoundedRectangle(
                    pos=(fx, fy),
                    size=(fw, fh),
                    radius=[fw * 0.5],
                )
                Color(min(1.0, r + 0.35), min(1.0, g + 0.35), min(1.0, b + 0.35), 0.70)
                RoundedRectangle(
                    pos=(fx + fw * 0.28, fy + dp(1)),
                    size=(max(dp(1), fw * 0.35), max(dp(1), fh - dp(2))),
                    radius=[fw * 0.2],
                )

            # 3. Металлический ползунок (ручка фейдера)
            kw_src, kh_src = fader_assets.KNOB_SIZE
            knob_w = track_w * (kw_src / tw_src)
            knob_h = knob_w * (kh_src / kw_src)
            knob_center_norm = fader_assets.KNOB_META["knob_center_y_norm"]

            kx = self.center_x - knob_w * 0.5
            ky = knob_center_y - knob_center_norm * knob_h
            self._knob_bounds = (kx, ky, knob_w, knob_h)

            Color(1, 1, 1, 1)
            Rectangle(texture=knob_tex, pos=(kx, ky), size=(knob_w, knob_h))

            # 4. Светящийся LED-индикатор в центре ручки
            lx_n, ly_n, lw_n, lh_n = fader_assets.KNOB_META["led_box_norm"]
            led_x = kx + lx_n * knob_w
            led_y = ky + ly_n * knob_h
            led_w = lw_n * knob_w
            led_h = lh_n * knob_h

            glow_alpha = 0.50 if self._dragging else 0.30
            Color(r, g, b, glow_alpha)
            Ellipse(
                pos=(led_x - dp(3), led_y - dp(2)),
                size=(led_w + dp(6), led_h + dp(4)),
            )

            Color(min(1.0, r + 0.15), min(1.0, g + 0.15), min(1.0, b + 0.15), 1.0)
            RoundedRectangle(
                pos=(led_x, led_y),
                size=(led_w, led_h),
                radius=[dp(1.5)],
            )


class StudioVerticalSlider(BoxLayout):
    """Готовый вертикальный студийный фейдер: значение сверху, шкала с ползунком, подпись снизу."""

    value = NumericProperty(0)
    min_value = NumericProperty(0)
    max_value = NumericProperty(100)
    step = NumericProperty(1)
    label_text = StringProperty("")
    value_text = StringProperty("")

    def __init__(
        self,
        label_text="",
        min_value=0,
        max_value=100,
        initial=50,
        step=1,
        on_value_change=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (None, 1)
        self.width = dp(64)
        self.spacing = dp(2)
        self.padding = [0, dp(2), 0, dp(2)]

        self.label_text = label_text
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.value = initial
        self._callback = on_value_change

        self.value_label = Label(
            text=str(initial),
            font_size=sp(14),
            bold=True,
            size_hint=(1, None),
            height=dp(24),
            halign="center",
            valign="middle",
        )
        self.value_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))

        self.track = FaderTrackArea(
            min_value=min_value,
            max_value=max_value,
            value=initial,
            step=step,
            on_change=self._on_track_change,
        )

        self.title_label = Label(
            text=label_text,
            font_size=sp(13),
            bold=True,
            size_hint=(1, None),
            height=dp(22),
            halign="center",
            valign="middle",
        )
        self.title_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))

        self.add_widget(self.value_label)
        self.add_widget(self.track)
        self.add_widget(self.title_label)

        self.bind(value=self._sync_from_prop, value_text=self._sync_text_prop)
        self.update_theme_colors()

    @staticmethod
    def _get_theme_accent(theme_id):
        if theme_id == "light":
            return [0.10, 0.58, 0.32, 1.0]
        elif theme_id == "dark":
            return [1.0, 0.50, 0.0, 1.0]
        return [0.18, 0.88, 0.28, 1.0]

    @staticmethod
    def _get_labels_color(theme_id):
        """Цвет показаний сверху и названий шкал снизу (тёмный для светлой темы)."""
        if theme_id == "light":
            return [0.13, 0.16, 0.18, 1.0]
        elif theme_id == "dark":
            return [1.0, 0.55, 0.08, 1.0]
        return [0.94, 0.98, 0.95, 0.96]

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = self._get_theme_accent(theme_id)
        lbl_col = self._get_labels_color(theme_id)
        self.track.accent_color = accent
        self.track.update_canvas()
        self.value_label.color = lbl_col
        self.title_label.color = lbl_col

    def _on_track_change(self, val):
        self.value = val
        if not self.value_text:
            self.value_label.text = str(val)
        if self._callback:
            self._callback(self, val)

    def set_value(self, new_value):
        new_value = max(self.min_value, min(self.max_value, new_value))
        if self.step > 0:
            steps = round((new_value - self.min_value) / self.step)
            new_value = self.min_value + steps * self.step
        if isinstance(self.step, int) and isinstance(self.min_value, int):
            new_value = int(round(new_value))
        self.value = new_value
        self.track.value = new_value
        if not self.value_text:
            self.value_label.text = str(new_value)

    def set_display_text(self, text):
        self.value_text = str(text)
        self.value_label.text = str(text)

    def _sync_from_prop(self, inst, val):
        if self.track.value != val:
            self.track.value = val
        if not self.value_text:
            self.value_label.text = str(val)

    def _sync_text_prop(self, inst, text):
        if text:
            self.value_label.text = str(text)