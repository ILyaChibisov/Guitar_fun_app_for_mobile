# screens/tuner_screen.py
"""
Экран гитарного тюнера — с красивой стрелкой и повёрнутыми цифрами
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Ellipse, PushMatrix, PopMatrix, Rotate, Mesh
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.utils import platform
from io import BytesIO
import math
import threading
import struct
import time
import sys

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from utils.notifications import notify

logger = screen_logger('Tuner')

# ============ ПРОВЕРКА ПЛАТФОРМЫ ============
IS_WINDOWS = sys.platform == 'win32' or sys.platform == 'win64'
IS_ANDROID = platform == 'android'

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# ============ ПОПЫТКА ИМПОРТА ANDROID AUDIO ============
try:
    from utils.android_audio import get_audio_recorder, set_debug_callback

    HAS_AUDIO_RECORDER = True
    logger.info("✅ Модуль android_audio загружен")
except ImportError:
    HAS_AUDIO_RECORDER = False
    logger.warning("⚠️ Модуль android_audio не найден, JNI AudioRecord недоступен")

# ============ ПОПЫТКА ИМПОРТА PYTHON AUDIO БИБЛИОТЕК ============
HAS_PYAUDIO = False
HAS_SOUNDDEVICE = False

try:
    import pyaudio

    HAS_PYAUDIO = True
    logger.info("✅ pyaudio загружен")
except ImportError:
    logger.warning("⚠️ pyaudio не найден")

try:
    import sounddevice as sd
    import numpy as np

    HAS_SOUNDDEVICE = True
    logger.info("✅ sounddevice загружен")
except ImportError:
    logger.warning("⚠️ sounddevice не найден")

# ============ НАСТРОЙКИ АУДИО ============
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

# ============ СТРОИ ГИТАР ============
TUNINGS = {
    'standard_6': {
        'name': 'Стандартный',
        'strings': 6,
        'notes': ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        'freqs': [82.41, 110.00, 146.83, 196.00, 246.94, 329.63],
        'note_names': ['E', 'A', 'D', 'G', 'B', 'E'],
    },
    'drop_d': {
        'name': 'Drop D',
        'strings': 6,
        'notes': ['D2', 'A2', 'D3', 'G3', 'B3', 'E4'],
        'freqs': [73.42, 110.00, 146.83, 196.00, 246.94, 329.63],
        'note_names': ['D', 'A', 'D', 'G', 'B', 'E'],
    },
    'open_g': {
        'name': 'Open G',
        'strings': 6,
        'notes': ['D2', 'G2', 'D3', 'G3', 'B3', 'D4'],
        'freqs': [73.42, 98.00, 146.83, 196.00, 246.94, 293.66],
        'note_names': ['D', 'G', 'D', 'G', 'B', 'D'],
    },
    'open_d': {
        'name': 'Open D',
        'strings': 6,
        'notes': ['D2', 'A2', 'D3', 'F#3', 'A3', 'D4'],
        'freqs': [73.42, 110.00, 146.83, 185.00, 220.00, 293.66],
        'note_names': ['D', 'A', 'D', 'F#', 'A', 'D'],
    },
    'dadgad': {
        'name': 'DADGAD',
        'strings': 6,
        'notes': ['D2', 'A2', 'D3', 'G3', 'A3', 'D4'],
        'freqs': [73.42, 110.00, 146.83, 196.00, 220.00, 293.66],
        'note_names': ['D', 'A', 'D', 'G', 'A', 'D'],
    },
    'half_step_down': {
        'name': 'На полтона ниже',
        'strings': 6,
        'notes': ['Eb2', 'Ab2', 'Db3', 'Gb3', 'Bb3', 'Eb4'],
        'freqs': [77.78, 103.83, 138.59, 185.00, 233.08, 311.13],
        'note_names': ['Eb', 'Ab', 'Db', 'Gb', 'Bb', 'Eb'],
    },
    'bass_4': {
        'name': 'Бас 4-струнный',
        'strings': 4,
        'notes': ['E1', 'A1', 'D2', 'G2'],
        'freqs': [41.20, 55.00, 73.42, 98.00],
        'note_names': ['E', 'A', 'D', 'G'],
    },
    'bass_5': {
        'name': 'Бас 5-струнный',
        'strings': 5,
        'notes': ['B0', 'E1', 'A1', 'D2', 'G2'],
        'freqs': [30.87, 41.20, 55.00, 73.42, 98.00],
        'note_names': ['B', 'E', 'A', 'D', 'G'],
    },
    'ukulele': {
        'name': 'Укулеле',
        'strings': 4,
        'notes': ['G4', 'C4', 'E4', 'A4'],
        'freqs': [392.00, 261.63, 329.63, 440.00],
        'note_names': ['G', 'C', 'E', 'A'],
    },
}

# Все ноты для определения
NOTES = {
    'B0': 30.87,
    'C1': 32.70, 'C#1': 34.65,
    'D1': 36.71, 'D#1': 38.89,
    'E1': 41.20,
    'F1': 43.65, 'F#1': 46.25,
    'G1': 49.00, 'G#1': 51.91,
    'A1': 55.00, 'A#1': 58.27,
    'B1': 61.74,
    'C2': 65.41, 'C#2': 69.30,
    'D2': 73.42, 'D#2': 77.78,
    'E2': 82.41,
    'F2': 87.31, 'F#2': 92.50,
    'G2': 98.00, 'G#2': 103.83,
    'A2': 110.00, 'A#2': 116.54,
    'B2': 123.47,
    'C3': 130.81, 'C#3': 138.59,
    'D3': 146.83, 'D#3': 155.56,
    'E3': 164.81,
    'F3': 174.61, 'F#3': 185.00,
    'G3': 196.00, 'G#3': 207.65,
    'A3': 220.00, 'A#3': 233.08,
    'B3': 246.94,
    'C4': 261.63, 'C#4': 277.18,
    'D4': 293.66, 'D#4': 311.13,
    'E4': 329.63,
    'F4': 349.23, 'F#4': 369.99,
    'G4': 392.00, 'G#4': 415.30,
    'A4': 440.00, 'A#4': 466.16,
    'B4': 493.88,
    'C5': 523.25, 'C#5': 554.37,
    'D5': 587.33, 'D#5': 622.25,
    'E5': 659.25,
    'F5': 698.46, 'F#5': 739.99,
    'G5': 783.99, 'G#5': 830.61,
    'A5': 880.00, 'A#5': 932.33,
    'B5': 987.77,
    'C6': 1046.50, 'C#6': 1108.73,
    'D6': 1174.66, 'D#6': 1244.51,
    'E6': 1318.51,
    'F6': 1396.91, 'F#6': 1479.98,
    'G6': 1567.98, 'G#6': 1661.22,
    'A6': 1760.00, 'A#6': 1864.66,
    'B6': 1975.53,
}


# ============ ОПРЕДЕЛЕНИЕ ЧАСТОТЫ ============
def detect_pitch(audio_data, sample_rate=SAMPLE_RATE):
    if not audio_data or len(audio_data) < 200:
        return 0
    try:
        if isinstance(audio_data, bytes):
            if len(audio_data) % 2 == 0:
                samples = struct.unpack(f'{len(audio_data) // 2}h', audio_data)
            else:
                return 0
        else:
            samples = audio_data
    except:
        return 0
    mean = sum(samples) / len(samples) if samples else 0
    samples = [s - mean for s in samples]
    max_amp = max(abs(s) for s in samples) if samples else 0
    if max_amp < 50:
        return 0
    max_corr = 0
    max_lag = 0
    corr_values = []
    min_lag = int(sample_rate / 800)
    max_lag = int(sample_rate / 80)
    if max_lag > len(samples) // 2:
        max_lag = len(samples) // 2
    if min_lag >= max_lag:
        return 0
    for lag in range(min_lag, max_lag):
        corr = sum(samples[i] * samples[i + lag] for i in range(len(samples) - lag))
        corr_values.append((lag, corr))
        if corr > max_corr:
            max_corr = corr
            max_lag = lag
    if max_lag == 0:
        return 0
    if max_lag > min_lag and max_lag < max_lag - 1:
        prev_corr = next((c for l, c in corr_values if l == max_lag - 1), 0)
        next_corr = next((c for l, c in corr_values if l == max_lag + 1), 0)
        if prev_corr > 0 and next_corr > 0:
            denom = prev_corr - 2 * max_corr + next_corr
            if denom != 0:
                offset = (prev_corr - next_corr) / (2 * denom)
                max_lag += offset
    if max_lag > 0:
        freq = sample_rate / max_lag
        if 80 < freq < 800:
            return freq
    return 0


def freq_to_note(freq, tuning_note_names=None, tuning_freqs=None):
    if freq <= 0:
        return None, None, None
    if tuning_note_names and tuning_freqs:
        closest_note = None
        closest_freq = None
        min_diff = float('inf')
        for i, note in enumerate(tuning_note_names):
            if i < len(tuning_freqs):
                note_freq = tuning_freqs[i]
                diff = abs(freq - note_freq)
                if diff < min_diff:
                    min_diff = diff
                    closest_note = note
                    closest_freq = note_freq
        max_diff = max(3, freq * 0.05)
        if min_diff < max_diff and closest_note is not None:
            return closest_note, closest_freq, min_diff
    closest_note = None
    closest_freq = None
    min_diff = float('inf')
    for note, note_freq in NOTES.items():
        diff = abs(freq - note_freq)
        if diff < min_diff:
            min_diff = diff
            closest_note = note
            closest_freq = note_freq
    max_diff = max(30, freq * 0.03)
    if min_diff < max_diff and closest_note is not None:
        return closest_note, closest_freq, min_diff
    return None, None, None


def cents_deviation(freq, target_freq):
    if target_freq == 0 or freq == 0:
        return 0
    cents = 1200 * math.log2(freq / target_freq)
    return max(-50, min(50, cents))


# ===================================================================
# ============ ТЮНЕР С КРАСИВОЙ СТРЕЛКОЙ ============
# ===================================================================

class TunerDial(Widget):
    """
    Тюнер с красивой стрелкой и повёрнутыми цифрами
    Дуга по центру: -50 слева, 0 сверху, +50 справа
    """

    deviation = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deviation = 0
        self._labels = []
        self.bind(pos=self.update_gauge, size=self.update_gauge)
        self.bind(deviation=self.update_gauge)
        Clock.schedule_once(self.update_gauge, 0.1)
        Clock.schedule_once(self.update_gauge, 0.3)
        Clock.schedule_once(self.update_gauge, 0.5)

    def update_gauge(self, *args):
        self.canvas.clear()

        for label in self._labels:
            if label.parent:
                self.remove_widget(label)
        self._labels.clear()

        if self.width <= 0 or self.height <= 0:
            return

        center_x = self.center_x
        center_y = self.center_y + dp(10)  # Чуть выше для красоты
        radius = min(self.width, self.height) / 2 - 30

        # ============ ПРАВИЛЬНЫЙ РАСЧЁТ ДУГИ ============
        # Дуга от -50 (слева) до +50 (справа)
        # Углы: -50 -> 150 градусов, +50 -> 30 градусов
        # 0 -> 90 градусов (верх)
        start_angle = 150  # Левая сторона (-50)
        end_angle = 30  # Правая сторона (+50)
        total_span = abs(end_angle - start_angle)  # 120 градусов

        with self.canvas:
            # ============ 1. ОСНОВНАЯ ДУГА (фон) ============
            Color(0.15, 0.15, 0.2, 0.5)
            Line(circle=(center_x, center_y, radius, start_angle, end_angle), width=12)

            # ============ 2. ЦВЕТНЫЕ СЕГМЕНТЫ ============
            num_segments = 10  # 10 сегментов по 10 центов
            gap_deg = 2
            segment_span = (total_span - gap_deg * (num_segments - 1)) / num_segments

            for i in range(num_segments):
                # Угол сегмента
                s_angle = start_angle - i * (segment_span + gap_deg)
                e_angle = s_angle - segment_span

                # Цвет от красного к зелёному
                t = i / (num_segments - 1)
                # Красный (t=0) -> Жёлтый (t=0.5) -> Зелёный (t=1)
                if t < 0.5:
                    r = 0.9
                    g = 0.9 * (t * 2)
                else:
                    r = 0.9 * (1 - (t - 0.5) * 2)
                    g = 0.9
                Color(r, g, 0.1, 0.9)
                Line(circle=(center_x, center_y, radius, e_angle, s_angle), width=12)

            # ============ 3. РИСКИ (ДЕЛЕНИЯ) ============
            for val in range(-50, 51, 10):
                pct = (val + 50) / 100.0
                angle_deg = start_angle + pct * total_span
                angle_rad = math.radians(angle_deg)

                # Длинная риска для основных делений
                inner_r = radius - 18
                outer_r = radius + 2
                x1 = center_x + inner_r * math.cos(angle_rad)
                y1 = center_y + inner_r * math.sin(angle_rad)
                x2 = center_x + outer_r * math.cos(angle_rad)
                y2 = center_y + outer_r * math.sin(angle_rad)

                Color(0.9, 0.9, 0.9, 0.8)
                Line(points=[x1, y1, x2, y2], width=2)

            # ============ 4. МАЛЕНЬКИЕ РИСКИ (каждые 5) ============
            for val in range(-45, 46, 5):
                if val % 10 == 0:
                    continue
                pct = (val + 50) / 100.0
                angle_deg = start_angle + pct * total_span
                angle_rad = math.radians(angle_deg)

                inner_r = radius - 10
                outer_r = radius + 2
                x1 = center_x + inner_r * math.cos(angle_rad)
                y1 = center_y + inner_r * math.sin(angle_rad)
                x2 = center_x + outer_r * math.cos(angle_rad)
                y2 = center_y + outer_r * math.sin(angle_rad)

                Color(0.6, 0.6, 0.6, 0.4)
                Line(points=[x1, y1, x2, y2], width=1)

            # ============ 5. ЦИФРЫ (повёрнутые) ============
            for val in range(-50, 51, 10):
                pct = (val + 50) / 100.0
                angle_deg = start_angle + pct * total_span
                angle_rad = math.radians(angle_deg)

                text_radius = radius - 32
                tx = center_x + text_radius * math.cos(angle_rad)
                ty = center_y + text_radius * math.sin(angle_rad)

                # Поворот лейбла (чтобы цифры читались)
                label_rotation = angle_deg - 90
                if angle_deg > 90:
                    label_rotation = angle_deg + 90

                # Цвет цифры
                if val == 0:
                    color = (0.46, 0.70, 0.71, 1)  # Бирюзовый для 0
                    font_size = '16sp'
                    bold = True
                else:
                    t = (val + 50) / 100.0
                    if t < 0.5:
                        r = 0.9
                        g = 0.9 * (t * 2)
                    else:
                        r = 0.9 * (1 - (t - 0.5) * 2)
                        g = 0.9
                    color = (r, g, 0.1, 0.9)
                    font_size = '13sp'
                    bold = False

                lbl = Label(
                    text=str(val),
                    font_size=font_size,
                    bold=bold,
                    color=color,
                    size_hint=(None, None),
                    size=(35, 20),
                    halign='center',
                    valign='middle'
                )
                lbl.canvas.before.clear()
                lbl.canvas.before.add(PushMatrix())
                lbl.canvas.before.add(Rotate(angle=label_rotation, origin=(tx, ty)))
                lbl.center = (tx, ty)
                lbl.canvas.before.add(PopMatrix())

                self.add_widget(lbl)
                self._labels.append(lbl)

            # ============ 6. СТРЕЛКА ============
            val_pct = (self.deviation - (-50)) / 100
            arrow_deg = start_angle + val_pct * total_span
            arrow_rad = math.radians(arrow_deg)

            tip_x = center_x + (radius - 8) * math.cos(arrow_rad)
            tip_y = center_y + (radius - 8) * math.sin(arrow_rad)

            base_width = 12
            perp_rad = arrow_rad + math.radians(90)
            base_x1 = center_x + base_width * math.cos(perp_rad)
            base_y1 = center_y + base_width * math.sin(perp_rad)
            base_x2 = center_x - base_width * math.cos(perp_rad)
            base_y2 = center_y - base_width * math.sin(perp_rad)

            # Цвет стрелки в зависимости от отклонения
            abs_dev = abs(self.deviation)
            if abs_dev < 3:
                arrow_color = (0.2, 0.9, 0.2, 1)  # Зелёная
            elif abs_dev < 10:
                arrow_color = (0.9, 0.85, 0.1, 1)  # Жёлтая
            elif abs_dev < 25:
                arrow_color = (0.95, 0.5, 0.1, 1)  # Оранжевая
            else:
                arrow_color = (0.9, 0.2, 0.1, 1)  # Красная

            # Тень стрелки
            Color(0, 0, 0, 0.3)
            Mesh(vertices=[
                base_x1 + 2, base_y1 - 2, 0, 0,
                base_x2 + 2, base_y2 - 2, 0, 0,
                tip_x + 2, tip_y - 2, 0, 0
            ], indices=[0, 1, 2], mode='triangles')

            # Основная стрелка
            Color(*arrow_color)
            Mesh(vertices=[
                base_x1, base_y1, 0, 0,
                base_x2, base_y2, 0, 0,
                tip_x, tip_y, 0, 0
            ], indices=[0, 1, 2], mode='triangles')

            # ============ 7. ЦЕНТРАЛЬНЫЙ КРУГ ============
            Color(0.1, 0.1, 0.15, 1)
            Line(circle=(center_x, center_y, 14), width=28, joint='round')

            # Ободок центра
            Color(0.46, 0.70, 0.71, 0.3)
            Line(circle=(center_x, center_y, 16), width=2)

            # Маленькая точка в центре
            Color(0.46, 0.70, 0.71, 0.6)
            Ellipse(pos=(center_x - 3, center_y - 3), size=(6, 6))


# ============ ЛЕЙБЛ ДЛЯ НОТЫ ============
class NoteLabel(MDLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._anim = None

    def set_note(self, note, is_in_tuning=True):
        self.text = note
        if is_in_tuning:
            self.text_color = [0.46, 0.70, 0.71, 1]
        else:
            self.text_color = [0.9, 0.7, 0.2, 1]
        if self._anim:
            self._anim.cancel(self)
        self.opacity = 0
        self._anim = Animation(opacity=1, duration=0.2)
        self._anim.start(self)


# ===================================================================
# ============ ОСНОВНОЙ ЭКРАН ============
# ===================================================================

class TunerScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'
        self.bg_image = None
        self.is_listening = False
        self.current_frequency = 0
        self.current_deviation = 0
        self.detected_note = None
        self.detected_freq = 0
        self._audio_thread = None
        self._running = False
        self._audio_backend = 'none'
        self._audio_recorder = None
        self._sounddevice_stream = None
        self._pyaudio_stream = None
        self._pyaudio = None
        self._error_message = ""
        self._attempts = []
        self._working_params = None

        self.current_tuning = 'standard_6'
        self.tuning_notes = TUNINGS[self.current_tuning]['notes']
        self.tuning_freqs = TUNINGS[self.current_tuning]['freqs']
        self.tuning_note_names = TUNINGS[self.current_tuning]['note_names']
        self.strings_count = TUNINGS[self.current_tuning]['strings']

        self.init_ui()
        self.load_background()
        self._set_debug_callback()
        Clock.schedule_once(self._init_audio, 0.5)
        logger.info('Экран тюнера создан')

    def load_background(self):
        try:
            if HAS_ASSETS:
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        logger.info(f"Фон загружен из ассета: {name}")
                        break
                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")
                    with self.canvas.before:
                        Color(1, 1, 1, 1)
                        self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                    self.bind(pos=self._update_bg, size=self._update_bg)
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    # ============ ОТЛАДКА ============
    def _set_debug_callback(self):
        try:
            if HAS_AUDIO_RECORDER:
                from utils.android_audio import set_debug_callback
                set_debug_callback(self._debug_log)
        except Exception as e:
            pass

    def _debug_log(self, message, level="INFO"):
        def _update_ui():
            if hasattr(self, '_hint_label') and not self._error_message:
                prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "DEBUG": "🔍"}.get(level, "🔍")
                self._hint_label.text = f"{prefix} {message}"
                self._hint_label.opacity = 1
                if level == "ERROR":
                    self._hint_label.text_color = [0.8, 0.2, 0.2, 1]
                elif level == "SUCCESS":
                    self._hint_label.text_color = [0.3, 0.8, 0.3, 1]
                elif level == "WARNING":
                    self._hint_label.text_color = [0.9, 0.7, 0.2, 1]
                else:
                    self._hint_label.text_color = [0.46, 0.70, 0.71, 1]

        Clock.schedule_once(lambda dt: _update_ui(), 0)
        print(f"[DEBUG] {message}")

    def _show_error(self, message):
        def _update_ui():
            self._error_message = message
            if hasattr(self, '_hint_label'):
                self._hint_label.text = f"❌ {message}"
                self._hint_label.opacity = 1
                self._hint_label.text_color = [0.8, 0.2, 0.2, 1]

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _show_success(self, message):
        def _update_ui():
            if hasattr(self, '_hint_label'):
                self._hint_label.text = f"✅ {message}"
                self._hint_label.opacity = 1
                self._hint_label.text_color = [0.3, 0.8, 0.3, 1]
                if hasattr(self, '_hint_timer'):
                    Clock.unschedule(self._hint_timer)
                self._hint_timer = Clock.schedule_once(lambda dt: self._hide_hint(), 3.0)

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _show_debug(self, message):
        def _update_ui():
            if hasattr(self, '_hint_label') and not self._error_message:
                self._hint_label.text = f"🔍 {message}"
                self._hint_label.opacity = 1
                self._hint_label.text_color = [0.46, 0.70, 0.71, 1]

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _show_status(self, message, color=None):
        if color is None:
            color = [0.46, 0.70, 0.71, 1]

        def _update_ui():
            if hasattr(self, '_hint_label'):
                self._hint_label.text = message
                self._hint_label.opacity = 1
                self._hint_label.text_color = color

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _hide_hint(self):
        def _update_ui():
            if hasattr(self, '_hint_label') and self._hint_label:
                if self._error_message:
                    return
                self._hint_label.text = ""
                self._hint_label.opacity = 0
                if hasattr(self, '_hint_timer'):
                    self._hint_timer = None

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _clear_error(self):
        def _update_ui():
            self._error_message = ""
            if hasattr(self, '_hint_label'):
                self._hint_label.text = ""
                self._hint_label.opacity = 0

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    # ============ АУДИО ============
    def _init_audio(self, dt):
        self._attempts = []
        if IS_ANDROID:
            self._show_debug("Инициализация аудио на Android...")
            try:
                from android.permissions import request_permissions, Permission
                self._show_debug("Запрос разрешения RECORD_AUDIO...")
                request_permissions([Permission.RECORD_AUDIO])
                self._show_success("Разрешение RECORD_AUDIO получено")
            except Exception as e:
                self._show_error(f"Ошибка разрешений: {str(e)[:100]}")
                return
            if HAS_AUDIO_RECORDER:
                try:
                    self._show_debug("Инициализация JNI AudioRecord...")
                    self._audio_recorder = get_audio_recorder()
                    self._audio_backend = 'android_jni'
                    self._show_success("JNI AudioRecord готов")
                    return
                except Exception as e:
                    self._show_error(f"JNI AudioRecord: {str(e)[:100]}")
                    return
            self._show_error("Аудио не доступно на Android")
            self._audio_backend = 'none'
        else:
            self._init_audio_windows()

    def _init_audio_windows(self):
        # ... (код инициализации аудио, как в предыдущей версии)
        pass

    # Остальные методы аудио (как в предыдущей версии)
    # ...

    def _process_frequency(self, freq):
        if not self.is_listening:
            return
        note, note_freq, diff = freq_to_note(freq, self.tuning_note_names, self.tuning_freqs)
        if note:
            cents = cents_deviation(freq, note_freq)

            if hasattr(self, 'note_label'):
                self.note_label.text = note
            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.1f} Hz"

            if abs(cents) < 3:
                self._show_success("В СТРОЕ!")
            elif abs(cents) < 10:
                self._show_status(f"{cents:+.1f} цент", [0.95, 0.85, 0.1, 1])
            elif abs(cents) < 25:
                self._show_status(f"{cents:+.1f} цент", [0.95, 0.5, 0.1, 1])
            else:
                self._show_status(f"{cents:+.1f} цент", [0.85, 0.15, 0.15, 1])

            if hasattr(self, 'tuner_dial'):
                self.tuner_dial.deviation = cents
        else:
            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.1f} Hz"
            if hasattr(self, 'tuner_dial'):
                self.tuner_dial.deviation = 0

    # ============ UI ============
    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        content_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(8), dp(4), dp(8), total_bottom]
        )

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(2),
            size_hint=(1, None),
            adaptive_height=True
        )

        # ============ СТРОЙ ============
        tuning_info = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(18),
            spacing=dp(8),
            padding=[dp(8), dp(0), dp(8), dp(0)]
        )
        self.tuning_name_label = MDLabel(
            text=TUNINGS[self.current_tuning]['name'],
            font_size=sp(9),
            halign="center",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.2],
            bold=False
        )
        tuning_info.add_widget(self.tuning_name_label)
        content.add_widget(tuning_info)

        # ============ ТЮНЕР ============
        dial_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(360),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )
        self.tuner_dial = TunerDial()
        dial_container.add_widget(self.tuner_dial)
        content.add_widget(dial_container)

        # ============ НОТА И ЧАСТОТА ============
        info_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(70),
            spacing=dp(2),
            padding=[dp(16), dp(4), dp(16), dp(4)]
        )

        self.note_label = MDLabel(
            text="--",
            font_size=sp(32),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )

        self.freq_label = MDLabel(
            text="--",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 0.7],
            bold=True
        )

        info_container.add_widget(self.note_label)
        info_container.add_widget(self.freq_label)
        content.add_widget(info_container)

        # ============ МЕНЮ ============
        menu_card = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            padding=[dp(4), dp(4), dp(4), dp(4)],
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.08],
            line_width=0.5,
            spacing=0
        )

        self.play_btn = MDIconButton(
            icon="play",
            size_hint=(1, 1),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.toggle_tuner
        )
        divider1 = MDBoxLayout(size_hint_x=None, width=dp(1), md_bg_color=[1, 1, 1, 0.08])
        self.tuning_btn = MDIconButton(
            icon="tune",
            size_hint=(1, 1),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.8],
            md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self._show_tuning_dialog()
        )
        divider2 = MDBoxLayout(size_hint_x=None, width=dp(1), md_bg_color=[1, 1, 1, 0.08])
        self.reset_btn = MDIconButton(
            icon="refresh",
            size_hint=(1, 1),
            theme_icon_color="Custom",
            icon_color=[0.7, 0.3, 0.3, 0.7],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.reset_tuner
        )

        menu_card.add_widget(self.play_btn)
        menu_card.add_widget(divider1)
        menu_card.add_widget(self.tuning_btn)
        menu_card.add_widget(divider2)
        menu_card.add_widget(self.reset_btn)
        content.add_widget(menu_card)

        # ============ СТАТУС ============
        self._hint_label = MDLabel(
            text="",
            font_size=sp(10),
            halign="center",
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            opacity=0
        )
        content.add_widget(self._hint_label)

        content_container.add_widget(content)
        content_container.add_widget(Widget(size_hint_y=1))
        main_layout.add_widget(content_container)
        self.add_widget(main_layout)
        logger.info("UI тюнера построен")

    def toggle_tuner(self, instance):
        if not self.is_listening:
            if self._audio_backend == 'none':
                self._show_error("Аудио не инициализировано")
                return
            self._show_debug("Запуск тюнера...")
            self.is_listening = True
            self.play_btn.icon = "stop"
            self.play_btn.icon_color = [0.8, 0.3, 0.3, 1]
            self._start_audio_thread()
        else:
            self._show_debug("Остановка тюнера...")
            self.is_listening = False
            self.play_btn.icon = "play"
            self.play_btn.icon_color = [0.46, 0.70, 0.71, 1]
            self._stop_audio_thread()
            if hasattr(self, 'tuner_dial'):
                self.tuner_dial.deviation = 0
            if hasattr(self, 'freq_label'):
                self.freq_label.text = "--"
            if hasattr(self, 'note_label'):
                self.note_label.text = "--"
            if hasattr(self, '_hint_label'):
                self._hint_label.text = ""
                self._hint_label.opacity = 0
            self._show_debug("Тюнер остановлен")

    def reset_tuner(self, instance):
        if self.is_listening:
            self.toggle_tuner(None)
        if hasattr(self, 'tuner_dial'):
            self.tuner_dial.deviation = 0
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "--"
        if hasattr(self, 'note_label'):
            self.note_label.text = "--"
        if hasattr(self, '_hint_label'):
            self._hint_label.text = ""
            self._hint_label.opacity = 0
        self._clear_error()
        logger.info("🔄 Тюнер сброшен")

    def _show_tuning_dialog(self):
        content = MDBoxLayout(orientation='vertical', spacing=dp(8), padding=dp(16),
                              size_hint_y=None, adaptive_height=True)
        categories = {
            '🎸 Гитара': ['standard_6', 'drop_d', 'open_g', 'open_d', 'dadgad', 'half_step_down'],
            '🎸 Бас': ['bass_4', 'bass_5'],
            '🎵 Укулеле': ['ukulele'],
        }
        for category, tuning_ids in categories.items():
            cat_label = MDLabel(text=category, font_size=sp(14), bold=True,
                                size_hint_y=None, height=dp(32),
                                theme_text_color="Custom", text_color=[0.46, 0.70, 0.71, 1])
            content.add_widget(cat_label)
            for tid in tuning_ids:
                if tid in TUNINGS:
                    t = TUNINGS[tid]
                    is_active = tid == self.current_tuning
                    btn = MDRaisedButton(
                        text=t['name'],
                        size_hint=(1, None), height=dp(44),
                        md_bg_color=[0.46, 0.70, 0.71, 1] if is_active else [0.2, 0.2, 0.2, 0.6],
                        text_color=[1, 1, 1, 1],
                        on_release=lambda x, tid2=tid: self._select_tuning(tid2)
                    )
                    content.add_widget(btn)
        self.tuning_dialog = MDDialog(title="Выберите строй", type="custom",
                                      content_cls=content,
                                      buttons=[MDRaisedButton(text="Закрыть",
                                                              on_release=lambda x: self.tuning_dialog.dismiss())])
        self.tuning_dialog.open()

    def _select_tuning(self, tuning_id):
        if self.tuning_dialog:
            self.tuning_dialog.dismiss()
        if tuning_id == self.current_tuning:
            return
        self.current_tuning = tuning_id
        t = TUNINGS[tuning_id]
        self.tuning_notes = t['notes']
        self.tuning_freqs = t['freqs']
        self.tuning_note_names = t['note_names']
        self.strings_count = t['strings']
        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = t['name']
        if hasattr(self, 'tuner_dial'):
            self.tuner_dial.deviation = 0
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "--"
        if hasattr(self, 'note_label'):
            self.note_label.text = "--"
        notify.success(f"Строй: {t['name']}")
        logger.info(f"🎸 Выбран строй: {t['name']}")

    def on_enter(self):
        logger.info("Вход в экран тюнера")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.force_update_title("Тюнер", show_back=True)
            app.top_nav.set_custom_back_callback(self.go_back)

    def go_back(self, instance=None):
        logger.info("🔙 Возврат на home")
        if self.is_listening:
            self.toggle_tuner(None)
        self._stop_audio_thread()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_back_callback()
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_leave(self):
        logger.info("Выход из экрана тюнера")
        if self.is_listening:
            self.toggle_tuner(None)
        self._stop_audio_thread()
        self._hide_hint()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            app.top_nav.update_title('home')