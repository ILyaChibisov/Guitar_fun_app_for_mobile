import math
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty, ColorProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp

KV = '''
MDScreen:
    md_bg_color: 0.1, 0.1, 0.12, 1

    MDBoxLayout:
        orientation: 'vertical'
        padding: "24dp"
        spacing: "32dp"

        MDLabel:
            text: "GUITAR TUNER"
            halign: "center"
            font_style: "H5"
            theme_text_color: "Custom"
            text_color: 0.7, 0.7, 0.7, 1
            adaptive_height: True

        # Визуальный круглый индикатор
        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'center'

            RelativeLayout:
                size_hint: None, None
                size: "280dp", "280dp"

                # Внешнее кольцо шкалы
                canvas.before:
                    Color:
                        rgba: 0.2, 0.2, 0.25, 1
                    Line:
                        circle: (self.center_x, self.center_y, dp(120))
                        width: dp(3)

                    # Засечка идеальной настройки (центр)
                    Color:
                        rgba: 0, 1, 0.5, 0.3
                    Line:
                        points: [self.center_x, self.center_y + dp(110), self.center_x, self.center_y + dp(130)]
                        width: dp(4)

                # Стрелка отклонения
                canvas:
                    Color:
                        rgba: app.accent_color
                    Line:
                        points: 
                            [
                            self.center_x, 
                            self.center_y, 
                            self.center_x + dp(115) * math.sin(math.radians(app.deviation_angle)), 
                            self.center_y + dp(115) * math.cos(math.radians(app.deviation_angle))
                            ]
                        width: dp(3)
                        cap: 'round'

                    # Центральная точка стрелки
                    Color:
                        rgba: app.accent_color
                    Ellipse:
                        pos: self.center_x - dp(8), self.center_y - dp(8)
                        size: dp(16), dp(16)

                # Текст внутри круга
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_size: True
                    pos_hint: {'center_x': .5, 'center_y': .4}
                    spacing: "4dp"

                    MDLabel:
                        text: app.current_note
                        font_style: "H2"
                        bold: True
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: app.accent_color

                    MDLabel:
                        text: app.frequency_text
                        font_style: "Subtitle1"
                        halign: "center"
                        theme_text_color: "Custom"
                        text_color: 0.6, 0.6, 0.6, 1

        # Нижняя панель с кнопкой
        MDBoxLayout:
            orientation: 'vertical'
            adaptive_height: True
            spacing: "16dp"

            MDFloatingActionButton:
                icon: "microphone-off" if app.is_listening else "microphone"
                md_bg_color: app.accent_color
                icon_color: 1, 1, 1, 1
                pos_hint: {'center_x': .5}
                on_release: app.toggle_tuner()

            MDLabel:
                text: "Слушаю..." if app.is_listening else "Нажмите, чтобы включить"
                halign: "center"
                font_style: "Caption"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.5, 1
'''


class TunerApp(MDApp):
    deviation_angle = NumericProperty(0.0)
    current_note = StringProperty("-")
    frequency_text = StringProperty("0.0 Hz")
    accent_color = ColorProperty([0.5, 0.5, 0.5, 1])
    is_listening = BooleanProperty(False)  # Исправлено на BooleanProperty

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        return Builder.load_string(KV)

    def toggle_tuner(self):
        self.is_listening = not self.is_listening
        if self.is_listening:
            self.accent_color = [1.0, 0.3, 0.3, 1.0]
            self._time_passed = 0.0
            Clock.schedule_interval(self.mock_tuner_update, 0.05)  # Более плавное обновление (20 FPS)
        else:
            Clock.unschedule(self.mock_tuner_update)
            self.reset_tuner()

    def reset_tuner(self):
        self.deviation_angle = 0.0
        self.current_note = "-"
        self.frequency_text = "0.0 Hz"
        self.accent_color = [0.5, 0.5, 0.5, 1.0]

    def mock_tuner_update(self, dt):
        if not self.is_listening:
            return False

        self._time_passed += dt

        # Симуляция колебания частоты вокруг первой струны E (Ми) ~ 329.63 Гц
        fake_freq = 329.63 + 5.0 * math.sin(self._time_passed * 3.0)
        diff = fake_freq - 329.63

        self.frequency_text = f"{fake_freq:.1f} Hz"
        self.current_note = "E"

        # Ограничиваем угол в пределах разумного (-45 до +45 градусов)
        self.deviation_angle = max(-45.0, min(45.0, diff * 12.0))

        # Цветовая индикация точности
        if abs(diff) < 0.4:
            self.accent_color = [0.0, 1.0, 0.5, 1.0]  # Зеленый (точно)
        elif abs(diff) < 2.0:
            self.accent_color = [1.0, 0.7, 0.0, 1.0]  # Оранжевый (близко)
        else:
            self.accent_color = [1.0, 0.3, 0.3, 1.0]  # Красный (мимо)


if __name__ == '__main__':
    TunerApp().run()
