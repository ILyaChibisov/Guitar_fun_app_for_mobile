# metronome_utils/pendulum_widget.py
import base64
import io
import math

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, Line, Mesh, PopMatrix, PushMatrix, Rotate
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget

from data.metronome import classic_graphite


class PendulumOverlay(Widget):
    """Динамический слой: светящаяся шкала, шток маятника, грузик и ось."""

    angle = NumericProperty(0.0)
    bpm_value = NumericProperty(120)
    is_running = BooleanProperty(False)
    accent_color = ListProperty([1.0, 0.72, 0.25, 1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.img_rect = (0, 0, 1, 1)
        self.meta = classic_graphite.META_DATA
        self.bind(
            pos=self.redraw,
            size=self.redraw,
            angle=self.redraw,
            bpm_value=self.redraw,
            accent_color=self.redraw,
            is_running=self.redraw,
        )

    def set_img_rect(self, img_rect):
        self.img_rect = img_rect
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        ix, iy, iw, ih = self.img_rect
        if iw <= 4 or ih <= 4:
            return

        px_norm, py_norm = self.meta["pivot"]
        sy_min_norm, sy_max_norm = self.meta["scale_y_range"]
        rod_len_norm = self.meta["rod_length_norm"]

        pivot_x = ix + px_norm * iw
        pivot_y = iy + py_norm * ih
        scale_y_min = iy + sy_min_norm * ih
        scale_y_max = iy + sy_max_norm * ih
        rod_len = rod_len_norm * ih

        # Пропорциональный коэффициент масштаба относительно базовой ширины 560px
        sc = iw / 560.0

        r, g, b, _ = self.accent_color
        glow_alpha = 0.28 if self.is_running else 0.16
        core_alpha = 0.95 if self.is_running else 0.72

        with self.canvas:
            # 1. СВЕТЯЩАЯСЯ ЦЕНТРАЛЬНАЯ ШКАЛА (как на референсе)
            Color(r, g, b, glow_alpha * 0.55)
            Line(points=[pivot_x, scale_y_min, pivot_x, scale_y_max], width=max(3.5, 9.0 * sc))

            Color(r, g, b, glow_alpha)
            Line(points=[pivot_x, scale_y_min, pivot_x, scale_y_max], width=max(2.0, 5.0 * sc))

            Color(min(1.0, r + 0.25), min(1.0, g + 0.25), min(1.0, b + 0.25), core_alpha)
            Line(points=[pivot_x, scale_y_min, pivot_x, scale_y_max], width=max(1.1, 1.8 * sc))

            # Деления шкалы (11 рисок)
            ticks = 11
            for i in range(ticks):
                t = i / (ticks - 1)
                ty = scale_y_min + t * (scale_y_max - scale_y_min)
                half_tick = (11.0 if i % 2 == 0 else 7.5) * sc

                Color(r, g, b, glow_alpha)
                Line(points=[pivot_x - half_tick, ty, pivot_x + half_tick, ty], width=max(2.2, 4.2 * sc))

                Color(min(1.0, r + 0.3), min(1.0, g + 0.3), min(1.0, b + 0.3), core_alpha)
                Line(points=[pivot_x - half_tick, ty, pivot_x + half_tick, ty], width=max(1.0, 1.4 * sc))

            # 2. ВРАЩАЮЩИЙСЯ МАЯТНИК (шток + скользящий грузик)
            PushMatrix()
            Rotate(angle=-self.angle, origin=(pivot_x, pivot_y))

            rod_w = max(2.2, 5.6 * sc)
            rod_top_y = pivot_y + rod_len

            # Мягкая тень от штока на заднюю стенку
            Color(0.0, 0.0, 0.0, 0.45)
            Line(points=[pivot_x + 4 * sc, pivot_y, pivot_x + 4 * sc, rod_top_y], width=rod_w * 1.15, cap="round")

            # Основной стальной шток (тёмная основа + светлая грань + блик)
            Color(0.32, 0.35, 0.39, 1.0)
            Line(points=[pivot_x, pivot_y, pivot_x, rod_top_y], width=rod_w, cap="round")

            Color(0.76, 0.80, 0.85, 1.0)
            Line(points=[pivot_x - rod_w * 0.14, pivot_y, pivot_x - rod_w * 0.14, rod_top_y], width=rod_w * 0.58, cap="round")

            Color(0.97, 0.98, 1.0, 0.95)
            Line(points=[pivot_x - rod_w * 0.24, pivot_y + 8 * sc, pivot_x - rod_w * 0.24, rod_top_y - 2 * sc], width=max(0.8, rod_w * 0.22), cap="round")

            # Позиция грузика вдоль штока: 30 BPM -> верх (0.76), 250 BPM -> низ (0.24)
            bpm_pct = max(0.0, min(1.0, (self.bpm_value - 30.0) / (250.0 - 30.0)))
            weight_y = pivot_y + rod_len * (0.76 - bpm_pct * 0.52)

            w_top = 34.0 * sc
            w_bot = 28.0 * sc
            w_h = 46.0 * sc
            wy1 = weight_y - w_h * 0.5
            wy2 = weight_y + w_h * 0.5

            # Тень под грузиком
            sh_off_x = 5.0 * sc
            sh_off_y = -6.0 * sc
            Color(0.0, 0.0, 0.0, 0.52)
            Mesh(
                vertices=[
                    pivot_x - w_bot * 0.5 + sh_off_x, wy1 + sh_off_y, 0, 0,
                    pivot_x + w_bot * 0.5 + sh_off_x, wy1 + sh_off_y, 0, 0,
                    pivot_x + w_top * 0.5 + sh_off_x, wy2 + sh_off_y, 0, 0,
                    pivot_x - w_top * 0.5 + sh_off_x, wy2 + sh_off_y, 0, 0,
                ],
                indices=[0, 1, 2, 2, 3, 0],
                mode="triangles",
            )

            # Корпус грузика (матовый графит с фаской)
            Color(0.18, 0.19, 0.21, 1.0)
            Mesh(
                vertices=[
                    pivot_x - w_bot * 0.5, wy1, 0, 0,
                    pivot_x + w_bot * 0.5, wy1, 0, 0,
                    pivot_x + w_top * 0.5, wy2, 0, 0,
                    pivot_x - w_top * 0.5, wy2, 0, 0,
                ],
                indices=[0, 1, 2, 2, 3, 0],
                mode="triangles",
            )

            # Левый световой блик и верхняя фаска грузика
            Color(0.42, 0.45, 0.50, 0.85)
            Line(
                points=[
                    pivot_x - w_bot * 0.5, wy1,
                    pivot_x - w_top * 0.5, wy2,
                    pivot_x + w_top * 0.5, wy2,
                ],
                width=max(1.0, 1.6 * sc),
            )

            # Тонкая индикаторная риска по центру грузика в цвет темы
            Color(r, g, b, 0.9)
            Line(
                points=[pivot_x - w_bot * 0.36, weight_y, pivot_x + w_bot * 0.36, weight_y],
                width=max(1.0, 1.5 * sc),
            )

            PopMatrix()

            # 3. НИЖНИЙ ШАРНИР (заглушка оси)
            r_cap = 17.5 * sc
            Color(0.0, 0.0, 0.0, 0.55)
            Ellipse(pos=(pivot_x - r_cap + 2 * sc, pivot_y - r_cap - 4 * sc), size=(r_cap * 2, r_cap * 2))

            Color(0.24, 0.26, 0.29, 1.0)
            Ellipse(pos=(pivot_x - r_cap, pivot_y - r_cap), size=(r_cap * 2, r_cap * 2))

            Color(0.48, 0.51, 0.56, 0.75)
            Line(circle=(pivot_x, pivot_y, r_cap - 1.0 * sc), width=max(1.0, 1.4 * sc))

            r_inner = r_cap * 0.72
            Color(0.14, 0.15, 0.17, 1.0)
            Ellipse(pos=(pivot_x - r_inner, pivot_y - r_inner), size=(r_inner * 2, r_inner * 2))


class MetronomePendulumWidget(FloatLayout):
    """Готовый виджет метронома: PNG-корпус + 60 FPS маятник с плавной физикой."""

    bpm_value = NumericProperty(120)
    is_running = BooleanProperty(False)
    pendulum_color = ListProperty([1.0, 0.72, 0.25, 1.0])
    angle = NumericProperty(0.0)

    MAX_ANGLE = 27.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._phase = 0.0
        self._direction = 1.0
        self._anim_event = None
        self._stop_anim = None

        raw = base64.b64decode(classic_graphite.PNG_BASE64)
        tex = CoreImage(io.BytesIO(raw), ext="png").texture

        self.body_image = Image(
            texture=tex,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(1.0, 1.0),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.add_widget(self.body_image)

        self.overlay = PendulumOverlay(size_hint=(1.0, 1.0), pos_hint={"x": 0, "y": 0})
        self.add_widget(self.overlay)

        self.bind(
            pos=self._sync_geometry,
            size=self._sync_geometry,
            bpm_value=self._on_bpm_updated,
            pendulum_color=self._on_color_updated,
            angle=self._on_angle_updated,
        )
        self.body_image.bind(pos=self._sync_geometry, size=self._sync_geometry, texture=self._sync_geometry)

    def _sync_geometry(self, *args):
        norm_w, norm_h = self.body_image.norm_image_size
        img_x = self.body_image.center_x - norm_w * 0.5
        img_y = self.body_image.center_y - norm_h * 0.5
        self.overlay.set_img_rect((img_x, img_y, norm_w, norm_h))

    def _on_bpm_updated(self, instance, value):
        self.overlay.bpm_value = value

    def _on_color_updated(self, instance, value):
        self.overlay.accent_color = value

    def _on_angle_updated(self, instance, value):
        self.overlay.angle = value

    def start(self):
        if self._stop_anim:
            self._stop_anim.cancel(self)
            self._stop_anim = None
        self.is_running = True
        self.overlay.is_running = True
        # Стартуем с крайней точки (-MAX_ANGLE), чтобы первый удар совпал с пиком
        self._phase = -math.pi * 0.5
        self.angle = -self.MAX_ANGLE
        if self._anim_event is None:
            self._anim_event = Clock.schedule_interval(self._update_swing, 1.0 / 60.0)

    def stop(self):
        self.is_running = False
        self.overlay.is_running = False
        if self._anim_event is not None:
            self._anim_event.cancel()
            self._anim_event = None
        self._stop_anim = Animation(angle=0.0, duration=0.22, transition="out_quad")
        self._stop_anim.start(self)

    def sync_beat(self, beat_index):
        """Мягко подравнивает фазу маятника к крайним точкам на каждый основной удар."""
        if not self.is_running:
            return
        # Чётные доли -> левая крайняя точка (-pi/2), нечётные -> правая (+pi/2)
        target_phase = -math.pi * 0.5 if (beat_index % 2 == 0) else math.pi * 0.5
        self._phase = target_phase

    def _update_swing(self, dt):
        if not self.is_running:
            return
        # За один полупериод (60 / bpm сек) фаза проходит pi радиан (от -pi/2 до +pi/2)
        omega = math.pi * (self.bpm_value / 60.0)
        self._phase += omega * dt
        self.angle = math.sin(self._phase) * self.MAX_ANGLE

