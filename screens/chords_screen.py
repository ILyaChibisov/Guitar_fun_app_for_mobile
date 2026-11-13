# screens/chords_screen.py
"""
Экран гитарных аккордов - с единым меню 5 в 1 под грифом.
Адаптирован под 3 темы (green, light, dark) и 6 языков.

ЛОКАЛЬНО в пакете chords/ оставлен ТОЛЬКО A Major (все варианты).
Всё остальное (другие тональности, другие типы) грузится с сервера.

ОПТИМИЗАЦИИ:
  - rebuild_slides пропускается, если данные/тема/аккорд не изменились.
  - В add_slide цвет/режим выставляются ДО load_chord → один _create_sprites.
  - _create_cached_menus — ленивая, при первом тапе.
  - _open_fullscreen_griff строит слайды порциями (не блокирует UI).
  - placeholder-слайды в оверлее имеют renderer=None; все циклы по renderers
    пропускают None.
"""
from kivy.uix.behaviors import ButtonBehavior
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivy.uix.textinput import TextInput
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.uix.carousel import Carousel
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from io import BytesIO
import pkgutil
import importlib
import re
import time
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.scatter import Scatter
from kivy.logger import Logger

from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from chord_utils.renderer import ChordRenderer
from utils.notifications import notify
from state.previous_screen import previous_screen_state
from api.chords_client import get_chords_client
from state.settings_state import settings_state as settings_manager
from utils.localization import get_text
from state.chords_state import chords_state

from utils.perf import perf, perf_registry

logger = screen_logger('Chords')
_perf_log = Logger.getChild('Chords:Perf')

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

LOCAL_TONALITY = "A"
LOCAL_TYPE = "Major"


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
            return [0.46, 0.70, 0.71, 0.4]

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

    @staticmethod
    def get_arrow_color(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 1]
        return [1, 1, 1, 1]

    @staticmethod
    def get_divider_color(theme_id):
        """Цвет «рваного» разделителя — как в TunerColors."""
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.6]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.6]
        else:
            return [0.46, 0.70, 0.71, 0.55]



