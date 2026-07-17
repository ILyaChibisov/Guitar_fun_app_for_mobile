import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle
from kivy.properties import BoundedNumericProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex


class VintageStudioTuner(Widget):
    # Отклонение от -50 до +50 центов
    value = BoundedNumericProperty(0, min=-50, max=50, errorvalue=0)

    def __init__(self, **kwargs):
        super(VintageStudioTuner, self).__init__(**kwargs)
        self.labels = []
        self.bind(pos=self.update_gauge, size=self.update_gauge, value=self.update_gauge)

    def update_gauge(self, *args):
        # Полная очистка холста и старых надписей
        self.canvas.clear()
        for label in self.labels:
            if label.parent:
                self.remove_widget(label)
        self.labels.clear()

        # Переменные позиционирования
        cx = self.center_x
        cy = self.y - self.height * 0.35  # Уносим центр круга глубоко вниз для пологой дуги
        radius = min(self.width, self.height) * 1.1

        # Узкая верхняя дуга: от 115 до 65 градусов (всего 50 градусов хода)
        start_angle = 115
        end_angle = 65
        angle_range = end_angle - start_angle  # -50 градусов

        with self.canvas:
            # 1. КРЕМОВАЯ ПОДЛОЖКА ШКАЛЫ (Эффект винтажной бумаги/пластика)
            Color(*get_color_from_hex('#f4f1ea'))
            Rectangle(pos=(self.x + 15, self.y + 15), size=(self.width - 30, self.height - 30))

            # Внутренняя металлическая рамка прибора
            Color(*get_color_from_hex('#2c3e50'))
            Line(rectangle=(self.x + 15, self.y + 15, self.width - 30, self.height - 30), width=4)

            # Мягкая тень под рамкой для объема
            Color(0, 0, 0, 0.15)
            Line(rectangle=(self.x + 17, self.y + 17, self.width - 34, self.height - 34), width=1.5)

            # 2. ОСНОВНАЯ ИЗМЕРИТЕЛЬНАЯ ДУГА (Тонкая аккуратная линия)
            Color(*get_color_from_hex('#1e272c'))
            Line(circle=(cx, cy, radius, end_angle - 2, start_angle + 2), width=1.5)

            # Опасная зона (Красная дуга перетяга от +40 до +50 центов)
            Color(*get_color_from_hex('#c0392b'))
            red_start = start_angle + 0.9 * angle_range
            red_end = start_angle + 1.0 * angle_range
            Line(circle=(cx, cy, radius + 3, red_end, red_start), width=3)

            # 3. АНАЛОГОВЫЕ ЗАСЕЧЕК ТЕМПА (Черточки разной длины)
            for i in range(51):  # 51 деление — на каждый цент!
                val = -50 + i
                pct = i / 50.0
                angle_deg = start_angle + pct * angle_range
                angle_rad = math.radians(angle_deg)

                # Иерархия делений: каждые 10 центов — длинные, каждые 5 — средние, остальные — мелкие
                if val % 10 == 0:
                    tick_len = 16
                    tick_w = 1.8
                    Color(*get_color_from_hex('#1e272c'))
                elif val % 5 == 0:
                    tick_len = 10
                    tick_w = 1.2
                    Color(*get_color_from_hex('#576574'))
                else:
                    tick_len = 5
                    tick_w = 0.8
                    Color(*get_color_from_hex('#8395a7'))

                # Координаты засечек (идут наружу от дуги)
                x_start = cx + radius * math.cos(angle_rad)
                y_start = cy + radius * math.sin(angle_rad)
                x_end = cx + (radius + tick_len) * math.cos(angle_rad)
                y_end = cy + (radius + tick_len) * math.sin(angle_rad)

                Line(points=[x_start, y_start, x_end, y_end], width=tick_w)

        # 4. СТРОГИЕ КЛАССИЧЕСКИЕ ШРИФТЫ ДЛЯ ЦИФР
        for val in [-50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50]:
            pct = (val - (-50)) / 100.0
            angle_deg = start_angle + pct * angle_range
            angle_rad = math.radians(angle_deg)

            # Цифры стоят чуть выше засечек
            text_radius = radius + 28
            tx = cx + text_radius * math.cos(angle_rad)
            ty = cy + text_radius * math.sin(angle_rad)

            # Винтажный зеленый для нуля, красный для экстремального диеза, черный для остальных
            if val == 0:
                lbl_color = get_color_from_hex('#27ae60')
            elif val == 50:
                lbl_color = get_color_from_hex('#c0392b')
            else:
                lbl_color = get_color_from_hex('#2c3e50')

            lbl = Label(
                text=str(val),
                font_size='12sp',
                bold=True if val in [-50, 0, 50] else False,
                color=lbl_color,
                size_hint=(None, None),
                size=(30, 15),
                center=(tx, ty)
            )
            self.add_widget(lbl)
            self.labels.append(lbl)

        # 5. ТОНКАЯ СТРЕЛКА ИЗМЕРИТЕЛЯ С БАЛАНСИРОМ
        val_pct = (self.value - (-50)) / 100.0
        arrow_deg = start_angle + val_pct * angle_range
        arrow_rad = math.radians(arrow_deg)

        # Кончик стрелки заходит на засечки
        tip_x = cx + (radius + 12) * math.cos(arrow_rad)
        tip_y = cy + (radius + 12) * math.sin(arrow_rad)

        # Основание стрелки (начинается чуть ниже видимой зоны экрана)
        base_x = cx + (radius - 120) * math.cos(arrow_rad)
        base_y = cy + (radius - 120) * math.sin(arrow_rad)

        with self.canvas:
            # Тень от стрелки на бумаге (сдвинута вправо и вниз для реалистичного 3D эффекта)
            Color(0, 0, 0, 0.12)
            Line(points=[base_x + 3, base_y - 2, tip_x + 3, tip_y - 2], width=1.5)

            # Сама стрелка (Классический угольно-черный цвет)
            Color(*get_color_from_hex('#1e272c'))
            Line(points=[base_x, base_y, tip_x, tip_y], width=1.8)


