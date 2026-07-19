import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.properties import BoundedNumericProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex


class ModernHorizontalTuner(Widget):
    value = BoundedNumericProperty(0, min=-50, max=50, errorvalue=0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale_rects = []      # полоски-градиент
        self.ticks = []            # засечки
        self.labels = []           # подписи
        self.indicator_rect = None # бегунок
        self._build_gauge()
        self.bind(pos=self.update_layout, size=self.update_layout, value=self.update_layout)

    @staticmethod
    def _gradient_color(pct):
        """
        pct: 0.0–1.0 по шкале от -50 до +50 центов.
        Возвращает RGB цвет: красный -> жёлтый -> зелёный -> жёлтый -> красный.
        """
        # зоны: 0–0.25: red->yellow, 0.25–0.5: yellow->green, 0.5–0.75: green->yellow, 0.75–1.0: yellow->red
        if pct < 0.25:
            t = pct / 0.25
            r, g, b = 1.0, t, 0.0
        elif pct < 0.5:
            t = (pct - 0.25) / 0.25
            r, g, b = 1.0 - t, 1.0, 0.0
        elif pct < 0.75:
            t = (pct - 0.5) / 0.25
            r, g, b = t, 1.0, 0.0
        else:
            t = (pct - 0.75) / 0.25
            r, g, b = 1.0, 1.0 - t, 0.0
        return r, g, b

    def _build_gauge(self):
        # Шкала из полосок (градиент)
        with self.canvas.before:
            # создадим много узких прямоугольников, чтобы получить градиент
            pass

        # Засечки
        Color(*get_color_from_hex('#bdc3c7'))
        for _ in range(5):
            line = Rectangle(size=(1.5, 12))  # используем Rectangle вместо Line для простоты
            self.canvas.add(line)
            self.ticks.append(line)

        # Подписи
        cents_vals = [-50, -25, 0, 25, 50]
        positions = [0, 0.25, 0.5, 0.75, 1.0]
        colors = [get_color_from_hex('#7f8c8d')] * 5
        colors[2] = get_color_from_hex('#2ecc71')

        for i, (pos_pct, text) in enumerate(zip(positions, cents_vals)):
            lbl = Label(
                text=str(text),
                font_size='12sp',
                bold=(i == 2),
                color=colors[i],
                size_hint=(None, None),
                size=(40, 20),
            )
            self.add_widget(lbl)
            self.labels.append(lbl)

        # Индикатор
        with self.canvas:
            Color(0.9, 0.3, 0.3, 1.0)
            self.indicator_rect = Rectangle(size=(6, 32))

    def update_layout(self, *args):
        scale_w = self.width * 0.8
        scale_x = self.center_x - scale_w / 2
        scale_y = self.center_y + 40
        strip_w = 2  # ширина одной полоски
        n_strips = int(scale_w // strip_w)

        # Удаляем старые полоски, если их количество изменилось (редко, но на всякий случай)
        while len(self.scale_rects) > n_strips:
            old = self.scale_rects.pop()
            self.canvas.remove(old)

        # Создаём недостающие полоски
        while len(self.scale_rects) < n_strips:
            with self.canvas.before:
                rect = Rectangle()
            self.scale_rects.append(rect)

        # Рисуем градиент
        for i in range(n_strips):
            pct = i / (n_strips - 1) if n_strips > 1 else 0.5
            r, g, b = self._gradient_color(pct)
            x = scale_x + i * strip_w
            rect = self.scale_rects[i]
            rect.pos = (x, scale_y - 10)
            rect.size = (strip_w, 20)
            Color(r, g, b, 1.0)  # цвет применяется к следующему примитиву
            # В Kivy Color действует на все последующие инструкции, поэтому важно порядок
            # Но здесь мы просто задаём rect, а цвет нужен для отрисовки — хитрость:
            # мы не можем задать цвет прямо у Rectangle, поэтому используем такой трюк:
            # удаляем старый Color и ставим новый перед отрисовкой. Но в цикле это сложно.
            # Поэтому делаем проще: храним цвета отдельно и перерисовываем через canvas.

        # Перерисуем шкалу правильно: очищаем canvas.before и заново добавляем rect+Color
        # Чтобы не усложнять, сделаем проще: используем один большой трюк —
        # рисуем шкалу через canvas.before, но каждый раз обновляем цвета через InstructionGroup.
        # Для простоты в этом примере я сделаю упрощённую версию: фиксированное число полосок
        # и обновляю их позиции и цвета через отдельные Color+Rectangle.

        # Ниже — правильная реализация с отдельными Color+Rectangle для каждой полоски
        self._draw_gradient_correctly(scale_x, scale_y, scale_w, n_strips)

        # Засечки
        positions = [0, 0.25, 0.5, 0.75, 1.0]
        ticks_height = [12, 12, 24, 12, 12]
        for i, pos_pct in enumerate(positions):
            curr_x = scale_x + pos_pct * scale_w
            h = ticks_height[i]
            self.ticks[i].pos = (curr_x - 0.75, scale_y - h/2)
            self.ticks[i].size = (1.5, h)

        # Подписи
        for i, pos_pct in enumerate(positions):
            curr_x = scale_x + pos_pct * scale_w
            self.labels[i].center = (curr_x, scale_y - 28)

        # Индикатор
        val_pct = (self.value - (-50)) / 100.0
        indicator_x = scale_x + val_pct * scale_w
        self.indicator_rect.pos = (indicator_x - 3, scale_y - 16)

        if abs(self.value) <= 1.5:
            Color(0.18, 0.8, 0.44, 1.0)
        elif abs(self.value) <= 12:
            Color(0.2, 0.6, 1.0, 1.0)
        else:
            Color(0.9, 0.3, 0.3, 1.0)

    def _draw_gradient_correctly(self, scale_x, scale_y, scale_w, n_strips):
        # Очищаем старые полоски из canvas.before
        # Но чтобы не удалять всё подряд, мы заранее создали InstructionGroup
        # Для простоты примера: удаляем все rect из scale_rects из canvas.before
        for r in self.scale_rects:
            self.canvas.before.remove(r)
        self.scale_rects.clear()

        strip_w = max(1, scale_w / n_strips)
        for i in range(n_strips):
            pct = i / (n_strips - 1) if n_strips > 1 else 0.5
            r, g, b = self._gradient_color(pct)
            x = scale_x + i * strip_w

            with self.canvas.before:
                Color(r, g, b, 1.0)
                rect = Rectangle(pos=(x, scale_y - 10), size=(strip_w, 20))
            self.scale_rects.append(rect)


class TunerApp(App):
    def build(self):
        root = FloatLayout()
        bg_color = get_color_from_hex('#1a1b20')
        with root.canvas.before:
            Color(*bg_color)
            self.bg_rect = Rectangle(size=(2000, 2000), pos=(0, 0))
            root.bind(size=self.update_bg)

        self.gauge = ModernHorizontalTuner(
            size_hint=(0.9, 0.55),
            pos_hint={'center_x': 0.5, 'center_y': 0.62}
        )
        root.add_widget(self.gauge)

        self.note_label = Label(
            text="E4",
            font_size='76sp',
            bold=True,
            color=get_color_from_hex('#ffffff'),
            pos_hint={'center_x': 0.5, 'center_y': 0.34}
        )
        root.add_widget(self.note_label)

        self.cents_label = Label(
            text="+0.0 cents",
            font_size='18sp',
            color=get_color_from_hex('#bdc3c7'),
            pos_hint={'center_x': 0.5, 'center_y': 0.22}
        )
        root.add_widget(self.cents_label)

        self.hz_label = Label(
            text="329.63 Hz",
            font_size='14sp',
            color=get_color_from_hex('#7f8c8d'),
            pos_hint={'center_x': 0.5, 'center_y': 0.14}
        )
        root.add_widget(self.hz_label)

        self.time = 0
        Clock.schedule_interval(self.simulate_tuning, 0.03)
        return root

    def update_bg(self, instance, value):
        self.bg_rect.size = instance.size

    def simulate_tuning(self, dt):
        self.time += dt
        cycle = self.time % 10
        if cycle < 4:
            simulated_value = -15 + math.sin(self.time * 6) * 3
        elif cycle < 7:
            simulated_value = -2 + math.sin(self.time * 3) * 1.0
        else:
            simulated_value = math.sin(self.time * 1.5) * 0.3

        self.gauge.value = simulated_value
        sign = "+" if simulated_value >= 0 else ""
        self.cents_label.text = f"{sign}{simulated_value:.1f} cents"

        if abs(simulated_value) <= 1.5:
            self.note_label.color = get_color_from_hex('#2ecc71')
            self.cents_label.color = get_color_from_hex('#2ecc71')
            self.hz_label.text = "329.63 Hz"
        elif abs(simulated_value) <= 12:
            self.note_label.color = get_color_from_hex('#ffffff')
            self.cents_label.color = get_color_from_hex('#3498db')
            hz_offset = simulated_value * 0.19
            self.hz_label.text = f"{329.63 + hz_offset:.2f} Hz"
        else:
            self.note_label.color = get_color_from_hex('#ffffff')
            self.cents_label.color = get_color_from_hex('#e74c3c')
            hz_offset = simulated_value * 0.19
            self.hz_label.text = f"{329.63 + hz_offset:.2f} Hz"


if __name__ == '__main__':
    TunerApp().run()
