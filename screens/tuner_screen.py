# screens/tuner_screen.py
"""
Улучшенный гитарный тюнер с визуализацией волны, калибровкой A4,
плавной анимацией и выбором строя
"""
import math
import struct
import pyaudio
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, Line, Ellipse
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu

from config.theme import theme
from config.logger_config import screen_logger

logger = screen_logger('Tuner')

# Настройки аудио
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
CHUNK = 1024

# Русские названия нот
NOTE_NAMES_RU = {
    'C': 'До', 'C#': 'До#', 'D': 'Ре', 'D#': 'Ре#',
    'E': 'Ми', 'F': 'Фа', 'F#': 'Фа#', 'G': 'Соль',
    'G#': 'Соль#', 'A': 'Ля', 'A#': 'Ля#', 'B': 'Си'
}

# Все ноты для отображения
NOTES_LIST = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# ============ ГИТАРНЫЕ СТРОИ ============
TUNINGS = {
    "Standard (E-A-D-G-B-E)": [
        ("E2", "6", "Ми"), ("A2", "5", "Ля"), ("D3", "4", "Ре"),
        ("G3", "3", "Соль"), ("B3", "2", "Си"), ("E4", "1", "Ми")
    ],
    "Drop D (D-A-D-G-B-E)": [
        ("D2", "6", "Ре"), ("A2", "5", "Ля"), ("D3", "4", "Ре"),
        ("G3", "3", "Соль"), ("B3", "2", "Си"), ("E4", "1", "Ми")
    ],
    "Drop C (C-G-C-F-A-D)": [
        ("C2", "6", "До"), ("G2", "5", "Соль"), ("C3", "4", "До"),
        ("F3", "3", "Фа"), ("A3", "2", "Ля"), ("D4", "1", "Ре")
    ],
    "Half Step Down (Eb-Ab-Db-Gb-Bb-Eb)": [
        ("Eb2", "6", "Миb"), ("Ab2", "5", "Ляb"), ("Db3", "4", "Реb"),
        ("Gb3", "3", "Сольb"), ("Bb3", "2", "Сиb"), ("Eb4", "1", "Миb")
    ],
    "Open G (D-G-D-G-B-D)": [
        ("D2", "6", "Ре"), ("G2", "5", "Соль"), ("D3", "4", "Ре"),
        ("G3", "3", "Соль"), ("B3", "2", "Си"), ("D4", "1", "Ре")
    ],
    "7-String Standard (B-E-A-D-G-B-E)": [
        ("B1", "7", "Си"), ("E2", "6", "Ми"), ("A2", "5", "Ля"),
        ("D3", "4", "Ре"), ("G3", "3", "Соль"), ("B3", "2", "Си"), ("E4", "1", "Ми")
    ],
    "Bass 4-String (E-A-D-G)": [
        ("E1", "4", "Ми"), ("A1", "3", "Ля"), ("D2", "2", "Ре"), ("G2", "1", "Соль")
    ],
}


