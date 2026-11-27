# screens/metronome_screen.py
"""
Экран гитарного метронома с анимированным маятником,
карточкой слайдеров и адаптивными индикаторами.
Адаптирован под 3 темы и 6 языков.

ДИЗАЙН:
  - Карточка со шкалами — те же фон/обводка/радиус, что у карточки тюнера.
  - Меню — отдельная карточка с теми же фон/обводкой/радиусом.
  - Разделители в меню — «рваные» короткие линии по центру.
  - Промежуток между карточкой и меню — dp(10), как в тюнере.
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line
from kivy.core.image import Image as CoreImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, BooleanProperty, ListProperty
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from io import BytesIO
import math
import array
import struct
import tempfile
import os
import random
from kivy.uix.anchorlayout import AnchorLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.slider import MDSlider
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Ellipse
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from state.settings_state import settings_state as settings_manager
from utils.localization import get_text
from metronome_utils.pendulum_widget import MetronomePendulumWidget
from metronome_utils.fader_widget import StudioVerticalSlider
from metronome_utils.button_widget import StudioHardwareButton
import io
import base64
logger = screen_logger('Metronome')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА (палитра согласована с TunerColors / ChordsColors)
# ============================================================

class MetronomeColors:
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
            return [1, 1, 1, 0.6]

    @staticmethod
    def get_card_bg(theme_id):
        """Фон карточки — как menu_bg в ChordsColors."""
        if theme_id == 'light':
            return [0.95, 0.95, 0.95, 1]
        elif theme_id == 'dark':
            return [0.15, 0.15, 0.15, 1]
        else:
            return [0, 0, 0, 0.15]

    @staticmethod
    def get_card_line(theme_id):
        """Обводка карточки — как card_line в ChordsColors."""
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        else:
            return [0.46, 0.70, 0.71, 0.4]

    @staticmethod
    def get_card_line_width(theme_id):
        return 1.5

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        else:
            return [1, 1, 1, 0.5]

    @staticmethod
    def get_slider_track_inactive(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 0.15]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.2]
        else:
            return [1, 1, 1, 0.3]

    @staticmethod
    def get_divider_color(theme_id):
        """Цвет «рваного» разделителя."""
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.6]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.6]
        else:
            return [0.46, 0.70, 0.71, 0.55]


# ============ ФУНКЦИИ ДЛЯ ПУТЕЙ И ВРЕМЕННЫХ ФАЙЛОВ ============
def get_temp_path():
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except:
            pass
    return tempfile.gettempdir()


# ============ ГЕНЕРАТОРЫ ЗВУКА ============
def generate_click_sound(frequency=1200, duration=0.05, sample_rate=44100, volume=0.8, waveform='sine'):
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
            f.write(b'WAVEfmt ')
            f.write(struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
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
            f.write(b'WAVEfmt ')
            f.write(struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
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
            f.write(b'WAVEfmt ')
            f.write(struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
            f.write(b'data')
            f.write(struct.pack('<I', len(audio_data) * 2))
            audio_data.tofile(f)

    sound = SoundLoader.load(tmp_path)
    try:
        os.unlink(tmp_path)
    except:
        pass
    return sound


def generate_mechanical_click(is_accent=False, sample_rate=44100, volume=0.8):
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

        noise = noise_buffer[i] * noise_amount * envelope * 0.6 if i < len(noise_buffer) else 0

        click = 0
        if t < 0.0015:
            click = 0.3 * (1 - t / 0.0015)

        combined = (tone * 0.5 + low_tone * 0.2 + noise + click) * envelope * vol
        combined = max(-1.0, min(1.0, combined))
        audio_data.append(int(32767 * combined))

    temp_dir = get_temp_path()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=temp_dir) as tmp_file:
        tmp_path = tmp_file.name
        with open(tmp_path, 'wb') as f:
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + len(audio_data) * 2))
            f.write(b'WAVEfmt ')
            f.write(struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
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
        self.size_hint = (None, 1)
        self.width = dp(80)
        self.spacing = dp(2)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]

        slider_container = BoxLayout(
            orientation='vertical', size_hint=(1, 1),
            padding=[dp(6), dp(2), dp(6), dp(2)]
        )

        self.value_label = MDLabel(
            text=str(int(initial)), font_size=sp(18),
            halign="center", valign="middle",
            size_hint=(1, None), height=dp(24),
            theme_text_color="Custom", bold=True
        )
        self.value_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))

        self.slider = MDSlider(
            min=min_value - 0.01, max=max_value + 0.01,
            value=initial, step=step, size_hint=(None, 1),
            width=dp(48),
            orientation='vertical',
            pos_hint={'center_x': 0.5}, hint=False
        )
        self.slider.ripple_scale = 0
        self.slider.bind(value=self._on_value_change)

        self.value_below = MDLabel(
            text=str(int(initial)), font_size=sp(14),
            halign="center", valign="middle",
            size_hint=(1, None), height=dp(18),
            theme_text_color="Custom", bold=True
        )
        self.value_below.bind(size=lambda inst, val: setattr(inst, 'text_size', val))

        self.label = MDLabel(
            text=label_text, font_size=sp(10),
            halign="center", valign="middle",
            size_hint=(1, None), height=dp(16),
            theme_text_color="Custom", bold=True
        )
        self.label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))

        slider_container.add_widget(self.slider)
        self.add_widget(self.value_label)
        self.add_widget(slider_container)
        self.add_widget(self.value_below)
        self.add_widget(self.label)

        self.update_theme_colors()


    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = MetronomeColors.get_accent(theme_id)
        text_s = MetronomeColors.get_text_secondary(theme_id)
        self.value_label.text_color = accent
        self.value_below.text_color = accent
        self.label.text_color = text_s
        self.slider.thumb_color_active = accent
        self.slider.thumb_color_inactive = accent
        self.slider.track_color_active = accent[:3] + [0.6]
        self.slider.track_color_inactive = MetronomeColors.get_slider_track_inactive(theme_id)

        try:
            self.slider.cursor_size = (dp(52), dp(52))
            self.slider.hint_width = dp(52)
        except Exception:
            pass

    def _on_value_change(self, instance, value):
        if value < self.min_value:
            self.slider.value = self.min_value
            return
        elif value > self.max_value:
            self.slider.value = self.max_value
            return
        rounded = round(value / self.step) * self.step
        if rounded != value:
            self.slider.value = rounded
            return
        self.value = rounded
        self.value_label.text = str(int(rounded))
        self.value_below.text = str(int(rounded))

    def set_value(self, new_value):
        new_value = max(self.min_value, min(self.max_value, new_value))
        rounded = round(new_value / self.step) * self.step
        self.slider.value = rounded
        self.value = rounded
        self.value_label.text = str(int(rounded))
        self.value_below.text = str(int(rounded))

    def get_value(self):
        return self.value


# ============ «РВАНЫЙ» РАЗДЕЛИТЕЛЬ ============
class DashedDivider(Widget):
    """
    Короткая вертикальная линия по центру, не доходит до краёв —
    как в меню аккордов и меню тюнера.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(2)
        self._line_color = MetronomeColors.get_divider_color(settings_manager.theme)
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
        self._line_color = MetronomeColors.get_divider_color(settings_manager.theme)
        self._color.rgba = self._line_color
        self._update_line()


