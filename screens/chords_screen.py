# screens/chords_screen.py
"""
Экран гитарных аккордов - с единым меню 5 в 1 под грифом
ТОН | ТИП | АККОРД | ВАРИАНТЫ | ПАЛЬЦЫ/НОТЫ
С меню выбора тональности, типа и аккорда
СТАТИЧНЫЙ ЭКРАН - БЕЗ ПРОКРУТКИ
"""
from kivy.uix.behaviors import ButtonBehavior
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.core.image import Image as CoreImage
from io import BytesIO
import pkgutil
import importlib
import re
import traceback

from kivymd.uix.textfield import MDTextField

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.chord_renderer import ChordRenderer
from utils.notifications import notify
from utils.screen_state import screen_state

logger = screen_logger('Chords')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# Константы
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

# Для отображения в описании
TYPE_DISPLAY = {
    "Major": "мажор",
    "Minor": "минор",
    "7": "септаккорд",
    "m7": "минорный септ",
    "maj7": "мажорный септ",
    "sus2": "sus2",
    "sus4": "sus4",
    "Dim": "уменьш",
    "Aug": "увелич",
    "Dim7": "ум.7",
    "m7b5": "m7-5",
}


class SearchBar(MDCard):
    """Поисковая строка"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self._search_timer = None

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 0
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)

        self.search_field = MDTextField(
            hint_text="Поиск аккордов...",
            size_hint_x=1,
            font_size=sp(15),
            height=dp(36),
            on_text_validate=self._on_search,
            mode="fill"
        )

        self.search_field.line_color_normal = [0, 0, 0, 0]
        self.search_field.line_color_focus = [0, 0, 0, 0]
        self.search_field.fill_color_normal = [1, 1, 1, 0]
        self.search_field.fill_color_focus = [1, 1, 1, 0]
        self.search_field.hint_text_color = [0.7, 0.7, 0.7, 1]
        self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]

        self.search_field.bind(text=self._on_text_change)

        self.clear_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            theme_icon_color="Custom",
            icon_color=[0.6, 0.6, 0.6, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear,
            opacity=0
        )

        self.search_icon = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search,
            pos_hint={'center_y': 0.5}
        )

        self.add_widget(self.search_field)
        self.add_widget(self.clear_btn)
        self.add_widget(self.search_icon)

    def _on_text_change(self, instance, text):
        self.clear_btn.opacity = 1 if text else 0
        self.current_query = text

        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if not text.strip():
            if self.on_clear:
                self.on_clear()
        else:
            self._search_timer = Clock.schedule_once(lambda dt: self._do_search(), 0.3)

    def _do_search(self):
        if self.on_search and self.current_query:
            text = self.current_query.strip()
            if text:
                self.on_search(text)

    def _on_search(self, instance):
        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear(self, instance):
        self.search_field.text = ""
        self.search_field.focus = True
        self.clear_btn.opacity = 0
        if self.on_clear:
            self.on_clear()

    def get_text(self):
        return self.search_field.text.strip()

    def set_text(self, text):
        self.search_field.text = text
        self.clear_btn.opacity = 1 if text else 0

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        self.search_field.focus = True


class IconMenuItem(ButtonBehavior, MDBoxLayout):
    """Пункт меню с иконкой (ТОН, ТИП, АККОРД, ВАРИАНТЫ или ПАЛЬЦЫ/НОТЫ) - без подписи"""

    def __init__(self, icon_name, on_press=None, is_active=False, icon_color=None, fixed_color=False, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press
        self.is_active = is_active
        self.fixed_color = fixed_color

        # Цвет иконки (если не указан - используем стандартный)
        if icon_color is None:
            self.icon_color = [1, 1, 1, 0.7]
        else:
            self.icon_color = icon_color

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = [dp(4), dp(6), dp(4), dp(6)]
        self.spacing = dp(0)
        self.md_bg_color = [0, 0, 0, 0]

        # Только иконка, без подписи
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
        self.update_state()

    def _on_enter(self, *args):
        self.md_bg_color = [1, 1, 1, 0.05]

    def _on_leave(self, *args):
        self.md_bg_color = [0, 0, 0, 0]

    def _on_press(self, instance):
        if self.on_press_callback and self.is_active:
            self.on_press_callback()

    def set_active(self, active):
        self.is_active = active
        self.update_state()

    def update_state(self):
        if self.fixed_color:
            return

        if self.is_active:
            # Активный цвет (яркий)
            self.icon_btn.icon_color = [0.46, 0.70, 0.71, 1]
            self.icon_btn.opacity = 1
        else:
            # Неактивный цвет (полупрозрачный)
            self.icon_btn.icon_color = [1, 1, 1, 0.3]
            self.icon_btn.opacity = 0.6

    def set_icon(self, icon_name):
        self.icon_name = icon_name
        self.icon_btn.icon = icon_name

    def set_color(self, color):
        self.icon_color = color
        self.icon_btn.icon_color = color


class ChordSelectorMenu(MDCard):
    """
    Временное меню выбора аккорда с горизонтальным скроллом
    Аккорды можно листать пальцем и нажимать для выбора
    """

    def __init__(self, available_chords, current_chord, on_confirm, on_cancel, **kwargs):
        super().__init__(**kwargs)
        self.available_chords = available_chords
        self.current_chord = current_chord
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0, 0, 0, 0.08]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.8
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        self._build_ui()

    def _build_ui(self):
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        self.chords_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(8),
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )
        self.chords_container.bind(minimum_width=self.chords_container.setter('width'))

        self.chord_btns = []
        for chord in self.available_chords:
            btn = MDRaisedButton(
                text=chord,
                size_hint=(None, 1),
                width=self._get_button_width(chord),
                md_bg_color=[0, 0, 0, 0],
                text_color=[1, 1, 1, 0.7],
                font_size=sp(14),
                elevation=0,
                on_release=lambda x, c=chord: self._on_chord_press(c)
            )
            self.chord_btns.append(btn)
            self.chords_container.add_widget(btn)

        self._highlight_current()

        scroll.add_widget(self.chords_container)
        self.add_widget(scroll)

    def _get_button_width(self, text):
        base_width = dp(30)
        char_width = dp(7)
        padding = dp(12)
        min_width = dp(36)
        max_width = dp(80)

        width = base_width + len(text) * char_width + padding
        width = max(min_width, min(width, max_width))
        return width

    def _highlight_current(self):
        for btn in self.chord_btns:
            if btn.text == self.current_chord:
                btn.md_bg_color = [1.0, 0.7, 0.0, 1]
                btn.text_color = [1, 1, 1, 1]
            else:
                btn.md_bg_color = [0, 0, 0, 0]
                btn.text_color = [1, 1, 1, 0.7]

    def _on_chord_press(self, chord):
        self.current_chord = chord
        self._highlight_current()
        if self.on_confirm:
            self.on_confirm(chord)


class TypeSelectorMenu(MDCard):
    """
    Временное меню выбора типа аккорда с горизонтальным скроллом
    Типы можно листать пальцем и нажимать для выбора
    """

    def __init__(self, current_type, on_confirm, on_cancel, **kwargs):
        super().__init__(**kwargs)
        self.current_type = current_type
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0, 0, 0, 0.08]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.8
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        self._build_ui()

    def _build_ui(self):
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        self.types_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(8),
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )
        self.types_container.bind(minimum_width=self.types_container.setter('width'))

        self.type_btns = []
        for chord_type in CHORD_TYPES:
            btn = MDRaisedButton(
                text=chord_type,
                size_hint=(None, 1),
                width=self._get_button_width(chord_type),
                md_bg_color=[0, 0, 0, 0],
                text_color=[1, 1, 1, 0.7],
                font_size=sp(13),
                elevation=0,
                on_release=lambda x, t=chord_type: self._on_type_press(t)
            )
            self.type_btns.append(btn)
            self.types_container.add_widget(btn)

        self._highlight_current()

        scroll.add_widget(self.types_container)
        self.add_widget(scroll)

    def _get_button_width(self, text):
        base_width = dp(40)
        char_width = dp(8)
        padding = dp(16)
        min_width = dp(44)
        max_width = dp(100)

        width = base_width + len(text) * char_width + padding
        width = max(min_width, min(width, max_width))
        return width

    def _highlight_current(self):
        for btn in self.type_btns:
            if btn.text == self.current_type:
                btn.md_bg_color = [0.0, 0.74, 0.83, 1]
                btn.text_color = [1, 1, 1, 1]
            else:
                btn.md_bg_color = [0, 0, 0, 0]
                btn.text_color = [1, 1, 1, 0.7]

    def _on_type_press(self, chord_type):
        self.current_type = chord_type
        self._highlight_current()
        if self.on_confirm:
            self.on_confirm(chord_type)


class TonalitySelectorMenu(MDCard):
    """
    Временное меню выбора тональности с горизонтальным скроллом
    Тона можно листать пальцем и нажимать для выбора
    """

    def __init__(self, current_tonality, on_confirm, on_cancel, **kwargs):
        super().__init__(**kwargs)
        self.current_tonality = current_tonality
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0, 0, 0, 0.08]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.8
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        self._build_ui()

    def _build_ui(self):
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        self.tones_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(8),
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )
        self.tones_container.bind(minimum_width=self.tones_container.setter('width'))

        self.tonality_btns = []
        for ton in TONALITIES:
            btn = MDRaisedButton(
                text=ton,
                size_hint=(None, 1),
                width=dp(48),
                md_bg_color=[0, 0, 0, 0],
                text_color=[1, 1, 1, 0.7],
                font_size=sp(16),
                elevation=0,
                on_release=lambda x, t=ton: self._on_tonality_press(t)
            )
            self.tonality_btns.append(btn)
            self.tones_container.add_widget(btn)

        self._highlight_current()

        scroll.add_widget(self.tones_container)
        self.add_widget(scroll)

    def _highlight_current(self):
        for btn in self.tonality_btns:
            if btn.text == self.current_tonality:
                btn.md_bg_color = [0.61, 0.15, 0.69, 1]
                btn.text_color = [1, 1, 1, 1]
            else:
                btn.md_bg_color = [0, 0, 0, 0]
                btn.text_color = [1, 1, 1, 0.7]

    def _on_tonality_press(self, tonality):
        self.current_tonality = tonality
        self._highlight_current()
        if self.on_confirm:
            self.on_confirm(tonality)


class UnifiedMenu(MDCard):
    """Единое меню 5 в 1: ТОН | ТИП | АККОРД | ВАРИАНТЫ | ПАЛЬЦЫ/НОТЫ"""

    def __init__(self,
                 tonality_value, type_value, chord_value,
                 on_tonality_press=None, on_type_press=None,
                 on_chord_press=None,
                 on_variants_press=None, on_mode_toggle=None,
                 variants_count=1, current_mode="finger",
                 chord_count=0,
                 **kwargs):
        super().__init__(**kwargs)

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0, 0, 0, 0.08]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.8
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        # 1. ТОН (иконка music-note-eighth) - ФИОЛЕТОВЫЙ
        self.tonality_item = IconMenuItem(
            icon_name="music-note-eighth",
            on_press=on_tonality_press,
            is_active=True,
            icon_color=[0.61, 0.15, 0.69, 1],
            fixed_color=True
        )

        # 2. ТИП (иконка tag) - БИРЮЗОВЫЙ
        self.type_item = IconMenuItem(
            icon_name="tag",
            on_press=on_type_press,
            is_active=True,
            icon_color=[0.0, 0.74, 0.83, 1],
            fixed_color=True
        )

        # 3. АККОРД (иконка music-circle) - активен только если есть > 1 аккорда
        has_chords = chord_count > 1
        self.chord_item = IconMenuItem(
            icon_name="music-circle",
            on_press=on_chord_press if has_chords else None,
            is_active=has_chords,
            icon_color=[1.0, 0.7, 0.0, 1] if has_chords else [1, 1, 1, 0.3]
        )

        # 4. ВАРИАНТЫ (иконка format-list-numbered) - СИНИЙ
        self.variants_item = IconMenuItem(
            icon_name="format-list-numbered",
            on_press=on_variants_press,
            is_active=(variants_count > 1),
            icon_color=[0.13, 0.59, 0.95, 1] if (variants_count > 1) else [1, 1, 1, 0.3]
        )

        # 5. ПАЛЬЦЫ/НОТЫ (иконка-тогл) - ОРАНЖЕВЫЙ / КРАСНЫЙ
        mode_icon = "gesture-tap" if current_mode == "finger" else "music-note"
        mode_color = [0.9, 0.55, 0.0, 1] if current_mode == "finger" else [0.8, 0.3, 0.3, 1]
        self.mode_item = IconMenuItem(
            icon_name=mode_icon,
            on_press=on_mode_toggle,
            is_active=True,
            icon_color=mode_color,
            fixed_color=True
        )

        # Добавляем разделители между пунктами
        self.add_widget(self.tonality_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.type_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.chord_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.variants_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.mode_item)

    def _create_divider(self):
        return MDBoxLayout(
            size_hint_x=None,
            width=dp(1),
            md_bg_color=[1, 1, 1, 0.1]
        )

    def update_chord(self, chord_count):
        has_chords = chord_count > 1
        self.chord_item.is_active = has_chords
        self.chord_item.on_press_callback = self.chord_item.on_press_callback if has_chords else None
        if has_chords:
            self.chord_item.set_color([1.0, 0.7, 0.0, 1])
            self.chord_item.icon_btn.opacity = 1
        else:
            self.chord_item.set_color([1, 1, 1, 0.3])
            self.chord_item.icon_btn.opacity = 0.6
        self.chord_item.update_state()

    def update_variants(self, count):
        has_variants = count > 1
        self.variants_item.is_active = has_variants
        if has_variants:
            self.variants_item.set_color([0.13, 0.59, 0.95, 1])
            self.variants_item.icon_btn.opacity = 1
        else:
            self.variants_item.set_color([1, 1, 1, 0.3])
            self.variants_item.icon_btn.opacity = 0.6
        self.variants_item.update_state()

    def update_mode(self, mode):
        is_finger = (mode == "finger")
        if is_finger:
            self.mode_item.set_icon("gesture-tap")
            self.mode_item.set_color([0.9, 0.55, 0.0, 1])
        else:
            self.mode_item.set_icon("music-note")
            self.mode_item.set_color([0.8, 0.3, 0.3, 1])


class ChordsScreen(BaseScreen):
    TONALITIES = TONALITIES
    CHORD_TYPES = CHORD_TYPES
    """Экран аккордов с единым меню 5 в 1 под грифом - СТАТИЧНЫЙ, БЕЗ ПРОКРУТКИ"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chords'
        self.all_chords = []
        self.current_chord_module = None
        self.is_search_mode = False
        self.search_results = []

        self.current_tonality = "A"
        self.current_tonality_index = 0

        self.current_type = "Major"
        self.current_type_index = 0

        self.current_chord_name = "A"
        self.current_chord_data = None
        self.current_chord_index = 0
        self.available_chords = []

        self.current_position = 1
        self.current_variants = []
        self.current_variant_index = 0

        self.current_mode = "finger"

        self.search_bar = None
        self.unified_menu = None
        self.chord_name_label = None
        self.chord_desc_label = None
        self.chord_renderer = None
        self.tonality_selector = None
        self.type_selector = None
        self.chord_selector = None
        self._menu_container = None
        self._info_label = None  # Единый лейбл для описания и подсказок
        self._hint_timer = None

        self.bg_image = None

        self.init_ui()
        self.load_background()
        self.scan_chords()

        logger.info('Экран аккордов создан (статичный, без прокрутки)')

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

    def _update_desc_height(self, instance, texture_size):
        """Обновляет высоту лейбла в зависимости от размера текстуры."""
        if texture_size:
            # Добавляем небольшой отступ
            new_height = texture_size[1] + dp(8)
            if self._info_label.height != new_height:
                self._info_label.height = new_height

    def init_ui(self):
        # Создаём контент БЕЗ ScrollView
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint=(1, 1),  # Растягиваем на весь экран
            padding=[dp(12), dp(8), dp(12), dp(16)]
        )

        # ============ 1. ПОИСК ============
        self.search_bar = SearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        content.add_widget(self.search_bar)

        # ============ 2. НАЗВАНИЕ АККОРДА ============
        self.chord_name_label = MDLabel(
            text="A | Amaj",
            font_size=sp(22),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(32),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95]
        )
        content.add_widget(self.chord_name_label)

        # ============ 3. ГРИФ ============
        griff_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(240),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )

        self.chord_renderer = ChordRenderer()
        griff_container.add_widget(self.chord_renderer)
        content.add_widget(griff_container)

        # ============ 4. КОНТЕЙНЕР ДЛЯ МЕНЮ ============
        self._menu_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(60),
            md_bg_color=[0, 0, 0, 0],
            padding=[0, 0, 0, 0]
        )
        content.add_widget(self._menu_container)

        # Добавляем основное меню в контейнер
        self.unified_menu = UnifiedMenu(
            tonality_value=self.current_tonality,
            type_value=self.current_type,
            chord_value=self.current_chord_name,
            on_tonality_press=self._open_tonality_selector,
            on_type_press=self._open_type_selector,
            on_chord_press=self._open_chord_selector if len(self.available_chords) > 1 else None,
            on_variants_press=self._next_variant,
            on_mode_toggle=self._toggle_mode,
            variants_count=len(self.current_variants),
            current_mode=self.current_mode,
            chord_count=len(self.available_chords)
        )
        self._menu_container.add_widget(self.unified_menu)

        # ============ 5. ИНФОРМАЦИОННЫЙ ЛЕЙБЛ (ОПИСАНИЕ/ПОДСКАЗКИ) ============
        # Единый лейбл для отображения ИЛИ описания аккорда, ИЛИ подсказок
        self._info_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(30),  # Начальная высота
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
        )
        # Позволяем тексту занимать несколько строк
        self._info_label.text_size = (None, None)
        self._info_label.bind(texture_size=self._update_desc_height)
        content.add_widget(self._info_label)

        # Добавляем растягивающийся виджет внизу
        content.add_widget(Widget(size_hint_y=1))

        # Строим UI БЕЗ скролла (use_scroll=False)
        self.build_ui(content_widget=content, use_scroll=False)

        try:
            bg_data = load_asset_as_bytes("griff_png")
            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="png")
                if img and img.texture:
                    self.chord_renderer.set_background(img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

        # Загружаем начальный аккорд
        self.load_current_variant()

    def _show_description(self):
        """Показывает описание аккорда в информационном лейбле."""
        if not self.current_variants:
            return

        variant = self.current_variants[self.current_variant_index]
        description = variant.get('description', '')

        if description:
            desc_parts = [p.strip() for p in description.replace('!', '|').split('|') if p.strip()]

            # Убираем дубликаты
            unique_parts = []
            for part in desc_parts:
                if part not in unique_parts:
                    unique_parts.append(part)

            # Формируем описание
            if unique_parts:
                chord_name = variant['name'].replace('!', ' | ').replace('$', '/')
                name_parts = [p.strip() for p in chord_name.split('|') if p.strip()]
                main_name = name_parts[0] if name_parts else ""

                formatted_desc = unique_parts[0]
                if main_name and main_name in formatted_desc:
                    formatted_desc = formatted_desc.replace(main_name, '').strip(' |')
                formatted_desc = re.sub(r'\s*\|\s*', ' | ', formatted_desc).strip(' |')
                formatted_desc = re.sub(r'\s+', ' ', formatted_desc)

                self._info_label.text = formatted_desc
            else:
                self._info_label.text = TYPE_DISPLAY.get(self.current_type, self.current_type)
        else:
            self._info_label.text = TYPE_DISPLAY.get(self.current_type, self.current_type)

    def _show_hint(self, text):
        """Показывает подсказку в информационном лейбле (временная замена описания)."""
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

        self._info_label.text = text

    def _show_temporary_hint(self, text, duration=1.5):
        """Показывает временную подсказку, заменяя описание."""
        if self._info_label:
            self._info_label.text = text
            if hasattr(self, '_hint_timer') and self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._restore_description(), duration)

    def _restore_description(self):
        """Восстанавливает описание аккорда после подсказки."""
        if hasattr(self, '_hint_timer'):
            self._hint_timer = None
        self._show_description()

    def _open_tonality_selector(self):
        logger.info("Открытие меню выбора тональности")

        if self.unified_menu and self.unified_menu.parent:
            self._menu_container.remove_widget(self.unified_menu)

        self.tonality_selector = TonalitySelectorMenu(
            current_tonality=self.current_tonality,
            on_confirm=self._on_tonality_confirmed,
            on_cancel=self._close_tonality_selector
        )
        self._menu_container.add_widget(self.tonality_selector)
        self._show_hint("Выберите тональность")

    def _on_tonality_confirmed(self, selected_tonality):
        logger.info(f"Выбрана тональность: {selected_tonality}")
        self.current_tonality = selected_tonality
        self.current_tonality_index = TONALITIES.index(selected_tonality)
        self.update_available_chords()
        self._close_tonality_selector()

    def _close_tonality_selector(self):
        logger.info("Закрытие меню выбора тональности")

        if self.tonality_selector and self.tonality_selector.parent:
            self._menu_container.remove_widget(self.tonality_selector)
            self.tonality_selector = None

        if self.unified_menu and not self.unified_menu.parent:
            self._menu_container.add_widget(self.unified_menu)

        # Восстанавливаем описание
        self._restore_description()

    def _open_type_selector(self):
        logger.info("Открытие меню выбора типа аккорда")

        if self.unified_menu and self.unified_menu.parent:
            self._menu_container.remove_widget(self.unified_menu)

        self.type_selector = TypeSelectorMenu(
            current_type=self.current_type,
            on_confirm=self._on_type_confirmed,
            on_cancel=self._close_type_selector
        )
        self._menu_container.add_widget(self.type_selector)
        self._show_hint("Выберите тип аккорда")

    def _on_type_confirmed(self, selected_type):
        logger.info(f"Выбран тип: {selected_type}")
        self.current_type = selected_type
        self.current_type_index = CHORD_TYPES.index(selected_type)
        self.update_available_chords()
        self._close_type_selector()

    def _close_type_selector(self):
        logger.info("Закрытие меню выбора типа аккорда")

        if self.type_selector and self.type_selector.parent:
            self._menu_container.remove_widget(self.type_selector)
            self.type_selector = None

        if self.unified_menu and not self.unified_menu.parent:
            self._menu_container.add_widget(self.unified_menu)

        # Восстанавливаем описание
        self._restore_description()

    def _open_chord_selector(self):
        if len(self.available_chords) <= 1:
            return

        logger.info("Открытие меню выбора аккорда")

        if self.unified_menu and self.unified_menu.parent:
            self._menu_container.remove_widget(self.unified_menu)

        self.chord_selector = ChordSelectorMenu(
            available_chords=self.available_chords,
            current_chord=self.current_chord_name,
            on_confirm=self._on_chord_confirmed,
            on_cancel=self._close_chord_selector
        )
        self._menu_container.add_widget(self.chord_selector)
        self._show_hint("Выберите вид данного аккорда")

    def _on_chord_confirmed(self, selected_chord):
        logger.info(f"Выбран аккорд: {selected_chord}")

        self.current_chord_name = selected_chord
        self.current_chord_index = self.available_chords.index(selected_chord)
        self._load_variants_for_chord(self.current_chord_name)
        self.load_current_variant()
        self._close_chord_selector()

    def _close_chord_selector(self):
        logger.info("Закрытие меню выбора аккорда")

        if self.chord_selector and self.chord_selector.parent:
            self._menu_container.remove_widget(self.chord_selector)
            self.chord_selector = None

        if self.unified_menu and not self.unified_menu.parent:
            self._menu_container.add_widget(self.unified_menu)

        # Восстанавливаем описание
        self._restore_description()

    def _toggle_mode(self):
        if self.current_mode == "finger":
            self.current_mode = "notes"
            self._show_temporary_hint("Выбран режим показа нот", 1.2)
        else:
            self.current_mode = "finger"
            self._show_temporary_hint("Выбран режим постановки пальцев", 1.2)

        self.unified_menu.update_mode(self.current_mode)

        if self.current_chord_module and self.chord_renderer:
            self.chord_renderer.set_mode(self.current_mode)

        logger.info(f"Режим отображения: {self.current_mode}")

    def _next_variant(self):
        if not self.current_variants or len(self.current_variants) <= 1:
            notify.info("Нет других вариантов")
            return

        total = len(self.current_variants)
        self.current_variant_index = (self.current_variant_index + 1) % total
        self.current_position = self.current_variant_index + 1
        self.load_current_variant()
        self._show_temporary_hint(f"Изменена позиция аккорда: {self.current_position}", 1.2)
        logger.info(f"Вариант {self.current_position}/{total}")

    def do_search(self, query):
        """Поиск аккордов по точному совпадению названия или описания"""
        query_original = query.strip()
        query_lower = query_original.lower()

        if not query_lower:
            if self.is_search_mode:
                self.clear_search()
            return

        self.is_search_mode = True
        self.search_results = []

        import string
        query_for_desc = query_lower
        for punct in string.punctuation:
            query_for_desc = query_for_desc.replace(punct, ' ')
        query_for_desc = ' '.join(query_for_desc.split())

        alt_map = {
            'bb': 'a#', 'a#': 'bb', 'db': 'c#', 'c#': 'db',
            'eb': 'd#', 'd#': 'eb', 'gb': 'f#', 'f#': 'gb',
            'ab': 'g#', 'g#': 'ab'
        }
        alt_query = alt_map.get(query_lower, None)

        for chord in self.all_chords:
            short_name_lower = chord['short_name'].lower()
            if short_name_lower == query_lower or (alt_query and short_name_lower == alt_query):
                if chord not in self.search_results:
                    self.search_results.append(chord)

        if not self.search_results:
            for chord in self.all_chords:
                description = chord.get('description', '')
                if description:
                    desc_clean = description.lower()
                    for punct in string.punctuation:
                        desc_clean = desc_clean.replace(punct, ' ')
                    desc_clean = ' '.join(desc_clean.split())
                    if desc_clean == query_for_desc:
                        if chord not in self.search_results:
                            self.search_results.append(chord)

        unique_results = []
        seen_names = set()
        for chord in self.search_results:
            if chord['short_name'] not in seen_names:
                seen_names.add(chord['short_name'])
                unique_results.append(chord)

        self.search_results = unique_results

        if self.search_results:
            selected_chord = self.search_results[0]
            self.current_chord_name = selected_chord['short_name']
            self.unified_menu.update_chord(len(self.available_chords))

            variants = []
            for chord in self.all_chords:
                if chord['short_name'] == self.current_chord_name:
                    variants.append(chord)

            if variants:
                variants.sort(key=lambda x: x['variant'])
                self.current_variants = variants
                self.current_variant_index = 0
                self.current_position = 1
                self.unified_menu.update_variants(len(variants))
                self.load_current_variant()

            notify.info(f"Найдено аккордов: {len(self.search_results)}", duration=1.5)
        else:
            self.search_bar.search_field.hint_text = f"'{query}' не найдено"
            Clock.schedule_once(lambda dt: self._reset_hint(), 2)

    def _reset_hint(self):
        self.search_bar.search_field.hint_text = "Поиск аккордов..."

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.search_field.hint_text = "Поиск аккордов..."
        self.update_available_chords()

    def _load_variants_for_chord(self, chord_name):
        variants = []
        for chord in self.all_chords:
            if chord['short_name'] == chord_name:
                tonality = self.extract_tonality(chord['name'])
                if tonality == self.current_tonality:
                    chord_types = chord['type'].split('|') if chord['type'] else []
                    if self.current_type in chord_types or self.current_type == chord.get('type', ''):
                        variants.append(chord)

        if variants:
            variants.sort(key=lambda x: x['variant'])
            self.current_variants = variants
            self.current_variant_index = 0
            self.current_position = 1
            self.unified_menu.update_variants(len(variants))
            self.load_current_variant()
        else:
            self.current_variants = []
            self.current_variant_index = 0
            self.current_position = 1
            self.unified_menu.update_variants(0)

    # ============ ЗАГРУЗКА АККОРДОВ ============
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
        self.update_available_chords()

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

    def update_available_chords(self):
        if self.is_search_mode:
            return
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

        self.available_chords = sorted(chords_by_name.keys())

        # Обновляем состояние иконки аккорда
        self.unified_menu.update_chord(len(self.available_chords))
        # Обновляем колбэк для иконки аккорда
        if len(self.available_chords) > 1:
            self.unified_menu.chord_item.on_press_callback = self._open_chord_selector
        else:
            self.unified_menu.chord_item.on_press_callback = None

        if self.available_chords:
            if self.current_chord_name not in self.available_chords:
                self.current_chord_index = 0
                self.current_chord_name = self.available_chords[0]

            chord_data = chords_by_name.get(self.current_chord_name)
            if chord_data:
                self.load_chord_variants(chord_data)
        else:
            self.available_chords = []
            self.current_variants = []
            self.current_chord_data = None

    def extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def load_chord_variants(self, variants):
        if not variants:
            return
        variants.sort(key=lambda x: x['variant'])
        self.current_variants = variants
        self.current_variant_index = 0
        self.current_position = 1
        self.unified_menu.update_variants(len(variants))
        self.load_current_variant()

    def load_current_variant(self):
        """Загружает текущий вариант аккорда и обновляет UI."""
        if not self.current_variants:
            return
        variant = self.current_variants[self.current_variant_index]
        self.current_chord_module = variant['module']

        chord_name = variant['name'].replace('!', ' | ').replace('$', '/')
        name_parts = [p.strip() for p in chord_name.split('|') if p.strip()]

        if len(name_parts) > 1:
            main_name = name_parts[0]
            other_names = []
            for name in name_parts[1:]:
                if name != main_name and name not in other_names:
                    other_names.append(name)

            if other_names:
                display_name = f"{main_name} ({', '.join(other_names)})"
            else:
                display_name = main_name
        else:
            display_name = name_parts[0] if name_parts else "?"

        self.chord_name_label.text = display_name

        # Показываем описание
        self._show_description()

        if self.chord_renderer:
            self.chord_renderer.load_chord(self.current_chord_module)
            self.chord_renderer.set_mode(self.current_mode)

    def _compact_description(self, parts):
        if len(parts) == 1:
            return parts[0]

        def find_longest_common_substring(strings):
            if not strings:
                return ""
            shortest = min(strings, key=len)
            longest_common = ""
            for i in range(len(shortest)):
                for j in range(i + 1, len(shortest) + 1):
                    substring = shortest[i:j]
                    if all(substring in s for s in strings):
                        if len(substring) > len(longest_common):
                            longest_common = substring
            return longest_common

        common_substring = find_longest_common_substring(parts)

        if common_substring:
            unique_parts = []
            for part in parts:
                unique = part.replace(common_substring, '').strip()
                if unique:
                    unique_parts.append(unique)

            unique_parts_unique = []
            for up in unique_parts:
                if up not in unique_parts_unique:
                    unique_parts_unique.append(up)

            first_unique = unique_parts_unique[0] if unique_parts_unique else ""
            other_uniques = unique_parts_unique[1:] if len(unique_parts_unique) > 1 else []

            if other_uniques:
                return f"{first_unique} ({', '.join(other_uniques)}) {common_substring}".strip()
            else:
                return f"{first_unique} {common_substring}".strip()
        else:
            return ', '.join(parts)

    def load_chord_by_name(self, chord_name):
        for chord in self.all_chords:
            if chord['short_name'].lower() == chord_name.lower():
                tonality = self.extract_tonality(chord['name'])
                if tonality in TONALITIES:
                    self.current_tonality = tonality
                    self.current_tonality_index = TONALITIES.index(tonality)
                    self.update_available_chords()

                    if self.current_chord_name != chord_name:
                        if chord_name in self.available_chords:
                            self.current_chord_name = chord_name
                            self.current_chord_index = self.available_chords.index(chord_name)
                            self._load_variants_for_chord(self.current_chord_name)
                break

    def select_chord_by_name(self, chord_name):
        logger.info(f"🎸 select_chord_by_name: ищем аккорд '{chord_name}'")

        target_chord = None
        for chord in self.all_chords:
            if chord['short_name'] == chord_name:
                target_chord = chord
                break

        if not target_chord:
            for chord in self.all_chords:
                name_variants = chord['name'].split('|')
                for variant in name_variants:
                    variant_clean = variant.strip().replace('$', '/')
                    if variant_clean == chord_name:
                        target_chord = chord
                        logger.info(f"   Найден по альтернативному названию: {chord['short_name']}")
                        break
                if target_chord:
                    break

        if not target_chord:
            alt_name = chord_name.replace('#', 'b')
            if alt_name != chord_name:
                logger.info(f"   Пробуем альтернативное написание: {alt_name}")
                return self.select_chord_by_name(alt_name)

        if target_chord:
            full_name = target_chord['name']
            tonality = self._extract_tonality_from_name(full_name)
            chord_type = target_chord.get('type', 'Major')

            logger.info(f"   Найден: {target_chord['short_name']}, тональность: {tonality}, тип: {chord_type}")

            if tonality in self.TONALITIES:
                self.current_tonality = tonality
                self.current_tonality_index = self.TONALITIES.index(tonality)

            if chord_type in self.CHORD_TYPES:
                self.current_type = chord_type
                self.current_type_index = self.CHORD_TYPES.index(chord_type)

            self.update_available_chords()

            chord_key = target_chord['short_name']
            if chord_key in self.available_chords:
                self.current_chord_name = chord_key
                self.current_chord_index = self.available_chords.index(chord_key)
                self._load_variants_for_chord(self.current_chord_name)
                self.load_current_variant()
                logger.info(f"✅ Аккорд {chord_name} успешно загружен")
                return True
            else:
                logger.warning(f"⚠️ Аккорд {chord_key} не найден в available_chords")
                return self._find_and_load_chord_variant(target_chord)
        else:
            logger.warning(f"⚠️ Аккорд {chord_name} не найден в базе")
            notify.warning(f"Аккорд {chord_name} не найден")
            return False

    def _extract_tonality_from_name(self, chord_name):
        if not chord_name:
            return "A"
        match = re.match(r'^([A-H][#b]?)', chord_name)
        if match:
            return match.group(1)
        return chord_name[0] if chord_name else "A"

    def _find_and_load_chord_variant(self, target_chord):
        logger.info(f"🔍 _find_and_load_chord_variant для {target_chord['short_name']}")

        variants = []
        for chord in self.all_chords:
            if chord['short_name'] == target_chord['short_name']:
                variants.append(chord)

        if variants:
            variants.sort(key=lambda x: x['variant'])
            self.current_variants = variants
            self.current_variant_index = 0
            self.current_position = 1
            self.unified_menu.update_variants(len(variants))
            self.current_chord_name = target_chord['short_name']
            self.load_current_variant()
            logger.info(f"✅ Загружен вариант аккорда {target_chord['short_name']}")
            return True
        else:
            logger.error(f"❌ Не найдено вариантов для {target_chord['short_name']}")
            return False

    def _extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        match = re.match(r'^([A-H][#b]?)', chord_name)
        if match:
            return match.group(1)
        return chord_name[0] if chord_name else ""

    # ============ МЕТОДЫ ДЛЯ ВОЗВРАТА НА ПРЕДЫДУЩИЙ ЭКРАН ============

    def on_enter(self):
        logger.info("🚪 Вход в экран аккордов")

        pending_chord = screen_state.get_pending_chord()
        if pending_chord:
            logger.info(f"🎸 Есть ожидающий аккорд: {pending_chord}")
            Clock.schedule_once(lambda dt: self.select_chord_by_name(pending_chord), 0.1)
            screen_state.clear_pending_chord()

        previous_screen = screen_state.get_previous_screen()
        if previous_screen:
            Clock.schedule_once(lambda dt: self._show_back_button(), 0.3)

        if self.tonality_selector:
            self._close_tonality_selector()
        if self.type_selector:
            self._close_type_selector()
        if self.chord_selector:
            self._close_chord_selector()

    def _show_back_button(self):
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.back_btn.opacity = 1
                app.top_nav.back_btn.disabled = False
                app.top_nav._custom_back_callback = self.go_back
                app.top_nav.screen_title.text = "Аккорды"
                logger.info("✅ Кнопка возврата принудительно показана")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")

    def on_leave(self):
        logger.info("🚪 Выход из экрана аккордов")
        if self.tonality_selector:
            self._close_tonality_selector()
        if self.type_selector:
            self._close_type_selector()
        if self.chord_selector:
            self._close_chord_selector()
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        logger.info("🔙 Нажата кнопка возврата")

        previous_screen = screen_state.get_previous_screen()
        logger.info(f"   Сохранённый предыдущий экран: {previous_screen}")

        if previous_screen and self.manager and self.manager.has_screen(previous_screen):
            screen_state.clear_pending_chord()
            self.manager.current = previous_screen
            logger.info(f"✅ Возврат на экран: {previous_screen}")
        else:
            logger.warning(f"Нет сохранённого предыдущего экрана или он не существует: {previous_screen}")
            if self.manager and self.manager.has_screen('song_detail'):
                self.manager.current = 'song_detail'
            elif self.manager and self.manager.has_screen('home'):
                self.manager.current = 'home'