class ClickableRendererContainer(ButtonBehavior, MDBoxLayout):
    """Контейнер для грифа, который умеет реагировать на тап (для увеличения)."""

    def __init__(self, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_click_callback = on_click

    def on_release(self):
        if self.on_click_callback:
            self.on_click_callback()


class SwipeContainer(MDBoxLayout):
    def __init__(self, on_swipe_horizontal=None, show_arrows=True, show_name=True, screen=None, **kwargs):
        super().__init__(**kwargs)
        self.on_swipe_horizontal = on_swipe_horizontal
        self.show_arrows = show_arrows
        self.show_name = show_name
        self.screen = screen
        self._touch_start_x = 0
        self._touch_start_y = 0
        self._touch_start_time = 0
        self._touch_moved = False
        self._is_dragging = False
        self._drag_threshold = 20
        self._fullscreen_overlay = None
        self._big_swipe = None
        self._overlay_name_label = None
        self._overlay_left_btn = None
        self._overlay_right_btn = None
        self._overlay_mode_btn = None
        self._overlay_menu_card = None
        self._overlay_menu_scatter = None
        self._overlay_dividers = []
        self._overlay_menu_container = None
        self._overlay_unified_menu = None
        self._overlay_scatter = None
        self._overlay_name_card = None
        self._overlay_name_scatter = None
        self._is_overlay_rotated = False
        self._overlay_side_left = None
        self._overlay_side_right = None
        self._wait_ticks = 0

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(460)
        self.md_bg_color = [0, 0, 0, 0]
        self.spacing = 0

        self.name_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(58) if show_name else 0,
            padding=[dp(8), dp(6), dp(8), dp(4)] if show_name else [0, 0, 0, 0],
            spacing=0,
            md_bg_color=[0, 0, 0, 0],
            opacity=1 if show_name else 0,
        )

        self.chord_name_card = MDCard(
            orientation='vertical', size_hint=(None, None), size=(dp(140), dp(46)),
            pos_hint={'center_x': 0.5}, radius=[0], elevation=0,
            padding=[dp(4), dp(2), dp(4), dp(2)], spacing=dp(0),
            md_bg_color=[0, 0, 0, 0],
            line_color=[0, 0, 0, 0],
            line_width=1,
        )

        self.chord_name_label = MDLabel(
            text="A", font_size=sp(22), bold=True, halign="center",
            valign="middle", theme_text_color="Custom",
        )
        self.chord_name_card.add_widget(self.chord_name_label)
        self.name_container.add_widget(self.chord_name_card)
        self.add_widget(self.name_container)

        self._current_main_name = ""
        self._alt_names = []
        self._alt_index = 0
        self._alt_timer = None
        self._alt_fade_anim = None

        self.carousel = Carousel(direction='right', loop=True, size_hint=(1, 1), anim_move_duration=0.3)
        self.carousel.bind(current_slide=self._on_carousel_slide)
        self.add_widget(self.carousel)

        self.alt_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(32) if show_name else 0,
            padding=[dp(16), dp(6), dp(16), dp(2)] if show_name else [0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            opacity=1 if show_name else 0,
        )
        self.chord_alt_label = MDLabel(
            text="", font_size=sp(13), halign="center", valign="middle",
            size_hint=(1, 1), opacity=0, theme_text_color="Custom",
        )
        self.chord_alt_label.text_size = (Window.width - dp(32), None)
        self.alt_container.add_widget(self.chord_alt_label)
        self.add_widget(self.alt_container)

        self.slides = []
        self.renderers = []
        self.current_index = 0
        self._programmatic_slide = False

        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.chord_name_card.md_bg_color = [0, 0, 0, 0]
        self.chord_name_card.line_color = [0, 0, 0, 0]
        self.chord_name_card.line_width = 1
        self.chord_name_label.text_color = ChordsColors.get_chord_name_color(theme_id)
        self.chord_alt_label.text_color = ChordsColors.get_text_secondary(theme_id)

        if theme_id == 'light':
            arrow_color = [0.2, 0.2, 0.2, 1]
        else:
            arrow_color = [1, 1, 1, 1]

        if hasattr(self, 'left_arrow') and self.left_arrow:
            self.left_arrow.text_color = arrow_color
            self.left_arrow.canvas.ask_update()
        if hasattr(self, 'right_arrow') and self.right_arrow:
            self.right_arrow.text_color = arrow_color
            self.right_arrow.canvas.ask_update()

    def update_fret_color(self, theme_id):
        color = "black" if theme_id == "light" else "white"
        for renderer in self.renderers:
            if renderer is not None:
                renderer.set_fret_color(color)

    def update_renderer_mode(self, mode):
        for renderer in self.renderers:
            if renderer is not None:
                renderer.set_mode(mode)

    def _build_griff_wrapper(self):
        theme_id = settings_manager.theme
        if theme_id == 'light':
            arrow_color = [0.2, 0.2, 0.2, 1]
        else:
            arrow_color = [1, 1, 1, 1]

        wrapper = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(4), dp(4), dp(4), dp(4)],
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0]
        )

        if self.show_arrows:
            self.left_arrow = MDIcon(
                icon="chevron-left",
                size_hint=(None, 1),
                width=dp(24),
                theme_text_color="Custom",
                text_color=arrow_color,
                font_size=sp(28)
            )
            self.right_arrow = MDIcon(
                icon="chevron-right",
                size_hint=(None, 1),
                width=dp(24),
                theme_text_color="Custom",
                text_color=arrow_color,
                font_size=sp(28)
            )
            wrapper.add_widget(self.left_arrow)

        renderer_container = ClickableRendererContainer(
            orientation='vertical',
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0],
            on_click=self._on_griff_click
        )
        wrapper.add_widget(renderer_container)

        if self.show_arrows:
            wrapper.add_widget(self.right_arrow)

        return wrapper, renderer_container

    def add_slide(self, chord_module):
        with perf('chords.swipe.add_slide', log_every=False):
            with perf('chords.swipe.add_slide.build_wrapper', log_every=False):
                slide = MDBoxLayout(orientation='vertical', size_hint=(1, 1), md_bg_color=[0, 0, 0, 0])
                wrapper, renderer_container = self._build_griff_wrapper()

            with perf('chords.swipe.add_slide.create_renderer', log_every=False):
                renderer = ChordRenderer()

            theme_id = settings_manager.theme
            renderer.FRET_COLOR = "black" if theme_id == "light" else "white"
            renderer.current_mode = "finger"

            with perf('chords.swipe.add_slide.load_griff_png', log_every=False):
                try:
                    bg_data = load_asset_as_bytes("griff_png")
                    if bg_data:
                        img = CoreImage(BytesIO(bg_data), ext="png")
                        if img and img.texture:
                            renderer.set_background(img.texture)
                except Exception as e:
                    logger.error(f"Ошибка загрузки фона грифа: {e}")

            if chord_module:
                with perf('chords.swipe.add_slide.load_chord', log_every=False):
                    renderer.load_chord(chord_module)
                renderer.chord_module = chord_module

            with perf('chords.swipe.add_slide.attach', log_every=False):
                renderer_container.add_widget(renderer)
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

    def set_current_slide(self, index, animate=True):
        if 0 <= index < len(self.slides):
            self._programmatic_slide = True
            if animate:
                self.carousel.load_slide(self.slides[index])
                Clock.schedule_once(lambda dt: setattr(self, '_programmatic_slide', False), 0.35)
            else:
                old_duration = self.carousel.anim_move_duration
                self.carousel.anim_move_duration = 0
                self.carousel.load_slide(self.slides[index])
                self.carousel.anim_move_duration = old_duration
                self._programmatic_slide = False
            self.current_index = index

    def _on_carousel_slide(self, instance, slide):
        if not self.slides:
            return
        try:
            index = self.slides.index(slide)
            if index != self.current_index:
                self.current_index = index
                if not self._programmatic_slide and self.screen:
                    if self is self.screen.swipe_container:
                        self.screen._on_carousel_index_changed(index)
                    elif self.screen.swipe_container and self is self.screen.swipe_container._big_swipe:
                        self.screen._on_carousel_index_changed(index, from_overlay=True)
        except ValueError:
            pass

    def _calc_card_width_and_font(self, name):
        font_size = sp(22)

        def natural_width(fs):
            return len(name) * fs * 0.62 + 2 * dp(20) + dp(16)

        total = natural_width(font_size)
        if total > dp(280):
            k = dp(280) / total
            font_size = max(sp(12), font_size * k)
            total = natural_width(font_size)
        return max(dp(120), min(total, dp(280))), font_size

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
            self._alt_index = 0
            Animation(opacity=1, duration=0.15, t='in_quad').start(self.chord_alt_label)
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
        self._alt_timer = Clock.schedule_interval(self._next_alt_name, 2.0)

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
        anim_out = Animation(opacity=0, duration=0.2, t='out_quad')
        anim_out.bind(on_complete=lambda *a: self._apply_next_alt())
        self._alt_fade_anim = anim_out
        anim_out.start(self.chord_alt_label)

    def _apply_next_alt(self):
        if not self._alt_names or not self.chord_alt_label.parent:
            return
        self._alt_index = (self._alt_index + 1) % len(self._alt_names)
        self.chord_alt_label.text = self._alt_names[self._alt_index]
        anim_in = Animation(opacity=1, duration=0.2, t='in_quad')
        anim_in.start(self.chord_alt_label)

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            self._touch_start_x, self._touch_start_y = touch.x, touch.y
            self._touch_start_time = time.time()
            self._touch_moved = False
            self._is_dragging = False
            touch.grab(self)
            return True
        return False

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
                    else:
                        if self.on_swipe_horizontal:
                            self.on_swipe_horizontal(-1)
            touch.ungrab(self)
            self._touch_moved = False
            self._is_dragging = False
            return True
        return super().on_touch_up(touch)

    def _on_griff_click(self):
        if not self.slides or not self.renderers:
            return
        idx = self.current_index
        if idx >= len(self.renderers):
            return
        current_renderer = self.renderers[idx]
        chord_module = getattr(current_renderer, 'chord_module', None) if current_renderer is not None else None
        self._open_fullscreen_griff(chord_module)

    def _update_overlay_name(self):
        if not self.screen or not self._fullscreen_overlay:
            return
        name_text = self.screen._current_main_name or "?"
        is_rot = getattr(self, '_is_overlay_rotated', False)

        if self._overlay_name_label is not None:
            self._overlay_name_label.text = name_text
            base_font_sp = 72 if len(name_text) <= 4 else (54 if len(name_text) <= 8 else 40)
            self._overlay_name_label.font_size = sp(base_font_sp)

        if self._overlay_unified_menu is not None:
            self._overlay_unified_menu.set_center_chord_name(is_rot, name_text)

    def _on_name_label_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self._close_fullscreen_griff()
            return True
        return False

    def _on_swipe_horizontal_from_overlay(self, step):
        if not self.screen:
            return
        scr = self.screen
        if not scr.current_variants or len(scr.current_variants) <= 1:
            return
        with perf('chords.overlay.swipe_horizontal', log_every=False):
            total = len(scr.current_variants)
            scr.current_variant_index = (scr.current_variant_index + step) % total
            scr.current_position = scr.current_variant_index + 1

            if scr.swipe_container:
                scr.swipe_container.set_current_slide(scr.current_variant_index)
            if self._big_swipe:
                self._big_swipe.set_current_slide(scr.current_variant_index)

            scr._update_display()
            self._update_overlay_name()
            self._update_overlay_menu()

    def _next_variant_in_overlay(self):
        self._on_swipe_horizontal_from_overlay(1)

    def _toggle_mode_in_overlay(self):
        if not self.screen:
            return
        scr = self.screen
        if scr.current_mode == "finger":
            scr.current_mode = "notes"
        else:
            scr.current_mode = "finger"
        if scr.swipe_container:
            scr.swipe_container.update_renderer_mode(scr.current_mode)
        if self._big_swipe:
            self._big_swipe.update_renderer_mode(scr.current_mode)
        self._update_overlay_menu()

    def _toggle_overlay_rotation(self):
        self._is_overlay_rotated = not getattr(self, '_is_overlay_rotated', False)
        self._apply_overlay_layout()
        self.update_overlay_theme()
        self._update_overlay_name()

    def _apply_overlay_layout(self, *args):
        with perf('chords.overlay.apply_layout', log_every=False):
            if not self._fullscreen_overlay or not self._big_swipe:
                return
            w, h = Window.width, Window.height
            is_rot = getattr(self, '_is_overlay_rotated', False)
            name_text = self.screen._current_main_name if self.screen else "?"

            if self._overlay_unified_menu is not None:
                self._overlay_unified_menu.set_icons_rotation(0)
                self._overlay_unified_menu.set_center_chord_name(is_rot, name_text)
                if self._overlay_unified_menu.rotate_item is not None:
                    self._overlay_unified_menu.rotate_item.set_icon(
                        "phone-rotate-portrait" if is_rot else "phone-rotate-landscape"
                    )
            if self.screen:
                for sel in (self.screen.tonality_selector, self.screen.type_selector, self.screen.chord_selector):
                    if sel is not None:
                        sel.set_items_rotation(0)

            scatter = getattr(self, '_overlay_scatter', None)
            name_scatter = getattr(self, '_overlay_name_scatter', None)
            name_card = getattr(self, '_overlay_name_card', None)
            menu_scatter = getattr(self, '_overlay_menu_scatter', None)
            menu_wrapper = getattr(self, '_overlay_menu_wrapper', None)
            has_variants = bool(self.screen and self.screen.current_variants and len(self.screen.current_variants) > 1)

            if is_rot:
                # 1. Меню вдоль ЛЕВОГО края с названием аккорда ровно по середине (3 + Название + 3)
                menu_thickness = dp(52)
                left_pad = dp(10)
                v_margin = dp(20)
                menu_len = max(dp(340), h - v_margin * 2)

                if menu_wrapper is not None and menu_scatter is not None:
                    menu_wrapper.size = (menu_len, menu_thickness)
                    menu_wrapper.pos = (0, 0)
                    menu_scatter.size = (menu_len, menu_thickness)
                    menu_scatter.rotation = -90
                    menu_scatter.center = (left_pad + menu_thickness / 2.0, h / 2.0)

                # 2. Скрываем отдельный заголовок справа (теперь он в центральной ячейке меню)
                if name_scatter is not None:
                    name_scatter.opacity = 0
                    name_scatter.disabled = True

                # 3. Максимально крупный гриф занимает всю правую область от меню до края экрана
                griff_left_limit = left_pad + menu_thickness + dp(8)
                griff_right_limit = w - dp(8)
                avail_w = max(dp(220), griff_right_limit - griff_left_limit)

                arrow_space = dp(24) if has_variants else dp(10)
                avail_h = max(dp(260), h - arrow_space * 2 - dp(12))

                center_x = griff_left_limit + avail_w / 2.0
                center_y = h / 2.0

                self._big_swipe.size = (avail_h, avail_w)
                self._big_swipe.pos = (0, 0)
                if scatter is not None:
                    scatter.size = (avail_h, avail_w)
                    scatter.rotation = -90
                    scatter.center = (center_x, center_y)

                # 4. Стрелки пагинации вплотную к верхнему и нижнему торцам грифа
                griff_top = center_y + avail_h / 2.0
                griff_bottom = center_y - avail_h / 2.0
                if self._overlay_side_left is not None and self._overlay_side_right is not None:
                    arrow_w, arrow_h = dp(64), dp(22)
                    arrow_x = center_x - arrow_w / 2.0

                    self._overlay_side_left.icon.icon = "chevron-up"
                    self._overlay_side_left.size = (arrow_w, arrow_h)
                    self._overlay_side_left.pos = (arrow_x, min(h - arrow_h - dp(2), griff_top - dp(4)))
                    self._overlay_side_left.opacity = 1 if has_variants else 0
                    self._overlay_side_left.disabled = not has_variants

                    self._overlay_side_right.icon.icon = "chevron-down"
                    self._overlay_side_right.size = (arrow_w, arrow_h)
                    self._overlay_side_right.pos = (arrow_x, max(dp(2), griff_bottom - arrow_h + dp(4)))
                    self._overlay_side_right.opacity = 1 if has_variants else 0
                    self._overlay_side_right.disabled = not has_variants
            else:
                # Стандартный горизонтальный оверлей (название вверху, меню из 6 кнопок без центральной ячейки)
                if name_scatter is not None:
                    name_scatter.opacity = 1
                    name_scatter.disabled = False

                side_margin = dp(24)
                bottom_margin = dp(20)
                menu_h = dp(60)
                menu_w = w - side_margin * 2

                if menu_wrapper is not None and menu_scatter is not None:
                    menu_wrapper.size = (menu_w, menu_h)
                    menu_wrapper.pos = (0, 0)
                    menu_scatter.size = (menu_w, menu_h)
                    menu_scatter.rotation = 0
                    menu_scatter.pos = (side_margin, bottom_margin)

                box_w = w - dp(16)
                box_h = dp(74)
                top_margin = dp(14)
                if name_scatter is not None and name_card is not None and self._overlay_name_label is not None:
                    name_card.size = (box_w, box_h)
                    name_card.pos = (0, 0)
                    self._overlay_name_label.text_size = (box_w, box_h)

                    name_scatter.size = (box_w, box_h)
                    name_scatter.rotation = 0
                    name_scatter.center_x = w / 2.0
                    name_scatter.top = h - top_margin

                side_arrow_space = dp(24)
                griff_width = max(dp(240), w - side_arrow_space * 2)
                griff_height = min(max(dp(290), griff_width * 0.65), max(dp(220), h - dp(230)))
                center_y = h / 2.0 + dp(12)

                self._big_swipe.size = (griff_width, griff_height)
                self._big_swipe.pos = (0, 0)
                if scatter is not None:
                    scatter.size = (griff_width, griff_height)
                    scatter.rotation = 0
                    scatter.center = (w / 2.0, center_y)

                if self._overlay_side_left is not None and self._overlay_side_right is not None:
                    arrow_h = dp(64)
                    self._overlay_side_left.icon.icon = "chevron-left"
                    self._overlay_side_left.size = (side_arrow_space, arrow_h)
                    self._overlay_side_left.pos = (dp(2), center_y - arrow_h / 2.0)
                    self._overlay_side_left.opacity = 1 if has_variants else 0
                    self._overlay_side_left.disabled = not has_variants

                    self._overlay_side_right.icon.icon = "chevron-right"
                    self._overlay_side_right.size = (side_arrow_space, arrow_h)
                    self._overlay_side_right.pos = (w - side_arrow_space - dp(2), center_y - arrow_h / 2.0)
                    self._overlay_side_right.opacity = 1 if has_variants else 0
                    self._overlay_side_right.disabled = not has_variants

    def _attach_overlay_selector(self, selector, on_confirm_cb):
        if selector is None or self._overlay_menu_container is None:
            return
        if selector.parent is not None:
            selector.parent.remove_widget(selector)
        self._overlay_menu_container.clear_widgets()

        selector.set_items_rotation(0)
        selector.disabled = False
        selector.opacity = 1
        selector.size_hint = (1, 1)
        selector.pos_hint = {'x': 0, 'y': 0}
        selector.on_confirm = on_confirm_cb
        selector.on_cancel = self._restore_overlay_unified
        self._overlay_menu_container.add_widget(selector)

    def _open_overlay_tonality_selector(self):
        if not self.screen:
            return
        self.screen._ensure_menus()
        if self.screen.tonality_selector is None:
            return
        selector = self.screen.tonality_selector
        selector.set_current(self.screen.current_tonality)
        self._attach_overlay_selector(selector, self._on_overlay_tonality_confirmed)

    def _on_overlay_tonality_confirmed(self, selected_tonality):
        self.screen._on_tonality_confirmed(selected_tonality)
        Clock.schedule_once(lambda dt: self._after_overlay_selection(), 0.35)

    def _open_overlay_type_selector(self):
        if not self.screen:
            return
        self.screen._ensure_menus()
        if self.screen.type_selector is None:
            return
        selector = self.screen.type_selector
        selector.set_current(self.screen.current_type)
        self._attach_overlay_selector(selector, self._on_overlay_type_confirmed)

    def _on_overlay_type_confirmed(self, selected_type):
        self.screen._on_type_confirmed(selected_type)
        Clock.schedule_once(lambda dt: self._after_overlay_selection(), 0.35)

    def _open_overlay_chord_selector(self):
        if not self.screen:
            return
        self.screen._ensure_menus()
        if self.screen.chord_selector is None:
            return
        selector = self.screen.chord_selector
        target_list = self.screen._pending_chord_list if self.screen._pending_chord_list is not None else self.screen.available_chords
        selector.set_chords(target_list, current_chord=self.screen.current_chord_name)
        selector.set_current(self.screen.current_chord_name)
        self._attach_overlay_selector(selector, self._on_overlay_chord_confirmed)

    def _on_overlay_chord_confirmed(self, selected_chord):
        self.screen._on_chord_confirmed(selected_chord)
        Clock.schedule_once(lambda dt: self._after_overlay_selection(), 0.35)

    def _after_overlay_selection(self):
        self._restore_overlay_unified()
        if not self.screen or not self._fullscreen_overlay:
            return

        def _wait_and_rebuild(dt):
            if not self.screen or not self._fullscreen_overlay:
                return False
            if getattr(self.screen, '_server_loading', False) or not self.screen.current_variants:
                self._wait_ticks = getattr(self, '_wait_ticks', 0) + 1
                if self._wait_ticks > 100:
                    self._wait_ticks = 0
                    self._rebuild_overlay_slides()
                    return False
                return True

            self._wait_ticks = 0
            self._rebuild_overlay_slides()
            return False

        self._wait_ticks = 0
        if getattr(self.screen, '_server_loading', False) or not self.screen.current_variants:
            Clock.schedule_interval(_wait_and_rebuild, 0.05)
        else:
            self._rebuild_overlay_slides()

    def _rebuild_overlay_slides(self):
        if not self.screen or not self._big_swipe:
            return
        with perf('chords.overlay.rebuild_slides'):
            with perf('chords.overlay.rebuild_slides.clear', log_every=False):
                self._big_swipe.clear_slides()
            variants = self.screen.current_variants or []
            for v in variants:
                module = v.get('module')
                if module is None and v.get('server_data'):
                    module = self.screen._dict_to_module(v['server_data'])
                if module:
                    with perf('chords.overlay.rebuild_slides.add_slide', log_every=False):
                        self._big_swipe.add_slide(module)
            if variants:
                with perf('chords.overlay.rebuild_slides.set_current', log_every=False):
                    self._big_swipe.set_current_slide(self.screen.current_variant_index, animate=False)
            with perf('chords.overlay.rebuild_slides.update_mode', log_every=False):
                self._big_swipe.update_renderer_mode(self.screen.current_mode)
            with perf('chords.overlay.rebuild_slides.update_theme', log_every=False):
                self._big_swipe.update_fret_color(settings_manager.theme)
            self._update_overlay_name()
            self._update_overlay_menu()

    def _restore_overlay_unified(self):
        if self._overlay_menu_container is None:
            return
        self._overlay_menu_container.clear_widgets()
        if self._overlay_unified_menu:
            self._overlay_unified_menu.set_icons_rotation(0)
            self._overlay_unified_menu.disabled = False
            self._overlay_unified_menu.opacity = 1
            self._overlay_unified_menu.size_hint = (1, 1)
            self._overlay_unified_menu.pos_hint = {'x': 0, 'y': 0}
            self._overlay_menu_container.add_widget(self._overlay_unified_menu)

    def _close_fullscreen_griff(self):
        overlay = self._fullscreen_overlay
        if overlay is None:
            return

        if getattr(self, '_overlay_build_event', None):
            try:
                Clock.unschedule(self._overlay_build_event)
            except Exception:
                pass
            self._overlay_build_event = None

        if self.screen:
            if self.screen.tonality_selector:
                if self.screen.tonality_selector.parent:
                    self.screen.tonality_selector.parent.remove_widget(self.screen.tonality_selector)
                self.screen.tonality_selector.set_items_rotation(0)
                self.screen.tonality_selector.on_confirm = self.screen._on_tonality_confirmed
                self.screen.tonality_selector.on_cancel = self.screen._close_tonality_selector
            if self.screen.type_selector:
                if self.screen.type_selector.parent:
                    self.screen.type_selector.parent.remove_widget(self.screen.type_selector)
                self.screen.type_selector.set_items_rotation(0)
                self.screen.type_selector.on_confirm = self.screen._on_type_confirmed
                self.screen.type_selector.on_cancel = self.screen._close_type_selector
            if self.screen.chord_selector:
                if self.screen.chord_selector.parent:
                    self.screen.chord_selector.parent.remove_widget(self.screen.chord_selector)
                self.screen.chord_selector.set_items_rotation(0)
                self.screen.chord_selector.on_confirm = self.screen._on_chord_confirmed
                self.screen.chord_selector.on_cancel = self.screen._close_chord_selector

        def _remove(animation, widget):
            if overlay.parent:
                overlay.parent.remove_widget(overlay)
            self._fullscreen_overlay = None
            self._big_swipe = None
            self._overlay_scatter = None
            self._overlay_name_card = None
            self._overlay_name_label = None
            self._overlay_name_scatter = None
            self._overlay_left_btn = None
            self._overlay_right_btn = None
            self._overlay_mode_btn = None
            self._overlay_menu_card = None
            self._overlay_menu_wrapper = None
            self._overlay_menu_scatter = None
            self._overlay_dividers = []
            self._overlay_menu_container = None
            self._overlay_unified_menu = None
            self._is_overlay_rotated = False
            self._overlay_side_left = None
            self._overlay_side_right = None
            self._overlay_build_event = None

        anim = Animation(opacity=0, duration=0.15)
        anim.bind(on_complete=_remove)
        anim.start(overlay)

    def _open_fullscreen_griff(self, chord_module):
        if self._fullscreen_overlay is not None:
            return

        with perf('chords.overlay.open.total'):
            overlay = FloatLayout(size_hint=(1, 1))
            self._is_overlay_rotated = False

            theme_id = settings_manager.theme
            with overlay.canvas.before:
                overlay._bg_color = Color(1, 1, 1, 1)
                overlay._bg_rect = Rectangle(pos=overlay.pos, size=overlay.size)
            overlay.bind(
                pos=lambda inst, val: setattr(overlay._bg_rect, 'pos', val),
                size=lambda inst, val: setattr(overlay._bg_rect, 'size', val),
            )

            self._overlay_menu_card = None
            self._overlay_menu_scatter = None
            self._overlay_dividers = []
            self._overlay_menu_container = None
            self._overlay_unified_menu = None
            self._overlay_build_event = None

            with perf('chords.overlay.open.create_scatter+big_swipe', log_every=False):
                scatter = Scatter(
                    do_rotation=False, do_scale=False, do_translation=False,
                    auto_bring_to_front=False, size_hint=(None, None),
                )
                self._overlay_scatter = scatter
                big_swipe = SwipeContainer(
                    on_swipe_horizontal=self._on_swipe_horizontal_from_overlay,
                    show_arrows=False, show_name=False, screen=self.screen,
                )
                big_swipe.size_hint = (None, None)
                big_swipe.md_bg_color = [0, 0, 0, 0]
                big_swipe._on_griff_click = self._close_fullscreen_griff
                big_swipe.padding = [0, 0, 0, 0]
                big_swipe.spacing = 0
                self._big_swipe = big_swipe

            with perf('chords.overlay.open.add_scatter+arrows', log_every=False):
                scatter.add_widget(big_swipe)
                overlay.add_widget(scatter)

                arrow_color = [0.2, 0.2, 0.2, 1] if theme_id == 'light' else [1, 1, 1, 1]

                class _OverlaySideArrow(ButtonBehavior, FloatLayout):
                    def __init__(self, icon_name, cb, **kw):
                        super().__init__(**kw)
                        self.size_hint = (None, None)
                        self.cb = cb
                        self.icon = MDIcon(
                            icon=icon_name, halign="center", valign="middle",
                            size_hint=(None, None), size=(dp(28), dp(28)),
                            text_size=(dp(28), dp(28)),
                            theme_text_color="Custom", text_color=arrow_color,
                            font_size=sp(28),
                        )
                        self.add_widget(self.icon)
                        self.bind(
                            pos=lambda inst, val: setattr(self.icon, 'center', inst.center),
                            size=lambda inst, val: setattr(self.icon, 'center', inst.center),
                        )

                    def on_release(self):
                        if self.cb and not self.disabled:
                            self.cb()

                self._overlay_side_left = _OverlaySideArrow(
                    "chevron-up", lambda: self._on_swipe_horizontal_from_overlay(-1)
                )
                self._overlay_side_right = _OverlaySideArrow(
                    "chevron-down", lambda: self._on_swipe_horizontal_from_overlay(1)
                )
                overlay.add_widget(self._overlay_side_left)
                overlay.add_widget(self._overlay_side_right)

            with perf('chords.overlay.open.name_header', log_every=False):
                name_text = self.screen._current_main_name if self.screen else "?"
                name_scatter = Scatter(
                    do_rotation=False, do_scale=False, do_translation=False,
                    auto_bring_to_front=False, size_hint=(None, None),
                    size=(Window.width - dp(16), dp(88)),
                )
                self._overlay_name_scatter = name_scatter

                name_card = MDCard(
                    orientation='vertical', size_hint=(None, None),
                    size=(Window.width - dp(16), dp(88)),
                    pos=(0, 0), radius=[dp(18)], elevation=0,
                    padding=[dp(4), dp(4), dp(4), dp(4)],
                    md_bg_color=[0, 0, 0, 0], line_color=[0, 0, 0, 0], line_width=1,
                )
                self._overlay_name_card = name_card

                name_label = Label(
                    text=name_text, font_size=sp(72), bold=True,
                    halign="center", valign="middle", size_hint=(1, 1),
                    color=ChordsColors.get_chord_name_color(theme_id),
                )
                name_label.bind(on_touch_down=self._on_name_label_touch)
                self._overlay_name_label = name_label
                name_card.add_widget(name_label)
                name_scatter.add_widget(name_card)
                overlay.add_widget(name_scatter)

            with perf('chords.overlay.open.menu', log_every=False):
                menu_scatter = Scatter(
                    do_rotation=False, do_scale=False, do_translation=False,
                    auto_bring_to_front=False, size_hint=(None, None),
                )
                self._overlay_menu_scatter = menu_scatter

                menu_wrapper = MDBoxLayout(
                    orientation='vertical', size_hint=(None, None), height=dp(60),
                )
                self._overlay_menu_wrapper = menu_wrapper

                menu_inner_card = MDCard(
                    orientation='horizontal', size_hint=(1, 1), radius=[dp(16)],
                    elevation=0, padding=[dp(2), dp(2), dp(2), dp(2)], spacing=dp(0),
                    md_bg_color=ChordsColors.get_menu_bg(theme_id),
                    line_color=ChordsColors.get_card_line(theme_id),
                    line_width=1.5,
                )
                self._overlay_menu_card = menu_inner_card
                self._overlay_menu_container = FloatLayout(size_hint=(1, 1))

                self._overlay_unified_menu = UnifiedMenu(
                    tonality_value=self.screen.current_tonality if self.screen else "A",
                    type_value=self.screen.current_type if self.screen else "Major",
                    chord_value=self.screen._current_main_name if self.screen else "A",
                    on_tonality_press=self._open_overlay_tonality_selector,
                    on_type_press=self._open_overlay_type_selector,
                    on_chord_press=self._open_overlay_chord_selector,
                    on_variants_press=self._next_variant_in_overlay,
                    on_mode_toggle=self._toggle_mode_in_overlay,
                    on_rotate_press=self._toggle_overlay_rotation,
                    variants_count=len(self.screen.current_variants) if self.screen else 1,
                    current_mode=self.screen.current_mode if self.screen else "finger",
                    chord_count=len(self.screen.available_chords) if self.screen else 0,
                )
                self._overlay_unified_menu.size_hint = (1, 1)
                self._overlay_unified_menu.pos_hint = {'x': 0, 'y': 0}
                self._overlay_menu_container.add_widget(self._overlay_unified_menu)

                menu_inner_card.add_widget(self._overlay_menu_container)
                menu_wrapper.add_widget(menu_inner_card)
                menu_scatter.add_widget(menu_wrapper)
                overlay.add_widget(menu_scatter)

            overlay.bind(size=self._apply_overlay_layout)
            overlay.bind(on_touch_down=self._on_overlay_touch)

            self._fullscreen_overlay = overlay

            with perf('chords.overlay.open.apply_layout+theme'):
                self._apply_overlay_layout()
                self.update_overlay_theme()

            overlay.opacity = 1
            app = MDApp.get_running_app()
            if app and app.root:
                app.root.add_widget(overlay)

            with perf('chords.overlay.open.schedule_post', log_every=False):
                self._update_overlay_name()
                Clock.schedule_once(self._apply_overlay_layout, 0)
                Clock.schedule_once(lambda dt: self._update_overlay_name(), 0)
                Clock.schedule_once(lambda dt: self._update_overlay_menu(), 0)

            self._build_overlay_slides_async()

    def _build_overlay_slides_async(self):
        if not self.screen or not self._big_swipe:
            return
        variants = list(self.screen.current_variants or [])
        big_swipe = self._big_swipe
        if not variants:
            return

        pending = list(range(len(variants)))

        def _tick(dt):
            if not self.screen or not self._big_swipe or self._big_swipe is not big_swipe:
                return False
            if not pending:
                try:
                    big_swipe.set_current_slide(
                        self.screen.current_variant_index, animate=False
                    )
                except Exception as e:
                    logger.error(f"overlay set_current_slide (final): {e}")
                self._overlay_build_event = None
                return False

            idx = pending.pop(0)
            v = variants[idx]
            module = v.get('module')
            if module is None and v.get('server_data') and self.screen:
                module = self.screen._dict_to_module(v['server_data'])
            if not module:
                return bool(pending)

            try:
                big_swipe.add_slide(module)
            except Exception as e:
                logger.error(f"overlay add_slide #{idx}: {e}")
                return bool(pending)

            if len(big_swipe.slides) == 1:
                try:
                    big_swipe.set_current_slide(0, animate=False)
                except Exception as e:
                    logger.error(f"overlay set_current_slide (first): {e}")

            return bool(pending)

        try:
            first_ok = _tick(0)
        except Exception as e:
            logger.error(f"overlay first tick: {e}")
            first_ok = False

        if first_ok:
            self._overlay_build_event = Clock.schedule_interval(_tick, 0.016)
        else:
            self._overlay_build_event = None

    def update_overlay_theme(self):
        if self._fullscreen_overlay is None:
            return
        theme_id = settings_manager.theme
        overlay = self._fullscreen_overlay

        if hasattr(overlay, '_bg_rect') and hasattr(overlay, '_bg_color'):
            if theme_id == 'green':
                tex = getattr(self.screen, 'texture', None) if self.screen else None
                if tex:
                    overlay._bg_rect.texture = tex
                    overlay._bg_color.rgba = (1, 1, 1, 1)
                else:
                    overlay._bg_rect.texture = None
                    overlay._bg_color.rgba = (0.1, 0.3, 0.2, 0.98)
            elif theme_id == 'dark':
                overlay._bg_rect.texture = None
                overlay._bg_color.rgba = (0.07, 0.07, 0.07, 0.97)
            elif theme_id == 'light':
                overlay._bg_rect.texture = None
                overlay._bg_color.rgba = (0.969, 0.976, 0.969, 0.98)

        if self._overlay_name_label is not None:
            self._overlay_name_label.color = ChordsColors.get_chord_name_color(theme_id)

        if self._big_swipe is not None:
            self._big_swipe.update_fret_color(theme_id)

        if getattr(self, '_overlay_menu_card', None) is not None:
            self._overlay_menu_card.md_bg_color = ChordsColors.get_menu_bg(theme_id)
            self._overlay_menu_card.line_color = ChordsColors.get_card_line(theme_id)

        if self._overlay_unified_menu is not None:
            self._overlay_unified_menu.update_theme_colors()

        arrow_color = [0.2, 0.2, 0.2, 1] if theme_id == 'light' else [1, 1, 1, 1]
        for side_arrow in (getattr(self, '_overlay_side_left', None), getattr(self, '_overlay_side_right', None)):
            if side_arrow is not None:
                side_arrow.icon.text_color = arrow_color

    def _update_overlay_menu(self):
        if not self.screen or not self._fullscreen_overlay:
            return
        try:
            if self._overlay_unified_menu is not None:
                self._overlay_unified_menu.update_mode(self.screen.current_mode)
                self._overlay_unified_menu.update_variants(len(self.screen.current_variants))
                self._overlay_unified_menu.update_chord(len(self.screen.available_chords))
        except Exception as e:
            logger.error(f"Error updating overlay menu: {e}")

        has_variants = bool(self.screen.current_variants) and len(self.screen.current_variants) > 1
        for side_arrow in (getattr(self, '_overlay_side_left', None), getattr(self, '_overlay_side_right', None)):
            if side_arrow is not None:
                side_arrow.opacity = 1 if has_variants else 0
                side_arrow.disabled = not has_variants

    def _on_overlay_touch(self, instance, touch):
        if self._fullscreen_overlay is None:
            return False
        for child in instance.children:
            if child.collide_point(*touch.pos):
                return False
        self._close_fullscreen_griff()
        return True


