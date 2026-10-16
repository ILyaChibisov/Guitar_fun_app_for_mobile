# screens/chords_screen.py
"""
Экран гитарных аккордов - с единым меню 5 в 1 под грифом
ТОН | ТИП | АККОРД | ВАРИАНТЫ | ПАЛЬЦЫ/НОТЫ
СТАТИЧНЫЙ ЭКРАН - БЕЗ ПРОКРУТКИ
С КЭШИРОВАНИЕМ МЕНЮ
СВАЙП ВЛЕВО/ВПРАВО МЕНЯЕТ ВАРИАНТ АККОРДА
ТРЕТЬЯ ИКОНКА - СЕЛЕКТОР АККОРДОВ (как первые две)
В РАМКЕ - ОСНОВНОЕ ИМЯ АККОРДА (по центру)
ПОД МЕНЮ - ОПИСАНИЕ + "Варианты записи:" + ВСЕ ИМЕНА
ПОИСК В СТИЛЕ ЯНДЕКС; ПОД РАМКОЙ - СТАТУС ПОИСКА (найдено / не найдено)
"""
from kivy.uix.behaviors import ButtonBehavior
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.uix.textinput import TextInput
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.carousel import Carousel
from io import BytesIO
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


# ============ КОНТЕЙНЕР С КАРУСЕЛЬЮ ============
class SwipeContainer(MDBoxLayout):
    """
    Контейнер с Carousel для аккордов.
    Горизонтальный свайп — переключение ВАРИАНТОВ аккорда.
    В рамке — только ОСНОВНОЕ имя аккорда (центрировано).
    """

    _NAME_FONT_BASE = sp(22)
    _NAME_FONT_MIN = sp(12)
    _NAME_PADDING = dp(20)
    _CARD_MIN_WIDTH = dp(120)
    _CARD_MAX_WIDTH = dp(280)
    _CHAR_WIDTH_FACTOR = 0.62

    def __init__(self, on_swipe_horizontal=None, **kwargs):
        super().__init__(**kwargs)
        self.on_swipe_horizontal = on_swipe_horizontal
        self._touch_start_x = 0
        self._touch_start_y = 0
        self._touch_moved = False
        self._is_dragging = False
        self._drag_threshold = 20

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(460)
        self.md_bg_color = [0, 0, 0, 0]
        self.spacing = 0

        # ============ БЛОК НАЗВАНИЯ АККОРДА ============
        self.name_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(96),
            padding=[dp(8), dp(8), dp(8), dp(24)],
            md_bg_color=[0, 0, 0, 0]
        )

        self.chord_name_card = MDCard(
            orientation='vertical',
            size_hint=(None, None),
            size=(dp(140), dp(52)),
            pos_hint={'center_x': 0.5},
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            line_color=[1, 1, 1, 0.15],
            line_width=0.8,
            padding=[dp(4), dp(4), dp(4), dp(4)],
            spacing=dp(0)
        )

        self.chord_name_label = MDLabel(
            text="A",
            font_size=sp(22),
            bold=True,
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.83, 0.69, 0.22, 1],  # тёмно-оранжевый золотой
        )
        self.chord_name_card.add_widget(self.chord_name_label)

        self.name_container.add_widget(self.chord_name_card)
        self.add_widget(self.name_container)

        self._current_main_name = ""

        # ============ КАРУСЕЛЬ ДЛЯ ГРИФОВ ============
        self.carousel = Carousel(
            direction='right',
            loop=True,
            size_hint=(1, 1),
            anim_move_duration=0.3
        )
        self.carousel.bind(current_slide=self._on_carousel_slide)
        self.add_widget(self.carousel)

        self.slides = []
        self.renderers = []
        self.current_index = 0

        self._programmatic_slide = False

    def _build_griff_wrapper(self):
        wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(8), dp(12), dp(8), dp(4)],
            md_bg_color=[0, 0, 0, 0]
        )
        return wrapper

    def add_slide(self, chord_module):
        slide = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )

        wrapper = self._build_griff_wrapper()

        renderer = ChordRenderer()

        try:
            bg_data = load_asset_as_bytes("griff_png")
            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="png")
                if img and img.texture:
                    renderer.set_background(img.texture)
        except Exception as e:
            logger.error(f"Ошибка загрузки фона грифа: {e}")

        if chord_module:
            renderer.load_chord(chord_module)
            renderer.set_mode("finger")

        wrapper.add_widget(renderer)
        slide.add_widget(wrapper)
        self.carousel.add_widget(slide)
        self.slides.append(slide)
        self.renderers.append(renderer)
        return slide, renderer

    def clear_slides(self):
        self.carousel.clear_widgets()
        self.slides = []
        self.renderers = []
        self.current_index = 0

    def set_current_slide(self, index):
        if 0 <= index < len(self.slides):
            self._programmatic_slide = True
            self.carousel.load_slide(self.slides[index])
            self.current_index = index
            Clock.schedule_once(lambda dt: setattr(self, '_programmatic_slide', False), 0.35)

    def _on_carousel_slide(self, instance, slide):
        if not self.slides:
            return

        try:
            index = self.slides.index(slide)
            if index != self.current_index:
                self.current_index = index
        except ValueError:
            pass

    # ============ ОБНОВЛЕНИЕ НАЗВАНИЯ ============

    def _calc_card_width_and_font(self, name):
        font_size = self._NAME_FONT_BASE

        def natural_width(fs):
            return len(name) * fs * self._CHAR_WIDTH_FACTOR + 2 * self._NAME_PADDING + dp(16)

        total = natural_width(font_size)
        if total > self._CARD_MAX_WIDTH:
            k = self._CARD_MAX_WIDTH / total
            font_size = max(self._NAME_FONT_MIN, font_size * k)
            total = natural_width(font_size)

        card_width = max(self._CARD_MIN_WIDTH, min(total, self._CARD_MAX_WIDTH))
        return card_width, font_size

    def update_chord_name(self, display_name):
        display_name = (display_name or "?").strip()
        if display_name == self._current_main_name:
            return

        self._current_main_name = display_name

        anim_out = Animation(opacity=0, duration=0.12, t='out_quad')
        anim_out.bind(on_complete=lambda *a: self._apply_name(display_name))
        anim_out.start(self.name_container)

    def _apply_name(self, name):
        card_width, font_size = self._calc_card_width_and_font(name)

        self.chord_name_label.text = name
        self.chord_name_label.font_size = font_size
        self.chord_name_card.width = card_width

        anim_in = Animation(opacity=1, duration=0.15, t='in_quad')
        anim_in.start(self.name_container)

    # ============ ОБРАБОТКА КАСАНИЙ ============

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start_x = touch.x
            self._touch_start_y = touch.y
            self._touch_moved = False
            self._is_dragging = False
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            dx = touch.x - self._touch_start_x
            dy = touch.y - self._touch_start_y

            if abs(dx) > self._drag_threshold or abs(dy) > self._drag_threshold:
                self._touch_moved = True
                self._is_dragging = True

            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self._touch_moved:
                dx = touch.x - self._touch_start_x
                dy = touch.y - self._touch_start_y

                abs_dx = abs(dx)
                abs_dy = abs(dy)

                if abs_dx > 50 and abs_dx > abs_dy:
                    if dx < 0:
                        if self.on_swipe_horizontal:
                            self.on_swipe_horizontal(1)
                        self.carousel.load_next()
                    else:
                        if self.on_swipe_horizontal:
                            self.on_swipe_horizontal(-1)
                        self.carousel.load_previous()

            touch.ungrab(self)
            self._touch_moved = False
            self._is_dragging = False
            return True
        return super().on_touch_up(touch)

    def update_renderer_mode(self, mode):
        for renderer in self.renderers:
            renderer.set_mode(mode)


