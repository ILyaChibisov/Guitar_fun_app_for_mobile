# screens/tuner_screen.py
"""
Экран гитарного тюнера — горизонтальная шкала в стиле tuner7 + эталонные ноты.
Адаптирован под 3 темы (green, dark, light) и 6 языков.
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

from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from utils.notifications import notify
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('Tuner')

IS_WINDOWS = sys.platform in ('win32', 'win64')
IS_ANDROID = platform == 'android'

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

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

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024


# ============================================================
# ЦВЕТА ДЛЯ ТЮНЕРА (адаптация под темы)
# ============================================================

class TunerColors:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        else:
            return [0.46, 0.70, 0.71, 1]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 1]
        else:
            return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        else:
            return [1, 1, 1, 0.5]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.1]
        else:
            return [0, 0, 0, 0.06]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        else:
            return [1, 1, 1, 0.08]

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        else:
            return [1, 1, 1, 0.5]


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


def clamp_value(value, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, value))


def generate_reference_note(frequency, duration=2.0, volume=0.6):
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    harmonics = [(1, 1.0), (2, 0.60), (3, 0.35), (4, 0.20), (5, 0.10)]
    audio_data = array.array('h')
    for i in range(num_samples):
        t = i / sample_rate
        value = 0.0
        for harmonic, amp in harmonics:
            value += amp * math.sin(2 * math.pi * frequency * harmonic * t + harmonic * 0.2)
        envelope = math.exp(-t * 2.0)
        attack = t / 0.01 if t < 0.01 else 1.0
        value = clamp_value(value * envelope * attack * volume, -1.0, 1.0)
        audio_data.append(int(32767 * value))
    return audio_data


def clean_temp_file(path):
    try:
        if os.path.exists(path):
            os.unlink(path)
    except Exception:
        pass


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
    except Exception:
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
    max_lag_limit = int(sample_rate / 80)
    if max_lag_limit > len(samples) // 2:
        max_lag_limit = len(samples) // 2
    if min_lag >= max_lag_limit:
        return 0
    for lag in range(min_lag, max_lag_limit):
        corr = sum(samples[i] * samples[i + lag] for i in range(len(samples) - lag))
        corr_values.append((lag, corr))
        if corr > max_corr:
            max_corr = corr
            max_lag = lag
    if max_lag == 0:
        return 0
    if max_lag > min_lag and max_lag < max_lag_limit - 1:
        prev_corr = next((c for l, c in corr_values if l == max_lag - 1), 0)
        next_corr = next((c for l, c in corr_values if l == max_lag + 1), 0)
        if prev_corr > 0 and next_corr > 0:
            denom = prev_corr - 2 * max_corr + next_corr
            if denom != 0:
                max_lag += (prev_corr - next_corr) / (2 * denom)
    if max_lag > 0:
        freq = sample_rate / max_lag
        if 80 < freq < 800:
            return freq
    return 0


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


# ============ ГОРИЗОНТАЛЬНЫЙ ТЮНЕР В СТИЛЕ TUNER7 ============

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
        ticks = [
            (-50, "-50"),
            (-25, "-25"),
            (0, "0"),
            (25, "+25"),
            (50, "+50"),
        ]
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
        max_h = dp(28)
        min_h = dp(10)

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
                curr_height = min_h + (max_h - min_h) * height_factor
                r, g, b = self._get_segment_color(value, 50)
                dist = abs(dev - value)

                with self.canvas:
                    Color(*outline_color)
                    Line(rounded_rectangle=(x, scale_y - curr_height / 2, segment_width - gap, curr_height, dp(3.5)),
                         width=1.2)

                if dist < 4.5:
                    glow_alpha = 0.35 * (1.0 - dist / 4.5)
                    Color(r, g, b, glow_alpha)
                    RoundedRectangle(
                        pos=(x - dp(2), scale_y - curr_height / 2 - dp(3)),
                        size=(segment_width - gap + dp(4), curr_height + dp(6)),
                        radius=[dp(5)]
                    )
                    brightness = 1.0
                    alpha = 1.0
                else:
                    brightness = 0.62 + 0.25 * (1.0 - norm_dist)
                    alpha = 0.78

                Color(r * brightness, g * brightness, b * brightness, alpha)
                RoundedRectangle(pos=(x, scale_y - curr_height / 2), size=(segment_width - gap, curr_height),
                                 radius=[dp(3.5)])

            ix = scale_x + ((dev + 50.0) / 100.0) * scale_w
            bar_bottom = scale_y - max_h / 2
            tip_y = bar_bottom - dp(8)
            base_y = tip_y - dp(15)
            half_w = dp(9)

            Color(active_rgb[0], active_rgb[1], active_rgb[2], 0.28)
            Triangle(
                points=[ix, tip_y + dp(3), ix - half_w - dp(4), base_y - dp(2), ix + half_w + dp(4), base_y - dp(2)])

            Color(*outline_color)
            Line(points=[ix, tip_y, ix - half_w, base_y, ix, base_y + dp(4)], width=1.2)
            Line(points=[ix, tip_y, ix + half_w, base_y, ix, base_y + dp(4)], width=1.2)

            Color(active_rgb[0], active_rgb[1], active_rgb[2], 1.0)
            Triangle(points=[ix, tip_y, ix - half_w, base_y, ix, base_y + dp(4)])

            Color(active_rgb[0] * 0.78, active_rgb[1] * 0.78, active_rgb[2] * 0.78, 1.0)
            Triangle(points=[ix, tip_y, ix + half_w, base_y, ix, base_y + dp(4)])


# ============ КНОПКА ЭТАЛОННОЙ НОТЫ ============

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
        self.size = (dp(40), dp(40))
        self.radius = [dp(20)] * 4
        self.elevation = 2
        self.ripple_behavior = True

        self.label = MDLabel(
            text=display_name, font_size=sp(13), halign="center", valign="middle",
            theme_text_color="Custom", bold=True, size_hint=(1, 1)
        )
        self.add_widget(self.label)

        self.bind(on_release=self._on_press)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)
        self.update_theme_colors()
        Clock.schedule_once(self._load_sound_from_assets, 0.1)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = TunerColors.get_accent(theme_id)
        text = TunerColors.get_text_primary(theme_id)
        self.md_bg_color = TunerColors.get_card_bg(theme_id)
        self.line_color = accent[:3] + [0.5]
        self.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5
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
            sound_class = getattr(module, module_name.title().replace('_', '') + 'Sounds')
            self._sound = sound_class.get_sound(self.note_name)
            self._sound_data = sound_class.get_sound_data(self.note_name)
            if not self._sound:
                self._generate_fallback_sound()
        except Exception:
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

    def _on_enter(self, *args):
        self.elevation = 4
        self.md_bg_color = TunerColors.get_card_bg(settings_manager.theme)

    def _on_leave(self, *args):
        self.elevation = 2
        if not self.is_active:
            self.md_bg_color = TunerColors.get_card_bg(settings_manager.theme)

    def _on_press(self, instance):
        if self.is_playing:
            return
        if self.on_press_callback:
            self.on_press_callback(self.note_name, self.frequency)
        anim = Animation(size=(dp(44), dp(44)), duration=0.05)
        anim += Animation(size=(dp(40), dp(40)), duration=0.05)
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
            self.elevation = 6
        else:
            self.update_theme_colors()
            self.elevation = 2


# ============ ОСНОВНОЙ ЭКРАН ============

class TunerScreen(BaseScreen):
    target_note = StringProperty("--")
    target_freq = NumericProperty(0.0)
    indicator_color = ListProperty([0.2, 0.95, 0.65, 1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
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
        self._note_buttons = []

        self.current_tuning = 'standard_6'
        self.tuning_notes = TUNINGS[self.current_tuning]['notes']
        self.tuning_freqs = TUNINGS[self.current_tuning]['freqs']
        self.tuning_note_names = TUNINGS[self.current_tuning]['note_names']
        self.strings_count = TUNINGS[self.current_tuning]['strings']

        self.selected_string_index = 3
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
        accent = TunerColors.get_accent(theme_id)
        text_p = TunerColors.get_text_primary(theme_id)
        text_s = TunerColors.get_text_secondary(theme_id)

        if hasattr(self, 'main_tuner_card'):
            self.main_tuner_card.md_bg_color = TunerColors.get_card_bg(theme_id)
            self.main_tuner_card.line_color = TunerColors.get_card_line(theme_id)

        if hasattr(self, 'note_label'):
            is_tuned = abs(self.current_deviation) <= 3.0 and self.is_listening
            self.note_label.text_color = [0.2, 0.95, 0.65, 1.0] if is_tuned else text_p
            self.note_label.font_size = sp(100)  # Принудительный фикс размера

        if hasattr(self, 'freq_label'):
            self.freq_label.text_color = accent

        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text_color = text_s
            self.tuning_name_label.text = get_text(TUNINGS[self.current_tuning]['name_key'])

        if hasattr(self, 'label_low'):
            self.label_low.text_color = text_s
            self.label_high.text_color = text_s

        if hasattr(self, 'status_label'):
            self.update_status_ui()

        if hasattr(self, 'menu_card'):
            self.menu_card.md_bg_color = TunerColors.get_card_bg(theme_id)
            self.menu_card.line_color = TunerColors.get_card_line(theme_id)
            self.menu_card.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5

        if hasattr(self, 'play_btn'):
            self.play_btn.icon_color = accent if not self.is_listening else [0.8, 0.3, 0.3, 1]
        if hasattr(self, 'tuning_btn'):
            self.tuning_btn.icon_color = accent
        if hasattr(self, 'reset_btn'):
            self.reset_btn.icon_color = [0.7, 0.3, 0.3, 0.7]
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
        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = get_text(TUNINGS[self.current_tuning]['name_key'])
        self.update_status_ui()

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
            prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "DEBUG": "🔍"}.get(level, "🔍")
            self._hint_label.text = f"{prefix} {message}"
            self._hint_label.opacity = 1

    def _show_error(self, message):
        def _update():
            self._error_message = message
            if hasattr(self, '_hint_label'):
                self._hint_label.text = f"❌ {message}"
                self._hint_label.opacity = 1
                self._hint_label.text_color = [0.8, 0.2, 0.2, 1]

        Clock.schedule_once(lambda dt: _update(), 0)

    def _show_success(self, message):
        def _update():
            if hasattr(self, '_hint_label'):
                self._hint_label.text = f"✅ {message}"
                self._hint_label.opacity = 1
                self._hint_label.text_color = [0.3, 0.8, 0.3, 1]
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

    def update_status_ui(self):
        if not hasattr(self, 'status_label'):
            return

        dev = self.current_deviation
        if not self.is_listening:
            self.status_label.text = ""
            self.status_label.opacity = 0
        else:
            self.status_label.opacity = 1
            if abs(dev) <= 3.0:
                self.status_label.text = get_text("in_tune")
                self.status_label.text_color = [0.2, 0.95, 0.65, 1]
            elif dev < -3.0:
                self.status_label.text = get_text("low", "LOW")
                self.status_label.text_color = [0.95, 0.5, 0.1, 1]
            else:
                self.status_label.text = get_text("high", "HIGH")
                self.status_label.text_color = [0.85, 0.15, 0.15, 1]

    # ============ АУДИО ============
    def _init_audio(self, dt):
        self._attempts = []
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
            freq = detect_pitch(data, SAMPLE_RATE)
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
                    freq = detect_pitch(audio_int16.tobytes(), rate)
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
                        freq = detect_pitch(data, self._working_params['rate'])
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
        self.current_frequency = freq

        note, note_freq, _ = freq_to_note(freq, self.tuning_note_names, self.tuning_freqs)
        if note:
            cents = cents_deviation(freq, note_freq)
            self.current_deviation = cents

            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(cents)

            if hasattr(self, 'note_label'):
                self.note_label.text = note
                is_tuned = abs(cents) <= 3.0
                self.note_label.text_color = [0.2, 0.95, 0.65, 1.0] if is_tuned else TunerColors.get_text_primary(
                    settings_manager.theme)

            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.2f} Hz"

            self.update_status_ui()

    def on_reference_note_pressed(self, note_name, frequency):
        for btn in self._note_buttons:
            btn.set_active(False)
        for btn in self._note_buttons:
            if btn.note_name == note_name:
                btn.set_active(True)
                break

        display_name = ''.join(c for c in note_name if not c.isdigit())
        self.target_note = display_name
        self.target_freq = frequency

        if hasattr(self, 'note_label'):
            self.note_label.text = display_name
            self.note_label.text_color = TunerColors.get_accent(settings_manager.theme)
            Clock.schedule_once(lambda dt: self._reset_note_display(), 2.0)
        Clock.schedule_once(lambda dt: self._reset_note_buttons(), 2.5)

    def _reset_note_display(self):
        if hasattr(self, 'note_label'):
            if self.is_listening and self.current_frequency > 0:
                note, _, _ = freq_to_note(self.current_frequency, self.tuning_note_names, self.tuning_freqs)
                self.note_label.text = note or "--"
            else:
                self.note_label.text = self.target_note
            self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)
            self.update_status_ui()

    def _reset_note_buttons(self):
        for btn in self._note_buttons:
            btn.set_active(False)

    def _update_note_buttons(self):
        if not self._note_buttons:
            return
        for i, btn in enumerate(self._note_buttons):
            if i < len(self.tuning_note_names):
                btn.note_name = self.tuning_notes[i]
                btn.display_name = self.tuning_note_names[i]
                btn.frequency = self.tuning_freqs[i]
                btn.label.text = self.tuning_note_names[i]
                btn.opacity = 1
                btn.disabled = False
            else:
                btn.opacity = 0
                btn.disabled = True

    def _show_tuning_dialog(self):
        content = MDBoxLayout(orientation='vertical', spacing=dp(8), padding=dp(16),
                              size_hint_y=None, adaptive_height=True)
        categories = [
            ('guitar', ['standard_6', 'drop_d', 'open_g', 'open_d', 'dadgad', 'half_step_down']),
            ('bass', ['bass_4', 'bass_5']),
            ('ukulele', ['ukulele']),
        ]
        theme_id = settings_manager.theme
        accent = TunerColors.get_accent(theme_id)
        for cat_key, tuning_ids in categories:
            cat_label = MDLabel(text=get_text(cat_key), font_size=sp(14), bold=True,
                                size_hint_y=None, height=dp(32),
                                theme_text_color="Custom", text_color=accent)
            content.add_widget(cat_label)
            for tid in tuning_ids:
                if tid in TUNINGS:
                    t = TUNINGS[tid]
                    is_active = tid == self.current_tuning
                    btn = MDRaisedButton(
                        text=get_text(t['name_key']),
                        size_hint=(1, None), height=dp(44),
                        md_bg_color=accent if is_active else TunerColors.get_card_bg(theme_id),
                        text_color=[1, 1, 1, 1],
                        on_release=lambda x, tid2=tid: self._select_tuning(tid2))
                    content.add_widget(btn)
        self.tuning_dialog = MDDialog(
            title=get_text('choose_tuning'), type="custom", content_cls=content,
            buttons=[MDRaisedButton(text=get_text('close'),
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

        self.selected_string_index = 0
        self.target_note = self.tuning_note_names[0]
        self.target_freq = self.tuning_freqs[0]

        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = get_text(t['name_key'])
        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(0)
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "-- Hz"
        if hasattr(self, 'note_label'):
            self.note_label.text = self.target_note
        self.current_deviation = 0
        self._update_note_buttons()
        self._reset_note_buttons()
        self.update_status_ui()
        notify.success(f"{get_text('tuning')}: {get_text(t['name_key'])}")

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        main_layout.add_widget(Widget(size_hint_y=None, height=layout_config.get_top_padding()))

        total_bottom = dp(60) + get_navigation_bar_height() + dp(16)
        content_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                                        padding=[dp(16), dp(4), dp(16), total_bottom])
        content = MDBoxLayout(orientation='vertical', spacing=dp(12),
                              size_hint=(1, None), adaptive_height=True)

        # 1. Карточка тюнера
        self.main_tuner_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(340),
            radius=[dp(24)],
            md_bg_color=TunerColors.get_card_bg(settings_manager.theme),
            line_color=TunerColors.get_card_line(settings_manager.theme),
            line_width=dp(1),
            elevation=0,
            padding=[dp(16), dp(8), dp(16), dp(12)],
            spacing=dp(4),
        )

        # 1.1 Название строя (Перенесено сверху)
        self.tuning_name_label = MDLabel(
            text=get_text(TUNINGS[self.current_tuning]['name_key']),
            font_size=sp(15),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            bold=True,
            text_color=TunerColors.get_text_secondary(settings_manager.theme)
        )
        self.main_tuner_card.add_widget(self.tuning_name_label)

        # 1.2 Крупная нота
        note_anchor = AnchorLayout(size_hint_y=None, height=dp(110))
        self.note_label = MDLabel(
            text=self.target_note,
            font_size=sp(100),
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(110),
            text_size=(None, None),
            theme_text_color="Custom",
            text_color=TunerColors.get_text_primary(settings_manager.theme)
        )
        self.note_label.bind(on_size=lambda *args: setattr(self.note_label, 'font_size', sp(100)))
        note_anchor.add_widget(self.note_label)
        self.main_tuner_card.add_widget(note_anchor)

        # 1.3 Текущая частота
        self.freq_label = MDLabel(
            text="-- Hz",
            font_size=sp(15),
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=TunerColors.get_accent(settings_manager.theme)
        )
        self.main_tuner_card.add_widget(self.freq_label)

        # 1.4 Шкала
        gauge_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(100)
        )
        self.tuner_gauge = ModernHorizontalTuner(
            size_hint_y=None,
            height=dp(100)
        )
        self.tuner_gauge.bind(indicator_color=self._update_indicator_color)
        gauge_container.add_widget(self.tuner_gauge)
        self.main_tuner_card.add_widget(gauge_container)

        # 1.5 Подписи LOW / IN TUNE / HIGH
        labels_box = MDBoxLayout(
            size_hint_y=None,
            height=dp(18),
            padding=[dp(12), 0]
        )
        self.label_low = MDLabel(
            text=get_text("low", "LOW").upper(), font_size=sp(11), bold=True, halign="left",
            theme_text_color="Custom", text_color=TunerColors.get_text_secondary(settings_manager.theme)
        )
        self.label_in_tune = MDLabel(
            text=get_text("in_tune").replace("!", ""), font_size=sp(11), bold=True, halign="center",
            theme_text_color="Custom", text_color=[0.2, 0.95, 0.65, 1]
        )
        self.label_high = MDLabel(
            text=get_text("high", "HIGH").upper(), font_size=sp(11), bold=True, halign="right",
            theme_text_color="Custom", text_color=TunerColors.get_text_secondary(settings_manager.theme)
        )
        labels_box.add_widget(self.label_low)
        labels_box.add_widget(self.label_in_tune)
        labels_box.add_widget(self.label_high)
        self.main_tuner_card.add_widget(labels_box)

        # 1.6 Статус (Listening / LOW / HIGH / IN TUNE) - скрыт по умолчанию
        self.status_label = MDLabel(
            text="",
            font_size=sp(14),
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            opacity=0,
            text_color=TunerColors.get_text_primary(settings_manager.theme)
        )
        self.main_tuner_card.add_widget(self.status_label)

        content.add_widget(self.main_tuner_card)

        # 2. Кнопки струн
        notes_row = MDBoxLayout(orientation='horizontal', size_hint=(1, None),
                                height=dp(44), spacing=dp(8),
                                padding=[dp(16), dp(4), dp(16), dp(8)])
        for display_name, full_name, freq in zip(self.tuning_note_names, self.tuning_notes, self.tuning_freqs):
            btn = NoteButton(note_name=full_name, display_name=display_name,
                             frequency=freq, tuning_id=self.current_tuning,
                             on_press=self.on_reference_note_pressed)
            self._note_buttons.append(btn)
            notes_row.add_widget(btn)
        if len(self.tuning_note_names) < 6:
            notes_row.add_widget(Widget(size_hint_x=1))
            notes_row.add_widget(Widget(size_hint_x=1))
        content.add_widget(notes_row)

        # 3. Нижнее меню
        self.menu_card = MDCard(orientation='horizontal', size_hint=(1, None),
                                height=dp(48), padding=[dp(4), dp(4), dp(4), dp(4)],
                                radius=[dp(12)], elevation=0, spacing=0,
                                md_bg_color=TunerColors.get_card_bg(settings_manager.theme),
                                line_color=TunerColors.get_card_line(settings_manager.theme),
                                line_width=dp(1))
        self.play_btn = MDIconButton(icon="play", size_hint=(1, 1),
                                     theme_icon_color="Custom",
                                     md_bg_color=[0, 0, 0, 0], on_release=self.toggle_tuner)
        divider1 = MDBoxLayout(size_hint_x=None, width=dp(1), md_bg_color=[1, 1, 1, 0.08])
        self.tuning_btn = MDIconButton(icon="tune", size_hint=(1, 1),
                                       theme_icon_color="Custom",
                                       md_bg_color=[0, 0, 0, 0],
                                       on_release=lambda x: self._show_tuning_dialog())
        divider2 = MDBoxLayout(size_hint_x=None, width=dp(1), md_bg_color=[1, 1, 1, 0.08])
        self.reset_btn = MDIconButton(icon="refresh", size_hint=(1, 1),
                                      theme_icon_color="Custom",
                                      md_bg_color=[0, 0, 0, 0], on_release=self.reset_tuner)
        self.menu_card.add_widget(self.play_btn)
        self.menu_card.add_widget(divider1)
        self.menu_card.add_widget(self.tuning_btn)
        self.menu_card.add_widget(divider2)
        self.menu_card.add_widget(self.reset_btn)
        content.add_widget(self.menu_card)

        # 4. Подсказка
        self._hint_label = MDLabel(text="", font_size=sp(10), halign="center",
                                   size_hint_y=None, height=dp(22),
                                   theme_text_color="Custom", opacity=0)
        content.add_widget(self._hint_label)

        content_container.add_widget(content)
        content_container.add_widget(Widget(size_hint_y=1))
        main_layout.add_widget(content_container)
        self.add_widget(main_layout)

        self.update_theme_colors()
        logger.info("UI тюнера построен")

    def _update_indicator_color(self, instance, value):
        self.indicator_color = value

    def toggle_tuner(self, instance):
        if not self.is_listening:
            if self._audio_backend == 'none':
                self._show_error(get_text('audio_not_init'))
                return
            self.is_listening = True
            self.play_btn.icon = "stop"
            self.play_btn.icon_color = [0.8, 0.3, 0.3, 1]
            self.status_label.text = get_text("listening", "Listening...")
            self.status_label.opacity = 1
            self.status_label.text_color = TunerColors.get_text_primary(settings_manager.theme)
            self._start_audio_thread()
        else:
            self.is_listening = False
            self.play_btn.icon = "play"
            self.play_btn.icon_color = TunerColors.get_accent(settings_manager.theme)
            self._stop_audio_thread()
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(0)
            if hasattr(self, 'freq_label'):
                self.freq_label.text = "-- Hz"
            if hasattr(self, 'note_label'):
                self.note_label.text = self.target_note
            self.current_deviation = 0
            self.update_status_ui()
            self._reset_note_buttons()

    def reset_tuner(self, instance):
        if self.is_listening:
            self.toggle_tuner(None)
        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(0)
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "-- Hz"
        if hasattr(self, 'note_label'):
            self.note_label.text = self.target_note
        self.current_deviation = 0
        self.update_status_ui()
        self._reset_note_buttons()
        self._clear_error()

    def on_enter(self):
        super().on_enter()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_back_callback(self.go_back)
        self.update_theme_colors()

    def go_back(self, instance=None):
        if self.is_listening:
            self.toggle_tuner(None)
        self._stop_audio_thread()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_back_callback()
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_leave(self):
        if self.is_listening:
            self.toggle_tuner(None)
        self._stop_audio_thread()
        self._hide_hint()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_back_callback()