class SearchBar(MDCard):
    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(16)] * 4
        self.elevation = 0
        self.padding = [dp(12), dp(4), dp(6), dp(4)]
        self.spacing = dp(6)

        self.search_field = TextInput(
            multiline=False, size_hint_x=1, height=dp(40), font_size=sp(16),
            background_color=[1, 1, 1, 0], background_normal="", background_active="",
            padding=[0, dp(10), 0, dp(4)], on_text_validate=self._on_search_pressed
        )
        self.search_field.bind(text=self._on_text_change)
        self.search_field.bind(focus=self._on_focus)

        self.clear_wrapper = MDCard(
            size_hint=(None, None), size=(dp(30), dp(30)), radius=[dp(15)] * 4,
            md_bg_color=[0, 0, 0, 0], elevation=0, pos_hint={'center_y': 0.5},
            opacity=0, disabled=True,
        )
        self.clear_btn = MDIconButton(
            icon="close-circle-outline", size_hint=(1, 1), theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0], on_release=self._on_clear_pressed, ripple_scale=0
        )
        self.clear_wrapper.add_widget(self.clear_btn)

        self.search_btn = MDRaisedButton(
            text="", size_hint=(None, None), size=(dp(64), dp(36)),
            text_color=[1, 1, 1, 1], font_size=sp(13), elevation=0,
            pos_hint={'center_y': 0.5},
        )
        try:
            self.search_btn._radius = dp(10)
            self.search_btn.ripple_scale = 0
            self.search_btn.elevation = 0
        except Exception:
            pass
        self.search_btn.bind(on_release=self._on_search_pressed)

        self.add_widget(self.search_field)
        self.add_widget(self.clear_wrapper)
        self.add_widget(self.search_btn)

        self.update_language()
        self.update_theme_colors()

    def update_language(self):
        self.search_field.hint_text = get_text('search', 'Поиск')
        self.search_btn.text = get_text('find', 'Найти')

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = ChordsColors.get_accent(theme_id)
        text_p = ChordsColors.get_text_primary(theme_id)
        text_s = ChordsColors.get_text_secondary(theme_id)
        line = ChordsColors.get_card_line(theme_id)

        if theme_id == 'light':
            self.md_bg_color = [1, 1, 1, 1]
            self.line_color = line
            self.line_width = 4.0
            self.search_field.foreground_color = text_p
            self.search_field.hint_text_color = text_s
            self.search_field.cursor_color = accent
            self.clear_btn.icon_color = accent
            self.search_btn.md_bg_color = accent
            self.search_btn.text_color = [0, 0, 0, 1]
        elif theme_id == 'dark':
            self.md_bg_color = [0.15, 0.15, 0.15, 1]
            self.line_color = line
            self.line_width = 4.0
            self.search_field.foreground_color = text_p
            self.search_field.hint_text_color = text_s
            self.search_field.cursor_color = accent
            self.clear_btn.icon_color = accent
            self.search_btn.md_bg_color = accent
            self.search_btn.text_color = [1, 1, 1, 1]
        else:
            self.md_bg_color = [1, 1, 1, 1]
            self.line_color = [1, 1, 1, 0.25]
            self.line_width = 4.0
            self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]
            self.search_field.hint_text_color = [0.55, 0.55, 0.55, 1]
            self.search_field.cursor_color = [0.1, 0.1, 0.1, 1]
            self.clear_btn.icon_color = [0.4, 0.4, 0.4, 0.8]
            self.search_btn.md_bg_color = [0.10, 0.42, 0.25, 1]
            self.search_btn.text_color = [1, 1, 1, 1]

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
        self.search_field.focus = False

    def _on_focus(self, instance, value):
        self.line_width = 5.0 if value else 4.0

    def clear(self):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""

    def focus(self):
        self.search_field.focus = True


