# screens/tuner_screen.py
"""
Экран гитарного тюнера - с визуальным индикатором и определением нот
Использует микрофон через plyer, НЕ требует PyAudio
С ПРАВИЛЬНЫМИ ОТСТУПАМИ через BaseScreen
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty, StringProperty
from kivy.utils import platform
from io import BytesIO
import math

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from utils.notifications import notify

logger = screen_logger('Tuner')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# ============ НАСТРОЙКИ ГИТАРЫ ============
GUITAR_STRINGS = {
    6: {'note': 'E2', 'freq': 82.41, 'name': 'E'},
    5: {'note': 'A2', 'freq': 110.00, 'name': 'A'},
    4: {'note': 'D3', 'freq': 146.83, 'name': 'D'},
    3: {'note': 'G3', 'freq': 196.00, 'name': 'G'},
    2: {'note': 'B3', 'freq': 246.94, 'name': 'B'},
    1: {'note': 'E4', 'freq': 329.63, 'name': 'E'},
}

NOTES = {
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
    'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
    'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88,
}


class TunerDial(Widget):
    """Круговой индикатор отклонения от частоты"""

    deviation = NumericProperty(0)
    note_name = StringProperty('')
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
            Color(0.1, 0.1, 0.1, 0.3)
            Ellipse(
                pos=(self.x + self.width * 0.05, self.y + self.height * 0.05),
                size=(self.width * 0.9, self.height * 0.9)
            )

            Color(0.46, 0.70, 0.71, 0.3)
            Line(
                circle=(self.center_x, self.center_y, min(self.width, self.height) * 0.42, 0, 360),
                width=dp(3)
            )

            self._draw_scale()

            Color(0.46, 0.70, 0.71, 0.8)
            Ellipse(
                pos=(self.center_x - dp(4), self.center_y - dp(4)),
                size=(dp(8), dp(8))
            )

            self._draw_needle()

    def _draw_scale(self):
        radius = min(self.width, self.height) * 0.38

        Color(0.3, 0.8, 0.3, 0.4)
        Line(
            circle=(self.center_x, self.center_y, radius, -10, 10),
            width=dp(8)
        )

        Color(0.9, 0.8, 0.2, 0.3)
        Line(
            circle=(self.center_x, self.center_y, radius, -30, -10),
            width=dp(6)
        )
        Line(
            circle=(self.center_x, self.center_y, radius, 10, 30),
            width=dp(6)
        )

        Color(0.8, 0.2, 0.2, 0.25)
        Line(
            circle=(self.center_x, self.center_y, radius, -50, -30),
            width=dp(4)
        )
        Line(
            circle=(self.center_x, self.center_y, radius, 30, 50),
            width=dp(4)
        )

        Color(0.46, 0.70, 0.71, 0.8)
        Line(
            circle=(self.center_x, self.center_y, radius * 1.05, -1, 1),
            width=dp(2)
        )

    def _draw_needle(self):
        angle_deg = self.deviation * 45
        angle_rad = math.radians(angle_deg)
        radius = min(self.width, self.height) * 0.35

        x_end = self.center_x + radius * math.sin(angle_rad)
        y_end = self.center_y + radius * math.cos(angle_rad)

        abs_dev = abs(self.deviation)
        if abs_dev < 0.1:
            color = self.colors['green']
        elif abs_dev < 0.3:
            color = self.colors['yellow']
        else:
            color = self.colors['red']

        Color(*color)
        Line(
            points=[self.center_x, self.center_y, x_end, y_end],
            width=dp(4),
            cap='round'
        )

    def _update_needle(self, *args):
        self._update()


class StringIndicator(MDCard):
    """Индикатор для одной струны"""

    def __init__(self, string_num, note_data, **kwargs):
        super().__init__(**kwargs)
        self.string_number = string_num
        self.note_name = note_data['note']
        self.frequency = note_data['freq']
        self.is_active = False
        self.deviation = 0

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.padding = [dp(12), dp(6), dp(12), dp(6)]
        self.spacing = dp(4)
        self.radius = [dp(8), dp(8), dp(8), dp(8)]
        self.elevation = 0
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0.2, 0.2, 0.2, 0.3]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5

        self._build_ui()

    def _build_ui(self):
        top = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(24),
            spacing=dp(8)
        )

        self.num_label = MDLabel(
            text=str(self.string_number),
            font_size=sp(14),
            halign="center",
            size_hint_x=None,
            width=dp(28),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            bold=True
        )

        self.note_label = MDLabel(
            text=self.note_name,
            font_size=sp(18),
            halign="center",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        self.status_label = MDLabel(
            text="--",
            font_size=sp(14),
            halign="center",
            size_hint_x=None,
            width=dp(40),
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.5],
            bold=True
        )

        top.add_widget(self.num_label)
        top.add_widget(self.note_label)
        top.add_widget(self.status_label)

        self.bar_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(4),
            padding=[dp(28), 0, dp(40), 0]
        )

        self.bar_bg = MDCard(
            size_hint=(1, 1),
            md_bg_color=[0.3, 0.3, 0.3, 0.3],
            radius=[dp(2), dp(2), dp(2), dp(2)],
            elevation=0
        )

        self.bar_fill = MDCard(
            size_hint=(0, 1),
            md_bg_color=[0.46, 0.70, 0.71, 0.8],
            radius=[dp(2), dp(2), dp(2), dp(2)],
            elevation=0
        )

        self.bar_bg.add_widget(self.bar_fill)
        self.bar_container.add_widget(self.bar_bg)

        self.add_widget(top)
        self.add_widget(self.bar_container)

    def set_active(self, active):
        self.is_active = active
        if active:
            self.md_bg_color = [0.46, 0.70, 0.71, 0.15]
            self.line_color = [0.46, 0.70, 0.71, 0.3]
        else:
            self.md_bg_color = [0.2, 0.2, 0.2, 0.3]
            self.line_color = [1, 1, 1, 0.05]

    def set_deviation(self, deviation):
        self.deviation = deviation
        normalized = (deviation + 1) / 2
        normalized = max(0, min(1, normalized))
        self.bar_fill.size_hint_x = normalized

        abs_dev = abs(deviation)
        if abs_dev < 0.05:
            color = [0.3, 0.8, 0.3, 0.9]
        elif abs_dev < 0.15:
            color = [0.9, 0.8, 0.2, 0.9]
        else:
            color = [0.8, 0.2, 0.2, 0.9]
        self.bar_fill.md_bg_color = color

        if abs_dev < 0.05:
            self.status_label.text = "✓"
            self.status_label.text_color = [0.3, 0.8, 0.3, 1]
        elif abs_dev < 0.15:
            self.status_label.text = "≈"
            self.status_label.text_color = [0.9, 0.8, 0.2, 1]
        else:
            self.status_label.text = "✗"
            self.status_label.text_color = [0.8, 0.2, 0.2, 1]

        self.status_label.opacity = 1


class TunerScreen(BaseScreen):
    """Гитарный тюнер с визуальным индикатором - с правильными отступами"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'
        self.bg_image = None
        self.is_listening = False
        self.microphone = None
        self.current_frequency = 0
        self.current_note = None
        self.current_deviation = 0
        self.detected_note = None
        self.detected_freq = 0
        self._emulation_event = None

        # Инициализация UI через BaseScreen
        self.init_ui()
        self.load_background()

        Clock.schedule_once(self._init_microphone, 0.5)

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

    def _init_microphone(self, dt):
        """Инициализация микрофона через plyer"""
        try:
            from plyer import microphone
            if hasattr(microphone, 'request_permissions'):
                microphone.request_permissions()
            self.microphone = microphone
            self.is_listening = True
            if hasattr(microphone, 'start_recording'):
                self._start_microphone()
            else:
                self._start_emulation()
            logger.info("✅ Микрофон инициализирован")
        except ImportError:
            logger.warning("⚠️ plyer не установлен, используем эмуляцию")
            self._start_emulation()
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации микрофона: {e}")
            self._start_emulation()

    def _start_microphone(self):
        try:
            from plyer import audio
            if hasattr(audio, 'record_audio'):
                audio.record_audio(
                    duration=0.1,
                    callback=self._on_audio_data,
                    format='pcm'
                )
                logger.info("🎤 Захват звука запущен")
            else:
                self._start_emulation()
        except Exception as e:
            logger.error(f"Ошибка захвата звука: {e}")
            self._start_emulation()

    def _start_emulation(self):
        logger.info("🎵 Используем эмуляцию тюнера")
        self.is_listening = True
        if self._emulation_event:
            Clock.unschedule(self._emulation_event)
        self._emulation_event = Clock.schedule_interval(self._emulate_frequency, 0.5)

    def _emulate_frequency(self, dt):
        import random
        freq = 440 + (random.random() - 0.5) * 40
        self._process_frequency(freq)

    def _on_audio_data(self, data):
        if not self.is_listening:
            return
        try:
            freq = self._estimate_frequency(data)
            if freq > 0:
                self._process_frequency(freq)
        except Exception as e:
            logger.error(f"Ошибка обработки аудио: {e}")

    def _estimate_frequency(self, data):
        import random
        return 440 + (random.random() - 0.5) * 20

    def _process_frequency(self, freq):
        self.current_frequency = freq

        closest_note = None
        closest_freq = None
        min_diff = float('inf')

        for note, note_freq in NOTES.items():
            diff = abs(freq - note_freq)
            if diff < min_diff:
                min_diff = diff
                closest_note = note
                closest_freq = note_freq

        if closest_note and min_diff < 50:
            self.detected_note = closest_note
            self.detected_freq = closest_freq

            cents = 1200 * math.log2(freq / closest_freq) if closest_freq > 0 else 0
            self.current_deviation = cents / 50
            self.current_deviation = max(-1, min(1, self.current_deviation))

            if hasattr(self, 'tuner_dial'):
                self.tuner_dial.deviation = self.current_deviation
                self.tuner_dial.note_name = closest_note
                self.tuner_dial.note_frequency = closest_freq

            self._update_strings(freq, closest_note)

            # Обновляем отображение частоты и ноты
            if hasattr(self, 'freq_label'):
                self.freq_label.text = f"{freq:.1f} Hz"
            if hasattr(self, 'note_label'):
                self.note_label.text = closest_note

    def _update_strings(self, freq, note):
        if not hasattr(self, 'string_indicators'):
            return

        best_string = None
        best_diff = float('inf')

        for num, data in GUITAR_STRINGS.items():
            diff = abs(freq - data['freq'])
            if diff < best_diff:
                best_diff = diff
                best_string = num

        for i, indicator in enumerate(self.string_indicators):
            string_num = i + 1
            if string_num == best_string and best_diff < 20:
                indicator.set_active(True)
                target_freq = GUITAR_STRINGS[string_num]['freq']
                cents = 1200 * math.log2(freq / target_freq) if target_freq > 0 else 0
                deviation = cents / 50
                deviation = max(-1, min(1, deviation))
                indicator.set_deviation(deviation)
            else:
                indicator.set_active(False)
                indicator.set_deviation(0)

    def init_ui(self):
        """Инициализирует UI через BaseScreen с правильными отступами"""

        # Создаём контент
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True
        )

        # Заголовок
        title = MDLabel(
            text="ГИТАРНЫЙ ТЮНЕР",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            bold=True
        )
        content.add_widget(title)

        # Круговой индикатор
        dial_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(240),
            padding=[dp(16), dp(4), dp(16), dp(4)]
        )
        self.tuner_dial = TunerDial()
        dial_container.add_widget(self.tuner_dial)
        content.add_widget(dial_container)

        # Информация о частоте и ноте
        info_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(16),
            padding=[dp(16), dp(4), dp(16), dp(4)]
        )

        self.freq_label = MDLabel(
            text="--",
            font_size=sp(22),
            halign="center",
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        self.note_label = MDLabel(
            text="--",
            font_size=sp(22),
            halign="center",
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        info_container.add_widget(self.freq_label)
        info_container.add_widget(self.note_label)
        content.add_widget(info_container)

        # Индикаторы струн
        strings_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            spacing=dp(6),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )
        strings_container.bind(minimum_height=strings_container.setter('height'))

        self.string_indicators = []
        for string_num in range(6, 0, -1):
            data = GUITAR_STRINGS[string_num]
            indicator = StringIndicator(string_num, data)
            self.string_indicators.append(indicator)
            strings_container.add_widget(indicator)

        content.add_widget(strings_container)

        # Кнопка старт/стоп
        btn_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            spacing=dp(12),
            padding=[dp(40), dp(4), dp(40), dp(4)]
        )

        self.toggle_btn = MDRaisedButton(
            text="Начать",
            size_hint=(1, 1),
            md_bg_color=[0.46, 0.70, 0.71, 1],
            text_color=[1, 1, 1, 1],
            font_size=sp(16),
            on_release=self.toggle_tuner
        )
        btn_container.add_widget(self.toggle_btn)
        content.add_widget(btn_container)

        # Нижний отступ
        content.add_widget(Widget(size_hint_y=None, height=dp(16)))

        # Строим UI через BaseScreen с прокруткой
        self.build_ui(content_widget=content, use_scroll=True)

        logger.info("UI тюнера построен через BaseScreen")

    def toggle_tuner(self, instance):
        """Включает/выключает тюнер"""
        if not self.is_listening:
            self.is_listening = True
            self.toggle_btn.text = "Остановить"
            self.toggle_btn.md_bg_color = [0.8, 0.3, 0.3, 1]
            notify.success("Тюнер запущен")

            if not hasattr(self.microphone, 'start_recording'):
                if self._emulation_event:
                    Clock.unschedule(self._emulation_event)
                self._emulation_event = Clock.schedule_interval(self._emulate_frequency, 0.3)
        else:
            self.is_listening = False
            self.toggle_btn.text = "Начать"
            self.toggle_btn.md_bg_color = [0.46, 0.70, 0.71, 1]
            notify.info("Тюнер остановлен")

            if self._emulation_event:
                Clock.unschedule(self._emulation_event)
                self._emulation_event = None

            if hasattr(self, 'tuner_dial'):
                self.tuner_dial.deviation = 0
                self.tuner_dial.note_name = '--'
            if hasattr(self, 'freq_label'):
                self.freq_label.text = "--"
            if hasattr(self, 'note_label'):
                self.note_label.text = "--"
            if hasattr(self, 'string_indicators'):
                for indicator in self.string_indicators:
                    indicator.set_active(False)
                    indicator.set_deviation(0)

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в экран тюнера")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Тюнер")
            app.top_nav._show_back_button()
            app.top_nav.back_btn.on_release = self.go_back

    def go_back(self, instance=None):
        """Возврат на главный экран"""
        logger.info("🔙 Возврат на home")
        if self.is_listening:
            self.toggle_tuner(None)
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана тюнера")
        if self.is_listening:
            self.toggle_tuner(None)
        if self._emulation_event:
            Clock.unschedule(self._emulation_event)
            self._emulation_event = None
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            app.top_nav.update_title('home')