# screens/favorite_detail_screen.py
"""
Экран просмотра песни ИЗ ИЗБРАННОГО.
Управление избранным — через TopNav.
Панель настроек открывается через шестеренку в TopNav.
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.slider import MDSlider
from kivymd.uix.card import MDSeparator
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.utils import platform
from io import BytesIO
import re

from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from chord_utils.renderer import ChordRenderer
from api.client import api
from utils.notifications import notify
from state.settings_state import settings_state as settings_manager
from utils.localization import get_text
from chord_utils.chord_highlighter import (
    ChordTextLabel,
    highlight_chords_in_text,
    extract_chords_from_text_wrapper as extract_chords_from_text,
)
from chord_utils.transposer import transpose_text, transpose_chord_list

logger = screen_logger('FavoriteDetail')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА ДЛЯ ЭКРАНА
# ============================================================
class DetailColors:
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
            return [0.1, 0.1, 0.1, 0.95]
        else:
            return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        else:
            return [1, 1, 1, 0.7]

    @staticmethod
    def get_panel_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 0.98]
        elif theme_id == 'dark':
            return [0.12, 0.12, 0.12, 0.98]
        else:
            return [0.05, 0.25, 0.15, 0.95]

    @staticmethod
    def get_panel_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.8]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.8]
        else:
            return [0.4, 0.8, 0.5, 0.5]

    @staticmethod
    def get_divider(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 0.1]
        else:
            return [0.5, 0.5, 0.5, 0.3]

    @staticmethod
    def get_icon_color(theme_id, action_name):
        """Возвращает уникальный цвет для каждой иконки во всех темах."""
        if theme_id == 'light':
            colors = {
                'chords': [0.61, 0.15, 0.69, 1],
                'tonality': [0.0, 0.74, 0.83, 1],
                'scroll': [0.9, 0.6, 0.0, 1],
                'tabs': [0.13, 0.59, 0.95, 1],
                'font': [0.8, 0.3, 0.3, 1],
                'back': [0.1, 0.55, 0.3, 1],
                'variant': [0.5, 0.2, 0.8, 1],
                'mode': [0.0, 0.7, 0.5, 1],
                'eye': [0.8, 0.4, 0.0, 1],
                'zoom': [0.2, 0.6, 0.9, 1],
            }
        elif theme_id == 'dark':
            colors = {
                'chords': [0.8, 0.4, 0.9, 1],
                'tonality': [0.4, 0.9, 1.0, 1],
                'scroll': [1.0, 0.8, 0.2, 1],
                'tabs': [0.4, 0.7, 1.0, 1],
                'font': [1.0, 0.5, 0.5, 1],
                'back': [0.2, 0.8, 0.4, 1],
                'variant': [0.7, 0.4, 1.0, 1],
                'mode': [0.3, 0.9, 0.7, 1],
                'eye': [1.0, 0.6, 0.2, 1],
                'zoom': [0.4, 0.8, 1.0, 1],
            }
        else:  # green
            colors = {
                'chords': [0.61, 0.15, 0.69, 1],
                'tonality': [0.0, 0.74, 0.83, 1],
                'scroll': [1.0, 0.7, 0.0, 1],
                'tabs': [0.13, 0.59, 0.95, 1],
                'font': [0.9, 0.55, 0.0, 1],
                'back': [0.4, 0.8, 0.5, 1],
                'variant': [0.7, 0.4, 1.0, 1],
                'mode': [0.3, 0.9, 0.7, 1],
                'eye': [1.0, 0.6, 0.2, 1],
                'zoom': [0.4, 0.8, 1.0, 1],
            }
        return colors.get(action_name, [1, 1, 1, 1])


def clean_text(text):
    if not text: return ""
    temp_text = re.sub(r'<[^>]+>', '', text)
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&apos;': "'", '&nbsp;': ' ', '&#39;': "'", '&#34;': '"',
        '&#38;': '&', '&#60;': '<', '&#62;': '>', '&#171;': '«',
        '&#187;': '»', '&#169;': '©', '&#174;': '®', '&#8364;': '€',
        '&#8470;': '№', '&#8211;': '–', '&#8212;': '—', '&#8216;': "'",
        '&#8217;': "'", '&#8220;': '"', '&#8221;': '"', '&#8230;': '…',
        '&#35;': '#', '%23': '#',
    }
    for entity, char in html_entities.items():
        temp_text = temp_text.replace(entity, char)
    lines = temp_text.split('\n')
    cleaned_lines = []
    for i, line in enumerate(lines):
        if i < 4: continue
        if 'источник:' in line.lower() or 'source:' in line.lower(): continue
        cleaned_lines.append(line)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    result = '\n'.join(cleaned_lines)
    if not result.strip(): result = '\n'.join(lines[4:])
    return result


# ============================================================
# КОМПОНЕНТЫ ПАНЕЛИ
# ============================================================
class PanelIcon(ButtonBehavior, AnchorLayout):
    def __init__(self, icon, on_click=None, action_name=None, **kwargs):
        super().__init__(**kwargs)
        self.anchor_x = 'center'
        self.anchor_y = 'center'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.on_click_callback = on_click
        self.icon_name = icon
        self.action_name = action_name

        self.icon_widget = MDIcon(
            icon=icon,
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )
        self.add_widget(self.icon_widget)
        self.bind(on_release=self._on_click)

    def _on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback()

    def set_color(self, color):
        self.icon_widget.text_color = color

    def set_icon(self, icon_name):
        self.icon_name = icon_name
        self.icon_widget.icon = icon_name


class FloatingPanel(MDCard):
    PANEL_WIDTH = dp(64)
    VISIBLE_MARGIN = dp(16)
    FIXED_HEIGHT = dp(280)

    def __init__(self, parent_screen=None, on_action=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.on_action_callback = on_action

        theme_id = settings_manager.theme
        panel_bg = DetailColors.get_panel_bg(theme_id)

        self.size_hint = (None, None)
        self.width = self.PANEL_WIDTH
        self.height = self.FIXED_HEIGHT

        self.md_bg_color = [0, 0, 0, 0]
        self.radius = [0, 0, 0, 0]
        self.elevation = 0
        self.padding = [0, 0, 0, 0]

        with self.canvas.before:
            Color(0, 0, 0, 0.3)
            self.shadow_rect = RoundedRectangle(
                pos=(self.x + dp(2), self.y - dp(2)),
                size=(self.PANEL_WIDTH, self.height),
                radius=[dp(16)] * 4
            )
            self.bg_color_inst = Color(*panel_bg)
            self.bg_rect = RoundedRectangle(
                pos=(self.x, self.y),
                size=(self.PANEL_WIDTH, self.height),
                radius=[dp(16)] * 4
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        with self.canvas.after:
            self.line_color_inst = Color(*DetailColors.get_panel_line(theme_id))
            self.outline_rect = Line(
                rounded_rectangle=(self.x, self.y, self.PANEL_WIDTH, self.height, dp(16)),
                width=1.5
            )

        self._visible_x = None
        self._hidden_x = None
        self.is_open = False
        self._anim = None
        self.mode = 'menu'
        self.items = []
        self._active_slider = None

        self.content = MDBoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            width=self.PANEL_WIDTH,
            height=self.FIXED_HEIGHT,
            pos_hint={'right': 1, 'center_y': 0.5},
            spacing=0,
            padding=[0, dp(8), 0, dp(8)]
        )
        self.add_widget(self.content)

        self._build_menu()
        Clock.schedule_once(lambda dt: self._init_position(), 0.5)

    def _update_bg(self, *args):
        self.bg_rect.pos = (self.x, self.y)
        self.bg_rect.size = (self.PANEL_WIDTH, self.height)
        self.shadow_rect.pos = (self.x + dp(2), self.y - dp(2))
        self.shadow_rect.size = (self.PANEL_WIDTH, self.height)
        self.outline_rect.rounded_rectangle = (
            self.x, self.y,
            self.PANEL_WIDTH, self.height, dp(16)
        )

    def _init_position(self):
        self._hidden_x = Window.width + dp(10)
        self._visible_x = Window.width - self.PANEL_WIDTH - self.VISIBLE_MARGIN
        self.x = self._hidden_x
        self._recenter()
        self.is_open = False

    def _recenter(self):
        if self._hidden_x is None: return
        self.y = (Window.height - self.height) / 2

    def toggle(self):
        if self.is_open:
            self.hide()
        else:
            self.show()

    def show(self):
        if self.is_open: return
        self.is_open = True
        if self._anim: self._anim.cancel(self)
        self._anim = Animation(x=self._visible_x, duration=0.25, t='out_quad')
        self._anim.start(self)

    def hide(self):
        if not self.is_open: return
        self.is_open = False

        if self.parent_screen:
            if not getattr(self.parent_screen, 'eye_active', False):
                if hasattr(self.parent_screen, 'close_chords_section'):
                    self.parent_screen.close_chords_section()

        if self._anim: self._anim.cancel(self)
        self._anim = Animation(x=self._hidden_x, duration=0.25, t='in_quad')
        self._anim.start(self)

    # ============ ГЛАВНОЕ МЕНЮ ============

    def _build_menu(self):
        self.content.clear_widgets()
        self.mode = 'menu'
        self.items = []
        self._active_slider = None

        if self.parent_screen and not getattr(self.parent_screen, 'eye_active', False):
            if hasattr(self.parent_screen, 'close_chords_section'):
                self.parent_screen.close_chords_section()

        items = [
            ('music', 'chords'),
            ('tune', 'tonality'),
            ('play-circle', 'scroll'),
            ('folder-music', 'tabs'),
            ('magnify', 'font'),
        ]

        self.content.add_widget(Widget(size_hint_y=None, height=dp(12)))

        for i, (icon, action) in enumerate(items):
            item = PanelIcon(icon=icon, on_click=lambda a=action: self._on_menu_item(a), action_name=action)
            self.items.append(item)
            self.content.add_widget(item)

            if i < len(items) - 1:
                div_container = MDBoxLayout(
                    orientation='horizontal',
                    size_hint=(1, None),
                    height=dp(1),
                    padding=[dp(10), 0, dp(10), 0]
                )
                inner_separator = MDSeparator(
                    color=DetailColors.get_divider(settings_manager.theme)
                )
                div_container.add_widget(inner_separator)
                div_container._inner_line = inner_separator
                self.content.add_widget(div_container)

        self.content.add_widget(Widget(size_hint_y=None, height=dp(12)))
        self.update_theme_colors()

    # ============ ВЕРТИКАЛЬНОЕ МЕНЮ АККОРДОВ ============

    def _build_chords_panel(self):
        self.content.clear_widgets()
        self.mode = 'chords'
        self._active_slider = None

        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)

        if self.parent_screen and hasattr(self.parent_screen, 'show_chords_section'):
            self.parent_screen.show_chords_section()

        self.content.add_widget(Widget(size_hint_y=None, height=dp(12)))

        self.variant_item = PanelIcon(icon="format-list-bulleted-square",
                                      on_click=lambda: self._on_menu_item('variant'),
                                      action_name='variant')
        self.content.add_widget(self.variant_item)

        # ✅ Функция для создания разделителя (как в главном меню)
        def add_divider():
            div = MDBoxLayout(
                orientation='horizontal', size_hint=(1, None), height=dp(1),
                padding=[dp(10), 0, dp(10), 0]
            )
            inner = MDSeparator(color=DetailColors.get_divider(settings_manager.theme))
            div.add_widget(inner)
            div._inner_line = inner
            self.content.add_widget(div)

        add_divider()

        self.mode_item = PanelIcon(icon="music-note",
                                   on_click=lambda: self._on_menu_item('mode'),
                                   action_name='mode')
        self.content.add_widget(self.mode_item)
        add_divider()

        # ✅ Иконка глаза зависит от текущего состояния
        initial_icon = "eye" if getattr(self.parent_screen, 'eye_active', False) else "eye-off"
        self.eye_item = PanelIcon(icon=initial_icon,
                                  on_click=lambda: self._on_menu_item('eye'),
                                  action_name='eye')
        self.content.add_widget(self.eye_item)
        add_divider()

        self.griff_zoom_item = PanelIcon(icon="magnify",
                                         on_click=lambda: self._on_menu_item('zoom'),
                                         action_name='zoom')
        self.content.add_widget(self.griff_zoom_item)

        # ✅ ДОБАВЛЯЕМ РАЗДЕЛИТЕЛЬ ПЕРЕД ГАЛОЧКОЙ
        add_divider()

        back_btn = PanelIcon(icon="check", on_click=lambda: self._build_menu(), action_name='back')
        self.content.add_widget(back_btn)

        self.content.add_widget(Widget(size_hint_y=None, height=dp(12)))
        self.update_theme_colors()

    def _switch_chord(self, direction):
        parent = self.parent_screen
        if not parent or not hasattr(parent, '_song_chords'): return
        song_chords = parent._song_chords
        if not song_chords: return
        current = parent._current_chord_index
        new_idx = (current + direction) % len(song_chords)
        parent._current_chord_index = new_idx
        if hasattr(parent, '_update_chords_display'):
            parent._update_chords_display()
        if parent.chords_carousel and parent.chord_slides:
            if new_idx < len(parent.chord_slides):
                parent.chords_carousel.load_slide(parent.chord_slides[new_idx])

    def _on_menu_item(self, action):
        if action == 'chords':
            self._build_chords_panel()
        elif action == 'variant':
            if self.parent_screen and hasattr(self.parent_screen, '_next_chord_variant'):
                self.parent_screen._next_chord_variant()
        elif action == 'mode':
            if self.parent_screen and hasattr(self.parent_screen, '_toggle_display_mode'):
                self.parent_screen._toggle_display_mode()
                parent_mode = getattr(self.parent_screen, 'display_mode', 'finger')
                self.mode_item.set_icon("gesture-tap" if parent_mode == "notes" else "music-note")
        elif action == 'eye':
            if self.parent_screen and hasattr(self.parent_screen, '_toggle_eye'):
                self.parent_screen._toggle_eye()
                is_active = getattr(self.parent_screen, 'eye_active', False)
                # ✅ Меняем иконку, а не цвет
                self.eye_item.set_icon("eye" if is_active else "eye-off")
                if is_active and not self.parent_screen.is_chords_mode:
                    self.parent_screen.show_chords_section()
        elif action == 'zoom':
            if self.parent_screen and hasattr(self.parent_screen, '_toggle_griff_zoom'):
                self.parent_screen._toggle_griff_zoom()
                new_scale = getattr(self.parent_screen, 'griff_scale', 0.8)
                self.griff_zoom_item.set_icon("magnify" if new_scale == 0.8 else "magnify-plus")
        elif action == 'tonality':
            self._build_slider_panel('tonality')
        elif action == 'scroll':
            self._build_slider_panel('scroll')
        elif action == 'font':
            self._build_slider_panel('font')
        elif action == 'tabs':
            self._build_menu()
            if self.parent_screen: self.parent_screen.show_tabs_picker()

    # ============ ПОД-ПАНЕЛИ ============

    def _build_slider_panel(self, type_str):
        self.content.clear_widgets()
        self.mode = type_str
        self._active_slider = None

        if self.parent_screen and not getattr(self.parent_screen, 'eye_active', False):
            if hasattr(self.parent_screen, 'close_chords_section'):
                self.parent_screen.close_chords_section()

        parent = self.parent_screen
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)
        text_p = DetailColors.get_text_primary(theme_id)
        div_color = DetailColors.get_divider(theme_id)

        self.content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # ✅ Функция для создания разделителя (как в главном меню)
        def add_divider():
            div = MDBoxLayout(
                orientation='horizontal', size_hint=(1, None), height=dp(1),
                padding=[dp(10), 0, dp(10), 0]
            )
            inner = MDSeparator(color=div_color)
            div.add_widget(inner)
            div._inner_line = inner
            self.content.add_widget(div)

        # ✅ НОВЫЙ ЗАГОЛОВОК: Сверху слово "Тон", снизу значение
        header_box = MDBoxLayout(
            orientation='vertical',  # <-- Вертикальное расположение
            size_hint=(1, None),
            height=dp(52),  # <-- Чуть увеличили высоту, чтобы влезло два элемента
            spacing=0,
            padding=[0, 2, 0, 2],
            pos_hint={'center_x': 0.5}
        )

        # 1. Верхняя надпись (Тон / Шрифт / Скорость)
        if type_str == 'tonality':
            title_text = "Тон"
        elif type_str == 'font':
            title_text = "Шрифт"
        else:
            title_text = "Скорость"

        title_label = MDLabel(
            text=title_text,
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=text_p,
            bold=True,
            size_hint=(1, None),
            height=dp(20),
            font_size=sp(12)
        )
        header_box.add_widget(title_label)

        # 2. Нижнее значение (без символов)
        if type_str == 'tonality':
            current_val = getattr(parent, 'current_tonality', 0)
            current_val_str = "0" if current_val == 0 else f"{current_val:+g}"
        elif type_str == 'font':
            curr_size = getattr(parent, 'current_font_size', 20)
            current_val_str = self._get_font_multiplier(curr_size)
        else:  # scroll
            curr_speed = getattr(parent, 'scroll_speed', 1.0)
            current_val_str = f"{curr_speed:.1f}x"

        # ✅ Используем MDLabel (он подхватит глобальный шрифт и отобразит цифры)
        # Убрали font_name='NotoSansSymbols2' и символы ♪, 🔍, ▶
        self._sub_val_label = MDLabel(
            text=current_val_str,
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=accent,
            bold=True,
            size_hint=(1, None),
            height=dp(26),
            font_size=sp(18)
        )
        header_box.add_widget(self._sub_val_label)

        self.content.add_widget(header_box)

        # ✅ ИСПОЛЬЗУЕМ НОВЫЙ РАЗДЕЛИТЕЛЬ
        add_divider()

        # Слайдер
        slider_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=0,
            spacing=0
        )

        center_box = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            width=dp(48),
            pos_hint={'center_x': 0.5}
        )

        # Плюс
        center_box.add_widget(MDLabel(
            text="+", halign="center", valign="middle",
            theme_text_color="Custom", text_color=[0.3, 0.7, 0.3, 0.9],
            size_hint=(None, None), size=(dp(40), dp(20)),
            pos_hint={'center_x': 0.5},
            bold=True, font_size=sp(14)
        ))

        # Слайдер
        if type_str == 'tonality':
            current_val_int = int(round(getattr(parent, 'current_tonality', 0) * 2))
            self.ton_slider = MDSlider(
                min=-6.01, max=6.01, value=current_val_int, step=1,
                orientation='vertical', size_hint=(1, 1), hint=False
            )
            self.ton_slider.ripple_scale = 0
            self.ton_slider.thumb_color_active = accent
            self.ton_slider.thumb_color_inactive = accent
            self.ton_slider.thumb_color_disabled = accent
            self.ton_slider.track_color_active = accent[:3] + [0.5]
            self.ton_slider.track_color_inactive = [1, 1, 1, 0.3]
            self.ton_slider.color = accent
            try:
                self.ton_slider.cursor_size = (dp(20), dp(20))
            except Exception:
                pass

            def on_ton_change(instance, value):
                if value < -6:
                    int_val = -6
                elif value > 6:
                    int_val = 6
                else:
                    int_val = int(round(value))

                if self.ton_slider.value != int_val:
                    self.ton_slider.value = int_val
                val_half = int_val / 2
                # ✅ Убрали символ ♪
                self._sub_val_label.text = "0" if val_half == 0 else f"{val_half:+g}"
                if parent and val_half != getattr(parent, 'current_tonality', 0):
                    parent.current_tonality = val_half
                    if hasattr(parent, 'apply_tonality'):
                        parent.apply_tonality(val_half)

            self.ton_slider.bind(value=on_ton_change)
            center_box.add_widget(self.ton_slider)

        elif type_str == 'font':
            if platform == 'android':
                font_sizes = [30, 34, 38, 42, 46, 50, 54, 58, 60]
            else:
                font_sizes = [14, 16, 18, 20, 22, 24, 26, 28, 30, 32]
            total_steps = len(font_sizes) - 1
            curr_size = getattr(parent, 'current_font_size', font_sizes[3])
            current_val = font_sizes.index(curr_size) if curr_size in font_sizes else 3

            self.font_slider = MDSlider(
                min=-0.01, max=float(total_steps + 0.01), value=current_val, step=1,
                orientation='vertical', size_hint=(1, 1), hint=False
            )
            self.font_slider.ripple_scale = 0
            self.font_slider.thumb_color_active = accent
            self.font_slider.thumb_color_inactive = accent
            self.font_slider.thumb_color_disabled = accent
            self.font_slider.track_color_active = accent[:3] + [0.5]
            self.font_slider.track_color_inactive = [1, 1, 1, 0.3]
            self.font_slider.color = accent
            try:
                self.font_slider.cursor_size = (dp(20), dp(20))
            except Exception:
                pass

            def on_font_change(instance, value):
                int_val = max(0, min(total_steps, int(round(value))))
                if self.font_slider.value != int_val:
                    self.font_slider.value = int_val
                new_size = font_sizes[int_val]
                # ✅ Убрали символ 🔍
                self._sub_val_label.text = f"{self._get_font_multiplier(new_size)}"
                if parent and getattr(parent, 'current_font_size', 0) != new_size:
                    parent.current_font_size = new_size
                    if hasattr(parent, 'content_label'):
                        parent.content_label.font_size = new_size
                    if hasattr(parent, '_update_content_height'):
                        parent._update_content_height()

            self.font_slider.bind(value=on_font_change)
            center_box.add_widget(self.font_slider)

        elif type_str == 'scroll':
            def speed_to_slider(s):
                return int(1 + (s - 0.2) / 0.03) if s <= 0.5 else int(10 + (s - 0.5) / 0.1)

            def slider_to_speed(v):
                return 0.2 + (v - 1) * 0.03 if v <= 10 else 0.5 + (v - 10) * 0.1

            curr_speed = getattr(parent, 'scroll_speed', 1.0)
            current_val = speed_to_slider(curr_speed)

            self.scroll_slider = MDSlider(
                min=0.99, max=28.01, value=current_val, step=1,
                orientation='vertical', size_hint=(1, 1), hint=False
            )
            self.scroll_slider.ripple_scale = 0
            self.scroll_slider.thumb_color_active = accent
            self.scroll_slider.thumb_color_inactive = accent
            self.scroll_slider.thumb_color_disabled = accent
            self.scroll_slider.track_color_active = accent[:3] + [0.5]
            self.scroll_slider.track_color_inactive = [1, 1, 1, 0.3]
            self.scroll_slider.color = accent
            try:
                self.scroll_slider.cursor_size = (dp(20), dp(20))
            except Exception:
                pass

            def on_scroll_change(instance, value):
                int_val = max(1, min(28, int(round(value))))
                if self.scroll_slider.value != int_val:
                    self.scroll_slider.value = int_val
                new_speed = slider_to_speed(int_val)
                # ✅ Убрали символ ▶
                self._sub_val_label.text = f"{new_speed:.1f}x"
                if parent:
                    parent.scroll_speed = new_speed

            self.scroll_slider.bind(value=on_scroll_change)
            center_box.add_widget(self.scroll_slider)

        # Минус
        center_box.add_widget(MDLabel(
            text="-", halign="center", valign="middle",
            theme_text_color="Custom", text_color=[0.8, 0.3, 0.3, 0.9],
            size_hint=(None, None), size=(dp(40), dp(20)),
            pos_hint={'center_x': 0.5},
            bold=True, font_size=sp(14)
        ))

        slider_container.add_widget(center_box)
        self.content.add_widget(slider_container)

        # ✅ ИСПОЛЬЗУЕМ НОВЫЙ РАЗДЕЛИТЕЛЬ
        add_divider()

        # ✅ ГАЛОЧКА "НАЗАД" В ПОДМЕНЮ (теперь цветная, как в меню аккордов)
        back_btn = PanelIcon(icon="check", on_click=lambda: self._build_menu(), action_name='back')
        self.content.add_widget(back_btn)

        self.update_theme_colors()

    def _get_font_multiplier(self, font_size):
        parent = self.parent_screen
        if parent is None: return f"{int(font_size)}px"
        std = getattr(parent, 'STANDARD_FONT_SIZE', None)
        if std is None: return f"{int(font_size)}px"
        ratio = round(font_size / std * 10) / 10
        return f"{int(ratio)}x" if ratio == int(ratio) else f"{ratio:.1f}x"

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        panel_bg = DetailColors.get_panel_bg(theme_id)
        panel_line = DetailColors.get_panel_line(theme_id)

        self.bg_color_inst.rgba = panel_bg
        self.line_color_inst.rgba = panel_line

        if self.mode == 'menu':
            for item in self.items:
                color = DetailColors.get_icon_color(theme_id, item.action_name)
                item.set_color(color)
            for child in self.content.children:
                if hasattr(child, '_inner_line'): child._inner_line.color = DetailColors.get_divider(theme_id)
        elif self.mode == 'chords':
            if hasattr(self, 'variant_item'):
                self.variant_item.set_color(DetailColors.get_icon_color(theme_id, 'variant'))
                self.mode_item.set_color(DetailColors.get_icon_color(theme_id, 'mode'))
                self.griff_zoom_item.set_color(DetailColors.get_icon_color(theme_id, 'zoom'))
                # ✅ Глаз всегда использует свой цвет из палитры (не меняется на красный)
                self.eye_item.set_color(DetailColors.get_icon_color(theme_id, 'eye'))

            for child in self.content.children:
                if isinstance(child, PanelIcon):
                    color = DetailColors.get_icon_color(theme_id, getattr(child, 'action_name', ''))
                    child.set_color(color)
        elif self.mode in ['font', 'scroll', 'tonality']:
            for child in self.content.children:
                if isinstance(child, MDBoxLayout):
                    for sub in child.children:
                        if isinstance(sub, MDIconButton):
                            sub.icon_color = DetailColors.get_accent(theme_id)
                        elif isinstance(sub, MDSlider):
                            sub.thumb_color_active = DetailColors.get_accent(theme_id)
                            sub.thumb_color_inactive = DetailColors.get_accent(theme_id)
                            sub.thumb_color_disabled = DetailColors.get_accent(theme_id)
                            sub.track_color_active = DetailColors.get_accent(theme_id)[:3] + [0.6]
                            sub.color = DetailColors.get_accent(theme_id)
                        elif isinstance(sub, PanelIcon):
                            color = DetailColors.get_icon_color(theme_id, getattr(sub, 'action_name', ''))
                            sub.set_color(color)


# ============================================================
# ОСНОВНОЙ ЭКРАН
# ============================================================
class FavoriteDetailScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorite_detail'
        self._manage_padding_manually = True

        self.song_id = None
        self.song_title = None
        self.song_artist = None
        self.is_favorite = True
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self.previous_screen = 'favorites'
        self.current_tonality = 0
        self.tabs = []
        self.current_tab_index = 0

        self.STANDARD_FONT_SIZE = 42 if platform == 'android' else 20
        self.current_font_size = self.STANDARD_FONT_SIZE

        self._song_chords = []
        self._current_chord_index = 0
        self.chord_renderers = []
        self.chord_slides = []
        self.chords_carousel = None
        self.display_mode = "finger"
        self.chord_variants = []
        self.chord_variant_index = 0
        self.is_chords_mode = False
        self.griff_scale = 0.8
        self.griff_container = None
        self._griff_added = False
        self.griff_divider = None
        self.eye_active = False
        self.eye_btn = None
        self.chord_name_section = None
        self.chord_name_label = None

        self.transposed_chords_cache = {}
        self.transposed_text_cache = {}
        self.original_cleaned_text = ""

        self.is_tonality_mode = False
        self.is_font_mode = False
        self.is_scroll_mode = False
        self.scroll_speed = 1.0
        self.scroll_animation = None
        self.is_scrolling = False

        self._floating_panel = None

        self.load_background()
        self.init_ui()
        logger.info('Экран просмотра избранной песни создан')

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
        if not hasattr(self, 'bg_color_inst') or not hasattr(self, 'bg_rect'): return
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
        text_p = DetailColors.get_text_primary(theme_id)
        div_color = DetailColors.get_divider(theme_id)

        if hasattr(self, 'content_label'): self.content_label.text_color = text_p
        for div in (getattr(self, 'top_divider', None), getattr(self, 'panel_divider', None),
                    getattr(self, 'bottom_divider', None)):
            if div: div.md_bg_color = div_color
        if getattr(self, 'griff_divider', None): self.griff_divider.md_bg_color = div_color
        if self.chord_name_label: self.chord_name_label.text_color = text_p
        if self._floating_panel: self._floating_panel.update_theme_colors()

    def init_ui(self):
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
        top_offset = layout_config.get_top_padding(include_top_nav=True)
        bottom_nav_total = layout_config.get_bottom_nav_total_height()

        # ✅ Возвращаем правильный отступ сверху
        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, top_offset, 0, 0]
        )

        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, bottom_nav_total],
            spacing=0,
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0
        )

        self.content_scroll = MDScrollView(size_hint=(1, 1), do_scroll_x=False, bar_width=3,
                                           bar_color=[0.5, 0.5, 0.5, 0.3], bar_inactive_color=[0.5, 0.5, 0.5, 0.1])

        # ✅ УМЕНЬШАЕМ ОТСТУП ВНУТРИ ТЕКСТА
        self._text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=4,
            padding=[dp(16), dp(4), dp(16), dp(4)],  # Верхний отступ dp(4)
            adaptive_height=True,
            md_bg_color=[0, 0, 0, 0]
        )

        # ✅ ИСПОЛЬЗУЕМ НАШ ШРИФТ ДЛЯ ТЕКСТА ПЕСНИ
        self.content_label = ChordTextLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            valign="top",
            line_height=1.5,
            markup=True,
            font_name='NotoSansSymbols2'  # <-- Добавляем шрифт для нот и символов
        )
        self.content_label.bind(texture_size=self._update_content_height)
        self._text_container.add_widget(self.content_label)

        self.content_scroll.add_widget(self._text_container)
        self.song_card.add_widget(self.content_scroll)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)
        self.add_widget(main_container)

        self._floating_panel = FloatingPanel(parent_screen=self)
        self.add_widget(self._floating_panel)

        Clock.schedule_once(lambda dt: self.update_theme_colors(), 0.2)
        Clock.schedule_once(lambda dt: self._floating_panel._init_position(), 0.5)

    def _update_content_height(self, *args):
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return

        text_height = self.content_label.texture_size[1]

        self.content_label.height = max(dp(50), text_height + dp(8))
        if self.content_label.parent:
            self.content_label.parent.height = text_height + dp(16)
        self.content_scroll.scroll_y = 1.0

    def toggle_settings_panel(self):
        if self._floating_panel:
            self._floating_panel.toggle()

    def show_chords_section(self):
        if not self._song_chords:
            notify.info(get_text('no_chords'))
            return
        if self.is_chords_mode:
            return
        self.is_chords_mode = True
        self._show_chords_layer()

    def _show_chords_layer(self):
        if self._griff_added: return
        from kivy.uix.carousel import Carousel
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)

        # Базовая высота контейнера (для стрелок и грифа)
        base_height = 135 * self.griff_scale

        # ✅ Рассчитываем ширину грифа в зависимости от масштаба
        griff_width = dp(340) * self.griff_scale

        # Ограничиваем ширину, чтобы не вылезти за экран
        max_griff_width = Window.width - dp(80)
        if griff_width > max_griff_width:
            griff_width = max_griff_width

        self.griff_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            width=griff_width + dp(60),
            height=dp(base_height),
            pos_hint={'center_x': 0.5},
            padding=[0, 0, 0, 0],
            spacing=dp(0)
        )

        # Цвет стрелок (белый с прозрачностью для всех тем)
        arrow_color = [1, 1, 1, 0.6]

        self.left_arrow = MDIcon(
            icon="chevron-left",
            size_hint=(None, 1),
            width=dp(30),
            pos_hint={'center_y': 0.5},
            theme_text_color="Custom",
            text_color=arrow_color,
            font_size=sp(36)
        )
        self.griff_container.add_widget(self.left_arrow)

        self.chords_carousel = Carousel(
            direction='right',
            loop=True,
            size_hint=(None, 1),
            width=griff_width,
            anim_move_duration=0.3
        )
        self.chords_carousel.bind(current_slide=self._on_carousel_slide)
        self.chord_renderers = []
        self.chord_slides = []

        for i, chord_name in enumerate(self._song_chords):
            slide = MDBoxLayout(
                orientation='vertical',
                size_hint=(1, 1),
                padding=[0, 0, 0, 0]
            )

            renderer = ChordRenderer(size_hint=(1, 1))
            renderer.chord_name = chord_name
            renderer.index = i
            renderer.set_fret_color("black" if theme_id == "light" else "white")
            try:
                griff_data = load_asset_as_bytes("griff_png")
                if griff_data:
                    griff_img = CoreImage(BytesIO(griff_data), ext="png")
                    if griff_img and griff_img.texture: renderer.set_background(griff_img.texture)
            except Exception:
                pass

            slide.add_widget(renderer)
            self.chords_carousel.add_widget(slide)
            self.chord_renderers.append(renderer)
            self.chord_slides.append(slide)

        self.griff_container.add_widget(self.chords_carousel)

        self.right_arrow = MDIcon(
            icon="chevron-right",
            size_hint=(None, 1),
            width=dp(30),
            pos_hint={'center_y': 0.5},
            theme_text_color="Custom",
            text_color=arrow_color,
            font_size=sp(36)
        )
        self.griff_container.add_widget(self.right_arrow)

        self.chord_name_section = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(24),
            padding=[0, 0, 0, 0],
            spacing=0
        )
        self.chord_name_label = MDLabel(
            text="",
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=text_p,
            bold=True,
            font_size=sp(18)
        )
        self.chord_name_section.add_widget(self.chord_name_label)

        content_scroll = self.content_scroll
        if content_scroll in self.song_card.children: self.song_card.remove_widget(content_scroll)

        self.song_card.add_widget(self.chord_name_section)
        self.song_card.add_widget(self.griff_container)
        self.song_card.add_widget(content_scroll)

        self._griff_added = True

        self._current_chord_index = 0
        if self._song_chords:
            self._load_chord_variants(self._song_chords[0])
            self._update_chords_display()

            if self.chords_carousel and self.chord_slides:
                self.chords_carousel.load_slide(self.chord_slides[0])

    def _on_carousel_slide(self, instance, slide):
        if not self.chord_slides: return
        try:
            index = self.chord_slides.index(slide)
            if index != self._current_chord_index:
                self._current_chord_index = index
                self._update_chords_display()
        except ValueError:
            pass

    def _hide_chords_layer(self):
        if not self._griff_added: return
        content_scroll = self.content_scroll
        for w in (self.chord_name_section, self.griff_container):
            if w and w in self.song_card.children: self.song_card.remove_widget(w)
        self.chord_name_section = None
        self.griff_container = None
        self.chord_name_label = None
        if content_scroll not in self.song_card.children: self.song_card.add_widget(content_scroll)
        self.chords_carousel = None
        self.chord_renderers = []
        self.chord_slides = []
        self._griff_added = False

    def close_chords_section(self, *args):
        self.is_chords_mode = False
        self._hide_chords_layer()

    def _load_chord_variants(self, chord_name):
        self.chord_variants = []
        self.chord_variant_index = 0

        if isinstance(chord_name, (list, tuple)) and chord_name:
            chord_name = chord_name[0]

        if not isinstance(chord_name, str):
            return

        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')
            variants = [c for c in chords_screen.all_chords if c['short_name'].lower() == chord_name.lower()]
            variants.sort(key=lambda x: x['variant'])
            self.chord_variants = variants
            if variants:
                self.load_current_variant()

    def load_current_variant(self):
        if not self.chord_variants: return
        variant = self.chord_variants[self.chord_variant_index]
        chord_module = variant.get('module') or variant.get('module_1')
        if chord_module and self._current_chord_index < len(self.chord_renderers):
            renderer = self.chord_renderers[self._current_chord_index]
            renderer.load_chord(chord_module)
            renderer.set_mode(self.display_mode)

    def _next_chord_variant(self):
        if not self.chord_variants: return
        self.chord_variant_index = (self.chord_variant_index + 1) % len(self.chord_variants)
        self.load_current_variant()

    def _toggle_display_mode(self):
        self.display_mode = "notes" if self.display_mode == "finger" else "finger"
        if self._current_chord_index < len(self.chord_renderers):
            self.chord_renderers[self._current_chord_index].set_mode(self.display_mode)

    def _toggle_eye(self):
        self.eye_active = not self.eye_active
        if not self.eye_active and self.is_chords_mode:
            self.close_chords_section()

    def _toggle_griff_zoom(self):
        if not self.griff_container: return
        zoom_levels = [0.8, 1.0, 1.2, 1.4]
        current = self.griff_scale
        new_scale = zoom_levels[(zoom_levels.index(current) + 1) % len(zoom_levels)] if current in zoom_levels else 0.8
        self.griff_scale = new_scale

        # Пересчитываем высоту
        self.griff_container.height = int(dp(135) * new_scale)

        # ✅ Пересчитываем ширину контейнера и карусели
        griff_width = dp(340) * new_scale
        max_griff_width = Window.width - dp(80)
        if griff_width > max_griff_width:
            griff_width = max_griff_width

        self.griff_container.width = griff_width + dp(60)
        if hasattr(self, 'chords_carousel') and self.chords_carousel:
            self.chords_carousel.width = griff_width

    def _update_chords_display(self):
        if not self._song_chords: return
        chord_name = self._song_chords[self._current_chord_index]
        if self.chord_name_label: self.chord_name_label.text = chord_name
        self._load_chord_variants(chord_name)

    def _extract_and_cache_chords(self):
        chords = set()
        for tab in self.tabs:
            content = tab.get('content', '')
            if content: chords.update(extract_chords_from_text(clean_text(content)))
        self._song_chords = sorted(list(chords))

    def apply_tonality(self, step):
        if isinstance(self.transposed_text_cache, dict):
            transposed = self.transposed_text_cache.get(step)
            if transposed:
                self.content_label.text = transposed
                self.content_label.markup = True

                if isinstance(self.transposed_chords_cache, dict):
                    self._song_chords = self.transposed_chords_cache.get(step, [])

                if self.is_chords_mode and self.chord_name_label and self._song_chords:
                    if self._current_chord_index >= len(self._song_chords):
                        self._current_chord_index = 0
                    self._update_chords_display()

    def precompute_transpositions(self, cleaned_text):
        self.original_cleaned_text = cleaned_text
        self.transposed_text_cache = {}
        self.transposed_text_cache[0] = highlight_chords_in_text(cleaned_text)
        self.transposed_chords_cache = {}
        self.transposed_chords_cache[0] = self._song_chords.copy()

        for step in [-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3]:
            self.transposed_text_cache[step] = transpose_text(cleaned_text, step)
            self.transposed_chords_cache[step] = transpose_chord_list(self._song_chords, step)

    def _get_font_multiplier(self, font_size):
        ratio = round(font_size / self.STANDARD_FONT_SIZE * 10) / 10
        return f"{int(ratio)}x" if ratio == int(ratio) else f"{ratio:.1f}x"

    def reset_font_size(self):
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'content_label'):
            self.content_label.font_size = self.current_font_size
            self._update_content_height()

    def toggle_scroll(self):
        if not self.is_scrolling and self.content_scroll.scroll_y <= 0.01: self.reset_scroll_position()
        if not self.is_scrolling:
            self.start_scroll()
        else:
            self.stop_scroll()

    def start_scroll(self):
        if self.is_scrolling: return
        self.is_scrolling = True

        def update_scroll(dt):
            if not self.is_scrolling: return False
            new_y = self.content_scroll.scroll_y - 0.0004 * self.scroll_speed
            if new_y <= 0:
                self.content_scroll.scroll_y = 0
                self.stop_scroll()
                return False
            self.content_scroll.scroll_y = new_y
            return True

        self.scroll_animation = Clock.schedule_interval(update_scroll, 1.0 / 60.0)

    def stop_scroll(self):
        if self.scroll_animation:
            self.scroll_animation.cancel()
            self.scroll_animation = None
        self.is_scrolling = False

    def reset_scroll_position(self):
        if self.is_scrolling: self.stop_scroll()
        self.content_scroll.scroll_y = 1.0

    def show_tabs_picker(self):
        if not self.tabs or len(self.tabs) <= 1:
            notify.info(get_text('no_variants'))
            return
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)

        content = MDBoxLayout(orientation='vertical', spacing=dp(8), padding=dp(16), size_hint_y=None,
                              adaptive_height=True)
        for i in range(len(self.tabs)):
            btn = MDRaisedButton(
                text=f"{get_text('variant')} {i + 1}",
                size_hint=(1, None), height=dp(48),
                md_bg_color=accent if i == self.current_tab_index else [0.2, 0.2, 0.2, 0.8],
                text_color=[1, 1, 1, 1],
                on_release=lambda x, idx=i: self._select_tab(idx))
            content.add_widget(btn)
        dialog = MDDialog(title=get_text('choose_chord'), type="custom", content_cls=content,
                          buttons=[MDRaisedButton(text=get_text('close'), on_release=lambda x: dialog.dismiss())])
        dialog.open()
        self.tabs_dialog = dialog

    def _select_tab(self, index):
        if hasattr(self, 'tabs_dialog'): self.tabs_dialog.dismiss()
        self.current_tab_index = index
        self._load_current_tab()

    def _load_current_tab(self):
        if self.tabs and self.current_tab_index < len(self.tabs):
            cleaned = clean_text(self.tabs[self.current_tab_index].get('content', ''))
            if cleaned:
                self.current_tonality = 0
                self.transposed_text_cache = {}
                self.transposed_chords_cache = {}
                self._extract_and_cache_chords()
                self.precompute_transpositions(cleaned)
                self.content_label.text = self.transposed_text_cache.get(0, cleaned)
                self.content_label.markup = True
            else:
                self.content_label.text = get_text('loading_error')
                self.content_label.markup = False
            self._update_content_height()
            Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)

    def set_song(self, song_id, artist="", title=""):
        self.song_id = song_id
        self.song_artist = artist
        self.song_title = title
        self.is_favorite = True
        self.reset_screen_state()
        self.load_song_data()

    def reset_screen_state(self):
        self.current_tonality = 0
        self.transposed_chords_cache = {}
        self.transposed_text_cache = {}
        self.original_cleaned_text = ""
        if self.is_chords_mode: self.close_chords_section()
        self.eye_active = False
        self._current_chord_index = 0
        self.reset_font_size()
        self.display_mode = "finger"
        self.chord_variants = []
        self.chord_variant_index = 0
        self.scroll_speed = 1.0
        self.is_scrolling = False
        self.griff_scale = 0.8
        if self._floating_panel:
            self._floating_panel.hide()

    def load_song_data(self):
        self.show_loading()
        api.get_tab(song_id=self.song_id, on_success=self.on_song_loaded, on_failure=self.on_load_failed,
                    force_refresh=False)

    def show_loading(self):
        if self.is_loading: return
        self.is_loading = True
        self.loading_spinner = MDBoxLayout()
        self.add_widget(self.loading_spinner)

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            self.remove_widget(self.loading_spinner)
            self.loading_spinner = None

    def on_song_loaded(self, data):
        self.song_artist = data.get('artist') or self.song_artist or get_text('unknown_artist')
        self.song_title = data.get('title') or self.song_title or get_text('untitled')
        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'): self.tabs = [{'content': data.get('content', '')}]
        self.current_tab_index = 0

        if self.tabs:
            cleaned = clean_text(self.tabs[0].get('content', ''))
            self._extract_and_cache_chords()
            self.precompute_transpositions(cleaned)
            self.content_label.text = self.transposed_text_cache.get(0, cleaned)
            self.content_label.markup = True
            self._update_content_height()

        self.is_favorite = api.is_song_favorited(self.song_id)
        if not self.is_favorite: self.is_favorite = data.get('is_favorite', True)
        self.update_top_nav_title()
        self.hide_loading()
        for delay in [0.3, 0.5, 0.8, 1.0]: Clock.schedule_once(self._wait_for_ready_and_scroll, delay)

    def _wait_for_ready_and_scroll(self, dt):
        if hasattr(self, 'content_label') and self.content_label.text:
            if self.content_label.texture and self.content_label.texture_size[1] > 0:
                self.content_scroll.scroll_y = 1.0
                return
        Clock.schedule_once(self._wait_for_ready_and_scroll, 0.15)

    def on_load_failed(self, req, error):
        self.hide_loading()
        self.content_label.text = get_text('loading_error')
        notify.error(get_text('loading_error'))

    def toggle_favorite(self, *args):
        if not api.is_authenticated():
            app = MDApp.get_running_app()
            if app and hasattr(app, 'open_profile'): app.open_profile()
            return

        def confirm(instance):
            dialog.dismiss()
            self._remove_from_favorites()

        dialog = MDDialog(
            title=get_text('remove_from_favorites'),
            text=f"{self.song_title}",
            buttons=[
                MDRaisedButton(text=get_text('close'), on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text=get_text('reset'), on_release=confirm, md_bg_color=[0.8, 0.3, 0.3, 1]),
            ])
        dialog.open()

    def _remove_from_favorites(self):
        def on_success(result):
            self.is_favorite = False
            notify.success(get_text('no_favorites'))
            Clock.schedule_once(lambda dt: self.go_back(), 0.3)

        def on_failure(req, error):
            self.is_favorite = True
            notify.error(get_text('search_error'))

        api.remove_from_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def update_top_nav_title(self):
        app = MDApp.get_running_app()
        if not app or not hasattr(app, 'top_nav'): return
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)
        text_s = DetailColors.get_text_secondary(theme_id)

        container = MDBoxLayout(orientation='vertical', size_hint=(1, 1), spacing=dp(2),
                                padding=[dp(8), dp(4), dp(8), dp(4)])
        title = MDLabel(text=self.song_title or get_text('artist_songs'), font_size=sp(18), halign="center",
                        valign="middle", theme_text_color="Custom", text_color=text_p, bold=True, shorten=True,
                        shorten_from="right")
        artist = MDLabel(text=self.song_artist or "", font_size=sp(12), halign="center", valign="middle",
                         theme_text_color="Custom", text_color=text_s, shorten=True, shorten_from="right")
        container.add_widget(title)
        container.add_widget(artist)
        app.top_nav.set_custom_title_widget(container)

    def go_back(self, instance=None):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            app.top_nav.force_update_title(get_text('favorites'), show_back=False)
            if hasattr(app.top_nav, '_update_right_buttons'): app.top_nav._update_right_buttons('favorites')
        if self.manager and self.manager.has_screen('favorites'):
            self.manager.current = 'favorites'
        else:
            self.manager.current = 'home'

    def on_enter(self):
        super().on_enter()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if hasattr(app.top_nav, 'left_container'):
                app.top_nav.left_container.clear_widgets()
                app.top_nav.left_container.add_widget(app.top_nav.back_btn)
                app.top_nav.back_btn.on_release = self.go_back
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('favorite_detail')
        if self.song_title: self.update_top_nav_title()
        self.update_theme_colors()
        if self._floating_panel:
            def _init_panel(dt):
                self._floating_panel._init_position()
                self._floating_panel.hide()
                self._floating_panel._build_menu()

            Clock.schedule_once(_init_panel, 0.1)

    def on_leave(self):
        logger.info("Выход из FavoriteDetailScreen")