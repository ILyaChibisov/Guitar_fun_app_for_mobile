# screens/tuner_screen.py
"""
Экран гитарного тюнера — горизонтальная шкала + эталонные ноты
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


# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
def get_temp_path():
    """Возвращает безопасный путь для временных файлов на Android"""
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
    """
    Генерирует чистый эталонный звук ноты
    С гармониками и плавным затуханием
    """
    sample_rate = 44100
    num_samples = int(sample_rate * duration)

    # Гармоники (обертоны) для реалистичности
    harmonics = [
        (1, 1.0),  # Основная
        (2, 0.60),  # 2-я
        (3, 0.35),  # 3-я
        (4, 0.20),  # 4-я
        (5, 0.10),  # 5-я
    ]

    audio_data = array.array('h')

    for i in range(num_samples):
        t = i / sample_rate

        value = 0.0
        for harmonic, amp in harmonics:
            freq = frequency * harmonic
            phase = harmonic * 0.2
            value += amp * math.sin(2 * math.pi * freq * t + phase)

        # Плавное затухание
        decay_rate = 2.0
        envelope = math.exp(-t * decay_rate)

        # Атака
        attack_time = 0.01
        if t < attack_time:
            attack = t / attack_time
        else:
            attack = 1.0

        value = value * envelope * attack * volume
        value = clamp_value(value, -1.0, 1.0)

        audio_data.append(int(32767 * value))

    return audio_data


def play_reference_note(frequency):
    """
    Воспроизводит эталонную ноту через временный WAV
    """
    try:
        from kivy.core.audio import SoundLoader

        audio_data = generate_reference_note(frequency)

        temp_dir = get_temp_path()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=temp_dir) as tmp_file:
            tmp_path = tmp_file.name
            with open(tmp_path, 'wb') as f:
                f.write(b'RIFF')
                f.write(struct.pack('<I', 36 + len(audio_data) * 2))
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write(struct.pack('<I', 16))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<I', 44100))
                f.write(struct.pack('<I', 44100 * 2))
                f.write(struct.pack('<H', 2))
                f.write(struct.pack('<H', 16))
                f.write(b'data')
                f.write(struct.pack('<I', len(audio_data) * 2))
                audio_data.tofile(f)

        sound = SoundLoader.load(tmp_path)

        if sound:
            sound.play()
            # Удаляем файл после воспроизведения
            Clock.schedule_once(lambda dt: clean_temp_file(tmp_path), sound.length + 0.1)
            return True

        return False

    except Exception as e:
        logger.error(f"Ошибка воспроизведения эталонной ноты: {e}")
        return False


def clean_temp_file(path):
    """Удаляет временный файл"""
    try:
        if os.path.exists(path):
            os.unlink(path)
    except:
        pass


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
# ============ ГОРИЗОНТАЛЬНЫЙ ТЮНЕР СО СТРЕЛКОЙ ============
# ===================================================================

# ===================================================================
# ============ ГОРИЗОНТАЛЬНЫЙ ТЮНЕР СО СТРЕЛКОЙ ============
# ===================================================================

class ModernHorizontalTuner(Widget):
    """
    Горизонтальная шкала тюнера с градиентной полосой
    и стрелкой-указателем из ассетов
    """
    deviation = NumericProperty(0)

    def __init__(self, **kwargs):
        super(ModernHorizontalTuner, self).__init__(**kwargs)
        self.scale_rects = []  # полоски градиента
        self.labels = []  # подписи
        self.arrow_texture = None  # текстура стрелки
        self.arrow_rect = None  # прямоугольник для стрелки

        self.bind(pos=self.update_gauge, size=self.update_gauge)
        self.bind(deviation=self.update_gauge)

        # Загружаем стрелку из ассетов
        Clock.schedule_once(self._load_arrow_texture, 0)
        Clock.schedule_once(self._init_components, 0.1)

    def _load_arrow_texture(self, dt):
        """Загружает текстуру стрелки из ассетов"""
        try:
            from data import load_asset_as_bytes

            # Пробуем загрузить ассет
            arrow_data = load_asset_as_bytes("guitar_tune_png")

            if arrow_data:
                from kivy.core.image import Image as CoreImage
                from io import BytesIO

                img = CoreImage(BytesIO(arrow_data), ext="png")
                self.arrow_texture = img.texture
                logger.info("✅ Стрелка загружена из ассета guitar_tune_png")
            else:
                # Если ассет не найден, создаем стрелку программно
                logger.warning("⚠️ Ассет guitar_tune_png не найден, создаем стрелку программно")
                self._create_fallback_arrow()

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки стрелки: {e}")
            self._create_fallback_arrow()

        self.update_gauge()

    def _create_fallback_arrow(self):
        """Создает стрелку-заглушку программно (для отладки)"""
        from kivy.graphics.texture import Texture

        # Создаем простую текстуру со стрелкой
        size = 64
        texture = Texture.create(size=(size, size))

        # Рисуем простую стрелку в текстуре
        pixels = bytearray(size * size * 4)

        for y in range(size):
            for x in range(size):
                # Нормализованные координаты
                nx = x / size
                ny = y / size

                # Стрелка указывает вниз (как треугольник)
                cx = 0.5
                cy = 0.3

                # Проверяем попадание в треугольник
                half_width = 0.3 * (1 - ny * 0.8)
                if ny >= 0.2 and abs(nx - cx) < half_width:
                    alpha = 255
                else:
                    alpha = 0

                idx = (y * size + x) * 4
                pixels[idx:idx + 4] = bytes([255, 255, 255, alpha])

        texture.blit_buffer(pixels, colorfmt='rgba', bufferfmt='ubyte')
        self.arrow_texture = texture
        logger.info("✅ Создана стрелка-заглушка")

    def _init_components(self, dt):
        """Инициализирует компоненты шкалы"""
        # Создаем стрелку как Rectangle с текстурой
        with self.canvas:
            self.arrow_rect = Rectangle(
                texture=self.arrow_texture,
                pos=(0, 0),
                size=(dp(24), dp(36))
            )

        self.update_gauge()

    @staticmethod
    def _gradient_color(pct):
        """
        pct: 0.0–1.0 по шкале от -50 до +50 центов.
        Возвращает RGB цвет: красный -> жёлтый -> зелёный -> жёлтый -> красный
        """
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

    def update_gauge(self, *args):
        """Обновляет все элементы шкалы"""
        # Сохраняем ссылку на стрелку
        arrow_rect = self.arrow_rect

        # Очищаем canvas (кроме стрелки)
        self.canvas.clear()

        # Удаляем старые подписи
        for label in self.labels:
            if label.parent:
                self.remove_widget(label)
        self.labels.clear()

        if self.width <= 0 or self.height <= 0:
            return

        scale_w = self.width * 0.85
        scale_x = self.center_x - scale_w / 2
        scale_y = self.center_y + dp(20)  # Поднимаем шкалу выше для места под ней

        # ===== 1. ГРАДИЕНТНАЯ ПОЛОСА =====
        strip_w = max(1.5, scale_w / 120)
        n_strips = int(scale_w // strip_w)
        if n_strips < 2:
            n_strips = 2

        for i in range(n_strips):
            pct = i / (n_strips - 1) if n_strips > 1 else 0.5
            r, g, b = self._gradient_color(pct)
            x = scale_x + i * strip_w

            with self.canvas:
                Color(r, g, b, 0.85)
                Rectangle(pos=(x, scale_y - dp(12)), size=(strip_w + 0.5, dp(24)))

        # Обводка полосы
        with self.canvas:
            Color(0.3, 0.35, 0.4, 0.5)
            Line(
                rectangle=(
                    scale_x - 1,
                    scale_y - dp(13),
                    scale_w + 2,
                    dp(26)
                ),
                width=0.8
            )

        # ===== 2. ЗАСЕЧКИ (только каждые 10 центов) =====
        # Засечки: -50, -40, -30, -20, -10, 0, +10, +20, +30, +40, +50
        num_ticks = 11  # от -50 до +50 с шагом 10
        tick_positions = []
        for i in range(num_ticks):
            pos_pct = i / (num_ticks - 1)
            value = -50 + i * 10
            tick_positions.append((pos_pct, value))

        for pos_pct, value in tick_positions:
            curr_x = scale_x + pos_pct * scale_w

            # Определяем высоту засечки
            if value == 0:
                h = dp(28)  # Центральная - самая высокая
                line_width = 2.5
                color = [0.6, 0.65, 0.7, 1]
            else:
                h = dp(18)  # Остальные - средние
                line_width = 1.8
                color = [0.5, 0.55, 0.6, 0.9]

            with self.canvas:
                Color(*color)
                Line(
                    points=[
                        curr_x, scale_y - h / 2,
                        curr_x, scale_y + h / 2
                    ],
                    width=line_width
                )

        # ===== 3. ПОДПИСИ (каждые 10) =====
        # Подписи: -50, -40, -30, -20, -10, 0, +10, +20, +30, +40, +50
        for i in range(num_ticks):
            pos_pct = i / (num_ticks - 1)
            value = -50 + i * 10
            curr_x = scale_x + pos_pct * scale_w
            is_zero = (value == 0)

            # Форматируем текст с знаком +
            if value > 0:
                text = f"+{value}"
            else:
                text = str(value)

            color = [0.18, 0.8, 0.44, 1] if is_zero else [0.5, 0.55, 0.6, 0.7]
            font_size = sp(13) if is_zero else sp(11)

            lbl = Label(
                text=text,
                font_size=font_size,
                bold=is_zero,
                color=color,
                size_hint=(None, None),
                size=(dp(40), dp(18)),
                center=(curr_x, scale_y - dp(32)),
                halign='center',
                valign='middle'
            )
            self.add_widget(lbl)
            self.labels.append(lbl)

        # ===== 4. СТРЕЛКА-ИНДИКАТОР =====
        dev = max(-50, min(50, self.deviation))
        val_pct = (dev - (-50)) / 100.0
        indicator_x = scale_x + val_pct * scale_w

        # Размер стрелки
        arrow_width = dp(28)
        arrow_height = dp(40)

        # Стрелка опущена ниже шкалы
        arrow_x = indicator_x - arrow_width / 2
        arrow_y = scale_y - dp(12) - arrow_height + dp(8)

        # Обновляем позицию стрелки
        if self.arrow_rect:
            self.arrow_rect.pos = (arrow_x, arrow_y)
            self.arrow_rect.size = (arrow_width, arrow_height)

            if not self.arrow_texture:
                self._create_fallback_arrow()
                self.arrow_rect.texture = self.arrow_texture

        if self.arrow_rect:
            self.canvas.add(self.arrow_rect)

    def set_value(self, value):
        """Устанавливает отклонение и обновляет шкалу"""
        self.deviation = clamp_value(value, -50, 50)

    def animate_to(self, value, duration=0.15):
        """Плавная анимация индикатора"""
        self.deviation = clamp_value(value, -50, 50)


# ===================================================================
# ============ КНОПКА ЭТАЛОННОЙ НОТЫ ============
# ===================================================================

class NoteButton(MDCard):
    """Кнопка-кружок для эталонной ноты"""

    note_name = StringProperty('')
    frequency = NumericProperty(0)
    is_active = BooleanProperty(False)

    def __init__(self, note_name, frequency, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.note_name = note_name
        self.frequency = frequency
        self.on_press_callback = on_press

        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (dp(40), dp(40))
        self.radius = [dp(20)] * 4
        self.md_bg_color = [0.2, 0.2, 0.3, 0.6]
        self.elevation = 2
        self.line_color = [0.46, 0.70, 0.71, 0.3]
        self.line_width = 1
        self.ripple_behavior = True

        self.label = MDLabel(
            text=note_name,
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True,
            size_hint=(1, 1)
        )
        self.add_widget(self.label)

        self.bind(on_release=self._on_press)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _on_enter(self, *args):
        self.elevation = 4
        self.md_bg_color = [0.3, 0.3, 0.4, 0.8]

    def _on_leave(self, *args):
        self.elevation = 2
        if not self.is_active:
            self.md_bg_color = [0.2, 0.2, 0.3, 0.6]

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.note_name, self.frequency)

        # Анимация нажатия
        anim = Animation(size=(dp(44), dp(44)), duration=0.05)
        anim += Animation(size=(dp(40), dp(40)), duration=0.05)
        anim.start(self)

    def set_active(self, active):
        self.is_active = active
        if active:
            self.md_bg_color = [0.46, 0.70, 0.71, 0.8]
            self.line_color = [0.46, 0.70, 0.71, 1]
            self.label.text_color = [1, 1, 1, 1]
            self.elevation = 6
        else:
            self.md_bg_color = [0.2, 0.2, 0.3, 0.6]
            self.line_color = [0.46, 0.70, 0.71, 0.3]
            self.label.text_color = [1, 1, 1, 0.9]
            self.elevation = 2


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
        self._note_buttons = []

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
        logger.info("=" * 70)
        logger.info("🔍 ПОИСК МИКРОФОНА (Windows)")
        logger.info("=" * 70)
        all_devices = []
        if HAS_SOUNDDEVICE:
            try:
                import sounddevice as sd
                for i, d in enumerate(sd.query_devices()):
                    if d['max_input_channels'] > 0:
                        all_devices.append({
                            'library': 'sounddevice',
                            'index': i,
                            'name': d['name'],
                            'channels': d['max_input_channels'],
                            'rate': int(d.get('default_samplerate', 0))
                        })
                        logger.info(f"   sounddevice [{i}]: {d['name']}")
            except Exception as e:
                logger.error(f"sounddevice: {e}")
        if HAS_PYAUDIO:
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                for i in range(p.get_device_count()):
                    info = p.get_device_info_by_index(i)
                    if info.get('maxInputChannels', 0) > 0:
                        all_devices.append({
                            'library': 'pyaudio',
                            'index': i,
                            'name': info.get('name', 'Unknown'),
                            'channels': info.get('maxInputChannels', 0),
                            'rate': int(info.get('defaultSampleRate', 0))
                        })
                        logger.info(f"   pyaudio [{i}]: {info.get('name')}")
                p.terminate()
            except Exception as e:
                logger.error(f"pyaudio: {e}")
        if not all_devices:
            self._show_error("Нет аудио устройств!")
            self._audio_backend = 'none'
            return
        logger.info(f"📋 Найдено устройств: {len(all_devices)}")
        all_devices.sort(key=lambda d: 0 if 'realtek' in d['name'].lower() and 'mic' in d['name'].lower() else 1)
        for dev in all_devices:
            library = dev['library']
            device_index = dev['index']
            device_name = dev['name']
            max_channels = min(1, dev['channels'])
            rates_to_try = [48000, 44100, 22050, 16000, 11025, 8000]
            if dev['rate'] > 0 and dev['rate'] in rates_to_try:
                rates_to_try.remove(dev['rate'])
                rates_to_try.insert(0, dev['rate'])
            if library == 'pyaudio':
                formats = [(pyaudio.paInt16, 'paInt16'), (pyaudio.paInt32, 'paInt32')]
            else:
                formats = [('float32', 'float32')]
            for fmt, fmt_name in formats:
                for rate in rates_to_try:
                    try:
                        if library == 'sounddevice':
                            import sounddevice as sd
                            s = sd.InputStream(device=device_index, samplerate=rate,
                                               channels=max_channels, blocksize=CHUNK_SIZE,
                                               dtype='float32', latency='high')
                        else:
                            import pyaudio
                            p = pyaudio.PyAudio()
                            s = p.open(format=fmt, channels=max_channels, rate=rate,
                                       input=True, input_device_index=device_index,
                                       frames_per_buffer=CHUNK_SIZE, start=False)
                        s.start()
                        s.stop()
                        s.close()
                        self._working_params = {
                            'library': library, 'device_index': device_index,
                            'device_name': device_name, 'rate': rate,
                            'channels': max_channels,
                            'format': fmt if library == 'pyaudio' else None,
                            'fmt_name': fmt_name
                        }
                        self._audio_backend = library
                        logger.info(f"✅ РАБОТАЕТ: {library} -> {device_name} ({fmt_name}, {rate}Hz)")
                        self._show_success(f"{library}: {device_name[:30]} ({rate}Hz)")
                        return
                    except Exception as e:
                        continue
        self._show_error("Не удалось найти рабочий микрофон. Проверьте подключение.")
        self._audio_backend = 'none'

    def _start_audio_thread(self):
        if self._running:
            return
        if self._audio_backend == 'none':
            self._show_error("Аудио не инициализировано")
            return
        self._running = True
        self._clear_error()
        self._show_debug(f"Запуск бэкенда: {self._audio_backend}")
        if self._audio_backend == 'android_jni':
            if self._audio_recorder:
                try:
                    self._audio_recorder.start_recording(
                        callback=self._on_audio_data,
                        sample_rate=SAMPLE_RATE,
                        chunk_size=CHUNK_SIZE
                    )
                    self._show_success("JNI AudioRecord запущен")
                except Exception as e:
                    self._show_error(f"JNI AudioRecord: {str(e)[:100]}")
                    self._running = False
        elif self._audio_backend == 'sounddevice':
            self._audio_thread = threading.Thread(target=self._audio_loop_sounddevice)
            self._audio_thread.daemon = True
            self._audio_thread.start()
            self._show_success("sounddevice запущен")
        elif self._audio_backend == 'pyaudio':
            self._audio_thread = threading.Thread(target=self._audio_loop_pyaudio)
            self._audio_thread.daemon = True
            self._audio_thread.start()
            self._show_success("pyaudio запущен")
        else:
            self._show_error(f"Неизвестный бэкенд: {self._audio_backend}")
            self._running = False

    def _on_audio_data(self, data):
        if not self.is_listening or not self._running:
            return
        if data:
            freq = detect_pitch(data, SAMPLE_RATE)
            if freq > 0:
                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))

    def _audio_loop_sounddevice(self):
        try:
            import sounddevice as sd
            import numpy as np
            params = self._working_params
            selected_rate = params['rate']
            device_index = params['device_index']
            device_name = params['device_name']

            def callback(indata, frames, time_info, status):
                if not self._running or not self.is_listening:
                    return
                try:
                    if indata is not None and len(indata) > 0:
                        audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
                        data_bytes = audio_int16.tobytes()
                        if len(data_bytes) > 0:
                            freq = detect_pitch(data_bytes, selected_rate)
                            if freq > 0:
                                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))
                except Exception as e:
                    pass

            self._sounddevice_stream = sd.InputStream(
                device=device_index, samplerate=selected_rate,
                channels=1, callback=callback, blocksize=CHUNK_SIZE,
                dtype='float32', latency='high'
            )
            self._sounddevice_stream.start()
            logger.info(f"✅ sounddevice запущен ({device_name})")
            while self._running:
                time.sleep(0.1)
            if self._sounddevice_stream:
                self._sounddevice_stream.stop()
                self._sounddevice_stream.close()
                self._sounddevice_stream = None
        except Exception as e:
            self._show_error(f"sounddevice: {str(e)[:150]}")
            self._running = False

    def _audio_loop_pyaudio(self):
        try:
            import pyaudio
            params = self._working_params
            selected_rate = params['rate']
            device_index = params['device_index']
            device_name = params['device_name']
            selected_format = params['format']
            self._pyaudio = pyaudio.PyAudio()
            stream = self._pyaudio.open(
                format=selected_format, channels=1, rate=selected_rate,
                input=True, input_device_index=device_index,
                frames_per_buffer=CHUNK_SIZE, start=True
            )
            self._pyaudio_stream = stream
            logger.info(f"✅ pyaudio запущен ({device_name})")
            while self._running:
                try:
                    if stream.is_active():
                        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                        if data:
                            freq = detect_pitch(data, selected_rate)
                            if freq > 0:
                                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))
                except:
                    break
            if stream:
                stream.stop_stream()
                stream.close()
            if self._pyaudio:
                self._pyaudio.terminate()
                self._pyaudio = None
        except Exception as e:
            self._show_error(f"pyaudio: {str(e)[:150]}")
            self._running = False

    def _stop_audio_thread(self):
        self._running = False
        if self._audio_backend == 'android_jni' and self._audio_recorder:
            try:
                self._audio_recorder.stop_recording()
            except:
                pass
        if self._audio_backend == 'sounddevice' and self._sounddevice_stream:
            try:
                self._sounddevice_stream.stop()
                self._sounddevice_stream.close()
                self._sounddevice_stream = None
            except:
                pass
        if self._audio_backend == 'pyaudio':
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

        # Обновляем частоту
        self.current_frequency = freq

        note, note_freq, diff = freq_to_note(freq, self.tuning_note_names, self.tuning_freqs)

        if note:
            cents = cents_deviation(freq, note_freq)
            self.current_deviation = cents

            # Обновляем индикатор
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(cents)

            # Обновляем информацию
            if hasattr(self, 'note_label'):
                self.note_label.text = note
                if abs(cents) < 3:
                    self.note_label.text_color = [0.18, 0.8, 0.44, 1]
                elif abs(cents) < 12:
                    self.note_label.text_color = [1, 1, 1, 1]
                else:
                    self.note_label.text_color = [1, 1, 1, 1]

            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.1f} Hz"

            if hasattr(self, 'cents_label'):
                sign = "+" if cents >= 0 else ""
                self.cents_label.text = f"{sign}{cents:.1f} cents"
                if abs(cents) < 3:
                    self.cents_label.text_color = [0.18, 0.8, 0.44, 1]
                elif abs(cents) < 12:
                    self.cents_label.text_color = [0.2, 0.6, 1, 1]
                else:
                    self.cents_label.text_color = [0.9, 0.3, 0.3, 1]

            # Статус
            if abs(cents) < 3:
                self._show_success("В СТРОЕ!")
            elif abs(cents) < 10:
                self._show_status(f"{cents:+.1f} цент", [0.95, 0.85, 0.1, 1])
            elif abs(cents) < 25:
                self._show_status(f"{cents:+.1f} цент", [0.95, 0.5, 0.1, 1])
            else:
                self._show_status(f"{cents:+.1f} цент", [0.85, 0.15, 0.15, 1])
        else:
            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.1f} Hz"
            if hasattr(self, 'tuner_gauge'):
                self.tuner_gauge.set_value(0)

    # ============ ЭТАЛОННЫЕ НОТЫ ============
    def on_reference_note_pressed(self, note_name, frequency):
        """Обработчик нажатия на эталонную ноту"""
        logger.info(f"🎵 Эталонная нота: {note_name} ({frequency:.2f} Hz)")

        # Сбрасываем активность всех кнопок
        for btn in self._note_buttons:
            btn.set_active(False)

        # Активируем нажатую кнопку
        for btn in self._note_buttons:
            if btn.note_name == note_name:
                btn.set_active(True)
                break

        # Воспроизводим звук
        play_reference_note(frequency)

        # Показываем в интерфейсе
        if hasattr(self, 'note_label'):
            self.note_label.text = note_name

        # Через 2 секунды сбрасываем подсветку
        Clock.schedule_once(lambda dt: self._reset_note_buttons(), 2.0)

    def _reset_note_buttons(self):
        """Сбрасывает подсветку кнопок нот"""
        for btn in self._note_buttons:
            btn.set_active(False)

    def _update_note_buttons(self):
        """Обновляет кнопки нот при смене строя"""
        if not self._note_buttons:
            return

        note_names = self.tuning_note_names
        freqs = self.tuning_freqs

        for i, btn in enumerate(self._note_buttons):
            if i < len(note_names):
                btn.note_name = note_names[i]
                btn.frequency = freqs[i]
                btn.label.text = note_names[i]
                btn.opacity = 1
                btn.disabled = False
            else:
                btn.opacity = 0
                btn.disabled = True

    # ============ ДИАЛОГ ВЫБОРА СТРОЯ ============
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

        # Обновляем UI
        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = t['name']

        if hasattr(self, 'tuner_gauge'):
            self.tuner_gauge.set_value(0)

        if hasattr(self, 'freq_label'):
            self.freq_label.text = "--"

        if hasattr(self, 'note_label'):
            self.note_label.text = "--"

        if hasattr(self, 'cents_label'):
            self.cents_label.text = "--"

        # Обновляем кнопки нот
        self._update_note_buttons()

        # Сбрасываем подсветку
        self._reset_note_buttons()

        notify.success(f"Строй: {t['name']}")
        logger.info(f"🎸 Выбран строй: {t['name']}")

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

        # ============ НОТА (по центру вверху) ============
        self.note_label = MDLabel(
            text="--",
            font_size=sp(60),
            halign="center",
            size_hint_y=None,
            height=dp(70),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )
        content.add_widget(self.note_label)

        # ============ ГОРИЗОНТАЛЬНЫЙ ТЮНЕР ============
        gauge_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            padding=[dp(8), dp(0), dp(8), dp(0)]
        )
        self.tuner_gauge = ModernHorizontalTuner()
        gauge_container.add_widget(self.tuner_gauge)
        content.add_widget(gauge_container)

        # ============ ЧАСТОТА И ЦЕНТЫ (по бокам под шкалой) ============
        info_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(30),
            spacing=dp(16),
            padding=[dp(24), dp(0), dp(24), dp(0)]
        )

        self.freq_label = MDLabel(
            text="--",
            font_size=sp(13),
            halign="left",
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7],
            bold=False
        )

        self.cents_label = MDLabel(
            text="--",
            font_size=sp(13),
            halign="right",
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7],
            bold=False
        )

        info_container.add_widget(self.freq_label)
        info_container.add_widget(self.cents_label)
        content.add_widget(info_container)

        # ============ НАЗВАНИЕ СТРОЯ ============
        tuning_info = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(20),
            padding=[dp(8), dp(4), dp(8), dp(0)]
        )
        self.tuning_name_label = MDLabel(
            text=TUNINGS[self.current_tuning]['name'],
            font_size=sp(11),
            halign="center",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3],
            bold=False
        )
        tuning_info.add_widget(self.tuning_name_label)
        content.add_widget(tuning_info)

        # ============ ЭТАЛОННЫЕ НОТЫ (по центру, без подписи) ============
        notes_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8),
            padding=[dp(16), dp(4), dp(16), dp(8)]
        )

        note_names = self.tuning_note_names
        freqs = self.tuning_freqs

        # Создаем кнопки нот
        for i, (name, freq) in enumerate(zip(note_names, freqs)):
            btn = NoteButton(
                note_name=name,
                frequency=freq,
                on_press=self.on_reference_note_pressed
            )
            self._note_buttons.append(btn)
            notes_row.add_widget(btn)

        # Добавляем пустые виджеты для центрирования, если нот меньше 6
        if len(note_names) < 6:
            for _ in range(6 - len(note_names)):
                notes_row.add_widget(Widget(size_hint_x=1))

        content.add_widget(notes_row)

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
            self._show_debug("Тюнер остановлен")

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
        logger.info("🔄 Тюнер сброшен")

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