# ============ ПОИСКОВАЯ СТРОКА (стиль Яндекс) ============
class SearchBar(MDCard):
    """
    Поисковая строка в стиле Яндекс:
    - тонкая серая обводка
    - поле ввода слева (без нижней полосы)
    - круглая серая кнопка «×» (появляется при вводе)
    - тёмно-зелёная кнопка «Найти» справа
    """

    _BORDER = [0.75, 0.75, 0.75, 1]
    _BTN_BG = [0.10, 0.42, 0.25, 1]
    _BTN_TEXT = [1, 1, 1, 1]
    _CLEAR_BG = [0.75, 0.75, 0.75, 1]

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(52)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [1, 1, 1, 1]
        self.elevation = 0
        self.line_color = self._BORDER
        self.line_width = 1.4
        self.padding = [dp(12), dp(6), dp(6), dp(6)]
        self.spacing = dp(6)

        self.search_field = TextInput(
            hint_text="Найти аккорд",
            multiline=False,
            size_hint_x=1,
            height=dp(40),
            font_size=sp(16),
            background_color=[1, 1, 1, 0],
            background_normal="",
            background_active="",
            foreground_color=[0.1, 0.1, 0.1, 1],
            hint_text_color=[0.55, 0.55, 0.55, 1],
            cursor_color=[0.1, 0.1, 0.1, 1],
            padding=[0, dp(10), 0, dp(6)],
            on_text_validate=self._on_search_pressed
        )
        self.search_field.bind(text=self._on_text_change)
        self.search_field.bind(focus=self._on_focus)

        self.clear_wrapper = MDCard(
            size_hint=(None, None),
            size=(dp(34), dp(34)),
            radius=[dp(17), dp(17), dp(17), dp(17)],
            md_bg_color=self._CLEAR_BG,
            elevation=0,
            pos_hint={'center_y': 0.5},
            opacity=0,
            disabled=True
        )

        self.clear_btn = MDIconButton(
            icon="close",
            size_hint=(1, 1),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear_pressed
        )
        self.clear_wrapper.add_widget(self.clear_btn)

        self.search_btn = MDRaisedButton(
            text="Найти",
            size_hint=(None, None),
            size=(dp(88), dp(40)),
            md_bg_color=self._BTN_BG,
            text_color=self._BTN_TEXT,
            font_size=sp(15),
            elevation=0,
            pos_hint={'center_y': 0.5}
        )
        self.search_btn.bind(on_release=self._on_search_pressed)

        self.add_widget(self.search_field)
        self.add_widget(self.clear_wrapper)
        self.add_widget(self.search_btn)

    def _on_text_change(self, instance, text):
        self.current_query = text
        if text.strip():
            self.clear_wrapper.opacity = 1
            self.clear_wrapper.disabled = False
        else:
            self.clear_wrapper.opacity = 0
            self.clear_wrapper.disabled = True

    def _on_search_pressed(self, *args):
        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear_pressed(self, instance):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""
        if self.on_clear:
            self.on_clear()
        self.search_field.focus = True

    def _on_focus(self, instance, value):
        if value:
            self.line_width = 1.6
        else:
            self.line_width = 1.4

    def clear(self):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""

    def focus(self):
        self.search_field.focus = True


