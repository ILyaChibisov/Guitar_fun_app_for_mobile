# screens/chord_detail_screen.py
"""
Экран просмотра аккорда ИЗ ПОИСКА.
Адаптирован под 3 темы и 6 языков.
Лады на светлой теме — чёрные.
"""
from kivy.uix.behaviors import ButtonBehavior
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
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
from api.chords_client import get_chords_client
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('ChordDetail')

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
CORE_TYPES = {"Major", "Minor", "7", "m7"}


# ============================================================
# ЦВЕТА ДЛЯ ЭКРАНА
# ============================================================

class ChordsColors:
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
            return [1, 1, 1, 1]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        else:
            return [1, 1, 1, 0.7]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.1]
        else:
            return [0, 0, 0, 0.08]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        else:
            return [1, 1, 1, 0.15]

    @staticmethod
    def get_menu_bg(theme_id):
        if theme_id == 'light':
            return [0.95, 0.95, 0.95, 1]
        elif theme_id == 'dark':
            return [0.15, 0.15, 0.15, 1]
        else:
            return [0, 0, 0, 0.15]

    @staticmethod
    def get_button_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [0.25, 0.25, 0.25, 1]
        else:
            return [1, 1, 1, 0.15]

    @staticmethod
    def get_button_text(theme_id):
        if theme_id == 'light':
            return [0.15, 0.15, 0.15, 1]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.9]
        else:
            return [1, 1, 1, 0.85]

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        else:
            return [1, 1, 1, 0.5]

    @staticmethod
    def get_chord_name_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        else:
            return [1.0, 0.95, 0.85, 0.95]


# ============ КОНТЕЙНЕР С КАРУСЕЛЬЮ ============
class SwipeContainer(MDBoxLayout):
    _NAME_FONT_BASE = sp(22)
    _NAME_FONT_MIN = sp(12)
    _NAME_PADDING = dp(20)
    _CARD_MIN_WIDTH = dp(120)
    _CARD_MAX_WIDTH = dp(280)
    _CHAR_WIDTH_FACTOR = 0.62
    _ALT_CYCLE_INTERVAL = 2.0
    _ALT_FADE_DURATION = 0.2

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

        self.name_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(100),
            padding=[dp(8), dp(6), dp(8), dp(16)], spacing=dp(6),
            md_bg_color=[0, 0, 0, 0])

        self.chord_name_card = MDCard(
            orientation='vertical', size_hint=(None, None), size=(dp(140), dp(52)),
            pos_hint={'center_x': 0.5}, radius=[dp(16)], elevation=0,
            padding=[dp(4)] * 4, spacing=dp(0))

        self.chord_name_label = MDLabel(
            text="A", font_size=sp(22), bold=True, halign="center",
            valign="middle", theme_text_color="Custom")
        self.chord_name_card.add_widget(self.chord_name_label)
        self.name_container.add_widget(self.chord_name_card)

        self.chord_alt_label = MDLabel(
            text="", font_size=sp(11), halign="center", valign="middle",
            size_hint_y=None, height=dp(16), opacity=0, theme_text_color="Custom")
        self.chord_alt_label.text_size = (Window.width - dp(32), None)
        self.name_container.add_widget(self.chord_alt_label)

        self.add_widget(self.name_container)

        self._current_main_name = ""
        self._alt_names = []
        self._alt_index = 0
        self._alt_timer = None
        self._alt_fade_anim = None

        self.carousel = Carousel(direction='right', loop=True,
                                  size_hint=(1, 1), anim_move_duration=0.3)
        self.carousel.bind(current_slide=self._on_carousel_slide)
        self.add_widget(self.carousel)

        self.slides = []
        self.renderers = []
        self.current_index = 0
        self._programmatic_slide = False

        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.chord_name_card.md_bg_color = ChordsColors.get_card_bg(theme_id)
        self.chord_name_card.line_color = ChordsColors.get_card_line(theme_id)
        self.chord_name_card.line_width = 1.5 if theme_id in ('dark', 'light') else 0.8
        self.chord_name_label.text_color = ChordsColors.get_chord_name_color(theme_id)
        self.chord_alt_label.text_color = ChordsColors.get_text_secondary(theme_id)

    def update_fret_color(self, theme_id):
        color = "black" if theme_id == "light" else "white"
        for renderer in self.renderers:
            renderer.set_fret_color(color)

    def _build_griff_wrapper(self):
        return MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                            padding=[dp(8), dp(4), dp(8), dp(4)], md_bg_color=[0, 0, 0, 0])

    def add_slide(self, chord_module):
        slide = MDBoxLayout(orientation='vertical', size_hint=(1, 1), md_bg_color=[0, 0, 0, 0])
        wrapper = self._build_griff_wrapper()
        renderer = ChordRenderer()

        theme_id = settings_manager.theme
        renderer.set_fret_color("black" if theme_id == "light" else "white")

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

    def update_chord_name(self, display_name, alt_names=None):
        display_name = (display_name or "?").strip()
        alt_names = [n for n in (alt_names or []) if n and n != display_name]
        if (display_name == self._current_main_name and alt_names == self._alt_names):
            return
        self._current_main_name = display_name
        self._alt_names = alt_names
        self._alt_index = 0
        anim_out = Animation(opacity=0, duration=0.12, t='out_quad')
        anim_out.bind(on_complete=lambda *a: self._apply_name(display_name, alt_names))
        anim_out.start(self.name_container)

    def _apply_name(self, name, alt_names):
        card_width, font_size = self._calc_card_width_and_font(name)
        self.chord_name_label.text = name
        self.chord_name_label.font_size = font_size
        self.chord_name_card.width = card_width
        if alt_names:
            self.chord_alt_label.text = alt_names[0]
            self.chord_alt_label.opacity = 1
            self._alt_index = 0
        else:
            self.chord_alt_label.text = ""
            self.chord_alt_label.opacity = 0
        anim_in = Animation(opacity=1, duration=0.15, t='in_quad')
        anim_in.bind(on_complete=lambda *a: self._start_alt_cycle())
        anim_in.start(self.name_container)

    def _start_alt_cycle(self):
        self._stop_alt_cycle()
        if not self._alt_names or len(self._alt_names) <= 1:
            return
        self._alt_timer = Clock.schedule_interval(self._next_alt_name, self._ALT_CYCLE_INTERVAL)

    def _stop_alt_cycle(self):
        if self._alt_timer:
            Clock.unschedule(self._alt_timer)
            self._alt_timer = None
        if self._alt_fade_anim:
            self._alt_fade_anim.cancel(self.chord_alt_label)
            self._alt_fade_anim = None

    def _next_alt_name(self, dt):
        if not self._alt_names or not self.chord_alt_label.parent:
            self._stop_alt_cycle()
            return
        if len(self._alt_names) <= 1:
            return
        anim_out = Animation(opacity=0, duration=self._ALT_FADE_DURATION, t='out_quad')
        anim_out.bind(on_complete=lambda *a: self._apply_next_alt())
        self._alt_fade_anim = anim_out
        anim_out.start(self.chord_alt_label)

    def _apply_next_alt(self):
        if not self._alt_names or not self.chord_alt_label.parent:
            return
        self._alt_index = (self._alt_index + 1) % len(self._alt_names)
        self.chord_alt_label.text = self._alt_names[self._alt_index]
        Animation(opacity=1, duration=self._ALT_FADE_DURATION, t='in_quad').start(self.chord_alt_label)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start_x, self._touch_start_y = touch.x, touch.y
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
                if abs(dx) > 50 and abs(dx) > abs(dy):
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


