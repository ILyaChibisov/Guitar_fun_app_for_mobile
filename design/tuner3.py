import math
from kivy.core.window import Window
from kivy.graphics import Color, Line, Ellipse, PushMatrix, PopMatrix, Rotate
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

# Размер окна для предпросмотра на ПК
Window.size = (390, 800)

KV = '''
#:import dp kivy.metrics.dp

<TunerGauge>:
    canvas.before:
        # Фоновая дуга шкалы
        Color:
            rgba: 0.16, 0.18, 0.24, 1
        Line:
            circle: (self.center_x, self.y + dp(40), self.gauge_radius, -65, 65)
            width: dp(4)
            cap: 'round'

        # Зона точной настройки (центр ±5 центов)
        Color:
            rgba: (0.15, 0.9, 0.45, 0.85) if abs(self.cents) <= 5 else (0.25, 0.28, 0.35, 1)
        Line:
            circle: (self.center_x, self.y + dp(40), self.gauge_radius, -6.5, 6.5)
            width: dp(6)
            cap: 'round'

<MainScreen>:
    md_bg_color: 0.07, 0.08, 0.11, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: [dp(20), dp(16), dp(20), dp(24)]
        spacing: dp(12)

        # Верхняя панель
        MDBoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(10)

            MDLabel:
                text: "GUITAR TUNER"
                font_style: "Subtitle1"
                bold: True
                theme_text_color: "Custom"
                text_color: 0.85, 0.88, 0.95, 1
                halign: "left"

            MDCard:
                size_hint: None, None
                size: dp(110), dp(34)
                radius: [dp(17)]
                md_bg_color: (0.15, 0.9, 0.45, 0.18) if root.auto_mode else (0.16, 0.18, 0.24, 1)
                elevation: 0
                ripple_behavior: True
                on_release: root.toggle_mode()

                MDLabel:
                    text: "АВТО" if root.auto_mode else "РУЧНОЙ"
                    halign: "center"
                    font_style: "Caption"
                    bold: True
                    theme_text_color: "Custom"
                    text_color: (0.15, 0.9, 0.45, 1) if root.auto_mode else (0.6, 0.65, 0.75, 1)

        # Полукруглая шкала со стрелкой
        TunerGauge:
            id: gauge
            size_hint_y: 0.42
            cents: root.current_cents

        # Центральный дисплей ноты
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.28
            spacing: dp(4)

            MDCard:
                size_hint: None, None
                size: dp(136), dp(136)
                pos_hint: {"center_x": 0.5}
                radius: [dp(68)]
                md_bg_color: 0.11, 0.13, 0.18, 1
                line_color: (0.15, 0.9, 0.45, 1) if abs(root.current_cents) <= 5 else (0.22, 0.25, 0.33, 1)
                line_width: dp(2.5) if abs(root.current_cents) <= 5 else dp(1.5)
                elevation: 0

                MDBoxLayout:
                    orientation: 'vertical'
                    padding: dp(10)

                    MDLabel:
                        text: root.current_note
                        font_style: "H2"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: (0.15, 0.9, 0.45, 1) if abs(root.current_cents) <= 5 else (0.95, 0.96, 0.98, 1)

                    MDLabel:
                        text: root.status_text
                        font_style: "Caption"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: (0.15, 0.9, 0.45, 1) if abs(root.current_cents) <= 5 else (0.55, 0.6, 0.7, 1)

            # Строка с отклонением в центах и частотой в Герцах
            MDBoxLayout:
                size_hint_y: None
                height: dp(32)
                padding: [dp(30), 0]

                MDLabel:
                    text: f"{root.current_cents:+.0f} центов"
                    font_style: "Body2"
                    halign: "left"
                    theme_text_color: "Custom"
                    text_color: 0.6, 0.65, 0.75, 1

                MDLabel:
                    text: f"{root.current_freq:.1f} Гц"
                    font_style: "Body2"
                    halign: "right"
                    theme_text_color: "Custom"
                    text_color: 0.6, 0.65, 0.75, 1

        # Нижняя панель выбора струн (E2 - E4)
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: dp(90)
            spacing: dp(8)

            MDLabel:
                text: "СТАНДАРТНЫЙ СТРОЙ (E2 - E4)"
                font_style: "Overline"
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.45, 0.5, 0.6, 1
                size_hint_y: None
                height: dp(18)

            MDBoxLayout:
                id: strings_box
                spacing: dp(8)
                size_hint_y: None
                height: dp(54)
'''