class WaveformWidget(Widget):
    """Виджет для отрисовки звуковой волны"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio_data = [0.0] * CHUNK

    def update_data(self, data):
        self.audio_data = data
        self.draw()

    def draw(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.3, 0.7, 0.7, 0.8)

            if len(self.audio_data) == 0:
                return

            width = self.width
            height = self.height
            center_y = self.height / 2

            step = len(self.audio_data) / width

            for x in range(int(width)):
                start_idx = int(x * step)
                end_idx = int((x + 1) * step)
                if end_idx > len(self.audio_data):
                    end_idx = len(self.audio_data)

                if start_idx < end_idx:
                    segment = self.audio_data[start_idx:end_idx]
                    # Вычисляем среднее абсолютное значение без numpy
                    val = sum(abs(v) for v in segment) / len(segment) * height * 2 if segment else 0
                    val = min(val, height / 2)

                    y1 = center_y - val
                    y2 = center_y + val
                    Line(points=[x, y1, x, y2], width=1)

            Color(0.5, 0.5, 0.5, 0.5)
            Line(points=[0, center_y, width, center_y], width=1)


class SmoothNeedleWidget(Widget):
    """Стрелка тюнера с плавной анимацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_angle = 0
        self.needle_length = dp(80)
        self.animation = None
        self.bind(pos=self.draw, size=self.draw)

    def set_angle(self, target_angle):
        target_angle = max(-45, min(45, target_angle))

        if self.animation:
            self.animation.cancel(self)

        self.animation = Animation(current_angle=target_angle, duration=0.1, t='out_quad')
        self.animation.start(self)

    def on_current_angle(self, instance, value):
        self.draw()

    def draw(self, *args):
        self.canvas.clear()
        center_x = self.center_x
        center_y = self.center_y

        with self.canvas:
            # Шкала
            Color(0.4, 0.4, 0.4, 0.8)
            for angle in range(-45, 46, 15):
                rad = math.radians(angle)
                x = center_x + math.sin(rad) * self.needle_length * 0.8
                y = center_y + math.cos(rad) * self.needle_length * 0.8
                Line(points=[x, y, x + math.sin(rad) * 5, y + math.cos(rad) * 5], width=2)

            # Центр
            Color(0.46, 0.70, 0.71, 1)
            Ellipse(pos=(center_x - 10, center_y - 10), size=(20, 20))

            # Стрелка
            rad = math.radians(self.current_angle)
            end_x = center_x + math.sin(rad) * self.needle_length
            end_y = center_y + math.cos(rad) * self.needle_length

            if abs(self.current_angle) > 10:
                Color(0.9, 0.2, 0.2, 1)
            elif abs(self.current_angle) > 3:
                Color(0.9, 0.6, 0.1, 1)
            else:
                Color(0.2, 0.8, 0.2, 1)

            Line(points=[center_x, center_y, end_x, end_y], width=4)
            Ellipse(pos=(end_x - 5, end_y - 5), size=(10, 10))


class StyledButton(Button):
    """Кастомная кнопка в стиле приложения"""

    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = sp(10)
        self.color = theme.PRIMARY
        self.background_normal = ''
        self.background_color = [0, 0, 0, 0]
        self.size_hint = (1, 1)