class IconMenuItem(ButtonBehavior, AnchorLayout):
    def __init__(self, icon_name, on_press=None, is_active=False, icon_color=None, fixed_color=False, **kwargs):
        super().__init__(**kwargs)
        self.anchor_x = 'center'
        self.anchor_y = 'center'
        self.icon_name = icon_name
        self.on_press_callback = on_press
        self.is_active = is_active
        self.fixed_color = fixed_color
        self.icon_color = icon_color if icon_color else [1, 1, 1, 0.7]

        self.size_hint = (1, 1)
        self.md_bg_color = [0, 0, 0, 0]

        self.icon_widget = MDIcon(
            icon=icon_name,
            halign="center",
            valign="center",
            size_hint=(None, None),
            size=(dp(26), dp(26)),
            theme_text_color="Custom",
            text_color=self.icon_color,
            font_size=sp(24),
        )
        self.add_widget(self.icon_widget)
        self.update_state()

    def set_rotation(self, angle):
        pass

    def on_release(self):
        if self.on_press_callback and self.is_active:
            self.on_press_callback()

    def set_active(self, active):
        self.is_active = active
        self.update_state()

    def update_state(self):
        if self.fixed_color:
            return
        if self.is_active:
            self.icon_widget.text_color = self.icon_color
            self.icon_widget.opacity = 1
        else:
            self.icon_widget.text_color = [1, 1, 1, 0.3]
            self.icon_widget.opacity = 0.6

    def set_icon(self, icon_name):
        self.icon_name = icon_name
        self.icon_widget.icon = icon_name

    def set_color(self, color):
        self.icon_color = color
        self.icon_widget.text_color = color



# ============ СЕЛЕКТОРЫ В СТИЛЕ АЛФАВИТА ============

class TextSelectorButton(MDBoxLayout):
    def __init__(self, text, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press
        self.is_selected = False
        self.size_hint = (None, 1)
        self.width = dp(40)
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]

        self._label_scatter = Scatter(
            do_rotation=False, do_scale=False, do_translation=False,
            auto_bring_to_front=False, size_hint=(None, None),
        )
        self.label = MDLabel(
            text=text, font_size=sp(15), halign="center", valign="middle",
            theme_text_color="Custom", text_color=[1, 1, 1, 0.7], bold=True,
            size_hint=(None, None)
        )
        self._label_scatter.add_widget(self.label)

        holder = FloatLayout(size_hint=(1, 1))
        holder.add_widget(self._label_scatter)
        self.add_widget(holder)

        def _sync_label_box(*args):
            angle = self._label_scatter.rotation
            if abs(angle % 180) == 90:
                self._label_scatter.size = (holder.height, holder.width)
                self.label.size = (holder.height, holder.width)
            else:
                self._label_scatter.size = (holder.width, holder.height)
                self.label.size = (holder.width, holder.height)
            self._label_scatter.center = holder.center

        self._sync_label_box = _sync_label_box
        holder.bind(pos=_sync_label_box, size=_sync_label_box)

        self.bind(on_touch_down=self._on_touch_down)
        self._update_style()

    def set_rotation(self, angle):
        if hasattr(self, '_label_scatter') and self._label_scatter:
            self._label_scatter.rotation = angle
            if hasattr(self, '_sync_label_box'):
                self._sync_label_box()

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self.on_press_callback:
                self.on_press_callback(self.btn_text)
            return True
        return False

    def set_selected(self, selected):
        if self.is_selected == selected:
            return
        self.is_selected = selected
        self._update_style()

    def _update_style(self):
        theme_id = settings_manager.theme
        if self.is_selected:
            self.md_bg_color = ChordsColors.get_accent(theme_id)
            self.label.text_color = [1, 1, 1, 1]
            self.radius = [dp(8)]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = ChordsColors.get_text_secondary(theme_id)
            self.radius = [0]


class _SelectorArrowBtn(ButtonBehavior, AnchorLayout):
    def __init__(self, icon_name, on_release_cb, is_left=True, **kwargs):
        super().__init__(**kwargs)
        self.anchor_x = 'center'
        self.anchor_y = 'center'
        self.size_hint = (None, 1)
        self.width = dp(32)
        self.on_release_cb = on_release_cb
        self.base_icon = icon_name
        self.is_left = is_left

        self.icon = MDIcon(
            icon=icon_name,
            halign="center",
            valign="center",
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            theme_text_color="Custom",
            font_size=sp(24),
        )
        self.add_widget(self.icon)

    def set_rotation(self, angle):
        pass

    def on_release(self):
        if self.on_release_cb:
            self.on_release_cb()


