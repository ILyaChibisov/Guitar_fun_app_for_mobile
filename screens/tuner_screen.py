# screens/tuner_screen.py
"""
Гитарный тюнер с использованием plyer (без pyaudio)
"""
import math
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, Line, Ellipse
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from plyer import accelerometer

from config.theme import theme
from config.logger_config import screen_logger

logger = screen_logger('Tuner')

# Русские названия нот
NOTE_NAMES_RU = {
    'C': 'До', 'C#': 'До#', 'D': 'Ре', 'D#': 'Ре#',
    'E': 'Ми', 'F': 'Фа', 'F#': 'Фа#', 'G': 'Соль',
    'G#': 'Соль#', 'A': 'Ля', 'A#': 'Ля#', 'B': 'Си'
}

# Все ноты для отображения
NOTES_LIST = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# ГИТАРНЫЕ СТРОИ
TUNINGS = {
    "Standard (E-A-D-G-B-E)": [
        ("E2", "6", "Ми"), ("A2", "5", "Ля"), ("D3", "4", "Ре"),
        ("G3", "3", "Соль"), ("B3", "2", "Си"), ("E4", "1", "Ми")
    ],
    "Drop D (D-A-D-G-B-E)": [
        ("D2", "6", "Ре"), ("A2", "5", "Ля"), ("D3", "4", "Ре"),
        ("G3", "3", "Соль"), ("B3", "2", "Си"), ("E4", "1", "Ми")
    ],
}


