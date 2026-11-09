from kivy.animation import Animation
from kivy.graphics import Color, Line, Triangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Triangle
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
import math
Window.size = (390, 820)

KV = '''
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<TunerScreenDesign>:
    md_bg_color: 0.06, 0.05, 0.11, 1

    MDBoxLayout:
        orientation: 'vertical'
        spacing: dp(14)
        padding: [0, 0, 0, dp(16)]

        # 1. ВЕРХНЯЯ ПАНЕЛЬ (Header)
        MDCard:
            size_hint_y: None
            height: dp(76)
            radius: [0, 0, dp(22), dp(22)]
            md_bg_color: 0.36, 0.25, 0.72, 1
            elevation: 0
            padding: [dp(16), dp(12), dp(12), dp(12)]
            spacing: dp(12)

            MDCard:
                size_hint: None, None
                size: dp(44), dp(44)
                radius: [dp(22)]
                md_bg_color: 1, 1, 1, 0.18
                elevation: 0
                pos_hint: {"center_y": 0.5}

                MDIcon:
                    icon: "music-note"
                    halign: "center"
                    valign: "center"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

            MDBoxLayout:
                orientation: 'vertical'
                pos_hint: {"center_y": 0.5}
                spacing: dp(2)

                MDLabel:
                    text: "GUITAR TUNER"
                    font_style: "Subtitle1"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1

                MDLabel:
                    text: "Chromatic Tuner"
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: 0.85, 0.85, 0.95, 0.8

            Widget:
                size_hint: None, None
                size: dp(10), dp(10)
                pos_hint: {"center_y": 0.5}
                canvas:
                    Color:
                        rgba: 0.2, 0.95, 0.65, 1
                    Line:
                        circle: (self.center_x, self.center_y, dp(4))
                        width: dp(1.5)

            MDIconButton:
                icon: "dots-vertical"
                theme_icon_color: "Custom"
                icon_color: 1, 1, 1, 1
                pos_hint: {"center_y": 0.5}

        # ОСНОВНОЙ КОНТЕНТ
        MDBoxLayout:
            orientation: 'vertical'
            padding: [dp(16), 0, dp(16), 0]
            spacing: dp(14)

            # 2. ГЛАВНАЯ КАРТОЧКА ДИСПЛЕЯ И ШКАЛЫ
            MDCard:
                orientation: 'vertical'
                size_hint_y: None
                height: dp(325)
                radius: [dp(24)]
                md_bg_color: 0.11, 0.12, 0.18, 1
                line_color: 1, 1, 1, 0.08
                line_width: dp(1)
                elevation: 0
                padding: [dp(16), dp(18), dp(16), dp(16)]
                spacing: dp(6)

                # Плашка TARGET
                MDCard:
                    size_hint: None, None
                    size: dp(215), dp(30)
                    pos_hint: {"center_x": 0.5}
                    radius: [dp(15)]
                    md_bg_color: 0.17, 0.18, 0.25, 1
                    elevation: 0

                    MDLabel:
                        text: f"TARGET: {root.target_note} ({root.target_freq:.2f} HZ)"
                        font_size: sp(11)
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.72, 0.75, 0.85, 1

                # Крупная центральная нота
                MDLabel:
                    text: root.target_note
                    font_size: sp(82)
                    bold: True
                    halign: "center"
                    size_hint_y: None
                    height: dp(96)
                    theme_text_color: "Custom"
                    text_color: 0.2, 0.95, 0.65, 1

                # Текущая частота
                MDLabel:
                    text: "-- Hz"
                    font_size: sp(15)
                    bold: True
                    halign: "center"
                    size_hint_y: None
                    height: dp(24)
                    theme_text_color: "Custom"
                    text_color: 0.45, 0.58, 0.95, 1

                # Горизонтальная шкала (высота увеличена до 96dp)
                ModernHorizontalTuner:
                    id: tuner_gauge
                    size_hint_y: None
                    height: dp(96)
                    deviation: root.deviation

                # Подписи LOW / IN TUNE / HIGH
                MDBoxLayout:
                    size_hint_y: None
                    height: dp(20)
                    padding: [dp(12), 0]

                    MDLabel:
                        text: "LOW"
                        font_size: sp(11)
                        bold: True
                        halign: "left"
                        theme_text_color: "Custom"
                        text_color: 0.55, 0.58, 0.68, 1

                    MDLabel:
                        text: "IN TUNE"
                        font_size: sp(11)
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.95, 0.65, 1

                    MDLabel:
                        text: "HIGH"
                        font_size: sp(11)
                        bold: True
                        halign: "right"
                        theme_text_color: "Custom"
                        text_color: 0.55, 0.58, 0.68, 1

                # Статус внизу карточки
                MDLabel:
                    text: "Listening..."
                    font_size: sp(14)
                    bold: True
                    halign: "center"
                    size_hint_y: None
                    height: dp(24)
                    theme_text_color: "Custom"
                    text_color: 0.92, 0.94, 0.98, 1

            # 3. СЕКЦИЯ ВЫБОРА СТРУН (Сетка 3x2)
            MDLabel:
                text: "STRINGS"
                font_size: sp(11)
                bold: True
                size_hint_y: None
                height: dp(18)
                padding: [dp(4), 0]
                theme_text_color: "Custom"
                text_color: 0.65, 0.68, 0.78, 1

            MDGridLayout:
                id: strings_grid
                cols: 3
                spacing: dp(10)
                size_hint_y: None
                height: dp(138)

            # 4. НИЖНЯЯ КАРТОЧКА ПРОГРЕССА НАСТРОЙКИ
            MDCard:
                orientation: 'vertical'
                size_hint_y: None
                height: dp(104)
                radius: [dp(20)]
                md_bg_color: 0.11, 0.12, 0.18, 1
                line_color: 1, 1, 1, 0.08
                line_width: dp(1)
                elevation: 0
                padding: [dp(14), dp(12), dp(14), dp(12)]
                spacing: dp(10)

                MDLabel:
                    text: f"{root.matched_count} / 6 strings matched"
                    font_size: sp(13)
                    bold: True
                    halign: "center"
                    size_hint_y: None
                    height: dp(22)
                    theme_text_color: "Custom"
                    text_color: 0.92, 0.94, 0.98, 1

                MDBoxLayout:
                    id: matched_row
                    spacing: dp(8)
                    size_hint_y: None
                    height: dp(38)

            Widget:
                size_hint_y: 1
'''