# ============ ПУНКТ МЕНЮ ============
class IconMenuItem(ButtonBehavior, MDBoxLayout):
    def __init__(self, icon_name, on_press=None, is_active=False, icon_color=None, fixed_color=False, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.on_press_callback = on_press
        self.is_active = is_active
        self.fixed_color = fixed_color
        self.icon_color = icon_color if icon_color is not None else [1, 1, 1, 0.7]

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
            self.icon_btn.icon_color = self.icon_color
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


# ============ БАЗОВЫЙ СЕЛЕКТОР ============
class BaseSelectorMenu(MDCard):
    def __init__(self, on_confirm, on_cancel, **kwargs):
        super().__init__(**kwargs)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.is_visible = False

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = 0
        self.radius = [dp(16)] * 4
        self.elevation = 0
        self.padding = [dp(4)] * 4
        self.spacing = dp(0)

        self.scroll = None
        self.container = None
        self.buttons = []
        self.current_selection = None
        self._build_ui()

    def _build_ui(self):
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False,
                                  bar_width=0, bar_color=[0, 0, 0, 0],
                                  bar_inactive_color=[0, 0, 0, 0], bar_margin=0)
        self.container = MDBoxLayout(orientation='horizontal', size_hint_x=None,
                                      spacing=dp(8), padding=[dp(8)] * 4)
        self.container.bind(minimum_width=self.container.setter('width'))
        self._populate_items()
        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)
        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = ChordsColors.get_menu_bg(theme_id)
        self.line_color = ChordsColors.get_card_line(theme_id)
        self.line_width = 1.5 if theme_id in ('dark', 'light') else 0.8

        idle_bg = ChordsColors.get_button_bg(theme_id)
        idle_text = ChordsColors.get_button_text(theme_id)
        accent = ChordsColors.get_accent(theme_id)

        for btn in self.buttons:
            if btn.text == self.current_selection:
                btn.md_bg_color = accent
                btn.text_color = [1, 1, 1, 1]
            else:
                btn.md_bg_color = idle_bg
                btn.text_color = idle_text

    def _populate_items(self):
        pass

    def _get_button_width(self, text):
        return max(dp(36), min(dp(80), dp(30) + len(text) * dp(7) + dp(12)))

    def _highlight_current(self):
        self.update_theme_colors()

    def _on_item_press(self, value):
        self.current_selection = value
        self._highlight_current()
        if self.on_confirm:
            self.on_confirm(value)

    def show(self):
        self.is_visible = True
        self.opacity = 1
        self.disabled = False
        self.height = dp(60)
        self._highlight_current()
        if self.scroll:
            Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_x', 0), 0)

    def hide(self):
        self.is_visible = False
        self.opacity = 0
        self.disabled = True
        self.height = 0