class BaseSelectorMenu(MDBoxLayout):
    def __init__(self, on_confirm, on_cancel, **kwargs):
        super().__init__(**kwargs)
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.is_visible = False

        self.orientation = 'horizontal'
        self.size_hint = (1, 1)
        self.md_bg_color = [0, 0, 0, 0]
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        self.scroll = None
        self.container = None
        self.buttons = []
        self.current_selection = None
        self._current_rotation = 0
        self._build_ui()

    def _build_ui(self):
        self.left_arrow_btn = _SelectorArrowBtn("chevron-left", lambda: self.scroll_by(-1), is_left=True)
        self.add_widget(self.left_arrow_btn)

        self.scroll = ScrollView(
            size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False,
            bar_width=0, bar_color=[0, 0, 0, 0], bar_inactive_color=[0, 0, 0, 0], bar_margin=0
        )
        self.container = MDBoxLayout(
            orientation='horizontal', size_hint_x=None, spacing=dp(8),
            padding=[dp(6), 0, dp(6), 0]
        )
        self.container.bind(minimum_width=self.container.setter('width'))
        self._populate_items()
        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

        self.right_arrow_btn = _SelectorArrowBtn("chevron-right", lambda: self.scroll_by(1), is_left=False)
        self.add_widget(self.right_arrow_btn)

        self.update_theme_colors()

    def set_items_rotation(self, angle):
        self._current_rotation = angle
        if hasattr(self, 'left_arrow_btn'):
            self.left_arrow_btn.set_rotation(angle)
        if hasattr(self, 'right_arrow_btn'):
            self.right_arrow_btn.set_rotation(angle)
        for btn in self.buttons:
            btn.set_rotation(angle)

    def reset_scroll_if_needed(self):
        if self.scroll and self.container:
            if self.container.width <= self.scroll.width:
                self.scroll.scroll_x = 0
            else:
                self.scroll.scroll_x = max(0.0, min(1.0, self.scroll.scroll_x))

    def scroll_by(self, direction):
        new_scroll = max(0, min(1, self.scroll.scroll_x + direction * 0.2))
        Animation(scroll_x=new_scroll, duration=0.2, t='out_quad').start(self.scroll)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        arrow_color = ChordsColors.get_arrow_color(theme_id)
        if hasattr(self, 'left_arrow_btn'):
            self.left_arrow_btn.icon.text_color = arrow_color
        if hasattr(self, 'right_arrow_btn'):
            self.right_arrow_btn.icon.text_color = arrow_color
        for btn in self.buttons:
            btn._update_style()

    def _populate_items(self):
        pass

    def _get_button_width(self, text):
        return max(dp(42), len(text) * dp(10.5) + dp(20))

    def _highlight_current(self):
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == self.current_selection)

    def _on_item_press(self, value):
        self.current_selection = value
        self._highlight_current()
        if self.on_confirm:
            self.on_confirm(value)

    def show(self):
        self.is_visible = True
        self.opacity = 1
        self.disabled = False
        Clock.schedule_once(lambda dt: self.reset_scroll_if_needed(), 0)

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
            btn = TextSelectorButton(text=ton, on_press=self._on_item_press)
            btn.width = dp(42)
            self.buttons.append(btn)
            self.container.add_widget(btn)
        self.current_selection = self.current_tonality
        self._highlight_current()

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
            btn = TextSelectorButton(text=chord_type, on_press=self._on_item_press)
            btn.width = self._get_button_width(chord_type)
            self.buttons.append(btn)
            self.container.add_widget(btn)
        self.current_selection = self.current_type
        self._highlight_current()

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
            btn = TextSelectorButton(text=chord_name, on_press=self._on_item_press)
            btn.width = self._get_button_width(chord_name)
            self.buttons.append(btn)
            self.container.add_widget(btn)
        self.current_selection = self.current_chord
        self._highlight_current()

    def set_chords(self, chords, current_chord=None):
        new_chords = list(chords) if chords else []

        if new_chords == self.chords and len(self.container.children) == len(new_chords):
            if current_chord is not None and current_chord != self.current_chord:
                self.current_chord = current_chord
                self.current_selection = current_chord
                self._highlight_current()
            Clock.schedule_once(lambda dt: self.reset_scroll_if_needed(), 0)
            return

        self.chords = new_chords
        if current_chord is not None:
            self.current_chord = current_chord
            self.current_selection = current_chord
        self.container.clear_widgets()
        self.buttons = []
        self._populate_items()
        self.set_items_rotation(getattr(self, '_current_rotation', 0))
        self._highlight_current()
        if self.scroll:
            self.scroll.scroll_x = 0
        Clock.schedule_once(lambda dt: self.reset_scroll_if_needed(), 0)

    def set_current(self, chord_name):
        if chord_name == self.current_chord:
            return
        self.current_chord = chord_name
        self.current_selection = chord_name
        self._highlight_current()

