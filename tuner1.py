import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle
from kivy.properties import BoundedNumericProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex


class ModernNeonTuner(Widget):
    # Отклонение от -50 до +50 центов
    value = BoundedNumericProperty(0, min=-50, max=50, errorvalue=0)

    def __init__(self, **kwargs):
        super(ModernNeonTuner, self).__init__(**kwargs)
        self.labels = []
        self.bind(pos=self.update_gauge, size=self.update_gauge, value=self.update_gauge)

    def update_gauge(self, *args):
        # Сброс холста и меток
        self.canvas.clear()
        for label in self.labels:
            if label.parent:
                self.remove_widget(label)
        self.labels.clear()

        cx = self.center_x
        cy = self.center_y - self.height * 0.05
        # Радиус основной шкалы
        radius = min(self.width, self.height) * 0.42

        # Современная геометрия: разомкнутый круг (от -220 до 40 градусов)
        start_angle = 220
        end_angle = -40
        angle_range = end_angle - start_angle  # -260 градусов

        with self.canvas:
            # 1. ТОНКАЯ ФОНОВАЯ ТЕМНАЯ ЛИНИЯ (Основа шкалы)
            Color(*get_color_from_hex('#2d3139'))
            Line(circle=(cx, cy, radius, end_angle, start_angle), width=3)

            # 2. РИСОВАНИЕ МИНИМАЛИСТИЧНЫХ ЗАСЕЧЕК (Каждые 10 центов)
            # Центральный ноль выделен ярче
            for i in range(11):
                val = -50 + i * 10
                pct = i / 10.0
                angle_deg = start_angle + pct * angle_range
                angle_rad = math.radians(angle_deg)

                # Тонкие деления, уходящие наружу
                tick_len = 12 if val == 0 else 6
                tick_w = 2.5 if val == 0 else 1.2

                x_start = cx + radius * math.cos(angle_rad)
                y_start = cy + radius * math.sin(angle_rad)
                x_end = cx + (radius + tick_len) * math.cos(angle_rad)
                y_end = cy + (radius + tick_len) * math.sin(angle_rad)

                if val == 0:
                    Color(*get_color_from_hex('#00f2fe'))  # Неоновый циан для 0
                else:
                    Color(*get_color_from_hex('#616975'))

                Line(points=[x_start, y_start, x_end, y_end], width=tick_w)

            # 3. НЕОНОВЫЙ ТРЕК ОТКЛОНЕНИЯ (Заполняется от центра!)
            # В современных тюнерах полоса растет от 0 влево или вправо
            pct_zero = 0.5  # 0 центов — это ровно середина (50%)
            angle_zero = start_angle + pct_zero * angle_range

            val_pct = (self.value - (-50)) / 100.0
            angle_current = start_angle + val_pct * angle_range

            if self.value != 0:
                # Меняем цвет в зависимости от точности
                if abs(self.value) <= 1.5:
                    Color(*get_color_from_hex('#00ff87'))  # Идеальный зеленый неон
                elif abs(self.value) <= 10:
                    Color(*get_color_from_hex('#00f2fe'))  # Близко (циан)
                else:
                    Color(*get_color_from_hex('#ff0055'))  # Сильный несовпадос (пурпурно-красный)

                # Рисуем дугу от нуля до текущего значения центов
                # Line требует, чтобы углы шли по возрастанию, поэтому определяем min/max
                a1 = min(angle_zero, angle_current)
                a2 = max(angle_zero, angle_current)

                # Эффект свечения подложки (размытый слой)
                if abs(self.value) <= 1.5:
                    Color(0, 1, 0.5, 0.15)
                elif abs(self.value) <= 10:
                    Color(0, 0.9, 1, 0.15)
                else:
                    Color(1, 0, 0.3, 0.15)
                Line(circle=(cx, cy, radius, a1, a2), width=10)  # Толстый полупрозрачный след

                # Основная яркая неоновая линия
                if abs(self.value) <= 1.5:
                    Color(*get_color_from_hex('#00ff87'))
                elif abs(self.value) <= 10:
                    Color(*get_color_from_hex('#00f2fe'))
                else:
                    Color(*get_color_from_hex('#ff0055'))
                Line(circle=(cx, cy, radius, a1, a2), width=4)

        # 4. ПОДПИСИ КРАЙНИХ И ЦЕНТРАЛЬНОЙ ТОЧЕК (-50, 0, +50)
        # Расположены аккуратно под засечками, без лишнего нагромождения цифр
        for val in [-50, 0, 50]:
            pct = (val - (-50)) / 100.0
            angle_deg = start_angle + pct * angle_range
            angle_rad = math.radians(angle_deg)

            text_radius = radius - 24
            tx = cx + text_radius * math.cos(angle_rad)
            ty = cy + text_radius * math.sin(angle_rad)

            if val == 0:
                lbl_color = get_color_from_hex('#00f2fe') if abs(self.value) > 1.5 else get_color_from_hex('#00ff87')
            else:
                lbl_color = get_color_from_hex('#4e5561')

            lbl = Label(
                text="0" if val == 0 else (f"-50" if val < 0 else "+50"),
                font_size='12sp',
                bold=True if val == 0 else False,
                color=lbl_color,
                size_hint=(None, None),
                size=(40, 20),
                center=(tx, ty)
            )
            self.add_widget(lbl)
            self.labels.append(lbl)


