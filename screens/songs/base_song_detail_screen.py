# screens/songs/base_song_detail_screen.py
"""
Базовый эталонный экран просмотра песни с аккордами.
Используется для наследования в:
  - FavoriteDetailScreen (screens/favorite/favorite_detail_screen.py)
  - SongDetailScreen (screens/songs/song_detail_screen.py)
  - SearchScreenDetail (screens/search/find_song_detail_screen.py)
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard, MDSeparator
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from songs_utils.fader_widget import SongsPanelFader
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image as KivyImage
from kivy.utils import platform
from io import BytesIO
import re
from config.navigation_config import navigate_back
from chord_utils.chord_parser import is_chord_line
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from chord_utils.renderer import ChordRenderer
from api.client import api
from api.chords_client import get_chords_client
from utils.notifications import notify
from state.base import BaseStateManager
from state.settings_state import settings_state as settings_manager
from utils.localization import get_text
from chord_utils.chord_highlighter import (
    ChordTextLabel,
    highlight_chords_in_text,
    extract_chords_from_text_wrapper as extract_chords_from_text,
)
from chord_utils.transposer import transpose_text
from screens.components.loading_spinner import LoadingSpinner


logger = screen_logger('BaseSongDetail')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None

ASSET_CHORDS_2_PNG = "chords_2_png"
ASSET_LOUPE_PNG = "loupe_png"
ASSET_OK_PNG = "ok_png"
_PANEL_ASSET_TEXTURES = {}


def preload_panel_textures():
    """Предзагружает текстуры иконок меню один раз при старте приложения."""
    if not HAS_ASSETS:
        return
    for asset_name in (ASSET_CHORDS_2_PNG, ASSET_LOUPE_PNG, ASSET_OK_PNG):
        if asset_name not in _PANEL_ASSET_TEXTURES:
            try:
                img_bytes = load_asset_as_bytes(asset_name)
                if img_bytes:
                    _PANEL_ASSET_TEXTURES[asset_name] = CoreImage(BytesIO(img_bytes), ext="png").texture
            except Exception as e:
                logger.error(f"Ошибка предзагрузки ассета {asset_name}: {e}")


# ============================================================
# БАЗОВЫЙ МЕНЕДЖЕР СОСТОЯНИЯ ДЛЯ ЭКРАНОВ ПЕСНИ
# ============================================================
class BaseSongDetailStateManager(BaseStateManager):
    """Кэш предвычисленных транспонирований, вкладок и скролла по song_id (LRU + TTL)."""

    def __init__(self, name: str, default_ttl: int = 600, max_cached_songs: int = 10):
        super().__init__(name=name, default_ttl=default_ttl)
        self._current_song_id = None
        self._max_cached_songs = max_cached_songs
        self._lru_order = []

    def _touch_lru(self, key: str):
        if key in self._lru_order:
            self._lru_order.remove(key)
        self._lru_order.append(key)
        while len(self._lru_order) > self._max_cached_songs:
            oldest = self._lru_order.pop(0)
            self.invalidate(oldest)

    def save_song_state(self, song_id: int, state_data: dict):
        if not song_id:
            return
        key = str(song_id)
        self._current_song_id = song_id
        self.save(key, state_data, ttl=self._ttl)
        self._touch_lru(key)

    def get_song_state(self, song_id: int) -> dict | None:
        if not song_id:
            return None
        key = str(song_id)
        data = self.get(key, allow_stale=False)
        if data is not None:
            self._touch_lru(key)
        return data

    def reset_song(self, song_id: int = None):
        if song_id is None:
            self.clear()
            self._lru_order.clear()
            self._current_song_id = None
        else:
            key = str(song_id)
            self.invalidate(key)
            if key in self._lru_order:
                self._lru_order.remove(key)


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
            return [0.95, 0.95, 0.95, 1]
        elif theme_id == 'dark':
            return [0.13, 0.13, 0.13, 1]
        else:
            return [0.05, 0.17, 0.11, 1]

    @staticmethod
    def get_panel_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        else:
            return [0.46, 0.70, 0.71, 0.4]

    @staticmethod
    def get_divider(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.6]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.6]
        else:
            return [0.46, 0.70, 0.71, 0.55]

    @staticmethod
    def get_icon_color(theme_id, action_name):
        colors = {
            'chords': [1.0, 0.7, 0.0, 1],
            'tonality': [0.61, 0.15, 0.69, 1],
            'scroll': [1.0, 0.55, 0.0, 1],
            'tabs': [0.0, 0.74, 0.83, 1],
            'tabs_disabled': [0.55, 0.55, 0.55, 0.7] if theme_id == 'light' else [1, 1, 1, 0.35],
            'font': [0.95, 0.45, 0.25, 1],

            'variant': [0.13, 0.59, 0.95, 1],
            'mode': [0.9, 0.55, 0.0, 1],
            'mode_notes': [0.8, 0.3, 0.3, 1],
            'eye': [0.25, 0.78, 0.55, 1],
            'eye_off': [0.55, 0.55, 0.55, 0.7] if theme_id == 'light' else [1, 1, 1, 0.35],
            'zoom': [0.95, 0.45, 0.25, 1],

            'play': [0.13, 0.59, 0.95, 1],
            'stop': [0.8, 0.3, 0.3, 1],
            'back': [0.25, 0.78, 0.55, 1],
        }
        return colors.get(action_name, [1, 1, 1, 1])


def clean_text(text):
    if not text:
        return ""

    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\xa0', ' ').replace('\u200b', '').replace('\ufeff', '')

    processed_tabs = []
    for raw_line in text.split('\n'):
        if '\t' in raw_line:
            line_with_single_spaces = re.sub(r'[ \t]+', ' ', raw_line).strip()
            if is_chord_line(line_with_single_spaces):
                processed_tabs.append(raw_line.replace('\t', '  ').rstrip())
            else:
                processed_tabs.append(line_with_single_spaces)
        else:
            processed_tabs.append(raw_line)
    text = '\n'.join(processed_tabs)

    temp_text = re.sub(r'<[^>]+>', '', text)
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&apos;': "'", '&nbsp;': ' ', '&#39;': "'", '&#34;': '"',
        '&#38;': '&', '&#60;': '<', '&#62;': '>', '&laquo;': '«',
        '&raquo;': '»', '&copy;': '©', '&reg;': '®', '&euro;': '€',
        '&#8470;': '№', '&ndash;': '–', '&mdash;': '—', '&lsquo;': "'",
        '&rsquo;': "'", '&ldquo;': '"', '&rdquo;': '"', '&hellip;': '…',
        '&#35;': '#', '%23': '#',
    }
    for entity, char in html_entities.items():
        temp_text = temp_text.replace(entity, char)

    lines = temp_text.split('\n')
    cleaned_lines = []
    for i, line in enumerate(lines):
        if i < 4:
            continue
        if 'источник:' in line.lower() or 'source:' in line.lower():
            continue
        cleaned_lines.append(line)

    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    result = '\n'.join(cleaned_lines)
    if not result.strip():
        result = '\n'.join(lines[4:])
    return result


# ============================================================
# КОМПОНЕНТЫ ПАНЕЛИ
# ============================================================
class PanelIcon(AnchorLayout):
    def __init__(self, icon, on_click=None, action_name=None, asset_name=None, **kwargs):
        kwargs.setdefault('size_hint', (1, 1))
        super().__init__(**kwargs)
        self.anchor_x = 'center'
        self.anchor_y = 'center'
        self.on_click_callback = on_click
        self.icon_name = icon
        self.action_name = action_name
        self.asset_name = asset_name
        self.is_image = False
        self._touch_down_pos = None

        texture = None
        if asset_name:
            if asset_name not in _PANEL_ASSET_TEXTURES:
                preload_panel_textures()
            texture = _PANEL_ASSET_TEXTURES.get(asset_name)

        if texture is not None:
            self.is_image = True
            self.icon_widget = KivyImage(
                texture=texture,
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                color=[1, 1, 1, 1],
                allow_stretch=True,
                keep_ratio=True
            )
        else:
            self.icon_widget = MDIcon(
                icon=icon,
                size_hint=(None, None),
                size=(dp(26), dp(26)),
                font_size=sp(26),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1]
            )
        self.add_widget(self.icon_widget)

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return False
        self._touch_down_pos = touch.pos
        touch.grab(self)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        start_pos = self._touch_down_pos
        self._touch_down_pos = None
        if start_pos and self.collide_point(*touch.pos):
            if abs(touch.x - start_pos[0]) < dp(12) and abs(touch.y - start_pos[1]) < dp(12):
                if self.on_click_callback:
                    self.on_click_callback()
        return True

    def set_color(self, color):
        if self.is_image:
            self.icon_widget.color = [1, 1, 1, 1]
        else:
            self.icon_widget.text_color = color

    def set_icon(self, icon_name):
        self.icon_name = icon_name
        if not self.is_image:
            self.icon_widget.icon = icon_name


class FloatingPanel(MDCard):
    PANEL_WIDTH = dp(55)
    VISIBLE_MARGIN = 0
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
            self.bg_color_inst = Color(*panel_bg)
            self.bg_rect = RoundedRectangle(
                pos=(self.x, self.y),
                size=(self.PANEL_WIDTH, self.height),
                radius=[dp(16), 0, 0, dp(16)]
            )

        with self.canvas.after:
            self.line_color_inst = Color(*DetailColors.get_panel_line(theme_id))
            self.outline_line = Line(points=[], width=1.5, cap='round', joint='round')

        self.bind(pos=self._update_bg, size=self._update_bg)

        self._visible_x = None
        self._hidden_x = None
        self.is_open = False
        self._anim = None
        self.mode = 'menu'
        self._mode_views = {}
        self._mode_items = {m: [] for m in ('menu', 'chords', 'tonality', 'scroll', 'font')}
        self._mode_dividers = {m: [] for m in ('menu', 'chords', 'tonality', 'scroll', 'font')}
        self._slider_labels = {}

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

        self._build_all_modes()
        self._switch_mode('menu')
        Clock.schedule_once(lambda dt: self._init_position(), 0.5)

    def _build_open_border_points(self):
        import math
        x, y = self.x, self.y
        w, h = self.PANEL_WIDTH, self.height
        r = min(dp(16), w / 2, h / 2)
        segments = 12

        pts = [x + w, y + h, x + r, y + h]
        cx_tl, cy_tl = x + r, y + h - r
        for i in range(1, segments + 1):
            angle = math.pi / 2 + (math.pi / 2) * (i / segments)
            pts.extend([cx_tl + r * math.cos(angle), cy_tl + r * math.sin(angle)])

        pts.extend([x, y + r])
        cx_bl, cy_bl = x + r, y + r
        for i in range(1, segments + 1):
            angle = math.pi + (math.pi / 2) * (i / segments)
            pts.extend([cx_bl + r * math.cos(angle), cy_bl + r * math.sin(angle)])

        pts.extend([x + w, y])
        return pts

    def _update_bg(self, *args):
        self.bg_rect.pos = (self.x, self.y)
        self.bg_rect.size = (self.PANEL_WIDTH, self.height)
        self.outline_line.points = self._build_open_border_points()

    def _init_position(self):
        self._hidden_x = Window.width + dp(4)
        self._visible_x = Window.width - self.PANEL_WIDTH - self.VISIBLE_MARGIN
        self.x = self._hidden_x
        self._recenter()
        self.is_open = False

    def _recenter(self):
        if self._hidden_x is None:
            return
        top_offset = layout_config.get_top_padding(include_top_nav=True)
        nav_bottom = layout_config.get_bottom_nav_total_height()
        work_area_height = Window.height - top_offset - nav_bottom
        self.y = nav_bottom + (work_area_height - self.height) / 2

    def toggle(self):
        if self.is_open:
            self.hide()
        else:
            self.show()

    def show(self):
        if self.is_open:
            return
        self.is_open = True
        if self._anim:
            self._anim.cancel(self)
        self._anim = Animation(x=self._visible_x, duration=0.25, t='out_quad')
        self._anim.start(self)

    def hide(self):
        if not self.is_open:
            return
        self.is_open = False
        if self.parent_screen and not getattr(self.parent_screen, 'eye_active', False):
            if hasattr(self.parent_screen, 'close_chords_section'):
                self.parent_screen.close_chords_section()
        if self._anim:
            self._anim.cancel(self)
        self._anim = Animation(x=self._hidden_x, duration=0.25, t='in_quad')
        self._anim.start(self)

    def _add_divider_to(self, container, mode_key):
        div = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(1.2),
            padding=[dp(8), 0, dp(8), 0]
        )
        inner = MDSeparator(color=DetailColors.get_divider(settings_manager.theme))
        div.add_widget(inner)
        self._mode_dividers[mode_key].append(inner)
        container.add_widget(div)

    def _build_all_modes(self):
        for m in ('menu', 'chords', 'tonality', 'scroll', 'font'):
            self._mode_views[m] = MDBoxLayout(
                orientation='vertical',
                size_hint=(1, 1),
                spacing=0,
                padding=0
            )
        self._populate_menu(self._mode_views['menu'])
        self._populate_chords_panel(self._mode_views['chords'])
        self._populate_slider_panel(self._mode_views['tonality'], 'tonality')
        self._populate_slider_panel(self._mode_views['scroll'], 'scroll')
        self._populate_slider_panel(self._mode_views['font'], 'font')

    def _switch_mode(self, mode_name):
        self.mode = mode_name
        self.content.clear_widgets()
        view = self._mode_views.get(mode_name)
        if view:
            self.content.add_widget(view)

        if mode_name == 'chords':
            if self.parent_screen and hasattr(self.parent_screen, 'show_chords_section'):
                self.parent_screen.show_chords_section()
        else:
            if self.parent_screen and not getattr(self.parent_screen, 'eye_active', False):
                if hasattr(self.parent_screen, 'close_chords_section'):
                    self.parent_screen.close_chords_section()

        self._sync_mode_values(mode_name)
        self.update_theme_colors()

    def _build_menu(self):
        self._switch_mode('menu')

    def _build_chords_panel(self):
        self._switch_mode('chords')

    def _build_slider_panel(self, type_str):
        self._switch_mode(type_str)

    def _populate_menu(self, container):
        items = [
            ('music', 'chords', ASSET_CHORDS_2_PNG),
            ('music-note', 'tonality', None),
            ('play-circle', 'scroll', None),
            ('folder-music', 'tabs', None),
            ('magnify', 'font', ASSET_LOUPE_PNG),
        ]
        for i, (icon, action, asset) in enumerate(items):
            item = PanelIcon(
                icon=icon,
                on_click=lambda a=action: self._on_menu_item(a),
                action_name=action,
                asset_name=asset
            )
            self._mode_items['menu'].append(item)
            container.add_widget(item)
            if i < len(items) - 1:
                self._add_divider_to(container, 'menu')

    def _populate_chords_panel(self, container):
        self.variant_item = PanelIcon(
            icon="format-list-bulleted-square",
            on_click=lambda: self._on_menu_item('variant'),
            action_name='variant'
        )
        self._mode_items['chords'].append(self.variant_item)
        container.add_widget(self.variant_item)
        self._add_divider_to(container, 'chords')

        self.mode_item = PanelIcon(
            icon="gesture-tap",
            on_click=lambda: self._on_menu_item('mode'),
            action_name='mode'
        )
        self._mode_items['chords'].append(self.mode_item)
        container.add_widget(self.mode_item)
        self._add_divider_to(container, 'chords')

        self.eye_item = PanelIcon(
            icon="eye-off",
            on_click=lambda: self._on_menu_item('eye'),
            action_name='eye_off'
        )
        self._mode_items['chords'].append(self.eye_item)
        container.add_widget(self.eye_item)
        self._add_divider_to(container, 'chords')

        self.griff_zoom_item = PanelIcon(
            icon="magnify",
            on_click=lambda: self._on_menu_item('zoom'),
            action_name='zoom',
            asset_name=ASSET_LOUPE_PNG
        )
        self._mode_items['chords'].append(self.griff_zoom_item)
        container.add_widget(self.griff_zoom_item)
        self._add_divider_to(container, 'chords')

        back_btn = PanelIcon(
            icon="check",
            on_click=lambda: self._switch_mode('menu'),
            action_name='back',
            asset_name=ASSET_OK_PNG
        )
        self._mode_items['chords'].append(back_btn)
        container.add_widget(back_btn)

    def _populate_slider_panel(self, container, type_str):
        parent = self.parent_screen
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)

        if type_str == 'scroll':
            self.scroll_toggle_item = PanelIcon(
                icon="play",
                on_click=self._on_scroll_toggle_click,
                action_name='play',
                size_hint=(1, None),
                height=dp(38)
            )
            self._mode_items['scroll'].append(self.scroll_toggle_item)
            container.add_widget(self.scroll_toggle_item)
            self._add_divider_to(container, 'scroll')

        header_box = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(26),
            spacing=0,
            padding=[0, dp(2), 0, 0],
            pos_hint={'center_x': 0.5}
        )
        val_label = MDLabel(
            text="0",
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=accent,
            bold=True,
            size_hint=(1, 1),
            font_size=sp(15)
        )
        self._slider_labels[type_str] = val_label
        header_box.add_widget(val_label)
        container.add_widget(header_box)

        slider_wrap = AnchorLayout(
            anchor_x='center',
            anchor_y='center',
            size_hint=(1, 1),
            padding=[0, dp(4), 0, dp(4)]
        )

        if type_str == 'tonality':
            self.ton_slider = SongsPanelFader(
                min_value=-6, max_value=6, value=0, step=1,
                size_hint=(None, 1), width=dp(46),
            )
            self._style_slider(self.ton_slider, accent)

            def on_ton_change(instance, value):
                int_val = max(-6, min(6, int(round(value))))
                if self.ton_slider.value != int_val:
                    self.ton_slider.value = int_val
                val_half = int_val / 2
                val_label.text = "0" if val_half == 0 else f"{val_half:+g}"
                if parent and val_half != getattr(parent, 'current_tonality', 0):
                    parent.current_tonality = val_half
                    if hasattr(parent, 'apply_tonality'):
                        parent.apply_tonality(val_half)

            self.ton_slider.bind(value=on_ton_change)
            slider_wrap.add_widget(self.ton_slider)

        elif type_str == 'font':
            std_size = getattr(parent, 'STANDARD_FONT_SIZE', 42 if platform == 'android' else 20)
            self._font_multipliers = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
            self._font_sizes = [int(round(std_size * m)) for m in self._font_multipliers]
            total_steps = len(self._font_sizes) - 1

            self.font_slider = SongsPanelFader(
                min_value=0, max_value=total_steps, value=3, step=1,
                size_hint=(None, 1), width=dp(46),
            )
            self._style_slider(self.font_slider, accent)

            def on_font_change(instance, value):
                int_val = max(0, min(total_steps, int(round(value))))
                if self.font_slider.value != int_val:
                    self.font_slider.value = int_val
                new_size = self._font_sizes[int_val]
                mult = self._font_multipliers[int_val]
                val_label.text = f"{int(mult)}x" if mult == int(mult) else f"{mult:.1f}x"
                if parent and getattr(parent, 'current_font_size', 0) != new_size:
                    parent.current_font_size = new_size
                    if hasattr(parent, 'content_label'):
                        parent.content_label.font_size = new_size
                    if hasattr(parent, '_update_content_height'):
                        parent._update_content_height()

            self.font_slider.bind(value=on_font_change)
            slider_wrap.add_widget(self.font_slider)

        elif type_str == 'scroll':
            def slider_to_speed(v):
                return 0.2 + (v - 1) * 0.03 if v <= 10 else 0.5 + (v - 10) * 0.1

            self.scroll_slider = SongsPanelFader(
                min_value=1, max_value=28, value=15, step=1,
                size_hint=(None, 1), width=dp(46),
            )
            self._style_slider(self.scroll_slider, accent)

            def on_scroll_change(instance, value):
                int_val = max(1, min(28, int(round(value))))
                if self.scroll_slider.value != int_val:
                    self.scroll_slider.value = int_val
                new_speed = slider_to_speed(int_val)
                val_label.text = f"{new_speed:.1f}x"
                if parent:
                    parent.scroll_speed = new_speed

            self.scroll_slider.bind(value=on_scroll_change)
            slider_wrap.add_widget(self.scroll_slider)

        container.add_widget(slider_wrap)

        self._add_divider_to(container, type_str)

        menu_slot_height = (self.FIXED_HEIGHT - dp(16) - dp(1.2) * 4) / 5
        back_btn = PanelIcon(
            icon="check",
            on_click=lambda: self._switch_mode('menu'),
            action_name='back',
            asset_name=ASSET_OK_PNG,
            size_hint=(1, None),
            height=menu_slot_height
        )
        self._mode_items[type_str].append(back_btn)
        container.add_widget(back_btn)

    def _style_slider(self, slider, accent):
        slider.accent_color = accent

    def _sync_mode_values(self, mode_name):
        parent = self.parent_screen
        if not parent:
            return
        if mode_name == 'chords':
            parent_mode = getattr(parent, 'display_mode', 'finger')
            self.mode_item.action_name = 'mode_notes' if parent_mode == 'notes' else 'mode'
            self.mode_item.set_icon("music-note" if parent_mode == "notes" else "gesture-tap")
            is_eye = getattr(parent, 'eye_active', False)
            self.eye_item.action_name = 'eye' if is_eye else 'eye_off'
            self.eye_item.set_icon("eye" if is_eye else "eye-off")
            new_scale = getattr(parent, 'griff_scale', 0.8)
            self.griff_zoom_item.set_icon("magnify" if new_scale == 0.8 else "magnify-plus")
        elif mode_name == 'tonality':
            cur_ton = getattr(parent, 'current_tonality', 0)
            self.ton_slider.value = int(round(cur_ton * 2))
            self._slider_labels['tonality'].text = "0" if cur_ton == 0 else f"{cur_ton:+g}"
        elif mode_name == 'font':
            curr_size = getattr(parent, 'current_font_size', self._font_sizes[3])
            idx = min(range(len(self._font_sizes)), key=lambda i: abs(self._font_sizes[i] - curr_size))
            self.font_slider.value = idx
            mult = self._font_multipliers[idx]
            self._slider_labels['font'].text = f"{int(mult)}x" if mult == int(mult) else f"{mult:.1f}x"
        elif mode_name == 'scroll':
            curr_speed = getattr(parent, 'scroll_speed', 1.0)
            idx = int(1 + (curr_speed - 0.2) / 0.03) if curr_speed <= 0.5 else int(10 + (curr_speed - 0.5) / 0.1)
            self.scroll_slider.value = max(1, min(28, idx))
            self._slider_labels['scroll'].text = f"{curr_speed:.1f}x"

    def _on_menu_item(self, action):
        if action == 'chords':
            self._switch_mode('chords')
        elif action == 'variant':
            if self.parent_screen and hasattr(self.parent_screen, '_next_chord_variant'):
                self.parent_screen._next_chord_variant()
        elif action == 'mode':
            if self.parent_screen and hasattr(self.parent_screen, '_toggle_display_mode'):
                self.parent_screen._toggle_display_mode()
            self._sync_mode_values('chords')
            self.update_theme_colors()
        elif action == 'eye':
            if self.parent_screen and hasattr(self.parent_screen, '_toggle_eye'):
                self.parent_screen._toggle_eye()
            self._sync_mode_values('chords')
            self.update_theme_colors()
            if getattr(self.parent_screen, 'eye_active', False) and not getattr(self.parent_screen, 'is_chords_mode', False):
                self.parent_screen.show_chords_section()
        elif action == 'zoom':
            if self.parent_screen and hasattr(self.parent_screen, '_toggle_griff_zoom'):
                self.parent_screen._toggle_griff_zoom()
            self._sync_mode_values('chords')
        elif action in ('tonality', 'scroll', 'font'):
            self._switch_mode(action)
        elif action == 'tabs':
            if self.parent_screen:
                self.parent_screen._next_song_tab()

    def _on_scroll_toggle_click(self):
        parent = self.parent_screen
        if not parent:
            return
        theme_id = settings_manager.theme
        if getattr(parent, 'is_scrolling', False):
            if hasattr(parent, 'stop_scroll'):
                parent.stop_scroll()
            self.scroll_toggle_item.action_name = 'play'
            self.scroll_toggle_item.set_icon("play")
            self.scroll_toggle_item.set_color(DetailColors.get_icon_color(theme_id, 'play'))
        else:
            if hasattr(parent, 'toggle_scroll'):
                parent.toggle_scroll()
            elif hasattr(parent, 'start_scroll'):
                parent.start_scroll()
            self.scroll_toggle_item.action_name = 'stop'
            self.scroll_toggle_item.set_icon("stop")
            self.scroll_toggle_item.set_color(DetailColors.get_icon_color(theme_id, 'stop'))



    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)
        div_color = DetailColors.get_divider(theme_id)

        self.bg_color_inst.rgba = DetailColors.get_panel_bg(theme_id)
        self.line_color_inst.rgba = DetailColors.get_panel_line(theme_id)

        for divs in self._mode_dividers.values():
            for d in divs:
                d.color = div_color

        has_multiple_tabs = len(getattr(self.parent_screen, 'tabs', [])) > 1
        for item in self._mode_items['menu']:
            if item.action_name in ('tabs', 'tabs_disabled'):
                item.action_name = 'tabs' if has_multiple_tabs else 'tabs_disabled'
            item.set_color(DetailColors.get_icon_color(theme_id, item.action_name))

        for m in ('chords', 'tonality', 'scroll', 'font'):
            if m == 'scroll' and hasattr(self, 'scroll_toggle_item'):
                is_scr = getattr(self.parent_screen, 'is_scrolling', False)
                key = 'stop' if is_scr else 'play'
                self.scroll_toggle_item.action_name = key
                self.scroll_toggle_item.set_icon(key)
            for item in self._mode_items[m]:
                item.set_color(DetailColors.get_icon_color(theme_id, item.action_name))

        for lbl in self._slider_labels.values():
            lbl.text_color = accent

        for sl_name in ('ton_slider', 'font_slider', 'scroll_slider'):
            if hasattr(self, sl_name):
                self._style_slider(getattr(self, sl_name), accent)


# ============================================================
# БАЗОВЫЙ ЭКРАН ПРОСМОТРА ПЕСНИ
# ============================================================
class BaseSongDetailScreen(BaseScreen):
    SCREEN_NAME = 'base_song_detail'
    DEFAULT_PREVIOUS_SCREEN = 'home'
    DEFAULT_IS_FAVORITE = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.SCREEN_NAME
        self._manage_padding_manually = True

        # Каждый наследник получает свой изолированный кэш состояний без лишних файлов
        self.state_manager = BaseSongDetailStateManager(name=self.__class__.__name__)

        self.song_id = None
        self.song_title = None
        self.song_artist = None
        self.is_favorite = self.DEFAULT_IS_FAVORITE
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self.previous_screen = self.DEFAULT_PREVIOUS_SCREEN

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

        self._chords_client = get_chords_client()
        self._batch_loaded = False
        self._batch_chords_data = {}
        self._pending_batch_event = None

        self.load_background()
        self.init_ui()
        logger.info(f'Экран {self.__class__.__name__} создан')

    def set_previous_screen(self, screen_name):
        self.previous_screen = screen_name

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
        text_p = DetailColors.get_text_primary(theme_id)
        div_color = DetailColors.get_divider(theme_id)

        if hasattr(self, 'content_label'):
            self.content_label.text_color = text_p

        for div in (getattr(self, 'top_divider', None), getattr(self, 'panel_divider', None),
                    getattr(self, 'bottom_divider', None)):
            if div:
                div.md_bg_color = div_color

        if getattr(self, 'griff_divider', None):
            self.griff_divider.md_bg_color = div_color

        if self.chord_name_label:
            self.chord_name_label.text_color = text_p

        if self._floating_panel:
            self._floating_panel.update_theme_colors()

        if self.original_cleaned_text:
            self.precompute_transpositions(self.original_cleaned_text)
            if isinstance(self.transposed_text_cache, dict):
                new_text = self.transposed_text_cache.get(self.current_tonality)
                if new_text:
                    self.content_label.text = new_text
                    self.content_label.markup = True
                    self._update_content_height()

    def prepare_clean_screen(self, song_id, artist="", title=""):
        """Мгновенно очищает старую песню до начала перехода на экран."""
        self.stop_scroll()
        self.song_id = song_id
        self.song_artist = artist
        self.song_title = title
        self.tabs = []
        self.current_tab_index = 0
        self.current_tonality = 0
        self.original_cleaned_text = ""
        self.transposed_text_cache = {}
        self.transposed_chords_cache = {}
        self._song_chords = []

        if self.content_label:
            self.content_label.text = ""
            self.content_label.height = dp(100)

        if self.content_scroll:
            self.content_scroll.scroll_y = 1.0

        if self.is_chords_mode:
            self.close_chords_section()
        self.eye_active = False

        if self._floating_panel:
            self._floating_panel._build_menu()

        self.update_top_nav_title()
        self.show_loading()

    def init_ui(self):
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
        top_offset = layout_config.get_top_padding(include_top_nav=True)
        bottom_nav_total = layout_config.get_bottom_nav_total_height()

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

        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.3],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        self._text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=4,
            padding=[dp(16), dp(4), dp(16), dp(4)],
            adaptive_height=True,
            md_bg_color=[0, 0, 0, 0]
        )

        self.content_label = ChordTextLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            valign="top",
            line_height=1.5,
            markup=True,
            font_name='NotoSansSymbols2'
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
        if self._griff_added:
            return

        from kivy.uix.carousel import Carousel
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)

        base_height = 135 * self.griff_scale
        griff_width = dp(340) * self.griff_scale
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

            from chord_utils.assets import get_griff_texture
            texture = get_griff_texture()
            if texture:
                renderer.set_background(texture)

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
        if content_scroll in self.song_card.children:
            self.song_card.remove_widget(content_scroll)

        self.song_card.add_widget(self.chord_name_section)
        self.song_card.add_widget(self.griff_container)
        self.song_card.add_widget(content_scroll)

        self._griff_added = True
        self._current_chord_index = 0

        if self._song_chords:
            if self._batch_chords_data:
                self._load_chord_variants(self._song_chords[0])
                self._update_chords_display()
            else:
                if self.chord_name_label:
                    self.chord_name_label.text = self._song_chords[0]
                for renderer in self.chord_renderers:
                    renderer.clear_sprites()
                self._load_missing_chords()

        if self.chords_carousel and self.chord_slides:
            self.chords_carousel.load_slide(self.chord_slides[0])

    def _on_carousel_slide(self, instance, slide):
        if not self.chord_slides or not self._song_chords:
            return
        try:
            index = self.chord_slides.index(slide)
            if index >= len(self._song_chords):
                index = index % len(self._song_chords)
            if index != self._current_chord_index:
                self._current_chord_index = index
                self._update_chords_display()
        except ValueError:
            pass

    def _hide_chords_layer(self):
        if not self._griff_added:
            return

        content_scroll = self.content_scroll
        for w in (self.chord_name_section, self.griff_container):
            if w and w in self.song_card.children:
                self.song_card.remove_widget(w)

        self.chord_name_section = None
        self.griff_container = None
        self.chord_name_label = None

        if content_scroll not in self.song_card.children:
            self.song_card.add_widget(content_scroll)

        self.chords_carousel = None
        self.chord_renderers = []
        self.chord_slides = []
        self._griff_added = False

    def close_chords_section(self, *args):
        self.is_chords_mode = False
        self._hide_chords_layer()

    # ============ BATCH-ЗАГРУЗКА АККОРДОВ ============
    def _load_chords_batch(self):
        if not self._song_chords or self._batch_loaded:
            return

        chord_pairs = []
        for chord_name in self._song_chords:
            main_name, chord_type = self._chords_client.resolve_chord(chord_name)
            chord_pairs.append({"main_name": main_name, "chord_type": chord_type})

        def _on_success(result):
            self._batch_loaded = True
            self._apply_batch_result(result)
            if self.is_chords_mode and self._griff_added:
                self._update_chords_display()

        def _on_error(err):
            logger.warning(f"{self.__class__.__name__}: batch failed: {err}")

        self._chords_client.get_chords_batch(
            chord_pairs, on_success=_on_success, on_error=_on_error
        )

    def _schedule_missing_chords_load(self):
        if self._pending_batch_event:
            Clock.unschedule(self._pending_batch_event)
        self._pending_batch_event = Clock.schedule_once(
            lambda dt: self._load_missing_chords(), 0.4
        )

    def _load_missing_chords(self):
        self._pending_batch_event = None
        if not self._song_chords or not self._chords_client:
            return

        missing_pairs = []
        for chord_name in self._song_chords:
            main_name, chord_type = self._chords_client.resolve_chord(chord_name)
            if not self._find_chord_group(main_name, chord_type):
                missing_pairs.append({"main_name": main_name, "chord_type": chord_type})

        if not missing_pairs:
            self._update_current_chord_from_batch()
            return

        def _on_success(result):
            new_chords = result.get("chords", {})
            if new_chords:
                self._batch_chords_data.update(new_chords)
                self._update_current_chord_from_batch()

            not_found = result.get("not_found", [])
            for nf in not_found:
                nf_name = nf.get("main_name") if isinstance(nf, dict) else str(nf)
                if nf_name:
                    self._fetch_synonym_fallback(nf_name)

        def _on_error(err):
            logger.warning(f"{self.__class__.__name__}: batch failed: {err}")

        self._chords_client.get_chords_batch(
            missing_pairs, on_success=_on_success, on_error=_on_error
        )

    def _fetch_synonym_fallback(self, requested_name: str):
        def _on_syn_results(items):
            if not items:
                return
            first = items[0]
            main_name = first.get("main_name")
            chord_type = first.get("chord_type")
            if not main_name or not chord_type:
                return

            def _on_variants(variants):
                if not variants:
                    return
                key = f"{requested_name}|{chord_type}"
                self._batch_chords_data[key] = {
                    "requested_main_name": requested_name,
                    "variants": variants,
                }
                self._update_current_chord_from_batch()

            self._chords_client.get_chord(main_name, chord_type, on_success=_on_variants)

        self._chords_client.search_by_synonym(requested_name, on_success=_on_syn_results)

    def _find_chord_group(self, main_name: str, chord_type: str):
        if not self._batch_chords_data:
            return None

        enharmonic_map = {
            'H': 'B', 'B': 'H',
            'A#': 'Bb', 'Bb': 'A#',
            'C#': 'Db', 'Db': 'C#',
            'D#': 'Eb', 'Eb': 'D#',
            'F#': 'Gb', 'Gb': 'F#',
            'G#': 'Ab', 'Ab': 'G#',
        }

        candidates = [main_name]
        for src, dst in enharmonic_map.items():
            if main_name.startswith(src) and (len(main_name) == len(src) or main_name[len(src)] not in ('#', 'b')):
                candidates.append(dst + main_name[len(src):])

        norm_candidates = {c.replace('/', '\\').lower() for c in candidates}
        target_type = (chord_type or "").lower()

        for key, group in self._batch_chords_data.items():
            if not isinstance(group, dict):
                continue
            if '|' in key:
                k_name, k_type = key.split('|', 1)
                if k_name.replace('/', '\\').lower() in norm_candidates and k_type.lower() == target_type:
                    return group

        for key, group in self._batch_chords_data.items():
            if not isinstance(group, dict):
                continue
            req_name = (group.get("requested_main_name") or "").replace('/', '\\').lower()
            if req_name in norm_candidates:
                return group
            for v in group.get("variants", []):
                v_main = (v.get("main_name") or "").replace('/', '\\').lower()
                syns = {s.replace('/', '\\').lower() for s in v.get("synonyms", [])}
                if v_main in norm_candidates or (norm_candidates & syns):
                    return group
        return None

    def _apply_batch_result(self, result):
        chords_data = result.get("chords", {})
        not_found = result.get("not_found", [])
        if not_found:
            logger.warning(f"{self.__class__.__name__}: не найдено {len(not_found)} аккордов: {not_found}")
        self._batch_chords_data = chords_data
        self._update_current_chord_from_batch()

    def _update_current_chord_from_batch(self):
        if not self._batch_chords_data or not self._song_chords:
            return
        if self._current_chord_index >= len(self._song_chords):
            self._current_chord_index = 0

        current_chord = self._song_chords[self._current_chord_index]
        main_name, chord_type = self._chords_client.resolve_chord(current_chord)
        group = self._find_chord_group(main_name, chord_type)
        if not group:
            if self._current_chord_index < len(self.chord_renderers):
                self.chord_renderers[self._current_chord_index].clear_sprites()
            return

        variants = []
        for v in group.get("variants", []):
            variants.append({
                "server_data": {
                    "main_name": v.get("main_name"),
                    "synonyms": v.get("synonyms", []),
                    "chord_type": v.get("chord_type"),
                    "variant": v.get("variant", 1),
                    "background_name": v.get("background_name", "griff"),
                    "frets": v.get("frets", {}),
                    "notes": v.get("notes", {}),
                    "open_notes": v.get("open_notes", {}),
                    "barres": v.get("barres", {}),
                    "selected_finger": v.get("selected_finger", []),
                    "selected_note": v.get("selected_note", []),
                }
            })

        if variants and self._current_chord_index < len(self.chord_renderers):
            renderer = self.chord_renderers[self._current_chord_index]
            module = self._dict_to_module(variants[0]["server_data"])
            renderer.load_chord(module)
            renderer.set_mode(self.display_mode)

        self.chord_variants = variants
        self.chord_variant_index = 0

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

    def _load_chord_variants(self, chord_name):
        self.chord_variants = []
        self.chord_variant_index = 0

        if not self._batch_chords_data:
            if self._current_chord_index < len(self.chord_renderers):
                self.chord_renderers[self._current_chord_index].clear_sprites()
            return

        if isinstance(chord_name, (list, tuple)) and chord_name:
            chord_name = chord_name[0]
        if not isinstance(chord_name, str):
            return

        main_name, chord_type = self._chords_client.resolve_chord(chord_name)
        group = self._find_chord_group(main_name, chord_type)
        if not group:
            if self._current_chord_index < len(self.chord_renderers):
                self.chord_renderers[self._current_chord_index].clear_sprites()
            return

        variants = []
        for v in group.get("variants", []):
            variants.append({
                "server_data": {
                    "main_name": v.get("main_name"),
                    "synonyms": v.get("synonyms", []),
                    "chord_type": v.get("chord_type"),
                    "variant": v.get("variant", 1),
                    "background_name": v.get("background_name", "griff"),
                    "frets": v.get("frets", {}),
                    "notes": v.get("notes", {}),
                    "open_notes": v.get("open_notes", {}),
                    "barres": v.get("barres", {}),
                    "selected_finger": v.get("selected_finger", []),
                    "selected_note": v.get("selected_note", []),
                }
            })

        self.chord_variants = variants
        if variants:
            self.load_current_variant()

    def load_current_variant(self):
        if not self.chord_variants:
            return
        variant = self.chord_variants[self.chord_variant_index]
        chord_module = variant.get('module') or variant.get('module_1')
        if not chord_module and variant.get('server_data'):
            chord_module = self._dict_to_module(variant['server_data'])

        if chord_module and self._current_chord_index < len(self.chord_renderers):
            renderer = self.chord_renderers[self._current_chord_index]
            renderer.load_chord(chord_module)
            renderer.set_mode(self.display_mode)

    def _next_chord_variant(self):
        if not self.chord_variants:
            return
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
        if not self.griff_container:
            return

        zoom_levels = [0.8, 1.0, 1.2]
        current = self.griff_scale
        new_scale = zoom_levels[(zoom_levels.index(current) + 1) % len(zoom_levels)] if current in zoom_levels else 0.8

        self.griff_scale = new_scale
        self.griff_container.height = int(dp(135) * new_scale)

        griff_width = dp(340) * new_scale
        max_griff_width = Window.width - dp(80)
        if griff_width > max_griff_width:
            griff_width = max_griff_width
        self.griff_container.width = griff_width + dp(60)

        if hasattr(self, 'chords_carousel') and self.chords_carousel:
            self.chords_carousel.width = griff_width

    def _update_chords_display(self):
        if not self._song_chords:
            return
        if self._current_chord_index >= len(self._song_chords):
            self._current_chord_index = 0

        chord_name = self._song_chords[self._current_chord_index]
        if self.chord_name_label:
            self.chord_name_label.text = chord_name

        if not self._batch_chords_data:
            return
        self._load_chord_variants(chord_name)

    def _extract_and_cache_chords(self):
        chords = set()
        if self.tabs and self.current_tab_index < len(self.tabs):
            content = self.tabs[self.current_tab_index].get('content', '')
            if content:
                chords.update(extract_chords_from_text(clean_text(content)))
        self._song_chords = sorted(list(chords))

    def precompute_transpositions(self, cleaned_text):
        theme_id = settings_manager.theme
        self.original_cleaned_text = cleaned_text
        self._extract_and_cache_chords()

        self.transposed_text_cache = {
            0: highlight_chords_in_text(cleaned_text, theme_id=theme_id)
        }
        self.transposed_chords_cache = {
            0: self._song_chords.copy()
        }
        self._all_possible_chords = list(self._song_chords)

    def apply_tonality(self, step):
        transposed = self._get_or_compute_tonality(step)
        if transposed:
            self.content_label.text = transposed
            self.content_label.markup = True

        if isinstance(self.transposed_chords_cache, dict):
            self._song_chords = list(self.transposed_chords_cache.get(step, []))

        self._schedule_missing_chords_load()

        if (self.is_chords_mode or getattr(self, 'eye_active', False)) and self._song_chords:
            self.is_chords_mode = True
            if not self._griff_added:
                self._show_chords_layer()
                return
            if len(self.chord_slides) != len(self._song_chords):
                self._hide_chords_layer()
                self._show_chords_layer()
                self.is_chords_mode = True
            else:
                if self._current_chord_index >= len(self._song_chords):
                    self._current_chord_index = 0
                self._update_chords_display()

    def _get_or_compute_tonality(self, step):
        if step in self.transposed_text_cache:
            return self.transposed_text_cache[step]
        if not self.original_cleaned_text:
            return None
        theme_id = settings_manager.theme
        if step == 0:
            markup = highlight_chords_in_text(self.original_cleaned_text, theme_id=theme_id)
            chords = self._song_chords.copy()
        else:
            markup = transpose_text(self.original_cleaned_text, step, theme_id=theme_id)
            plain = re.sub(r'\[/?[a-z]+.*?\]', '', markup)
            chords = extract_chords_from_text(plain)
        self.transposed_text_cache[step] = markup
        self.transposed_chords_cache[step] = chords
        return markup

    def _get_font_multiplier(self, font_size):
        ratio = round(font_size / self.STANDARD_FONT_SIZE * 10) / 10
        return f"{int(ratio)}x" if ratio == int(ratio) else f"{ratio:.1f}x"

    def reset_font_size(self):
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'content_label'):
            self.content_label.font_size = self.current_font_size
        self._update_content_height()

    def toggle_scroll(self):
        if not self.is_scrolling and self.content_scroll.scroll_y <= 0.01:
            self.reset_scroll_position()

        if not self.is_scrolling:
            self.start_scroll()
        else:
            self.stop_scroll()

    def start_scroll(self):
        if self.is_scrolling:
            return
        self.is_scrolling = True

        def update_scroll(dt):
            if not self.is_scrolling:
                return False
            new_y = self.content_scroll.scroll_y - 0.0004 * self.scroll_speed
            if new_y <= 0:
                self.content_scroll.scroll_y = 0
                self.stop_scroll()
                if (self._floating_panel
                        and hasattr(self._floating_panel, 'scroll_toggle_item')
                        and self._floating_panel.scroll_toggle_item):
                    theme_id = settings_manager.theme
                    self._floating_panel.scroll_toggle_item.action_name = 'play'
                    self._floating_panel.scroll_toggle_item.set_icon("play")
                    self._floating_panel.scroll_toggle_item.set_color(DetailColors.get_icon_color(theme_id, 'play'))
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
        if self.is_scrolling:
            self.stop_scroll()
        self.content_scroll.scroll_y = 1.0

    def show_tabs_picker(self):
        if not self.tabs or len(self.tabs) <= 1:
            notify.info(get_text('no_variants'))
            return

        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)

        content = MDBoxLayout(
            orientation='vertical', spacing=dp(8), padding=dp(16),
            size_hint_y=None, adaptive_height=True
        )
        for i in range(len(self.tabs)):
            btn = MDRaisedButton(
                text=f"{get_text('variant')} {i + 1}",
                size_hint=(1, None), height=dp(48),
                md_bg_color=accent if i == self.current_tab_index else [0.2, 0.2, 0.2, 0.8],
                text_color=[1, 1, 1, 1],
                on_release=lambda x, idx=i: self._select_tab(idx)
            )
            content.add_widget(btn)

        dialog = MDDialog(
            title=get_text('choose_chord'), type="custom", content_cls=content,
            buttons=[MDRaisedButton(text=get_text('close'), on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.tabs_dialog = dialog

    def _select_tab(self, index):
        if hasattr(self, 'tabs_dialog'):
            self.tabs_dialog.dismiss()
        self.current_tab_index = index
        self._load_current_tab()

    def _next_song_tab(self):
        if not self.tabs or len(self.tabs) <= 1:
            notify.info(get_text('no_variants'))
            return
        self.current_tab_index = (self.current_tab_index + 1) % len(self.tabs)
        self._load_current_tab()
        notify.info(f"{get_text('variant')} {self.current_tab_index + 1} / {len(self.tabs)}")

    def _load_current_tab(self):
        if self.tabs and self.current_tab_index < len(self.tabs):
            cleaned = clean_text(self.tabs[self.current_tab_index].get('content', ''))
            if cleaned:
                self.current_tonality = 0
                self.transposed_text_cache = {}
                self.transposed_chords_cache = {}
                self.precompute_transpositions(cleaned)
                self.content_label.text = self._get_or_compute_tonality(0) or cleaned
                self._song_chords = list(self.transposed_chords_cache.get(0, []))
                self.content_label.markup = True
                self._current_chord_index = 0
                self._load_chords_batch()

                if self.is_chords_mode or getattr(self, 'eye_active', False):
                    self._hide_chords_layer()
                    if self._song_chords:
                        self._show_chords_layer()
                        self.is_chords_mode = True
                    else:
                        self.is_chords_mode = False
            else:
                self.content_label.text = get_text('loading_error')
                self.content_label.markup = False

        self._update_content_height()
        Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1)

    def set_song(self, song_id, artist="", title=""):
        self.song_id = song_id
        self.song_artist = artist
        self.song_title = title
        self.is_favorite = self.DEFAULT_IS_FAVORITE or api.is_song_favorited(song_id)
        self.reset_screen_state()
        self.load_song_data()

    def reset_screen_state(self):
        self.current_tonality = 0
        self.transposed_chords_cache = {}
        self.transposed_text_cache = {}
        self.original_cleaned_text = ""

        if self.is_chords_mode:
            self.close_chords_section()
        self.eye_active = False
        self._current_chord_index = 0
        self.reset_font_size()
        self.display_mode = "finger"
        self.chord_variants = []
        self.chord_variant_index = 0
        self.scroll_speed = 1.0
        self.is_scrolling = False
        self.griff_scale = 0.8
        self._batch_loaded = False
        self._batch_chords_data = {}

        if self._floating_panel:
            self._floating_panel.hide()

    def load_song_data(self):
        saved = self.state_manager.get_song_state(self.song_id)
        if saved and saved.get('tabs'):
            self.song_artist = saved.get('artist') or self.song_artist
            self.song_title = saved.get('title') or self.song_title
            self.tabs = saved.get('tabs', [])
            self.current_tab_index = saved.get('current_tab_index', 0)
            self.current_tonality = saved.get('current_tonality', 0)
            self.original_cleaned_text = saved.get('original_cleaned_text', '')
            self.transposed_text_cache = saved.get('transposed_text_cache', {})
            self.transposed_chords_cache = saved.get('transposed_chords_cache', {})
            self._song_chords = list(self.transposed_chords_cache.get(self.current_tonality, []))
            self._batch_chords_data = saved.get('batch_chords_data', {})

            text_to_show = self._get_or_compute_tonality(self.current_tonality)
            if text_to_show:
                self.content_label.text = text_to_show
                self.content_label.markup = True
                self._update_content_height()

            self.update_top_nav_title()
            self.hide_loading()
            if self._floating_panel:
                self._floating_panel.update_theme_colors()

            self._load_chords_batch()
            saved_scroll = saved.get('scroll_y', 1.0)
            Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', saved_scroll), 0.05)
            return

        self.show_loading()
        api.get_tab(
            song_id=self.song_id,
            on_success=self.on_song_loaded,
            on_failure=self.on_load_failed,
            force_refresh=False
        )

    def show_loading(self):
        if self.is_loading:
            return
        self.is_loading = True
        spinner = LoadingSpinner(text=get_text('loading', 'Загрузка'))
        spinner.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.loading_spinner = spinner
        self.add_widget(spinner)
        spinner.start_animation()

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            if hasattr(self.loading_spinner, 'stop_animation'):
                self.loading_spinner.stop_animation()
            if self.loading_spinner.parent:
                self.remove_widget(self.loading_spinner)
            self.loading_spinner = None

    def _save_current_song_state(self):
        if not self.song_id or not self.tabs:
            return
        self.state_manager.save_song_state(self.song_id, {
            'artist': self.song_artist,
            'title': self.song_title,
            'tabs': self.tabs,
            'current_tab_index': self.current_tab_index,
            'current_tonality': self.current_tonality,
            'original_cleaned_text': self.original_cleaned_text,
            'transposed_text_cache': self.transposed_text_cache,
            'transposed_chords_cache': self.transposed_chords_cache,
            'batch_chords_data': self._batch_chords_data,
            'scroll_y': self.content_scroll.scroll_y if self.content_scroll else 1.0,
        })


    def on_song_loaded(self, data):
        self.song_artist = data.get('artist') or self.song_artist or get_text('unknown_artist')
        self.song_title = data.get('title') or self.song_title or get_text('untitled')
        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'):
            self.tabs = [{'id': self.song_id, 'content': data.get('content', '')}]
        self.current_tab_index = 0

        if self.tabs:
            cleaned = clean_text(self.tabs[0].get('content', ''))
            self._extract_and_cache_chords()
            self.precompute_transpositions(cleaned)
            self.content_label.text = self.transposed_text_cache.get(0, cleaned)
            self.content_label.markup = True
            self._update_content_height()

        self.is_favorite = api.is_song_favorited(self.song_id)
        if not self.is_favorite:
            self.is_favorite = data.get('is_favorite', self.DEFAULT_IS_FAVORITE)
        self._on_favorite_status_changed()

        self.update_top_nav_title()
        self.hide_loading()

        for delay in [0.3, 0.5, 0.8, 1.0]:
            Clock.schedule_once(self._wait_for_ready_and_scroll, delay)

        self._load_chords_batch()

        if len(self.tabs) <= 1 and self.song_artist and self.song_title:
            self._fetch_other_variants()
        elif self._floating_panel:
            self._floating_panel.update_theme_colors()

    def _fetch_other_variants(self):
        current_song_id = self.song_id

        def _on_tabs_list(res):
            if self.song_id != current_song_id or not isinstance(res, dict):
                return
            tabs_info = res.get('tabs', [])
            other_ids = [
                t['id'] for t in tabs_info
                if t.get('id') and str(t['id']) != str(current_song_id)
            ]
            if not other_ids:
                if self._floating_panel:
                    self._floating_panel.update_theme_colors()
                return
            for vid in other_ids:
                api.get_tab(
                    song_id=vid,
                    on_success=lambda tab_data, expected_id=current_song_id: self._append_variant_tab(
                        tab_data, expected_id
                    ),
                    on_failure=lambda req, err: None
                )

        api.get_tabs_by_song(self.song_artist, self.song_title, on_success=_on_tabs_list)

    def _append_variant_tab(self, tab_data, expected_song_id):
        if self.song_id != expected_song_id or not isinstance(tab_data, dict):
            return
        new_tabs = tab_data.get('tabs', [])
        if not new_tabs and tab_data.get('content'):
            new_tabs = [{'id': tab_data.get('id'), 'content': tab_data.get('content', '')}]

        existing_texts = {clean_text(t.get('content', '')) for t in self.tabs}
        added = False
        for t in new_tabs:
            cleaned = clean_text(t.get('content', ''))
            if cleaned and cleaned not in existing_texts:
                self.tabs.append(t)
                existing_texts.add(cleaned)
                added = True

        if added and self._floating_panel:
            self._floating_panel.update_theme_colors()

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

    # ============ ИЗБРАННОЕ ============
    def toggle_favorite(self, *args):
        if not api.is_authenticated():
            app = MDApp.get_running_app()
            if app and hasattr(app, 'open_profile'):
                app.open_profile()
            return

        if self.is_favorite:
            def confirm(instance):
                dialog.dismiss()
                self._remove_from_favorites()

            dialog = MDDialog(
                title=get_text('remove_from_favorites'),
                text=f"{self.song_title}",
                buttons=[
                    MDRaisedButton(text=get_text('close'), on_release=lambda x: dialog.dismiss()),
                    MDRaisedButton(text=get_text('reset'), on_release=confirm, md_bg_color=[0.8, 0.3, 0.3, 1]),
                ]
            )
            dialog.open()
        else:
            self._add_to_favorites()

    def _add_to_favorites(self):
        def on_success(result):
            self.is_favorite = True
            self._on_favorite_status_changed()
            notify.success(get_text('favorite_added'))

        def on_failure(req, error):
            notify.error(get_text('favorite_error'))

        api.add_to_favorites(
            song_id=self.song_id,
            song_data={'artist': self.song_artist or '', 'title': self.song_title or ''},
            on_success=on_success,
            on_failure=on_failure
        )

    def _remove_from_favorites(self):
        def on_success(result):
            self.is_favorite = False
            self._on_favorite_status_changed()
            notify.success(get_text('no_favorites'))

        def on_failure(req, error):
            self.is_favorite = True
            notify.error(get_text('search_error'))

        api.remove_from_favorites(
            song_id=self.song_id,
            on_success=on_success,
            on_failure=on_failure
        )

    def _on_favorite_status_changed(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if hasattr(app.top_nav, 'set_song_favorite_state'):
                app.top_nav.set_song_favorite_state(self.song_id, self.is_favorite)
            elif hasattr(app.top_nav, 'update_favorite_icon'):
                app.top_nav.update_favorite_icon(self.is_favorite)

    # ============ НАВИГАЦИЯ И TOP_NAV ============
    def update_top_nav_title(self):
        app = MDApp.get_running_app()
        if not app or not hasattr(app, 'top_nav'):
            return

        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)
        text_s = DetailColors.get_text_secondary(theme_id)

        container = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            spacing=dp(2), padding=[dp(8), dp(4), dp(8), dp(4)]
        )
        title = MDLabel(
            text=self.song_title or get_text('artist_songs'),
            font_size=sp(18), halign="center", valign="middle",
            theme_text_color="Custom", text_color=text_p,
            bold=True, shorten=True, shorten_from="right"
        )
        artist = MDLabel(
            text=self.song_artist or "",
            font_size=sp(12), halign="center", valign="middle",
            theme_text_color="Custom", text_color=text_s,
            shorten=True, shorten_from="right"
        )
        container.add_widget(title)
        container.add_widget(artist)

        app.top_nav.set_custom_title_widget(container)

    def _configure_top_nav_on_enter(self, top_nav):
        if hasattr(top_nav, 'set_song_favorite_state'):
            top_nav.set_song_favorite_state(self.song_id, self.is_favorite)

    def on_leave(self):
        self.stop_scroll()
        self._save_current_song_state()
        logger.info(f"Выход из {self.__class__.__name__}")

    def go_back(self, instance=None):
        from config.navigation_config import navigate_back
        navigate_back(self.manager, self.SCREEN_NAME)

    def on_enter(self):
        super().on_enter()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            self._configure_top_nav_on_enter(app.top_nav)

        if self.song_title:
            self.update_top_nav_title()

        self.update_theme_colors()

        if self._floating_panel:
            def _init_panel(dt):
                self._floating_panel._init_position()
                self._floating_panel.hide()
                self._floating_panel._build_menu()
            Clock.schedule_once(_init_panel, 0.1)