# ============ МЕНЮ МЕТРОНОМА ============
class IconMenuItem(ButtonBehavior, MDBoxLayout):
    def __init__(self, icon_name, on_press=None, icon_color=None, fixed_color=False, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press
        self.fixed_color = fixed_color
        self.icon_color = icon_color if icon_color else [1, 1, 1, 0.7]

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = [dp(4), dp(6), dp(4), dp(6)]
        self.spacing = dp(0)
        self.md_bg_color = [0, 0, 0, 0]

        self.icon_btn = MDIconButton(
            icon=icon_name, size_hint=(None, None), size=(dp(32), dp(32)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}, theme_icon_color="Custom",
            icon_color=self.icon_color, md_bg_color=[0, 0, 0, 0], ripple_scale=0)
        self.icon_btn.bind(on_release=self._on_press)

        self.add_widget(self.icon_btn)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _on_enter(self, *args):
        self.md_bg_color = [1, 1, 1, 0.05]

    def _on_leave(self, *args):
        self.md_bg_color = [0, 0, 0, 0]

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback()

    def set_icon(self, icon_name):
        self.icon_name = icon_name
        self.icon_btn.icon = icon_name

    def set_color(self, color):
        self.icon_color = color
        self.icon_btn.icon_color = color


class MetronomeMenu(MDBoxLayout):
    """Студийная рэковая панель с 4 триггер-пэдами в едином стиле со шкалами."""

    _panel_dark_tex = None
    _panel_light_tex = None

    def __init__(
        self,
        on_play_press=None,
        on_reset_press=None,
        on_accent_press=None,
        on_tone_press=None,
        is_running=False,
        is_accent_enabled=True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (1, None)
        self.height = dp(74)
        self.padding = [dp(22), dp(9), dp(22), dp(9)]
        self.spacing = dp(8)

        self.on_play_press = on_play_press
        self.on_reset_press = on_reset_press
        self.on_accent_press = on_accent_press
        self.on_tone_press = on_tone_press
        self.is_running = is_running
        self.is_accent_enabled = is_accent_enabled

        if MetronomeMenu._panel_dark_tex is None:
            from data.metronome import button_assets
            MetronomeMenu._panel_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(button_assets.PANEL_DARK_B64)), ext="png"
            ).texture
            MetronomeMenu._panel_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(button_assets.PANEL_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._panel_dark_tex,
                pos=self.pos,
                size=self.size,
            )

        self.bind(pos=self._update_bg, size=self._update_bg)

        self._build_ui()
        self.update_theme_colors()

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _build_ui(self):
        self.play_item = StudioHardwareButton(
            icon_type="stop" if self.is_running else "play",
            is_active=self.is_running,
            on_press=self._on_play,
        )
        self.reset_item = StudioHardwareButton(
            icon_type="reset",
            is_active=False,
            on_press=self._on_reset,
        )
        self.accent_item = StudioHardwareButton(
            icon_type="accent",
            is_active=self.is_accent_enabled,
            on_press=self._on_accent,
        )
        self.tone_item = StudioHardwareButton(
            icon_type="tone",
            is_active=True,
            on_press=self._on_tone,
        )

        self.add_widget(self.play_item)
        self.add_widget(self.reset_item)
        self.add_widget(self.accent_item)
        self.add_widget(self.tone_item)

    def _on_play(self):
        if self.on_play_press:
            self.on_play_press()

    def _on_reset(self):
        if self.on_reset_press:
            self.on_reset_press()

    def _on_accent(self):
        if self.on_accent_press:
            self.on_accent_press()

    def _on_tone(self):
        if self.on_tone_press:
            self.on_tone_press()

    def update_state(self, is_running, is_accent_enabled):
        self.is_running = is_running
        self.is_accent_enabled = is_accent_enabled

        self.play_item.icon_type = "stop" if is_running else "play"
        self.play_item.is_active = is_running
        self.play_item.custom_glow_color = [0.95, 0.28, 0.28, 1.0] if is_running else []

        self.accent_item.is_active = is_accent_enabled

    def update_tone_color(self, color):
        self.tone_item.custom_glow_color = list(color)
        self.tone_item.is_active = True

    def update_theme_colors(self):
        is_light = settings_manager.theme == "light"
        self._bg_rect.texture = self._panel_light_tex if is_light else self._panel_dark_tex

        for btn in (self.play_item, self.reset_item, self.accent_item, self.tone_item):
            btn.update_theme_colors()