class TunerApp(App):
    def build(self):
        root = FloatLayout()

        # Матовый темный Hi-Tech фон (#0b0c10 - глубокий космический черный)
        with root.canvas.before:
            Color(*get_color_from_hex('#0b0c10'))
            self.bg_rect = Rectangle(size=(1000, 1000), pos=(0, 0))
            root.bind(size=self.update_bg)

        # Добавляем современный неоновый виджет
        self.gauge = ModernNeonTuner(
            size_hint=(0.85, 0.85),
            pos_hint={'center_x': 0.5, 'center_y': 0.55}
        )
        root.add_widget(self.gauge)

        # КРУПНЫЙ ИНДИКАТОР НОТЫ (По центру круга, как в хай-тек аудиоплагинах)
        self.note_label = Label(
            text="A4",
            font_size='72sp',
            bold=True,
            color=get_color_from_hex('#ffffff'),
            pos_hint={'center_x': 0.5, 'center_y': 0.53}
        )
        root.add_widget(self.note_label)

        # ИНДИКАТОР ТОЧНЫХ ЦЕНТОВ С ПЛЮСОМ ИЛИ МИНУСОМ
        self.cents_label = Label(
            text="+0.0",
            font_size='18sp',
            color=get_color_from_hex('#00f2fe'),
            pos_hint={'center_x': 0.5, 'center_y': 0.41}
        )
        root.add_widget(self.cents_label)

        # Нижний плоский виджет частоты
        self.hz_label = Label(
            text="440.00 Hz",
            font_size='16sp',
            color=get_color_from_hex('#4e5561'),
            pos_hint={'center_x': 0.5, 'center_y': 0.12}
        )
        root.add_widget(self.hz_label)

        # Имитация работы алгоритма захвата частоты
        self.time = 0
        Clock.schedule_interval(self.simulate_tuning, 0.03)

        return root

    def update_bg(self, instance, value):
        self.bg_rect.size = instance.size

    def simulate_tuning(self, dt):
        self.time += dt

        # Имитируем, как струна плавно приближается к идеальной настройке
        # Сначала колеблется сильно, затем затухает около 0
        cycle = self.time % 12
        if cycle < 5:
            # Струна только дернута: болтается в районе +18 центов
            simulated_value = 18 + math.sin(self.time * 6) * 4
        elif cycle < 9:
            # Стабилизируется ближе к нулю (+3 цента)
            simulated_value = 3 + math.sin(self.time * 4) * 1.5
        else:
            # Идеальное попадание в ноль (In Tune)
            simulated_value = math.sin(self.time * 2) * 0.4

        self.gauge.value = simulated_value

        # Динамическое обновление цифровых индикаторов и их цветов
        sign = "+" if simulated_value >= 0 else ""
        self.cents_label.text = f"{sign}{simulated_value:.1f} cents"

        if abs(simulated_value) <= 1.5:
            # Идеально настроено
            self.note_label.color = get_color_from_hex('#00ff87')  # Зеленый неон
            self.cents_label.color = get_color_from_hex('#00ff87')
            self.hz_label.text = "440.00 Hz"
        elif abs(simulated_value) <= 10:
            # Близко
            self.note_label.color = get_color_from_hex('#00f2fe')  # Циан
            self.cents_label.color = get_color_from_hex('#00f2fe')
            self.hz_label.text = f"{440.00 + (simulated_value * 0.25):.2f} Hz"
        else:
            # Мимо ноты
            self.note_label.color = get_color_from_hex('#ffffff')  # Белый
            self.cents_label.color = get_color_from_hex('#ff0055')  # Розово-красный неон
            self.hz_label.text = f"{440.00 + (simulated_value * 0.25):.2f} Hz"


if __name__ == '__main__':
    TunerApp().run()
