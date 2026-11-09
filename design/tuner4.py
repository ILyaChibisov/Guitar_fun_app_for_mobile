import threading

import numpy as np
import sounddevice as sd

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from kivymd.app import MDApp


# Стандартный строй гитары: от шестой струны к первой
STRINGS = [
    ("E2", 82.4069),
    ("A2", 110.0000),
    ("D3", 146.8324),
    ("G3", 195.9977),
    ("B3", 246.9417),
    ("E4", 329.6276),
]

NOTE_NAMES = ["C", "C♯", "D", "D♯", "E", "F",
              "F♯", "G", "G♯", "A", "A♯", "B"]

BG = (0.035, 0.047, 0.075, 1)
PANEL = (0.075, 0.092, 0.13, 1)
ACCENT = (0.40, 0.95, 0.72, 1)
MUTED = (0.56, 0.62, 0.72, 1)


class Panel(BoxLayout):
    """Карточка с мягким скруглённым фоном."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = kwargs.get("padding", 14)
        with self.canvas.before:
            Color(*PANEL)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size


class SoftButton(Button):
    fill_color = ListProperty([0.13, 0.16, 0.22, 1])
    text_color = ListProperty([0.93, 0.96, 1, 1])

    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("color", self.text_color)
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw, state=self._draw,
                  fill_color=self._draw, text_color=self._update_text_color)
        self._draw()

    def _update_text_color(self, *_):
        self.color = self.text_color

    def _draw(self, *_):
        self.canvas.before.clear()
        color = self.fill_color
        if self.state == "down":
            color = [min(1, c * 1.18) for c in color[:3]] + [color[3]]
        with self.canvas.before:
            Color(*color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[14])


class TunerGauge(Widget):
    cents = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.redraw, size=self.redraw, cents=self.redraw)
        self.redraw()

    def redraw(self, *_):
        self.canvas.clear()

        cx = self.center_x
        cy = self.y + 22
        radius = min(self.width * 0.43, self.height * 0.82)

        with self.canvas:
            # Основа шкалы и центральная зона точной настройки
            Color(0.22, 0.27, 0.35, 1)
            Line(circle=(cx, cy, radius, 0, 180), width=3)

            Color(0.25, 0.88, 0.64, 1)
            Line(circle=(cx, cy, radius, 81, 99), width=5)

            # Деления шкалы
            for value in range(-50, 51, 10):
                angle = np.pi - ((value + 50) / 100) * np.pi
                inner = radius - (12 if value % 20 == 0 else 7)
                x1 = cx + np.cos(angle) * inner
                y1 = cy + np.sin(angle) * inner
                x2 = cx + np.cos(angle) * radius
                y2 = cy + np.sin(angle) * radius
                Color(0.62, 0.69, 0.78, 0.9)
                Line(points=[x1, y1, x2, y2], width=1.3)

            # Стрелка
            value = max(-50, min(50, self.cents))
            angle = np.pi - ((value + 50) / 100) * np.pi
            needle_len = radius - 18
            nx = cx + np.cos(angle) * needle_len
            ny = cy + np.sin(angle) * needle_len

            Color(0.40, 0.95, 0.72, 1)
            Line(points=[cx, cy, nx, ny], width=2.5)
            Ellipse(pos=(cx - 6, cy - 6), size=(12, 12))


class GuitarTuner(MDApp):
    def build(self):
        self.title = "TONE — Guitar Tuner"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"

        self.audio_stream = None
        self.audio_lock = threading.Lock()
        self.audio_buffer = np.zeros(8192, dtype=np.float32)
        self.running = False
        self.selected_string = None  # None означает автоматический выбор

        self.root_layout = FloatLayout()
        with self.root_layout.canvas.before:
            Color(*BG)
            self.background = Rectangle(
                pos=self.root_layout.pos, size=self.root_layout.size
            )
        self.root_layout.bind(
            pos=lambda w, p: setattr(self.background, "pos", p),
            size=lambda w, s: setattr(self.background, "size", s),
        )

        page = BoxLayout(
            orientation="vertical",
            padding=[22, 18, 22, 18],
            spacing=12,
            size_hint=(1, 1),
        )
        self.root_layout.add_widget(page)

        # Заголовок
        header = BoxLayout(size_hint_y=None, height=48, spacing=10)
        title = Label(
            text="[b]TONE[/b]  [color=66F3B8]STUDIO[/color]",
            markup=True, font_size="22sp", halign="left",
        )
        title.bind(size=lambda w, s: setattr(w, "text_size", s))
        header.add_widget(title)
        header.add_widget(Label(
            text="GUITAR TUNER", color=MUTED, font_size="11sp",
            size_hint_x=None, width=110,
        ))
        page.add_widget(header)

        intro = Label(
            text="Настрой гитару точно — струна за струной",
            color=MUTED, font_size="14sp", size_hint_y=None, height=28,
            halign="left",
        )
        intro.bind(size=lambda w, s: setattr(w, "text_size", s))
        page.add_widget(intro)

        # Основная карточка
        card = Panel(
            orientation="vertical",
            padding=[18, 16, 18, 12],
            spacing=4,
            size_hint_y=1,
        )
        page.add_widget(card)

        card.add_widget(Label(
            text="СЛУШАЮЩАЯ НОТА", color=MUTED, font_size="11sp",
            size_hint_y=None, height=22,
        ))

        self.note_label = Label(
            text="—", color=(0.95, 0.98, 1, 1), font_size="58sp",
            bold=True, size_hint_y=None, height=76,
        )
        card.add_widget(self.note_label)

        self.string_label = Label(
            text="Включи микрофон и сыграй одну струну",
            color=MUTED, font_size="14sp", size_hint_y=None, height=28,
        )
        card.add_widget(self.string_label)

        self.gauge = TunerGauge(size_hint_y=1)
        card.add_widget(self.gauge)

        self.cents_label = Label(
            text="0¢", color=ACCENT, font_size="26sp", bold=True,
            size_hint_y=None, height=38,
        )
        card.add_widget(self.cents_label)

        self.advice_label = Label(
            text="СТРУНА НАСТРОЕНА", color=MUTED, font_size="11sp",
            size_hint_y=None, height=24,
        )
        card.add_widget(self.advice_label)

        # Выбор струны
        page.add_widget(Label(
            text="ЦЕЛЕВАЯ СТРУНА", color=MUTED, font_size="11sp",
            size_hint_y=None, height=22, halign="left",
        ))

        self.string_row = BoxLayout(size_hint_y=None, height=54, spacing=7)
        page.add_widget(self.string_row)
        self.string_buttons = []

        auto_button = SoftButton(
            text="AUTO", fill_color=[0.12, 0.22, 0.22, 1],
            text_color=ACCENT, font_size="12sp",
        )
        auto_button.bind(on_release=lambda *_: self.select_string(None))
        self.string_row.add_widget(auto_button)
        self.string_buttons.append(auto_button)

        for i, (name, _) in enumerate(STRINGS):
            button = SoftButton(
                text=name, font_size="13sp",
                fill_color=[0.13, 0.16, 0.22, 1],
            )
            button.bind(on_release=lambda _btn, index=i: self.select_string(index))
            self.string_row.add_widget(button)
            self.string_buttons.append(button)

        # Кнопка микрофона и статус
        self.start_button = SoftButton(
            text="●   НАЧАТЬ НАСТРОЙКУ",
            size_hint_y=None, height=56,
            fill_color=[0.20, 0.78, 0.57, 1],
            text_color=[0.025, 0.08, 0.065, 1],
            font_size="14sp",
        )
        self.start_button.bind(on_release=self.toggle_mic)
        page.add_widget(self.start_button)

        self.status_label = Label(
            text="Микрофон выключен",
            color=MUTED, font_size="12sp", size_hint_y=None, height=24,
        )
        page.add_widget(self.status_label)

        Clock.schedule_interval(self.refresh_tuner, 0.12)
        self.update_string_buttons()
        return self.root_layout

    def select_string(self, index):
        self.selected_string = index
        self.update_string_buttons()

    def update_string_buttons(self):
        for i, button in enumerate(self.string_buttons):
            active = (i == 0 and self.selected_string is None) or (
                i > 0 and self.selected_string == i - 1
            )
            button.fill_color = (
                [0.15, 0.34, 0.29, 1] if active else [0.13, 0.16, 0.22, 1]
            )
            button.text_color = ACCENT if active else [0.85, 0.89, 0.95, 1]

    def toggle_mic(self, *_):
        if self.running:
            self.stop_mic()
        else:
            self.start_mic()

    def start_mic(self):
        try:
            self.audio_stream = sd.InputStream(
                samplerate=44100,
                channels=1,
                dtype="float32",
                blocksize=1024,
                callback=self.audio_callback,
            )
            self.audio_stream.start()
            self.running = True
            self.status_label.text = "Микрофон активен · сыграй открытую струну"
            self.start_button.text = "■   ОСТАНОВИТЬ"
            self.start_button.fill_color = [0.48, 0.22, 0.27, 1]
            self.start_button.text_color = [1, 0.88, 0.90, 1]
        except Exception as exc:
            self.status_label.text = f"Не удалось открыть микрофон: {exc}"

    def stop_mic(self):
        self.running = False
        if self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None

        self.status_label.text = "Микрофон выключен"
        self.start_button.text = "●   НАЧАТЬ НАСТРОЙКУ"
        self.start_button.fill_color = [0.20, 0.78, 0.57, 1]
        self.start_button.text_color = [0.025, 0.08, 0.065, 1]

    def audio_callback(self, indata, frames, time_info, status):
        chunk = indata[:, 0].copy()
        with self.audio_lock:
            self.audio_buffer = np.concatenate(
                (self.audio_buffer, chunk)
            )[-8192:]

    @staticmethod
    def detect_pitch(samples, sample_rate=44100):
        samples = samples.astype(np.float32)
        samples -= np.mean(samples)

        rms = np.sqrt(np.mean(samples * samples))
        if rms < 0.003:
            return None, 0

        # Автокорреляция через FFT
        windowed = samples * np.hanning(len(samples))
        size = 1 << (2 * len(windowed) - 1).bit_length()
        spectrum = np.fft.rfft(windowed, n=size)
        corr = np.fft.irfft(spectrum * np.conj(spectrum), n=size)[:len(windowed)]

        if corr[0] <= 0:
            return None, 0
        corr /= corr[0]

        min_lag = int(sample_rate / 400)
        max_lag = min(int(sample_rate / 65), len(corr) // 2)
        if max_lag <= min_lag:
            return None, 0

        region = corr[min_lag:max_lag]
        peak_lag = int(np.argmax(region)) + min_lag
        confidence = float(corr[peak_lag])

        if confidence < 0.35:
            return None, confidence

        # Уточнение положения пика для более точной частоты
        if 1 <= peak_lag < len(corr) - 1:
            left, center, right = corr[peak_lag - 1:peak_lag + 2]
            denom = left - 2 * center + right
            if abs(denom) > 1e-9:
                peak_lag += 0.5 * (left - right) / denom

        return sample_rate / peak_lag, confidence

    def refresh_tuner(self, _dt):
        if not self.running:
            return

        with self.audio_lock:
            samples = self.audio_buffer.copy()

        frequency, confidence = self.detect_pitch(samples)
        if frequency is None:
            return

        # Нота, ближайшая к услышанной частоте
        midi = int(round(69 + 12 * np.log2(frequency / 440.0)))
        note = NOTE_NAMES[midi % 12]
        octave = midi // 12 - 1
        self.note_label.text = f"{note}{octave}"

        # Авто: ближайшая стандартная гитарная струна.
        # Ручной режим: сравниваем с выбранной струной.
        if self.selected_string is None:
            index = int(np.argmin([
                abs(1200 * np.log2(frequency / target))
                for _, target in STRINGS
            ]))
        else:
            index = self.selected_string

        string_name, target_frequency = STRINGS[index]
        cents = 1200 * np.log2(frequency / target_frequency)

        self.gauge.cents = cents
        self.cents_label.text = f"{cents:+.0f}¢"
        self.string_label.text = (
            f"Цель: струна {string_name}  ·  "
            f"{frequency:.1f} Гц  ·  сигнал {confidence:.0%}"
        )

        if abs(cents) <= 5:
            self.advice_label.text = "●  СТРУНА НАСТРОЕНА"
            self.advice_label.color = ACCENT
        elif cents < 0:
            self.advice_label.text = "СЛИШКОМ НИЗКО · ПОДТЯНИ СТРУНУ"
            self.advice_label.color = (1, 0.68, 0.36, 1)
        else:
            self.advice_label.text = "СЛИШКОМ ВЫСОКО · ОСЛАБЬ СТРУНУ"
            self.advice_label.color = (1, 0.52, 0.48, 1)

    def on_stop(self):
        self.stop_mic()


if __name__ == "__main__":
    GuitarTuner().run()