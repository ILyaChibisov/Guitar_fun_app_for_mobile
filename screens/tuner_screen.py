# screens/tuner_screen.py
"""
Экран гитарного тюнера — горизонтальная шкала + эталонные ноты.
Адаптирован под 3 темы и 6 языков.
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.utils import platform, get_color_from_hex
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

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from utils.notifications import notify
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('Tuner')

IS_WINDOWS = sys.platform == 'win32' or sys.platform == 'win64'
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
        except:
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
    except:
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


# ============ ГОРИЗОНТАЛЬНЫЙ ТЮНЕР ============

class ModernHorizontalTuner(Widget):
    deviation = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scale_rects = []
        self.labels = []
        self.arrow_texture = None
        self.arrow_rect = None
        self.bind(pos=self.update_gauge, size=self.update_gauge)
        self.bind(deviation=self.update_gauge)
        Clock.schedule_once(self._load_arrow_texture, 0)
        Clock.schedule_once(self._init_components, 0.1)

    def _load_arrow_texture(self, dt):
        try:
            arrow_data = load_asset_as_bytes("guitar_tune_png")
            if arrow_data:
                img = CoreImage(BytesIO(arrow_data), ext="png")
                self.arrow_texture = img.texture
            else:
                self._create_fallback_arrow()
        except Exception as e:
            logger.error(f"Ошибка загрузки стрелки: {e}")
            self._create_fallback_arrow()
        self.update_gauge()

    def _create_fallback_arrow(self):
        from kivy.graphics.texture import Texture
        size = 64
        texture = Texture.create(size=(size, size))
        pixels = bytearray(size * size * 4)
        for y in range(size):
            for x in range(size):
                nx, ny = x / size, y / size
                half_width = 0.3 * (1 - ny * 0.8)
                alpha = 255 if ny >= 0.2 and abs(nx - 0.5) < half_width else 0
                idx = (y * size + x) * 4
                pixels[idx:idx + 4] = bytes([255, 255, 255, alpha])
        texture.blit_buffer(pixels, colorfmt='rgba', bufferfmt='ubyte')
        self.arrow_texture = texture

    def _init_components(self, dt):
        with self.canvas:
            self.arrow_rect = Rectangle(texture=self.arrow_texture, pos=(0, 0), size=(dp(24), dp(36)))
        self.update_gauge()

    @staticmethod
    def _get_segment_color(value, max_value=50):
        normalized = max(-1, min(1, value / max_value))
        pct = (normalized + 1) / 2
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
        arrow_rect = self.arrow_rect
        self.canvas.clear()
        for label in self.labels:
            if label.parent:
                self.remove_widget(label)
        self.labels.clear()
        if self.width <= 0 or self.height <= 0:
            return

        scale_w = self.width * 0.9
        scale_x = self.center_x - scale_w / 2
        scale_y = self.center_y + dp(20)
        num_segments = 21
        segment_width = scale_w / num_segments
        gap = dp(1.5)
        segment_height = dp(24)

        for i in range(num_segments):
            value = -50 + i * 5
            x = scale_x + i * segment_width + gap / 2
            r, g, b = self._get_segment_color(value, 50)
            brightness = 0.7 + 0.3 * (1 - abs(value) / 50)
            with self.canvas:
                Color(r * brightness, g * brightness, b * brightness, 0.85)
                Rectangle(pos=(x, scale_y - segment_height / 2), size=(segment_width - gap, segment_height))

        for i in range(11):
            pos_pct = i / 10.0
            value = -50 + i * 10
            curr_x = scale_x + pos_pct * scale_w
            is_zero = (value == 0)
            text = f"+{value}" if value > 0 else str(value)
            r, g, b = self._get_segment_color(value, 50)
            color = [r, g, b, 1.0] if is_zero else [r, g, b, 0.7]
            lbl = Label(text=text, font_size=sp(14 if is_zero else 11), bold=is_zero,
                        color=color, size_hint=(None, None), size=(dp(44), dp(18)),
                        center=(curr_x, scale_y - dp(34)), halign='center', valign='middle')
            self.add_widget(lbl)
            self.labels.append(lbl)

        dev = max(-50, min(50, self.deviation))
        indicator_x = scale_x + ((dev + 50) / 100.0) * scale_w
        arrow_width = dp(28)
        arrow_height = dp(40)
        if self.arrow_rect:
            self.arrow_rect.pos = (indicator_x - arrow_width / 2,
                                   scale_y - segment_height / 2 - arrow_height + dp(8))
            self.arrow_rect.size = (arrow_width, arrow_height)
            if not self.arrow_texture:
                self._create_fallback_arrow()
                self.arrow_rect.texture = self.arrow_texture
        if self.arrow_rect:
            self.canvas.add(self.arrow_rect)

    def set_value(self, value):
        self.deviation = clamp_value(value, -50, 50)


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
                import tempfile
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
        except:
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

        # ✅ Сначала фон, потом UI (исправляет AttributeError: bg_rect)
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

        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text_color = text_s
            self.tuning_name_label.text = get_text(TUNINGS[self.current_tuning]['name_key'])
        if hasattr(self, 'note_label'):
            self.note_label.text_color = text_p
        if hasattr(self, 'freq_label'):
            self.freq_label.text_color = text_s
        if hasattr(self, 'cents_label'):
            self.cents_label.text_color = text_s
        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.update_gauge()

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

    def update_language(self):
        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = get_text(TUNINGS[self.current_tuning]['name_key'])

    def _set_debug_callback(self):
        try:
            if HAS_AUDIO_RECORDER:
                set_debug_callback(self._debug_log)
        except:
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

    def _show_debug(self, message):
        def _update():
            if hasattr(self, '_hint_label') and not self._error_message:
                self._hint_label.text = f"🔍 {message}"
                self._hint_label.opacity = 1
                self._hint_label.text_color = TunerColors.get_hint_color(settings_manager.theme)
        Clock.schedule_once(lambda dt: _update(), 0)

    def _show_status(self, message, color=None):
        if color is None:
            color = TunerColors.get_hint_color(settings_manager.theme)
        def _update():
            if hasattr(self, '_hint_label'):
                self._hint_label.text = message
                self._hint_label.opacity = 1
                self._hint_label.text_color = color
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

    # ============ АУДИО ============
    def _init_audio(self, dt):
        self._attempts = []
        if IS_ANDROID:
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.RECORD_AUDIO])
            except:
                pass
            if HAS_AUDIO_RECORDER:
                try:
                    self._audio_recorder = get_audio_recorder()
                    self._audio_backend = 'android_jni'
                    return
                except:
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
            except:
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
            except:
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
                    except:
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
            except:
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
                except:
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
                except:
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
            except:
                pass
        if self._sounddevice_stream:
            try:
                self._sounddevice_stream.stop()
                self._sounddevice_stream.close()
            except:
                pass
            self._sounddevice_stream = None
        if self._pyaudio_stream:
            try:
                self._pyaudio_stream.stop_stream()
                self._pyaudio_stream.close()
            except:
                pass
            self._pyaudio_stream = None
        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except:
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
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(cents)
            if hasattr(self, 'note_label'):
                self.note_label.text = note
                self.note_label.text_color = ([0.18, 0.8, 0.44, 1] if abs(cents) < 3
                                              else TunerColors.get_text_primary(settings_manager.theme))
            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.1f} Hz"
            if hasattr(self, 'cents_label'):
                sign = "+" if cents >= 0 else ""
                self.cents_label.text = f"{sign}{cents:.1f} {get_text('cents')}"
                if abs(cents) < 3:
                    self.cents_label.text_color = [0.18, 0.8, 0.44, 1]
                elif abs(cents) < 12:
                    self.cents_label.text_color = [0.2, 0.6, 1, 1]
                else:
                    self.cents_label.text_color = [0.9, 0.3, 0.3, 1]
            if abs(cents) < 3:
                self._show_success(get_text('in_tune'))
            elif abs(cents) < 10:
                self._show_status(f"{cents:+.1f} {get_text('cents')}", [0.95, 0.85, 0.1, 1])
            elif abs(cents) < 25:
                self._show_status(f"{cents:+.1f} {get_text('cents')}", [0.95, 0.5, 0.1, 1])
            else:
                self._show_status(f"{cents:+.1f} {get_text('cents')}", [0.85, 0.15, 0.15, 1])
        else:
            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.1f} Hz"
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(0)

    def on_reference_note_pressed(self, note_name, frequency):
        for btn in self._note_buttons:
            btn.set_active(False)
        for btn in self._note_buttons:
            if btn.note_name == note_name:
                btn.set_active(True)
                break
        if hasattr(self, 'note_label'):
            display_name = ''.join(c for c in note_name if not c.isdigit())
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
                self.note_label.text = "--"
            self.note_label.text_color = TunerColors.get_text_primary(settings_manager.theme)

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
        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = get_text(t['name_key'])
        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(0)
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "--"
        if hasattr(self, 'note_label'):
            self.note_label.text = "--"
        if hasattr(self, 'cents_label'):
            self.cents_label.text = "--"
        self._update_note_buttons()
        self._reset_note_buttons()
        notify.success(f"{get_text('tuning')}: {get_text(t['name_key'])}")

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        main_layout.add_widget(Widget(size_hint_y=None, height=layout_config.get_top_padding()))
        total_bottom = dp(60) + get_navigation_bar_height() + dp(16)
        content_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                                        padding=[dp(8), dp(4), dp(8), total_bottom])
        content = MDBoxLayout(orientation='vertical', spacing=dp(2),
                              size_hint=(1, None), adaptive_height=True)

        tuning_info = MDBoxLayout(orientation='horizontal', size_hint=(1, None),
                                  height=dp(24), padding=[dp(8), dp(2), dp(8), dp(0)])
        self.tuning_name_label = MDLabel(
            text=get_text(TUNINGS[self.current_tuning]['name_key']),
            font_size=sp(12), halign="center", size_hint_x=1,
            theme_text_color="Custom", bold=False)
        tuning_info.add_widget(self.tuning_name_label)
        content.add_widget(tuning_info)

        self.note_label = MDLabel(text="--", font_size=sp(60), halign="center",
                                  size_hint_y=None, height=dp(70),
                                  theme_text_color="Custom", bold=True)
        content.add_widget(self.note_label)

        gauge_container = MDBoxLayout(orientation='vertical', size_hint=(1, None),
                                      height=dp(120), padding=[dp(8), dp(0), dp(8), dp(0)])
        self.tuner_gauge = ModernHorizontalTuner()
        gauge_container.add_widget(self.tuner_gauge)
        content.add_widget(gauge_container)

        info_container = MDBoxLayout(orientation='horizontal', size_hint=(1, None),
                                     height=dp(30), spacing=dp(16),
                                     padding=[dp(24), dp(0), dp(24), dp(0)])
        self.freq_label = MDLabel(text="--", font_size=sp(13), halign="left",
                                  size_hint_x=0.5, theme_text_color="Custom")
        self.cents_label = MDLabel(text="--", font_size=sp(13), halign="right",
                                   size_hint_x=0.5, theme_text_color="Custom")
        info_container.add_widget(self.freq_label)
        info_container.add_widget(self.cents_label)
        content.add_widget(info_container)

        notes_row = MDBoxLayout(orientation='horizontal', size_hint=(1, None),
                                height=dp(44), spacing=dp(8),
                                padding=[dp(16), dp(4), dp(16), dp(8)])
        for display_name, full_name, freq in zip(self.tuning_note_names,
                                                 self.tuning_notes,
                                                 self.tuning_freqs):
            btn = NoteButton(note_name=full_name, display_name=display_name,
                             frequency=freq, tuning_id=self.current_tuning,
                             on_press=self.on_reference_note_pressed)
            self._note_buttons.append(btn)
            notes_row.add_widget(btn)
        if len(self.tuning_note_names) < 6:
            notes_row.add_widget(Widget(size_hint_x=1), index=0)
            notes_row.add_widget(Widget(size_hint_x=1))
        content.add_widget(notes_row)

        self.menu_card = MDCard(orientation='horizontal', size_hint=(1, None),
                                height=dp(48), padding=[dp(4), dp(4), dp(4), dp(4)],
                                radius=[dp(12)], elevation=0, spacing=0)
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

    def toggle_tuner(self, instance):
        if not self.is_listening:
            if self._audio_backend == 'none':
                self._show_error(get_text('audio_not_init'))
                return
            self.is_listening = True
            self.play_btn.icon = "stop"
            self.play_btn.icon_color = [0.8, 0.3, 0.3, 1]
            self._start_audio_thread()
        else:
            self.is_listening = False
            self.play_btn.icon = "play"
            self.play_btn.icon_color = TunerColors.get_accent(settings_manager.theme)
            self._stop_audio_thread()
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(0)
            if hasattr(self, 'freq_label'):
                self.freq_label.text = "--"
            if hasattr(self, 'note_label'):
                self.note_label.text = "--"
            if hasattr(self, 'cents_label'):
                self.cents_label.text = "--"
            if hasattr(self, '_hint_label'):
                self._hint_label.text = ""
                self._hint_label.opacity = 0
            self._reset_note_buttons()

    def reset_tuner(self, instance):
        if self.is_listening:
            self.toggle_tuner(None)
        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(0)
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "--"
        if hasattr(self, 'note_label'):
            self.note_label.text = "--"
        if hasattr(self, 'cents_label'):
            self.cents_label.text = "--"
        if hasattr(self, '_hint_label'):
            self._hint_label.text = ""
            self._hint_label.opacity = 0
        self._reset_note_buttons()
        self._clear_error()

    def on_enter(self):
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