# ============ ГОРИЗОНТАЛЬНЫЙ ТЮНЕР ============

class ModernHorizontalTuner(Widget):
    deviation = NumericProperty(0.0)
    animated_deviation = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.labels = []
        self.bind(pos=self._on_layout_change, size=self._on_layout_change)
        self.bind(animated_deviation=self.update_gauge)

    def on_deviation(self, instance, value):
        clamped = max(-50.0, min(50.0, float(value)))
        Animation.cancel_all(self, 'animated_deviation')
        anim = Animation(animated_deviation=clamped, duration=0.18, transition='out_cubic')
        anim.start(self)

    def set_value(self, value):
        self.deviation = max(-50.0, min(50.0, float(value)))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            scale_w = self.width * 0.94
            scale_x = self.x + (self.width - scale_w) / 2
            rel = (touch.x - scale_x) / scale_w
            target_dev = (max(0.0, min(1.0, rel)) * 100.0) - 50.0
            if abs(target_dev) < 4:
                target_dev = 0.0
            self.set_value(target_dev)
            return True
        return super().on_touch_down(touch)

    def _on_layout_change(self, *args):
        self._rebuild_labels()
        self.update_gauge()

    @staticmethod
    def _get_segment_color(value, max_value=50):
        normalized = max(-1, min(1, value / max_value))
        pct = (normalized + 1) / 2
        if pct < 0.25:
            t = pct / 0.25
            return 1.0, t, 0.0
        elif pct < 0.5:
            t = (pct - 0.25) / 0.25
            return 1.0 - t, 1.0, 0.0
        elif pct < 0.75:
            t = (pct - 0.5) / 0.25
            return t, 1.0, 0.0
        else:
            t = (pct - 0.75) / 0.25
            return 1.0, 1.0 - t, 0.0

    def _rebuild_labels(self):
        for label in self.labels:
            if label.parent:
                self.remove_widget(label)
        self.labels.clear()

        if self.width <= 0 or self.height <= 0:
            return

        scale_w = self.width * 0.94
        scale_x = self.x + (self.width - scale_w) / 2
        scale_y = self.center_y - dp(8)

        num_segments = 21
        segment_width = scale_w / num_segments
        max_h = dp(28)

        # 5 ключевых меток ровно над центрами соответствующих сегментов
        ticks = [
            (0, -50),   # 1-й сегмент (-50)
            (5, -25),   # 6-й сегмент (-25)
            (10, 0),    # 11-й сегмент (0)
            (15, 25),   # 16-й сегмент (+25)
            (20, 50),   # 21-й сегмент (+50)
        ]

        for seg_idx, value in ticks:
            curr_x = scale_x + (seg_idx + 0.5) * segment_width
            is_zero = (value == 0)
            text = f"+{value}" if value > 0 else str(value)
            r, g, b = self._get_segment_color(value, 50)
            color = [0.2, 0.95, 0.65, 1.0] if is_zero else [r * 0.9 + 0.1, g * 0.9 + 0.1, b * 0.9 + 0.1, 0.85]

            lbl = Label(
                text=text,
                font_size=sp(12 if is_zero else 11),
                bold=True,
                color=color,
                size_hint=(None, None),
                size=(dp(36), dp(16)),
                center=(curr_x, scale_y + max_h / 2 + dp(14)),
                halign='center',
                valign='middle'
            )
            self.add_widget(lbl)
            self.labels.append(lbl)

    def update_gauge(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return

        scale_w = self.width * 0.94
        scale_x = self.x + (self.width - scale_w) / 2
        scale_y = self.center_y - dp(8)

        num_segments = 21
        segment_width = scale_w / num_segments
        gap = dp(2.4)

        max_h = dp(28)
        min_h = dp(10)

        with self.canvas:
            # 1. Сегменты шкалы с профилем волны
            for i in range(num_segments):
                value = -50 + i * 5
                x = scale_x + i * segment_width + gap / 2

                norm_dist = abs(value) / 50.0
                height_factor = (math.cos(norm_dist * math.pi) + 1.0) / 2.0
                curr_height = min_h + (max_h - min_h) * height_factor

                r, g, b = self._get_segment_color(value, 50)
                dist = abs(self.animated_deviation - value)
                focus_boost = 0.25 if dist < 4.5 else 0.0
                brightness = min(1.0, 0.65 + 0.25 * (1 - norm_dist) + focus_boost)
                alpha = 0.98 if dist < 4.5 else 0.78

                Color(r * brightness, g * brightness, b * brightness, alpha)
                RoundedRectangle(
                    pos=(x, scale_y - curr_height / 2),
                    size=(segment_width - gap, curr_height),
                    radius=[dp(3.5)]
                )

            # 2. Векторная стрелка
            dev = max(-50.0, min(50.0, self.animated_deviation))
            ix = scale_x + ((dev + 50.0) / 100.0) * scale_w
            is_tuned = abs(dev) <= 3.0

            glow_color = (0.2, 0.95, 0.65, 0.28) if is_tuned else (0.55, 0.45, 1.0, 0.28)
            body_color = (0.2, 0.95, 0.65, 1.0) if is_tuned else (1.0, 1.0, 1.0, 0.98)

            bar_bottom = scale_y - max_h / 2
            bar_top = scale_y + max_h / 2

            tip_y = bar_bottom - dp(3)
            base_y = tip_y - dp(15)
            half_w = dp(9)

            # Лазерный визир
            Color(*glow_color)
            Line(points=[ix, bar_bottom - dp(1), ix, bar_top + dp(2)], width=dp(3.5), cap='round')
            Color(*body_color)
            Line(points=[ix, bar_bottom - dp(1), ix, bar_top + dp(2)], width=dp(1.6), cap='round')

            # Ореол свечения стрелки
            Color(*glow_color)
            Triangle(points=[
                ix, tip_y + dp(3),
                ix - half_w - dp(4), base_y - dp(2),
                ix + half_w + dp(4), base_y - dp(2)
            ])

            # Левая грань стрелки
            Color(*body_color)
            Triangle(points=[
                ix, tip_y,
                ix - half_w, base_y,
                ix, base_y + dp(4)
            ])

            # Правая грань стрелки
            Color(
                body_color[0] * 0.82,
                body_color[1] * 0.85,
                body_color[2] * 0.92,
                1.0
            )
            Triangle(points=[
                ix, tip_y,
                ix + half_w, base_y,
                ix, base_y + dp(4)
            ])


# ============ КНОПКА СТРУНЫ В СЕТКЕ 3x2 ============

class StringTileButton(MDCard):
    selected = BooleanProperty(False)

    def __init__(self, index, note_letter, full_note, freq, on_select, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.note_letter = note_letter
        self.full_note = full_note
        self.freq = freq
        self.on_select = on_select
        self.radius = [dp(18)]
        self.elevation = 0
        self.ripple_behavior = True

        self.lbl = MDLabel(
            text=note_letter,
            font_size=sp(22),
            bold=True,
            halign="center",
            valign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        self.add_widget(self.lbl)
        self.update_style()

    def on_selected(self, *args):
        self.update_style()

    def update_style(self):
        if self.selected:
            self.md_bg_color = (0.50, 0.32, 0.96, 1)
            self.line_color = (0.75, 0.65, 1.0, 0.9)
            self.line_width = dp(1.5)
        else:
            self.md_bg_color = (0.43, 0.25, 0.90, 0.92)
            self.line_color = (0, 0, 0, 0)
            self.line_width = dp(1)

    def on_release(self):
        self.on_select(self.index)


# ============ ИНДИКАТОР СТРУНЫ В НИЖНЕЙ КАРТОЧКЕ ============

class MatchedPill(MDCard):
    matched = BooleanProperty(False)

    def __init__(self, index, note_letter, on_toggle, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.note_letter = note_letter
        self.on_toggle = on_toggle
        self.radius = [dp(16)]
        self.elevation = 0
        self.ripple_behavior = True

        self.size_hint_x = None
        self.width = dp(44)
        self.size_hint_y = None
        self.height = dp(38)

        self.lbl = MDLabel(
            text=f"{note_letter} ○",
            font_size=sp(12),
            bold=True,
            halign="center",
            valign="center",
            theme_text_color="Custom"
        )
        self.add_widget(self.lbl)
        self.update_style()

    def on_matched(self, *args):
        self.update_style()

    def update_style(self):
        if self.matched:
            self.md_bg_color = (0.2, 0.95, 0.65, 0.18)
            self.line_color = (0.2, 0.95, 0.65, 0.85)
            self.line_width = dp(1)
            self.lbl.text = f"{self.note_letter} ●"
            self.lbl.text_color = (0.2, 0.95, 0.65, 1)
        else:
            self.md_bg_color = (0.16, 0.17, 0.24, 1)
            self.line_color = (1, 1, 1, 0.06)
            self.line_width = dp(1)
            self.lbl.text = f"{self.note_letter} ○"
            self.lbl.text_color = (0.65, 0.68, 0.78, 1)

    def on_release(self):
        self.on_toggle(self.index)


# ============ ОСНОВНОЙ ЭКРАН ============

class TunerScreenDesign(MDScreen):
    target_note = StringProperty("E")
    target_freq = NumericProperty(329.63)
    deviation = NumericProperty(0)
    matched_count = NumericProperty(0)

    STRINGS_DATA = [
        ("E", "E2", 82.41),
        ("A", "A2", 110.00),
        ("D", "D3", 146.83),
        ("G", "G3", 196.00),
        ("B", "B3", 246.94),
        ("E", "E4", 329.63),
    ]

    def on_kv_post(self, base_widget):
        self.tile_buttons = []
        self.matched_pills = []
        grid = self.ids.strings_grid
        row = self.ids.matched_row

        for idx, (letter, full_note, freq) in enumerate(self.STRINGS_DATA):
            btn = StringTileButton(idx, letter, full_note, freq, self.select_string)
            self.tile_buttons.append(btn)
            grid.add_widget(btn)

            pill = MatchedPill(idx, letter, self.toggle_matched)
            self.matched_pills.append(pill)
            row.add_widget(pill)

        self.select_string(3)

    def select_string(self, index):
        for i, btn in enumerate(self.tile_buttons):
            btn.selected = (i == index)
        letter, _, freq = self.STRINGS_DATA[index]
        self.target_note = letter
        self.target_freq = freq

    def toggle_matched(self, index):
        pill = self.matched_pills[index]
        pill.matched = not pill.matched
        self.matched_count = sum(1 for p in self.matched_pills if p.matched)


class TunerPreviewApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        Builder.load_string(KV)
        return TunerScreenDesign()


if __name__ == "__main__":
    TunerPreviewApp().run()