import math
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivymd.app import MDApp

KV = '''
MDScreenManager:
    WaveTunerScreen:
        name: "wave_tuner"

<WaveTunerScreen>:
    md_bg_color: [0.04, 0.04, 0.05, 1]  # Глубокий монохромный темный фон

    MDBoxLayout:
        orientation: 'vertical'
        padding: 
        spacing: 20

        # Верхнее фиксированное меню (Полное соответствие размерам экрана аккордов)
        MDBoxLayout:
            size_hint_y: None
            height: "56dp"
            spacing: 20
            pos_hint: {"center_x": .5}

            Widget:
                size_hint_x: 0.5

            MDIconButton:
                icon: "magnify"
                icon_size: "26dp"
                theme_icon_color: "Custom"
                icon_color: [0.35, 0.35, 0.4, 1]
                pos_hint: {"center_y": .5}

            MDIconButton:
                icon: "tune"
                icon_size: "26dp"
                theme_icon_color: "Custom"
                icon_color: root.wave_color
                pos_hint: {"center_y": .5}

            MDIconButton:
                icon: "music-chord-diagram"
                icon_size: "26dp"
                theme_icon_color: "Custom"
                icon_color: [0.35, 0.35, 0.4, 1]
                pos_hint: {"center_y": .5}

            Widget:
                size_hint_x: 0.5

        # Центральный блок с крупной премиальной типографикой
        MDAnchorLayout:
            anchor_x: 'center'
            anchor_y: 'center'
            size_hint_y: 0.4

            MDBoxLayout:
                orientation: 'vertical'
                size_hint: None, None
                size: "200dp", "120dp"
                spacing: 5

                MDLabel:
                    text: root.current_note
                    font_style: "H1"
                    font_size: "72sp"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: [1, 1, 1, 1]  # Чистый белый цвет для премиального контраста
                    bold: True

                MDLabel:
                    text: f"{'+' if root.cents > 0 else ''}{int(root.cents)} CT" if root.cents != 0 else "IN TUNE"
                    font_style: "Button"
                    halign: "center"
                    theme_text_color: "Custom"
                    text_color: root.wave_color
                    bold: True
                    opacity: 0.9

        # Блок интерактивной жидкой волны (Canvas)
        MDAnchorLayout:
            size_hint_y: 0.25
            anchor_x: 'center'
            anchor_y: 'center'

            Widget:
                id: wave_widget
                size_hint_y: None
                height: "100dp"

        # Нижний блок выбора струн с фиксированной высотой меню аккордов
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "60dp"
            spacing: 12
            pos_hint: {"center_x": .5}

            Widget:
                size_hint_x: .05

            WaveButton:
                text: "E"
                is_active: root.current_note == "E"
                on_release: root.select_note("E")
            WaveButton:
                text: "A"
                is_active: root.current_note == "A"
                on_release: root.select_note("A")
            WaveButton:
                text: "D"
                is_active: root.current_note == "D"
                on_release: root.select_note("D")
            WaveButton:
                text: "G"
                is_active: root.current_note == "G"
                on_release: root.select_note("G")
            WaveButton:
                text: "B"
                is_active: root.current_note == "B"
                on_release: root.select_note("B")
            WaveButton:
                text: "E"
                is_active: root.current_note == "E"
                on_release: root.select_note("E")

            Widget:
                size_hint_x: .05

<WaveButton@MDRoundFlatButton>:
    is_active: False
    text_color: if self.is_active else [0.4, 0.45, 0.5, 1]
    line_color: [0.12, 0.53, 0.9, 1] if self.is_active else [0.12, 0.14, 0.16, 1]
    md_bg_color: [0.12, 0.53, 0.9, 0.12] if self.is_active else [0.06, 0.07, 0.08, 1]
    font_size: "15sp"
    size_hint_x: 1
    bold: True
'''


class WaveTunerScreen(Screen):
    cents = NumericProperty(45)
    wave_amplitude = NumericProperty(30)  # Высота волны (чем ближе к 0, тем ровнее линия)
    wave_phase = NumericProperty(0)  # Фаза сдвига волны (для эффекта анимации движения)
    current_note = StringProperty("E")
    wave_color = ListProperty([0.95, 0.35, 0.45])  # Изначально мягкий красный

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Каждые 1/60 секунды перерисовываем волну для создания живой 60 FPS плавной графики
        Clock.schedule_interval(self.update_wave_canvas, 1 / 60)

    def on_enter(self, *args):
        self.simulate_smooth_tuning()

    def select_note(self, note_name):
        self.current_note = note_name

    def on_cents(self, instance, value):
        """Плавное изменение физики волны и её цвета на основе отклонения."""
        abs_val = abs(value)

        # Рассчитываем целевую амплитуду (высоту колебаний): если 0 центов -> амплитуда станет 0 (идеальная прямая)
        target_amp = 0 if abs_val <= 1.5 else max(4, min(35, abs_val * 0.8))
        Animation(wave_amplitude=target_amp, duration=0.3, t='out_quad').start(self)

        # Плавное премиальное изменение цвета
        if abs_val <= 2:
            self.wave_color = [0.15, 0.8, 0.45]  # Изумрудный зеленый
        elif abs_val <= 15:
            self.wave_color = [0.95, 0.65, 0.15]  # Студийный янтарный
        else:
            self.wave_color = [0.95, 0.35, 0.45]  # Глубокий коралловый/красный

    def update_wave_canvas(self, dt):
        """Генерация и динамическая отрисовка синусоидальной волны звука."""
        wave_widget = self.ids.wave_widget
        if not wave_widget:
            return

        # Постоянно сдвигаем фазу, чтобы волна «бежала» на экране
        # Если струна настроена (амплитуда 0), волна замирает в идеальную линию
        if self.wave_amplitude > 0:
            self.wave_phase += 0.12
        else:
            self.wave_phase += 0.02  # Легкое микро-дыхание линии

        wave_widget.canvas.clear()

        with wave_widget.canvas:
            from kivy.graphics import Color, Line

            points = []
            steps = 40  # Детализация изгибов волны

            for i in range(steps + 1):
                # Процент прохождения экрана по горизонтали
                pct = i / steps
                x = wave_widget.x + (wave_widget.width * pct)

                # Математика затухания синусоиды к краям экрана для эффекта "жидкой нити"
                edge_fade = math.sin(pct * math.pi)

                # Основное уравнение звуковой волны
                y = wave_widget.center_y + (
                        self.wave_amplitude * math.sin(pct * math.pi * 3 + self.wave_phase) * edge_fade
                )
                points.extend([x, y])

            # 1. Отрисовка размытого объемного неонового следа под волной
            Color(self.wave_color[0], self.wave_color[1], self.wave_color[2], 0.15)
            Line(points=points, width=4, cap='round', joint='round')

            # 2. Отрисовка основного яркого ядра нити волны
            Color(self.wave_color[0], self.wave_color[1], self.wave_color[2], 0.95)
            Line(points=points, width=2, cap='round', joint='round')

    def simulate_smooth_tuning(self):
        """Мягкий демонстрационный цикл затухания звука."""
        anim = (
                Animation(cents=-45, duration=1.5)
                + Animation(cents=28, duration=1.3)
                + Animation(cents=-12, duration=1.0)
                + Animation(cents=0, duration=2.5, t='out_quad')
        )
        anim.repeat = True
        anim.start(self)


class WaveTunerApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)


if __name__ == '__main__':
    WaveTunerApp().run()