# ============ СВЕТОДИОДНЫЕ ИНДИКАТОРЫ ДОЛЕЙ ============
class BeatLedIndicator(Widget):
    """Полуобъёмная стеклянная лампочка микшерного пульта в металлическом ободке."""
    led_color = ListProperty([0.18, 0.92, 0.34, 1.0])
    is_active = BooleanProperty(False)
    is_accent_beat = BooleanProperty(False)
    glow_alpha = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(26), dp(26))
        self.bind(
            pos=self._redraw,
            size=self._redraw,
            led_color=self._redraw,
            is_active=self._on_active_changed,
            is_accent_beat=self._redraw,
            glow_alpha=self._redraw,
        )

    def _on_active_changed(self, instance, value):
        Animation.cancel_all(self, 'glow_alpha')
        if value:
            self.glow_alpha = 1.0
        else:
            Animation(glow_alpha=0.0, duration=0.14, transition='out_quad').start(self)

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width <= 2 or self.height <= 2:
            return

        cx, cy = self.center
        r = min(self.width, self.height) * 0.5
        cr, cg, cb, _ = self.led_color
        is_light = (settings_manager.theme == 'light')
        g = max(0.0, min(1.0, self.glow_alpha))

        with self.canvas:
            # 1. Широкий внешний ореол свечения при срабатывании доли
            if g > 0.01:
                Color(cr, cg, cb, 0.24 * g)
                r_halo2 = r + dp(4.0)
                Ellipse(pos=(cx - r_halo2, cy - r_halo2), size=(r_halo2 * 2, r_halo2 * 2))

                Color(cr, cg, cb, 0.42 * g)
                r_halo1 = r + dp(1.8)
                Ellipse(pos=(cx - r_halo1, cy - r_halo1), size=(r_halo1 * 2, r_halo1 * 2))

            # 2. Тёмная посадочная шахта цоколя
            Color(0.02, 0.03, 0.04, 0.96) if not is_light else Color(0.45, 0.48, 0.47, 0.95)
            Ellipse(pos=(cx - r, cy - r), size=(r * 2, r * 2))

            # 3. Металлический ободок (цоколь лампочки) с фаской
            bezel_r = r - dp(0.8)
            Color(0.46, 0.50, 0.54, 1.0) if not is_light else Color(0.82, 0.85, 0.84, 1.0)
            Line(circle=(cx, cy, bezel_r), width=dp(1.5))

            Color(0.82, 0.86, 0.90, 0.55) if not is_light else Color(1.0, 1.0, 1.0, 0.85)
            Line(circle=(cx, cy + dp(0.3), bezel_r - dp(0.5)), width=dp(0.8))

            # 4. Тёмная подложка стеклянной линзы (чтобы потухшая лампочка выглядела как тёмное стекло)
            lens_r = r - dp(2.4)
            if is_light:
                Color(0.24, 0.28, 0.27, 0.92)
            else:
                Color(0.08, 0.10, 0.11, 0.96)
            Ellipse(pos=(cx - lens_r, cy - lens_r), size=(lens_r * 2, lens_r * 2))

            # 5. Основной цвет купола лампочки (в ожидании — приглушённое цветное стекло, при ударе — полная яркость)
            idle_fill = 0.26 if self.is_accent_beat else 0.18
            fill_alpha = idle_fill + (1.0 - idle_fill) * g
            Color(cr, cg, cb, fill_alpha)
            Ellipse(pos=(cx - lens_r, cy - lens_r), size=(lens_r * 2, lens_r * 2))

            # 6. Яркое внутреннее ядро линзы (создаёт 3D-объём полусферы)
            core_r = lens_r * 0.68
            core_alpha = (0.14 if self.is_accent_beat else 0.08) + 0.78 * g
            Color(
                min(1.0, cr + 0.25),
                min(1.0, cg + 0.25),
                min(1.0, cb + 0.25),
                min(0.95, core_alpha),
            )
            Ellipse(pos=(cx - core_r, cy - core_r * 0.9), size=(core_r * 2, core_r * 2))

            # 7. Нижний рефлекс стеклянной полусферы (внутреннее отражение света)
            ref_w = lens_r * 1.15
            ref_h = lens_r * 0.45
            Color(
                min(1.0, cr + 0.35),
                min(1.0, cg + 0.35),
                min(1.0, cb + 0.35),
                0.14 + 0.42 * g,
            )
            Ellipse(pos=(cx - ref_w * 0.5, cy - lens_r * 0.78), size=(ref_w, ref_h))

            # 8. Верхний глянцевый блик стекла (всегда виден на линзе как на реальном светодиоде)
            hl_w = lens_r * 0.86
            hl_h = lens_r * 0.42
            Color(1.0, 1.0, 1.0, 0.28 + 0.58 * g)
            Ellipse(pos=(cx - hl_w * 0.5, cy + lens_r * 0.26), size=(hl_w, hl_h))