class IconMenuItem(ButtonBehavior, MDBoxLayout):
    """Пункт меню с иконкой"""

    def __init__(self, icon_name, on_press=None, is_active=False, icon_color=None, fixed_color=False, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press
        self.is_active = is_active
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
            self.icon_btn.icon_color = [0.46, 0.70, 0.71, 1]
            self.icon_btn.opacity = 1
        else:
            self.icon_btn.icon_color = [1, 1, 1, 0.3]
            self.icon_btn.opacity = 0.6

    def set_icon(self, icon_name):
        self.icon_name = icon_name
        self.icon_btn.icon = icon_name

    def set_color(self, color):
        self.icon_color = color
        self.icon_btn.icon_color = color


class BaseSelectorMenu(MDCard):
    """Базовый класс для всех меню-селекторов с кэшированием"""

    def __init__(self, on_confirm, on_cancel, **kwargs):
        super().__init__(**kwargs)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.is_visible = False

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

        self.scroll = None
        self.container = None
        self.buttons = []
        self.current_selection = None

        self._build_ui()

    def _build_ui(self):
        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        self.container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(8),
            padding=[dp(8), dp(8), dp(8), dp(8)]
        )
        self.container.bind(minimum_width=self.container.setter('width'))

        self._populate_items()

        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def _populate_items(self):
        pass

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
        for btn in self.buttons:
            is_selected = (btn.text == self.current_selection)
            if is_selected:
                btn.md_bg_color = [0.0, 0.74, 0.83, 1]
                btn.text_color = [1, 1, 1, 1]
            else:
                btn.md_bg_color = [0, 0, 0, 0]
                btn.text_color = [1, 1, 1, 0.7]

    def _on_item_press(self, value):
        self.current_selection = value
        self._highlight_current()
        if self.on_confirm:
            self.on_confirm(value)

    def show(self):
        self.is_visible = True
        self.opacity = 1
        self.disabled = False
        self._highlight_current()

    def hide(self):
        self.is_visible = False
        self.opacity = 0
        self.disabled = True


class TonalitySelectorMenu(BaseSelectorMenu):
    def __init__(self, current_tonality, on_confirm, on_cancel, **kwargs):
        self.current_tonality = current_tonality
        super().__init__(on_confirm, on_cancel, **kwargs)

    def _populate_items(self):
        self.buttons = []
        for ton in TONALITIES:
            btn = MDRaisedButton(
                text=ton,
                size_hint=(None, 1),
                width=dp(48),
                md_bg_color=[0, 0, 0, 0],
                text_color=[1, 1, 1, 0.7],
                font_size=sp(16),
                elevation=0,
                on_release=lambda x, t=ton: self._on_item_press(t)
            )
            self.buttons.append(btn)
            self.container.add_widget(btn)

        self.current_selection = self.current_tonality

    def set_current(self, tonality):
        self.current_selection = tonality
        self._highlight_current()