class SmoothNeedleWidget(Widget):
    """Стрелка тюнера с плавной анимацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_angle = 0
        self.needle_length = dp(80)
        self.animation = None
        self.bind(pos=self.draw, size=self.draw)

    def set_angle(self, target_angle):
        target_angle = max(-45, min(45, target_angle))
        if self.animation:
            self.animation.cancel(self)
        self.animation = Animation(current_angle=target_angle, duration=0.1, t='out_quad')
        self.animation.start(self)

    def on_current_angle(self, instance, value):
        self.draw()

    def draw(self, *args):
        self.canvas.clear()
        center_x = self.center_x
        center_y = self.center_y

        with self.canvas:
            Color(0.4, 0.4, 0.4, 0.8)
            for angle in range(-45, 46, 15):
                rad = math.radians(angle)
                x = center_x + math.sin(rad) * self.needle_length * 0.8
                y = center_y + math.cos(rad) * self.needle_length * 0.8
                Line(points=[x, y, x + math.sin(rad) * 5, y + math.cos(rad) * 5], width=2)

            Color(0.46, 0.70, 0.71, 1)
            Ellipse(pos=(center_x - 10, center_y - 10), size=(20, 20))

            rad = math.radians(self.current_angle)
            end_x = center_x + math.sin(rad) * self.needle_length
            end_y = center_y + math.cos(rad) * self.needle_length

            if abs(self.current_angle) > 10:
                Color(0.9, 0.2, 0.2, 1)
            elif abs(self.current_angle) > 3:
                Color(0.9, 0.6, 0.1, 1)
            else:
                Color(0.2, 0.8, 0.2, 1)

            Line(points=[center_x, center_y, end_x, end_y], width=4)
            Ellipse(pos=(end_x - 5, end_y - 5), size=(10, 10))


class TunerScreen(MDScreen):
    """Экран гитарного тюнера (демо-режим, без реального аудио)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'
        self.md_bg_color = [0, 0, 0, 0]

        self.current_tuning = "Standard (E-A-D-G-B-E)"
        self.current_strings = TUNINGS[self.current_tuning]
        self.current_cents = 0
        self.tuning_menu = None

        self.init_ui()
        logger.info('Экран тюнера создан (демо-режим)')

    def get_note_frequency(self, note_name, octave):
        A4_index = NOTES_LIST.index('A')
        note_index = NOTES_LIST.index(note_name)
        semitone_diff = (octave - 4) * 12 + (note_index - A4_index)
        return 440.0 * (2 ** (semitone_diff / 12.0))

    def init_ui(self):
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.widget import Widget

        scroll = ScrollView(size_hint=(1, 1))

        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(2), dp(16), dp(16)],
            spacing=dp(12),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        from config.system_bars import get_status_bar_height
        from config.theme import theme
        status_h = get_status_bar_height()
        total_top_padding = status_h + theme.TOP_NAV_HEIGHT
        top_spacer = Widget(size_hint_y=None, height=dp(total_top_padding))
        main_layout.add_widget(top_spacer)

        # Карточка с информацией о демо-режиме
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0.18, 0.18, 0.18, 0.85],
            padding=[dp(16), dp(12), dp(16), dp(12)]
        )

        info_label = MDLabel(
            text="🎸 Тюнер\n\nРеальная настройка гитары будет доступна в следующей версии.\nПока здесь демо-режим.",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[0.8, 0.8, 0.8, 1]
        )
        info_card.add_widget(info_label)
        main_layout.add_widget(info_card)

        # Выбор строя
        tuning_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(48), spacing=dp(8),
                                    padding=[dp(8), dp(4), dp(8), dp(4)])
        tuning_label = MDLabel(text="Строй:", size_hint_x=0.25, font_size=sp(14), theme_text_color="Custom",
                               text_color=[0.8, 0.8, 0.8, 1], valign="middle")

        self.tuning_btn = Button(text=self.current_tuning, size_hint_x=0.75, font_size=sp(11), color=theme.PRIMARY,
                                 background_normal='', background_color=[0, 0, 0, 0])
        self.tuning_btn.bind(on_release=self.open_tuning_menu)

        tuning_layout.add_widget(tuning_label)
        tuning_layout.add_widget(self.tuning_btn)
        main_layout.add_widget(tuning_layout)

        # Карточка с нотой
        note_card = MDCard(orientation='vertical', size_hint=(1, None), height=dp(140), radius=[theme.CORNER_RADIUS],
                           md_bg_color=[0.18, 0.18, 0.18, 0.85], elevation=4, padding=[dp(16), dp(12), dp(16), dp(12)])

        self.note_label = MDLabel(text="--", halign="center", font_size=sp(56), theme_text_color="Custom",
                                  text_color=theme.PRIMARY, bold=True, size_hint_y=None, height=dp(70))
        self.string_hint_label = MDLabel(text="Выберите строй", halign="center", font_size=sp(12),
                                         theme_text_color="Custom", text_color=[0.7, 0.7, 0.7, 1],
                                         size_hint_y=None, height=dp(20))
        self.freq_label = MDLabel(text="440.0 Hz", halign="center", font_size=sp(14), theme_text_color="Custom",
                                  text_color=[0.8, 0.8, 0.8, 1], size_hint_y=None, height=dp(25))
        self.cents_label = MDLabel(text="0¢", halign="center", font_size=sp(14), theme_text_color="Custom",
                                   text_color=[1, 0.75, 0.1, 1], size_hint_y=None, height=dp(25))

        note_card.add_widget(self.note_label)
        note_card.add_widget(self.string_hint_label)
        note_card.add_widget(self.freq_label)
        note_card.add_widget(self.cents_label)
        main_layout.add_widget(note_card)

        # Стрелка
        self.needle = SmoothNeedleWidget(size_hint=(1, None), height=dp(160))
        main_layout.add_widget(self.needle)

        # Кнопка демо-звука
        demo_btn = Button(
            text="▶ ДЕМО (Ля)",
            size_hint=(0.6, None),
            height=dp(48),
            font_size=sp(14),
            color=theme.PRIMARY,
            background_normal='',
            background_color=[0.2, 0.2, 0.2, 0.5],
            pos_hint={'center_x': 0.5}
        )
        demo_btn.bind(on_release=self.demo_sound)
        main_layout.add_widget(demo_btn)

        # Струны
        self.strings_container = MDBoxLayout(orientation='vertical', size_hint=(1, None), height=dp(70))
        self.update_strings_display()
        main_layout.add_widget(self.strings_container)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

    def demo_sound(self, instance):
        """Демонстрация работы тюнера (без реального микрофона)"""
        # Показываем ноту A4 (Ля)
        self.note_label.text = "Ля4"
        self.freq_label.text = "440.0 Hz"
        self.cents_label.text = "0¢"
        self.cents_label.text_color = [0.2, 0.8, 0.2, 1]
        self.string_hint_label.text = "Демо: нота Ля (440 Hz)"
        self.needle.set_angle(0)
        logger.info("Демо-звук (нота Ля 440 Hz)")

    def update_strings_display(self):
        self.strings_container.clear_widgets()
        strings_layout = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(65), spacing=dp(4),
                                     padding=[dp(2), dp(4), dp(2), dp(4)])

        for note_id, string_num, string_name in reversed(self.current_strings):
            display_text = f"{string_num}\n{string_name}"
            btn = Button(text=display_text, size_hint=(1, 1), font_size=sp(10), color=theme.PRIMARY,
                         background_normal='', background_color=[0, 0, 0, 0])
            btn.bind(on_release=lambda x, n=note_id: self.set_reference_note(n))
            strings_layout.add_widget(btn)

        self.strings_container.add_widget(strings_layout)

    def open_tuning_menu(self, instance):
        menu_items = []
        for name in TUNINGS.keys():
            menu_items.append({
                "text": name,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=name: self.select_tuning(x),
            })

        self.tuning_menu = MDDropdownMenu(caller=self.tuning_btn, items=menu_items, width_mult=4, max_height=dp(300))
        self.tuning_menu.open()

    def select_tuning(self, tuning_name):
        self.current_tuning = tuning_name
        self.current_strings = TUNINGS[tuning_name]
        self.tuning_btn.text = tuning_name
        self.update_strings_display()
        self.string_hint_label.text = f"Строй: {tuning_name[:20]}"
        if self.tuning_menu:
            self.tuning_menu.dismiss()

    def set_reference_note(self, note_id):
        note_name = note_id[:-1]
        octave = int(note_id[-1])
        freq = self.get_note_frequency(note_name, octave)
        ru_name = NOTE_NAMES_RU.get(note_name, note_name)
        self.freq_label.text = f"{ru_name}: {freq:.1f} Hz"
        self.string_hint_label.text = f"Струна настроена на {ru_name}{octave}"
        self.note_label.text = f"{ru_name}{octave}"
        self.cents_label.text = "0¢"
        self.cents_label.text_color = [0.2, 0.8, 0.2, 1]
        self.needle.set_angle(0)