class TunerGauge(Widget):
    cents = NumericProperty(0.0)
    gauge_radius = NumericProperty(dp(145))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas, cents=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        cx = self.center_x
        cy = self.y + dp(40)
        self.gauge_radius = min(self.width * 0.44, self.height * 0.78)

        with self.canvas:
            # Деления шкалы от -50 до +50 с шагом 5 центов
            for val in range(-50, 55, 5):
                angle_deg = (val / 50.0) * 65.0
                angle_rad = math.radians(90 - angle_deg)

                is_major = (val % 10 == 0)
                is_center = (val == 0)

                inner_r = self.gauge_radius - (dp(18) if is_major else dp(10))
                outer_r = self.gauge_radius + (dp(6) if is_center else 0)

                x1 = cx + inner_r * math.cos(angle_rad)
                y1 = cy + inner_r * math.sin(angle_rad)
                x2 = cx + outer_r * math.cos(angle_rad)
                y2 = cy + outer_r * math.sin(angle_rad)

                if is_center:
                    Color(0.15, 0.9, 0.45, 1)
                    width = dp(3)
                elif abs(val) <= 5:
                    Color(0.15, 0.9, 0.45, 0.6)
                    width = dp(1.5)
                elif is_major:
                    Color(0.55, 0.6, 0.7, 0.9)
                    width = dp(2)
                else:
                    Color(0.3, 0.34, 0.42, 0.7)
                    width = dp(1.2)

                Line(points=[x1, y1, x2, y2], width=width, cap='round')

            # Положение стрелки
            clamped_cents = max(-50.0, min(50.0, self.cents))
            needle_angle = -(clamped_cents / 50.0) * 65.0
            is_tuned = abs(clamped_cents) <= 5

            PushMatrix()
            Rotate(angle=needle_angle, origin=(cx, cy))

            # Мягкое свечение вокруг стрелки
            Color(*(0.15, 0.9, 0.45, 0.25) if is_tuned else (0.95, 0.35, 0.4, 0.2))
            Line(points=[cx, cy + dp(14), cx, cy + self.gauge_radius - dp(4)], width=dp(8), cap='round')

            # Основная линия стрелки
            Color(*(0.15, 0.9, 0.45, 1) if is_tuned else (0.95, 0.35, 0.4, 1))
            Line(points=[cx, cy + dp(14), cx, cy + self.gauge_radius - dp(4)], width=dp(3), cap='round')

            PopMatrix()

            # Центральная точка крепления стрелки
            Color(0.16, 0.18, 0.24, 1)
            Ellipse(pos=(cx - dp(12), cy - dp(12)), size=(dp(24), dp(24)))
            Color(*(0.15, 0.9, 0.45, 1) if is_tuned else (0.95, 0.35, 0.4, 1))
            Ellipse(pos=(cx - dp(6), cy - dp(6)), size=(dp(12), dp(12)))


class StringButton(MDCard):
    note_name = StringProperty("")
    freq = NumericProperty(0.0)
    selected = BooleanProperty(False)

    def __init__(self, note_name, freq, callback, **kwargs):
        super().__init__(**kwargs)
        self.note_name = note_name
        self.freq = freq
        self.callback = callback
        self.radius = [dp(14)]
        self.elevation = 0
        self.ripple_behavior = True

        self.label = MDLabel(
            text=note_name,
            halign="center",
            font_style="Subtitle1",
            bold=True,
            theme_text_color="Custom"
        )
        self.add_widget(self.label)
        self.update_style()

    def on_selected(self, instance, value):
        self.update_style()

    def update_style(self):
        if self.selected:
            self.md_bg_color = (0.15, 0.9, 0.45, 0.2)
            self.line_color = (0.15, 0.9, 0.45, 1)
            self.line_width = dp(1.5)
            if hasattr(self, 'label'):
                self.label.text_color = (0.15, 0.9, 0.45, 1)
        else:
            self.md_bg_color = (0.12, 0.14, 0.19, 1)
            self.line_color = (0.2, 0.23, 0.3, 1)
            self.line_width = dp(1)
            if hasattr(self, 'label'):
                self.label.text_color = (0.8, 0.84, 0.92, 1)

    def on_release(self):
        self.callback(self)


class MainScreen(MDScreen):
    current_note = StringProperty("E2")
    current_freq = NumericProperty(82.4)
    current_cents = NumericProperty(0.0)
    status_text = StringProperty("ТОЧНО")
    auto_mode = BooleanProperty(True)

    GUITAR_STRINGS = [
        ("E2", 82.41),
        ("A2", 110.00),
        ("D3", 146.83),
        ("G3", 196.00),
        ("B3", 246.94),
        ("E4", 329.63),
    ]

    def on_kv_post(self, base_widget):
        self.string_buttons = []
        box = self.ids.strings_box
        for note, freq in self.GUITAR_STRINGS:

            btn = StringButton(note, freq, self.select_string)
            self.string_buttons.append(btn)
            box.add_widget(btn)
            # Выделяем первую струну по умолчанию
            self.select_string(self.string_buttons[0], manual=False)

    def select_string(self, selected_btn, manual=True):
        if manual:
            self.auto_mode = False
        for btn in self.string_buttons:
            btn.selected = (btn == selected_btn)
            self.current_note = selected_btn.note_name
            self.current_freq = selected_btn.freq

    def toggle_mode(self):
        self.auto_mode = not self.auto_mode

class GuitarTunerApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        Builder.load_string(KV)
        return MainScreen()

if __name__ == '__main__':
    GuitarTunerApp().run()