class TypeSelectorMenu(BaseSelectorMenu):
    def __init__(self, current_type, on_confirm, on_cancel, **kwargs):
        self.current_type = current_type
        super().__init__(on_confirm, on_cancel, **kwargs)

    def _populate_items(self):
        self.buttons = []
        for chord_type in CHORD_TYPES:
            btn = MDRaisedButton(
                text=chord_type,
                size_hint=(None, 1),
                width=self._get_button_width(chord_type),
                md_bg_color=[0, 0, 0, 0],
                text_color=[1, 1, 1, 0.7],
                font_size=sp(13),
                elevation=0,
                on_release=lambda x, t=chord_type: self._on_item_press(t)
            )
            self.buttons.append(btn)
            self.container.add_widget(btn)

        self.current_selection = self.current_type

    def set_current(self, chord_type):
        self.current_selection = chord_type
        self._highlight_current()


# ============ СЕЛЕКТОР АККОРДОВ ============
class ChordSelectorMenu(BaseSelectorMenu):
    """Селектор доступных аккордов для текущей тональности/типа."""

    def __init__(self, current_chord, on_confirm, on_cancel, chords=None, **kwargs):
        self.current_chord = current_chord
        self.chords = list(chords) if chords else []
        super().__init__(on_confirm, on_cancel, **kwargs)

    def _populate_items(self):
        self.buttons = []
        for chord_name in self.chords:
            btn = MDRaisedButton(
                text=chord_name,
                size_hint=(None, 1),
                width=self._get_button_width(chord_name),
                md_bg_color=[0, 0, 0, 0],
                text_color=[1, 1, 1, 0.7],
                font_size=sp(14),
                elevation=0,
                on_release=lambda x, t=chord_name: self._on_item_press(t)
            )
            self.buttons.append(btn)
            self.container.add_widget(btn)

        self.current_selection = self.current_chord

    def set_chords(self, chords, current_chord=None):
        self.chords = list(chords) if chords else []
        if current_chord is not None:
            self.current_chord = current_chord
            self.current_selection = current_chord

        self.container.clear_widgets()
        self.buttons = []
        self._populate_items()
        self._highlight_current()

    def set_current(self, chord_name):
        self.current_chord = chord_name
        self.current_selection = chord_name
        self._highlight_current()


