# screens/metronome_screen.py
"""
Экран гитарного метронома с анимированным маятником,
карточкой слайдеров и адаптивными индикаторами
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Mesh
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, BooleanProperty, ListProperty
from kivy.core.audio import SoundLoader
from kivy.utils import get_color_from_hex, platform
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
from kivymd.uix.button import MDIconButton
from kivymd.uix.slider import MDSlider
from kivy.uix.behaviors import ButtonBehavior

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen

logger = screen_logger('Metronome')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


# ============ ФУНКЦИИ ДЛЯ ПУТЕЙ И ВРЕМЕННЫХ ФАЙЛОВ ============
def get_temp_path():
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except:
            pass
    return tempfile.gettempdir()


# ============ ГЕНЕРАТОРЫ ЗВУКА (из рабочего модуля) ============
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


# ============ РЕАЛИСТИЧНЫЙ МАЯТНИК (только визуальный, без звука) ============
class RealisticMetronome(Widget):
    angle = NumericProperty(0)
    bpm_value = NumericProperty(120)
    is_running = BooleanProperty(False)
    pendulum_color = ListProperty([0.46, 0.70, 0.71, 1])

    def __init__(self, **kwargs):
        super(RealisticMetronome, self).__init__(**kwargs)
        self._animation = None
        self.size_hint = (1, 1)
        self.bind(pos=self.render, size=self.render, angle=self.render, bpm_value=self.render)

    def render(self, *args):
        self.canvas.clear()

        cx = self.center_x
        base_y = self.y + 10
        w_base = min(self.width, self.height) * 0.7
        h_body = self.height - 30

        top_x, top_y = cx, base_y + h_body
        left_x, left_y = cx - w_base / 2, base_y
        right_x, right_y = cx + w_base / 2, base_y
        pivot_y = base_y + h_body * 0.22

        with self.canvas:
            Color(*get_color_from_hex('#3a1d11'))
            Mesh(vertices=[left_x, left_y, 0, 0, right_x, right_y, 0, 0, top_x, top_y, 0, 0],
                 indices=[0, 1, 2], mode='triangles')

            Color(0, 0, 0, 0.4)
            Line(points=[left_x, left_y, top_x, top_y, right_x, right_y], width=3)

            Color(*get_color_from_hex('#cd9a62'))
            scale_w = w_base * 0.22
            scale_ly, scale_hy = pivot_y - 10, top_y - 30
            Mesh(vertices=[cx - scale_w / 2, scale_ly, 0, 0, cx + scale_w / 2, scale_ly, 0, 0,
                           cx + scale_w / 3, scale_hy, 0, 0, cx - scale_w / 3, scale_hy, 0, 0],
                 indices=[0, 1, 2, 2, 3, 0], mode='triangles')

            Color(0.2, 0.1, 0, 0.6)
            for i in range(10):
                y_pos = scale_ly + (i / 9) * (scale_hy - scale_ly - 15)
                curr_w = (scale_w / 2) - (i / 9) * (scale_w / 6)
                Line(points=[cx - curr_w, y_pos, cx + curr_w, y_pos], width=1.2)

            rad = math.radians(self.angle + 90)
            rod_len = h_body * 0.65
            end_x = cx + rod_len * math.cos(rad)
            end_y = pivot_y + rod_len * math.sin(rad)

            Color(*get_color_from_hex('#7f8c8d'))
            Line(points=[cx, pivot_y, end_x, end_y], width=2.5)
            Color(*get_color_from_hex('#ffffff'))
            Line(points=[cx, pivot_y, end_x, end_y], width=0.8)

            bpm_pct = (self.bpm_value - 40) / (210 - 40)
            bpm_pct = max(0, min(1, bpm_pct))
            weight_dist = rod_len * (0.9 - (bpm_pct * 0.55))
            wx = cx + weight_dist * math.cos(rad)
            wy = pivot_y + weight_dist * math.sin(rad)

            color = self.pendulum_color
            Color(color[0], color[1], color[2], 1)
            Line(circle=(wx, wy, 10), width=14, joint='round')

            Color(*get_color_from_hex('#fef08a'))
            Line(circle=(wx - 2, wy + 2, 5), width=5, joint='round')

            Color(*get_color_from_hex('#78350f'))
            Line(circle=(wx, wy, 11), width=1.5)

            Color(*get_color_from_hex('#5c2e16'))
            Mesh(vertices=[left_x, left_y, 0, 0, cx - scale_w / 2 - 4, scale_ly, 0, 0,
                           cx - scale_w / 3 - 4, scale_hy, 0, 0, top_x, top_y, 0, 0],
                 indices=[0, 1, 2, 2, 3, 0], mode='triangles')
            Mesh(vertices=[right_x, right_y, 0, 0, cx + scale_w / 2 + 4, scale_ly, 0, 0,
                           cx + scale_w / 3 + 4, scale_hy, 0, 0, top_x, top_y, 0, 0],
                 indices=[0, 1, 2, 2, 3, 0], mode='triangles')
            Mesh(vertices=[left_x, left_y, 0, 0, right_x, right_y, 0, 0,
                           cx + scale_w / 2 + 4, scale_ly, 0, 0, cx - scale_w / 2 - 4, scale_ly, 0, 0],
                 indices=[0, 1, 2, 2, 3, 0], mode='triangles')

            Color(*get_color_from_hex('#1a1a1a'))
            Line(circle=(cx, pivot_y, 7), width=8, joint='round')
            Color(*get_color_from_hex('#8a8a8a'))
            Line(circle=(cx, pivot_y, 3), width=4, joint='round')

    def start(self):
        self.is_running = True
        self._animate_swing()

    def stop(self):
        self.is_running = False
        if self._animation:
            self._animation.cancel_all(self)
            self._animation = None
        anim_center = Animation(angle=0, duration=0.2, transition='out_quad')
        anim_center.start(self)

    def _animate_swing(self):
        if not self.is_running:
            return

        duration = 60.0 / self.bpm_value
        target_angle = 28 if self.angle <= 0 else -28

        self._animation = Animation(angle=target_angle, duration=duration, transition='in_out_quad')
        self._animation.bind(on_complete=self._on_swing_complete)
        self._animation.start(self)

    def _on_swing_complete(self, animation, widget):
        if self.is_running:
            # Маятник просто продолжает качаться, звук идёт от _tick()
            self._animate_swing()

    def on_bpm_value(self, instance, value):
        if self.is_running:
            self.stop()
            Clock.schedule_once(lambda dt: self.start(), 0.1)


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
        self.width = dp(70)
        self.height = dp(280)
        self.spacing = dp(2)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]

        slider_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(16), dp(2), dp(16), dp(2)]
        )

        self.value_label = MDLabel(
            text=str(int(initial)),
            font_size=sp(20),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        self.slider = MDSlider(
            min=min_value - 0.01,
            max=max_value + 0.01,
            value=initial,
            step=step,
            size_hint=(None, 1),
            width=dp(18),
            orientation='vertical',
            pos_hint={'center_x': 0.5},
            hint=False
        )
        self.slider.ripple_scale = 0

        bi_color = [0.46, 0.70, 0.71, 1]
        self.slider.thumb_color_active = bi_color
        self.slider.thumb_color_inactive = bi_color
        self.slider.track_color_active = [0.46, 0.70, 0.71, 0.6]
        self.slider.track_color_inactive = [1, 1, 1, 0.2]

        self.slider.bind(value=self._on_value_change)

        self.value_below = MDLabel(
            text=str(int(initial)),
            font_size=sp(14),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        self.label = MDLabel(
            text=label_text,
            font_size=sp(10),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            bold=True
        )

        slider_container.add_widget(self.value_label)
        slider_container.add_widget(self.slider)

        self.add_widget(slider_container)
        self.add_widget(self.value_below)
        self.add_widget(self.label)

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
        if new_value < self.min_value:
            new_value = self.min_value
        elif new_value > self.max_value:
            new_value = self.max_value

        rounded = round(new_value / self.step) * self.step
        self.slider.value = rounded
        self.value = rounded
        self.value_label.text = str(int(rounded))
        self.value_below.text = str(int(rounded))

    def get_value(self):
        return self.value


# ============ МЕНЮ МЕТРОНОМА ============
class IconMenuItem(ButtonBehavior, MDBoxLayout):
    def __init__(self, icon_name, on_press=None, icon_color=None, fixed_color=False, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press
        self.fixed_color = fixed_color

        if icon_color is None:
            self.icon_color = [1, 1, 1, 0.7]
        else:
            self.icon_color = icon_color

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = [dp(4), dp(6), dp(4), dp(6)]
        self.spacing = dp(0)
        self.md_bg_color = [0, 0, 0, 0]

        self.icon_btn = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            theme_icon_color="Custom",
            icon_color=self.icon_color,
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0
        )
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


class MetronomeMenu(MDCard):
    def __init__(self,
                 on_play_press=None,
                 on_reset_press=None,
                 on_accent_press=None,
                 on_tone_press=None,
                 is_running=False,
                 is_accent_enabled=True,
                 **kwargs):
        super().__init__(**kwargs)

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.radius = [0, 0, 0, 0]
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        self.on_play_press = on_play_press
        self.on_reset_press = on_reset_press
        self.on_accent_press = on_accent_press
        self.on_tone_press = on_tone_press

        self.is_running = is_running
        self.is_accent_enabled = is_accent_enabled

        self._build_ui()

    def _build_ui(self):
        play_icon = "stop" if self.is_running else "play"
        play_color = [0.8, 0.3, 0.3, 1] if self.is_running else [0.46, 0.70, 0.71, 1]
        self.play_item = IconMenuItem(
            icon_name=play_icon,
            on_press=self._on_play,
            icon_color=play_color,
            fixed_color=True
        )

        self.reset_item = IconMenuItem(
            icon_name="refresh",
            on_press=self._on_reset,
            icon_color=[0.9, 0.7, 0.2, 0.9],
            fixed_color=True
        )

        accent_icon = "music-note" if self.is_accent_enabled else "music-note-off"
        accent_color = [0.46, 0.70, 0.71, 1] if self.is_accent_enabled else [0.6, 0.6, 0.6, 0.5]
        self.accent_item = IconMenuItem(
            icon_name=accent_icon,
            on_press=self._on_accent,
            icon_color=accent_color,
            fixed_color=True
        )

        self.tone_item = IconMenuItem(
            icon_name="speaker",
            on_press=self._on_tone,
            icon_color=[0.8, 0.4, 0.8, 1],
            fixed_color=True
        )

        self.add_widget(self.play_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.reset_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.accent_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.tone_item)

    def _create_divider(self):
        return MDBoxLayout(
            size_hint_x=None,
            width=dp(1),
            md_bg_color=[1, 1, 1, 0.1]
        )

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

        play_icon = "stop" if is_running else "play"
        play_color = [0.8, 0.3, 0.3, 1] if is_running else [0.46, 0.70, 0.71, 1]
        self.play_item.set_icon(play_icon)
        self.play_item.set_color(play_color)

        accent_icon = "music-note" if is_accent_enabled else "music-note-off"
        accent_color = [0.46, 0.70, 0.71, 1] if is_accent_enabled else [0.6, 0.6, 0.6, 0.5]
        self.accent_item.set_icon(accent_icon)
        self.accent_item.set_color(accent_color)

    def update_tone_color(self, color):
        self.tone_item.set_color(color)


# ============ ОСНОВНОЙ ЭКРАН МЕТРОНОМА ============
class MetronomeScreen(BaseScreen):
    DEFAULT_BPM = 120
    DEFAULT_BEATS = 4
    DEFAULT_SUBDIVISION = 0
    DEFAULT_VOLUME = 50
    DEFAULT_ACCENT = True
    DEFAULT_TONE = 'mechanical'

    SOUND_TONES = {
        'mechanical': {'name': 'Механический', 'type': 'mechanical'},
        'electronic': {'name': 'Электронный', 'type': 'synthetic', 'waveform': 'sine', 'freq': 1200, 'accent_freq': 1800},
        'wood': {'name': 'Деревянный', 'type': 'synthetic', 'waveform': 'triangle', 'freq': 800, 'accent_freq': 1200},
        'click': {'name': 'Щелчок', 'type': 'synthetic', 'waveform': 'square', 'freq': 600, 'accent_freq': 900},
        'beep': {'name': 'Пищалка', 'type': 'synthetic', 'waveform': 'sawtooth', 'freq': 1500, 'accent_freq': 2200},
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'metronome'
        self.bg_image = None

        self.bpm = self.DEFAULT_BPM
        self.beats_per_measure = self.DEFAULT_BEATS
        self.subdivision = 'none'
        self.sound_tone = self.DEFAULT_TONE
        self.volume = self.DEFAULT_VOLUME / 100.0
        self.is_accent_enabled = self.DEFAULT_ACCENT
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

        logger.info('Экран метронома создан (с маятником)')

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
        try:
            tone = self.SOUND_TONES.get(self.sound_tone, self.SOUND_TONES['mechanical'])
            accent_volume = 1.0 if self.is_accent_enabled else 0.0

            if self.sound_tone == 'mechanical':
                self.click_sound = generate_mechanical_click(is_accent=False, volume=self.volume)
                self.accent_sound = generate_mechanical_click(is_accent=True, volume=accent_volume)
                self.subdivision_sound = generate_mechanical_click(is_accent=False, volume=self.volume * 0.5)
            else:
                waveform = tone['waveform']
                self.click_sound = generate_click_sound(tone['freq'], 0.05, 44100, self.volume, waveform)
                self.accent_sound = generate_accent_sound(tone['accent_freq'], 0.08, 44100, accent_volume, waveform)
                self.subdivision_sound = generate_subdivision_sound(tone['freq'] * 0.7, 0.03, 44100, self.volume * 0.6, waveform)

            logger.info(f"✅ Звуки загружены (тембр: {tone['name']})")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки звуков: {e}")

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
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )

        # === ВЕРХНЯЯ ЧАСТЬ: КАРТОЧКА СО СЛАЙДЕРАМИ + МЕНЮ ===
        top_section = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(360),
            spacing=dp(2)
        )

        unified_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(2), dp(2), dp(2), dp(2)],
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=[0, 0, 0, 0.1],
            elevation=0,
            line_color=[1, 1, 1, 0.15],
            line_width=0.8,
            spacing=0
        )

        sliders_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(270),
            spacing=dp(2)
        )

        self.bpm_slider = VerticalSlider(
            label_text="BPM",
            min_value=30,
            max_value=250,
            initial=self.DEFAULT_BPM,
            step=1
        )
        self.bpm_slider.bind(value=self._on_bpm_change)

        self.beat_slider = VerticalSlider(
            label_text="BEAT",
            min_value=2,
            max_value=12,
            initial=self.DEFAULT_BEATS,
            step=1
        )
        self.beat_slider.bind(value=self._on_beat_change)

        self.subdivision_slider = VerticalSlider(
            label_text="SUB",
            min_value=0,
            max_value=3,
            initial=self.DEFAULT_SUBDIVISION,
            step=1
        )
        self.subdivision_slider.bind(value=self._on_subdivision_change)

        self.volume_slider = VerticalSlider(
            label_text="VOL",
            min_value=0,
            max_value=100,
            initial=self.DEFAULT_VOLUME,
            step=5
        )
        self.volume_slider.bind(value=self._on_volume_change)

        sliders_layout.add_widget(Widget(size_hint_x=0.05))
        sliders_layout.add_widget(self.bpm_slider)
        sliders_layout.add_widget(Widget(size_hint_x=0.02))
        sliders_layout.add_widget(self.beat_slider)
        sliders_layout.add_widget(Widget(size_hint_x=0.02))
        sliders_layout.add_widget(self.subdivision_slider)
        sliders_layout.add_widget(Widget(size_hint_x=0.02))
        sliders_layout.add_widget(self.volume_slider)
        sliders_layout.add_widget(Widget(size_hint_x=0.05))

        unified_card.add_widget(sliders_layout)

        divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(1),
            md_bg_color=[1, 1, 1, 0.15],
            padding=[dp(12), 0, dp(12), 0]
        )
        unified_card.add_widget(divider)

        self.metronome_menu = MetronomeMenu(
            on_play_press=self.toggle_metronome,
            on_reset_press=self._reset_to_defaults,
            on_accent_press=self.toggle_accent,
            on_tone_press=self.cycle_tone,
            is_running=self.is_running,
            is_accent_enabled=self.is_accent_enabled
        )
        unified_card.add_widget(self.metronome_menu)

        top_section.add_widget(unified_card)

        self._hint_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            opacity=0
        )
        top_section.add_widget(self._hint_label)

        content_container.add_widget(top_section)

        # === ИНДИКАТОРЫ ===
        indicator_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(52),
            padding=[dp(6), dp(2), dp(6), dp(2)],
            md_bg_color=[0, 0, 0, 0]
        )

        self.indicator_card = MDCard(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(4), dp(4), dp(4), dp(4)],
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.12],
            line_width=0.5,
            spacing=dp(4),
            opacity=0
        )

        indicator_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=dp(4),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )

        self.beat_indicators = []
        initial_size = dp(36)
        for i in range(12):
            indicator = MDCard(
                size_hint=(None, None),
                size=(initial_size, initial_size),
                radius=[initial_size / 2] * 4,
                md_bg_color=[0.3, 0.3, 0.3, 0.3],
                elevation=0,
                opacity=0,
                line_color=[1, 1, 1, 0.1],
                line_width=0.3
            )
            self.beat_indicators.append(indicator)
            indicator_layout.add_widget(indicator)

        self.indicator_card.add_widget(indicator_layout)
        indicator_container.add_widget(self.indicator_card)
        content_container.add_widget(indicator_container)

        # === МАЯТНИК (всё оставшееся место) ===
        pendulum_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        self.pendulum = RealisticMetronome(
            bpm_value=self.DEFAULT_BPM,
            size_hint=(1, 1)
        )
        pendulum_container.add_widget(self.pendulum)
        content_container.add_widget(pendulum_container)

        main_layout.add_widget(content_container)
        self.add_widget(main_layout)

        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()
        self._hide_indicators()
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
        self.metronome_menu.update_tone_color([0.8, 0.6, 0.2, 1])

        self.load_sounds()
        self._show_temporary_hint("Сброс")
        logger.info("🔄 Настройки сброшены к стандартным")

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

    def _update_indicators(self, count):
        if count < 2:
            count = 2
        if count > 12:
            count = 12

        from kivy.core.window import Window
        available_width = Window.width - dp(32) - dp(16) - dp(16) - dp(8)
        if available_width < dp(100):
            available_width = dp(100)

        spacing = dp(4)
        total_spacing = (count - 1) * spacing
        calculated_size = (available_width - total_spacing) / count

        if count <= 6:
            max_size = dp(36)
            min_size = dp(20)
        elif count <= 8:
            max_size = dp(32)
            min_size = dp(18)
        elif count <= 10:
            max_size = dp(28)
            min_size = dp(16)
        else:
            max_size = dp(24)
            min_size = dp(14)

        final_size = max(min(calculated_size, max_size), min_size)

        for i in range(12):
            if i < count:
                self.beat_indicators[i].size = (final_size, final_size)
                self.beat_indicators[i].radius = [final_size / 2] * 4
                self.beat_indicators[i].opacity = 1 if self.is_running else 0
                self.beat_indicators[i].disabled = False
            else:
                self.beat_indicators[i].opacity = 0
                self.beat_indicators[i].disabled = True

        if self.is_running and count > 0:
            self.indicator_card.opacity = 1
        else:
            self.indicator_card.opacity = 0

        self._update_beat_indicators()

    def _update_beat_indicators(self):
        for i in range(self.beats_per_measure):
            if i == 0 and self.is_accent_enabled:
                self.beat_indicators[i].md_bg_color = [0.46, 0.70, 0.71, 0.7]
            else:
                self.beat_indicators[i].md_bg_color = [0.3, 0.3, 0.3, 0.3]

        for i in range(self.beats_per_measure, 12):
            self.beat_indicators[i].opacity = 0

    def _highlight_beat(self, beat_index):
        self._update_beat_indicators()
        if beat_index == 0 and self.is_accent_enabled:
            color = [0.46, 0.70, 0.71, 1.0]
        else:
            color = [0.6, 0.6, 0.6, 0.8]

        if beat_index < len(self.beat_indicators):
            self.beat_indicators[beat_index].md_bg_color = color

    def _show_indicators(self):
        self._update_indicators(self.beats_per_measure)

    def _hide_indicators(self):
        for indicator in self.beat_indicators:
            indicator.opacity = 0
            indicator.md_bg_color = [0.3, 0.3, 0.3, 0.3]
        self.indicator_card.opacity = 0

    def _update_subdivision_label(self, value):
        subdivision_names = ['Нет', '1/8', '1/8T', '1/16']
        if 0 <= int(value) <= 3:
            self.subdivision_slider.value_label.text = subdivision_names[int(value)]
            self.subdivision_slider.value_below.text = subdivision_names[int(value)]

    def _update_display(self):
        subdivision_names = {'none': 'Нет', 'eighth': '1/8', 'triplet': '1/8T', 'sixteenth': '1/16'}
        sub_text = subdivision_names.get(self.subdivision, 'Нет')
        self._show_temporary_hint(f"{self.bpm} BPM | {self.beats_per_measure}/4 | {sub_text}", 1.5)

    def _on_bpm_change(self, instance, value):
        self.bpm = int(value)
        if hasattr(self, 'pendulum'):
            self.pendulum.bpm_value = self.bpm
        self._update_display()
        if self.is_running:
            self.stop_metronome()
            self.start_metronome()

    def _on_beat_change(self, instance, value):
        self.beats_per_measure = int(value)
        self._update_display()
        self._update_indicators(self.beats_per_measure)
        self.tick_count = 0
        if self.is_running:
            self._update_beat_indicators()

    def _on_subdivision_change(self, instance, value):
        self.subdivision = ['none', 'eighth', 'triplet', 'sixteenth'][int(value)]
        self._update_subdivision_label(value)
        self._update_display()

    def _on_volume_change(self, instance, value):
        self.volume = float(value) / 100.0
        self.load_sounds()

    def toggle_accent(self):
        self.is_accent_enabled = not self.is_accent_enabled
        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)
        self.load_sounds()
        if self.is_running:
            self.stop_metronome()
            self.start_metronome()
        self._show_temporary_hint(f"Акцент: {'ВКЛ' if self.is_accent_enabled else 'ВЫКЛ'}", 1.2)

    def cycle_tone(self):
        tone_ids = list(self.SOUND_TONES.keys())
        current_index = tone_ids.index(self.sound_tone)
        next_index = (current_index + 1) % len(tone_ids)
        self.sound_tone = tone_ids[next_index]

        colors = {
            'mechanical': [0.8, 0.6, 0.2, 1],
            'electronic': [0.46, 0.70, 0.71, 1],
            'wood': [0.6, 0.4, 0.2, 1],
            'click': [0.8, 0.8, 0.8, 1],
            'beep': [0.9, 0.2, 0.9, 1],
        }
        self.metronome_menu.update_tone_color(colors.get(self.sound_tone, [0.8, 0.4, 0.8, 1]))

        self.load_sounds()
        if self.is_running:
            self.stop_metronome()
            self.start_metronome()

        tone_data = self.SOUND_TONES.get(self.sound_tone, self.SOUND_TONES['mechanical'])
        self._show_temporary_hint(tone_data['name'], 1.2)

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
                self._show_temporary_hint("Ошибка звука", 1.5)
                return

        self.is_running = True
        self.tick_count = 0
        self.subdivision_count = 0

        # Запускаем маятник
        if hasattr(self, 'pendulum'):
            self.pendulum.start()
            if self.is_accent_enabled:
                self.pendulum.pendulum_color = [0.46, 0.70, 0.71, 1]
            else:
                self.pendulum.pendulum_color = [0.6, 0.6, 0.6, 1]

        # Показываем индикаторы
        self._show_indicators()
        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)

        # ЗАПУСКАЕМ ТАЙМЕР КАК В РАБОЧЕМ МОДУЛЕ
        interval = 60.0 / self.bpm
        self._tick()  # первый тик сразу
        self.tick_event = Clock.schedule_interval(self._tick, interval)

        self._show_temporary_hint(f"Запущен: {self.bpm} BPM", 1.2)
        logger.info(f"✅ Метроном запущен: {self.bpm} BPM, {self.beats_per_measure}/4")

    def stop_metronome(self):
        # Останавливаем таймер
        if self.tick_event:
            self.tick_event.cancel()
            self.tick_event = None

        self.is_running = False
        self._hide_indicators()
        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)

        # Останавливаем маятник
        if hasattr(self, 'pendulum'):
            self.pendulum.stop()

        self.tick_count = 0
        self.subdivision_count = 0

        self._show_temporary_hint("Остановлен", 1.2)
        logger.info("⏹ Метроном остановлен")

    def _tick(self, dt=None):
        """Тик метронома - полностью из рабочего модуля"""
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

    def on_enter(self):
        logger.info("Вход в экран метронома")
        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()
        if not self.is_running:
            self._hide_indicators()
        self._update_display()

    def on_size(self, *args):
        if hasattr(self, 'beats_per_measure'):
            Clock.schedule_once(lambda dt: self._update_indicators(self.beats_per_measure), 0.05)

    def on_leave(self):
        logger.info("Выход из экрана метронома")
        if self.is_running:
            self.stop_metronome()
        self._hide_hint()