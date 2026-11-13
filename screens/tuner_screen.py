# screens/tuner_screen.py
"""
Экран гитарного тюнера — горизонтальная шкала + эталонные ноты.
Адаптирован под 3 темы (green, dark, light) и 6 языков.

ОБНОВЛЕНИЯ:
  - Профессиональный алгоритм YIN для точного определения частоты (без скачков октав).
  - Ручной режим фиксации выбранной струны (Manual Mode).
  - Плавное сглаживание частоты (EMA-фильтр).
  - Увеличенный буфер (2048) для уверенного захвата басов.
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Triangle, RoundedRectangle
from kivy.core.text import Label as CoreLabel
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.utils import platform
from io import BytesIO
import math
import threading
import struct
import time
import sys
import os
import array
import tempfile
from kivy.core.audio import SoundLoader

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.app import MDApp
from kivy.uix.behaviors import ButtonBehavior

from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from utils.notifications import notify
from state.settings_state import settings_state as settings_manager
from utils.localization import get_text

logger = screen_logger('Tuner')

IS_WINDOWS = sys.platform in ('win32', 'win64')
IS_ANDROID = platform == 'android'

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name): return None

try:
    from utils.android_audio import get_audio_recorder, set_debug_callback
    HAS_AUDIO_RECORDER = True
except ImportError:
    HAS_AUDIO_RECORDER = False

HAS_PYAUDIO = False
HAS_SOUNDDEVICE = False

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    pass

try:
    import sounddevice as sd
    import numpy as np
    HAS_SOUNDDEVICE = True
except ImportError:
    pass

# Увеличенный буфер для лучшего захвата низких частот
SAMPLE_RATE = 44100
CHUNK_SIZE = 2048


# ============================================================
# ЦВЕТА (палитра согласована с ChordsColors для меню аккордов)
# ============================================================

class TunerColors:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light': return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark': return [1.0, 0.5, 0.0, 1]
        else: return [0.46, 0.70, 0.71, 1]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light': return [0.1, 0.1, 0.1, 1]
        else: return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light': return [0.4, 0.4, 0.4, 1]
        else: return [1, 1, 1, 0.5]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light': return [0.95, 0.95, 0.95, 1]
        elif theme_id == 'dark': return [0.15, 0.15, 0.15, 1]
        else: return [0, 0, 0, 0.15]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light': return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark': return [1.0, 0.5, 0.0, 0.5]
        else: return [0.46, 0.70, 0.71, 0.4]

    @staticmethod
    def get_card_line_width(theme_id): return 1.5

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'dark': return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light': return [0.1, 0.55, 0.3, 1]
        else: return [1, 1, 1, 0.5]

    @staticmethod
    def get_divider_color(theme_id):
        if theme_id == 'light': return [0.1, 0.55, 0.3, 0.6]
        elif theme_id == 'dark': return [1.0, 0.5, 0.0, 0.6]
        else: return [0.46, 0.70, 0.71, 0.55]

    @staticmethod
    def get_note_bg(theme_id):
        if theme_id == 'light': return [1, 1, 1, 1]
        elif theme_id == 'dark': return [0.15, 0.15, 0.15, 1]
        else: return [0, 0, 0, 0.15]

    @staticmethod
    def get_note_line(theme_id):
        if theme_id == 'light': return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark': return [1.0, 0.5, 0.0, 0.5]
        else: return [0.46, 0.70, 0.71, 0.4]

    @staticmethod
    def get_note_line_width(theme_id): return 1.5


# ============ СТРОИ ГИТАР ============
TUNINGS = {
    'standard_6': {
        'name_key': 'tuning_standard_6', 'strings': 6,
        'notes': ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        'freqs': [82.41, 110.00, 146.83, 196.00, 246.94, 329.63],
        'note_names': ['E', 'A', 'D', 'G', 'B', 'E'],
    },
    'drop_d': {
        'name_key': 'tuning_drop_d', 'strings': 6,
        'notes': ['D2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        'freqs': [73.42, 110.00, 146.83, 196.00, 246.94, 329.63],
        'note_names': ['D', 'A', 'D', 'G', 'B', 'E'],
    },
    'open_g': {
        'name_key': 'tuning_open_g', 'strings': 6,
        'notes': ['D2', 'G2', 'D3', 'G3', 'B3', 'D4'],
        'freqs': [73.42, 98.00, 146.83, 196.00, 246.94, 293.66],
        'note_names': ['D', 'G', 'D', 'G', 'B', 'D'],
    },
    'open_d': {
        'name_key': 'tuning_open_d', 'strings': 6,
        'notes': ['D2', 'A2', 'D3', 'F#3', 'A3', 'D4'],
        'freqs': [73.42, 110.00, 146.83, 185.00, 220.00, 293.66],
        'note_names': ['D', 'A', 'D', 'F#', 'A', 'D'],
    },
    'dadgad': {
        'name_key': 'tuning_dadgad', 'strings': 6,
        'notes': ['D2', 'A2', 'D3', 'G3', 'A3', 'D4'],
        'freqs': [73.42, 110.00, 146.83, 196.00, 220.00, 293.66],
        'note_names': ['D', 'A', 'D', 'G', 'A', 'D'],
    },
    'half_step_down': {
        'name_key': 'tuning_half_step_down', 'strings': 6,
        'notes': ['Eb2', 'Ab2', 'Db3', 'Gb3', 'Bb3', 'Eb4'],
        'freqs': [77.78, 103.83, 138.59, 185.00, 233.08, 311.13],
        'note_names': ['Eb', 'Ab', 'Db', 'Gb', 'Bb', 'Eb'],
    },
    'bass_4': {
        'name_key': 'tuning_bass_4', 'strings': 4,
        'notes': ['E1', 'A1', 'D2', 'G2'],
        'freqs': [41.20, 55.00, 73.42, 98.00],
        'note_names': ['E', 'A', 'D', 'G'],
    },
    'bass_5': {
        'name_key': 'tuning_bass_5', 'strings': 5,
        'notes': ['B0', 'E1', 'A1', 'D2', 'G2'],
        'freqs': [30.87, 41.20, 55.00, 73.42, 98.00],
        'note_names': ['B', 'E', 'A', 'D', 'G'],
    },
    'ukulele': {
        'name_key': 'tuning_ukulele', 'strings': 4,
        'notes': ['G4', 'C4', 'E4', 'A4'],
        'freqs': [392.00, 261.63, 329.63, 440.00],
        'note_names': ['G', 'C', 'E', 'A'],
    },
}

NOTES = {
    'B0': 30.87, 'C1': 32.70, 'C#1': 34.65, 'D1': 36.71, 'D#1': 38.89,
    'E1': 41.20, 'F1': 43.65, 'F#1': 46.25, 'G1': 49.00, 'G#1': 51.91,
    'A1': 55.00, 'A#1': 58.27, 'B1': 61.74, 'C2': 65.41, 'C#2': 69.30,
    'D2': 73.42, 'D#2': 77.78, 'E2': 82.41, 'F2': 87.31, 'F#2': 92.50,
    'G2': 98.00, 'G#2': 103.83, 'A2': 110.00, 'A#2': 116.54, 'B2': 123.47,
    'C3': 130.81, 'C#3': 138.59, 'D3': 146.83, 'D#3': 155.56, 'E3': 164.81,
    'F3': 174.61, 'F#3': 185.00, 'G3': 196.00, 'G#3': 207.65, 'A3': 220.00,
    'A#3': 233.08, 'B3': 246.94, 'C4': 261.63, 'C#4': 277.18, 'D4': 293.66,
    'D#4': 311.13, 'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00,
    'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88, 'C5': 523.25,
    'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25, 'E5': 659.25, 'F5': 698.46,
    'F#5': 739.99, 'G5': 783.99, 'G#5': 830.61, 'A5': 880.00, 'A#5': 932.33,
    'B5': 987.77, 'C6': 1046.50, 'C#6': 1108.73, 'D6': 1174.66, 'D#6': 1244.51,
    'E6': 1318.51, 'F6': 1396.91, 'F#6': 1479.98, 'G6': 1567.98, 'G#6': 1661.22,
    'A6': 1760.00, 'A#6': 1864.66, 'B6': 1975.53,
}


def get_temp_path():
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except Exception:
            pass
    return tempfile.gettempdir()


def generate_reference_note(frequency, duration=2.0, volume=0.6, string_type='mid'):
    try:
        from utils.generate_sounds import generate_realistic_string_sound
        return generate_realistic_string_sound(
            frequency=frequency,
            duration=duration,
            volume=volume,
            string_type=string_type
        )
    except Exception as e:
        logger.error(f"Не удалось вызвать generate_realistic_string_sound: {e}")
        return array.array('h')


def clean_temp_file(path):
    try:
        if os.path.exists(path):
            os.unlink(path)
    except Exception:
        pass


# ============ ПРОФЕССИОНАЛЬНЫЙ ДЕТЕКТОР YIN ============

def detect_pitch(audio_data, sample_rate=SAMPLE_RATE, min_freq=28.0, max_freq=850.0):
    """
    Определение основной частоты методом YIN (разностная функция с кумулятивной нормализацией).
    Исключает ошибки на октаву вверх и стабильно работает на низких частотах (от 28 Гц).
    """
    if not audio_data or len(audio_data) < 512:
        return 0.0

    try:
        if isinstance(audio_data, bytes):
            if len(audio_data) % 2 != 0:
                return 0.0
            samples = struct.unpack(f'{len(audio_data) // 2}h', audio_data)
        else:
            samples = audio_data
    except Exception:
        return 0.0

    n = len(samples)
    if n < 512:
        return 0.0

    # Проверка уровня сигнала (Noise Gate)
    mean_val = sum(samples) / n
    centered = [s - mean_val for s in samples]
    rms = math.sqrt(sum(s * s for s in centered) / n)
    if rms < 80.0:  # Отсекаем тишину и слабый фоновый шум
        return 0.0

    min_tau = max(2, int(sample_rate / max_freq))
    max_tau = min(n // 2, int(sample_rate / min_freq))
    if min_tau >= max_tau:
        return 0.0

    # Шаг 1 и 2: Разностная функция d(tau) и кумулятивная нормализация CMNDF
    yin_buffer = [0.0] * (max_tau + 1)
    yin_buffer[0] = 1.0
    running_sum = 0.0

    for tau in range(1, max_tau + 1):
        diff_sum = 0.0
        # Шаг 2 для ускорения на длинных окнах без потери точности на басах
        step = 2 if tau > 200 else 1
        limit = n - max_tau
        for j in range(0, limit, step):
            delta = centered[j] - centered[j + tau]
            diff_sum += delta * delta
        if step == 2:
            diff_sum *= 2.0

        yin_buffer[tau] = diff_sum
        running_sum += diff_sum
        if running_sum > 0:
            yin_buffer[tau] *= tau / running_sum
        else:
            yin_buffer[tau] = 1.0

    # Шаг 3: Поиск первого локального минимума ниже порога уверенности (0.15)
    threshold = 0.15
    tau_estimate = -1
    for tau in range(min_tau, max_tau):
        if yin_buffer[tau] < threshold:
            while tau + 1 < max_tau and yin_buffer[tau + 1] < yin_buffer[tau]:
                tau += 1
            tau_estimate = tau
            break

    # Если строгий порог не пройден, берем глобальный минимум, если сигнал достаточно периодичен
    if tau_estimate == -1:
        min_val = min(yin_buffer[min_tau:max_tau])
        if min_val < 0.35:
            tau_estimate = yin_buffer.index(min_val, min_tau, max_tau)
        else:
            return 0.0

    # Шаг 4: Параболическая интерполяция для точности до долей герца
    better_tau = float(tau_estimate)
    if min_tau < tau_estimate < max_tau - 1:
        s0 = yin_buffer[tau_estimate - 1]
        s1 = yin_buffer[tau_estimate]
        s2 = yin_buffer[tau_estimate + 1]
        denom = 2.0 * (2.0 * s1 - s2 - s0)
        if denom != 0:
            better_tau += (s2 - s0) / denom

    if better_tau <= 0:
        return 0.0

    freq = sample_rate / better_tau
    if min_freq <= freq <= max_freq:
        return freq
    return 0.0


def freq_to_note(freq, tuning_note_names=None, tuning_freqs=None):
    if freq <= 0:
        return None, None, None
    if tuning_note_names and tuning_freqs:
        closest_note, closest_freq, min_diff = None, None, float('inf')
        for i, note in enumerate(tuning_note_names):
            if i < len(tuning_freqs):
                diff = abs(freq - tuning_freqs[i])
                if diff < min_diff:
                    min_diff = diff
                    closest_note = note
                    closest_freq = tuning_freqs[i]
        if min_diff < max(3, freq * 0.05) and closest_note is not None:
            return closest_note, closest_freq, min_diff
    closest_note, closest_freq, min_diff = None, None, float('inf')
    for note, note_freq in NOTES.items():
        diff = abs(freq - note_freq)
        if diff < min_diff:
            min_diff = diff
            closest_note = note
            closest_freq = note_freq
    if min_diff < max(30, freq * 0.03) and closest_note is not None:
        return closest_note, closest_freq, min_diff
    return None, None, None


def cents_deviation(freq, target_freq):
    if target_freq == 0 or freq == 0:
        return 0
    return max(-50, min(50, 1200 * math.log2(freq / target_freq)))


# ============ ГОРИЗОНТАЛЬНЫЙ ТЮНЕР (ШКАЛА) ============

class ModernHorizontalTuner(Widget):
    deviation = NumericProperty(0.0)
    animated_deviation = NumericProperty(0.0)
    indicator_color = ListProperty([0.2, 0.95, 0.65, 1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tick_textures = {}
        self._build_tick_textures()
        self.bind(pos=self.update_gauge, size=self.update_gauge)
        self.bind(animated_deviation=self.update_gauge)

    def _build_tick_textures(self):
        ticks = [(-50, "-50"), (-25, "-25"), (0, "0"), (25, "+25"), (50, "+50")]
        for val, text in ticks:
            is_zero = (val == 0)
            r, g, b = self._get_segment_color(val, 50)
            rgba = (0.2, 0.95, 0.65, 1.0) if is_zero else (r * 0.85 + 0.15, g * 0.85 + 0.15, b * 0.85 + 0.15, 0.9)
            lbl = CoreLabel(text=text, font_size=sp(12 if is_zero else 11), bold=True, color=rgba)
            lbl.refresh()
            self._tick_textures[val] = lbl.texture

    def on_deviation(self, instance, value):
        clamped = max(-50.0, min(50.0, float(value)))
        Animation.cancel_all(self, 'animated_deviation')
        anim = Animation(animated_deviation=clamped, duration=0.18, transition='out_cubic')
        anim.start(self)

    def set_value(self, value):
        self.deviation = max(-50.0, min(50.0, float(value)))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            scale_w = self.width * 0.94
            scale_x = self.x + (self.width - scale_w) / 2
            rel = (touch.x - scale_x) / scale_w
            target_dev = (max(0.0, min(1.0, rel)) * 100.0) - 50.0
            if abs(target_dev) < 4:
                target_dev = 0.0
            self.set_value(target_dev)
            return True
        return super().on_touch_down(touch)

    @staticmethod
    def _get_segment_color(value, max_value=50):
        normalized = max(-1.0, min(1.0, value / max_value))
        pct = (normalized + 1.0) / 2.0
        if pct < 0.25:
            t = pct / 0.25
            return 1.0, t, 0.0
        elif pct < 0.5:
            t = (pct - 0.25) / 0.25
            return 1.0 - t, 1.0, 0.0
        elif pct < 0.75:
            t = (pct - 0.5) / 0.25
            return t, 1.0, 0.0
        else:
            t = (pct - 0.75) / 0.25
            return 1.0, 1.0 - t, 0.0

    def update_gauge(self, *args):
        self.canvas.clear()
        if self.width <= 0 or self.height <= 0:
            return
        scale_w = self.width * 0.94
        scale_x = self.x + (self.width - scale_w) / 2
        scale_y = self.center_y - dp(2)
        num_segments = 21
        segment_width = scale_w / num_segments
        gap = dp(2.4)
        max_h = dp(38)
        min_h = dp(14)

        dev = max(-50.0, min(50.0, self.animated_deviation))
        is_tuned = abs(dev) <= 3.0
        if is_tuned:
            active_rgb = (0.2, 0.95, 0.65)
        else:
            sr, sg, sb = self._get_segment_color(dev, 50)
            active_rgb = (min(1.0, sr * 0.9 + 0.1), min(1.0, sg * 0.9 + 0.1), min(1.0, sb * 0.9 + 0.1))
        self.indicator_color = [active_rgb[0], active_rgb[1], active_rgb[2], 1.0]

        with self.canvas:
            ticks_indices = [(0, -50), (5, -25), (10, 0), (15, 25), (20, 50)]
            label_y = scale_y + max_h / 2 + dp(6)
            Color(1, 1, 1, 1)
            for seg_idx, val in ticks_indices:
                tex = self._tick_textures.get(val)
                if tex:
                    cx = scale_x + (seg_idx + 0.5) * segment_width
                    Rectangle(texture=tex, pos=(cx - tex.width / 2, label_y), size=tex.size)

            theme_id = settings_manager.theme
            if theme_id == 'light':
                outline_color = (0, 0, 0, 0.4)
            elif theme_id == 'dark':
                outline_color = (1.0, 0.5, 0.0, 0.6)
            else:
                outline_color = (0.0, 0.2, 0.1, 0.8)

            for i in range(num_segments):
                value = -50 + i * 5
                x = scale_x + i * segment_width + gap / 2
                norm_dist = abs(value) / 50.0
                height_factor = (math.cos(norm_dist * math.pi) + 1.0) / 2.0
                curr_height = max(min_h, min_h + (max_h - min_h) * height_factor)
                r, g, b = self._get_segment_color(value, 50)
                dist = abs(dev - value)
                seg_w = max(dp(1), segment_width - gap)

                with self.canvas:
                    Color(*outline_color)
                    if seg_w > 0:
                        Line(rounded_rectangle=(x, scale_y - curr_height / 2, seg_w, curr_height, dp(4)), width=1.5)

                if dist < 4.5:
                    glow_alpha = 0.35 * (1.0 - dist / 4.5)
                    Color(r, g, b, glow_alpha)
                    RoundedRectangle(pos=(x - dp(2), scale_y - curr_height / 2 - dp(3)),
                                     size=(seg_w + dp(4), curr_height + dp(6)), radius=[dp(6)])
                    brightness = 1.0
                    alpha = 1.0
                else:
                    brightness = 0.62 + 0.25 * (1.0 - norm_dist)
                    alpha = 0.78

                Color(r * brightness, g * brightness, b * brightness, alpha)
                if seg_w > 0:
                    RoundedRectangle(pos=(x, scale_y - curr_height / 2), size=(seg_w, curr_height), radius=[dp(4)])

            ix = scale_x + ((dev + 50.0) / 100.0) * scale_w
            bar_bottom = scale_y - max_h / 2
            tip_y = bar_bottom - dp(8)
            base_y = tip_y - dp(15)
            half_w = dp(9)

            Color(active_rgb[0], active_rgb[1], active_rgb[2], 0.28)
            Triangle(
                points=[ix, tip_y + dp(3), ix - half_w - dp(4), base_y - dp(2), ix + half_w + dp(4), base_y - dp(2)])

            Color(*outline_color)
            Line(points=[ix, tip_y, ix - half_w, base_y, ix, base_y + dp(4)], width=1.5)
            Line(points=[ix, tip_y, ix + half_w, base_y, ix, base_y + dp(4)], width=1.5)

            Color(active_rgb[0], active_rgb[1], active_rgb[2], 1.0)
            Triangle(points=[ix, tip_y, ix - half_w, base_y, ix, base_y + dp(4)])

            Color(active_rgb[0] * 0.78, active_rgb[1] * 0.78, active_rgb[2] * 0.78, 1.0)
            Triangle(points=[ix, tip_y, ix + half_w, base_y, ix, base_y + dp(4)])


# ============ «РВАНЫЙ» РАЗДЕЛИТЕЛЬ ============

class DashedDivider(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(2)
        self._line_color = TunerColors.get_divider_color(settings_manager.theme)
        self.bind(pos=self._update_line, size=self._update_line)
        with self.canvas:
            self._color = Color(*self._line_color)
            self._line = Line(points=[], width=dp(1.2))
        self._update_line()

    def _update_line(self, *args):
        if self.height <= 0:
            return
        pad = dp(8)
        cx = self.center_x
        self._line.points = [cx, self.y + pad, cx, self.top - pad]

    def update_theme_colors(self):
        self._line_color = TunerColors.get_divider_color(settings_manager.theme)
        self._color.rgba = self._line_color
        self._update_line()


# ============ КНОПКА НОТЫ ============

class NoteButton(MDCard):
    note_name = StringProperty('')
    display_name = StringProperty('')
    frequency = NumericProperty(0)
    is_active = BooleanProperty(False)
    is_playing = BooleanProperty(False)

    def __init__(self, note_name, display_name, frequency, tuning_id='standard', on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.note_name = note_name
        self.display_name = display_name
        self.frequency = frequency
        self.tuning_id = tuning_id
        self.on_press_callback = on_press
        self._sound = None
        self._sound_data = None

        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (dp(44), dp(44))
        self.radius = [dp(22)] * 4
        self.elevation = 0
        self.ripple_behavior = True

        self.label = MDLabel(
            text=display_name, font_size=sp(15), halign="center", valign="middle",
            theme_text_color="Custom", bold=True, size_hint=(1, 1)
        )
        self.add_widget(self.label)

        self.bind(on_release=self._on_press)
        self.update_theme_colors()
        Clock.schedule_once(self._load_sound_from_assets, 0.1)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        text = TunerColors.get_text_primary(theme_id)
        self.md_bg_color = TunerColors.get_note_bg(theme_id)
        self.line_color = TunerColors.get_note_line(theme_id)
        self.line_width = TunerColors.get_note_line_width(theme_id)
        self.label.text_color = text

    def _load_sound_from_assets(self, dt):
        try:
            import importlib
            tuning_map = {
                'standard_6': 'standard', 'drop_d': 'drop_d', 'open_g': 'open_g',
                'open_d': 'open_d', 'dadgad': 'dadgad', 'half_step_down': 'half_step_down',
                'bass_4': 'bass_4', 'bass_5': 'bass_5', 'ukulele': 'ukulele',
            }
            module_name = tuning_map.get(self.tuning_id, self.tuning_id)
            module = importlib.import_module(f"data.sounds.{module_name}")
            class_name = module_name.title().replace('_', '') + 'Sounds'
            sound_class = getattr(module, class_name)
            self._sound = sound_class.get_sound(self.note_name)
            self._sound_data = sound_class.get_sound_data(self.note_name)
            if not self._sound:
                logger.warning(f"Звук {self.note_name} ({self.tuning_id}) не загружен из ассетов, запуск fallback")
                self._generate_fallback_sound()
        except Exception as e:
            logger.error(f"Ошибка загрузки звука {self.note_name} ({self.tuning_id}): {e}")
            self._generate_fallback_sound()

    def _generate_fallback_sound(self):
        def generate():
            try:
                audio_data = generate_reference_note(self.frequency, 2.0, 0.5)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=get_temp_path()) as f:
                    tmp_path = f.name
                    with open(tmp_path, 'wb') as fout:
                        fout.write(b'RIFF')
                        fout.write(struct.pack('<I', 36 + len(audio_data) * 2))
                        fout.write(b'WAVEfmt ')
                        fout.write(struct.pack('<IHHIIHH', 16, 1, 1, 44100, 44100 * 2, 2, 16))
                        fout.write(b'data')
                        fout.write(struct.pack('<I', len(audio_data) * 2))
                        audio_data.tofile(fout)
                Clock.schedule_once(lambda dt: self._load_fallback_sound(tmp_path), 0)
            except Exception as e:
                logger.error(f"Ошибка генерации: {e}")

        threading.Thread(target=generate, daemon=True).start()

    def _load_fallback_sound(self, path):
        try:
            self._sound = SoundLoader.load(path)
            Clock.schedule_once(lambda dt: clean_temp_file(path), 1.0)
        except Exception:
            pass

    def _on_press(self, instance):
        if self.is_playing:
            return
        if self.on_press_callback:
            self.on_press_callback(self.note_name, self.frequency)
        anim = Animation(size=(dp(48), dp(48)), duration=0.05)
        anim += Animation(size=(dp(44), dp(44)), duration=0.05)
        anim.start(self)
        self._play_sound()

    def _play_sound(self):
        try:
            if self._sound:
                if self._sound.state == 'play':
                    self._sound.stop()
                self.is_playing = True
                self._sound.play()
                duration = self._sound.length if self._sound.length else 2.0
                Clock.schedule_once(lambda dt: setattr(self, 'is_playing', False), duration + 0.1)
            else:
                Clock.schedule_once(self._load_sound_from_assets, 0.1)
                self._generate_fallback_sound()
        except Exception as e:
            logger.error(f"Ошибка воспроизведения: {e}")
            self.is_playing = False

    def set_active(self, active):
        self.is_active = active
        if active:
            accent = TunerColors.get_accent(settings_manager.theme)
            self.md_bg_color = accent[:3] + [0.8]
            self.line_color = accent
            self.elevation = 2
            self.label.text_color = [1, 1, 1, 1]
        else:
            self.elevation = 0
            self.update_theme_colors()


# ============ КНОПКИ МЕНЮ ============

class IconMenuItem(ButtonBehavior, MDBoxLayout):
    def __init__(self, icon_name, on_press=None, is_active=True, icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press
        self.is_active = is_active
        self.icon_color = icon_color if icon_color else [1, 1, 1, 0.7]

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = [0, dp(4), 0, dp(4)]
        self.spacing = dp(0)
        self.md_bg_color = [0, 0, 0, 0]

        self.icon_btn = MDIconButton(
            icon=icon_name, size_hint=(None, None), size=(dp(28), dp(28)),
            pos_hint={'center_x': 0.5}, theme_icon_color="Custom",
            icon_color=self.icon_color, md_bg_color=[0, 0, 0, 0],
            ripple_scale=0, ripple_alpha=0
        )
        self.icon_btn.bind(on_release=self._on_press)
        self.add_widget(self.icon_btn)

    def _on_press(self, instance):
        if self.on_press_callback and self.is_active:
            self.on_press_callback()

    def set_icon(self, icon_name):
        self.icon_name = icon_name
        self.icon_btn.icon = icon_name

    def set_color(self, color):
        self.icon_color = color
        self.icon_btn.icon_color = color


# ============ МЕНЮ УПРАВЛЕНИЯ ============

class UnifiedTunerMenu(MDCard):
    def __init__(self, on_play=None, on_tune=None, on_reset=None, on_instrument=None, current_instrument='guitar',
                 is_listening=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.radius = [dp(16)]
        self.elevation = 0
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = dp(0)

        self.play_item = IconMenuItem(
            "stop" if is_listening else "play",
            on_press=on_play,
            icon_color=[0.8, 0.3, 0.3, 1] if is_listening else [0.13, 0.59, 0.95, 1]
        )
        self.tune_item = IconMenuItem(
            "tune",
            on_press=on_tune,
            icon_color=[0.61, 0.15, 0.69, 1]
        )
        self.instrument_item = IconMenuItem(
            self._get_instrument_icon(current_instrument),
            on_press=on_instrument,
            icon_color=self._get_instrument_color(current_instrument)
        )
        self.reset_item = IconMenuItem(
            "refresh",
            on_press=on_reset,
            icon_color=[0.9, 0.4, 0.2, 1]
        )

        self.add_widget(self.play_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.tune_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.instrument_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.reset_item)
        self.update_theme_colors()

    def _get_instrument_icon(self, instrument):
        if instrument == 'guitar': return "guitar-acoustic"
        elif instrument == 'bass': return "guitar-electric"
        else: return "guitar-acoustic"

    def _get_instrument_color(self, instrument):
        if instrument == 'guitar': return [1.0, 0.7, 0.0, 1]
        elif instrument == 'bass': return [0.0, 0.8, 0.6, 1]
        else: return [0.6, 0.2, 0.8, 1]

    def _create_divider(self):
        return DashedDivider()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = TunerColors.get_card_bg(theme_id)
        self.line_color = TunerColors.get_card_line(theme_id)
        self.line_width = TunerColors.get_card_line_width(theme_id)

        for child in self.children:
            if isinstance(child, DashedDivider):
                child.update_theme_colors()

    def update_state(self, is_listening):
        if is_listening:
            self.play_item.set_icon("stop")
            self.play_item.set_color([0.8, 0.3, 0.3, 1])
        else:
            self.play_item.set_icon("play")
            self.play_item.set_color([0.13, 0.59, 0.95, 1])

    def update_instrument(self, instrument):
        self.instrument_item.set_icon(self._get_instrument_icon(instrument))
        self.instrument_item.set_color(self._get_instrument_color(instrument))


# ============ ОСНОВНОЙ ЭКРАН ============

class TunerScreen(BaseScreen):
    target_note = StringProperty("--")
    target_freq = NumericProperty(0.0)
    indicator_color = ListProperty([0.2, 0.95, 0.65, 1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'
        self.bg_color_inst = None
        self.bg_rect = None
        self.is_listening = False
        self.current_frequency = 0
        self.current_deviation = 0
        self._audio_thread = None
        self._running = False
        self._audio_backend = 'none'
        self._audio_recorder = None
        self._sounddevice_stream = None
        self._pyaudio_stream = None
        self._pyaudio = None
        self._error_message = ""
        self._note_buttons = []

        self.current_tuning = 'standard_6'
        self.current_instrument = 'guitar'
        self.tuning_notes = TUNINGS[self.current_tuning]['notes']
        self.tuning_freqs = TUNINGS[self.current_tuning]['freqs']
        self.tuning_note_names = TUNINGS[self.current_tuning]['note_names']

        # Переменные для ручного режима и сглаживания
        self.selected_string_index = 0
        self.is_manual_mode = False
        self._smoothed_freq = 0.0
        self.target_note = self.tuning_note_names[self.selected_string_index]
        self.target_freq = self.tuning_freqs[self.selected_string_index]

        self.load_background()
        self.init_ui()
        self._set_debug_callback()
        Clock.schedule_once(self._init_audio, 0.5)
        logger.info('Экран тюнера создан')

    def load_background(self):
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.texture = None
        try:
            if HAS_ASSETS:
                bg_data = load_asset_as_bytes("background_jpg")
                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")
                    self.texture = img.texture
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')
        self.update_screen_background()

    def _update_rect(self, *args):
        if hasattr(self, 'bg_rect') and self.bg_rect:
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def update_screen_background(self):
        if not hasattr(self, 'bg_color_inst') or not hasattr(self, 'bg_rect'):
            return
        theme_id = settings_manager.theme
        if theme_id == 'green':
            if self.texture:
                self.bg_rect.texture = self.texture
                self.bg_color_inst.rgba = (1, 1, 1, 1)
            else:
                self.bg_rect.texture = None
                self.bg_color_inst.rgba = (0.1, 0.3, 0.2, 1)
        elif theme_id == 'dark':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.07, 0.07, 0.07, 1)
        elif theme_id == 'light':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.969, 0.976, 0.969, 1)

    def update_theme_colors(self):
        self.update_screen_background()
        theme_id = settings_manager.theme
        text_p = TunerColors.get_text_primary(theme_id)
        text_s = TunerColors.get_text_secondary(theme_id)

        if hasattr(self, 'main_tuner_card'):
            self.main_tuner_card.md_bg_color = TunerColors.get_card_bg(theme_id)
            self.main_tuner_card.line_color = TunerColors.get_card_line(theme_id)
            self.main_tuner_card.line_width = TunerColors.get_card_line_width(theme_id)

        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text_color = text_s

        if hasattr(self, 'note_label'):
            is_tuned = abs(self.current_deviation) <= 3.0 and self.is_listening
            self.note_label.text_color = [0.2, 0.95, 0.65, 1.0] if is_tuned else text_p
            self.note_label.font_size = sp(100)

        if hasattr(self, 'freq_label'):
            self.freq_label.text_color = TunerColors.get_accent(theme_id)

        if hasattr(self, 'label_low'):
            self.label_low.text_color = text_s
            self.label_high.text_color = text_s

        if hasattr(self, 'cents_label'):
            self.update_cents_ui()

        if hasattr(self, 'menu_stack'):
            self.menu_stack.update_theme_colors()

        if hasattr(self, '_hint_label'):
            self._hint_label.text_color = TunerColors.get_hint_color(theme_id)

        for btn in self._note_buttons:
            btn.update_theme_colors()

        self.update_text_outlines()

    def update_text_outlines(self):
        theme_id = settings_manager.theme
        if hasattr(self, 'note_label'):
            if theme_id == 'green':
                self.note_label.outline_color = (0.05, 0.15, 0.1, 1)
                self.note_label.outline_width = 1.5
            else:
                self.note_label.outline_color = (0, 0, 0, 0.5)
                self.note_label.outline_width = 1

    def update_language(self):
        if hasattr(self, 'menu_stack'):
            self.menu_stack.update_instrument(self.current_instrument)
        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = get_text(TUNINGS[self.current_tuning]['name_key'])
        if hasattr(self, 'label_low'):
            self.label_low.text = get_text("low", "LOW").upper()
            self.label_high.text = get_text("high", "HIGH").upper()
        self.update_cents_ui()
        self._update_hint()

    def _set_debug_callback(self):
        try:
            if HAS_AUDIO_RECORDER:
                set_debug_callback(self._debug_log)
        except Exception:
            pass

    def _debug_log(self, message, level="INFO"):
        Clock.schedule_once(lambda dt: self._update_hint_ui(message, level), 0)

    def _update_hint_ui(self, message, level="INFO"):
        if hasattr(self, '_hint_label') and not self._error_message:
            self._hint_label.text = message
            self._hint_label.opacity = 1
            self._hint_label.text_color = TunerColors.get_hint_color(settings_manager.theme)

    def _show_error(self, message):
        def _update():
            self._error_message = message
            if hasattr(self, '_hint_label'):
                self._hint_label.text = message
                self._hint_label.opacity = 1
                self._hint_label.text_color = [0.8, 0.2, 0.2, 1]
        Clock.schedule_once(lambda dt: _update(), 0)

    def _show_success(self, message):
        def _update():
            if hasattr(self, '_hint_label'):
                self._hint_label.text = message
                self._hint_label.opacity = 1
                self._hint_label.text_color = TunerColors.get_hint_color(settings_manager.theme)
                if hasattr(self, '_hint_timer') and self._hint_timer:
                    Clock.unschedule(self._hint_timer)
                self._hint_timer = Clock.schedule_once(lambda dt: self._hide_hint(), 3.0)
        Clock.schedule_once(lambda dt: _update(), 0)

    def _hide_hint(self):
        def _update():
            if hasattr(self, '_hint_label') and not self._error_message:
                self._hint_label.text = ""
                self._hint_label.opacity = 0
        Clock.schedule_once(lambda dt: _update(), 0)

    def _clear_error(self):
        def _update():
            self._error_message = ""
            if hasattr(self, '_hint_label'):
                self._hint_label.text = ""
                self._hint_label.opacity = 0
        Clock.schedule_once(lambda dt: _update(), 0)

    def update_cents_ui(self):
        if not hasattr(self, 'cents_label'):
            return

        dev = self.current_deviation
        if not self.is_listening or abs(dev) <= 3.0:
            self.cents_label.text = f"0 {get_text('cents')}"
            self.cents_label.font_size = sp(14)
            self.cents_label.bold = True
            self.cents_label.text_color = (
                [0.2, 0.95, 0.65, 1]
                if self.is_listening
                else TunerColors.get_text_secondary(settings_manager.theme)
            )
        else:
            sign = "+" if dev > 0 else ""
            self.cents_label.text = f"{sign}{dev:.0f} {get_text('cents')}"
            self.cents_label.font_size = sp(14)
            self.cents_label.bold = True
            self.cents_label.text_color = TunerColors.get_accent(settings_manager.theme)

    # ============ АУДИО ============
    def _init_audio(self, dt):
        if IS_ANDROID:
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.RECORD_AUDIO])
            except Exception:
                pass
            if HAS_AUDIO_RECORDER:
                try:
                    self._audio_recorder = get_audio_recorder()
                    self._audio_backend = 'android_jni'
                    return
                except Exception:
                    pass
            self._audio_backend = 'none'
        else:
            self._init_audio_windows()

    def _init_audio_windows(self):
        all_devices = []
        if HAS_SOUNDDEVICE:
            try:
                for i, d in enumerate(sd.query_devices()):
                    if d['max_input_channels'] > 0:
                        all_devices.append({'library': 'sounddevice', 'index': i, 'name': d['name'],
                                            'channels': d['max_input_channels'],
                                            'rate': int(d.get('default_samplerate', 0))})
            except Exception:
                pass
        if HAS_PYAUDIO:
            try:
                p = pyaudio.PyAudio()
                for i in range(p.get_device_count()):
                    info = p.get_device_info_by_index(i)
                    if info.get('maxInputChannels', 0) > 0:
                        all_devices.append({'library': 'pyaudio', 'index': i,
                                            'name': info.get('name', 'Unknown'),
                                            'channels': info.get('maxInputChannels', 0),
                                            'rate': int(info.get('defaultSampleRate', 0))})
                p.terminate()
            except Exception:
                pass
        if not all_devices:
            self._audio_backend = 'none'
            return
        all_devices.sort(key=lambda d: 0 if 'realtek' in d['name'].lower() and 'mic' in d['name'].lower() else 1)
        for dev in all_devices:
            for fmt_name in (['float32'] if dev['library'] == 'sounddevice' else ['paInt16', 'paInt32']):
                for rate in [48000, 44100, 22050, 16000, 11025, 8000]:
                    try:
                        if dev['library'] == 'sounddevice':
                            s = sd.InputStream(device=dev['index'], samplerate=rate, channels=1,
                                               blocksize=CHUNK_SIZE, dtype='float32', latency='high')
                        else:
                            p = pyaudio.PyAudio()
                            fmt = pyaudio.paInt16 if fmt_name == 'paInt16' else pyaudio.paInt32
                            s = p.open(format=fmt, channels=1, rate=rate, input=True,
                                       input_device_index=dev['index'],
                                       frames_per_buffer=CHUNK_SIZE, start=False)
                        s.start()
                        s.stop()
                        s.close()
                        self._working_params = {'library': dev['library'], 'device_index': dev['index'],
                                                'device_name': dev['name'], 'rate': rate,
                                                'channels': 1, 'fmt_name': fmt_name}
                        self._audio_backend = dev['library']
                        return
                    except Exception:
                        continue
        self._audio_backend = 'none'

    def _get_min_freq(self):
        return 27.0 if self.current_instrument == 'bass' else 60.0

    def _start_audio_thread(self):
        if self._running or self._audio_backend == 'none':
            return
        self._running = True
        if self._audio_backend == 'android_jni' and self._audio_recorder:
            try:
                self._audio_recorder.start_recording(callback=self._on_audio_data,
                                                     sample_rate=SAMPLE_RATE, chunk_size=CHUNK_SIZE)
            except Exception:
                self._running = False
        elif self._audio_backend == 'sounddevice':
            self._audio_thread = threading.Thread(target=self._audio_loop_sounddevice, daemon=True)
            self._audio_thread.start()
        elif self._audio_backend == 'pyaudio':
            self._audio_thread = threading.Thread(target=self._audio_loop_pyaudio, daemon=True)
            self._audio_thread.start()

    def _on_audio_data(self, data):
        if not self.is_listening or not self._running:
            return
        if data:
            freq = detect_pitch(data, SAMPLE_RATE, min_freq=self._get_min_freq())
            if freq > 0:
                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))

    def _audio_loop_sounddevice(self):
        try:
            rate = self._working_params['rate']

            def callback(indata, frames, time_info, status):
                if not self._running or not self.is_listening:
                    return
                try:
                    audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
                    freq = detect_pitch(audio_int16.tobytes(), rate, min_freq=self._get_min_freq())
                    if freq > 0:
                        Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))
                except Exception:
                    pass

            self._sounddevice_stream = sd.InputStream(
                device=self._working_params['device_index'], samplerate=rate, channels=1,
                callback=callback, blocksize=CHUNK_SIZE, dtype='float32', latency='high')
            self._sounddevice_stream.start()
            while self._running:
                time.sleep(0.1)
            self._sounddevice_stream.stop()
            self._sounddevice_stream.close()
            self._sounddevice_stream = None
        except Exception as e:
            logger.error(f"sounddevice: {e}")
            self._running = False

    def _audio_loop_pyaudio(self):
        try:
            p = pyaudio.PyAudio()
            fmt = pyaudio.paInt16 if self._working_params['fmt_name'] == 'paInt16' else pyaudio.paInt32
            stream = p.open(format=fmt, channels=1, rate=self._working_params['rate'],
                            input=True, input_device_index=self._working_params['device_index'],
                            frames_per_buffer=CHUNK_SIZE, start=True)
            self._pyaudio = p
            self._pyaudio_stream = stream
            while self._running:
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    if data:
                        freq = detect_pitch(data, self._working_params['rate'], min_freq=self._get_min_freq())
                        if freq > 0:
                            Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))
                except Exception:
                    break
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            logger.error(f"pyaudio: {e}")
            self._running = False

    def _stop_audio_thread(self):
        self._running = False
        if self._audio_backend == 'android_jni' and self._audio_recorder:
            try:
                self._audio_recorder.stop_recording()
            except Exception:
                pass
        if self._sounddevice_stream:
            try:
                self._sounddevice_stream.stop()
                self._sounddevice_stream.close()
            except Exception:
                pass
            self._sounddevice_stream = None
        if self._pyaudio_stream:
            try:
                self._pyaudio_stream.stop_stream()
                self._pyaudio_stream.close()
            except Exception:
                pass
            self._pyaudio_stream = None
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None
        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=1)
        self._audio_thread = None
        self._clear_error()

    def _process_frequency(self, freq):
        if not self.is_listening:
            return

        # Экспоненциальное сглаживание частоты (убирает скачки стрелки)
        if self._smoothed_freq <= 0 or abs(freq - self._smoothed_freq) > self._smoothed_freq * 0.15:
            self._smoothed_freq = freq
        else:
            self._smoothed_freq = 0.65 * self._smoothed_freq + 0.35 * freq

        smooth_f = self._smoothed_freq
        self.current_frequency = smooth_f

        if self.is_manual_mode and self.target_freq > 0:
            # Ручной режим: сравниваем строго с зафиксированной нотой
            note = self.target_note
            note_freq = self.target_freq
            raw_cents = 1200.0 * math.log2(smooth_f / note_freq)
            cents = max(-50.0, min(50.0, raw_cents))
        else:
            # Автоматический режим: сам определяет ближайшую струну текущего строя
            note, note_freq, _ = freq_to_note(smooth_f, self.tuning_note_names, self.tuning_freqs)
            if not note:
                return
            cents = cents_deviation(smooth_f, note_freq)
            self.target_note = note
            self.target_freq = note_freq

        self.current_deviation = cents

        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(cents)

        if hasattr(self, 'note_label'):
            self.note_label.text = note
            is_tuned = abs(cents) <= 3.0
            self.note_label.text_color = (
                [0.2, 0.95, 0.65, 1.0]
                if is_tuned
                else TunerColors.get_text_primary(settings_manager.theme)
            )

        if hasattr(self, 'freq_label'):
            self.freq_label.text = f"{smooth_f:.2f} Hz"

        self.update_cents_ui()

    def on_reference_note_pressed(self, note_name, frequency):
        already_active = any(
            btn.note_name == note_name and btn.is_active
            for btn in self._note_buttons
        )

        for btn in self._note_buttons:
            btn.set_active(False)

        if already_active:
            # Повторное нажатие на активную кнопку — возврат в автоматический режим
            self.is_manual_mode = False
            self._smoothed_freq = 0.0
            self.current_deviation = 0
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(0)
            if hasattr(self, 'freq_label'):
                self.freq_label.text = "-- Hz"
            if hasattr(self, 'note_label'):
                self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)
            self.update_cents_ui()
            self._show_success("Автоматический режим")
            return

        # Фиксируем выбранную ноту
        for btn in self._note_buttons:
            if btn.note_name == note_name:
                btn.set_active(True)
                break

        display_name = ''.join(c for c in note_name if not c.isdigit())
        self.is_manual_mode = True
        self._smoothed_freq = 0.0
        self.target_note = display_name
        self.target_freq = frequency
        self.current_deviation = 0

        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(0)
        if hasattr(self, 'freq_label'):
            self.freq_label.text = f"{frequency:.2f} Hz"
        if hasattr(self, 'note_label'):
            self.note_label.text = display_name
            self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)

        self.update_cents_ui()

        # Автоматически запускаем прослушивание, если тюнер был остановлен
        if not self.is_listening and self._audio_backend != 'none':
            self.toggle_tuner()

    def _reset_note_display(self):
        if hasattr(self, 'note_label'):
            if self.is_listening and self.current_frequency > 0:
                note, _, _ = freq_to_note(self.current_frequency, self.tuning_note_names, self.tuning_freqs)
                self.note_label.text = note or "--"
            else:
                self.note_label.text = self.target_note
            self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)
            self.update_cents_ui()

    def _reset_note_buttons(self):
        for btn in self._note_buttons:
            btn.set_active(False)

    def _rebuild_note_buttons(self):
        self.notes_row.clear_widgets()
        self._note_buttons = []
        self.notes_row.add_widget(Widget(size_hint_x=1))
        for display_name, full_name, freq in zip(self.tuning_note_names, self.tuning_notes, self.tuning_freqs):
            btn = NoteButton(note_name=full_name, display_name=display_name,
                             frequency=freq, tuning_id=self.current_tuning,
                             on_press=self.on_reference_note_pressed)
            self._note_buttons.append(btn)
            self.notes_row.add_widget(btn)
        self.notes_row.add_widget(Widget(size_hint_x=1))

    def _cycle_tuning(self):
        categories = {
            'guitar': ['standard_6', 'drop_d', 'open_g', 'open_d', 'dadgad', 'half_step_down'],
            'bass': ['bass_4', 'bass_5'],
            'ukulele': ['ukulele']
        }
        available = categories.get(self.current_instrument, [])
        if not available:
            return

        try:
            current_idx = available.index(self.current_tuning)
            next_idx = (current_idx + 1) % len(available)
        except ValueError:
            next_idx = 0

        self.current_tuning = available[next_idx]
        t = TUNINGS[self.current_tuning]
        self.tuning_notes = t['notes']
        self.tuning_freqs = t['freqs']
        self.tuning_note_names = t['note_names']

        self.is_manual_mode = False
        self._smoothed_freq = 0.0
        self.selected_string_index = 0
        self.target_note = self.tuning_note_names[0]
        self.target_freq = self.tuning_freqs[0]
        self.current_deviation = 0

        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(0)
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "-- Hz"
        if hasattr(self, 'note_label'):
            self.note_label.text = self.target_note
            self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)

        self._rebuild_note_buttons()
        self._reset_note_buttons()
        self.update_cents_ui()

        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = get_text(t['name_key'])

        self._show_success(f"Строй: {get_text(t['name_key'])}")

    def _on_instrument_selected(self):
        if self.current_instrument == 'guitar':
            self.current_instrument = 'bass'
        elif self.current_instrument == 'bass':
            self.current_instrument = 'ukulele'
        else:
            self.current_instrument = 'guitar'

        self.menu_stack.update_instrument(self.current_instrument)

        categories = {
            'guitar': ['standard_6', 'drop_d', 'open_g', 'open_d', 'dadgad', 'half_step_down'],
            'bass': ['bass_4', 'bass_5'],
            'ukulele': ['ukulele']
        }
        available = categories.get(self.current_instrument, [])

        if self.current_tuning not in available:
            self.current_tuning = available[0]
            t = TUNINGS[self.current_tuning]
            self.tuning_notes = t['notes']
            self.tuning_freqs = t['freqs']
            self.tuning_note_names = t['note_names']
            self.is_manual_mode = False
            self._smoothed_freq = 0.0
            self.target_note = self.tuning_note_names[0]
            self.target_freq = self.tuning_freqs[0]
            self.current_deviation = 0
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(0)
            if hasattr(self, 'freq_label'):
                self.freq_label.text = "-- Hz"
            if hasattr(self, 'note_label'):
                self.note_label.text = self.target_note
                self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)
            self._rebuild_note_buttons()
            self._reset_note_buttons()
            self.update_cents_ui()
            if hasattr(self, 'tuning_name_label'):
                self.tuning_name_label.text = get_text(t['name_key'])

        instr_name = {'guitar': 'Гитара', 'bass': 'Бас', 'ukulele': 'Укулеле'}[self.current_instrument]
        self._show_success(f"Инструмент: {instr_name}")

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        main_layout.add_widget(Widget(size_hint_y=None, height=layout_config.get_top_padding()))

        nav_bottom = layout_config.get_bottom_nav_total_height()
        padding_bottom = nav_bottom

        content_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                                        padding=[dp(16), dp(4), dp(16), padding_bottom])
        content = MDBoxLayout(orientation='vertical', spacing=dp(10),
                              size_hint=(1, None), adaptive_height=True)

        # 1. КАРТОЧКА ТЮНЕРА
        self.main_tuner_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(330),
            radius=[dp(16)],
            md_bg_color=TunerColors.get_card_bg(settings_manager.theme),
            line_color=TunerColors.get_card_line(settings_manager.theme),
            line_width=TunerColors.get_card_line_width(settings_manager.theme),
            elevation=0,
            padding=[dp(16), dp(14), dp(16), dp(14)],
            spacing=dp(0),
        )

        self.tuning_name_label = MDLabel(
            text=get_text(TUNINGS[self.current_tuning]['name_key']),
            font_size=sp(13), halign="center", valign="top",
            size_hint_y=None, height=dp(20),
            theme_text_color="Custom", bold=False,
            text_color=TunerColors.get_text_secondary(settings_manager.theme)
        )
        self.main_tuner_card.add_widget(self.tuning_name_label)
        self.main_tuner_card.add_widget(Widget(size_hint_y=1))

        note_anchor = AnchorLayout(size_hint_y=None, height=dp(80))
        self.note_label = MDLabel(
            text=self.target_note, font_size=sp(90), bold=True,
            halign="center", valign="middle", size_hint=(1, None), height=dp(80),
            text_size=(None, None), theme_text_color="Custom",
            text_color=TunerColors.get_text_primary(settings_manager.theme)
        )
        self.note_label.bind(on_size=lambda *args: setattr(self.note_label, 'font_size', sp(90)))
        note_anchor.add_widget(self.note_label)
        self.main_tuner_card.add_widget(note_anchor)
        self.main_tuner_card.add_widget(Widget(size_hint_y=1))

        self.freq_label = MDLabel(
            text="-- Hz", font_size=sp(14), bold=True, halign="center",
            size_hint_y=None, height=dp(20), theme_text_color="Custom",
            text_color=TunerColors.get_accent(settings_manager.theme)
        )
        self.main_tuner_card.add_widget(self.freq_label)
        self.main_tuner_card.add_widget(Widget(size_hint_y=1))

        gauge_container = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(90))
        self.tuner_gauge = ModernHorizontalTuner(size_hint_y=None, height=dp(90))
        self.tuner_gauge.bind(indicator_color=self._update_indicator_color)
        gauge_container.add_widget(self.tuner_gauge)
        self.main_tuner_card.add_widget(gauge_container)

        labels_box = MDBoxLayout(size_hint_y=None, height=dp(22), padding=[dp(12), 0])
        self.label_low = MDLabel(
            text=get_text("low", "LOW").upper(), font_size=sp(7.5), bold=False,
            halign="left", theme_text_color="Custom",
            text_color=TunerColors.get_text_secondary(settings_manager.theme)
        )
        self.cents_label = MDLabel(
            text=f"0 {get_text('cents')}", font_size=sp(14), bold=True,
            halign="center", theme_text_color="Custom",
            text_color=TunerColors.get_text_secondary(settings_manager.theme)
        )
        self.label_high = MDLabel(
            text=get_text("high", "HIGH").upper(), font_size=sp(7.5), bold=False,
            halign="right", theme_text_color="Custom",
            text_color=TunerColors.get_text_secondary(settings_manager.theme)
        )
        labels_box.add_widget(self.label_low)
        labels_box.add_widget(self.cents_label)
        labels_box.add_widget(self.label_high)
        self.main_tuner_card.add_widget(labels_box)
        content.add_widget(self.main_tuner_card)

        # 2. МЕНЮ
        self.menu_container = MDBoxLayout(orientation='vertical', size_hint=(1, None), height=dp(60))
        self.menu_stack = UnifiedTunerMenu(
            on_play=self.toggle_tuner,
            on_tune=self._cycle_tuning,
            on_instrument=self._on_instrument_selected,
            on_reset=self.reset_tuner,
            current_instrument=self.current_instrument,
            is_listening=self.is_listening
        )
        self.menu_container.add_widget(self.menu_stack)
        content.add_widget(self.menu_container)

        # 3. КНОПКИ НОТ
        self.notes_row = MDBoxLayout(orientation='horizontal', size_hint=(1, None),
                                     height=dp(52), spacing=dp(12),
                                     padding=[dp(16), dp(8), dp(16), dp(8)])
        self._rebuild_note_buttons()
        content.add_widget(self.notes_row)

        # 4. Подсказка
        self._hint_label = MDLabel(
            text="", font_size=sp(12), halign="center",
            size_hint_y=None, height=dp(24), theme_text_color="Custom", opacity=0
        )
        content.add_widget(self._hint_label)

        content_container.add_widget(content)
        content_container.add_widget(Widget(size_hint_y=1))
        main_layout.add_widget(content_container)
        self.add_widget(main_layout)

        self.update_theme_colors()
        logger.info("UI тюнера построен")

    def _update_indicator_color(self, instance, value):
        self.indicator_color = value

    def toggle_tuner(self, *args):
        if not self.is_listening:
            if self._audio_backend == 'none':
                self._show_error(get_text('audio_not_init'))
                return
            self._smoothed_freq = 0.0
            self.is_listening = True
            self.menu_stack.update_state(True)
            self._start_audio_thread()
            self.update_cents_ui()
        else:
            self.is_listening = False
            self._smoothed_freq = 0.0
            self.menu_stack.update_state(False)
            self._stop_audio_thread()
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(0)
            if hasattr(self, 'freq_label'):
                self.freq_label.text = "-- Hz"
            if hasattr(self, 'note_label'):
                self.note_label.text = self.target_note
                self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)
            self.current_deviation = 0
            self.update_cents_ui()
            if not self.is_manual_mode:
                self._reset_note_buttons()

    def reset_tuner(self, *args):
        if self.is_listening:
            self.toggle_tuner()
        self.is_manual_mode = False
        self._smoothed_freq = 0.0
        self.selected_string_index = 0
        self.target_note = self.tuning_note_names[0]
        self.target_freq = self.tuning_freqs[0]
        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(0)
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "-- Hz"
        if hasattr(self, 'note_label'):
            self.note_label.text = self.target_note
            self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)
        self.current_deviation = 0
        self.update_cents_ui()
        self._reset_note_buttons()
        self._clear_error()
        self._show_success("Сброшено")

    def _update_hint(self):
        pass

    def on_enter(self):
        super().on_enter()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_back_callback(self.go_back)
        self.update_theme_colors()

    def go_back(self, instance=None):
        if self.is_listening:
            self.toggle_tuner()
        self._stop_audio_thread()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_back_callback()
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_leave(self):
        if self.is_listening:
            self.toggle_tuner()
        self._stop_audio_thread()
        self._hide_hint()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_back_callback()