class UnifiedMenu(MDCard):
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

        self.tonality_item = IconMenuItem(
            icon_name="music-note-eighth",
            on_press=on_tonality_press,
            is_active=True,
            icon_color=[0.61, 0.15, 0.69, 1],
            fixed_color=True
        )

        self.type_item = IconMenuItem(
            icon_name="tag",
            on_press=on_type_press,
            is_active=True,
            icon_color=[0.0, 0.74, 0.83, 1],
            fixed_color=True
        )

        has_chords = chord_count > 1
        self.chord_item = IconMenuItem(
            icon_name="music-circle",
            on_press=on_chord_press,
            is_active=True,
            icon_color=[1.0, 0.7, 0.0, 1] if has_chords else [1, 1, 1, 0.35],
            fixed_color=False
        )

        self.variants_item = IconMenuItem(
            icon_name="format-list-numbered",
            on_press=on_variants_press,
            is_active=(variants_count > 1),
            icon_color=[0.13, 0.59, 0.95, 1] if (variants_count > 1) else [1, 1, 1, 0.3]
        )

        mode_icon = "gesture-tap" if current_mode == "finger" else "music-note"
        mode_color = [0.9, 0.55, 0.0, 1] if current_mode == "finger" else [0.8, 0.3, 0.3, 1]
        self.mode_item = IconMenuItem(
            icon_name=mode_icon,
            on_press=on_mode_toggle,
            is_active=True,
            icon_color=mode_color,
            fixed_color=True
        )

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
        self.chord_item.is_active = True
        if has_chords:
            self.chord_item.set_color([1.0, 0.7, 0.0, 1])
            self.chord_item.icon_btn.opacity = 1
        else:
            self.chord_item.set_color([1, 1, 1, 0.35])
            self.chord_item.icon_btn.opacity = 0.7
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
        self.search_status_label = None    # <-- лейбл статуса под рамкой поиска
        self.unified_menu = None
        self._menu_container = None
        self._info_label = None
        self._hint_timer = None

        self.bg_image = None

        self.tonality_selector = None
        self.type_selector = None
        self.chord_selector = None
        self._menu_cache_initialized = False

        self._griff_height = dp(280)
        self._update_griff_timer = None

        self.swipe_container = None
        self._data_loaded = False

        self._current_main_name = ""
        self._current_alt_names = []
        self._current_all_names = []

        self.init_ui()
        self.load_background()

        Clock.schedule_once(self._create_cached_menus, 0.05)
        Clock.schedule_once(lambda dt: self.scan_chords(), 0.1)

        logger.info('Экран аккордов создан (с Carousel)')

    def _create_cached_menus(self, dt=None):
        if self._menu_cache_initialized:
            return

        logger.info("🔧 Создание кэшированных меню...")

        self.tonality_selector = TonalitySelectorMenu(
            current_tonality=self.current_tonality,
            on_confirm=self._on_tonality_confirmed,
            on_cancel=self._close_tonality_selector
        )
        self.tonality_selector.opacity = 0
        self.tonality_selector.disabled = True
        self._menu_container.add_widget(self.tonality_selector)

        self.type_selector = TypeSelectorMenu(
            current_type=self.current_type,
            on_confirm=self._on_type_confirmed,
            on_cancel=self._close_type_selector
        )
        self.type_selector.opacity = 0
        self.type_selector.disabled = True
        self._menu_container.add_widget(self.type_selector)

        self.chord_selector = ChordSelectorMenu(
            current_chord=self.current_chord_name,
            on_confirm=self._on_chord_confirmed,
            on_cancel=self._close_chord_selector,
            chords=self.available_chords
        )
        self.chord_selector.opacity = 0
        self.chord_selector.disabled = True
        self._menu_container.add_widget(self.chord_selector)

        self._menu_cache_initialized = True
        logger.info("✅ Кэшированные меню созданы")

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
        if texture_size:
            new_height = texture_size[1] + dp(8)
            if self._info_label.height != new_height:
                self._info_label.height = new_height

    def _update_griff_size(self, *args):
        if hasattr(self, 'swipe_container') and self.swipe_container:
            window_width = Window.width

            padding_total = dp(24)
            available_width = window_width - padding_total
            griff_height = available_width * 0.45

            min_height = dp(200)
            max_height = window_width * 0.6

            if griff_height < min_height:
                griff_height = min_height
            if griff_height > max_height:
                griff_height = max_height

            griff_height = int(griff_height)
            self._griff_height = griff_height

            self.swipe_container.height = griff_height + dp(120)

            logger.info(f"📐 Гриф обновлён: {griff_height}dp")

    def _add_chord_slide(self, chord_module):
        if self.swipe_container:
            self.swipe_container.add_slide(chord_module)

    def _rebuild_slides_for_current_chord(self):
        if not self.swipe_container:
            return

        self.swipe_container.clear_slides()

        for variant in self.current_variants:
            module = variant.get('module')
            if module:
                self.swipe_container.add_slide(module)

        self.swipe_container.update_renderer_mode(self.current_mode)

        if self.current_variants:
            self.swipe_container.set_current_slide(self.current_variant_index)

    def _update_display(self):
        if not self.current_variants:
            return

        variant = self.current_variants[self.current_variant_index]
        self.current_chord_module = variant['module']

        chord_name = variant['name'].replace('!', ' | ').replace('$', '/')
        name_parts = [p.strip() for p in chord_name.split('|') if p.strip()]

        unique_names = []
        for n in name_parts:
            if n not in unique_names:
                unique_names.append(n)

        if not unique_names:
            unique_names = ["?"]

        main_name = unique_names[0]
        alt_names = unique_names[1:] if len(unique_names) > 1 else []

        self._current_main_name = main_name
        self._current_alt_names = alt_names
        self._current_all_names = list(unique_names)

        logger.info(f"🎸 Основное имя: '{main_name}', все: {unique_names}")

        if self.swipe_container:
            self.swipe_container.update_chord_name(main_name)

        self._show_description()
        self._data_loaded = True

    def init_ui(self):
        padding = layout_config.get_content_padding()
        horizontal_padding = [padding[0], 0, padding[2], 0]

        content = MDBoxLayout(
            orientation='vertical',
            spacing=0,
            size_hint=(1, 1),
            padding=[0, 0, 0, 0]
        )

        # ---- Рамка поиска ----
        search_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(52),
            padding=[0, 0, 0, 0]
        )
        self.search_bar = SearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        search_container.add_widget(self.search_bar)
        content.add_widget(search_container)

        # ---- Лейбл СТАТУСА поиска (ПОД рамкой) ----
        # Место заложено заранее (dp(20)), чтобы layout не сдвигался.
        # По умолчанию скрыт (opacity=0).
        self.search_status_label = MDLabel(
            text="",
            font_size=sp(11),
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(20),
            opacity=0,
            theme_text_color="Custom",
            text_color=[0.6, 0.6, 0.6, 1],
            padding=[dp(4), 0, dp(4), 0],
        )
        self.search_status_label.text_size = (None, None)
        content.add_widget(self.search_status_label)

        # ---- Отступ между поиском и рамкой аккорда ----
        content.add_widget(Widget(size_hint_y=None, height=dp(16)))

        self.swipe_container = SwipeContainer(
            on_swipe_horizontal=self._on_swipe_horizontal
        )
        self.swipe_container.size_hint = (1, None)
        self.swipe_container.height = self._griff_height + dp(120)
        content.add_widget(self.swipe_container)

        Window.bind(on_resize=self._on_window_resize)

        content.add_widget(Widget(size_hint_y=None, height=dp(4)))

        menu_wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(60),
            padding=horizontal_padding
        )
        self._menu_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0],
            padding=[0, 0, 0, 0]
        )
        menu_wrapper.add_widget(self._menu_container)
        content.add_widget(menu_wrapper)

        self.unified_menu = UnifiedMenu(
            tonality_value=self.current_tonality,
            type_value=self.current_type,
            chord_value=self.current_chord_name,
            on_tonality_press=self._open_tonality_selector,
            on_type_press=self._open_type_selector,
            on_chord_press=self._open_chord_selector,
            on_variants_press=self._next_variant,
            on_mode_toggle=self._toggle_mode,
            variants_count=len(self.current_variants),
            current_mode=self.current_mode,
            chord_count=len(self.available_chords)
        )
        self._menu_container.add_widget(self.unified_menu)

        content.add_widget(Widget(size_hint_y=None, height=dp(2)))

        self._info_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
        )
        self._info_label.text_size = (None, None)
        self._info_label.bind(texture_size=self._update_desc_height)
        content.add_widget(self._info_label)

        content.add_widget(Widget(size_hint_y=1))

        self.build_ui(
            content_widget=content,
            use_scroll=False
        )

        Clock.schedule_once(self._update_griff_size, 0.1)
        Clock.schedule_once(self._update_griff_size, 0.3)
        Clock.schedule_once(self._update_griff_size, 0.5)

        Clock.schedule_once(lambda dt: self._update_display(), 0.2)

    # ============ СТАТУС ПОИСКА ============

    def _set_search_status(self, status):
        """
        status: 'found' | 'not_found' | None
        Показывает под рамкой поиска соответствующее сообщение.
        Место заложено заранее — layout не сдвигается.
        """
        if not self.search_status_label:
            return

        if status == 'found':
            self.search_status_label.text = "Мы нашли ваш аккорд"
            self.search_status_label.text_color = [0.35, 0.75, 0.45, 1]
            self.search_status_label.opacity = 1
        elif status == 'not_found':
            self.search_status_label.text = "По вашему запросу ничего не нашлось"
            self.search_status_label.text_color = [0.85, 0.45, 0.45, 1]
            self.search_status_label.opacity = 1
        else:
            self.search_status_label.text = ""
            self.search_status_label.opacity = 0

    # ============ ОБРАБОТЧИК ГОРИЗОНТАЛЬНОГО СВАЙПА ============

    def _on_swipe_horizontal(self, step):
        if not self.current_variants or len(self.current_variants) <= 1:
            self._show_temporary_hint("Нет других вариантов", 1.0)
            return

        total = len(self.current_variants)
        self.current_variant_index = (self.current_variant_index + step) % total
        self.current_position = self.current_variant_index + 1

        self._update_display()
        self._show_temporary_hint(
            f"Вариант {self.current_position}/{total}", 1.0
        )
        logger.info(f"🔄 Свайп: вариант {self.current_position}/{total}")

    def _find_chord_data(self, chord_name):
        for chord in self.all_chords:
            if chord['short_name'] == chord_name:
                return chord
        return None

    # ============ ОТКРЫТИЕ/ЗАКРЫТИЕ СЕЛЕКТОРА АККОРДОВ ============

    def _open_chord_selector(self):
        if self.chord_selector and self.chord_selector.is_visible:
            self._close_chord_selector()
            return

        if not self.available_chords:
            self._show_temporary_hint("Нет доступных аккордов", 1.0)
            return

        logger.info("Открытие меню выбора аккорда (кешированное)")

        if not self.chord_selector:
            self.chord_selector = ChordSelectorMenu(
                current_chord=self.current_chord_name,
                on_confirm=self._on_chord_confirmed,
                on_cancel=self._close_chord_selector,
                chords=self.available_chords
            )
            self.chord_selector.opacity = 0
            self.chord_selector.disabled = True
            self._menu_container.add_widget(self.chord_selector)

        self.chord_selector.set_chords(
            self.available_chords,
            current_chord=self.current_chord_name
        )

        if self.unified_menu and self.unified_menu.parent:
            self._menu_container.remove_widget(self.unified_menu)

        self.chord_selector.show()
        self._menu_container.add_widget(self.chord_selector)
        self._show_hint("Выберите аккорд")

    def _on_chord_confirmed(self, selected_chord):
        logger.info(f"Выбран аккорд: {selected_chord}")

        if not selected_chord or selected_chord == self.current_chord_name:
            self._close_chord_selector()
            return

        self.current_chord_name = selected_chord
        if selected_chord in self.available_chords:
            self.current_chord_index = self.available_chords.index(selected_chord)

        self._load_variants_for_chord(self.current_chord_name)

        if self.unified_menu:
            self.unified_menu.update_chord(len(self.available_chords))

        self._close_chord_selector()

    def _close_chord_selector(self):
        logger.info("Закрытие меню выбора аккорда")

        if self.chord_selector:
            self.chord_selector.hide()
            if self.chord_selector.parent:
                self._menu_container.remove_widget(self.chord_selector)

        if self.unified_menu and not self.unified_menu.parent:
            self._menu_container.add_widget(self.unified_menu)

        self._restore_description()

    # ============ ОПИСАНИЕ ПОД МЕНЮ ============

    def _show_description(self):
        """
        Формат: <описание>, Варианты записи: <все имена через запятую>
        """
        if not self.current_variants:
            self._info_label.text = ""
            return

        variant = self.current_variants[self.current_variant_index]

        parts = []

        description = variant.get('description', '')
        if description:
            desc_parts = [
                p.strip()
                for p in description.replace('!', '|').split('|')
                if p.strip()
            ]
            unique_desc = []
            for part in desc_parts:
                if part not in unique_desc:
                    unique_desc.append(part)

            if unique_desc:
                formatted_desc = unique_desc[0]
                main_name = self._current_main_name
                if main_name and main_name in formatted_desc:
                    formatted_desc = formatted_desc.replace(main_name, '').strip(' |,')
                formatted_desc = re.sub(r'\s*\|\s*', ', ', formatted_desc).strip(' ,')
                formatted_desc = re.sub(r'\s+', ' ', formatted_desc)

                if formatted_desc:
                    parts.append(formatted_desc)

        if self._current_all_names:
            variants_str = ", ".join(self._current_all_names)
            parts.append(f"Варианты записи: {variants_str}")

        if parts:
            self._info_label.text = ", ".join(parts)
        else:
            self._info_label.text = self._current_main_name or ""

    def _show_hint(self, text):
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None
        self._info_label.text = text

    def _show_temporary_hint(self, text, duration=1.5):
        if self._info_label:
            self._info_label.text = text
            if hasattr(self, '_hint_timer') and self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._restore_description(), duration)

    def _restore_description(self):
        if hasattr(self, '_hint_timer'):
            self._hint_timer = None
        self._show_description()

    def _open_tonality_selector(self):
        if self.tonality_selector and self.tonality_selector.is_visible:
            self._close_tonality_selector()
            return

        logger.info("Открытие меню выбора тональности (кешированное)")

        if not self.tonality_selector:
            self.tonality_selector = TonalitySelectorMenu(
                current_tonality=self.current_tonality,
                on_confirm=self._on_tonality_confirmed,
                on_cancel=self._close_tonality_selector
            )
            self.tonality_selector.opacity = 0
            self.tonality_selector.disabled = True
            self._menu_container.add_widget(self.tonality_selector)

        self.tonality_selector.set_current(self.current_tonality)

        if self.unified_menu and self.unified_menu.parent:
            self._menu_container.remove_widget(self.unified_menu)

        self.tonality_selector.show()
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

        if self.tonality_selector:
            self.tonality_selector.hide()
            if self.tonality_selector.parent:
                self._menu_container.remove_widget(self.tonality_selector)

        if self.unified_menu and not self.unified_menu.parent:
            self._menu_container.add_widget(self.unified_menu)

        self._restore_description()

    def _open_type_selector(self):
        if self.type_selector and self.type_selector.is_visible:
            self._close_type_selector()
            return

        logger.info("Открытие меню выбора типа аккорда (кешированное)")

        if not self.type_selector:
            self.type_selector = TypeSelectorMenu(
                current_type=self.current_type,
                on_confirm=self._on_type_confirmed,
                on_cancel=self._close_type_selector
            )
            self.type_selector.opacity = 0
            self.type_selector.disabled = True
            self._menu_container.add_widget(self.type_selector)

        self.type_selector.set_current(self.current_type)

        if self.unified_menu and self.unified_menu.parent:
            self._menu_container.remove_widget(self.unified_menu)

        self.type_selector.show()
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

        if self.type_selector:
            self.type_selector.hide()
            if self.type_selector.parent:
                self._menu_container.remove_widget(self.type_selector)

        if self.unified_menu and not self.unified_menu.parent:
            self._menu_container.add_widget(self.unified_menu)

        self._restore_description()

    def _toggle_mode(self):
        if self.current_mode == "finger":
            self.current_mode = "notes"
            self._show_temporary_hint("Выбран режим показа нот", 1.2)
        else:
            self.current_mode = "finger"
            self._show_temporary_hint("Выбран режим постановки пальцев", 1.2)

        self.unified_menu.update_mode(self.current_mode)

        if self.swipe_container:
            self.swipe_container.update_renderer_mode(self.current_mode)

        logger.info(f"Режим отображения: {self.current_mode}")

    def _next_variant(self):
        if not self.current_variants or len(self.current_variants) <= 1:
            notify.info("Нет других вариантов")
            return

        total = len(self.current_variants)
        self.current_variant_index = (self.current_variant_index + 1) % total
        self.current_position = self.current_variant_index + 1

        if self.swipe_container:
            self.swipe_container.carousel.load_next()

        self._update_display()
        self._show_temporary_hint(f"Изменена позиция аккорда: {self.current_position}", 1.2)
        logger.info(f"Вариант {self.current_position}/{total}")

    def do_search(self, query):
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
            # Найдено — показываем «Мы нашли ваш аккорд»
            self._set_search_status('found')

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

                self._rebuild_slides_for_current_chord()
                self._update_display()

            notify.info(f"Найдено аккордов: {len(self.search_results)}", duration=1.5)
        else:
            # Не найдено — «По вашему запросу ничего не нашлось»
            self._set_search_status('not_found')

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self._set_search_status(None)
        self.update_available_chords()

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
        self._data_loaded = True

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

        self.unified_menu.update_chord(len(self.available_chords))

        if self.chord_selector is not None:
            self.chord_selector.set_chords(
                self.available_chords,
                current_chord=self.current_chord_name
            )

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

        self._rebuild_slides_for_current_chord()
        self._update_display()

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

            self._rebuild_slides_for_current_chord()
            self._update_display()
        else:
            self.current_variants = []
            self.current_variant_index = 0
            self.current_position = 1
            self.unified_menu.update_variants(0)

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

            self._rebuild_slides_for_current_chord()
            self._update_display()
            logger.info(f"✅ Загружен вариант аккорда {target_chord['short_name']}")
            return True
        else:
            logger.error(f"❌ Не найдено вариантов для {target_chord['short_name']}")
            return False

    def _on_window_resize(self, window, width, height):
        if hasattr(self, '_update_griff_timer') and self._update_griff_timer:
            Clock.unschedule(self._update_griff_timer)
        self._update_griff_timer = Clock.schedule_once(lambda dt: self._update_griff_size(), 0.1)

    def on_enter(self):
        logger.info("🚪 Вход в экран аккордов")

        Clock.schedule_once(self._update_griff_size, 0.1)
        Clock.schedule_once(self._update_griff_size, 0.3)

        pending_chord = screen_state.get_pending_chord()
        if pending_chord:
            logger.info(f"🎸 Есть ожидающий аккорд: {pending_chord}")
            Clock.schedule_once(lambda dt: self.select_chord_by_name(pending_chord), 0.1)
            screen_state.clear_pending_chord()

        previous_screen = screen_state.get_previous_screen()
        if previous_screen:
            Clock.schedule_once(lambda dt: self._show_back_button(), 0.3)

        self._close_tonality_selector()
        self._close_type_selector()
        self._close_chord_selector()

    def _show_back_button(self):
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav._custom_back_callback = self.go_back
                app.top_nav.screen_title.text = "Аккорды"
                logger.info("✅ Кнопка возврата принудительно показана")
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")

    def on_leave(self):
        logger.info("🚪 Выход из экрана аккордов")
        self._close_tonality_selector()
        self._close_type_selector()
        self._close_chord_selector()
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        logger.info("🔙 Нажата кнопка возврата")
        if self.manager and self.manager.has_screen('home'):
            self.manager.current = 'home'
            logger.info("✅ Возврат на home")
        else:
            logger.error("❌ Экран home не найден")

    def on_size(self, *args):
        Clock.schedule_once(self._update_griff_size, 0.05)