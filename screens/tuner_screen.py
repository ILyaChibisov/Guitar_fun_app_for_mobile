# screens/tuner_screen.py
"""
Экран гитарного тюнера - универсальный
Windows: максимальное количество попыток (sounddevice, pyaudio, WASAPI, MME)
Android: JNI AudioRecord (будет донастроен)
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
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
    from utils.android_audio import get_audio_recorder

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
    'bass_4': {
        'name': 'Бас 4-струнный',
        'strings': 4,
        'notes': ['E1', 'A1', 'D2', 'G2'],
        'freqs': [41.20, 55.00, 73.42, 98.00],
        'note_names': ['E', 'A', 'D', 'G'],
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
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
    'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
    'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88,
    'C1': 32.70, 'C#1': 34.65, 'D1': 36.71, 'D#1': 38.89,
    'E1': 41.20, 'F1': 43.65, 'F#1': 46.25, 'G1': 49.00,
    'G#1': 51.91, 'A1': 55.00, 'A#1': 58.27, 'B1': 61.74,
    'C2': 65.41, 'C#2': 69.30, 'D2': 73.42, 'D#2': 77.78,
    'E2': 82.41, 'F2': 87.31, 'F#2': 92.50, 'G2': 98.00,
    'G#2': 103.83, 'A2': 110.00, 'A#2': 116.54, 'B2': 123.47,
}


# ============ ОПРЕДЕЛЕНИЕ ЧАСТОТЫ ============
def detect_pitch(audio_data, sample_rate=SAMPLE_RATE):
    """
    Определяет частоту через автокорреляцию
    """
    if not audio_data or len(audio_data) < 100:
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

    # Центрируем сигнал
    mean = sum(samples) / len(samples) if samples else 0
    samples = [s - mean for s in samples]

    # Автокорреляция
    max_corr = 0
    max_lag = 0

    min_lag = int(sample_rate / 800)
    max_lag = int(sample_rate / 80)

    if max_lag > len(samples) // 2:
        max_lag = len(samples) // 2

    if min_lag >= max_lag:
        return 0

    for lag in range(min_lag, max_lag):
        corr = sum(samples[i] * samples[i + lag] for i in range(len(samples) - lag))
        if corr > max_corr:
            max_corr = corr
            max_lag = lag

    if max_lag > 0:
        freq = sample_rate / max_lag
        if 80 < freq < 800:
            return freq

    return 0


def freq_to_note(freq):
    """Преобразует частоту в ближайшую ноту"""
    closest_note = None
    closest_freq = None
    min_diff = float('inf')

    for note, note_freq in NOTES.items():
        diff = abs(freq - note_freq)
        if diff < min_diff:
            min_diff = diff
            closest_note = note
            closest_freq = note_freq

    if min_diff < 30:
        return closest_note, closest_freq, min_diff
    return None, None, None


def cents_deviation(freq, target_freq):
    """Отклонение в центах (-50..50)"""
    if target_freq == 0:
        return 0
    cents = 1200 * math.log2(freq / target_freq)
    return max(-50, min(50, cents))


# ============ КОМПОНЕНТЫ UI ============

class NoteScale(Widget):
    """Шкала нот"""

    current_note = StringProperty('--')
    highlighted_notes = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.highlighted_notes = []
        self.current_note = '--'

        self.bind(pos=self.redraw, size=self.redraw)
        self.bind(current_note=self.redraw)
        self.bind(highlighted_notes=self.redraw)

    def redraw(self, *args):
        self.canvas.clear()

        if self.width <= 0 or self.height <= 0:
            return

        with self.canvas:
            Color(0.1, 0.1, 0.1, 0.3)
            Rectangle(
                pos=(self.x, self.y),
                size=(self.width, self.height)
            )

            Color(0.46, 0.70, 0.71, 0.2)
            Line(
                rectangle=(self.x, self.y, self.width, self.height),
                width=1
            )

            note_width = self.width / len(self.notes)
            note_height = self.height * 0.7
            note_y = self.y + self.height * 0.15

            for i, note in enumerate(self.notes):
                x = self.x + i * note_width + note_width / 2

                is_highlighted = note in self.highlighted_notes
                is_current = note == self.current_note

                if is_current:
                    Color(0.46, 0.70, 0.71, 0.3)
                    Ellipse(
                        pos=(x - note_width * 0.3, note_y - note_height * 0.1),
                        size=(note_width * 0.6, note_height * 0.8)
                    )
                elif is_highlighted:
                    Color(0.46, 0.70, 0.71, 0.15)
                    Ellipse(
                        pos=(x - note_width * 0.25, note_y - note_height * 0.05),
                        size=(note_width * 0.5, note_height * 0.6)
                    )

                if is_current:
                    Color(0.46, 0.70, 0.71, 1)
                elif is_highlighted:
                    Color(0.46, 0.70, 0.71, 0.6)
                else:
                    Color(0.5, 0.5, 0.5, 0.4)

                if is_current:
                    Color(0.46, 0.70, 0.71, 0.2)
                    Ellipse(
                        pos=(x - dp(14), note_y - dp(10)),
                        size=(dp(28), dp(20))
                    )

    def set_current_note(self, note):
        self.current_note = note
        self.redraw()

    def set_highlighted(self, notes):
        self.highlighted_notes = notes
        self.redraw()


class TunerDial(Widget):
    """Круговой индикатор отклонения"""

    deviation = NumericProperty(0)
    note_name = StringProperty('--')
    note_frequency = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.deviation = 0
        self.note_name = '--'
        self.note_frequency = 0

        self.colors = {
            'green': [0.3, 0.8, 0.3, 1],
            'yellow': [0.9, 0.8, 0.2, 1],
            'red': [0.8, 0.2, 0.2, 1],
        }

        self.bind(pos=self._update, size=self._update)
        self.bind(deviation=self._update_needle)

    def _update(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.1, 0.1, 0.1, 0.4)
            Ellipse(
                pos=(self.x + self.width * 0.02, self.y + self.height * 0.02),
                size=(self.width * 0.96, self.height * 0.96)
            )

            Color(0.46, 0.70, 0.71, 0.3)
            Line(
                circle=(self.center_x, self.center_y, min(self.width, self.height) * 0.45, 0, 360),
                width=dp(2)
            )

            self._draw_scale()

            Color(0.46, 0.70, 0.71, 0.8)
            Ellipse(
                pos=(self.center_x - dp(3), self.center_y - dp(3)),
                size=(dp(6), dp(6))
            )

            self._draw_needle()

    def _draw_scale(self):
        radius = min(self.width, self.height) * 0.40

        Color(0.3, 0.8, 0.3, 0.4)
        Line(
            circle=(self.center_x, self.center_y, radius, -12, 12),
            width=dp(6)
        )

        Color(0.9, 0.8, 0.2, 0.3)
        Line(
            circle=(self.center_x, self.center_y, radius, -30, -12),
            width=dp(4)
        )
        Line(
            circle=(self.center_x, self.center_y, radius, 12, 30),
            width=dp(4)
        )

        Color(0.8, 0.2, 0.2, 0.25)
        Line(
            circle=(self.center_x, self.center_y, radius, -50, -30),
            width=dp(3)
        )
        Line(
            circle=(self.center_x, self.center_y, radius, 30, 50),
            width=dp(3)
        )

        Color(0.46, 0.70, 0.71, 0.8)
        Line(
            circle=(self.center_x, self.center_y, radius * 1.05, -1, 1),
            width=dp(2)
        )

    def _draw_needle(self):
        angle_deg = self.deviation * 45 / 50
        angle_rad = math.radians(angle_deg)
        radius = min(self.width, self.height) * 0.35

        x_end = self.center_x + radius * math.sin(angle_rad)
        y_end = self.center_y + radius * math.cos(angle_rad)

        abs_dev = abs(self.deviation)
        if abs_dev < 5:
            color = self.colors['green']
        elif abs_dev < 15:
            color = self.colors['yellow']
        else:
            color = self.colors['red']

        Color(*color)
        Line(
            points=[self.center_x, self.center_y, x_end, y_end],
            width=dp(3),
            cap='round'
        )

    def _update_needle(self, *args):
        self._update()


class NoteLabel(MDLabel):
    """Лейбл для отображения ноты с анимацией"""

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


# ============ ОСНОВНОЙ ЭКРАН ============

class TunerScreen(BaseScreen):
    """Гитарный тюнер - универсальный, с максимальными попытками"""

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
        self._device_checked = False

        # Текущий строй
        self.current_tuning = 'standard_6'
        self.tuning_notes = TUNINGS[self.current_tuning]['notes']
        self.tuning_freqs = TUNINGS[self.current_tuning]['freqs']
        self.tuning_note_names = TUNINGS[self.current_tuning]['note_names']
        self.strings_count = TUNINGS[self.current_tuning]['strings']

        self.all_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

        self.init_ui()
        self.load_background()

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

    def _show_error(self, message):
        """Показывает ошибку в интерфейсе"""

        def _update_ui():
            self._error_message = message
            if hasattr(self, '_hint_label'):
                self._hint_label.text = f"❌ {message}"
                self._hint_label.opacity = 1
                self._hint_label.text_color = [0.8, 0.2, 0.2, 1]
            logger.error(f"❌ {message}")

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _clear_error(self):
        """Очищает сообщение об ошибке"""

        def _update_ui():
            self._error_message = ""
            if hasattr(self, '_hint_label'):
                self._hint_label.text = ""
                self._hint_label.opacity = 0
                self._hint_label.text_color = [1, 1, 1, 0.5]

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _show_attempt(self, attempt_text):
        """Показывает текущую попытку в интерфейсе"""

        def _update_ui():
            if hasattr(self, '_hint_label') and not self._error_message:
                self._hint_label.text = f"🔄 {attempt_text}"
                self._hint_label.opacity = 1
                self._hint_label.text_color = [0.46, 0.70, 0.71, 1]

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _init_audio(self, dt):
        """Инициализация аудио - МАКСИМАЛЬНОЕ КОЛИЧЕСТВО ПОПЫТОК"""
        self._attempts = []

        if IS_ANDROID:
            # ============ ANDROID ============
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.RECORD_AUDIO])
                logger.info("✅ Запрошено разрешение RECORD_AUDIO")
            except Exception as e:
                self._show_error(f"Ошибка разрешений Android: {str(e)[:100]}")
                return

            if HAS_AUDIO_RECORDER:
                try:
                    self._audio_recorder = get_audio_recorder()
                    self._audio_backend = 'android_jni'
                    logger.info("✅ Android JNI AudioRecord готов")
                    self._show_attempt("Android AudioRecord готов")
                    return
                except Exception as e:
                    self._show_error(f"JNI AudioRecord: {str(e)[:100]}")
                    return

            self._show_error("Аудио не доступно на Android. Проверьте разрешения.")
            self._audio_backend = 'none'

        else:
            # ============ WINDOWS / MACOS / LINUX ============
            logger.info("=" * 60)
            logger.info("🔍 НАЧАЛО ПОИСКА МИКРОФОНА (Windows)")
            logger.info("=" * 60)

            # ===== ПОПЫТКА 1: SOUNDDEVICE с WASAPI =====
            if HAS_SOUNDDEVICE:
                try:
                    import sounddevice as sd
                    self._show_attempt("Попытка 1: sounddevice (WASAPI)...")
                    logger.info("🔹 Попытка 1: sounddevice (WASAPI)...")

                    devices = sd.query_devices()
                    input_devices = []

                    for i, device in enumerate(devices):
                        if device['max_input_channels'] > 0:
                            name = device['name']
                            input_devices.append({'index': i, 'name': name})
                            logger.info(f"   Устройство {i}: {name}")

                    if input_devices:
                        # Ищем WASAPI или микрофон
                        selected = None
                        for dev in input_devices:
                            if 'wasapi' in dev['name'].lower() or 'loopback' in dev['name'].lower():
                                selected = dev
                                logger.info(f"   ✅ Найдено WASAPI: {dev['name']}")
                                break

                        if selected is None:
                            for dev in input_devices:
                                if 'mic' in dev['name'].lower() or 'микрофон' in dev['name'].lower():
                                    selected = dev
                                    logger.info(f"   ✅ Найдено устройство с микрофоном: {dev['name']}")
                                    break

                        if selected is None:
                            selected = input_devices[0]
                            logger.info(f"   ✅ Используем первое устройство: {selected['name']}")

                        self._audio_backend = 'sounddevice'
                        logger.info(f"✅ sounddevice выбран: {selected['name']}")
                        self._show_attempt(f"sounddevice OK: {selected['name'][:30]}")
                        return
                    else:
                        logger.warning("⚠️ sounddevice: нет устройств ввода")
                        self._attempts.append("sounddevice: устройства ввода не найдены")

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ sounddevice ошибка: {error_msg}")
                    self._attempts.append(f"sounddevice: {error_msg[:100]}")

            # ===== ПОПЫТКА 2: SOUNDDEVICE с MME (без WASAPI) =====
            if HAS_SOUNDDEVICE:
                try:
                    import sounddevice as sd
                    self._show_attempt("Попытка 2: sounddevice (MME)...")
                    logger.info("🔹 Попытка 2: sounddevice (MME)...")

                    # Пробуем с host_api='MME'
                    devices = sd.query_devices()
                    input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]

                    if input_devices:
                        # Пробуем разные частоты
                        for rate in [48000, 44100, 22050, 16000]:
                            try:
                                test_stream = sd.InputStream(
                                    device=input_devices[0],
                                    samplerate=rate,
                                    channels=1,
                                    blocksize=CHUNK_SIZE,
                                    dtype='float32',
                                    latency='high'
                                )
                                test_stream.start()
                                test_stream.stop()
                                test_stream.close()

                                self._audio_backend = 'sounddevice_mme'
                                logger.info(f"✅ sounddevice (MME) работает с частотой {rate}Hz")
                                self._show_attempt(f"sounddevice MME OK ({rate}Hz)")
                                return
                            except:
                                continue
                    else:
                        logger.warning("⚠️ sounddevice MME: нет устройств ввода")
                        self._attempts.append("sounddevice MME: устройства ввода не найдены")

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ sounddevice MME ошибка: {error_msg}")
                    self._attempts.append(f"sounddevice MME: {error_msg[:100]}")

            # ===== ПОПЫТКА 3: PYAUDIO с разными форматами =====
            if HAS_PYAUDIO:
                try:
                    import pyaudio
                    self._show_attempt("Попытка 3: PyAudio...")
                    logger.info("🔹 Попытка 3: PyAudio...")

                    p = pyaudio.PyAudio()
                    input_devices = []

                    for i in range(p.get_device_count()):
                        info = p.get_device_info_by_index(i)
                        if info.get('maxInputChannels', 0) > 0:
                            input_devices.append({
                                'index': i,
                                'name': info.get('name', 'Unknown'),
                                'channels': info.get('maxInputChannels', 0)
                            })
                            logger.info(f"   Устройство {i}: {info.get('name')}")

                    p.terminate()

                    if input_devices:
                        # Пробуем разные форматы и частоты
                        formats = [
                            (pyaudio.paInt16, 'paInt16'),
                            (pyaudio.paInt32, 'paInt32'),
                            (pyaudio.paFloat32, 'paFloat32'),
                        ]
                        rates = [48000, 44100, 22050, 16000, 11025, 8000]

                        for fmt, fmt_name in formats:
                            for rate in rates:
                                try:
                                    p = pyaudio.PyAudio()
                                    test_stream = p.open(
                                        format=fmt,
                                        channels=1,
                                        rate=rate,
                                        input=True,
                                        input_device_index=input_devices[0]['index'],
                                        frames_per_buffer=CHUNK_SIZE,
                                        start=False
                                    )
                                    test_stream.start_stream()
                                    test_stream.stop_stream()
                                    test_stream.close()
                                    p.terminate()

                                    self._audio_backend = 'pyaudio'
                                    logger.info(f"✅ PyAudio работает: {fmt_name}, {rate}Hz")
                                    self._show_attempt(f"PyAudio OK ({fmt_name}, {rate}Hz)")
                                    return
                                except:
                                    try:
                                        p.terminate()
                                    except:
                                        pass
                                    continue
                    else:
                        logger.warning("⚠️ PyAudio: нет устройств ввода")
                        self._attempts.append("PyAudio: устройства ввода не найдены")

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ PyAudio ошибка: {error_msg}")
                    self._attempts.append(f"PyAudio: {error_msg[:100]}")

            # ===== ПОПЫТКА 4: PYAUDIO с другим устройством =====
            if HAS_PYAUDIO:
                try:
                    import pyaudio
                    self._show_attempt("Попытка 4: PyAudio (другие устройства)...")
                    logger.info("🔹 Попытка 4: PyAudio (другие устройства)...")

                    p = pyaudio.PyAudio()
                    input_devices = []

                    for i in range(p.get_device_count()):
                        info = p.get_device_info_by_index(i)
                        if info.get('maxInputChannels', 0) > 0:
                            input_devices.append({
                                'index': i,
                                'name': info.get('name', 'Unknown')
                            })

                    p.terminate()

                    # Пробуем каждое устройство
                    for dev in input_devices:
                        try:
                            p = pyaudio.PyAudio()
                            test_stream = p.open(
                                format=pyaudio.paInt16,
                                channels=1,
                                rate=44100,
                                input=True,
                                input_device_index=dev['index'],
                                frames_per_buffer=CHUNK_SIZE,
                                start=False
                            )
                            test_stream.start_stream()
                            test_stream.stop_stream()
                            test_stream.close()
                            p.terminate()

                            self._audio_backend = 'pyaudio'
                            logger.info(f"✅ PyAudio работает с устройством: {dev['name']}")
                            self._show_attempt(f"PyAudio OK: {dev['name'][:30]}")
                            return
                        except:
                            try:
                                p.terminate()
                            except:
                                pass
                            continue

                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ PyAudio (другие) ошибка: {error_msg}")
                    self._attempts.append(f"PyAudio (другие): {error_msg[:100]}")

            # ===== ВСЕ ПОПЫТКИ НЕ УДАЛИСЬ =====
            logger.error("=" * 60)
            logger.error("❌ ВСЕ ПОПЫТКИ НЕ УДАЛИСЬ")
            logger.error("=" * 60)

            # Формируем подробное сообщение об ошибке
            error_lines = []
            error_lines.append("Не удалось найти рабочий микрофон.")
            error_lines.append("")
            error_lines.append("Проверьте:")
            error_lines.append("1. Подключен ли микрофон к компьютеру")
            error_lines.append("2. Разрешён ли доступ к микрофону в Windows Settings")
            error_lines.append("3. Закрыты ли другие программы (Discord, Zoom, Skype)")
            error_lines.append("")
            error_lines.append("Попытки:")
            for i, attempt in enumerate(self._attempts[:5], 1):
                error_lines.append(f"  {i}. {attempt}")

            if not self._attempts:
                error_lines.append("  - Нет попыток (возможно, библиотеки не установлены)")

            error_lines.append("")
            error_lines.append("Установите sounddevice: pip install sounddevice numpy")

            full_error = "\n".join(error_lines)
            self._show_error(full_error)
            self._audio_backend = 'none'

    def _start_audio_thread(self):
        """Запускает поток захвата аудио"""
        if self._running:
            return

        if self._audio_backend == 'none':
            self._show_error("Аудио не инициализировано")
            return

        self._running = True
        self._clear_error()

        if self._audio_backend == 'android_jni':
            if self._audio_recorder:
                try:
                    self._audio_recorder.start_recording(
                        callback=self._on_audio_data,
                        sample_rate=SAMPLE_RATE,
                        chunk_size=CHUNK_SIZE
                    )
                    logger.info("🎤 Android JNI AudioRecord запущен")
                except Exception as e:
                    self._show_error(f"JNI AudioRecord: {str(e)[:100]}")
                    self._running = False
            else:
                self._show_error("JNI AudioRecord не инициализирован")
                self._running = False

        elif self._audio_backend == 'sounddevice' or self._audio_backend == 'sounddevice_mme':
            self._audio_thread = threading.Thread(target=self._audio_loop_sounddevice)
            self._audio_thread.daemon = True
            self._audio_thread.start()
            logger.info("🎤 sounddevice поток запущен")

        elif self._audio_backend == 'pyaudio':
            self._audio_thread = threading.Thread(target=self._audio_loop_pyaudio)
            self._audio_thread.daemon = True
            self._audio_thread.start()
            logger.info("🎤 pyaudio поток запущен")
        else:
            self._show_error(f"Неизвестный бэкенд: {self._audio_backend}")
            self._running = False

    def _on_audio_data(self, data):
        """Callback от Android AudioRecord"""
        if not self.is_listening or not self._running:
            return

        if data:
            freq = detect_pitch(data, SAMPLE_RATE)
            if freq > 0:
                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))

    def _audio_loop_sounddevice(self):
        """Захват через sounddevice"""
        try:
            import sounddevice as sd
            import numpy as np

            logger.info("🔍 sounddevice: поиск устройств...")

            devices = sd.query_devices()
            input_devices = []

            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels']
                    })
                    logger.info(f"   Устройство {i}: {device['name']}")

            if not input_devices:
                self._show_error("sounddevice: нет устройств ввода")
                self._running = False
                return

            # Выбираем устройство
            selected_dev = None

            # Ищем с микрофоном
            for dev in input_devices:
                name_lower = dev['name'].lower()
                if 'mic' in name_lower or 'микрофон' in name_lower:
                    selected_dev = dev
                    logger.info(f"✅ Выбрано устройство с микрофоном: {dev['name']}")
                    break

            if selected_dev is None:
                selected_dev = input_devices[0]
                logger.info(f"✅ Используем устройство по умолчанию: {selected_dev['name']}")

            device_index = selected_dev['index']
            device_name = selected_dev['name']

            # Пробуем разные частоты
            rates = [48000, 44100, 22050, 16000]
            selected_rate = 44100

            for rate in rates:
                try:
                    test_stream = sd.InputStream(
                        device=device_index,
                        samplerate=rate,
                        channels=1,
                        blocksize=CHUNK_SIZE,
                        dtype='float32',
                        latency='high'
                    )
                    test_stream.start()
                    test_stream.stop()
                    test_stream.close()
                    selected_rate = rate
                    logger.info(f"✅ Устройство работает с частотой {rate}Hz")
                    break
                except:
                    continue

            def callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Статус: {status}")

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
                    logger.error(f"Ошибка обработки: {e}")

            self._sounddevice_stream = sd.InputStream(
                device=device_index,
                samplerate=selected_rate,
                channels=1,
                callback=callback,
                blocksize=CHUNK_SIZE,
                dtype='float32',
                latency='high'
            )

            self._sounddevice_stream.start()
            logger.info(f"✅ sounddevice захват запущен ({device_name}, {selected_rate}Hz)")

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
        """Захват через pyaudio"""
        try:
            import pyaudio

            self._pyaudio = pyaudio.PyAudio()

            input_devices = []
            for i in range(self._pyaudio.get_device_count()):
                info = self._pyaudio.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    input_devices.append({
                        'index': i,
                        'name': info.get('name', 'Unknown')
                    })
                    logger.info(f"🎤 Найдено устройство: {info.get('name')}")

            if not input_devices:
                self._show_error("pyaudio: нет устройств ввода")
                self._running = False
                return

            # Выбираем устройство с микрофоном
            selected_dev = None
            for dev in input_devices:
                name_lower = dev['name'].lower()
                if 'mic' in name_lower or 'микрофон' in name_lower:
                    selected_dev = dev
                    logger.info(f"✅ Выбрано устройство: {dev['name']}")
                    break

            if selected_dev is None:
                selected_dev = input_devices[0]
                logger.info(f"✅ Используем устройство по умолчанию: {selected_dev['name']}")

            # Пробуем разные форматы и частоты
            formats = [
                (pyaudio.paInt16, 'paInt16'),
                (pyaudio.paInt32, 'paInt32'),
                (pyaudio.paFloat32, 'paFloat32'),
            ]
            rates = [48000, 44100, 22050, 16000, 8000]

            stream = None
            selected_format = None
            selected_rate = None

            for fmt, fmt_name in formats:
                for rate in rates:
                    try:
                        test_stream = self._pyaudio.open(
                            format=fmt,
                            channels=1,
                            rate=rate,
                            input=True,
                            input_device_index=selected_dev['index'],
                            frames_per_buffer=CHUNK_SIZE,
                            start=False
                        )
                        test_stream.start_stream()
                        test_stream.stop_stream()
                        test_stream.close()

                        selected_format = fmt
                        selected_rate = rate
                        logger.info(f"✅ PyAudio работает: {fmt_name}, {rate}Hz")
                        break
                    except:
                        continue
                if selected_format is not None:
                    break

            if selected_format is None:
                self._show_error("pyaudio: не удалось открыть поток ни с одним параметром")
                self._running = False
                return

            stream = self._pyaudio.open(
                format=selected_format,
                channels=1,
                rate=selected_rate,
                input=True,
                input_device_index=selected_dev['index'],
                frames_per_buffer=CHUNK_SIZE,
                start=True
            )

            self._pyaudio_stream = stream
            logger.info(f"✅ pyaudio захват запущен ({selected_dev['name']}, {selected_rate}Hz)")

            while self._running:
                try:
                    if stream.is_active():
                        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                        if data:
                            freq = detect_pitch(data, selected_rate)
                            if freq > 0:
                                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))
                except IOError as e:
                    if e.errno == pyaudio.paInputOverflowed:
                        continue
                    else:
                        self._show_error(f"pyaudio: {str(e)[:100]}")
                        break
                except Exception as e:
                    self._show_error(f"pyaudio: {str(e)[:100]}")
                    break

            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            if self._pyaudio:
                try:
                    self._pyaudio.terminate()
                except:
                    pass
                self._pyaudio = None

        except Exception as e:
            self._show_error(f"pyaudio: {str(e)[:150]}")
            self._running = False

    def _stop_audio_thread(self):
        """Останавливает аудио поток"""
        self._running = False

        if self._audio_backend == 'android_jni' and self._audio_recorder:
            try:
                self._audio_recorder.stop_recording()
                logger.info("⏹ JNI AudioRecord остановлен")
            except:
                pass

        if self._audio_backend in ['sounddevice', 'sounddevice_mme'] and self._sounddevice_stream:
            try:
                self._sounddevice_stream.stop()
                self._sounddevice_stream.close()
                self._sounddevice_stream = None
                logger.info("⏹ sounddevice остановлен")
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
            logger.info("⏹ pyaudio остановлен")

        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=1)
        self._audio_thread = None

        self._clear_error()
        logger.info("⏹ Аудио поток остановлен")

    def _process_frequency(self, freq):
        """Обрабатывает обнаруженную частоту"""
        if not self.is_listening:
            return

        note, note_freq, diff = freq_to_note(freq)

        if note:
            cents = cents_deviation(freq, note_freq)
            deviation = cents / 50

            if hasattr(self, 'tuner_dial'):
                self.tuner_dial.deviation = deviation
                self.tuner_dial.note_name = note
                self.tuner_dial.note_frequency = note_freq

            if hasattr(self, 'note_scale'):
                self.note_scale.set_current_note(note)
                self.note_scale.set_highlighted(self.tuning_note_names)

            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.1f} Hz"

            if hasattr(self, 'note_label'):
                is_in_tuning = note in self.tuning_note_names
                self.note_label.set_note(note, is_in_tuning)

    def _show_tuning_dialog(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        categories = {
            '🎸 Гитара': ['standard_6', 'drop_d', 'open_g'],
            '🎸 Бас': ['bass_4'],
            '🎵 Укулеле': ['ukulele'],
        }

        for category, tuning_ids in categories.items():
            cat_label = MDLabel(
                text=category,
                font_size=sp(14),
                bold=True,
                size_hint_y=None,
                height=dp(32),
                theme_text_color="Custom",
                text_color=[0.46, 0.70, 0.71, 1]
            )
            content.add_widget(cat_label)

            for tuning_id in tuning_ids:
                if tuning_id in TUNINGS:
                    tuning = TUNINGS[tuning_id]
                    is_active = tuning_id == self.current_tuning
                    btn = MDRaisedButton(
                        text=tuning['name'],
                        size_hint=(1, None),
                        height=dp(44),
                        md_bg_color=[0.46, 0.70, 0.71, 1] if is_active else [0.2, 0.2, 0.2, 0.6],
                        text_color=[1, 1, 1, 1],
                        on_release=lambda x, tid=tuning_id: self._select_tuning(tid)
                    )
                    content.add_widget(btn)

        self.tuning_dialog = MDDialog(
            title="Выберите строй",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="Закрыть",
                    on_release=lambda x: self.tuning_dialog.dismiss()
                )
            ]
        )
        self.tuning_dialog.open()

    def _select_tuning(self, tuning_id):
        if self.tuning_dialog:
            self.tuning_dialog.dismiss()

        if tuning_id == self.current_tuning:
            return

        self.current_tuning = tuning_id
        tuning = TUNINGS[tuning_id]
        self.tuning_notes = tuning['notes']
        self.tuning_freqs = tuning['freqs']
        self.tuning_note_names = tuning['note_names']
        self.strings_count = tuning['strings']

        if hasattr(self, 'tuning_name_label'):
            self.tuning_name_label.text = tuning['name']

        if hasattr(self, 'note_scale'):
            self.note_scale.set_highlighted(self.tuning_note_names)

        if hasattr(self, 'tuner_dial'):
            self.tuner_dial.deviation = 0
            self.tuner_dial.note_name = '--'
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "--"
        if hasattr(self, 'note_label'):
            self.note_label.text = "--"

        notify.success(f"Строй: {tuning['name']}")
        logger.info(f"🎸 Выбран строй: {tuning['name']}")

    def init_ui(self):
        """Инициализирует UI"""

        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        content_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(6),
            size_hint=(1, None),
            adaptive_height=True
        )

        title_label = MDLabel(
            text="ТЮНЕР",
            font_size=sp(18),
            halign="center",
            size_hint_y=None,
            height=dp(32),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            bold=True
        )
        content.add_widget(title_label)

        scale_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(50),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )
        self.note_scale = NoteScale()
        self.note_scale.set_highlighted(self.tuning_note_names)
        scale_container.add_widget(self.note_scale)
        content.add_widget(scale_container)

        tuning_info = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(24),
            spacing=dp(8),
            padding=[dp(8), dp(2), dp(8), dp(2)]
        )

        self.tuning_name_label = MDLabel(
            text=TUNINGS[self.current_tuning]['name'],
            font_size=sp(11),
            halign="center",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4]
        )
        tuning_info.add_widget(self.tuning_name_label)
        content.add_widget(tuning_info)

        dial_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(180),
            padding=[dp(32), dp(4), dp(32), dp(4)]
        )
        self.tuner_dial = TunerDial()
        dial_container.add_widget(self.tuner_dial)
        content.add_widget(dial_container)

        info_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(16),
            padding=[dp(16), dp(4), dp(16), dp(4)]
        )

        self.freq_label = MDLabel(
            text="--",
            font_size=sp(14),
            halign="center",
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        self.note_label = NoteLabel(
            text="--",
            font_size=sp(24),
            halign="center",
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        info_container.add_widget(self.freq_label)
        info_container.add_widget(self.note_label)
        content.add_widget(info_container)

        menu_card = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(4), dp(4), dp(4), dp(4)],
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            line_color=[1, 1, 1, 0.15],
            line_width=0.8,
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

        divider1 = MDBoxLayout(
            size_hint_x=None,
            width=dp(1),
            md_bg_color=[1, 1, 1, 0.1]
        )

        self.tuning_btn = MDIconButton(
            icon="tune",
            size_hint=(1, 1),
            theme_icon_color="Custom",
            icon_color=[0.9, 0.7, 0.2, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self._show_tuning_dialog()
        )

        divider2 = MDBoxLayout(
            size_hint_x=None,
            width=dp(1),
            md_bg_color=[1, 1, 1, 0.1]
        )

        self.reset_btn = MDIconButton(
            icon="refresh",
            size_hint=(1, 1),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.reset_tuner
        )

        menu_card.add_widget(self.play_btn)
        menu_card.add_widget(divider1)
        menu_card.add_widget(self.tuning_btn)
        menu_card.add_widget(divider2)
        menu_card.add_widget(self.reset_btn)

        content.add_widget(menu_card)

        # ============ ЛЕЙБЛ ДЛЯ ОШИБОК И ПОДСКАЗОК ============
        self._hint_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(30),
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
        """Включает/выключает тюнер"""
        if not self.is_listening:
            if self._audio_backend == 'none':
                self._show_error("Аудио не инициализировано. Проверьте настройки.")
                return

            self.is_listening = True
            self.play_btn.icon = "stop"
            self.play_btn.icon_color = [0.8, 0.3, 0.3, 1]
            self._start_audio_thread()
        else:
            self.is_listening = False
            self.play_btn.icon = "play"
            self.play_btn.icon_color = [0.46, 0.70, 0.71, 1]
            self._stop_audio_thread()

            if hasattr(self, 'tuner_dial'):
                self.tuner_dial.deviation = 0
                self.tuner_dial.note_name = '--'
            if hasattr(self, 'freq_label'):
                self.freq_label.text = "--"
            if hasattr(self, 'note_label'):
                self.note_label.text = "--"
            if hasattr(self, 'note_scale'):
                self.note_scale.set_current_note('--')

    def reset_tuner(self, instance):
        """Сброс тюнера"""
        if self.is_listening:
            self.toggle_tuner(None)

        if hasattr(self, 'tuner_dial'):
            self.tuner_dial.deviation = 0
            self.tuner_dial.note_name = '--'
        if hasattr(self, 'freq_label'):
            self.freq_label.text = "--"
        if hasattr(self, 'note_label'):
            self.note_label.text = "--"
        if hasattr(self, 'note_scale'):
            self.note_scale.set_current_note('--')

        self._clear_error()
        logger.info("🔄 Тюнер сброшен")

    def _show_temporary_hint(self, text, duration=1.5):
        def _update_ui():
            if hasattr(self, '_hint_label') and self._hint_label:
                if self._error_message:
                    return
                self._hint_label.text = text
                self._hint_label.opacity = 1
                self._hint_label.text_color = [1, 1, 1, 0.7]
                if hasattr(self, '_hint_timer') and self._hint_timer:
                    Clock.unschedule(self._hint_timer)
                self._hint_timer = Clock.schedule_once(lambda dt: self._hide_hint(), duration)

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def _hide_hint(self):
        def _update_ui():
            if hasattr(self, '_hint_label') and self._hint_label:
                if self._error_message:
                    return
                self._hint_label.text = ""
                self._hint_label.opacity = 0
                self._hint_label.text_color = [1, 1, 1, 0.5]
                if hasattr(self, '_hint_timer'):
                    self._hint_timer = None

        Clock.schedule_once(lambda dt: _update_ui(), 0)

    def on_enter(self):
        logger.info("Вход в экран тюнера")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Тюнер")
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