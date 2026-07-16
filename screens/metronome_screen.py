# screens/metronome_screen.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Экран гитарного метронома с анимированным маятником
4 вертикальные шкалы + меню в стиле аккордов
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Ellipse, Rotate, PushMatrix, PopMatrix
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
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


# ============ ГЕНЕРАТОРЫ ЗВУКА ============
def get_temp_path():
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except:
            pass
    return tempfile.gettempdir()


def generate_click_sound(frequency=1200, duration=0.05, sample_rate=44100, volume=0.8, waveform='sine'):
    num_samples = int(sample_rate * duration)
    audio_data = array.array('h')
    for i in range(num_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 30)
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
    return generate_click_sound(frequency, duration, sample_rate, volume, waveform)


def generate_subdivision_sound(frequency=800, duration=0.03, sample_rate=44100, volume=0.5, waveform='sine'):
    return generate_click_sound(frequency, duration, sample_rate, volume, waveform)


def generate_mechanical_click(is_accent=False, sample_rate=44100, volume=0.8):
    freq = 1600 if is_accent else 1200
    duration = 0.055 if is_accent else 0.035
    return generate_click_sound(freq, duration, sample_rate, volume, 'sine')


# ============ МАЯТНИК ============
class MetronomePendulum(Widget):
    angle = NumericProperty(0)
    max_angle = NumericProperty(0.5)
    is_running = BooleanProperty(False)
    bpm = NumericProperty(120)
    pendulum_color = ListProperty([0.46, 0.70, 0.71, 1])
    glow_color = ListProperty([0.46, 0.70, 0.71, 0.3])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._update_clock = None
        self._current_amplitude = 0.4
        self._angle_velocity = 0
        self.size_hint = (1, 1)
        Clock.schedule_interval(self._update_pendulum, 1 / 60.0)

    def start(self):
        self.is_running = True
        self._animate_swing()

    def stop(self):
        self.is_running = False
        if self._update_clock:
            try:
                Clock.unschedule(self._update_clock)
                self._update_clock = None
            except:
                pass

    def _animate_swing(self):
        if not self.is_running:
            return

        if self._update_clock:
            try:
                Clock.unschedule(self._update_clock)
                self._update_clock = None
            except:
                pass

        period = 60.0 / self.bpm

        if self.bpm < 60:
            amplitude = self.max_angle
        elif self.bpm < 120:
            amplitude = self.max_angle * (1 - (self.bpm - 60) / 60 * 0.3)
        elif self.bpm < 180:
            amplitude = self.max_angle * (0.7 - (self.bpm - 120) / 60 * 0.2)
        else:
            amplitude = self.max_angle * 0.5

        self._current_amplitude = amplitude

        def update_angle(dt):
            if not self.is_running:
                return False
            time = Clock.get_time()
            self.angle = self._current_amplitude * math.sin(2 * math.pi * time / period)
            return True

        self._update_clock = Clock.schedule_interval(update_angle, 1 / 60.0)

    def _update_pendulum(self, dt):
        if not self.is_running and self._angle_velocity != 0:
            self._angle_velocity *= 0.98
            self.angle += self._angle_velocity * dt
            if abs(self._angle_velocity) < 0.001:
                self._angle_velocity = 0
                self.angle = 0

    def on_bpm(self, instance, value):
        if self.is_running:
            self.stop()
            Clock.schedule_once(lambda dt: self.start(), 0.1)

    def on_size(self, *args):
        self.draw_pendulum()

    def draw_pendulum(self):
        self.canvas.clear()
        with self.canvas:
            w = self.width
            h = self.height
            if w < 10 or h < 10:
                return

            center_x = w / 2
            center_y = h * 0.82
            pendulum_length = min(w, h) * 0.65
            bob_radius = min(w, h) * 0.09

            # Тень
            Color(0, 0, 0, 0.15)
            Ellipse(
                pos=(center_x - bob_radius * 1.2, center_y - pendulum_length - bob_radius * 0.4),
                size=(bob_radius * 2.4, bob_radius * 0.4)
            )

            # Свечение
            Color(*self.glow_color)
            Ellipse(
                pos=(center_x - bob_radius * 1.8, center_y - pendulum_length - bob_radius * 1.8),
                size=(bob_radius * 3.6, bob_radius * 3.6)
            )

            # Корпус
            PushMatrix()
            Rotate(origin=(center_x, center_y), angle=math.degrees(self.angle))

            # Стержень
            Color(0.2, 0.2, 0.3, 0.7)
            Line(
                points=[center_x, center_y, center_x, center_y - pendulum_length],
                width=2,
                cap='round'
            )

            Color(*self.pendulum_color)
            Line(
                points=[center_x, center_y, center_x, center_y - pendulum_length],
                width=1.2,
                cap='round'
            )

            # Грузик
            Color(0.3, 0.3, 0.4, 0.9)
            Ellipse(
                pos=(center_x - bob_radius, center_y - pendulum_length - bob_radius),
                size=(bob_radius * 2, bob_radius * 2)
            )

            Color(*self.pendulum_color)
            Ellipse(
                pos=(center_x - bob_radius * 0.7, center_y - pendulum_length - bob_radius * 0.7),
                size=(bob_radius * 1.4, bob_radius * 1.4)
            )

            Color(1, 1, 1, 0.25)
            Ellipse(
                pos=(center_x - bob_radius * 0.35, center_y - pendulum_length + bob_radius * 0.2),
                size=(bob_radius * 0.7, bob_radius * 0.4)
            )

            # Точка подвеса
            Color(0.3, 0.3, 0.4, 0.7)
            Ellipse(pos=(center_x - 5, center_y - 5), size=(10, 10))

            Color(*self.pendulum_color)
            Ellipse(pos=(center_x - 3, center_y - 3), size=(6, 6))

            PopMatrix()

    def on_angle(self, instance, value):
        self.draw_pendulum()


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
        self.size_hint = (1, 1)
        self.spacing = dp(1)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]

        self.value_label = MDLabel(
            text=str(int(initial)),
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(28),
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
            width=dp(16),
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

        self.label = MDLabel(
            text=label_text,
            font_size=sp(9),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(16),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            bold=True
        )

        self.add_widget(self.value_label)
        self.add_widget(self.slider)
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

    def set_value(self, new_value):
        if new_value < self.min_value:
            new_value = self.min_value
        elif new_value > self.max_value:
            new_value = self.max_value

        rounded = round(new_value / self.step) * self.step
        self.slider.value = rounded
        self.value = rounded
        self.value_label.text = str(int(rounded))

    def get_value(self):
        return self.value


# ============ МЕНЮ ============
class IconMenuItem(ButtonBehavior, MDBoxLayout):
    def __init__(self, icon_name, on_press=None, icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press

        if icon_color is None:
            self.icon_color = [1, 1, 1, 0.7]
        else:
            self.icon_color = icon_color

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = dp(0)
        self.md_bg_color = [0, 0, 0, 0]

        self.icon_btn = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(dp(30), dp(30)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            theme_icon_color="Custom",
            icon_color=self.icon_color,
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0
        )
        self.icon_btn.bind(on_release=self._on_press)
        self.add_widget(self.icon_btn)

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
        self.height = dp(50)
        self.radius = [0, 0, 0, 0]
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.padding = [dp(4), dp(2), dp(4), dp(2)]
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
            icon_color=play_color
        )

        self.reset_item = IconMenuItem(
            icon_name="refresh",
            on_press=self._on_reset,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )

        accent_icon = "music-note" if self.is_accent_enabled else "music-note-off"
        accent_color = [0.46, 0.70, 0.71, 1] if self.is_accent_enabled else [0.6, 0.6, 0.6, 0.5]
        self.accent_item = IconMenuItem(
            icon_name=accent_icon,
            on_press=self._on_accent,
            icon_color=accent_color
        )

        self.tone_item = IconMenuItem(
            icon_name="speaker",
            on_press=self._on_tone,
            icon_color=[0.8, 0.4, 0.8, 1]
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


# ============ ОСНОВНОЙ ЭКРАН ============
class MetronomeScreen(BaseScreen):
    DEFAULT_BPM = 120
    DEFAULT_BEATS = 4
    DEFAULT_SUBDIVISION = 0
    DEFAULT_VOLUME = 50
    DEFAULT_ACCENT = True
    DEFAULT_TONE = 'mechanical'

    SOUND_TONES = {
        'mechanical': {'name': 'Механический', 'type': 'mechanical'},
        'electronic': {'name': 'Электронный', 'type': 'synthetic', 'waveform': 'sine', 'freq': 1200,
                       'accent_freq': 1800},
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
        try:
            tone = self.SOUND_TONES.get(self.sound_tone, self.SOUND_TONES['mechanical'])
            accent_volume = 1.0 if self.is_accent_enabled else 0.0

            if self.sound_tone == 'mechanical':
                self.click_sound = generate_mechanical_click(is_accent=False, volume=self.volume)
                self.accent_sound = generate_mechanical_click(is_accent=True, volume=accent_volume)
                self.subdivision_sound = generate_mechanical_click(is_accent=False, volume=self.volume * 0.5)
            else:
                waveform = tone.get('waveform', 'sine')
                self.click_sound = generate_click_sound(tone['freq'], 0.05, 44100, self.volume, waveform)
                self.accent_sound = generate_accent_sound(tone['accent_freq'], 0.08, 44100, accent_volume, waveform)
                self.subdivision_sound = generate_subdivision_sound(tone['freq'] * 0.7, 0.03, 44100, self.volume * 0.6,
                                                                    waveform)

            logger.info(f"✅ Звуки загружены (тембр: {tone['name']})")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки звуков: {e}")

    def init_ui(self):
        # Главный layout с отступами
        main_layout = BoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ (под TopNav)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Нижний отступ (над BottomNav)
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(8)

        # Основной контент
        content = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(10), dp(4), dp(10), total_bottom],
            spacing=dp(6)
        )

        # ===== МАЯТНИК (35% высоты) =====
        pendulum_container = MDCard(
            orientation='vertical',
            size_hint=(1, 0.35),
            padding=[dp(6), dp(2), dp(6), dp(2)],
            radius=[dp(14), dp(14), dp(14), dp(14)],
            md_bg_color=[0, 0, 0, 0.05],
            elevation=0,
            line_color=[1, 1, 1, 0.1],
            line_width=0.5
        )

        self.pendulum = MetronomePendulum(bpm=self.DEFAULT_BPM, size_hint=(1, 1))
        pendulum_container.add_widget(self.pendulum)

        # BPM поверх маятника
        self.bpm_label = MDLabel(
            text=str(self.DEFAULT_BPM),
            font_size=sp(28),
            halign="center",
            valign="top",
            size_hint=(1, None),
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True,
            pos_hint={'top': 1}
        )
        pendulum_container.add_widget(self.bpm_label)

        content.add_widget(pendulum_container)

        # ===== КАРТОЧКА СО СЛАЙДЕРАМИ (55% высоты) =====
        sliders_card = MDCard(
            orientation='vertical',
            size_hint=(1, 0.55),
            padding=[dp(4), dp(4), dp(4), dp(4)],
            radius=[dp(14), dp(14), dp(14), dp(14)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            line_color=[1, 1, 1, 0.1],
            line_width=0.5,
            spacing=dp(2)
        )

        # Слайдеры
        sliders_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.75),
            spacing=dp(4)
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

        sliders_row.add_widget(self.bpm_slider)
        sliders_row.add_widget(self.beat_slider)
        sliders_row.add_widget(self.subdivision_slider)
        sliders_row.add_widget(self.volume_slider)

        sliders_card.add_widget(sliders_row)

        # Разделитель - простой виджет
        divider = MDBoxLayout(
            size_hint=(1, None),
            height=dp(1),
            md_bg_color=[1, 1, 1, 0.15]
        )
        sliders_card.add_widget(divider)

        # Меню (25% от карточки)
        self.metronome_menu = MetronomeMenu(
            on_play_press=self.toggle_metronome,
            on_reset_press=self._reset_to_defaults,
            on_accent_press=self.toggle_accent,
            on_tone_press=self.cycle_tone,
            is_running=self.is_running,
            is_accent_enabled=self.is_accent_enabled,
            size_hint=(1, 0.25)
        )
        sliders_card.add_widget(self.metronome_menu)

        content.add_widget(sliders_card)

        # ===== ПОДСКАЗКА =====
        self._hint_label = MDLabel(
            text="",
            font_size=sp(10),
            halign="center",
            size_hint=(1, None),
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            opacity=0
        )
        content.add_widget(self._hint_label)

        # ===== ИНДИКАТОРЫ =====
        indicator_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(34),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        self.indicator_card = MDCard(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(3), dp(3), dp(3), dp(3)],
            radius=[dp(10), dp(10), dp(10), dp(10)],
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.1],
            line_width=0.5,
            spacing=dp(2),
            opacity=0
        )

        indicator_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=dp(2),
            padding=[dp(3), dp(3), dp(3), dp(3)]
        )

        self.beat_indicators = []
        for i in range(12):
            indicator = MDCard(
                size_hint=(None, None),
                size=(dp(22), dp(22)),
                radius=[dp(11)] * 4,
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
        content.add_widget(indicator_container)

        main_layout.add_widget(content)
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

        if hasattr(self, 'pendulum'):
            self.pendulum.bpm = self.DEFAULT_BPM

        self._update_display()
        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()
        self._hide_indicators()

        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)
        self.load_sounds()
        self._show_temporary_hint("Сброс")

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
        available_width = Window.width - dp(28) - dp(12) - dp(12) - dp(6)
        if available_width < dp(80):
            available_width = dp(80)

        spacing = dp(2)
        total_spacing = (count - 1) * spacing
        calculated_size = (available_width - total_spacing) / count

        if count <= 6:
            max_size = dp(22)
            min_size = dp(14)
        elif count <= 8:
            max_size = dp(20)
            min_size = dp(12)
        elif count <= 10:
            max_size = dp(18)
            min_size = dp(10)
        else:
            max_size = dp(16)
            min_size = dp(8)

        final_size = max(min(calculated_size, max_size), min_size)

        for i in range(12):
            if i < count:
                self.beat_indicators[i].size = (final_size, final_size)
                self.beat_indicators[i].radius = [final_size / 2] * 4
                self.beat_indicators[i].opacity = 1 if self.is_running else 0
            else:
                self.beat_indicators[i].opacity = 0

        self.indicator_card.opacity = 1 if self.is_running and count > 0 else 0
        self._update_beat_indicators()

    def _update_beat_indicators(self):
        for i in range(self.beats_per_measure):
            if i == 0 and self.is_accent_enabled:
                self.beat_indicators[i].md_bg_color = [0.46, 0.70, 0.71, 0.7]
            else:
                self.beat_indicators[i].md_bg_color = [0.3, 0.3, 0.3, 0.3]

    def _highlight_beat(self, beat_index):
        self._update_beat_indicators()
        if beat_index < len(self.beat_indicators):
            color = [0.46, 0.70, 0.71, 1.0] if (beat_index == 0 and self.is_accent_enabled) else [0.6, 0.6, 0.6, 0.8]
            self.beat_indicators[beat_index].md_bg_color = color

    def _show_indicators(self):
        self._update_indicators(self.beats_per_measure)

    def _hide_indicators(self):
        for indicator in self.beat_indicators:
            indicator.opacity = 0
            indicator.md_bg_color = [0.3, 0.3, 0.3, 0.3]
        self.indicator_card.opacity = 0

    def _update_display(self):
        subdivision_names = {'none': 'Нет', 'eighth': '1/8', 'triplet': '1/8T', 'sixteenth': '1/16'}
        sub_text = subdivision_names.get(self.subdivision, 'Нет')
        self._show_temporary_hint(f"{self.bpm} BPM | {self.beats_per_measure}/4 | {sub_text}", 1.5)
        if hasattr(self, 'bpm_label'):
            self.bpm_label.text = str(self.bpm)

    def _on_bpm_change(self, instance, value):
        self.bpm = int(value)
        if hasattr(self, 'pendulum'):
            self.pendulum.bpm = self.bpm
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
        self.sound_tone = tone_ids[(current_index + 1) % len(tone_ids)]

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

        if hasattr(self, 'pendulum'):
            self.pendulum.start()
            self.pendulum.pendulum_color = [0.46, 0.70, 0.71, 1] if self.is_accent_enabled else [0.6, 0.6, 0.6, 1]

        self._show_indicators()
        self.metronome_menu.update_state(self.is_running, self.is_accent_enabled)

        interval = 60.0 / self.bpm
        self._tick()
        self.tick_event = Clock.schedule_interval(self._tick, interval)

        self._show_temporary_hint(f"Запущен: {self.bpm} BPM", 1.2)

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
        self.subdivision_count = 0
        self._show_temporary_hint("Остановлен", 1.2)

    def _tick(self, dt=None):
        if not self.is_running:
            return

        is_main_beat = (self.subdivision_count == 0)
        is_accent = (is_main_beat and self.tick_count == 0)

        try:
            if is_accent and self.is_accent_enabled and self.accent_sound:
                self.accent_sound.play()
            elif is_main_beat and self.click_sound:
                self.click_sound.play()
            elif not is_main_beat and self.subdivision_sound:
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
        self._update_indicators(self.beats_per_measure)
        self._update_beat_indicators()
        if not self.is_running:
            self._hide_indicators()
        self._update_display()

    def on_size(self, *args):
        if hasattr(self, 'beats_per_measure'):
            Clock.schedule_once(lambda dt: self._update_indicators(self.beats_per_measure), 0.05)

    def on_leave(self):
        if self.is_running:
            self.stop_metronome()
        self._hide_hint()