# ============ ОСНОВНОЙ ЭКРАН ============
class MetronomeScreen(BaseScreen):
    DEFAULT_BPM = 120
    DEFAULT_BEATS = 4
    DEFAULT_SUBDIVISION = 0
    DEFAULT_VOLUME = 50
    DEFAULT_ACCENT = True
    DEFAULT_TONE = 'mechanical'

    SOUND_TONE_KEYS = ['mechanical', 'electronic', 'wood', 'click', 'beep']
    SOUND_TONES = {
        'mechanical': {'type': 'mechanical'},
        'electronic': {'type': 'synthetic', 'waveform': 'sine', 'freq': 1200, 'accent_freq': 1800},
        'wood': {'type': 'synthetic', 'waveform': 'triangle', 'freq': 800, 'accent_freq': 1200},
        'click': {'type': 'synthetic', 'waveform': 'square', 'freq': 600, 'accent_freq': 900},
        'beep': {'type': 'synthetic', 'waveform': 'sawtooth', 'freq': 1500, 'accent_freq': 2200},
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'metronome'
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None

        self.bpm = self.DEFAULT_BPM
        self.beats_per_measure = self.DEFAULT_BEATS
        self.subdivision = 'none'
        self.sound_tone = self.DEFAULT_TONE
        self.volume = self.DEFAULT_VOLUME / 100.0
        self.is_accent_enabled = self.DEFAULT_ACCENT
        self.is_running = False
        self.tick_count = 0
        self.total_beats = 0
        self.subdivision_count = 0
        self.click_sound = None
        self.accent_sound = None
        self.subdivision_sound = None
        self.tick_event = None

        self.load_background()
        self.init_ui()
        self.load_sounds()

        logger.info('Экран метронома создан')

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
        accent = MetronomeColors.get_accent(theme_id)

        if hasattr(self, 'bpm_slider'): self.bpm_slider.update_theme_colors()
        if hasattr(self, 'beat_slider'): self.beat_slider.update_theme_colors()
        if hasattr(self, 'subdivision_slider'): self.subdivision_slider.update_theme_colors()
        if hasattr(self, 'volume_slider'): self.volume_slider.update_theme_colors()

        if hasattr(self, 'metronome_menu'):
            self.metronome_menu.update_theme_colors()

        if hasattr(self, '_fader_panel_rect'):
            is_light = (theme_id == 'light')
            self._fader_panel_rect.texture = (
                self._fader_panel_light_tex if is_light else self._fader_panel_dark_tex
            )

        if hasattr(self, '_hint_label'):
            self._hint_label.text_color = MetronomeColors.get_hint_color(theme_id)

        if hasattr(self, '_led_strip_rect'):
            is_light = (theme_id == 'light')
            self._led_strip_rect.texture = (
                self._led_strip_light_tex if is_light else self._led_strip_dark_tex
            )

        if hasattr(self, 'pendulum'):
            self.pendulum.pendulum_color = (
                accent if self.is_accent_enabled else [0.6, 0.6, 0.6, 1]
            )

        if hasattr(self, 'beat_indicators'):
            self._update_beat_indicators()

    def update_language(self):
        if hasattr(self, '_hint_label') and self._hint_label.opacity > 0:
            self._update_display()

    def load_sounds(self):
        try:
            tone = self.SOUND_TONES.get(self.sound_tone, self.SOUND_TONES['mechanical'])
            accent_volume = min(1.0, self.volume * 1.25) if self.is_accent_enabled else self.volume
            if self.sound_tone == 'mechanical':
                self.click_sound = generate_mechanical_click(is_accent=False, volume=self.volume)
                self.accent_sound = generate_mechanical_click(is_accent=True,
                                                              volume=accent_volume) if self.is_accent_enabled else self.click_sound
                self.subdivision_sound = generate_mechanical_click(is_accent=False, volume=self.volume * 0.5)
            else:
                waveform = tone['waveform']
                self.click_sound = generate_click_sound(tone['freq'], 0.05, 44100, self.volume, waveform)
                self.accent_sound = generate_accent_sound(tone['accent_freq'], 0.08, 44100, accent_volume,
                                                          waveform) if self.is_accent_enabled else self.click_sound
                self.subdivision_sound = generate_subdivision_sound(tone['freq'] * 0.7, 0.03, 44100, self.volume * 0.6,
                                                                    waveform)
            logger.info(f"Звуки загружены ({self.sound_tone})")
        except Exception as e:
            logger.error(f"Ошибка загрузки звуков: {e}")

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        nav_bottom = layout_config.get_bottom_nav_total_height()
        padding_bottom = max(0, nav_bottom - dp(2))

        content_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            padding=[dp(16), dp(8), dp(16), padding_bottom]
        )

        # Верхний блок: шкалы dp(330) + LED-планка dp(42) + меню dp(74) + подсказка dp(22) = dp(468)
        top_section = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(468),
            spacing=0,
        )

        from data.metronome import fader_assets
        self._fader_panel_dark_tex = CoreImage(
            io.BytesIO(base64.b64decode(fader_assets.PANEL_DARK_B64)), ext="png"
        ).texture
        self._fader_panel_light_tex = CoreImage(
            io.BytesIO(base64.b64decode(fader_assets.PANEL_LIGHT_B64)), ext="png"
        ).texture

        # 1. КАРТОЧКА СО ШКАЛАМИ
        self.unified_card = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(330),
            padding=[dp(22), dp(14), dp(22), dp(14)],
            spacing=0
        )
        with self.unified_card.canvas.before:
            Color(1, 1, 1, 1)
            self._fader_panel_rect = Rectangle(
                texture=self._fader_panel_dark_tex,
                pos=self.unified_card.pos,
                size=self.unified_card.size,
            )
        self.unified_card.bind(
            pos=lambda inst, val: setattr(self._fader_panel_rect, 'pos', val),
            size=lambda inst, val: setattr(self._fader_panel_rect, 'size', val),
        )

        sliders_layout = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            spacing=dp(4)
        )

        self.bpm_slider = StudioVerticalSlider(
            label_text="BPM", min_value=30, max_value=250,
            initial=self.DEFAULT_BPM, step=1,
            on_value_change=self._on_bpm_change
        )

        self.beat_slider = StudioVerticalSlider(
            label_text="BEAT", min_value=2, max_value=12,
            initial=self.DEFAULT_BEATS, step=1,
            on_value_change=self._on_beat_change
        )

        self.subdivision_slider = StudioVerticalSlider(
            label_text="SUB", min_value=0, max_value=3,
            initial=self.DEFAULT_SUBDIVISION, step=1,
            on_value_change=self._on_subdivision_change
        )

        self.volume_slider = StudioVerticalSlider(
            label_text="VOL", min_value=0, max_value=100,
            initial=self.DEFAULT_VOLUME, step=5,
            on_value_change=self._on_volume_change
        )

        for w in (
                Widget(size_hint_x=1), self.bpm_slider,
                Widget(size_hint_x=1), self.beat_slider,
                Widget(size_hint_x=1), self.subdivision_slider,
                Widget(size_hint_x=1), self.volume_slider,
                Widget(size_hint_x=1),
        ):
            sliders_layout.add_widget(w)

        self.unified_card.add_widget(sliders_layout)
        top_section.add_widget(self.unified_card)

        # 2. LED-ПАНЕЛЬ ИНДИКАТОРОВ ДОЛЕЙ (между шкалами и кнопками меню)
        from data.metronome import button_assets
        self._led_strip_dark_tex = CoreImage(
            io.BytesIO(base64.b64decode(button_assets.LED_STRIP_DARK_B64)), ext="png"
        ).texture
        self._led_strip_light_tex = CoreImage(
            io.BytesIO(base64.b64decode(button_assets.LED_STRIP_LIGHT_B64)), ext="png"
        ).texture

        indicator_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None),
            height=dp(42), padding=[0, dp(1), 0, dp(1)]
        )
        self.indicator_card = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            padding=[dp(22), dp(5), dp(22), dp(5)],
        )
        with self.indicator_card.canvas.before:
            Color(1, 1, 1, 1)
            self._led_strip_rect = Rectangle(
                texture=self._led_strip_dark_tex,
                pos=self.indicator_card.pos,
                size=self.indicator_card.size,
            )
        self.indicator_card.bind(
            pos=lambda inst, val: setattr(self._led_strip_rect, 'pos', val),
            size=lambda inst, val: setattr(self._led_strip_rect, 'size', val),
        )

        indicator_wrapper = AnchorLayout(
            anchor_x='center', anchor_y='center', size_hint=(1, 1)
        )
        self.indicator_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            height=dp(26),
            spacing=dp(10),
        )
        self.beat_indicators = []
        for i in range(12):
            ind = BeatLedIndicator(opacity=1)
            self.beat_indicators.append(ind)

        indicator_wrapper.add_widget(self.indicator_layout)
        self.indicator_card.add_widget(indicator_wrapper)
        indicator_container.add_widget(self.indicator_card)
        top_section.add_widget(indicator_container)

        # 3. МЕНЮ КНОПОК УПРАВЛЕНИЯ
        self.metronome_menu = MetronomeMenu(
            on_play_press=self.toggle_metronome,
            on_reset_press=self._reset_to_defaults,
            on_accent_press=self.toggle_accent,
            on_tone_press=self.cycle_tone,
            is_running=self.is_running,
            is_accent_enabled=self.is_accent_enabled
        )
        top_section.add_widget(self.metronome_menu)

        # 4. СТРОКА ПОДСКАЗОК ПОД МЕНЮ
        hint_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(22),
            padding=[0, dp(6), 0, 0],
        )
        self._hint_label = MDLabel(
            text="", font_size=sp(11), halign="center",
            size_hint_y=None, height=dp(18),
            theme_text_color="Custom", opacity=0
        )
        hint_box.add_widget(self._hint_label)
        top_section.add_widget(hint_box)

        content_container.add_widget(top_section)

        # 5. МАЯТНИК МЕТРОНОМА
        pendulum_container = FloatLayout(size_hint=(1, 1))
        pendulum_scale = 0.95 if platform == 'android' else 0.98
        self.pendulum = MetronomePendulumWidget(
            bpm_value=self.DEFAULT_BPM,
            size_hint=(pendulum_scale, pendulum_scale),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        pendulum_container.add_widget(self.pendulum)
        content_container.add_widget(pendulum_container)

        main_layout.add_widget(content_container)
        self.add_widget(main_layout)

        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()
        self._show_indicators()
        self._update_subdivision_label(self.DEFAULT_SUBDIVISION)
        self.update_theme_colors()
        self._update_display()

    def _reset_to_defaults(self):
        was_running = self.is_running
        if was_running:
            self.stop_metronome()
        self.bpm = self.DEFAULT_BPM
        self.beats_per_measure = self.DEFAULT_BEATS
        self.subdivision = 'none'
        self.sound_tone = self.DEFAULT_TONE
        self.volume = self.DEFAULT_VOLUME / 100.0
        self.is_accent_enabled = self.DEFAULT_ACCENT
        self.bpm_slider.set_value(self.DEFAULT_BPM)
        self.beat_slider.set_value(self.DEFAULT_BEATS)
        self.subdivision_slider.set_value(self.DEFAULT_SUBDIVISION)
        self.volume_slider.set_value(self.DEFAULT_VOLUME)
        self._update_subdivision_label(self.DEFAULT_SUBDIVISION)
        self._update_display()
        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()
        self._hide_indicators()
        if hasattr(self, 'pendulum'):
            self.pendulum.bpm_value = self.DEFAULT_BPM
            if not self.is_running:
                self.pendulum.angle = 0
        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)
        self.load_sounds()
        self._show_temporary_hint(get_text('reset', 'Сброс'))

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
            self._hint_timer = None

    def _get_led_palette(self):
        """Цвета лампочек микшера: главная доля — зелёная, остальные — жёлтые."""
        theme_id = settings_manager.theme
        if theme_id == 'light':
            return [0.06, 0.72, 0.28, 1.0], [0.95, 0.68, 0.04, 1.0]
        return [0.16, 0.96, 0.34, 1.0], [1.0, 0.78, 0.10, 1.0]

    def _update_indicators(self, count):
        count = max(2, min(12, count))
        from kivy.core.window import Window
        # Внутренняя ниша планки (с учётом боковых полей dp(32) и стоек планки ~dp(44))
        available_width = max(dp(120), Window.width - dp(84))

        spacing = dp(10) if count <= 6 else (dp(7) if count <= 9 else dp(4.5))
        self.indicator_layout.spacing = spacing

        total_spacing = (count - 1) * spacing
        calculated_size = (available_width - total_spacing) / count

        if count <= 6:
            max_size, min_size = dp(24), dp(18)
        elif count <= 8:
            max_size, min_size = dp(22), dp(16)
        elif count <= 10:
            max_size, min_size = dp(19), dp(14)
        else:
            max_size, min_size = dp(17), dp(12)

        final_size = max(min(calculated_size, max_size), min_size)

        self.indicator_layout.clear_widgets()
        for i in range(count):
            ind = self.beat_indicators[i]
            ind.size = (final_size, final_size)
            ind.opacity = 1
            self.indicator_layout.add_widget(ind)

        self.indicator_layout.height = final_size
        self.indicator_layout.width = count * final_size + (count - 1) * spacing
        self.indicator_card.opacity = 1
        self._update_beat_indicators()

    def _update_beat_indicators(self):
        accent_col, normal_col = self._get_led_palette()
        for i in range(self.beats_per_measure):
            ind = self.beat_indicators[i]
            is_acc = (i == 0 and self.is_accent_enabled)
            ind.is_accent_beat = is_acc
            ind.is_active = False
            ind.led_color = accent_col if is_acc else normal_col

    def _highlight_beat(self, beat_index):
        self._update_beat_indicators()
        if 0 <= beat_index < self.beats_per_measure:
            ind = self.beat_indicators[beat_index]
            ind.is_active = True
            Clock.unschedule(self._deactivate_leds)
            Clock.schedule_once(self._deactivate_leds, 0.12)

    def _deactivate_leds(self, dt=None):
        for ind in self.beat_indicators:
            ind.is_active = False

    def _hide_indicators(self):
        """В режиме ожидания лампочки остаются видимыми на планке, но гаснут."""
        Clock.unschedule(self._deactivate_leds)
        for ind in self.beat_indicators:
            Animation.cancel_all(ind, 'glow_alpha')
            ind.glow_alpha = 0.0
            ind.is_active = False
        self.indicator_card.opacity = 1

    def _show_indicators(self):
        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()
        self.indicator_card.opacity = 1
        for i in range(self.beats_per_measure):
            self.beat_indicators[i].opacity = 1


    def _tick(self, dt=None):
        if not self.is_running:
            return
        subs = self._get_subdivisions_per_beat()
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
            if hasattr(self, 'pendulum'):
                self.pendulum.sync_beat(self.total_beats)
            self.total_beats += 1
            self._highlight_beat(beat_index)
            self.tick_count = (self.tick_count + 1) % self.beats_per_measure

        self.subdivision_count = (self.subdivision_count + 1) % subs

    def _update_subdivision_label(self, value):
        names = [get_text('sub_none'), get_text('sub_eighth'),
                 get_text('sub_triplet'), get_text('sub_sixteenth')]
        if 0 <= int(value) <= 3:
            self.subdivision_slider.set_display_text(names[int(value)])

    def _update_display(self):
        sub_names = {'none': get_text('sub_none'), 'eighth': get_text('sub_eighth'),
                     'triplet': get_text('sub_triplet'), 'sixteenth': get_text('sub_sixteenth')}
        sub_text = sub_names.get(self.subdivision, get_text('sub_none'))
        self._show_temporary_hint(
            f"{self.bpm} BPM | {self.beats_per_measure}/4 | {sub_text}", 1.5
        )

    def _on_bpm_change(self, instance, value):
        self.bpm = int(value)
        if hasattr(self, 'pendulum'):
            self.pendulum.bpm_value = self.bpm
        self._update_display()
        self._restart_tick_timer()

    def _on_subdivision_change(self, instance, value):
        self.subdivision = ['none', 'eighth', 'triplet', 'sixteenth'][int(value)]
        self._update_subdivision_label(value)
        self._update_display()
        self.subdivision_count = 0
        self._restart_tick_timer()

    def _on_beat_change(self, instance, value):
        self.beats_per_measure = int(value)
        self._update_display()
        self._update_indicators(self.beats_per_measure)
        self.tick_count = 0
        if self.is_running:
            self._update_beat_indicators()


    def _on_volume_change(self, instance, value):
        self.volume = float(value) / 100.0
        self.load_sounds()

    def toggle_accent(self):
        self.is_accent_enabled = not self.is_accent_enabled
        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)
        self.load_sounds()
        self._update_beat_indicators()
        if hasattr(self, 'pendulum'):
            self.pendulum.pendulum_color = (
                MetronomeColors.get_accent(settings_manager.theme)
                if self.is_accent_enabled else [0.6, 0.6, 0.6, 1]
            )
        state = get_text('on') if self.is_accent_enabled else get_text('off')
        self._show_temporary_hint(f"{get_text('accent')}: {state}", 1.2)

    def cycle_tone(self):
        keys = self.SOUND_TONE_KEYS
        idx = keys.index(self.sound_tone)
        self.sound_tone = keys[(idx + 1) % len(keys)]
        colors = {
            'mechanical': [0.61, 0.15, 0.69, 1],
            'electronic': [0.0, 0.74, 0.83, 1],
            'wood': [0.85, 0.55, 0.25, 1],
            'click': [0.2, 0.8, 0.6, 1],
            'beep': [0.9, 0.3, 0.7, 1],
        }
        self.metronome_menu.update_tone_color(
            colors.get(self.sound_tone, [0.8, 0.4, 0.8, 1])
        )
        self.load_sounds()
        if self.is_running:
            self.stop_metronome()
            self.start_metronome()
        self._show_temporary_hint(get_text('tone_' + self.sound_tone), 1.2)

    def toggle_metronome(self):
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
                self._show_temporary_hint(get_text('audio_error', 'Ошибка звука'), 1.5)
                return
        self.is_running = True
        self.tick_count = 0
        self.total_beats = 0
        self.subdivision_count = 0
        if hasattr(self, 'pendulum'):
            self.pendulum.start()
            self.pendulum.pendulum_color = (
                MetronomeColors.get_accent(settings_manager.theme)
                if self.is_accent_enabled else [0.6, 0.6, 0.6, 1]
            )
        self._show_indicators()
        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)
        self._tick()
        self._restart_tick_timer()
        self._show_temporary_hint(
            get_text('started', 'Запущен') + f": {self.bpm} BPM", 1.2
        )


    def _get_subdivisions_per_beat(self):
        mapping = {
            'none': 1,
            'eighth': 2,
            'triplet': 3,
            'sixteenth': 4,
        }
        return mapping.get(self.subdivision, 1)

    def _restart_tick_timer(self):
        if not self.is_running:
            return
        if self.tick_event:
            self.tick_event.cancel()
        subs = self._get_subdivisions_per_beat()
        interval = (60.0 / self.bpm) / subs
        self.tick_event = Clock.schedule_interval(self._tick, interval)


    def stop_metronome(self):
        if self.tick_event:
            self.tick_event.cancel()
            self.tick_event = None
        self.is_running = False
        self._hide_indicators()
        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)
        if hasattr(self, 'pendulum'):
            self.pendulum.stop()
        self.tick_count = 0
        self.total_beats = 0
        self.subdivision_count = 0
        self._show_temporary_hint(get_text('stopped', 'Остановлен'), 1.2)


    def on_enter(self):
        super().on_enter()

        self.update_theme_colors()
        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()
        if not self.is_running:
            self._hide_indicators()
        self._update_display()

    def on_size(self, *args):
        if hasattr(self, 'beats_per_measure'):
            Clock.schedule_once(
                lambda dt: self._update_indicators(self.beats_per_measure), 0.05
            )

    def on_leave(self):
        if self.is_running:
            self.stop_metronome()
        self._hide_hint()