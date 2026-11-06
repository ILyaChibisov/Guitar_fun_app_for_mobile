from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.animation import Animation
from kivymd.app import MDApp

KV = '''
<TunerModuleScreen>:
    md_bg_color: [0.07, 0.08, 0.1, 1]

    MDBoxLayout:
        orientation: 'vertical'
        padding: [20, 20, 20, 30]
        spacing: 25

        # Верхнее сбалансированное меню
        MDBoxLayout:
            size_hint_y: None
            height: "56dp"
            spacing: 25
            pos_hint: {"center_x": .5}

            Widget:
                size_hint_x: 0.5

            MDIconButton:
                icon: "magnify"
                icon_size: "28dp"
                theme_icon_color: "Custom"
                icon_color: [0.4, 0.4, 0.5, 1]
                pos_hint: {"center_y": .5}

            MDIconButton:
                icon: "tune"
                icon_size: "28dp"
                theme_icon_color: "Custom"
                icon_color: [0.12, 0.53, 0.9, 1]
                pos_hint: {"center_y": .5}

            MDIconButton:
                icon: "music-chord-diagram"
                icon_size: "28dp"
                theme_icon_color: "Custom"
                icon_color: [0.4, 0.4, 0.5, 1]
                pos_hint: {"center_y": .5}

            Widget:
                size_hint_x: 0.5

        # Центральный круговой блок отображения ноты
        MDAnchorLayout:
            anchor_x: 'center'
            anchor_y: 'center'
            size_hint_y: 0.4

            RelativeLayout:
                size_hint: None, None
                size: "180dp", "180dp"

                canvas.before:
                    Color:
                        rgba: root.state_color + [0.06]
                    Ellipse:
                        size: self.size
                        pos: 0, 0
                    Color:
                        rgba: root.state_color + [0.12]
                    Ellipse:
                        size: self.width - 36, self.height - 36
                        pos: 18, 18

                MDLabel:
                    text: root.current_note
                    font_style: "H2"
                    halign: "center"
                    valign: "middle"
                    theme_text_color: "Custom"
                    text_color: root.state_color
                    bold: True

        # Блок полукруглой шкалы с вращающейся стрелкой
        MDBoxLayout:
            orientation: 'vertical'
            size_hint_y: 0.35
            spacing: 15

            RelativeLayout:
                size_hint_y: None
                height: "100dp"

                # Кастомная иконка стрелки, которая вращается по свойству стрелы
                MDIconButton:
                    icon: "chevron-up"
                    icon_size: "48dp"
                    theme_icon_color: "Custom"
                    icon_color: root.state_color
                    pos_hint: {"center_x": 0.5, "center_y": 0.2}
                    canvas.before:
                        PushMatrix
                        Rotate:
                            angle: root.needle_angle
                            origin: self.center
                    canvas.after:
                        PopMatrix

                # Текстовое отклонение
                MDLabel:
                    text: f"{'+' if root.cents > 0 else ''}{int(root.cents)} cents" if root.cents != 0 else "In Tune"
                    halign: "center"
                    pos_hint: {"center_x": 0.5, "center_y": 0.8}
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: root.state_color
                    bold: True

        # Нижний блок выбора струн с фиксированной высотой меню
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "60dp"
            spacing: 12
            pos_hint: {"center_x": .5}

            Widget:
                size_hint_x: .05

            StandardStringButton:
                text: "E"
                is_active: root.current_note == "E"
                on_release: root.select_note("E")
            StandardStringButton:
                text: "A"
                is_active: root.current_note == "A"
                on_release: root.select_note("A")
            StandardStringButton:
                text: "D"
                is_active: root.current_note == "D"
                on_release: root.select_note("D")
            StandardStringButton:
                text: "G"
                is_active: root.current_note == "G"
                on_release: root.select_note("G")
            StandardStringButton:
                text: "B"
                is_active: root.current_note == "B"
                on_release: root.select_note("B")
            StandardStringButton:
                text: "E"
                is_active: root.current_note == "E"
                on_release: root.select_note("E")

            Widget:
                size_hint_x: .05

<StandardStringButton@MDRoundFlatButton>:
    is_active: False
    text_color: [1, 1, 1, 1] if self.is_active else [0.4, 0.4, 0.5, 1]
    line_color: [0.12, 0.53, 0.9, 1] if self.is_active else [0.15, 0.17, 0.2, 1]
    md_bg_color: [0.12, 0.53, 0.9, 0.15] if self.is_active else [0.11, 0.12, 0.15, 1]
    font_size: "15sp"
    size_hint_x: 1
    bold: True
'''


class TunerModuleScreen(Screen):
    cents = NumericProperty(0)  # Отклонение от -50 до +50
    needle_angle = NumericProperty(0)  # Угол поворота стрелки от -60 до +60 градусов
    current_note = StringProperty("E")  # Текущая нота
    state_color = ListProperty([0.12, 0.53, 0.9])  # Базовый цвет без альфа-канала

    def on_enter(self, *args):
        """Запуск демонстрационного цикла при входе на экран модуля."""
        self.simulate_tuning_process()

    def select_note(self, note_name):
        """Метод для ручного переключения ноты по кнопке."""
        self.current_note = note_name

    def on_cents(self, instance, value):
        """Вызывается при обновлении значения центов."""
        # 1. Рассчитываем целевой угол стрелки прибора (-50 центов = -60 градусов)
        target_angle = -(value / 50.0) * 60.0
        Animation(needle_angle=target_angle, duration=0.2, t='out_quad').start(self)

        # 2. Обновляем статический цвет (без анимации списков во избежание TypeError)
        abs_val = abs(value)
        if abs_val <= 2:
            self.state_color = [0.15, 0.83, 0.48]  # Идеальный зеленый
        elif abs_val <= 15:
            self.state_color = [0.95, 0.72, 0.2]  # Янтарный близкий
        else:
            self.state_color = [0.95, 0.32, 0.42]  # Красный диез/бемоль

    def simulate_tuning_process(self):
        """Симуляция входящего аудиосигнала для демонстрации модуля."""
        anim = (
                Animation(cents=-45, duration=1.2)
                + Animation(cents=-15, duration=1.0)
                + Animation(cents=8, duration=0.8)
                + Animation(cents=0, duration=1.5, t='out_quad')
        )
        anim.repeat = True
        anim.start(self)


class StandaloneTunerApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"

        # Подгружаем KV-структуру
        Builder.load_string(KV)

        # Инициализируем изолированный менеджер экранов
        sm = ScreenManager()
        sm.add_widget(TunerModuleScreen(name="tuner_main"))
        return sm


if __name__ == '__main__':
    StandaloneTunerApp().run()