class TunerApp(App):
    def build(self):
        root = FloatLayout()

        # Внешний фон — текстура рэковой стойки (темный матовый антрацит)
        with root.canvas.before:
            Color(*get_color_from_hex('#1e252b'))
            self.bg_rect = Rectangle(size=(1000, 1000), pos=(0, 0))
            root.bind(size=self.update_bg)

        # Добавляем наш стрелочный VU-панель виджет
        self.gauge = VintageStudioTuner(
            size_hint=(0.9, 0.55),
            pos_hint={'center_x': 0.5, 'center_y': 0.65}
        )
        root.add_widget(self.gauge)

        # ЛАМПОЧКА ИНДИКАТОРА ТОЧНОЙ НАСТРОЙКИ (Светодиод "TUNE")
        # Будет загораться мягким зеленым светом
        self.led_bg = Widget(size_hint=(None, None), size=(16, 16), pos_hint={'center_x': 0.5, 'center_y': 0.32})
        with self.led_bg.canvas:
            self.led_color = Color(*get_color_from_hex('#3d4d41'))  # Выключен (темно-зеленый)
            self.led_circle = Line(circle=(0, 0, 6), width=12, joint='round')
        self.led_bg.bind(pos=self.update_led_pos)
        root.add_widget(self.led_bg)

        # КРУПНЫЙ ВИНТАЖНЫЙ ИНДИКАТОР НОТЫ (Как на старых LCD экранах)
        self.note_label = Label(
            text="D3",
            font_size='64sp',
            bold=True,
            color=get_color_from_hex('#eceff1'),
            pos_hint={'center_x': 0.5, 'center_y': 0.2}
        )
        root.add_widget(self.note_label)

        # Частота
        self.hz_label = Label(
            text="146.83 Hz",
            font_size='16sp',
            color=get_color_from_hex('#607d8b'),
            pos_hint={'center_x': 0.5, 'center_y': 0.08}
        )
        root.add_widget(self.hz_label)

        # Имитируем физику аналоговой стрелки (у неё есть инерция и легкий отскок)
        self.time = 0
        Clock.schedule_interval(self.simulate_analog_needle, 0.04)

        return root

    def update_bg(self, instance, value):
        self.bg_rect.size = instance.size

    def update_led_pos(self, instance, value):
        # Корректно центрируем круг светодиода при изменении размеров экрана
        self.led_circle.circle = (instance.center_x, instance.center_y, 6)

    def simulate_analog_needle(self, dt):
        self.time += dt

        # Физика затухающих колебаний струны "Ре" (D3)
        cycle = self.time % 11
        if cycle < 4:
            # Струну только извлекли — сильный перетяг (+34 цента) с затухающим дрожанием
            simulated_value = 34 + math.sin(self.time * 8) * 5 * math.exp(-(cycle))
        elif cycle < 7:
            # Струна почти настроена, стрелка колеблется у отметки +5 центов
            simulated_value = 5 + math.sin(self.time * 5) * 1.5
        else:
            # Идеальный баланс (In Tune)
            simulated_value = math.sin(self.time * 2) * 0.4

        self.gauge.value = simulated_value

        # Управление аналоговым светодиодом и цветом шрифтов
        if abs(simulated_value) <= 1.5:
            self.led_color.rgb = get_color_from_hex('#2ecc71')  # Ярко-зеленый (Горит)
            self.note_label.color = get_color_from_hex('#2ecc71')
            self.hz_label.text = "146.83 Hz"
        else:
            self.led_color.rgb = get_color_from_hex('#3d4d41')  # Матовый темный (Выключен)
            self.note_label.color = get_color_from_hex('#eceff1')
            self.hz_label.text = f"{146.83 + (simulated_value * 0.08):.2f} Hz"


if __name__ == '__main__':
    TunerApp().run()