class TonalitySelectorMenu(BaseSelectorMenu):
    def __init__(self, current_tonality, on_confirm, on_cancel, **kwargs):
        self.current_tonality = current_tonality
        super().__init__(on_confirm, on_cancel, **kwargs)

    def _populate_items(self):
        self.buttons = []
        for ton in TONALITIES:
            btn = MDRaisedButton(
                text=ton, size_hint=(None, 1), width=dp(48),
                md_bg_color=[0, 0, 0, 0], font_size=sp(16), elevation=0,
                on_release=lambda x, t=ton: self._on_item_press(t))
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
                text=chord_type, size_hint=(None, 1),
                width=self._get_button_width(chord_type),
                md_bg_color=[0, 0, 0, 0], font_size=sp(13), elevation=0,
                on_release=lambda x, t=chord_type: self._on_item_press(t))
            self.buttons.append(btn)
            self.container.add_widget(btn)
        self.current_selection = self.current_type

    def set_current(self, chord_type):
        self.current_selection = chord_type
        self._highlight_current()


class ChordSelectorMenu(BaseSelectorMenu):
    def __init__(self, current_chord, on_confirm, on_cancel, chords=None, **kwargs):
        self.current_chord = current_chord
        self.chords = list(chords) if chords else []
        super().__init__(on_confirm, on_cancel, **kwargs)

    def _populate_items(self):
        self.buttons = []
        for chord_name in self.chords:
            btn = MDRaisedButton(
                text=chord_name, size_hint=(None, 1),
                width=self._get_button_width(chord_name),
                md_bg_color=[0, 0, 0, 0], font_size=sp(14), elevation=0,
                on_release=lambda x, t=chord_name: self._on_item_press(t))
            self.buttons.append(btn)
            self.container.add_widget(btn)
        self.current_selection = self.current_chord

    def set_chords(self, chords, current_chord=None):
        new_chords = list(chords) if chords else []

        if new_chords == self.chords:
            if current_chord is not None and current_chord != self.current_chord:
                self.current_chord = current_chord
                self.current_selection = current_chord
                self._highlight_current()
            return

        self.chords = new_chords
        if current_chord is not None:
            self.current_chord = current_chord
            self.current_selection = current_chord
        self.container.clear_widgets()
        self.buttons = []
        self._populate_items()
        self._highlight_current()

    def set_current(self, chord_name):
        if chord_name == self.current_chord:
            return
        self.current_chord = chord_name
        self.current_selection = chord_name
        self._highlight_current()


# ============ ЕДИНОЕ МЕНЮ ============
class UnifiedMenu(MDCard):
    def __init__(self, tonality_value, type_value, chord_value,
                 on_tonality_press=None, on_type_press=None,
                 on_chord_press=None, on_variants_press=None, on_mode_toggle=None,
                 variants_count=1, current_mode="finger", chord_count=0, **kwargs):
        super().__init__(**kwargs)
        # ✅ Сохраняем колбэк, чтобы update_chord мог его восстановить
        self._on_chord_press_restore = on_chord_press

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.radius = [dp(16)] * 4
        self.elevation = 0
        self.padding = [dp(4)] * 4
        self.spacing = dp(0)

        self.tonality_item = IconMenuItem("music-note-eighth", on_tonality_press, True,
                                           icon_color=[0.61, 0.15, 0.69, 1], fixed_color=True)
        self.type_item = IconMenuItem("tag", on_type_press, True,
                                       icon_color=[0.0, 0.74, 0.83, 1], fixed_color=True)
        has_chords = chord_count > 1
        self.chord_item = IconMenuItem(
            "music-circle", on_chord_press if has_chords else None,
            is_active=has_chords,
            icon_color=[1.0, 0.7, 0.0, 1] if has_chords else [1, 1, 1, 0.3])
        self.variants_item = IconMenuItem(
            "format-list-numbered", on_variants_press,
            is_active=(variants_count > 1),
            icon_color=[0.13, 0.59, 0.95, 1] if variants_count > 1 else [1, 1, 1, 0.3])
        mode_icon = "gesture-tap" if current_mode == "finger" else "music-note"
        mode_color = [0.9, 0.55, 0.0, 1] if current_mode == "finger" else [0.8, 0.3, 0.3, 1]
        self.mode_item = IconMenuItem(mode_icon, on_mode_toggle, True,
                                       icon_color=mode_color, fixed_color=True)

        self.add_widget(self.tonality_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.type_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.chord_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.variants_item)
        self.add_widget(self._create_divider())
        self.add_widget(self.mode_item)

        self.update_theme_colors()

    def _create_divider(self):
        return MDBoxLayout(size_hint_x=None, width=dp(1))

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = ChordsColors.get_menu_bg(theme_id)
        self.line_color = ChordsColors.get_card_line(theme_id)
        self.line_width = 1.5 if theme_id in ('dark', 'light') else 0.8
        for child in self.children:
            if isinstance(child, MDBoxLayout) and child.width == dp(1):
                child.md_bg_color = ChordsColors.get_card_line(theme_id)

    def update_chord(self, chord_count):
        # ✅ Всегда восстанавливаем колбэк, если аккордов больше 1
        has_chords = chord_count > 1
        self.chord_item.is_active = has_chords
        if has_chords:
            self.chord_item.on_press_callback = self._on_chord_press_restore
            self.chord_item.set_color([1.0, 0.7, 0.0, 1])
            self.chord_item.icon_btn.opacity = 1
        else:
            self.chord_item.on_press_callback = None
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
        if mode == "finger":
            self.mode_item.set_icon("gesture-tap")
            self.mode_item.set_color([0.9, 0.55, 0.0, 1])
        else:
            self.mode_item.set_icon("music-note")
            self.mode_item.set_color([0.8, 0.3, 0.3, 1])