class DashedDivider(Widget):
    """Короткая вертикальная линия строго внутри границ меню, как в тюнере."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(2)
        self._line_color = ChordsColors.get_divider_color(settings_manager.theme)
        with self.canvas:
            self._color = Color(*self._line_color)
            self._line = Line(points=[], width=dp(1.2))
        self.bind(pos=self._update_line, size=self._update_line)

    def _update_line(self, *args):
        if self.height <= dp(12) or self.width <= 0:
            self._line.points = []
            return
        pad = dp(5)
        cx = self.x + self.width / 2.0
        self._line.points = [cx, self.y + pad, cx, self.y + self.height - pad]

    def update_theme_colors(self):
        self._line_color = ChordsColors.get_divider_color(settings_manager.theme)
        self._color.rgba = self._line_color
        self._update_line()


class UnifiedMenu(MDBoxLayout):
    def __init__(self, tonality_value, type_value, chord_value,
                 on_tonality_press=None, on_type_press=None, on_chord_press=None,
                 on_variants_press=None, on_mode_toggle=None, on_rotate_press=None,
                 variants_count=1, current_mode="finger", chord_count=0, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, 1)
        self.md_bg_color = [0, 0, 0, 0]
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = dp(0)

        self.tonality_item = IconMenuItem(
            "music-note-eighth", on_tonality_press, True,
            icon_color=[0.61, 0.15, 0.69, 1], fixed_color=True
        )
        self.type_item = IconMenuItem(
            "tag", on_type_press, True,
            icon_color=[0.0, 0.74, 0.83, 1], fixed_color=True
        )
        self.chord_item = IconMenuItem(
            "music-circle", on_chord_press, True,
            icon_color=[1.0, 0.7, 0.0, 1] if chord_count > 1 else [1, 1, 1, 0.35],
            fixed_color=False
        )
        self.variants_item = IconMenuItem(
            "format-list-numbered", on_variants_press,
            is_active=(variants_count > 1),
            icon_color=[0.13, 0.59, 0.95, 1] if variants_count > 1 else [1, 1, 1, 0.3]
        )
        self.mode_item = IconMenuItem(
            "gesture-tap", on_mode_toggle, True,
            icon_color=[0.9, 0.55, 0.0, 1] if current_mode == "finger" else [0.8, 0.3, 0.3, 1],
            fixed_color=True
        )

        self.rotate_item = None
        if on_rotate_press is not None:
            self.rotate_item = IconMenuItem(
                "phone-rotate-landscape", on_rotate_press, True,
                icon_color=[0.25, 0.78, 0.55, 1], fixed_color=True
            )

        # Центральная ячейка под название аккорда (только для вертикального оверлея)
        self.center_name_box = AnchorLayout(
            anchor_x='center', anchor_y='center',
            size_hint=(1.8, 1), padding=[dp(4), 0, dp(4), 0]
        )
        self.center_name_label = MDLabel(
            text=chord_value or "A",
            font_size=sp(24),
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(1, 1),
            theme_text_color="Custom",
            text_color=ChordsColors.get_chord_name_color(settings_manager.theme),
        )
        self.center_name_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        self.center_name_box.add_widget(self.center_name_label)

        self._center_visible = False
        self._rebuild_slots()
        self.update_theme_colors()

    def _create_divider(self):
        return DashedDivider()

    def _rebuild_slots(self):
        """Собирает строго симметричные слоты без лишних скрытых виджетов."""
        self.clear_widgets()
        items_left = [self.tonality_item, self.type_item, self.chord_item]
        items_right = [self.variants_item, self.mode_item]
        if self.rotate_item is not None:
            items_right.append(self.rotate_item)

        for idx, item in enumerate(items_left):
            self.add_widget(item)
            if idx < len(items_left) - 1:
                self.add_widget(self._create_divider())

        if self._center_visible:
            self.add_widget(self._create_divider())
            self.add_widget(self.center_name_box)
            self.add_widget(self._create_divider())
        else:
            self.add_widget(self._create_divider())

        for idx, item in enumerate(items_right):
            self.add_widget(item)
            if idx < len(items_right) - 1:
                self.add_widget(self._create_divider())

        self.update_theme_colors()

    def set_center_chord_name(self, visible, chord_text=""):
        if visible:
            text = (chord_text or "?").strip()
            self.center_name_label.text = text
            fs = 24 if len(text) <= 4 else (20 if len(text) <= 7 else (16 if len(text) <= 10 else 13))
            self.center_name_label.font_size = sp(fs)

        if self._center_visible != visible:
            self._center_visible = visible
            self._rebuild_slots()

    def set_icons_rotation(self, angle):
        pass

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        for child in self.children:
            if isinstance(child, DashedDivider):
                child.update_theme_colors()
        if hasattr(self, 'center_name_label'):
            self.center_name_label.text_color = ChordsColors.get_chord_name_color(theme_id)

    def update_chord(self, chord_count):
        has_chords = chord_count > 1
        self.chord_item.is_active = True
        if has_chords:
            self.chord_item.set_color([1.0, 0.7, 0.0, 1])
            self.chord_item.icon_widget.opacity = 1
        else:
            self.chord_item.set_color([1, 1, 1, 0.35])
            self.chord_item.icon_widget.opacity = 0.7
        self.chord_item.update_state()

    def update_variants(self, count):
        has_variants = count > 1
        self.variants_item.is_active = has_variants
        if has_variants:
            self.variants_item.set_color([0.13, 0.59, 0.95, 1])
            self.variants_item.icon_widget.opacity = 1
        else:
            self.variants_item.set_color([1, 1, 1, 0.3])
            self.variants_item.icon_widget.opacity = 0.6
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
        with perf('chords.init.total'):
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

            self._local_tonality = LOCAL_TONALITY
            self._local_type = LOCAL_TYPE

            self._chords_client = get_chords_client()
            self._server_loading = False
            self.current_mode = "finger"
            self.search_bar = None
            self.search_status_label = None
            self.unified_menu = None
            self._menu_container = None
            self._info_label = None
            self._hint_timer = None
            self.bg_image = None
            self.bg_color_inst = None
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
            self._request_id = 0
            self._pending_chord_list = None

            saved = chords_state.get(allow_stale=True)
            if saved:
                self.current_tonality = saved.get('current_tonality', 'A')
                self.current_type = saved.get('current_type', 'Major')
                self.current_chord_name = saved.get('current_chord_name', 'A')
                self.current_variant_index = saved.get('current_variant_index', 0)
                self.current_mode = saved.get('current_mode', 'finger')
                try:
                    self.current_tonality_index = TONALITIES.index(self.current_tonality)
                    self.current_type_index = CHORD_TYPES.index(self.current_type)
                except ValueError:
                    pass
                logger.info(f"♻️ Chords: восстановлено из state: ton={self.current_tonality}, "
                            f"type={self.current_type}, chord={self.current_chord_name}, "
                            f"mode={self.current_mode}")

            try:
                chords_state.invalidate_scan()
            except AttributeError:
                chords_state._scan_done = False
                chords_state._all_chords = []

            with perf('chords.init.init_ui'):
                self.init_ui()
            with perf('chords.init.load_background'):
                self.load_background()

            Clock.schedule_once(lambda dt: self.scan_chords(), 0.1)
        logger.info('Экран аккордов создан')

    def _is_local_pair(self, tonality: str, chord_type: str) -> bool:
        return tonality == self._local_tonality and chord_type == self._local_type

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
        if not self.bg_color_inst:
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
        with perf('chords.update_theme_colors', log_every=False):
            self.update_screen_background()
            if self.search_bar:
                self.search_bar.update_theme_colors()
            if self.unified_menu:
                self.unified_menu.update_theme_colors()
            if self.swipe_container:
                self.swipe_container.update_theme_colors()
                self.swipe_container.update_fret_color(settings_manager.theme)
                self.swipe_container.update_overlay_theme()
            if self.tonality_selector:
                self.tonality_selector.update_theme_colors()
            if self.type_selector:
                self.type_selector.update_theme_colors()
            if self.chord_selector:
                self.chord_selector.update_theme_colors()

            if hasattr(self, 'menu_card'):
                theme_id = settings_manager.theme
                self.menu_card.md_bg_color = ChordsColors.get_menu_bg(theme_id)
                self.menu_card.line_color = ChordsColors.get_card_line(theme_id)
                self.menu_card.line_width = 1.5

            theme_id = settings_manager.theme
            hint_color = ChordsColors.get_hint_color(theme_id)
            if self._info_label:
                self._info_label.text_color = hint_color
            if self.search_status_label:
                self.search_status_label.text_color = hint_color

    def update_language(self):
        if self.search_bar:
            self.search_bar.update_language()
        self._set_search_status(None)
        self._show_description()

    def _ensure_menus(self):
        if self._menu_cache_initialized:
            return
        with perf('chords.create_menus.total'):
            with perf('chords.create_menus.tonality'):
                self.tonality_selector = TonalitySelectorMenu(
                    self.current_tonality, self._on_tonality_confirmed, self._close_tonality_selector
                )
            with perf('chords.create_menus.type'):
                self.type_selector = TypeSelectorMenu(
                    self.current_type, self._on_type_confirmed, self._close_type_selector
                )
            with perf('chords.create_menus.chord'):
                self.chord_selector = ChordSelectorMenu(
                    self.current_chord_name, self._on_chord_confirmed,
                    self._close_chord_selector, chords=self.available_chords
                )
            self._menu_cache_initialized = True

    def _update_desc_height(self, instance, texture_size):
        if texture_size:
            new_height = texture_size[1] + dp(8)
            if self._info_label.height != new_height:
                self._info_label.height = new_height

    def _update_griff_size(self, *args):
        with perf('chords.update_griff_size', log_every=False):
            if hasattr(self, 'swipe_container') and self.swipe_container:
                window_width = Window.width
                available_width = window_width - dp(24)
                griff_height = available_width * 0.45
                min_height = dp(200)
                max_height = window_width * 0.6
                griff_height = max(min_height, min(griff_height, max_height))
                new_height = int(griff_height) + dp(90)
                self._griff_height = int(griff_height)
                if abs(self.swipe_container.height - new_height) > 0.5:
                    self.swipe_container.height = new_height

    def _variants_equal(self, a, b):
        if len(a) != len(b):
            return False
        for x, y in zip(a, b):
            if x.get('short_name') != y.get('short_name'):
                return False
            if x.get('variant') != y.get('variant'):
                return False
        return True

    def _rebuild_slides_for_current_chord(self):
        if not self.swipe_container:
            return
        with perf('chords.rebuild_slides.local'):
            with perf('chords.rebuild_slides.local.clear', log_every=False):
                self.swipe_container.clear_slides()
            for variant in self.current_variants:
                module = variant.get('module')
                if module:
                    with perf('chords.rebuild_slides.local.add_slide', log_every=False):
                        self.swipe_container.add_slide(module)
            if self.current_variants:
                with perf('chords.rebuild_slides.local.set_current', log_every=False):
                    self.swipe_container.set_current_slide(self.current_variant_index)
            chords_state.mark_slides_built(
                settings_manager.theme,
                self.current_chord_name,
                self.current_variants,
            )

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
            "name": data.get("main_name", ""), "variant": data.get("variant", 1),
            "type": data.get("chord_type", ""), "description": data.get("description", ""),
        }
        return m

    def _rebuild_server_slides(self):
        if not self.swipe_container:
            return
        with perf('chords.rebuild_slides.server'):
            with perf('chords.rebuild_slides.server.clear', log_every=False):
                self.swipe_container.clear_slides()
            for variant in self.current_variants:
                server_data = variant.get("server_data")
                if not server_data:
                    continue
                with perf('chords.rebuild_slides.server.dict_to_module', log_every=False):
                    module = self._dict_to_module(server_data)
                with perf('chords.rebuild_slides.server.add_slide', log_every=False):
                    self.swipe_container.add_slide(module)
            if self.current_variants:
                with perf('chords.rebuild_slides.server.set_current', log_every=False):
                    self.swipe_container.set_current_slide(self.current_variant_index)
            chords_state.mark_slides_built(
                settings_manager.theme,
                self.current_chord_name,
                self.current_variants,
            )

    def _update_display(self):
        if not self.current_variants:
            return
        with perf('chords.update_display', log_every=False):
            variant = self.current_variants[self.current_variant_index]

            with perf('chords.update_display.parse_names', log_every=False):
                if variant.get("module") is not None:
                    self.current_chord_module = variant["module"]
                    chord_name = variant["name"].replace('!', ' | ').replace('$', '/')
                    name_parts = [p.strip() for p in chord_name.split('|') if p.strip()]
                else:
                    self.current_chord_module = None
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

            with perf('chords.update_display.update_chord_name', log_every=False):
                if self.swipe_container:
                    self.swipe_container.update_chord_name(main_name, alt_names)

            with perf('chords.update_display.show_description', log_every=False):
                if not (hasattr(self, '_hint_timer') and self._hint_timer):
                    self._show_description()
            self._data_loaded = True

    def init_ui(self):
        with perf('chords.init_ui.build'):
            padding = layout_config.get_content_padding()
            content = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))

            content.add_widget(Widget(size_hint_y=None, height=dp(48)))

            search_container = MDBoxLayout(
                orientation='vertical', size_hint=(1, None), height=dp(48),
                padding=[padding[0], 0, padding[2], 0],
            )
            self.search_bar = SearchBar(on_search=self.do_search, on_clear=self.clear_search)
            search_container.add_widget(self.search_bar)
            content.add_widget(search_container)

            content.add_widget(Widget(size_hint_y=None, height=dp(4)))

            self.search_status_label = MDLabel(
                text="", font_size=sp(11), halign="center", valign="middle",
                size_hint=(1, None), height=0, opacity=0, theme_text_color="Custom",
            )
            self.search_status_label.text_size = (None, None)
            content.add_widget(self.search_status_label)

            content.add_widget(Widget(size_hint_y=None, height=dp(24)))

            self.swipe_container = SwipeContainer(
                on_swipe_horizontal=self._on_swipe_horizontal,
                screen=self,
            )
            self.swipe_container.size_hint = (1, None)
            self.swipe_container.height = self._griff_height + dp(90)
            content.add_widget(self.swipe_container)

            Window.bind(on_resize=self._on_window_resize)

            content.add_widget(Widget(size_hint_y=None, height=dp(18)))

            menu_padding_side = dp(38)
            menu_wrapper = MDBoxLayout(orientation='vertical', size_hint=(1, None), height=dp(64),
                                       padding=[menu_padding_side, 0, menu_padding_side, 0])

            self.menu_card = MDCard(
                orientation='horizontal', size_hint=(1, 1), radius=[dp(16)],
                elevation=0, padding=[dp(2), dp(2), dp(2), dp(2)], spacing=dp(0)
            )

            self._menu_container = FloatLayout(size_hint=(1, 1))

            self.unified_menu = UnifiedMenu(
                tonality_value=self.current_tonality, type_value=self.current_type,
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
            self.unified_menu.size_hint = (1, 1)
            self.unified_menu.pos_hint = {'x': 0, 'y': 0}
            self._menu_container.add_widget(self.unified_menu)

            self.menu_card.add_widget(self._menu_container)
            menu_wrapper.add_widget(self.menu_card)
            content.add_widget(menu_wrapper)

            content.add_widget(Widget(size_hint_y=None, height=dp(2)))

            self._info_label = MDLabel(
                text="", font_size=sp(12), halign="center", size_hint_y=None,
                height=dp(30), theme_text_color="Custom",
            )
            self._info_label.text_size = (None, None)
            self._info_label.bind(texture_size=self._update_desc_height)
            content.add_widget(self._info_label)

            content.add_widget(Widget(size_hint_y=1))

            self.build_ui(
                content_widget=content,
                use_scroll=False,
                custom_padding=[0, 0, 0, 0],
            )

            Clock.schedule_once(self._update_griff_size, 0.1)
            Clock.schedule_once(self._update_griff_size, 0.3)
            Clock.schedule_once(self._update_griff_size, 0.5)
            Clock.schedule_once(lambda dt: self._update_display(), 0.2)
            Clock.schedule_once(lambda dt: self.update_theme_colors(), 0.3)

    def _set_search_status(self, status):
        if not self.search_status_label:
            return
        theme_id = settings_manager.theme
        if status == 'found':
            self.search_status_label.text = get_text('search_found', "Мы нашли ваш аккорд")
            if theme_id == 'dark':
                self.search_status_label.text_color = [1.0, 0.5, 0.0, 1]
            elif theme_id == 'light':
                self.search_status_label.text_color = [0.1, 0.55, 0.3, 1]
            else:
                self.search_status_label.text_color = [0.35, 0.75, 0.45, 1]
            self.search_status_label.opacity = 1
            self.search_status_label.height = dp(18)
        elif status == 'not_found':
            self.search_status_label.text = get_text('search_not_found', "По вашему запросу ничего не нашлось")
            if theme_id == 'dark':
                self.search_status_label.text_color = [1.0, 0.5, 0.0, 1]
            elif theme_id == 'light':
                self.search_status_label.text_color = [0.1, 0.55, 0.3, 1]
            else:
                self.search_status_label.text_color = [0.85, 0.45, 0.45, 1]
            self.search_status_label.opacity = 1
            self.search_status_label.height = dp(18)
        else:
            self.search_status_label.text = ""
            self.search_status_label.opacity = 0
            self.search_status_label.height = 0

    def _on_swipe_horizontal(self, step):
        with perf('chords.on_swipe', log_every=False):
            if not self.current_variants or len(self.current_variants) <= 1:
                self._show_temporary_hint(get_text('no_variants', "Нет других вариантов"), 1.0)
                return
            total = len(self.current_variants)
            self.current_variant_index = (self.current_variant_index + step) % total
            self.current_position = self.current_variant_index + 1

            with perf('chords.on_swipe.set_current', log_every=False):
                if self.swipe_container:
                    self.swipe_container.set_current_slide(self.current_variant_index)

            with perf('chords.on_swipe.update_display', log_every=False):
                self._update_display()
            self._show_temporary_hint(f"{get_text('variant', 'Вариант')} {self.current_position}", 1.0)

    def _on_carousel_index_changed(self, index, from_overlay=False):
        if not self.current_variants or not (0 <= index < len(self.current_variants)):
            return
        if self.current_variant_index == index:
            return

        self.current_variant_index = index
        self.current_position = index + 1

        if from_overlay:
            if self.swipe_container:
                self.swipe_container.set_current_slide(index)
        else:
            if self.swipe_container and self.swipe_container._big_swipe:
                self.swipe_container._big_swipe.set_current_slide(index)

        self._update_display()
        if self.swipe_container:
            self.swipe_container._update_overlay_name()
            self.swipe_container._update_overlay_menu()
        self._show_temporary_hint(f"{get_text('variant', 'Вариант')} {self.current_position}", 1.2)

    def _show_selector(self, selector):
        self._menu_container.clear_widgets()

        if selector is not None:
            if selector.parent is not None:
                selector.parent.remove_widget(selector)
            selector.set_items_rotation(0)
            selector.disabled = False
            selector.opacity = 1
            selector.size_hint = (1, 1)
            selector.pos_hint = {'x': 0, 'y': 0}
            self._menu_container.add_widget(selector)
            selector.is_visible = True
            Clock.schedule_once(lambda dt: selector.reset_scroll_if_needed(), 0)

    def _restore_unified(self):
        self._menu_container.clear_widgets()

        if self.unified_menu:
            self.unified_menu.disabled = False
            self.unified_menu.opacity = 1
            self.unified_menu.size_hint = (1, 1)
            self.unified_menu.pos_hint = {'x': 0, 'y': 0}
            self._menu_container.add_widget(self.unified_menu)

        self._restore_description()

    def _open_chord_selector(self):
        self._ensure_menus()
        if self.chord_selector and self.chord_selector.parent:
            self._restore_unified()
            return
        if not self.available_chords and not self._pending_chord_list:
            self._show_temporary_hint(get_text('no_chords', "Нет доступных аккордов"), 1.0)
            return

        if self.chord_selector is not None:
            target_list = self._pending_chord_list if self._pending_chord_list is not None else self.available_chords
            self.chord_selector.set_chords(target_list, current_chord=self.current_chord_name)
            self._pending_chord_list = None

        self.chord_selector.set_current(self.current_chord_name)
        self._show_selector(self.chord_selector)
        self._show_hint(get_text('choose_chord', "Выберите аккорд"))

    def _on_chord_confirmed(self, selected_chord):
        if not selected_chord or selected_chord == self.current_chord_name:
            self._restore_unified()
            return

        self.current_chord_name = selected_chord
        if selected_chord in self.available_chords:
            self.current_chord_index = self.available_chords.index(selected_chord)
        if self.unified_menu:
            self.unified_menu.update_chord(len(self.available_chords))

        def _after_delay(dt):
            self._restore_unified()
            self._show_hint(get_text('loading', 'Загрузка...'))
            Clock.schedule_once(lambda dt2: self._load_variants_for_chord(self.current_chord_name), 0.05)

        Clock.schedule_once(_after_delay, 0.25)

    def _close_chord_selector(self):
        self._restore_unified()

    def _show_description(self):
        if hasattr(self, '_hint_timer') and self._hint_timer:
            return

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
                formatted_desc = unique_desc[0]
                main_name = self._current_main_name
                if main_name and main_name in formatted_desc:
                    formatted_desc = formatted_desc.replace(main_name, '').strip(' |,')
                formatted_desc = re.sub(r'\s*\|\s*', ', ', formatted_desc).strip(' ,')
                formatted_desc = re.sub(r'\s+', ' ', formatted_desc)
                if formatted_desc:
                    parts.append(formatted_desc)

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
        self._ensure_menus()
        if self.tonality_selector and self.tonality_selector.parent:
            self._restore_unified()
            return
        self.tonality_selector.set_current(self.current_tonality)
        self._show_selector(self.tonality_selector)
        self._show_hint(get_text('choose_tonality', "Выберите тональность"))

    def _on_tonality_confirmed(self, selected_tonality):
        with perf('chords.action.on_tonality_confirmed'):
            self.current_tonality = selected_tonality
            self.current_tonality_index = TONALITIES.index(selected_tonality)
            self.is_search_mode = False
            self._set_search_status(None)
            self.current_chord_name = ""
            self.current_chord_index = 0
            self.current_variants = []
            self.current_variant_index = 0
            self.current_position = 1

            def _after_delay(dt):
                self._restore_unified()
                self._show_hint(get_text('loading', 'Загрузка...'))
                Clock.schedule_once(lambda dt2: self.update_available_chords(), 0.05)

            Clock.schedule_once(_after_delay, 0.25)

    def _close_tonality_selector(self):
        self._restore_unified()

    def _open_type_selector(self):
        self._ensure_menus()
        if self.type_selector and self.type_selector.parent:
            self._restore_unified()
            return
        self.type_selector.set_current(self.current_type)
        self._show_selector(self.type_selector)
        self._show_hint(get_text('choose_type', "Выберите тип аккорда"))

    def _on_type_confirmed(self, selected_type):
        with perf('chords.action.on_type_confirmed'):
            self.current_type = selected_type
            self.current_type_index = CHORD_TYPES.index(selected_type)
            self.is_search_mode = False
            self._set_search_status(None)
            self.current_chord_name = ""
            self.current_chord_index = 0
            self.current_variants = []
            self.current_variant_index = 0
            self.current_position = 1

            def _after_delay(dt):
                self._restore_unified()
                self._show_hint(get_text('loading', 'Загрузка...'))
                Clock.schedule_once(lambda dt2: self.update_available_chords(), 0.05)

            Clock.schedule_once(_after_delay, 0.25)

    def _close_type_selector(self):
        self._restore_unified()

    def _toggle_mode(self):
        with perf('chords.action.toggle_mode', log_every=False):
            if self.current_mode == "finger":
                self.current_mode = "notes"
                self._show_temporary_hint(get_text('mode_notes', "Выбран режим показа нот"), 1.2)
            else:
                self.current_mode = "finger"
                self._show_temporary_hint(get_text('mode_fingers', "Выбран режим постановки пальцев"), 1.2)
            self.unified_menu.update_mode(self.current_mode)
            if self.swipe_container:
                self.swipe_container.update_renderer_mode(self.current_mode)

    def _next_variant(self):
        with perf('chords.action.next_variant', log_every=False):
            if not self.current_variants or len(self.current_variants) <= 1:
                notify.info(get_text('no_variants', "Нет других вариантов"))
                return
            total = len(self.current_variants)
            self.current_variant_index = (self.current_variant_index + 1) % total
            self.current_position = self.current_variant_index + 1
            if self.swipe_container:
                self.swipe_container.set_current_slide(self.current_variant_index)
            self._update_display()
            msg = f"{get_text('variant', 'Вариант')} {self.current_position}"
            self._show_temporary_hint(msg, 1.2)

    def do_search(self, query):
        with perf('chords.action.do_search'):
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
            alt_map = {'bb': 'a#', 'a#': 'bb', 'db': 'c#', 'c#': 'db', 'eb': 'd#', 'd#': 'eb',
                       'gb': 'f#', 'f#': 'gb', 'ab': 'g#', 'g#': 'ab'}
            alt_query = alt_map.get(query_lower, None)

            with perf('chords.action.do_search.local_lookup', log_every=False):
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
                self._set_search_status('found')
                selected_chord = self.search_results[0]
                self.current_chord_name = selected_chord['short_name']
                self.unified_menu.update_chord(len(self.available_chords))
                variants = [
                    c for c in self.all_chords
                    if c['short_name'] == self.current_chord_name
                    and self.extract_tonality(c['name']) == self.current_tonality
                ]
                if variants:
                    variants.sort(key=lambda x: x['variant'])
                    self.current_variants = variants
                    self.current_variant_index = 0
                    self.current_position = 1
                    self.unified_menu.update_variants(len(variants))
                    with perf('chords.action.do_search.rebuild_local_slides'):
                        self._rebuild_slides_for_current_chord()
                    with perf('chords.action.do_search.update_display'):
                        self._update_display()
                else:
                    self._load_variants_for_chord(self.current_chord_name)
            else:
                with perf('chords.action.do_search.to_server'):
                    self._search_server(query_original)

    def _search_server(self, query: str):
        t_net = time.perf_counter()

        def _on_results(items):
            dt_net = (time.perf_counter() - t_net) * 1000.0
            _perf_log.info(f"🌐 GET chords/search '{query}' OK {dt_net:.1f} ms results={len(items or [])}")
            perf_registry.add('chords.net.search', dt_net)
            if not items:
                alt = query.replace('#', 'b') if '#' in query else query.replace('b', '#')
                if alt != query:
                    self._chords_client.search_by_synonym(
                        alt,
                        on_success=lambda items2: self._handle_server_search_results(items2, alt),
                        on_error=lambda msg: self._set_search_status('not_found')
                    )
                else:
                    self._set_search_status('not_found')
            else:
                self._handle_server_search_results(items, query)

        def _on_err(msg):
            dt_net = (time.perf_counter() - t_net) * 1000.0
            _perf_log.warning(f"🌐 GET chords/search '{query}' FAIL {dt_net:.1f} ms err={msg}")
            self._set_search_status('not_found')

        self._chords_client.search_by_synonym(query, on_success=_on_results, on_error=_on_err)

    def _handle_server_search_results(self, items, query):
        if not items:
            self._set_search_status('not_found')
            return
        best = items[0]
        main_name = best.get("main_name") or query
        tonality = best.get("tonality") or ""
        chord_type = best.get("chord_type") or ""
        self._set_search_status('found')
        if tonality in self.TONALITIES:
            self.current_tonality = tonality
            self.current_tonality_index = self.TONALITIES.index(tonality)
        if chord_type in self.CHORD_TYPES:
            self.current_type = chord_type
            self.current_type_index = self.CHORD_TYPES.index(chord_type)
        self.is_search_mode = False
        self.current_chord_name = main_name
        self._load_available_and_variants(main_name)

    def _load_available_and_variants(self, target_chord_name: str):
        def _on_list(chords):
            self.available_chords = list(chords or [])
            if target_chord_name not in self.available_chords:
                self.available_chords.append(target_chord_name)
                self.available_chords.sort()
            if self.unified_menu:
                self.unified_menu.update_chord(len(self.available_chords))
            self._pending_chord_list = list(self.available_chords)
            self.current_chord_name = target_chord_name
            self.current_chord_index = self.available_chords.index(target_chord_name)
            self._load_variants_for_chord(target_chord_name)

        def _on_err(msg):
            self.available_chords = [target_chord_name]
            self.current_chord_name = target_chord_name
            self.current_chord_index = 0
            if self.unified_menu:
                self.unified_menu.update_chord(1)
            self._pending_chord_list = [target_chord_name]
            self._load_variants_for_chord(target_chord_name)

        self._chords_client.get_available_chords(self.current_tonality, self.current_type, on_success=_on_list,
                                                 on_error=_on_err)

    def clear_search(self):
        with perf('chords.action.clear_search', log_every=False):
            self.is_search_mode = False
            self.search_results = []
            self._set_search_status(None)
            self.current_chord_name = ""
            self.current_chord_index = 0
            self.current_variants = []
            self.current_variant_index = 0
            self.current_position = 1
            self.update_available_chords()

    def scan_chords(self):
        with perf('chords.scan.total'):
            if chords_state.is_scan_done():
                self.all_chords = chords_state.get_all_chords()
                logger.info(f"♻️ Chords: восстановлено {len(self.all_chords)} локальных модулей из кэша")
                with perf('chords.scan.update_available (from cache)'):
                    self.update_available_chords()
                self._data_loaded = True
                return

            self.all_chords = []
            try:
                with perf('chords.scan.pkgutil_importlib'):
                    import chords
                    self._scan_module_recursive(chords, 'chords')
            except Exception as e:
                logger.error(f"Chords: ошибка сканирования пакета: {e}")

            chords_state.set_all_chords(self.all_chords)
            logger.info(f"🔍 Chords: просканировано {len(self.all_chords)} локальных модулей")
            with perf('chords.scan.update_available (from scan)'):
                self.update_available_chords()
            self._data_loaded = True

    def _scan_module_recursive(self, module, module_path):
        if hasattr(module, '__path__'):
            for module_info in pkgutil.iter_modules(module.__path__, f"{module_path}."):
                try:
                    sub_module = importlib.import_module(module_info.name)
                    if hasattr(sub_module, '__path__'):
                        self._scan_module_recursive(sub_module, module_info.name)
                    else:
                        self._load_chord_module(sub_module, module_info.name)
                except Exception:
                    pass

    def _load_chord_module(self, module, module_name):
        try:
            metadata = getattr(module, 'METADATA', {})
            chord_name = metadata.get('name', module_name.split('.')[-1]).replace('!', '|').replace('$', '/')
            path_parts = module_name.split('.')
            chord_type = metadata.get('type', '')
            if not chord_type and len(path_parts) >= 2:
                chord_type = path_parts[-2]

            tonality = self.extract_tonality(chord_name)
            if tonality != self._local_tonality or chord_type != self._local_type:
                return

            variant_match = re.search(r'_(\d+)$', path_parts[-1])
            variant_num = int(variant_match.group(1)) if variant_match else metadata.get('variant', 1)
            short_name = chord_name.split('|')[0].replace('$', '/')
            self.all_chords.append({
                'id': f"{short_name}_{chord_type}_v{variant_num}", 'name': chord_name,
                'short_name': short_name, 'variant': variant_num, 'type': chord_type,
                'description': metadata.get('description', ''), 'module': module, 'path': module_name
            })
        except Exception as e:
            logger.debug(f"Chords: пропущен модуль {module_name}: {e}")

    def update_available_chords(self):
        if self.is_search_mode:
            return

        mode = 'local' if self._is_local_pair(self.current_tonality, self.current_type) else 'server'
        with perf(f'chords.update_available.{mode}'):

            if mode == 'local':
                with perf('chords.update_available.local.filter', log_every=False):
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
                        if chord['short_name'] not in chords_by_name:
                            chords_by_name[chord['short_name']] = []
                        chords_by_name[chord['short_name']].append(chord)

                self.available_chords = sorted(chords_by_name.keys())
                if self.unified_menu:
                    self.unified_menu.update_chord(len(self.available_chords))
                self._pending_chord_list = list(self.available_chords)

                if self.available_chords:
                    if self.current_chord_name not in self.available_chords:
                        self.current_chord_index = 0
                        self.current_chord_name = self.available_chords[0]
                    if chords_by_name.get(self.current_chord_name):
                        with perf('chords.update_available.local.load_variants'):
                            self.load_chord_variants(chords_by_name.get(self.current_chord_name))
                else:
                    self.current_variants = []
                    self.current_chord_data = None
                return

            self._request_id += 1
            my_id = self._request_id
            t_net = time.perf_counter()

            def _on_list(chords):
                dt_net = (time.perf_counter() - t_net) * 1000.0
                _perf_log.info(
                    f"🌐 GET available_chords ton={self.current_tonality} "
                    f"type={self.current_type} OK {dt_net:.1f} ms count={len(chords or [])}"
                )
                perf_registry.add('chords.net.available_chords', dt_net)

                if my_id != self._request_id:
                    return
                with perf('chords.update_available.server.on_list'):
                    self.available_chords = list(chords or [])
                    if self.unified_menu:
                        self.unified_menu.update_chord(len(self.available_chords))
                    self._pending_chord_list = list(self.available_chords)
                    if not self.available_chords:
                        self._show_temporary_hint("None", 2.0)
                        self.current_variants = []
                        if self.unified_menu:
                            self.unified_menu.update_variants(0)
                        return
                    if self.current_chord_name not in self.available_chords:
                        self.current_chord_index = 0
                        self.current_chord_name = self.available_chords[0]
                    self._load_variants_for_chord(self.current_chord_name)

            def _on_err(msg):
                dt_net = (time.perf_counter() - t_net) * 1000.0
                _perf_log.warning(
                    f"🌐 GET available_chords ton={self.current_tonality} "
                    f"type={self.current_type} FAIL {dt_net:.1f} ms err={msg}"
                )
                if my_id != self._request_id:
                    return
                self.available_chords = []
                self._pending_chord_list = []
                if self.unified_menu:
                    self.unified_menu.update_chord(0)
                self._show_temporary_hint(get_text('loading_error', 'Ошибка загрузки'), 2.0)

            self._chords_client.get_available_chords(
                self.current_tonality, self.current_type,
                on_success=_on_list, on_error=_on_err
            )

    def extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def load_chord_variants(self, variants):
        if not variants:
            return
        with perf('chords.load_chord_variants.local', log_every=False):
            variants.sort(key=lambda x: x['variant'])
            same = self._variants_equal(variants, self.current_variants)
            self.current_variants = variants
            self.current_variant_index = 0
            self.current_position = 1
            if self.unified_menu:
                self.unified_menu.update_variants(len(variants))

            can_reuse = same and chords_state.can_reuse_slides(
                settings_manager.theme, self.current_chord_name, variants
            )
            if can_reuse:
                logger.debug(f"♻️ Chords: локальные слайды переиспользованы ({self.current_chord_name})")
            else:
                with perf('chords.load_chord_variants.rebuild_slides'):
                    self._rebuild_slides_for_current_chord()

            with perf('chords.load_chord_variants.update_display'):
                self._update_display()

    def _load_variants_for_chord(self, chord_name):
        mode = 'local' if self._is_local_pair(self.current_tonality, self.current_type) else 'server'
        with perf(f'chords.load_variants.{mode}'):
            if mode == 'local':
                with perf('chords.load_variants.local.filter', log_every=False):
                    variants = []
                    for chord in self.all_chords:
                        if chord['short_name'] != chord_name:
                            continue
                        if self.extract_tonality(chord['name']) != self.current_tonality:
                            continue
                        chord_types = chord['type'].split('|') if chord['type'] else []
                        if self.current_type in chord_types or self.current_type == chord.get('type', ''):
                            variants.append(chord)
                if variants:
                    variants.sort(key=lambda x: x['variant'])
                    same = self._variants_equal(variants, self.current_variants)
                    self.current_variants = variants
                    self.current_variant_index = 0
                    self.current_position = 1
                    if self.unified_menu:
                        self.unified_menu.update_variants(len(variants))

                    can_reuse = same and chords_state.can_reuse_slides(
                        settings_manager.theme, self.current_chord_name, variants
                    )
                    if can_reuse:
                        logger.debug(f"♻️ Chords: локальные слайды переиспользованы ({chord_name})")
                    else:
                        with perf('chords.load_variants.local.rebuild_slides'):
                            self._rebuild_slides_for_current_chord()

                    with perf('chords.load_variants.local.update_display'):
                        self._update_display()
                else:
                    self.current_variants = []
                    self.current_variant_index = 0
                    self.current_position = 1
                    if self.unified_menu:
                        self.unified_menu.update_variants(0)
                return

            self._server_loading = True
            self._request_id += 1
            my_id = self._request_id
            t_net = time.perf_counter()

            def _on_success(variants):
                dt_net = (time.perf_counter() - t_net) * 1000.0
                _perf_log.info(
                    f"🌐 GET chord {chord_name}/{self.current_type} "
                    f"OK {dt_net:.1f} ms variants={len(variants or [])}"
                )
                perf_registry.add('chords.net.chord_variants', dt_net)

                if my_id != self._request_id:
                    return
                with perf('chords.load_variants.server.on_success'):
                    self._server_loading = False
                    normalized = []
                    for v in variants:
                        syn = v.get("synonyms") or [v.get("main_name", "?")]
                        normalized.append({
                            "name": " | ".join(syn), "short_name": v.get("main_name", "?"),
                            "variant": v.get("variant", 1), "type": v.get("chord_type", ""),
                            "description": v.get("description", ""), "module": None, "server_data": v,
                        })
                    normalized.sort(key=lambda x: x["variant"])
                    same = self._variants_equal(normalized, self.current_variants)
                    self.current_variants = normalized
                    self.current_variant_index = 0
                    self.current_position = 1
                    if self.unified_menu:
                        self.unified_menu.update_variants(len(normalized))

                    can_reuse = same and chords_state.can_reuse_slides(
                        settings_manager.theme, self.current_chord_name, normalized
                    )
                    if can_reuse:
                        logger.debug(f"♻️ Chords: серверные слайды переиспользованы ({chord_name}/{self.current_type})")
                    else:
                        with perf('chords.load_variants.server.rebuild_slides'):
                            self._rebuild_server_slides()

                    with perf('chords.load_variants.server.update_display'):
                        self._update_display()

            def _on_error(msg):
                dt_net = (time.perf_counter() - t_net) * 1000.0
                _perf_log.warning(
                    f"🌐 GET chord {chord_name}/{self.current_type} "
                    f"FAIL {dt_net:.1f} ms err={msg}"
                )
                if my_id != self._request_id:
                    return
                self._server_loading = False
                self.current_variants = []
                self.current_variant_index = 0
                self.current_position = 1
                if self.unified_menu:
                    self.unified_menu.update_variants(0)
                self._show_temporary_hint(get_text('loading_error', 'Ошибка загрузки'), 2.0)

            self._chords_client.get_chord(
                chord_name, self.current_type,
                on_success=_on_success, on_error=_on_error
            )

    def select_chord_by_name(self, chord_name):
        with perf('chords.action.select_chord_by_name'):
            target_chord = None
            for chord in self.all_chords:
                if chord['short_name'] == chord_name:
                    target_chord = chord
                    break
            if not target_chord:
                for chord in self.all_chords:
                    for variant in chord['name'].split('|'):
                        if variant.strip().replace('$', '/') == chord_name:
                            target_chord = chord
                            break
                    if target_chord:
                        break
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
                chord_key = target_chord['short_name']
                if chord_key in self.available_chords:
                    self.current_chord_name = chord_key
                    self.current_chord_index = self.available_chords.index(chord_key)
                    self._load_variants_for_chord(self.current_chord_name)
                    return True
                return self._find_and_load_chord_variant(target_chord)
            self._search_server(chord_name)
            return True

    def _extract_tonality_from_name(self, chord_name):
        if not chord_name:
            return "A"
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "A")

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
        with perf('chords.on_window_resize', log_every=False):
            if hasattr(self, '_update_griff_timer') and self._update_griff_timer:
                Clock.unschedule(self._update_griff_timer)
            self._update_griff_timer = Clock.schedule_once(lambda dt: self._update_griff_size(), 0.15)

    def _save_state(self):
        chords_state.save({
            'current_tonality': self.current_tonality,
            'current_type': self.current_type,
            'current_chord_name': self.current_chord_name,
            'current_variant_index': self.current_variant_index,
            'current_mode': self.current_mode,
        })

    def on_enter(self):
        with perf('chords.on_enter.total'):
            super().on_enter()

            with perf('chords.on_enter.update_theme'):
                self.update_theme_colors()

            theme_id = settings_manager.theme
            can_reuse = chords_state.can_reuse_slides(
                theme_id, self.current_chord_name, self.current_variants
            )
            if self.swipe_container and self.current_variants and not can_reuse:
                with perf('chords.on_enter.rebuild_slides'):
                    Clock.schedule_once(lambda dt: self._rebuild_slides_for_current_chord(), 0.05)
                logger.info(f"🔄 Chords: пересоздание слайдов (theme={theme_id}, chord={self.current_chord_name})")
            else:
                logger.debug(f"♻️ Chords: слайды переиспользованы (theme={theme_id}, chord={self.current_chord_name})")

            Clock.schedule_once(self._update_griff_size, 0.1)
            Clock.schedule_once(self._update_griff_size, 0.3)

            with perf('chords.on_enter.pending_chord', log_every=False):
                pending_chord = previous_screen_state.get_pending_chord()
                if pending_chord:
                    Clock.schedule_once(lambda dt: self.select_chord_by_name(pending_chord), 0.1)
                    previous_screen_state.clear_pending_chord()

            previous_screen = previous_screen_state.get_previous()
            if previous_screen:
                Clock.schedule_once(lambda dt: self._show_back_button(), 0.3)

            self._close_tonality_selector()
            self._close_type_selector()
            self._close_chord_selector()
            if self.swipe_container and self._current_alt_names:
                self.swipe_container.update_chord_name(self._current_main_name, self._current_alt_names)

            self._save_state()

    def _show_back_button(self):
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav._custom_back_callback = self.go_back
                app.top_nav.screen_title.text = get_text('chords', 'Аккорды')
        except Exception:
            pass

    def on_leave(self):
        perf_registry.dump(prefix='[chords]')
        self._close_tonality_selector()
        self._close_type_selector()
        self._close_chord_selector()
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None
        if self.swipe_container:
            self.swipe_container._stop_alt_cycle()
        self._save_state()

    def go_back(self, instance=None):
        if self.manager and self.manager.has_screen('home'):
            self.manager.current = 'home'

    def on_size(self, *args):
        with perf('chords.on_size', log_every=False):
            if hasattr(self, '_update_griff_timer') and self._update_griff_timer:
                Clock.unschedule(self._update_griff_timer)
            self._update_griff_timer = Clock.schedule_once(lambda dt: self._update_griff_size(), 0.15)