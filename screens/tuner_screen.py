# screens/tuner_screen.py
"""
Экран гитарного тюнера - с реальным определением частоты
Windows: sounddevice (с автоматическим выбором устройства)
Android: JNI AudioRecord
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
import random
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

# ============ ПОПЫТКА ИМПОРТА SOUNDDEVICE ============
try:
    import sounddevice as sd
    import numpy as np

    HAS_SOUNDDEVICE = True
    logger.info("✅ sounddevice загружен")
except ImportError:
    HAS_SOUNDDEVICE = False
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
    """Гитарный тюнер с реальным определением частоты"""

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
        self._audio_backend = 'emulation'
        self._audio_recorder = None
        self._sounddevice_stream = None
        self._checked_microphone = False

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

    def _check_microphone(self):
        """Проверяет, доступен ли микрофон на Windows"""
        if self._checked_microphone:
            return True

        if IS_ANDROID:
            self._checked_microphone = True
            return True

        try:
            import sounddevice as sd
            devices = sd.query_devices()
            input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]

            if not input_devices:
                logger.warning("⚠️ Микрофон не найден!")
                self._show_temporary_hint("Микрофон не найден!", 2.0)
                return False

            # Пробуем открыть тестовый поток
            try:
                test_stream = sd.InputStream(
                    samplerate=44100,
                    channels=1,
                    duration=0.1,
                    device=input_devices[0]
                )
                test_stream.start()
                test_stream.stop()
                test_stream.close()
                logger.info("✅ Микрофон доступен")
                self._checked_microphone = True
                return True
            except Exception as e:
                logger.warning(f"⚠️ Микрофон недоступен: {e}")
                self._show_temporary_hint("Микрофон недоступен!", 2.0)
                return False

        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки микрофона: {e}")
            return False

    def _init_audio(self, dt):
        """Инициализация аудио для всех платформ"""
        try:
            if IS_ANDROID:
                # ============ ANDROID ============
                try:
                    from android.permissions import request_permissions, Permission
                    request_permissions([Permission.RECORD_AUDIO])
                    logger.info("✅ Запрошено разрешение RECORD_AUDIO")
                except Exception as e:
                    logger.error(f"Ошибка запроса разрешений: {e}")

                if HAS_AUDIO_RECORDER:
                    try:
                        self._audio_recorder = get_audio_recorder()
                        self._audio_backend = 'android_jni'
                        logger.info("✅ Android JNI AudioRecord готов")
                        return
                    except Exception as e:
                        logger.error(f"❌ Ошибка JNI AudioRecord: {e}")

                logger.warning("⚠️ Аудио не доступно на Android, используем эмуляцию")
                self._audio_backend = 'emulation'

            else:
                # ============ WINDOWS / MACOS / LINUX ============
                if HAS_SOUNDDEVICE:
                    try:
                        import sounddevice as sd

                        # Проверяем наличие устройств ввода
                        devices = sd.query_devices()
                        input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]

                        if input_devices:
                            logger.info(f"🎤 Найдено устройств ввода: {len(input_devices)}")
                            for idx in input_devices:
                                logger.info(f"   - {devices[idx]['name']}")

                            self._audio_backend = 'sounddevice'
                            logger.info("✅ sounddevice загружен (Desktop)")
                            return
                        else:
                            logger.warning("⚠️ Нет устройств ввода! Проверьте подключение микрофона.")
                    except Exception as e:
                        logger.error(f"❌ Ошибка инициализации sounddevice: {e}")

                # Если sounddevice не работает - эмуляция
                logger.warning("⚠️ Аудио не доступно, используем эмуляцию")
                self._audio_backend = 'emulation'

        except Exception as e:
            logger.error(f"Ошибка инициализации аудио: {e}")
            self._audio_backend = 'emulation'

    def _start_audio_thread(self):
        """Запускает поток захвата аудио"""
        if self._running:
            return

        self._running = True

        if self._audio_backend == 'android_jni':
            if self._audio_recorder:
                self._audio_recorder.start_recording(
                    callback=self._on_audio_data,
                    sample_rate=SAMPLE_RATE,
                    chunk_size=CHUNK_SIZE
                )
                logger.info("🎤 Android JNI AudioRecord запущен")
            else:
                self._audio_loop_emulation()
        elif self._audio_backend == 'sounddevice':
            # Проверяем микрофон перед запуском
            if IS_WINDOWS and not self._check_microphone():
                self._show_temporary_hint("Микрофон не найден!", 2.0)
                self._running = False
                return

            self._audio_thread = threading.Thread(target=self._audio_loop_sounddevice)
            self._audio_thread.daemon = True
            self._audio_thread.start()
            logger.info("🎤 sounddevice поток запущен")
        else:
            self._audio_thread = threading.Thread(target=self._audio_loop_emulation)
            self._audio_thread.daemon = True
            self._audio_thread.start()
            logger.info("🎵 Эмуляция запущена")

    def _on_audio_data(self, data):
        """Callback от Android AudioRecord"""
        if not self.is_listening or not self._running:
            return

        if data:
            freq = detect_pitch(data, SAMPLE_RATE)
            if freq > 0:
                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))

    def _audio_loop_sounddevice(self):
        """Захват через sounddevice (Windows/Desktop) с умным выбором устройства"""
        try:
            import sounddevice as sd
            import numpy as np

            logger.info("🔍 Поиск аудио-устройств ввода...")

            # ============ ПОЛУЧАЕМ СПИСОК УСТРОЙСТВ ============
            devices = sd.query_devices()
            input_devices = []

            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rates': device.get('default_samplerate', 0)
                    })
                    logger.info(f"   Устройство {i}: {device['name']} (каналов: {device['max_input_channels']})")

            if not input_devices:
                logger.warning("⚠️ Нет устройств ввода! Проверьте подключение микрофона.")
                self._audio_loop_emulation()
                return

            # ============ ВЫБИРАЕМ ЛУЧШЕЕ УСТРОЙСТВО ============
            selected_device = None
            priority_keywords = ['microphone', 'mic', 'input', 'audio', 'usb', 'cable']

            # Сначала ищем по ключевым словам
            for dev in input_devices:
                name_lower = dev['name'].lower()
                for keyword in priority_keywords:
                    if keyword in name_lower:
                        if selected_device is None:
                            selected_device = dev
                        if keyword in ['microphone', 'mic']:
                            selected_device = dev
                            logger.info(f"✅ Найдено устройство с '{keyword}': {dev['name']}")
                            break
                if selected_device and 'microphone' in selected_device['name'].lower():
                    break

            # Если не нашли по ключевым словам - берем первое
            if selected_device is None:
                selected_device = input_devices[0]
                logger.info(f"✅ Используем устройство по умолчанию: {selected_device['name']}")

            device_index = selected_device['index']
            device_name = selected_device['name']
            max_channels = selected_device['channels']

            # ============ ОПРЕДЕЛЯЕМ ПОДДЕРЖИВАЕМУЮ ЧАСТОТУ ============
            sample_rates_to_try = [44100, 48000, 22050, 16000, 11025, 8000]
            selected_rate = None

            for rate in sample_rates_to_try:
                try:
                    sd.check_input_settings(
                        device=device_index,
                        samplerate=rate,
                        channels=min(1, max_channels)
                    )
                    selected_rate = rate
                    logger.info(f"✅ Устройство поддерживает {rate}Hz")
                    break
                except Exception as e:
                    logger.debug(f"   {rate}Hz не поддерживается: {e}")
                    continue

            if selected_rate is None:
                logger.warning("⚠️ Не удалось найти поддерживаемую частоту, используем 44100")
                selected_rate = 44100

            # ============ ОТКРЫВАЕМ ПОТОК ============
            logger.info(f"🎤 Открываем поток: {device_name}, {selected_rate}Hz, {min(1, max_channels)} канал(а)")

            def callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Статус звука: {status}")

                if not self._running or not self.is_listening:
                    return

                try:
                    if indata is None or len(indata) == 0:
                        return

                    if indata.shape[1] > 0:
                        audio_int16 = (indata[:, 0] * 32767).astype(np.int16)
                        data_bytes = audio_int16.tobytes()

                        if len(data_bytes) > 0:
                            freq = detect_pitch(data_bytes, selected_rate)
                            if freq > 0:
                                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))
                except Exception as e:
                    logger.error(f"Ошибка обработки аудио: {e}")

            # Создаем поток с правильными параметрами
            try:
                self._sounddevice_stream = sd.InputStream(
                    device=device_index,
                    samplerate=selected_rate,
                    channels=min(1, max_channels),
                    callback=callback,
                    blocksize=CHUNK_SIZE,
                    dtype='float32',
                    latency='low'
                )
            except Exception as e:
                logger.error(f"❌ Не удалось создать поток: {e}")
                try:
                    logger.info("🔄 Пробуем с устройством по умолчанию...")
                    self._sounddevice_stream = sd.InputStream(
                        samplerate=selected_rate,
                        channels=1,
                        callback=callback,
                        blocksize=CHUNK_SIZE,
                        dtype='float32'
                    )
                except Exception as e2:
                    logger.error(f"❌ Не удалось создать поток с устройством по умолчанию: {e2}")
                    self._audio_loop_emulation()
                    return

            self._sounddevice_stream.start()
            logger.info(f"✅ sounddevice поток запущен (устройство: {device_name})")

            # Ждем завершения
            while self._running:
                time.sleep(0.1)

            # Закрываем поток
            if self._sounddevice_stream:
                self._sounddevice_stream.stop()
                self._sounddevice_stream.close()
                self._sounddevice_stream = None

        except Exception as e:
            logger.error(f"❌ Ошибка sounddevice: {e}")
            logger.info("🔄 Переключаемся на эмуляцию...")
            self._audio_loop_emulation()

    def _audio_loop_emulation(self):
        """Эмуляция для тестирования"""
        logger.info("🎵 Эмуляция аудио")
        while self._running:
            if self.tuning_freqs:
                freq = random.choice(self.tuning_freqs)
                freq += (random.random() - 0.5) * 10
                Clock.schedule_once(lambda dt, f=freq: self._process_frequency(f))
            time.sleep(0.3)

    def _stop_audio_thread(self):
        """Останавливает аудио поток"""
        self._running = False

        if self._audio_backend == 'android_jni' and self._audio_recorder:
            self._audio_recorder.stop_recording()
            logger.info("⏹ JNI AudioRecord остановлен")

        if self._audio_backend == 'sounddevice' and self._sounddevice_stream:
            try:
                self._sounddevice_stream.stop()
                self._sounddevice_stream.close()
                self._sounddevice_stream = None
                logger.info("⏹ sounddevice остановлен")
            except:
                pass

        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=1)
        self._audio_thread = None

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

        self._hint_label = MDLabel(
            text="",
            font_size=sp(11),
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
        """Включает/выключает тюнер"""
        if not self.is_listening:
            # Проверяем микрофон перед запуском
            if self._audio_backend == 'sounddevice' and IS_WINDOWS:
                if not self._check_microphone():
                    return

            self.is_listening = True
            self.play_btn.icon = "stop"
            self.play_btn.icon_color = [0.8, 0.3, 0.3, 1]
            self._show_temporary_hint("Тюнер запущен")
            self._start_audio_thread()
        else:
            self.is_listening = False
            self.play_btn.icon = "play"
            self.play_btn.icon_color = [0.46, 0.70, 0.71, 1]
            self._show_temporary_hint("Тюнер остановлен")
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

        self._show_temporary_hint("Сброшено")
        logger.info("🔄 Тюнер сброшен")

    def _show_temporary_hint(self, text, duration=1.5):
        if hasattr(self, '_hint_label') and self._hint_label:
            self._hint_label.text = text
            self._hint_label.opacity = 1
            if hasattr(self, '_hint_timer') and self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._hide_hint(), duration)

    def _hide_hint(self):
        if hasattr(self, '_hint_label') and self._hint_label:
            self._hint_label.text = ""
            self._hint_label.opacity = 0
            if hasattr(self, '_hint_timer'):
                self._hint_timer = None

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