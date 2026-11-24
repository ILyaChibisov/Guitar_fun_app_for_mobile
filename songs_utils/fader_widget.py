# songs_utils/fader_widget.py
import base64
import io

from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.widget import Widget

from data.songs import panel_fader_assets


class SongsPanelFader(Widget):
    """Компактный студийный фейдер для выезжающих панелей песен и словаря."""

    value = NumericProperty(0.0)
    min_value = NumericProperty(-6.0)
    max_value = NumericProperty(6.0)
    step = NumericProperty(1.0)
    accent_color = ListProperty([0.96, 0.78, 0.28, 1.0])

    _track_tex = None
    _knob_tex = None

    def __init__(self, min_value=-6, max_value=6, value=0, step=1, **kwargs):
        super().__init__(**kwargs)
        self.min_value = float(min_value)
        self.max_value = float(max_value)
        self.value = float(value)
        self.step = float(step)
        self.is_dragging = False
        self._travel_y1 = 0.0
        self._travel_y2 = 1.0

        if SongsPanelFader._track_tex is None:
            raw_t = base64.b64decode(panel_fader_assets.TRACK_PNG_BASE64)
            SongsPanelFader._track_tex = CoreImage(io.BytesIO(raw_t), ext="png").texture

        if SongsPanelFader._knob_tex is None:
            raw_k = base64.b64decode(panel_fader_assets.KNOB_PNG_BASE64)
            SongsPanelFader._knob_tex = CoreImage(io.BytesIO(raw_k), ext="png").texture

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

        tw_src, _ = panel_fader_assets.TRACK_SIZE
        kw_src, kh_src = panel_fader_assets.KNOB_SIZE
        t_meta = panel_fader_assets.TRACK_META
        k_meta = panel_fader_assets.KNOB_META

        track_h = self.height
        track_w = min(self.width, dp(46))

        tx = self.center_x - track_w * 0.5
        ty = self.center_y - track_h * 0.5

        sx1_n, sx2_n = t_meta["slot_x_norm"]
        sy1_n, _ = t_meta["slot_y_norm"]
        ty1_n, ty2_n = t_meta["travel_y_norm"]

        slot_x = tx + sx1_n * track_w
        slot_w = (sx2_n - sx1_n) * track_w
        slot_y1 = ty + sy1_n * track_h

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

            # 2. Цветное заполнение снизу до ручки
            if fill_h > dp(1.5):
                Color(r, g, b, 0.28)
                RoundedRectangle(
                    pos=(slot_x - dp(1), slot_y1),
                    size=(slot_w + dp(2), fill_h),
                    radius=[slot_rad],
                )
                Color(r, g, b, 0.96)
                RoundedRectangle(
                    pos=(slot_x + dp(0.6), slot_y1 + dp(0.6)),
                    size=(max(dp(1.5), slot_w - dp(1.2)), max(dp(1.5), fill_h - dp(0.6))),
                    radius=[slot_rad * 0.85],
                )

            # 3. Шлифованная металлическая кнопка
            Color(1, 1, 1, 1)
            Rectangle(texture=self._knob_tex, pos=(knob_x, knob_y), size=(knob_w, knob_h))

            # 4. Светящийся индикатор в центре кнопки
            lx_n, ly_n, lw_n, lh_n = k_meta["led_box_norm"]
            led_x = knob_x + lx_n * knob_w
            led_y = knob_y + ly_n * knob_h
            led_w = lw_n * knob_w
            led_h = lh_n * knob_h

            Color(min(1.0, r + 0.2), min(1.0, g + 0.2), min(1.0, b + 0.2), 1.0)
            RoundedRectangle(
                pos=(led_x, led_y),
                size=(led_w, led_h),
                radius=[dp(1.5)],
            )

    def _y_to_value(self, touch_y):
        span_px = max(1.0, self._travel_y2 - self._travel_y1)
        pct = max(0.0, min(1.0, (touch_y - self._travel_y1) / span_px))
        raw = self.min_value + pct * (self.max_value - self.min_value)
        stepped = round(raw / self.step) * self.step
        return max(self.min_value, min(self.max_value, stepped))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_dragging = True
            self.value = self._y_to_value(touch.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.is_dragging:
            self.value = self._y_to_value(touch.y)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.is_dragging:
            self.is_dragging = False
            return True
        return super().on_touch_up(touch)
