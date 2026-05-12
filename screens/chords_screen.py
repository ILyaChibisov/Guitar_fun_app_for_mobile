# screens/chords_screen.py
"""
Экран гитарных аккордов - переведён на BaseScreen
"""
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.core.image import Image as CoreImage
from io import BytesIO
import os
import pkgutil
import importlib
import re
import traceback

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.chord_renderer import ChordRenderer
from utils.notifications import notify

logger = screen_logger('Chords')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None

TONALITIES = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']

CHORD_TYPES = [
    "Major", "Minor", "7", "m7", "Dim", "Dim7", "Aug", "sus2",
    "sus4", "maj7", "7sus4", "maj9", "maj11", "maj13", "maj9#11", "maj13#11",
    "add9", "6add9", "maj7b5", "maj7#5", "m6", "m9", "m11", "m13",
    "madd9", "m6add9", "mmaj7", "mmaj9", "m7b5", "m7#5", "6", "9",
    "11", "13", "7b5", "7#5", "7b9", "7#9", "7(b5,b9)", "7(b5,#9)",
    "7(#5,b9)", "7(#5,#9)", "9b5", "9#5", "13#11", "13b9", "11b9",
    "sus2sus4", "-5", "5"
]


class TonalityButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.main_layout = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[dp(2), dp(2), dp(2), dp(2)])
        self.label = MDLabel(text=text, font_size=sp(11), halign="center", valign="middle",
                             theme_text_color="Custom", bold=True, size_hint=(1, 1))
        self.main_layout.add_widget(self.label)
        self.add_widget(self.main_layout)
        self.is_active = is_active
        self.bind(on_release=self._on_press)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.main_layout.md_bg_color = [0.46, 0.70, 0.71, 1]
            self.main_layout.radius = [dp(6), dp(6), dp(6), dp(6)]
        else:
            self.label.text_color = [0, 0, 0, 1]
            self.main_layout.md_bg_color = [0, 0, 0, 0]
            self.main_layout.radius = [0, 0, 0, 0]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class TonalityRow(MDBoxLayout):
    def __init__(self, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(70)
        self.spacing = dp(4)
        self.padding = [dp(12), dp(2), dp(12), dp(2)]
        self.on_item_selected = on_item_selected
        self.current_page = 0
        self.items_per_page = 6
        self.current_selected = "A"
        self.tonality_list = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
        self.total_pages = 2
        self.buttons = []
        self._build_ui()

    def _build_ui(self):
        title_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(24), spacing=dp(12), padding=[dp(4), dp(1), dp(4), dp(1)])
        self.prev_btn = MDIconButton(icon="chevron-left", size_hint=(None, None), size=(dp(28), dp(28)),
                                      theme_icon_color="Custom", icon_color="#FFFFFF", on_release=self.prev_page,
                                      md_bg_color=[0, 0, 0, 0])
        self.title_label = MDLabel(text="Тональность", font_size=sp(13), halign="center", valign="middle",
                                    size_hint_x=0.6, theme_text_color="Custom", text_color=[1, 1, 1, 1], bold=True)
        self.next_btn = MDIconButton(icon="chevron-right", size_hint=(None, None), size=(dp(28), dp(28)),
                                      theme_icon_color="Custom", icon_color="#FFFFFF", on_release=self.next_page,
                                      md_bg_color=[0, 0, 0, 0])
        title_layout.add_widget(MDBoxLayout(size_hint_x=0.05))
        title_layout.add_widget(self.prev_btn)
        title_layout.add_widget(self.title_label)
        title_layout.add_widget(self.next_btn)
        title_layout.add_widget(MDBoxLayout(size_hint_x=0.05))
        self.add_widget(title_layout)

        self.tonality_card = MDCard(orientation='vertical', size_hint=(1, None), height=dp(40),
                                     radius=[theme.CORNER_RADIUS_SMALL] * 4, md_bg_color="#E8E8E8",
                                     elevation=0, padding=[dp(4), dp(2), dp(4), dp(2)])
        self.buttons_container = MDBoxLayout(orientation='horizontal', spacing=dp(4), size_hint_x=1, height=dp(34))
        self.tonality_card.add_widget(self.buttons_container)
        self.add_widget(self.tonality_card)
        self.update_display()

    def update_display(self):
        self.buttons_container.clear_widgets()
        self.buttons.clear()
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.tonality_list))
        current_items = self.tonality_list[start_idx:end_idx]
        for item in current_items:
            btn = TonalityButton(text=item, is_active=(item == self.current_selected),
                                  on_press_callback=self.on_tonality_press)
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)
        for i in range(self.items_per_page - len(current_items)):
            spacer = MDBoxLayout(size_hint=(1, 1))
            self.buttons_container.add_widget(spacer)

    def on_tonality_press(self, tonality):
        self.set_selected(tonality)
        if self.on_item_selected:
            self.on_item_selected(tonality)

    def prev_page(self, instance):
        self.current_page = (self.current_page - 1) % self.total_pages
        self.update_display()

    def next_page(self, instance):
        self.current_page = (self.current_page + 1) % self.total_pages
        self.update_display()

    def set_selected(self, tonality):
        self.current_selected = tonality
        for btn in self.buttons:
            btn.set_active(btn.btn_text == tonality)


class TypeButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.padding = [dp(1), dp(2), dp(1), dp(2)]
        length = len(text)
        if length <= 4:
            font_size = sp(9)
        elif length <= 5:
            font_size = sp(8.5)
        elif length <= 6:
            font_size = sp(8)
        elif length <= 7:
            font_size = sp(7.5)
        elif length <= 8:
            font_size = sp(7)
        elif length <= 9:
            font_size = sp(6.5)
        elif length <= 10:
            font_size = sp(6)
        else:
            font_size = sp(5.5)
        self.main_layout = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[dp(1), dp(1), dp(1), dp(1)])
        self.label = MDLabel(text=text, font_size=font_size, halign="center", valign="middle",
                             theme_text_color="Custom", bold=True, size_hint=(1, 1))
        self.main_layout.add_widget(self.label)
        self.add_widget(self.main_layout)
        self.is_active = is_active
        self.bind(on_release=self._on_press)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.main_layout.md_bg_color = [0.9, 0.6, 0.2, 1]
            self.main_layout.radius = [dp(6), dp(6), dp(6), dp(6)]
        else:
            self.label.text_color = [0, 0, 0, 1]
            self.main_layout.md_bg_color = [0, 0, 0, 0]
            self.main_layout.radius = [0, 0, 0, 0]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class TypeRow(MDBoxLayout):
    def __init__(self, items, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(70)
        self.spacing = dp(4)
        self.padding = [dp(12), dp(2), dp(12), dp(2)]
        self.items = items
        self.on_item_selected = on_item_selected
        self.current_page = 0
        self.items_per_page = 4
        self.current_selected = "Major"
        self.buttons = []
        self.total_pages = max(1, (len(items) + self.items_per_page - 1) // self.items_per_page)
        self._build_ui()

    def _build_ui(self):
        title_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(24), spacing=dp(12), padding=[dp(4), dp(1), dp(4), dp(1)])
        self.prev_btn = MDIconButton(icon="chevron-left", size_hint=(None, None), size=(dp(28), dp(28)),
                                      theme_icon_color="Custom", icon_color="#FFFFFF", on_release=self.prev_page,
                                      md_bg_color=[0, 0, 0, 0])
        self.title_label = MDLabel(text="Тип аккорда", font_size=sp(13), halign="center", valign="middle",
                                    size_hint_x=0.6, theme_text_color="Custom", text_color=[1, 1, 1, 1], bold=True)
        self.next_btn = MDIconButton(icon="chevron-right", size_hint=(None, None), size=(dp(28), dp(28)),
                                      theme_icon_color="Custom", icon_color="#FFFFFF", on_release=self.next_page,
                                      md_bg_color=[0, 0, 0, 0])
        title_layout.add_widget(MDBoxLayout(size_hint_x=0.05))
        title_layout.add_widget(self.prev_btn)
        title_layout.add_widget(self.title_label)
        title_layout.add_widget(self.next_btn)
        title_layout.add_widget(MDBoxLayout(size_hint_x=0.05))
        self.add_widget(title_layout)

        self.type_card = MDCard(orientation='vertical', size_hint=(1, None), height=dp(40),
                                 radius=[theme.CORNER_RADIUS_SMALL] * 4, md_bg_color="#E8E8E8",
                                 elevation=0, padding=[dp(4), dp(2), dp(4), dp(2)])
        self.buttons_container = MDBoxLayout(orientation='horizontal', spacing=dp(4), size_hint_x=1, height=dp(34))
        self.type_card.add_widget(self.buttons_container)
        self.add_widget(self.type_card)
        self.update_display()

    def update_display(self):
        self.buttons_container.clear_widgets()
        self.buttons.clear()
        self.total_pages = max(1, (len(self.items) + self.items_per_page - 1) // self.items_per_page)
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.items))
        current_items = self.items[start_idx:end_idx]
        for item in current_items:
            btn = TypeButton(text=item, is_active=(item == self.current_selected),
                              on_press_callback=self.on_type_press)
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)
        for i in range(self.items_per_page - len(current_items)):
            spacer = MDBoxLayout(size_hint=(1, 1))
            self.buttons_container.add_widget(spacer)

    def on_type_press(self, chord_type):
        self.current_selected = chord_type
        for btn in self.buttons:
            btn.set_active(btn.btn_text == chord_type)
        if self.on_item_selected:
            self.on_item_selected(chord_type)

    def prev_page(self, instance):
        self.current_page = (self.current_page - 1) % self.total_pages
        self.update_display()

    def next_page(self, instance):
        self.current_page = (self.current_page + 1) % self.total_pages
        self.update_display()

    def set_selected(self, chord_type):
        self.current_selected = chord_type
        for btn in self.buttons:
            btn.set_active(btn.btn_text == chord_type)


class ChordsButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        length = len(text)
        if length <= 4:
            font_size = sp(10)
        elif length <= 5:
            font_size = sp(9.5)
        elif length <= 6:
            font_size = sp(9)
        elif length <= 7:
            font_size = sp(8.5)
        elif length <= 8:
            font_size = sp(8)
        else:
            font_size = sp(7.5)
        self.main_layout = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[dp(2), dp(2), dp(2), dp(2)])
        self.label = MDLabel(text=text, font_size=font_size, halign="center", valign="middle",
                             theme_text_color="Custom", bold=True, size_hint=(1, 1))
        self.main_layout.add_widget(self.label)
        self.add_widget(self.main_layout)
        self.is_active = is_active
        self.bind(on_release=self._on_press)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.main_layout.md_bg_color = [0.2, 0.5, 0.9, 1]
            self.main_layout.radius = [dp(6), dp(6), dp(6), dp(6)]
        else:
            self.label.text_color = [0, 0, 0, 1]
            self.main_layout.md_bg_color = [0, 0, 0, 0]
            self.main_layout.radius = [0, 0, 0, 0]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class ChordsRow(MDBoxLayout):
    def __init__(self, on_item_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(70)
        self.spacing = dp(4)
        self.padding = [dp(12), dp(2), dp(12), dp(2)]
        self.on_item_selected = on_item_selected
        self.current_page = 0
        self.items_per_page = 4
        self.current_selected = None
        self.buttons = []
        self.chords_data = {}
        self.current_items = []
        self.total_pages = 1
        self._build_ui()

    def _build_ui(self):
        title_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(24), spacing=dp(12), padding=[dp(4), dp(1), dp(4), dp(1)])
        self.prev_btn = MDIconButton(icon="chevron-left", size_hint=(None, None), size=(dp(28), dp(28)),
                                      theme_icon_color="Custom", icon_color="#FFFFFF", on_release=self.prev_page,
                                      md_bg_color=[0, 0, 0, 0])
        self.title_label = MDLabel(text="Аккорды", font_size=sp(13), halign="center", valign="middle",
                                    size_hint_x=0.6, theme_text_color="Custom", text_color=[1, 1, 1, 1], bold=True)
        self.next_btn = MDIconButton(icon="chevron-right", size_hint=(None, None), size=(dp(28), dp(28)),
                                      theme_icon_color="Custom", icon_color="#FFFFFF", on_release=self.next_page,
                                      md_bg_color=[0, 0, 0, 0])
        title_layout.add_widget(MDBoxLayout(size_hint_x=0.05))
        title_layout.add_widget(self.prev_btn)
        title_layout.add_widget(self.title_label)
        title_layout.add_widget(self.next_btn)
        title_layout.add_widget(MDBoxLayout(size_hint_x=0.05))
        self.add_widget(title_layout)

        self.chords_card = MDCard(orientation='vertical', size_hint=(1, None), height=dp(40),
                                   radius=[theme.CORNER_RADIUS_SMALL] * 4, md_bg_color="#E8E8E8",
                                   elevation=0, padding=[dp(8), dp(2), dp(8), dp(2)])
        self.buttons_container = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_x=1, height=dp(34))
        self.chords_card.add_widget(self.buttons_container)
        self.add_widget(self.chords_card)

    def set_chords(self, chords_list):
        self.current_items = [chord['short_name'] for chord in chords_list]
        self.chords_data = {chord['short_name']: chord for chord in chords_list}
        self.current_page = 0
        self.total_pages = max(1, (len(self.current_items) + self.items_per_page - 1) // self.items_per_page)
        if self.current_items:
            self.current_selected = self.current_items[0]
        self.update_display()
        if self.current_items and self.on_item_selected:
            Clock.schedule_once(lambda dt: self.on_item_selected(self.current_items[0]), 0.1)

    def update_display(self):
        self.buttons_container.clear_widgets()
        self.buttons.clear()
        if not self.current_items:
            empty_label = MDLabel(text="Нет аккордов", halign="center", font_size=sp(11),
                                   theme_text_color="Custom", text_color=[0.5, 0.5, 0.5, 1])
            self.buttons_container.add_widget(empty_label)
            return
        self.total_pages = max(1, (len(self.current_items) + self.items_per_page - 1) // self.items_per_page)
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(self.current_items))
        current_items = self.current_items[start_idx:end_idx]
        for item in current_items:
            btn = ChordsButton(text=item, is_active=(item == self.current_selected),
                                on_press_callback=self.on_chord_press)
            self.buttons.append(btn)
            self.buttons_container.add_widget(btn)
        for i in range(self.items_per_page - len(current_items)):
            spacer = MDBoxLayout(size_hint=(1, 1))
            self.buttons_container.add_widget(spacer)

    def on_chord_press(self, chord_name):
        self.current_selected = chord_name
        for btn in self.buttons:
            btn.set_active(btn.btn_text == chord_name)
        if self.on_item_selected:
            self.on_item_selected(chord_name)

    def prev_page(self, instance):
        if not self.current_items:
            return
        self.current_page = (self.current_page - 1) % self.total_pages
        self.update_display()

    def next_page(self, instance):
        if not self.current_items:
            return
        self.current_page = (self.current_page + 1) % self.total_pages
        self.update_display()

    def get_chord_data(self, chord_name):
        return self.chords_data.get(chord_name)


class ChordActionButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, icon_name, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press_callback
        self.size_hint = (None, None)
        self.size = (dp(42), dp(42))
        self.icon = Image(size_hint=(None, None), size=(dp(24), dp(24)),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5}, allow_stretch=True)
        self.add_widget(self.icon)
        self.bind(on_release=self._on_press)
        self.load_icon()

    def load_icon(self):
        icon_data = load_asset_as_bytes(self.icon_name)
        if icon_data:
            img = CoreImage(BytesIO(icon_data), ext="png")
            self.icon.texture = img.texture

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.icon_name)


class ChordsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chords'
        self.all_chords = []
        self.current_chord_module = None
        self.current_tonality = "A"
        self.current_type = "Major"
        self.current_variants = []
        self.current_variant_index = 0
        self.current_mode = "finger"
        self.bg_image = None

        self.init_ui()
        self.load_background()
        self.scan_chords()

        logger.info('Экран аккордов создан (BaseScreen)')

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

    def init_ui(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(6),
            size_hint_y=None,
            adaptive_height=True
        )

        self.tonality_row = TonalityRow(on_item_selected=self.on_tonality_selected)
        content.add_widget(self.tonality_row)

        self.type_row = TypeRow(items=CHORD_TYPES, on_item_selected=self.on_type_selected)
        content.add_widget(self.type_row)

        self.chords_row = ChordsRow(on_item_selected=self.on_chord_selected)
        content.add_widget(self.chords_row)

        # Блок с грифом
        griff_block = MDBoxLayout(orientation='vertical', size_hint=(1, None), height=dp(340), spacing=dp(4))

        self.chord_name_label = MDLabel(text="Выберите аккорд", halign="center", font_size=sp(18), bold=True,
                                         size_hint_y=None, height=dp(32), theme_text_color="Custom",
                                         text_color=[1, 1, 1, 1])
        griff_block.add_widget(self.chord_name_label)

        self.chord_desc_label = MDLabel(text="", halign="center", font_size=sp(8),
                                         theme_text_color="Custom", text_color=[1, 1, 1, 0.6],
                                         size_hint_y=None, height=dp(20), markup=True)
        griff_block.add_widget(self.chord_desc_label)

        griff_container = MDBoxLayout(size_hint=(1, None), height=dp(220), padding=[dp(8), dp(4), dp(8), dp(4)])
        self.chord_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_renderer)
        griff_block.add_widget(griff_container)

        # Нижняя панель
        bottom_panel = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(48),
                                    spacing=dp(8), padding=[dp(8), dp(4), dp(8), dp(4)])

        action_icons_layout = MDBoxLayout(orientation='horizontal', size_hint_x=None, width=dp(40), spacing=dp(8),
                                           padding=[dp(4), dp(2), dp(4), dp(2)])
        self.finger_btn = ChordActionButton(icon_name="fingers_png", on_press_callback=lambda x: self.set_mode("finger"))
        action_icons_layout.add_widget(self.finger_btn)
        self.note_btn = ChordActionButton(icon_name="notes_png", on_press_callback=lambda x: self.set_mode("note"))
        action_icons_layout.add_widget(self.note_btn)
        self.sound_btn = ChordActionButton(icon_name="sound_png", on_press_callback=lambda x: self.on_sound_press())
        action_icons_layout.add_widget(self.sound_btn)

        bottom_panel.add_widget(action_icons_layout)
        bottom_panel.add_widget(MDBoxLayout(size_hint_x=1))

        variants_panel = MDBoxLayout(orientation='horizontal', size_hint_x=None, width=dp(180), spacing=dp(6),
                                      padding=[dp(4), dp(2), dp(4), dp(2)])
        position_title = MDLabel(text="Позиция", font_size=sp(12), size_hint_x=None, width=dp(70),
                                  theme_text_color="Custom", text_color=[1, 1, 1, 0.8], bold=True, valign="middle")
        variants_panel.add_widget(position_title)

        pagination_card = MDBoxLayout(orientation='horizontal', size_hint_x=None, width=dp(72), height=dp(32),
                                       spacing=dp(2), padding=[dp(2), dp(2), dp(2), dp(2)])
        self.variants_prev_btn = MDIconButton(icon="chevron-left", size_hint=(None, None), size=(dp(26), dp(26)),
                                               theme_icon_color="Custom", icon_color="#FFFFFF",
                                               on_release=self.prev_variant, md_bg_color=[0, 0, 0, 0])
        self.variant_number_label = MDLabel(text="1/1", font_size=sp(12), size_hint_x=None, width=dp(28),
                                             halign="center", valign="middle", theme_text_color="Custom",
                                             text_color=[1, 1, 1, 1], bold=True)
        self.variants_next_btn = MDIconButton(icon="chevron-right", size_hint=(None, None), size=(dp(26), dp(26)),
                                               theme_icon_color="Custom", icon_color="#FFFFFF",
                                               on_release=self.next_variant, md_bg_color=[0, 0, 0, 0])
        pagination_card.add_widget(self.variants_prev_btn)
        pagination_card.add_widget(self.variant_number_label)
        pagination_card.add_widget(self.variants_next_btn)
        variants_panel.add_widget(pagination_card)

        bottom_panel.add_widget(variants_panel)
        griff_block.add_widget(bottom_panel)
        content.add_widget(griff_block)

        # Строим UI с прокруткой
        self.build_ui(content_widget=content, use_scroll=True)

        # Загружаем фон грифа
        try:
            bg_data = load_asset_as_bytes("griff_png")
            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="png")
                if img and img.texture:
                    self.chord_renderer.set_background(img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

    def update_variant_display(self):
        if self.current_variants:
            total = len(self.current_variants)
            self.variant_number_label.text = f"{self.current_variant_index + 1}/{total}"
            enabled = total > 1
            self.variants_prev_btn.icon_color = [0.5, 0.5, 0.5, 1] if not enabled else [1, 1, 1, 1]
            self.variants_next_btn.icon_color = [0.5, 0.5, 0.5, 1] if not enabled else [1, 1, 1, 1]
        else:
            self.variant_number_label.text = "1/1"

    def prev_variant(self, instance):
        if self.current_variants and len(self.current_variants) > 1:
            self.current_variant_index = (self.current_variant_index - 1) % len(self.current_variants)
            self.load_current_variant()
            self.update_variant_display()

    def next_variant(self, instance):
        if self.current_variants and len(self.current_variants) > 1:
            self.current_variant_index = (self.current_variant_index + 1) % len(self.current_variants)
            self.load_current_variant()
            self.update_variant_display()

    def on_sound_press(self):
        notify.info("🔊 Звук аккорда (будет доступно в следующей версии)")

    def scan_chords(self):
        print("\n" + "=" * 60)
        print("SCAN_CHORDS: Начинаю сканирование аккордов")
        self.all_chords = []
        try:
            import chords
            self._scan_module_recursive(chords, 'chords')
        except ImportError as e:
            print(f"❌ Пакет chords не найден: {e}")
        except Exception as e:
            print(f"❌ Непредвиденная ошибка: {e}")
            traceback.print_exc()
        print(f"РЕЗУЛЬТАТ: Загружено {len(self.all_chords)} аккордов")
        self.update_chords_list()

    def _scan_module_recursive(self, module, module_path):
        try:
            if hasattr(module, '__path__'):
                for module_info in pkgutil.iter_modules(module.__path__, f"{module_path}."):
                    try:
                        sub_module = importlib.import_module(module_info.name)
                        if hasattr(sub_module, '__path__'):
                            self._scan_module_recursive(sub_module, module_info.name)
                        else:
                            self._load_chord_module(sub_module, module_info.name)
                    except Exception as e:
                        print(f"    ❌ Ошибка импорта {module_info.name}: {e}")
        except Exception as e:
            print(f"  ❌ Ошибка сканирования {module_path}: {e}")

    def _load_chord_module(self, module, module_name):
        try:
            metadata = getattr(module, 'METADATA', {})
            chord_name = metadata.get('name', module_name.split('.')[-1])
            chord_name = chord_name.replace('!', '|').replace('$', '/')
            path_parts = module_name.split('.')
            chord_type = metadata.get('type', '')
            if not chord_type and len(path_parts) >= 2:
                chord_type = path_parts[-2]
            variant_match = re.search(r'_(\d+)$', path_parts[-1])
            variant_num = int(variant_match.group(1)) if variant_match else metadata.get('variant', 1)
            short_name = chord_name.split('|')[0].replace('$', '/')
            chord_data = {
                'id': f"{short_name}_{chord_type}_v{variant_num}",
                'name': chord_name,
                'short_name': short_name,
                'variant': variant_num,
                'type': chord_type,
                'description': metadata.get('description', ''),
                'module': module,
                'path': module_name
            }
            self.all_chords.append(chord_data)
        except Exception as e:
            print(f"    ❌ Ошибка загрузки модуля {module_name}: {e}")

    def update_chords_list(self):
        filtered = []
        for chord in self.all_chords:
            tonality = self.extract_tonality(chord['name'])
            if tonality != self.current_tonality:
                continue
            chord_types = chord['type'].split('|') if chord['type'] else []
            if self.current_type not in chord_types and self.current_type != chord.get('type', ''):
                continue
            filtered.append(chord)

        chords_by_name = {}
        for chord in filtered:
            name = chord['short_name']
            if name not in chords_by_name:
                chords_by_name[name] = []
            chords_by_name[name].append(chord)

        chords_list = []
        for name, variants in chords_by_name.items():
            variants.sort(key=lambda x: x['variant'])
            chords_list.append({'short_name': name, 'variants': variants})
        chords_list.sort(key=lambda x: x['short_name'])
        self.chords_row.set_chords(chords_list)

    def extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        if '|' in chord_name:
            main_name = chord_name.split('|')[0]
        else:
            main_name = chord_name
        match = re.match(r'^([A-H][#b]?)', main_name)
        return match.group(1) if match else (main_name[0] if main_name else "")

    def on_chord_selected(self, chord_name):
        chord_data = self.chords_row.get_chord_data(chord_name)
        if chord_data:
            self.load_chord_variants(chord_data['variants'])

    def load_chord_variants(self, variants):
        if not variants:
            return
        variants.sort(key=lambda x: x['variant'])
        self.current_variants = variants
        self.current_variant_index = 0
        self.update_variant_display()
        self.load_current_variant()

    def load_current_variant(self):
        if not self.current_variants:
            return
        variant = self.current_variants[self.current_variant_index]
        self.current_chord_module = variant['module']
        chord_name = variant['name'].replace('!', ' | ').replace('$', '/')
        name_parts = chord_name.split('|')
        unique_names = []
        seen_names = set()
        for part in name_parts:
            part_clean = part.strip()
            if part_clean and part_clean not in seen_names:
                seen_names.add(part_clean)
                unique_names.append(part_clean)
        display_name = ' | '.join(unique_names)
        self.chord_name_label.text = display_name
        description = variant.get('description', '')
        description = self.clean_description(description, unique_names)
        self.chord_desc_label.text = description
        self.update_variant_display()
        if hasattr(self, 'chord_renderer'):
            self.chord_renderer.load_chord(self.current_chord_module)
            self.chord_renderer.set_mode(self.current_mode)

    def clean_description(self, description, chord_names):
        if not description:
            return ""
        description = description.replace('!', '|')
        parts = description.split('|')
        unique_parts = []
        seen = set()
        for part in parts:
            part_clean = part.strip()
            if part_clean and part_clean not in seen:
                is_chord_name = any(part_clean.lower() == name.lower() for name in chord_names)
                if not is_chord_name:
                    seen.add(part_clean)
                    unique_parts.append(part_clean)
        return ' | '.join(unique_parts)

    def set_mode(self, mode):
        self.current_mode = mode
        if self.current_chord_module and hasattr(self, 'chord_renderer'):
            self.chord_renderer.set_mode(mode)

    def on_tonality_selected(self, tonality):
        self.current_tonality = tonality
        self.tonality_row.set_selected(tonality)
        self.update_chords_list()

    def on_type_selected(self, chord_type):
        self.current_type = chord_type
        self.type_row.set_selected(chord_type)
        self.update_chords_list()

    def load_chord_by_name(self, chord_name):
        for chord in self.all_chords:
            if chord['short_name'].lower() == chord_name.lower():
                tonality = self.extract_tonality(chord['name'])
                self.current_tonality = tonality
                self.tonality_row