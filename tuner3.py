import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle
from kivy.properties import BoundedNumericProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex


class ModernHorizontalTuner(Widget):
    # Отклонение от -50 до +50 центов
    value = BoundedNumericProperty(0, min=-50, max=50, errorvalue=0)

    def __init__(self, **kwargs):
        super(ModernHorizontalTuner, self).__init__(**kwargs)
        self.labels = []
        self.bind(pos=self.update_gauge, size=self.update_gauge, value=self.update_gauge)

    def update_gauge(self, *args):
        self.canvas.clear()
        for label in self.labels:
            if label.parent:
                self.remove_widget(label)
        self.labels.clear()

        # Размеры горизонтальной шкалы
        scale_w = self.width * 0.8
        scale_x = self.center_x - scale_w / 2
        scale_y = self.center_y + 40

        with self.canvas:
            # 1. ОСНОВНАЯ ГОРИЗОНТАЛЬНАЯ ЛИНИЯ (Тёмно-серая подложка)
            Color(*get_color_from_hex('#2c3e50'))
            Line(points=[scale_x, scale_y, scale_x + scale_w, scale_y], width=2)

            # 2. СЕРЕБРЯНЫЕ ВЕРТИКАЛЬНЫЕ ЗАСЕЧКИ (-50, -25, 0, 25, 50)
            Color(*get_color_from_hex('#7f8c8d'))
            positions = [0, 0.25, 0.5, 0.75, 1.0]  # Процентные точки на шкале
            for pos_pct in positions:
                curr_x = scale_x + (pos_pct * scale_w)
                # Центральная засечка (0 центов) длиннее остальных
                tick_h = 24 if pos_pct == 0.5 else 12
                Line(points=[curr_x, scale_y - tick_h / 2, curr_x, scale_y + tick_h / 2], width=1.5)

        # 3. ДОБАВЛЕНИЕ ПОДПИСЕЙ К ЗАСЕЧКАМ
        cents_vals = {0: "-50", 0.25: "-25", 0.5: "0", 0.75: "+25", 1.0: "+50"}
        for pos_pct, text in cents_vals.items():
            curr_x = scale_x + (pos_pct * scale_w)

            # Зелёный цвет для нуля, серый для остальных
            is_zero = (pos_pct == 0.5)
            lbl_color = get_color_from_hex('#2ecc71') if is_zero else get_color_from_hex('#7f8c8d')

            lbl = Label(
                text=text,
                font_size='12sp',
                bold=is_zero,
                color=lbl_color,
                size_hint=(None, None),
                size=(40, 20),
                center=(curr_x, scale_y - 25)
            )
            self.add_widget(lbl)
            self.labels.append(lbl)

        # 4. ОТРИСОВКА ДИНАМИЧЕСКОГО БЕГУНКА (ИНДИКАТОРА)
        # Переводим текущее значение центов (-50...50) в позицию по оси X
        val_pct = (self.value - (-50)) / 100.0
        indicator_x = scale_x + (val_pct * scale_w)

        with self.canvas:
            # Цвет индикатора зависит от точности (чистые независимые вызовы Color без списков)
            if abs(self.value) <= 1.5:
                Color(0.18, 0.8, 0.44, 1.0)  # Зелёный
                ind_w = 4
            elif abs(self.value) <= 12:
                Color(0.2, 0.6, 1.0, 1.0)  # Синий
                ind_w = 2.5
            else:
                Color(0.9, 0.3, 0.3, 1.0)  # Красный
                ind_w = 2.5

            # Рисуем яркую вертикальную линию текущего положения
            Line(points=[indicator_x, scale_y - 18, indicator_x, scale_y + 18], width=ind_w)


class TunerApp(App):
    def build(self):
        root = FloatLayout()

        # Глубокий тёмный минималистичный фон
        with root.canvas.before:
            Color(*get_color_from_hex('#111215'))
            self.bg_rect = Rectangle(size=(2000, 2000), pos=(0, 0))
            root.bind(size=self.update_bg)

        # Добавляем горизонтальный тюнер
        self.gauge = ModernHorizontalTuner(
            size_hint=(0.9, 0.6),
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )
        root.add_widget(self.gauge)

        # КРУПНЫЙ ЦИФРОВОЙ ДИСПЛЕЙ НОТЫ
        self.note_label = Label(
            text="E4",
            font_size='82sp',
            bold=True,
            color=get_color_from_hex('#ffffff'),
            pos_hint={'center_x': 0.5, 'center_y': 0.32}
        )
        root.add_widget(self.note_label)

        # ЦИФРОВОЙ ТЕКСТ ЦЕНТОВ
        self.cents_label = Label(
            text="+0.0 cents",
            font_size='18sp',
            color=get_color_from_hex('#7f8c8d'),
            pos_hint={'center_x': 0.5, 'center_y': 0.18}
        )
        root.add_widget(self.cents_label)

        # ТЕКСТ С ТОЧНОЙ ЧАСТОТОЙ ГЕРЦ
        self.hz_label = Label(
            text="329.63 Hz",
            font_size='14sp',
            color=get_color_from_hex('#34495e'),
            pos_hint={'center_x': 0.5, 'center_y': 0.10}
        )
        root.add_widget(self.hz_label)

        # Плавная симуляция струны Ми (E4 = 329.63 Гц)
        self.time = 0
        Clock.schedule_interval(self.simulate_tuning, 0.03)

        return root

    def update_bg(self, instance, value):
        self.bg_rect.size = instance.size

    def simulate_tuning(self, dt):
        self.time += dt

        cycle = self.time % 10
        if cycle < 4:
            # Первое извлечение: струна низит (-15 центов) с небольшим затухающим дрожанием
            simulated_value = -15 + math.sin(self.time * 6) * 3
        elif cycle < 7:
            # Стабилизация у центра (-2 цента)
            simulated_value = -2 + math.sin(self.time * 3) * 1.0
        else:
            # Идеальное попадание в ноль (In Tune)
            simulated_value = math.sin(self.time * 1.5) * 0.3

        self.gauge.value = simulated_value

        # Форматируем текст
        sign = "+" if simulated_value >= 0 else ""
        self.cents_label.text = f"{sign}{simulated_value:.1f} cents"

        # Динамическое изменение цвета текста
        if abs(simulated_value) <= 1.5:
            self.note_label.color = get_color_from_hex('#2ecc71')  # Зелёный
            self.cents_label.color = get_color_from_hex('#2ecc71')
            self.hz_label.text = "329.63 Hz"
        elif abs(simulated_value) <= 12:
            self.note_label.color = get_color_from_hex('#ffffff')  # Белый
            self.cents_label.color = get_color_from_hex('#3498db')  # Синий
            self.hz_label.text = f"{329.63 + (simulated_value * 0.19):.2f} Hz"
        else:
            self.note_label.color = get_color_from_hex('#ffffff')
            self.cents_label.color = get_color_from_hex('#e74c3c')  # Красный
            self.hz_label.text = f"{329.63 + (simulated_value * 0.19):.2f} Hz"


if __name__ == '__main__':
    TunerApp().run()