class TunerScreen(MDScreen):
    """Экран гитарного тюнера"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'
        self.md_bg_color = [0, 0, 0, 0]

        # Аудио
        self.audio = None
        self.stream = None
        self.is_listening = False

        # Настройки
        self.a4_freq = 440.0
        self.current_tuning = "Standard (E-A-D-G-B-E)"
        self.current_strings = TUNINGS[self.current_tuning]
        self.selected_string = None
        self.current_frequency = 0
        self.current_cents = 0

        self.tuning_menu = None
        self.init_ui()
        logger.info('Экран тюнера создан')

    def get_note_frequency(self, note_name, octave):
        """Возвращает частоту ноты с учетом калибровки A4"""
        A4_index = NOTES_LIST.index('A')
        note_index = NOTES_LIST.index(note_name)
        semitone_diff = (octave - 4) * 12 + (note_index - A4_index)
        return self.a4_freq * (2 ** (semitone_diff / 12.0))

    def find_closest_note(self, frequency):
        """Находит ближайшую ноту из текущего строя"""
        closest_note = None
        closest_freq = 0
        min_diff = float('inf')

        for note_id, string_num, string_name in self.current_strings:
            note_name = note_id[:-1]
            octave = int(note_id[-1])
            freq = self.get_note_frequency(note_name, octave)

            diff = abs(frequency - freq)
            if diff < min_diff:
                min_diff = diff
                closest_note = f"{note_name}{octave}"
                closest_freq = freq
                self.selected_string = (note_id, string_num, string_name)

        return closest_note, closest_freq

    def init_ui(self):
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.widget import Widget

        scroll = ScrollView(size_hint=(1, 1))

        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(2), dp(16), dp(16)],
            spacing=dp(12),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # Выбор строя
        tuning_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(48), spacing=dp(8),
                                    padding=[dp(8), dp(4), dp(8), dp(4)])
        tuning_label = MDLabel(text="Строй:", size_hint_x=0.25, font_size=sp(14), theme_text_color="Custom",
                               text_color=[0.8, 0.8, 0.8, 1], valign="middle")

        # Используем Button для выбора строя
        self.tuning_btn = Button(text=self.current_tuning, size_hint_x=0.75, font_size=sp(11), color=theme.PRIMARY,
                                 background_normal='', background_color=[0, 0, 0, 0])
        self.tuning_btn.bind(on_release=self.open_tuning_menu)

        tuning_layout.add_widget(tuning_label)
        tuning_layout.add_widget(self.tuning_btn)
        main_layout.add_widget(tuning_layout)

        # Визуализация волны
        self.waveform = WaveformWidget(size_hint=(1, None), height=dp(100))
        main_layout.add_widget(self.waveform)

        # Индикатор громкости
        self.volume_label = MDLabel(text="🎤 Уровень: ---", halign="center", font_size=sp(10), theme_text_color="Custom",
                                    text_color=[0.6, 0.6, 0.6, 1], size_hint_y=None, height=dp(20))
        main_layout.add_widget(self.volume_label)

        # Карточка с нотой
        note_card = MDCard(orientation='vertical', size_hint=(1, None), height=dp(140), radius=[theme.CORNER_RADIUS],
                           md_bg_color=[0.18, 0.18, 0.18, 0.85], elevation=4, padding=[dp(16), dp(12), dp(16), dp(12)])

        self.note_label = MDLabel(text="---", halign="center", font_size=sp(56), theme_text_color="Custom",
                                  text_color=theme.PRIMARY, bold=True, size_hint_y=None, height=dp(70))
        self.string_hint_label = MDLabel(text="", halign="center", font_size=sp(12), theme_text_color="Custom",
                                         text_color=[0.7, 0.7, 0.7, 1], size_hint_y=None, height=dp(20))
        self.freq_label = MDLabel(text="0.0 Hz", halign="center", font_size=sp(14), theme_text_color="Custom",
                                  text_color=[0.8, 0.8, 0.8, 1], size_hint_y=None, height=dp(25))
        self.cents_label = MDLabel(text="0¢", halign="center", font_size=sp(14), theme_text_color="Custom",
                                   text_color=[1, 0.75, 0.1, 1], size_hint_y=None, height=dp(25))

        note_card.add_widget(self.note_label)
        note_card.add_widget(self.string_hint_label)
        note_card.add_widget(self.freq_label)
        note_card.add_widget(self.cents_label)
        main_layout.add_widget(note_card)

        # Стрелка
        self.needle = SmoothNeedleWidget(size_hint=(1, None), height=dp(160))
        main_layout.add_widget(self.needle)

        # Калибровка A4
        cal_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(40), spacing=dp(8),
                                 padding=[dp(8), dp(4), dp(8), dp(4)])
        cal_label = MDLabel(text="A4:", size_hint_x=0.2, font_size=sp(12), theme_text_color="Custom",
                            text_color=[0.8, 0.8, 0.8, 1], valign="middle")
        self.a4_label = MDLabel(text=f"{self.a4_freq} Hz", size_hint_x=0.3, font_size=sp(14), theme_text_color="Custom",
                                text_color=theme.PRIMARY, bold=True, valign="middle")

        btn_minus = Button(text="-", size_hint_x=0.15, font_size=sp(18), color=theme.PRIMARY, background_normal='',
                           background_color=[0, 0, 0, 0])
        btn_minus.bind(on_release=lambda x: self.change_a4_freq(-5))

        btn_plus = Button(text="+", size_hint_x=0.15, font_size=sp(18), color=theme.PRIMARY, background_normal='',
                          background_color=[0, 0, 0, 0])
        btn_plus.bind(on_release=lambda x: self.change_a4_freq(5))

        cal_layout.add_widget(cal_label)
        cal_layout.add_widget(self.a4_label)
        cal_layout.add_widget(btn_minus)
        cal_layout.add_widget(btn_plus)
        main_layout.add_widget(cal_layout)

        # Струны
        self.strings_container = MDBoxLayout(orientation='vertical', size_hint=(1, None), height=dp(70))
        self.update_strings_display()
        main_layout.add_widget(self.strings_container)

        # Инфо
        info_label = MDLabel(text="Выберите строй и сыграйте на струне\nТочность ±3 цента", halign="center",
                             font_size=sp(9), theme_text_color="Custom", text_color=[0.5, 0.5, 0.5, 1],
                             size_hint_y=None, height=dp(32))
        main_layout.add_widget(info_label)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

    def update_strings_display(self):
        self.strings_container.clear_widgets()
        strings_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(65), spacing=dp(4),
                                     padding=[dp(2), dp(4), dp(2), dp(4)])

        for note_id, string_num, string_name in reversed(self.current_strings):
            display_text = f"{string_num}\n{string_name}"
            btn = Button(text=display_text, size_hint=(1, 1), font_size=sp(10), color=theme.PRIMARY,
                         background_normal='', background_color=[0, 0, 0, 0])
            btn.bind(on_release=lambda x, n=note_id: self.set_reference_note(n))
            strings_layout.add_widget(btn)

        self.strings_container.add_widget(strings_layout)

    def open_tuning_menu(self, instance):
        menu_items = []
        for name in TUNINGS.keys():
            menu_items.append({
                "text": name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=name: self.select_tuning(x),
            })

        self.tuning_menu = MDDropdownMenu(caller=self.tuning_btn, items=menu_items, width_mult=4, max_height=dp(300))
        self.tuning_menu.open()

    def select_tuning(self, tuning_name):
        self.current_tuning = tuning_name
        self.current_strings = TUNINGS[tuning_name]
        self.tuning_btn.text = tuning_name
        self.update_strings_display()
        logger.info(f"Строй: {tuning_name}")
        self.freq_label.text = f"Строй: {tuning_name[:20]}..."
        Clock.schedule_once(lambda dt: self.restore_freq_label(), 2)
        if self.tuning_menu:
            self.tuning_menu.dismiss()

    def change_a4_freq(self, delta):
        new_freq = self.a4_freq + delta
        if 420 <= new_freq <= 460:
            self.a4_freq = new_freq
            self.a4_label.text = f"{self.a4_freq} Hz"
            self.freq_label.text = f"A4 = {self.a4_freq} Hz"
            Clock.schedule_once(lambda dt: self.restore_freq_label(), 1.5)

    def restore_freq_label(self):
        if self.current_frequency > 0:
            self.freq_label.text = f"{self.current_frequency:.1f} Hz"
        else:
            self.freq_label.text = "0.0 Hz"

    def set_reference_note(self, note_id):
        note_name = note_id[:-1]
        octave = int(note_id[-1])
        freq = self.get_note_frequency(note_name, octave)
        ru_name = NOTE_NAMES_RU.get(note_name, note_name)
        self.freq_label.text = f"{ru_name}: {freq:.1f} Hz"
        self.string_hint_label.text = f"Настройте струну до {ru_name}{octave}"
        self.cents_label.text_color = [0.6, 0.6, 0.6, 1]
        self.cents_label.text = "🎸 эталон"
        Clock.schedule_once(lambda dt: self.clear_string_hint(), 2)

    def clear_string_hint(self):
        self.string_hint_label.text = ""
        self.restore_labels()

    def restore_labels(self):
        self.restore_freq_label()
        self.cents_label.text_color = [1, 0.75, 0.1, 1]
        if self.current_cents != 0:
            sign = "+" if self.current_cents > 0 else ""
            self.cents_label.text = f"{sign}{self.current_cents:.0f}¢"
        else:
            self.cents_label.text = "0¢"

    def start_tuner(self):
        try:
            self.audio = pyaudio.PyAudio()
            if self.audio.get_device_count() == 0:
                raise Exception("Нет аудиоустройств")
            self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                                          frames_per_buffer=CHUNK, stream_callback=self.audio_callback)
            self.stream.start_stream()
            self.is_listening = True
            logger.info("✅ Тюнер запущен")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            self.note_label.text = "❌"
            self.freq_label.text = "Нет микрофона"

    def audio_callback(self, in_data, frame_count, time_info, status):
        if not self.is_listening:
            return (None, pyaudio.paContinue)
        try:
            # Преобразуем байты в список float без numpy
            data = list(struct.unpack('f' * (len(in_data) // 4), in_data))

            # Вычисляем уровень громкости
            level = math.sqrt(sum(x * x for x in data) / len(data)) if data else 0
            Clock.schedule_once(lambda dt: self.update_waveform(data), 0)
            if level < 0.005:
                Clock.schedule_once(lambda dt: self.show_silence())
                return (None, pyaudio.paContinue)
            frequency = self.detect_pitch(data, RATE)
            if frequency > 0:
                self.current_frequency = frequency
                Clock.schedule_once(lambda dt: self.update_tuner_display(frequency), 0)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        return (None, pyaudio.paContinue)

    def update_waveform(self, data):
        if hasattr(self, 'waveform') and len(data) > 0:
            max_val = max(abs(x) for x in data) if data else 1
            normalized = [x / (max_val + 0.001) for x in data]
            self.waveform.update_data(normalized[:min(CHUNK, len(normalized))])

            # Вычисляем уровень в dB
            rms = math.sqrt(sum(x * x for x in data) / len(data)) if data else 0
            level_db = -40 if rms < 0.01 else min(0, int(20 * math.log10(rms) + 0.5))
            self.volume_label.text = f"🎤 Уровень: {level_db} dB"

    def detect_pitch(self, data, sample_rate):
        """Определяет частоту звука (без numpy)"""
        if len(data) == 0:
            return 0

        # Простая оконная функция Ханна (на чистом Python)
        window = [0.5 * (1 - math.cos(2 * math.pi * i / (len(data) - 1))) for i in range(len(data))]
        data = [data[i] * window[i] for i in range(len(data))]

        # Автокорреляция на чистом Python
        corr = []
        for i in range(len(data)):
            corr_val = 0
            for j in range(len(data) - i):
                corr_val += data[j] * data[j + i]
            corr.append(corr_val)

        min_freq, max_freq = 40, 400
        min_lag = int(sample_rate / max_freq)
        max_lag = int(sample_rate / min_freq)

        if max_lag >= len(corr):
            max_lag = len(corr) - 1
        if min_lag >= max_lag or min_lag < 0:
            return 0

        # Ищем максимум автокорреляции
        try:
            search = corr[min_lag:max_lag + 1]
            peak_idx = search.index(max(search)) + min_lag
        except (ValueError, IndexError):
            return 0

        if 0 < peak_idx < len(corr) - 1:
            try:
                y0, y1, y2 = corr[peak_idx - 1], corr[peak_idx], corr[peak_idx + 1]
                if y1 > 0:
                    peak_idx += (y2 - y0) / (2 * (2 * y1 - y2 - y0))
            except (ValueError, IndexError):
                pass

        frequency = sample_rate / peak_idx if peak_idx > 0 else 0
        return frequency if min_freq <= frequency <= max_freq else 0

    def show_silence(self):
        if hasattr(self, 'note_label') and self.note_label.text not in ["---", "❌", "🎤"]:
            self.note_label.text = "🎤"
            self.freq_label.text = "Сыграйте ноту"

    def update_tuner_display(self, frequency):
        closest_note, target_freq = self.find_closest_note(frequency)
        if closest_note:
            try:
                cents = max(-50, min(50, 1200 * math.log2(frequency / target_freq)))
            except (ValueError, ZeroDivisionError):
                cents = 0
            self.current_cents = cents
            note_name, octave = closest_note[:-1], closest_note[-1]
            ru_name = NOTE_NAMES_RU.get(note_name, note_name)

            self.note_label.text = f"{ru_name}{octave}"
            self.freq_label.text = f"{frequency:.1f} Hz"
            if self.selected_string:
                _, string_num, string_name = self.selected_string
                self.string_hint_label.text = f"Струна {string_num} ({string_name})"

            sign = "+" if cents > 0 else ""
            self.cents_label.text = f"{sign}{cents:.0f}¢"

            if abs(cents) < 3:
                self.cents_label.text_color = [0.2, 0.8, 0.2, 1]
                self.note_label.text_color = [0.2, 0.8, 0.2, 1]
            elif abs(cents) < 10:
                self.cents_label.text_color = [0.9, 0.6, 0.1, 1]
                self.note_label.text_color = [0.9, 0.6, 0.1, 1]
            else:
                self.cents_label.text_color = [0.9, 0.2, 0.2, 1]
                self.note_label.text_color = theme.PRIMARY

            self.needle.set_angle(cents * 0.9)

    def stop_tuner(self):
        self.is_listening = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass

    def on_pre_leave(self):
        self.stop_tuner()

    def on_enter(self):
        self.start_tuner()