# screens/metronome_screen.py
"""
Экран гитарного метронома с полным набором настроек
Работает на Android через SDL2 Audio
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from io import BytesIO
import math
import array
import struct
import tempfile
import os
import random

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.slider import MDSlider
from kivymd.uix.dialog import MDDialog

from config.theme import theme
from config.logger_config import screen_logger
from screens.base_screen import BaseScreen

logger = screen_logger('Metronome')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


# ============ ФУНКЦИИ ДЛЯ РАБОТЫ НА ANDROID ============
def get_temp_path():
    """Возвращает безопасный путь для временных файлов на Android"""
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except:
            pass
    return tempfile.gettempdir()


# ============ ГЕНЕРАТОРЫ ЗВУКА ============
def generate_click_sound(frequency=1200, duration=0.05, sample_rate=44100, volume=0.8, waveform='sine'):
    """Генерирует звук с разными формами волны"""
    num_samples = int(sample_rate * duration)

    audio_data = array.array('h')
    for i in range(num_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 30)

        if waveform == 'sine':
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)
        elif waveform == 'square':
            value = int(32767 * volume * (1 if math.sin(2 * math.pi * frequency * t) > 0 else -1) * envelope)
        elif waveform == 'triangle':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            tri = 2 * abs(phase / math.pi - 1) - 1
            value = int(32767 * volume * tri * envelope)
        elif waveform == 'sawtooth':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            saw = 2 * (phase / (2 * math.pi)) - 1
            value = int(32767 * volume * saw * envelope)
        else:
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)

        audio_data.append(value)

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
            f.write(struct.pack('<I', sample_rate))
            f.write(struct.pack('<I', sample_rate * 2))
            f.write(struct.pack('<H', 2))
            f.write(struct.pack('<H', 16))
            f.write(b'data')
            f.write(struct.pack('<I', len(audio_data) * 2))
            audio_data.tofile(f)

    sound = SoundLoader.load(tmp_path)
    try:
        os.unlink(tmp_path)
    except:
        pass
    return sound


def generate_accent_sound(frequency=1800, duration=0.08, sample_rate=44100, volume=1.0, waveform='sine'):
    """Генерирует акцентный звук с разными формами волны"""
    num_samples = int(sample_rate * duration)

    audio_data = array.array('h')
    for i in range(num_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 25)

        if waveform == 'sine':
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)
        elif waveform == 'square':
            value = int(32767 * volume * (1 if math.sin(2 * math.pi * frequency * t) > 0 else -1) * envelope)
        elif waveform == 'triangle':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            tri = 2 * abs(phase / math.pi - 1) - 1
            value = int(32767 * volume * tri * envelope)
        elif waveform == 'sawtooth':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            saw = 2 * (phase / (2 * math.pi)) - 1
            value = int(32767 * volume * saw * envelope)
        else:
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)

        audio_data.append(value)

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
            f.write(struct.pack('<I', sample_rate))
            f.write(struct.pack('<I', sample_rate * 2))
            f.write(struct.pack('<H', 2))
            f.write(struct.pack('<H', 16))
            f.write(b'data')
            f.write(struct.pack('<I', len(audio_data) * 2))
            audio_data.tofile(f)

    sound = SoundLoader.load(tmp_path)
    try:
        os.unlink(tmp_path)
    except:
        pass
    return sound


def generate_subdivision_sound(frequency=800, duration=0.03, sample_rate=44100, volume=0.5, waveform='sine'):
    """Генерирует звук для деления длительностей"""
    num_samples = int(sample_rate * duration)

    audio_data = array.array('h')
    for i in range(num_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 40)

        if waveform == 'sine':
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)
        elif waveform == 'square':
            value = int(32767 * volume * (1 if math.sin(2 * math.pi * frequency * t) > 0 else -1) * envelope)
        elif waveform == 'triangle':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            tri = 2 * abs(phase / math.pi - 1) - 1
            value = int(32767 * volume * tri * envelope)
        elif waveform == 'sawtooth':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            saw = 2 * (phase / (2 * math.pi)) - 1
            value = int(32767 * volume * saw * envelope)
        else:
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)

        audio_data.append(value)

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
            f.write(struct.pack('<I', sample_rate))
            f.write(struct.pack('<I', sample_rate * 2))
            f.write(struct.pack('<H', 2))
            f.write(struct.pack('<H', 16))
            f.write(b'data')
            f.write(struct.pack('<I', len(audio_data) * 2))
            audio_data.tofile(f)

    sound = SoundLoader.load(tmp_path)
    try:
        os.unlink(tmp_path)
    except:
        pass
    return sound


# ============ РЕАЛИСТИЧНЫЙ МЕХАНИЧЕСКИЙ ЗВУК ============
def generate_mechanical_click(is_accent=False, sample_rate=44100, volume=0.8):
    """Генерирует реалистичный звук механического метронома"""
    if is_accent:
        duration = 0.055
        vol = volume * 1.0
        base_freq = 1600
        decay_factor = 22
        noise_amount = 0.15
    else:
        duration = 0.035
        vol = volume * 0.75
        base_freq = 1200
        decay_factor = 30
        noise_amount = 0.25

    num_samples = int(sample_rate * duration)
    audio_data = array.array('h')

    noise_buffer = [random.uniform(-1, 1) for _ in range(num_samples)]

    for i in range(num_samples):
        t = i / sample_rate

        attack_time = 0.001
        if t < attack_time:
            envelope = t / attack_time
        else:
            envelope = math.exp(-(t - attack_time) * decay_factor)

        if t > 0.02:
            envelope *= 0.8

        freq_mult = 1.0 if not is_accent else 1.3

        tone = 0
        harmonic_count = 4 if is_accent else 3
        for h in range(1, harmonic_count + 1):
            freq = base_freq * h * freq_mult
            amp = 1.0 / (h * 1.2)
            tone += math.sin(2 * math.pi * freq * t) * amp
        tone /= harmonic_count

        low_freq = base_freq * 0.4 * freq_mult
        low_tone = math.sin(2 * math.pi * low_freq * t) * 0.3

        noise_idx = i
        if noise_idx < len(noise_buffer):
            noise = noise_buffer[noise_idx] * noise_amount * envelope * 0.6
        else:
            noise = 0

        click = 0
        if t < 0.0015:
            click = 0.3 * (1 - t / 0.0015)

        combined = (tone * 0.5 + low_tone * 0.2 + noise + click) * envelope * vol
        combined = max(-1.0, min(1.0, combined))
        value = int(32767 * combined)
        audio_data.append(value)

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
            f.write(struct.pack('<I', sample_rate))
            f.write(struct.pack('<I', sample_rate * 2))
            f.write(struct.pack('<H', 2))
            f.write(struct.pack('<H', 16))
            f.write(b'data')
            f.write(struct.pack('<I', len(audio_data) * 2))
            audio_data.tofile(f)

    sound = SoundLoader.load(tmp_path)
    try:
        os.unlink(tmp_path)
    except:
        pass
    return sound


# ============ ВЕРТИКАЛЬНЫЙ СЛАЙДЕР ============
class VerticalSlider(MDBoxLayout):
    value = NumericProperty(60)
    min_value = NumericProperty(30)
    max_value = NumericProperty(240)
    step = NumericProperty(1)

    def __init__(self, label_text="BPM", min_value=30, max_value=240, initial=60, step=1, **kwargs):
        super().__init__(**kwargs)
        self.label_text = label_text
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial
        self.step = step

        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.width = dp(80)
        self.height = dp(280)
        self.spacing = dp(8)
        self.padding = [dp(8), dp(8), dp(8), dp(8)]

        slider_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(20), dp(8), dp(20), dp(8)]
        )

        self.value_label = MDLabel(
            text=str(int(initial)),
            font_size=sp(24),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        self.slider = MDSlider(
            min=min_value,
            max=max_value,
            value=initial,
            step=step,
            size_hint=(None, 1),
            width=dp(20),
            orientation='vertical',
            pos_hint={'center_x': 0.5},
            hint=False
        )

        bi_color = [0.46, 0.70, 0.71, 1]
        self.slider.thumb_color_active = bi_color
        self.slider.thumb_color_inactive = bi_color
        self.slider.track_color_active = [0.46, 0.70, 0.71, 0.6]
        self.slider.track_color_inactive = [1, 1, 1, 0.2]

        self.slider.bind(value=self._on_value_change)

        self.label = MDLabel(
            text=label_text,
            font_size=sp(11),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        slider_container.add_widget(self.value_label)
        slider_container.add_widget(self.slider)

        self.add_widget(slider_container)
        self.add_widget(self.label)

    def _on_value_change(self, instance, value):
        rounded = round(value / self.step) * self.step
        if rounded != value:
            self.slider.value = rounded
            return
        self.value = rounded
        self.value_label.text = str(int(rounded))

    def get_value(self):
        return self.value


# ============ ГОРИЗОНТАЛЬНЫЙ СЛАЙДЕР ============
class HorizontalSlider(MDBoxLayout):
    value = NumericProperty(50)
    min_value = NumericProperty(0)
    max_value = NumericProperty(100)
    step = NumericProperty(1)

    def __init__(self, label_text="", min_value=0, max_value=100, initial=50, step=1, **kwargs):
        super().__init__(**kwargs)
        self.label_text = label_text
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(40)
        self.spacing = dp(12)
        self.padding = [dp(4), dp(4), dp(4), dp(4)]

        self.label = MDLabel(
            text=label_text,
            font_size=sp(12),
            halign="left",
            valign="middle",
            size_hint_x=None,
            width=dp(60),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8]
        )

        self.value_label = MDLabel(
            text=str(initial),
            font_size=sp(12),
            halign="center",
            valign="middle",
            size_hint_x=None,
            width=dp(36),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        self.slider = MDSlider(
            min=min_value,
            max=max_value,
            value=initial,
            step=step,
            size_hint_x=1,
            height=dp(20),
            hint=False
        )

        bi_color = [0.46, 0.70, 0.71, 1]
        self.slider.thumb_color_active = bi_color
        self.slider.thumb_color_inactive = bi_color
        self.slider.track_color_active = [0.46, 0.70, 0.71, 0.6]
        self.slider.track_color_inactive = [1, 1, 1, 0.2]

        self.slider.bind(value=self._on_slider_change)

        self.add_widget(self.label)
        self.add_widget(self.slider)
        self.add_widget(self.value_label)

        self.value = initial

    def _on_slider_change(self, instance, value):
        rounded = round(value / self.step) * self.step
        if rounded != value:
            self.slider.value = rounded
            return
        self.value = rounded
        self.value_label.text = str(int(rounded))
        self.on_value(self, self.value)

    def get_value(self):
        return self.value

    def on_value(self, instance, value):
        """Событие изменения значения - переопределяется в потомках"""
        pass


# ============ КАСТОМНЫЙ ПЕРЕКЛЮЧАТЕЛЬ ============
class CustomSwitch(MDBoxLayout):
    active = NumericProperty(0)

    def __init__(self, active=True, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (dp(50), dp(30))
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = dp(0)

        self.bg = MDCard(
            size_hint=(1, 1),
            radius=[dp(15)] * 4,
            md_bg_color=[0.3, 0.3, 0.3, 0.6],
            elevation=0
        )

        self.thumb = MDCard(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            radius=[dp(12)] * 4,
            md_bg_color=[0.8, 0.8, 0.8, 0.9],
            elevation=1,
            pos_hint={'center_y': 0.5},
            x=dp(2)
        )

        self.bg.add_widget(self.thumb)
        self.add_widget(self.bg)

        self.active = 1 if active else 0
        self._update_state()

        self.bg.bind(on_release=self.toggle)

    def toggle(self, instance=None):
        self.active = 1 - self.active
        self._update_state()
        self.on_active(self, self.active)

    def _update_state(self):
        if self.active:
            self.bg.md_bg_color = [0.46, 0.70, 0.71, 0.8]
            self.thumb.md_bg_color = [0.46, 0.70, 0.71, 1]
            anim = Animation(x=dp(24), duration=0.15, t='out_quad')
            anim.start(self.thumb)
        else:
            self.bg.md_bg_color = [0.3, 0.3, 0.3, 0.6]
            self.thumb.md_bg_color = [0.8, 0.8, 0.8, 0.9]
            anim = Animation(x=dp(2), duration=0.15, t='out_quad')
            anim.start(self.thumb)

    def on_active(self, instance, value):
        """Событие изменения состояния - переопределяется в потомках"""
        pass


# ============ ОСНОВНОЙ ЭКРАН МЕТРОНОМА ============
class MetronomeScreen(BaseScreen):
    # 5 ТЕМБРОВ: механический + 4 синтезированных
    SOUND_TONES = {
        'mechanical': {
            'name': '🔧 Механический',
            'type': 'mechanical',
            'description': 'Реалистичный звук механического метронома'
        },
        'electronic': {
            'name': '⚡ Электронный',
            'type': 'synthetic',
            'waveform': 'sine',
            'freq': 1200,
            'accent_freq': 1800,
            'description': 'Чистый синтезированный звук'
        },
        'wood': {
            'name': '🪵 Деревянный',
            'type': 'synthetic',
            'waveform': 'triangle',
            'freq': 800,
            'accent_freq': 1200,
            'description': 'Мягкий деревянный стук'
        },
        'click': {
            'name': '👆 Щелчок',
            'type': 'synthetic',
            'waveform': 'square',
            'freq': 600,
            'accent_freq': 900,
            'description': 'Резкий щелчок'
        },
        'beep': {
            'name': '📢 Пищалка',
            'type': 'synthetic',
            'waveform': 'sawtooth',
            'freq': 1500,
            'accent_freq': 2200,
            'description': 'Яркий электронный сигнал'
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'metronome'
        self.bg_image = None

        self.bpm = 120
        self.beats_per_measure = 4
        self.subdivision = 'none'
        self.sound_tone = 'mechanical'
        self.volume = 0.8
        self.accent_volume = 1.0
        self.is_accent_enabled = True

        self.is_running = False
        self.tick_count = 0
        self.subdivision_count = 0

        self.click_sound = None
        self.accent_sound = None
        self.subdivision_sound = None

        self.tick_event = None

        self.init_ui()
        self.load_background()
        self.load_sounds()

        logger.info('Экран метронома создан')

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

    def load_sounds(self):
        """Загружает звуки с учётом выбранного тембра"""
        try:
            tone = self.SOUND_TONES.get(self.sound_tone, self.SOUND_TONES['mechanical'])

            if self.sound_tone == 'mechanical':
                self.click_sound = generate_mechanical_click(
                    is_accent=False,
                    volume=self.volume
                )
                self.accent_sound = generate_mechanical_click(
                    is_accent=True,
                    volume=self.accent_volume
                )
                self.subdivision_sound = generate_mechanical_click(
                    is_accent=False,
                    volume=self.volume * 0.5
                )
            else:
                waveform = tone['waveform']
                self.click_sound = generate_click_sound(
                    frequency=tone['freq'],
                    volume=self.volume,
                    waveform=waveform
                )
                self.accent_sound = generate_accent_sound(
                    frequency=tone['accent_freq'],
                    volume=self.accent_volume,
                    waveform=waveform
                )
                self.subdivision_sound = generate_subdivision_sound(
                    frequency=tone['freq'] * 0.7,
                    volume=self.volume * 0.6,
                    waveform=waveform
                )

            logger.info(f"✅ Все звуки метронома загружены (тембр: {tone['name']})")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки звуков: {e}")

    def init_ui(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True
        )

        # ============ BPM и РАЗМЕР ============
        settings_card = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(300),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=[0, 0, 0, 0.1],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1,
            spacing=dp(4)
        )

        self.bpm_slider = VerticalSlider(
            label_text="BPM",
            min_value=30,
            max_value=250,
            initial=120,
            step=1
        )
        self.bpm_slider.bind(value=self._on_bpm_change)

        self.beat_slider = VerticalSlider(
            label_text="Размер",
            min_value=2,
            max_value=12,
            initial=4,
            step=1
        )
        self.beat_slider.bind(value=self._on_beat_change)

        self.subdivision_slider = VerticalSlider(
            label_text="Деление",
            min_value=0,
            max_value=3,
            initial=0,
            step=1
        )
        self.subdivision_slider.bind(value=self._on_subdivision_change)
        self._update_subdivision_label(0)

        settings_card.add_widget(Widget(size_hint_x=0.2))
        settings_card.add_widget(self.bpm_slider)
        settings_card.add_widget(Widget(size_hint_x=0.1))
        settings_card.add_widget(self.beat_slider)
        settings_card.add_widget(Widget(size_hint_x=0.1))
        settings_card.add_widget(self.subdivision_slider)
        settings_card.add_widget(Widget(size_hint_x=0.2))

        content.add_widget(settings_card)

        # ============ ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ============
        extras_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(250),
            padding=[dp(12), dp(8), dp(12), dp(8)],
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1,
            spacing=dp(4)
        )

        self.volume_slider = HorizontalSlider(
            label_text="Громкость",
            min_value=0,
            max_value=100,
            initial=80,
            step=5
        )
        self.volume_slider.on_value = self._on_volume_change

        self.accent_volume_slider = HorizontalSlider(
            label_text="Акцент",
            min_value=0,
            max_value=100,
            initial=100,
            step=5
        )
        self.accent_volume_slider.on_value = self._on_accent_volume_change

        accent_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(36),
            spacing=dp(12),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        accent_label = MDLabel(
            text="Акцент на сильную долю",
            font_size=sp(12),
            halign="left",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_x=1
        )

        self.accent_switch = CustomSwitch(active=True)
        self.accent_switch.on_active = self._on_accent_toggle

        accent_row.add_widget(accent_label)
        accent_row.add_widget(self.accent_switch)

        # ВЫБОР ТЕМБРА
        tone_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(12),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        tone_label = MDLabel(
            text="Тембр",
            font_size=sp(12),
            halign="left",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_x=None,
            width=dp(60)
        )

        current_tone = self.SOUND_TONES.get(self.sound_tone, self.SOUND_TONES['mechanical'])
        self.tone_button = MDRaisedButton(
            text=current_tone['name'],
            size_hint=(1, 1),
            md_bg_color=[0.3, 0.3, 0.3, 0.5],
            text_color=[1, 1, 1, 0.9],
            on_release=self.show_tone_dialog,
            font_size=sp(11)
        )

        tone_row.add_widget(tone_label)
        tone_row.add_widget(self.tone_button)

        extras_card.add_widget(self.volume_slider)
        extras_card.add_widget(self.accent_volume_slider)
        extras_card.add_widget(accent_row)
        extras_card.add_widget(tone_row)

        content.add_widget(extras_card)

        # ============ ВИЗУАЛЬНЫЙ ИНДИКАТОР ============
        self.indicator_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(56),
            padding=[dp(8), dp(4), dp(8), dp(4)],
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1
        )

        self.indicator_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=dp(6),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )

        self.beat_indicators = []
        for i in range(12):
            indicator = MDCard(
                size_hint=(None, None),
                size=(dp(26), dp(26)),
                radius=[dp(13)] * 4,
                md_bg_color=[0.3, 0.3, 0.3, 0.5],
                elevation=0
            )
            self.beat_indicators.append(indicator)
            self.indicator_layout.add_widget(indicator)

        for i in range(12):
            self.beat_indicators[i].opacity = 0

        self.indicator_card.add_widget(self.indicator_layout)
        content.add_widget(self.indicator_card)

        # ============ КНОПКИ УПРАВЛЕНИЯ ============
        controls_card = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            padding=[dp(12), dp(4), dp(12), dp(4)],
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1,
            spacing=dp(12)
        )

        self.play_btn = MDRaisedButton(
            text="▶ ВКЛ",
            size_hint=(0.5, 1),
            md_bg_color=[0.46, 0.70, 0.71, 1],
            text_color=[1, 1, 1, 1],
            on_release=self.toggle_metronome,
            font_size=sp(16)
        )

        reset_btn = MDRaisedButton(
            text="↺ Сброс",
            size_hint=(0.5, 1),
            md_bg_color=[0.3, 0.3, 0.3, 0.5],
            text_color=[1, 1, 1, 0.8],
            on_release=self.reset_metronome,
            font_size=sp(14)
        )

        controls_card.add_widget(self.play_btn)
        controls_card.add_widget(reset_btn)

        content.add_widget(controls_card)

        # ============ ИНФОРМАЦИЯ ============
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(56),
            padding=[dp(12), dp(4), dp(12), dp(4)],
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1
        )

        self.status_label = MDLabel(
            text="⏸ Остановлен",
            font_size=sp(14),
            halign="center",
            theme_text_color="Custom",
            text_color=[0.7, 0.7, 0.7, 0.8],
            size_hint_y=None,
            height=dp(26)
        )

        self.bpm_display = MDLabel(
            text="120 BPM | 4/4 | Нет деления",
            font_size=sp(11),
            halign="center",
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.6],
            size_hint_y=None,
            height=dp(20)
        )

        info_card.add_widget(self.status_label)
        info_card.add_widget(self.bpm_display)

        content.add_widget(info_card)

        # Дополнительный отступ снизу
        content.add_widget(Widget(size_hint_y=None, height=dp(16)))

        self.build_ui(content_widget=content, use_scroll=True)
        self._update_indicators(4)

    def _update_subdivision_label(self, value):
        subdivision_names = ['Нет', '1/8', '1/8T', '1/16']
        if 0 <= int(value) <= 3:
            self.subdivision_slider.value_label.text = subdivision_names[int(value)]

    def _on_bpm_change(self, instance, value):
        self.bpm = int(value)
        self._update_display()
        if self.is_running:
            self.stop_metronome()
            self.start_metronome()

    def _on_beat_change(self, instance, value):
        self.beats_per_measure = int(value)
        self._update_display()
        self._update_indicators(self.beats_per_measure)
        self.tick_count = 0

    def _on_subdivision_change(self, instance, value):
        self.subdivision = ['none', 'eighth', 'triplet', 'sixteenth'][int(value)]
        self._update_subdivision_label(value)
        self._update_display()

    def _on_volume_change(self, instance, value):
        self.volume = float(value) / 100.0
        self.load_sounds()

    def _on_accent_volume_change(self, instance, value):
        self.accent_volume = float(value) / 100.0
        self.load_sounds()

    def _on_accent_toggle(self, instance, value):
        self.is_accent_enabled = bool(value)

    # ============ ВЫБОР ТЕМБРА ============
    def show_tone_dialog(self, instance):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        for tone_id, tone_data in self.SOUND_TONES.items():
            btn_text = tone_data['name']
            if 'description' in tone_data:
                btn_text += f"\n{tone_data['description']}"

            btn = MDRaisedButton(
                text=btn_text,
                size_hint=(1, None),
                height=dp(50),
                md_bg_color=[0.46, 0.70, 0.71, 1] if tone_id == self.sound_tone else [0.2, 0.2, 0.2, 0.8],
                text_color=[1, 1, 1, 1],
                font_size=sp(12),
                on_release=lambda x, tid=tone_id: self._select_tone(tid)
            )
            content.add_widget(btn)

        dialog = MDDialog(
            title="Выберите тембр звука",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Закрыть", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.tone_dialog = dialog

    def _select_tone(self, tone_id):
        self.sound_tone = tone_id
        tone_data = self.SOUND_TONES.get(tone_id, self.SOUND_TONES['mechanical'])
        self.tone_button.text = tone_data['name']

        if hasattr(self, 'tone_dialog'):
            self.tone_dialog.dismiss()

        self.load_sounds()

        if self.is_running:
            self.stop_metronome()
            self.start_metronome()

        logger.info(f"🎵 Выбран тембр: {tone_data['name']}")

    def _update_display(self):
        subdivision_names = {
            'none': 'Нет деления',
            'eighth': 'Восьмые',
            'triplet': 'Триоли',
            'sixteenth': 'Шестнадцатые',
        }
        self.bpm_display.text = f"{self.bpm} BPM | {self.beats_per_measure}/4 | {subdivision_names.get(self.subdivision, 'Нет деления')}"

    def _update_indicators(self, count):
        for i in range(12):
            if i < count:
                self.beat_indicators[i].opacity = 1
                self.beat_indicators[i].md_bg_color = [0.3, 0.3, 0.3, 0.5]
            else:
                self.beat_indicators[i].opacity = 0

    def _update_beat_indicators(self):
        for i in range(self.beats_per_measure):
            if i == 0 and self.is_accent_enabled:
                self.beat_indicators[i].md_bg_color = [0.46, 0.70, 0.71, 0.9]
            else:
                self.beat_indicators[i].md_bg_color = [0.3, 0.3, 0.3, 0.5]

    def _highlight_beat(self, beat_index):
        self._update_beat_indicators()

        if beat_index == 0 and self.is_accent_enabled:
            color = [0.46, 0.70, 0.71, 1.0]
        else:
            color = [0.6, 0.6, 0.6, 0.8]

        if beat_index < len(self.beat_indicators):
            self.beat_indicators[beat_index].md_bg_color = color

    def toggle_metronome(self, instance=None):
        if self.is_running:
            self.stop_metronome()
        else:
            self.start_metronome()

    def start_metronome(self):
        if self.is_running:
            return

        if not self.click_sound or not self.accent_sound:
            self.load_sounds()
            if not self.click_sound or not self.accent_sound:
                self.status_label.text = "❌ Ошибка звука"
                return

        self.is_running = True
        self.tick_count = 0
        self.subdivision_count = 0
        self.play_btn.text = "⏹ СТОП"
        self.play_btn.md_bg_color = [0.8, 0.3, 0.3, 1]
        self.status_label.text = "▶ Работает"
        self.status_label.text_color = [0.46, 0.70, 0.71, 1]

        interval = 60.0 / self.bpm
        self._tick()
        self.tick_event = Clock.schedule_interval(self._tick, interval)
        logger.info(f"✅ Метроном запущен: {self.bpm} BPM, {self.beats_per_measure}/4")

    def stop_metronome(self):
        if self.tick_event:
            self.tick_event.cancel()
            self.tick_event = None

        self.is_running = False
        self.play_btn.text = "▶ ВКЛ"
        self.play_btn.md_bg_color = [0.46, 0.70, 0.71, 1]
        self.status_label.text = "⏸ Остановлен"
        self.status_label.text_color = [0.7, 0.7, 0.7, 0.8]

        self._update_beat_indicators()
        self.tick_count = 0
        self.subdivision_count = 0
        logger.info("⏹ Метроном остановлен")

    def reset_metronome(self, instance=None):
        if self.is_running:
            self.stop_metronome()

        self.tick_count = 0
        self.subdivision_count = 0
        self._update_beat_indicators()
        self.bpm_slider.value = 120
        self.beat_slider.value = 4
        self.subdivision_slider.value = 0
        self.bpm = 120
        self.beats_per_measure = 4
        self.subdivision = 'none'
        self._update_display()
        self.status_label.text = "↺ Сброшен"
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', '⏸ Остановлен'), 1)

    def _tick(self, dt=None):
        if not self.is_running:
            return

        is_main_beat = (self.subdivision_count == 0)
        is_accent = (is_main_beat and self.tick_count == 0)

        try:
            if is_accent and self.is_accent_enabled:
                if self.accent_sound:
                    self.accent_sound.play()
            elif is_main_beat:
                if self.click_sound:
                    self.click_sound.play()
            else:
                if self.subdivision_sound:
                    self.subdivision_sound.play()
        except Exception as e:
            logger.error(f"Ошибка воспроизведения: {e}")

        if is_main_beat:
            beat_index = self.tick_count % self.beats_per_measure
            self._highlight_beat(beat_index)

            if beat_index < len(self.beat_indicators):
                indicator = self.beat_indicators[beat_index]
                anim = Animation(opacity=1.0, duration=0.05) + Animation(opacity=0.7, duration=0.1)
                anim.start(indicator)

            self.tick_count = (self.tick_count + 1) % self.beats_per_measure

            if is_accent:
                self.status_label.text = f"▶ {self.tick_count + 1}/{self.beats_per_measure} (акцент)"
            else:
                self.status_label.text = f"▶ {self.tick_count + 1}/{self.beats_per_measure}"

        if self.subdivision == 'none':
            self.subdivision_count = 0
        elif self.subdivision == 'eighth':
            self.subdivision_count = (self.subdivision_count + 1) % 2
        elif self.subdivision == 'triplet':
            self.subdivision_count = (self.subdivision_count + 1) % 3
        elif self.subdivision == 'sixteenth':
            self.subdivision_count = (self.subdivision_count + 1) % 4

    def on_enter(self):
        logger.info("Вход в экран метронома")
        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()

    def on_leave(self):
        logger.info("Выход из экрана метронома")
        if self.is_running:
            self.stop_metronome()