# ============ ОСНОВНОЙ ЭКРАН ============
class ChordDetailScreen(BaseScreen):
    TONALITIES = TONALITIES
    CHORD_TYPES = CHORD_TYPES

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chord_detail'
        self.all_chords = []
        self.is_search_mode = False
        self.current_tonality = "A"
        self.current_tonality_index = 0
        self.current_type = "Major"
        self.current_type_index = 0
        self.current_chord_name = "A"
        self.current_chord_index = 0
        self.available_chords = []
        self.current_position = 1
        self.current_variants = []
        self.current_variant_index = 0
        self._core_types = CORE_TYPES
        self._chords_client = get_chords_client()
        self._server_loading = False
        self._request_id = 0
        self.current_mode = "finger"
        self.unified_menu = None
        self._menu_container = None
        self._info_label = None
        self._hint_timer = None
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self.tonality_selector = None
        self.type_selector = None
        self.chord_selector = None
        self._menu_cache_initialized = False
        self._griff_height = dp(280)
        self._update_griff_timer = None
        self.swipe_container = None
        self._data_loaded = False
        self._chord_to_load = None
        self._current_main_name = ""
        self._current_alt_names = []
        self._current_all_names = []
        self._pending_chord_list = None

        self.load_background()
        self.init_ui()

        Clock.schedule_once(self._create_cached_menus, 0.05)
        Clock.schedule_once(lambda dt: self.scan_chords(), 0.1)
        logger.info('ChordDetailScreen создан')

    def load_background(self):
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        self.texture = None
        try:
            if HAS_ASSETS:
                for name in ["background_jpg", "background", "bg", "BACKGROUND_JPG"]:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        img = CoreImage(BytesIO(bg_data), ext="jpg")
                        self.texture = img.texture
                        break
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
        if self.swipe_container:
            self.swipe_container.update_theme_colors()
            self.swipe_container.update_fret_color(theme_id)
        if self.unified_menu:
            self.unified_menu.update_theme_colors()
        if self.tonality_selector:
            self.tonality_selector.update_theme_colors()
        if self.type_selector:
            self.type_selector.update_theme_colors()
        if self.chord_selector:
            self.chord_selector.update_theme_colors()
        if self._info_label:
            self._info_label.text_color = ChordsColors.get_hint_color(theme_id)

    def update_language(self):
        self._show_description()

    def _create_cached_menus(self, dt=None):
        if self._menu_cache_initialized:
            return
        self.tonality_selector = TonalitySelectorMenu(
            current_tonality=self.current_tonality,
            on_confirm=self._on_tonality_confirmed,
            on_cancel=self._close_tonality_selector)
        self.tonality_selector.opacity = 0
        self.tonality_selector.disabled = True
        self.tonality_selector.height = 0
        self._menu_container.add_widget(self.tonality_selector)

        self.type_selector = TypeSelectorMenu(
            current_type=self.current_type,
            on_confirm=self._on_type_confirmed,
            on_cancel=self._close_type_selector)
        self.type_selector.opacity = 0
        self.type_selector.disabled = True
        self.type_selector.height = 0
        self._menu_container.add_widget(self.type_selector)

        self.chord_selector = ChordSelectorMenu(
            current_chord=self.current_chord_name,
            on_confirm=self._on_chord_confirmed,
            on_cancel=self._close_chord_selector,
            chords=self.available_chords)
        self.chord_selector.opacity = 0
        self.chord_selector.disabled = True
        self.chord_selector.height = 0
        self._menu_container.add_widget(self.chord_selector)

        self._menu_cache_initialized = True

    def _update_desc_height(self, instance, texture_size):
        if texture_size:
            new_height = texture_size[1] + dp(8)
            if self._info_label.height != new_height:
                self._info_label.height = new_height

    def _update_griff_size(self, *args):
        if self.swipe_container:
            window_width = Window.width
            available_width = window_width - dp(24)
            griff_height = int(available_width * 0.45)
            min_height = dp(200)
            max_height = int(window_width * 0.6)
            griff_height = max(min_height, min(griff_height, max_height))
            self._griff_height = griff_height
            self.swipe_container.height = griff_height + dp(136)

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

    def _dict_to_module(self, data: dict):
        class _FakeModule:
            pass
        m = _FakeModule()
        m.__name__ = f"server_chord_{data.get('main_name', '?')}_{data.get('variant', 1)}"
        m.BACKGROUND_NAME = data.get("background_name", "griff")
        m.FRETS = data.get("frets", {})
        m.NOTES = data.get("notes", {})
        m.OPEN_NOTES = data.get("open_notes", {})
        m.BARRES = data.get("barres", {})
        m.SELECTED_FINGER = data.get("selected_finger", [])
        m.SELECTED_NOTE = data.get("selected_note", [])
        m.METADATA = {
            "name": data.get("main_name", ""),
            "variant": data.get("variant", 1),
            "type": data.get("chord_type", ""),
            "description": data.get("description", ""),
        }
        return m

    def _rebuild_server_slides(self):
        if not self.swipe_container:
            return
        self.swipe_container.clear_slides()
        for variant in self.current_variants:
            server_data = variant.get("server_data")
            if not server_data:
                continue
            module = self._dict_to_module(server_data)
            self.swipe_container.add_slide(module)
        self.swipe_container.update_renderer_mode(self.current_mode)
        if self.current_variants:
            self.swipe_container.set_current_slide(self.current_variant_index)

    def _update_display(self):
        if not self.current_variants:
            return
        variant = self.current_variants[self.current_variant_index]

        if variant.get("module") is not None:
            chord_name = variant["name"].replace('!', ' | ').replace('$', '/')
            name_parts = [p.strip() for p in chord_name.split('|') if p.strip()]
        else:
            server_data = variant.get("server_data") or {}
            synonyms = server_data.get("synonyms") or [server_data.get("main_name", "?")]
            name_parts = [s.replace('!', ' | ').replace('$', '/') for s in synonyms]

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

        if self.swipe_container:
            self.swipe_container.update_chord_name(main_name, alt_names)

        self._show_description()
        self._data_loaded = True

    def init_ui(self):
        padding = layout_config.get_content_padding()
        horizontal_padding = [padding[0], 0, padding[2], 0]
        content = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))
        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self.swipe_container = SwipeContainer(on_swipe_horizontal=self._on_swipe_horizontal)
        self.swipe_container.size_hint = (1, None)
        self.swipe_container.height = self._griff_height + dp(136)
        content.add_widget(self.swipe_container)

        Window.bind(on_resize=self._on_window_resize)
        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        menu_wrapper = MDBoxLayout(orientation='vertical', size_hint=(1, None),
                                    height=dp(60), padding=horizontal_padding)
        self._menu_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                                            md_bg_color=[0, 0, 0, 0])
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
            chord_count=len(self.available_chords))
        self._menu_container.add_widget(self.unified_menu)

        content.add_widget(Widget(size_hint_y=None, height=dp(2)))

        self._info_label = MDLabel(
            text="", font_size=sp(12), halign="center",
            size_hint_y=None, height=dp(30), theme_text_color="Custom")
        self._info_label.text_size = (None, None)
        self._info_label.bind(texture_size=self._update_desc_height)
        content.add_widget(self._info_label)
        content.add_widget(Widget(size_hint_y=1))

        self.build_ui(content_widget=content, use_scroll=False)

        Clock.schedule_once(self._update_griff_size, 0.1)
        Clock.schedule_once(self._update_griff_size, 0.3)
        Clock.schedule_once(self._update_griff_size, 0.5)
        Clock.schedule_once(lambda dt: self.update_theme_colors(), 0.2)

    def _on_swipe_horizontal(self, step):
        if not self.current_variants or len(self.current_variants) <= 1:
            self._show_temporary_hint(get_text('no_variants'), 1.0)
            return
        total = len(self.current_variants)
        self.current_variant_index = (self.current_variant_index + step) % total
        self.current_position = self.current_variant_index + 1
        self._update_display()
        self._show_temporary_hint(f"{get_text('variant')} {self.current_position}/{total}", 1.0)

    def _show_description(self):
        if settings_manager.language != 'ru':
            self._info_label.text = ""
            return
        if not self.current_variants:
            self._info_label.text = ""
            return
        variant = self.current_variants[self.current_variant_index]
        parts = []
        description = variant.get('description', '')
        if description:
            desc_parts = [p.strip() for p in description.replace('!', '|').split('|') if p.strip()]
            unique_desc = []
            for part in desc_parts:
                if part not in unique_desc:
                    unique_desc.append(part)
            if unique_desc:
                formatted = unique_desc[0]
                main_name = self._current_main_name
                if main_name and main_name in formatted:
                    formatted = formatted.replace(main_name, '').strip(' |,')
                formatted = re.sub(r'\s*\|\s*', ', ', formatted).strip(' ,')
                formatted = re.sub(r'\s+', ' ', formatted)
                if formatted:
                    parts.append(formatted)
        self._info_label.text = ", ".join(parts) if parts else (self._current_main_name or "")

    def _show_hint(self, text):
        if self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None
        self._info_label.text = text

    def _show_temporary_hint(self, text, duration=1.5):
        if self._info_label:
            self._info_label.text = text
            if self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._restore_description(), duration)

    def _restore_description(self):
        self._hint_timer = None
        self._show_description()

    def _show_selector(self, selector):
        if self.unified_menu:
            self.unified_menu.opacity = 0
            self.unified_menu.disabled = True
            self.unified_menu.height = 0
        for sel in (self.tonality_selector, self.type_selector, self.chord_selector):
            if sel is None or sel is selector:
                continue
            sel.opacity = 0
            sel.disabled = True
            sel.is_visible = False
            sel.height = 0
        if selector is not None:
            selector.opacity = 1
            selector.disabled = False
            selector.is_visible = True
            selector.height = dp(60)
            if hasattr(selector, 'scroll') and selector.scroll:
                Clock.schedule_once(lambda dt: setattr(selector.scroll, 'scroll_x', 0), 0)

    def _restore_unified(self):
        for sel in (self.tonality_selector, self.type_selector, self.chord_selector):
            if sel is not None:
                sel.opacity = 0
                sel.disabled = True
                sel.is_visible = False
                sel.height = 0
        if self.unified_menu:
            self.unified_menu.opacity = 1
            self.unified_menu.disabled = False
            self.unified_menu.height = dp(60)
        self._restore_description()

    def _open_tonality_selector(self):
        if self.tonality_selector and self.tonality_selector.is_visible:
            self._restore_unified()
            return
        if not self.tonality_selector:
            self.tonality_selector = TonalitySelectorMenu(
                current_tonality=self.current_tonality,
                on_confirm=self._on_tonality_confirmed,
                on_cancel=self._close_tonality_selector)
            self.tonality_selector.opacity = 0
            self.tonality_selector.disabled = True
            self.tonality_selector.height = 0
            self._menu_container.add_widget(self.tonality_selector)
        self.tonality_selector.set_current(self.current_tonality)
        self._show_selector(self.tonality_selector)
        self._show_hint(get_text('choose_tonality'))

    def _on_tonality_confirmed(self, selected_tonality):
        self.current_tonality = selected_tonality
        self.current_tonality_index = TONALITIES.index(selected_tonality)
        self.is_search_mode = False
        self.current_chord_name = ""
        self.current_chord_index = 0
        self.current_variants = []
        self.current_variant_index = 0
        self.current_position = 1
        self.update_available_chords()
        self._restore_unified()

    def _close_tonality_selector(self):
        self._restore_unified()

    def _open_type_selector(self):
        if self.type_selector and self.type_selector.is_visible:
            self._restore_unified()
            return
        if not self.type_selector:
            self.type_selector = TypeSelectorMenu(
                current_type=self.current_type,
                on_confirm=self._on_type_confirmed,
                on_cancel=self._close_type_selector)
            self.type_selector.opacity = 0
            self.type_selector.disabled = True
            self.type_selector.height = 0
            self._menu_container.add_widget(self.type_selector)
        self.type_selector.set_current(self.current_type)
        self._show_selector(self.type_selector)
        self._show_hint(get_text('choose_type'))

    def _on_type_confirmed(self, selected_type):
        self.current_type = selected_type
        self.current_type_index = CHORD_TYPES.index(selected_type)
        self.is_search_mode = False
        self.current_chord_name = ""
        self.current_chord_index = 0
        self.current_variants = []
        self.current_variant_index = 0
        self.current_position = 1
        self.update_available_chords()
        self._restore_unified()

    def _close_type_selector(self):
        self._restore_unified()

    def _open_chord_selector(self):
        if self.chord_selector and self.chord_selector.is_visible:
            self._restore_unified()
            return
        if not self.available_chords and not self._pending_chord_list:
            self._show_temporary_hint(get_text('no_chords'), 1.0)
            return

        if self.chord_selector is not None:
            target_list = self._pending_chord_list if self._pending_chord_list is not None else self.available_chords
            self.chord_selector.set_chords(target_list, current_chord=self.current_chord_name)
            self._pending_chord_list = None

        self.chord_selector.set_current(self.current_chord_name)
        self._show_selector(self.chord_selector)
        self._show_hint(get_text('choose_chord'))

    def _on_chord_confirmed(self, selected_chord):
        if not selected_chord or selected_chord == self.current_chord_name:
            self._restore_unified()
            return
        self.current_chord_name = selected_chord
        if selected_chord in self.available_chords:
            self.current_chord_index = self.available_chords.index(selected_chord)
        self._load_variants_for_chord(self.current_chord_name)
        if self.unified_menu:
            self.unified_menu.update_chord(len(self.available_chords))
        self._restore_unified()

    def _close_chord_selector(self):
        self._restore_unified()

    def _toggle_mode(self):
        if self.current_mode == "finger":
            self.current_mode = "notes"
            self._show_temporary_hint(get_text('mode_notes'), 1.2)
        else:
            self.current_mode = "finger"
            self._show_temporary_hint(get_text('mode_fingers'), 1.2)
        self.unified_menu.update_mode(self.current_mode)
        if self.swipe_container:
            self.swipe_container.update_renderer_mode(self.current_mode)

    def _next_variant(self):
        if not self.current_variants or len(self.current_variants) <= 1:
            notify.info(get_text('no_variants'))
            return
        total = len(self.current_variants)
        self.current_variant_index = (self.current_variant_index + 1) % total
        self.current_position = self.current_variant_index + 1
        if self.swipe_container:
            self.swipe_container.carousel.load_next()
        self._update_display()
        self._show_temporary_hint(f"{get_text('variant')}: {self.current_position}", 1.2)

    def scan_chords(self):
        self.all_chords = []
        try:
            import chords
            self._scan_module_recursive(chords, 'chords')
        except ImportError as e:
            logger.error(f"Пакет chords не найден: {e}")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            traceback.print_exc()
        self._data_loaded = True
        if self._chord_to_load:
            chord_name = self._chord_to_load
            self._chord_to_load = None
            Clock.schedule_once(lambda dt: self.select_chord_by_name(chord_name), 0.05)

    def _scan_module_recursive(self, module, module_path):
        if hasattr(module, '__path__'):
            for module_info in pkgutil.iter_modules(module.__path__, f"{module_path}."):
                try:
                    sub = importlib.import_module(module_info.name)
                    if hasattr(sub, '__path__'):
                        self._scan_module_recursive(sub, module_info.name)
                    else:
                        self._load_chord_module(sub, module_info.name)
                except Exception as e:
                    logger.error(f"Ошибка импорта {module_info.name}: {e}")

    def _load_chord_module(self, module, module_name):
        try:
            metadata = getattr(module, 'METADATA', {})
            chord_name = metadata.get('name', module_name.split('.')[-1])
            chord_name = chord_name.replace('!', '|').replace('$', '/')
            path_parts = module_name.split('.')
            chord_type = metadata.get('type', '') or (path_parts[-2] if len(path_parts) >= 2 else '')
            if chord_type not in self._core_types:
                return
            variant_match = re.search(r'_(\d+)$', path_parts[-1])
            variant_num = int(variant_match.group(1)) if variant_match else metadata.get('variant', 1)
            short_name = chord_name.split('|')[0].replace('$', '/')
            self.all_chords.append({
                'id': f"{short_name}_{chord_type}_v{variant_num}",
                'name': chord_name,
                'short_name': short_name,
                'variant': variant_num,
                'type': chord_type,
                'description': metadata.get('description', ''),
                'module': module,
                'path': module_name
            })
        except Exception as e:
            logger.error(f"Ошибка загрузки {module_name}: {e}")

    def update_available_chords(self):
        if self.is_search_mode:
            return
        if self.current_type in self._core_types:
            filtered = []
            for chord in self.all_chords:
                if self.extract_tonality(chord['name']) != self.current_tonality:
                    continue
                chord_types = chord['type'].split('|') if chord['type'] else []
                if self.current_type not in chord_types and self.current_type != chord.get('type', ''):
                    continue
                filtered.append(chord)
            chords_by_name = {}
            for chord in filtered:
                chords_by_name.setdefault(chord['short_name'], []).append(chord)
            self.available_chords = sorted(chords_by_name.keys())
            if self.unified_menu:
                self.unified_menu.update_chord(len(self.available_chords))
            self._pending_chord_list = list(self.available_chords)
            if self.available_chords:
                if self.current_chord_name not in self.available_chords:
                    self.current_chord_index = 0
                    self.current_chord_name = self.available_chords[0]
                data = chords_by_name.get(self.current_chord_name)
                if data:
                    self.load_chord_variants(data)
            else:
                self.current_variants = []
            return

        self._request_id += 1
        my_id = self._request_id

        def _on_list(chords):
            if my_id != self._request_id:
                return
            self.available_chords = list(chords or [])
            if self.unified_menu:
                self.unified_menu.update_chord(len(self.available_chords))
            self._pending_chord_list = list(self.available_chords)
            if not self.available_chords:
                self._show_temporary_hint(f"{self.current_tonality}/{self.current_type}: {get_text('no_chords')}", 2.0)
                self.current_variants = []
                if self.unified_menu:
                    self.unified_menu.update_variants(0)
                return
            if self.current_chord_name not in self.available_chords:
                self.current_chord_index = 0
                self.current_chord_name = self.available_chords[0]
            self._load_variants_for_chord(self.current_chord_name)

        def _on_err(msg):
            if my_id != self._request_id:
                return
            self.available_chords = []
            self._pending_chord_list = []
            if self.unified_menu:
                self.unified_menu.update_chord(0)
            self._show_temporary_hint(get_text('loading_error'), 2.0)

        self._chords_client.get_available_chords(
            self.current_tonality, self.current_type,
            on_success=_on_list, on_error=_on_err)

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
        if self.unified_menu:
            self.unified_menu.update_variants(len(variants))
        self._rebuild_slides_for_current_chord()
        self._update_display()

    def _load_variants_for_chord(self, chord_name):
        if self.current_type in self._core_types:
            variants = []
            for chord in self.all_chords:
                if chord['short_name'] == chord_name and self.extract_tonality(chord['name']) == self.current_tonality:
                    chord_types = chord['type'].split('|') if chord['type'] else []
                    if self.current_type in chord_types or self.current_type == chord.get('type', ''):
                        variants.append(chord)
            if variants:
                variants.sort(key=lambda x: x['variant'])
                self.current_variants = variants
                self.current_variant_index = 0
                self.current_position = 1
                if self.unified_menu:
                    self.unified_menu.update_variants(len(variants))
                self._rebuild_slides_for_current_chord()
                self._update_display()
            else:
                self.current_variants = []
                if self.unified_menu:
                    self.unified_menu.update_variants(0)
            return

        self._server_loading = True
        self._request_id += 1
        my_id = self._request_id

        def _on_success(variants):
            if my_id != self._request_id:
                return
            self._server_loading = False
            normalized = []
            for v in variants:
                syn = v.get("synonyms") or [v.get("main_name", "?")]
                normalized.append({
                    "name": " | ".join(syn),
                    "short_name": v.get("main_name", "?"),
                    "variant": v.get("variant", 1),
                    "type": v.get("chord_type", ""),
                    "description": v.get("description", ""),
                    "module": None,
                    "server_data": v,
                })
            normalized.sort(key=lambda x: x["variant"])
            self.current_variants = normalized
            self.current_variant_index = 0
            self.current_position = 1
            if self.unified_menu:
                self.unified_menu.update_variants(len(normalized))
            self._rebuild_server_slides()
            self._update_display()

        def _on_error(msg):
            if my_id != self._request_id:
                return
            self._server_loading = False
            self._show_temporary_hint(get_text('loading_error'), 2.0)
            self.current_variants = []
            if self.unified_menu:
                self.unified_menu.update_variants(0)

        self._chords_client.get_chord(chord_name, self.current_type,
                                      on_success=_on_success, on_error=_on_error)

    def select_chord_by_name(self, chord_name):
        if not self._data_loaded:
            self._chord_to_load = chord_name
            return False
        target_chord = None
        for chord in self.all_chords:
            if chord['short_name'] == chord_name:
                target_chord = chord
                break
        if not target_chord:
            for chord in self.all_chords:
                for v in chord['name'].split('|'):
                    if v.strip().replace('$', '/') == chord_name:
                        target_chord = chord
                        break
                if target_chord:
                    break
        if not target_chord:
            alt = chord_name.replace('#', 'b')
            if alt != chord_name:
                return self.select_chord_by_name(alt)
        if target_chord:
            tonality = self._extract_tonality_from_name(target_chord['name'])
            chord_type = target_chord.get('type', 'Major')
            if tonality in self.TONALITIES:
                self.current_tonality = tonality
                self.current_tonality_index = self.TONALITIES.index(tonality)
            if chord_type in self.CHORD_TYPES:
                self.current_type = chord_type
                self.current_type_index = self.CHORD_TYPES.index(chord_type)
            self.update_available_chords()
            if target_chord['short_name'] in self.available_chords:
                self.current_chord_name = target_chord['short_name']
                self.current_chord_index = self.available_chords.index(self.current_chord_name)
                self._load_variants_for_chord(self.current_chord_name)
                return True
            return self._find_and_load_chord_variant(target_chord)
        self._search_server_and_select(chord_name)
        return True

    def _search_server_and_select(self, chord_name):
        def _on_results(items):
            if not items:
                alt = chord_name.replace('#', 'b') if '#' in chord_name else chord_name.replace('b', '#')
                if alt != chord_name:
                    self._chords_client.search_by_synonym(
                        alt,
                        on_success=lambda items2: self._apply_server_search(items2, alt),
                        on_error=lambda msg: notify.warning(f"{chord_name} {get_text('term_not_found')}"))
                else:
                    notify.warning(f"{chord_name} {get_text('term_not_found')}")
                return
            self._apply_server_search(items, chord_name)

        self._chords_client.search_by_synonym(
            chord_name, on_success=_on_results,
            on_error=lambda msg: notify.warning(get_text('search_error')))

    def _apply_server_search(self, items, query):
        if not items:
            notify.warning(f"{query} {get_text('term_not_found')}")
            return
        best = items[0]
        main_name = best.get("main_name") or query
        tonality = best.get("tonality") or ""
        chord_type = best.get("chord_type") or ""
        if tonality in self.TONALITIES:
            self.current_tonality = tonality
            self.current_tonality_index = self.TONALITIES.index(tonality)
        if chord_type in self.CHORD_TYPES:
            self.current_type = chord_type
            self.current_type_index = self.CHORD_TYPES.index(chord_type)
        self.current_chord_name = main_name
        self._load_available_and_variants(main_name)

    def _load_available_and_variants(self, target_name):
        def _on_list(chords):
            self.available_chords = list(chords or [])
            if target_name not in self.available_chords:
                self.available_chords.append(target_name)
                self.available_chords.sort()
            if self.unified_menu:
                self.unified_menu.update_chord(len(self.available_chords))
            self._pending_chord_list = list(self.available_chords)
            self.current_chord_name = target_name
            self.current_chord_index = self.available_chords.index(target_name)
            self._load_variants_for_chord(target_name)

        def _on_err(msg):
            self.available_chords = [target_name]
            self.current_chord_name = target_name
            self.current_chord_index = 0
            if self.unified_menu:
                self.unified_menu.update_chord(1)
            self._pending_chord_list = [target_name]
            self._load_variants_for_chord(target_name)

        self._chords_client.get_available_chords(
            self.current_tonality, self.current_type,
            on_success=_on_list, on_error=_on_err)

    def _extract_tonality_from_name(self, chord_name):
        if not chord_name:
            return "A"
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else "A"

    def _find_and_load_chord_variant(self, target_chord):
        short = target_chord['short_name']
        variants = [c for c in self.all_chords if c['short_name'] == short]
        if variants:
            variants.sort(key=lambda x: x['variant'])
            self.current_variants = variants
            self.current_variant_index = 0
            self.current_position = 1
            if self.unified_menu:
                self.unified_menu.update_variants(len(variants))
            self.current_chord_name = short
            self._rebuild_slides_for_current_chord()
            self._update_display()
            return True
        return False

    def _on_window_resize(self, window, width, height):
        if self._update_griff_timer:
            Clock.unschedule(self._update_griff_timer)
        self._update_griff_timer = Clock.schedule_once(lambda dt: self._update_griff_size(), 0.15)

    def go_back(self, instance=None):
        screen_state.clear_pending_chord()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
        if self.manager:
            if self.manager.has_screen('search'):
                self.manager.current = 'search'
            else:
                self.manager.current = 'home'

    def on_enter(self):
        super().on_enter()

        self.update_theme_colors()
        self._update_griff_size()
        pending_chord = screen_state.get_pending_chord()
        if pending_chord:
            self.select_chord_by_name(pending_chord)
            screen_state.clear_pending_chord()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title(get_text('chords'))
            app.top_nav.back_btn.on_release = self.go_back
        self._close_tonality_selector()
        self._close_type_selector()
        self._close_chord_selector()

    def on_leave(self):
        self._close_tonality_selector()
        self._close_type_selector()
        self._close_chord_selector()
        if self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None
        if self.swipe_container:
            self.swipe_container._stop_alt_cycle()

    def on_size(self, *args):
        if self._update_griff_timer:
            Clock.unschedule(self._update_griff_timer)
        self._update_griff_timer = Clock.schedule_once(lambda dt: self._update_griff_size(), 0.15)