# screens/favorite_detail_screen.py
"""
Экран просмотра песни ИЗ ИЗБРАННОГО.
С встроенной ручкой в панель справа и ловушкой свайпа.
Адаптирован под 3 темы и 6 языков.
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
from kivy.core.window import Window
from io import BytesIO
import re
from kivy.utils import platform

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height, get_status_bar_height
from screens.base_screen import BaseScreen
from screens.chord_renderer import ChordRenderer
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
from utils.settings_manager import settings_manager
from utils.localization import get_text
from utils.chord_highlighter import (
    ChordTextLabel,
    highlight_chords_in_text,
    extract_chords_from_text_wrapper as extract_chords_from_text,
)
from utils.transposer import transpose_text, transpose_chord_list

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
            return [0.1, 0.3, 0.2, 0.95]

    @staticmethod
    def get_divider(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 0.1]
        else:
            return [0.5, 0.5, 0.5, 0.3]


def clean_text(text):
    if not text:
        return ""
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
# ЛОВУШКА СВАЙПА
# ============================================================

class EdgeSwipeCatcher(Widget):
    """
    Прозрачная зона справа экрана, ловит свайп влево,
    чтобы открыть панель, когда она задвинута.
    """
    def __init__(self, on_swipe_open=None, **kwargs):
        super().__init__(**kwargs)
        self.on_swipe_open = on_swipe_open

        self.size_hint = (None, 1)
        self.width = dp(24)
        self.pos_hint = {'right': 1, 'center_y': 0.5}

        self._touch_start_x = 0
        self._dragging = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start_x = touch.x
            self._dragging = False
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            dx = touch.x - self._touch_start_x
            if dx < -dp(10) and not self._dragging:
                self._dragging = True
                if self.on_swipe_open:
                    self.on_swipe_open()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if not self._dragging:
                if self.on_swipe_open:
                    self.on_swipe_open()
            self._dragging = False
            return True
        return super().on_touch_up(touch)


# ============================================================
# ПАНЕЛЬ С РУЧКОЙ
# ============================================================

class FloatingPanelItem(ButtonBehavior, MDBoxLayout):
    """Иконка + мелкая подпись."""
    def __init__(self, icon, label, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.spacing = dp(0)
        self.md_bg_color = [0, 0, 0, 0]
        self.on_click_callback = on_click

        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)
        text_s = DetailColors.get_text_secondary(theme_id)

        self.icon_btn = MDIconButton(
            icon=icon, size_hint=(1, None), height=dp(28),
            theme_icon_color='Custom', icon_color=accent,
            md_bg_color=[0, 0, 0, 0], ripple_scale=0
        )
        self.label = MDLabel(
            text=label, font_size=sp(4),
            halign='center', valign='top',
            size_hint=(1, None), height=dp(10),
            theme_text_color='Custom', text_color=text_s,
            shorten=True, shorten_from='right',
            text_size=(52, None)
        )
        self.add_widget(self.icon_btn)
        self.add_widget(self.label)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click_callback:
                self.on_click_callback()
            return True
        return super().on_touch_down(touch)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)
        text_s = DetailColors.get_text_secondary(theme_id)
        self.icon_btn.icon_color = accent
        self.label.text_color = text_s


class FloatingPanel(MDCard):
    """
    Панель с встроенной ручкой слева.
    Старт — задвинута, видна только ручка.
    Свайп влево — выдвинуть, вправо — задвинуть.
    """
    PANEL_WIDTH = dp(64)
    HANDLE_WIDTH = dp(24)
    TOTAL_WIDTH = PANEL_WIDTH + HANDLE_WIDTH
    VISIBLE_MARGIN = dp(4)

    def __init__(self, parent_screen=None, on_action=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.on_action_callback = on_action

        theme_id = settings_manager.theme
        panel_bg = DetailColors.get_panel_bg(theme_id)
        bg_color = [panel_bg[0], panel_bg[1], panel_bg[2], 0.96]

        self.size_hint = (None, None)
        self.width = self.TOTAL_WIDTH
        self.height = dp(44) * 6 + dp(8) + dp(1) + dp(44) + dp(8)
        self.pos_hint = {}
        self.radius = [dp(16), 0, 0, dp(16)]
        self.elevation = 6
        self.md_bg_color = bg_color
        self.padding = [0, dp(6), 0, dp(6)]
        self.spacing = 0

        self._visible_x = None
        self._hidden_x = None
        self._is_visible = False
        self._anim = None
        self._touch_start_x = 0
        self._start_panel_x = 0
        self._dragging = False

        self._build_handle()

        self.content = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0,
            padding=[dp(2), 0, dp(2), 0]
        )
        self.add_widget(self.content)

        self.mode = 'menu'
        self._build_menu()
        Clock.schedule_once(lambda dt: self._init_position(), 0.5)

    def _build_handle(self):
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)

        handle = MDBoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=self.HANDLE_WIDTH,
            pos_hint={'x': 0, 'center_y': 0.5},
            padding=[dp(2), 0, dp(2), 0]
        )
        self._handle_icon = MDIconButton(
            icon='dots-vertical',
            size_hint=(1, None),
            height=dp(24),
            pos_hint={'center_y': 0.5},
            theme_icon_color='Custom',
            icon_color=accent,
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0
        )
        handle.add_widget(Widget(size_hint_y=1))
        handle.add_widget(self._handle_icon)
        handle.add_widget(Widget(size_hint_y=1))
        self.add_widget(handle)

    def _init_position(self):
        self._visible_x = Window.width - self.TOTAL_WIDTH - self.VISIBLE_MARGIN
        self._hidden_x = Window.width - self.HANDLE_WIDTH
        self.x = self._hidden_x
        self.y = (Window.height - self.height) / 2
        self._is_visible = False

    def _build_menu(self):
        self.content.clear_widgets()
        self.mode = 'menu'
        self.items = []

        items = [
            ('music', 'chords', get_text('chords', 'Аккорды')),
            ('tune', 'tonality', get_text('tonality', 'Тональность')),
            ('play-circle', 'scroll', get_text('started', 'Прокрутка')),
            ('folder-music', 'tabs', get_text('variant', 'Подборы')),
            ('format-size', 'font', get_text('settings', 'Шрифт')),
            ('palette', 'theme', get_text('theme', 'Тема')),
        ]

        for icon, action, label in items:
            item = FloatingPanelItem(
                icon=icon, label=label,
                on_click=lambda a=action: self._on_menu_item(a)
            )
            self.items.append(item)
            self.content.add_widget(item)

        div = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(1),
            md_bg_color=DetailColors.get_divider(settings_manager.theme)
        )
        self.content.add_widget(div)

        unfav = FloatingPanelItem(
            icon='star-off', label=get_text('remove_from_favorites', 'Убрать'),
            on_click=lambda: self._on_menu_item('unfavorite')
        )
        self.items.append(unfav)
        self.content.add_widget(unfav)

        self.height = dp(44) * 6 + dp(8) + dp(1) + dp(44) + dp(8)
        if self._hidden_x is not None:
            self.y = (Window.height - self.height) / 2

    def _on_menu_item(self, action):
        if action == 'chords':
            if self.parent_screen:
                self.parent_screen.show_chords_section()
        elif action == 'tonality':
            notify.info(get_text('tonality'))
        elif action == 'scroll':
            notify.info(get_text('started'))
        elif action == 'font':
            notify.info(get_text('settings'))
        elif action == 'tabs':
            if self.parent_screen:
                self.parent_screen.show_tabs_picker()
        elif action == 'theme':
            if self.parent_screen:
                self.parent_screen._toggle_theme()
        elif action == 'unfavorite':
            if self.parent_screen:
                self.parent_screen.toggle_favorite()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        panel_bg = DetailColors.get_panel_bg(theme_id)
        self.md_bg_color = [panel_bg[0], panel_bg[1], panel_bg[2], 0.96]

        if hasattr(self, '_handle_icon'):
            self._handle_icon.icon_color = DetailColors.get_accent(theme_id)

        if self.mode == 'menu':
            for item in self.items:
                item.update_theme_colors()
            for child in self.content.children:
                if isinstance(child, MDBoxLayout) and child.height == dp(1):
                    child.md_bg_color = DetailColors.get_divider(theme_id)

    def on_touch_down(self, touch):
        if self._visible_x is None or self._hidden_x is None:
            self._init_position()

        if self.collide_point(*touch.pos):
            if self._is_child_interactive(touch):
                return super().on_touch_down(touch)

            self._touch_start_x = touch.x
            self._start_panel_x = self.x
            self._dragging = False
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def _is_child_interactive(self, touch):
        for child in self.walk():
            if child is self:
                continue
            if hasattr(child, 'collide_point') and child.collide_point(*touch.pos):
                if isinstance(child, MDIconButton) or isinstance(child, FloatingPanelItem):
                    return True
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            dx = touch.x - self._touch_start_x
            if abs(dx) > dp(10):
                self._dragging = True
            new_x = self._start_panel_x + dx
            new_x = max(self._visible_x, min(self._hidden_x, new_x))
            self.x = new_x
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self._dragging:
                midpoint = (self._visible_x + self._hidden_x) / 2
                if self.x < midpoint:
                    self.show()
                else:
                    self.hide()
            self._dragging = False
            return True
        return super().on_touch_up(touch)

    def show(self):
        if self._is_visible:
            return
        self._is_visible = True
        if self._anim:
            self._anim.cancel(self)
        self._anim = Animation(x=self._visible_x, duration=0.25, t='out_quad')
        self._anim.start(self)

    def hide(self):
        if not self._is_visible:
            return
        self._is_visible = False
        if self._anim:
            self._anim.cancel(self)
        self._anim = Animation(x=self._hidden_x, duration=0.25, t='in_quad')
        self._anim.start(self)


# ============================================================
# ОСТАЛЬНЫЕ КОМПОНЕНТЫ
# ============================================================

class LoadingSpinner(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(16)
        theme_id = settings_manager.theme
        self.label = MDLabel(
            text=get_text('loading'), halign="center", font_size=sp(16),
            theme_text_color="Custom",
            text_color=DetailColors.get_text_secondary(theme_id),
            size_hint_y=None, height=dp(30))
        self.add_widget(self.label)

    def start_animation(self):
        pass

    def stop_animation(self):
        pass


# ============================================================
# ОСНОВНОЙ ЭКРАН
# ============================================================

class FavoriteDetailScreen(BaseScreen):
    """Экран просмотра песни ИЗ ИЗБРАННОГО."""

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

        if platform == 'android':
            self.STANDARD_FONT_SIZE = 42
            self.MIN_FONT_SIZE = 30
            self.MAX_FONT_SIZE = 60
        else:
            self.STANDARD_FONT_SIZE = 20
            self.MIN_FONT_SIZE = 14
            self.MAX_FONT_SIZE = 32
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
        self.griff_scale = 1.0
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
        self._edge_catcher = None

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
        for div in (getattr(self, 'top_divider', None),
                     getattr(self, 'panel_divider', None),
                     getattr(self, 'bottom_divider', None)):
            if div:
                div.md_bg_color = div_color
        if getattr(self, 'griff_divider', None):
            self.griff_divider.md_bg_color = div_color
        if self.chord_name_label:
            self.chord_name_label.text_color = text_p

        if self._floating_panel:
            self._floating_panel.update_theme_colors()

    def update_language(self):
        if self.song_title:
            self.update_top_nav_title()

    def init_ui(self):
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
        top_offset = layout_config.get_top_padding(include_top_nav=True)
        bottom_nav_total = layout_config.get_bottom_nav_total_height()

        card_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                                       padding=[0, top_offset, 0, 0])

        self.song_card = MDCard(
            orientation='vertical', size_hint=(1, 1),
            padding=[0, 0, 0, bottom_nav_total], spacing=0,
            radius=[0, 0, 0, 0], md_bg_color=[0, 0, 0, 0], elevation=0)

        self.top_divider = MDBoxLayout(orientation='horizontal',
                                        size_hint=(1, None), height=dp(2))
        self.song_card.add_widget(self.top_divider)

        self.content_scroll = MDScrollView(
            size_hint=(1, 1), do_scroll_x=False, bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.3],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1])

        self._text_container = MDBoxLayout(
            orientation='vertical', size_hint_y=None, spacing=4,
            padding=[dp(16), dp(16), dp(16), dp(4)],
            adaptive_height=True, md_bg_color=[0, 0, 0, 0])

        self.content_label = ChordTextLabel(
            text="", font_size=self.current_font_size, size_hint_y=None,
            theme_text_color="Custom", valign="top", line_height=1.5, markup=True)
        self.content_label.bind(texture_size=self._update_content_height)
        self._text_container.add_widget(self.content_label)

        self.content_scroll.add_widget(self._text_container)
        self.song_card.add_widget(self.content_scroll)

        self.bottom_divider = MDBoxLayout(orientation='horizontal',
                                           size_hint=(1, None), height=dp(2))
        self.song_card.add_widget(self.bottom_divider)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)
        self.add_widget(main_container)

        # === Панель с ручкой ===
        self._floating_panel = FloatingPanel(
            parent_screen=self,
            on_action=self._on_drawer_action
        )
        self.add_widget(self._floating_panel)

        # === Ловушка свайпа справа ===
        self._edge_catcher = EdgeSwipeCatcher(
            on_swipe_open=self._floating_panel.show
        )
        self.add_widget(self._edge_catcher)

        Clock.schedule_once(lambda dt: self._update_card_size(), 0.1)
        Clock.schedule_once(lambda dt: self._update_card_size(), 0.3)
        Clock.schedule_once(lambda dt: self.update_theme_colors(), 0.2)
        Clock.schedule_once(lambda dt: self._floating_panel._init_position(), 0.5)

    def _update_card_size(self, *args):
        if self.song_card:
            self.song_card.size_hint = (1, 1)
            self.song_card.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    def _update_content_height(self, *args):
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return
        text_height = self.content_label.texture_size[1]
        self.content_label.height = max(dp(50), text_height + dp(8))
        if self.content_label.parent:
            self.content_label.parent.height = text_height + dp(16)
        self.content_scroll.scroll_y = 1.0

    def _on_drawer_action(self, action):
        pass

    def show_chords_section(self):
        if self.is_tonality_mode: self.close_tonality_panel()
        if self.is_font_mode: self.close_font_panel()
        if self.is_scroll_mode: self.close_scroll_panel()
        if not self._song_chords:
            notify.info(get_text('no_chords'))
            return
        if self.is_chords_mode:
            self.close_chords_section()
            return
        self.is_chords_mode = True
        self._show_chords_layer()

    def _show_chords_layer(self):
        if self._griff_added:
            return
        from kivy.uix.carousel import Carousel
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)

        self.chord_name_section = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(30),
            padding=[dp(8), dp(2), dp(8), dp(2)], spacing=dp(4))
        self.chord_name_label = MDLabel(
            text="", halign="center", valign="middle", size_hint_x=1,
            theme_text_color="Custom", text_color=text_p,
            bold=True, font_size=sp(18))
        self.chord_name_section.add_widget(self.chord_name_label)

        self.griff_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(120),
            padding=[dp(10), dp(4), dp(10), dp(4)])

        self.chords_carousel = Carousel(direction='right', loop=True,
                                         size_hint=(1, 1), anim_move_duration=0.3)
        self.chords_carousel.bind(current_slide=self._on_carousel_slide)
        self.chord_renderers = []
        self.chord_slides = []

        for i, chord_name in enumerate(self._song_chords):
            slide = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
            renderer = ChordRenderer(size_hint=(1, 1))
            renderer.chord_name = chord_name
            renderer.index = i
            renderer.set_fret_color("black" if theme_id == "light" else "white")
            try:
                griff_data = load_asset_as_bytes("griff_png")
                if griff_data:
                    griff_img = CoreImage(BytesIO(griff_data), ext="png")
                    if griff_img and griff_img.texture:
                        renderer.set_background(griff_img.texture)
            except Exception as e:
                logger.error(f"Ошибка загрузки фона грифа: {e}")
            slide.add_widget(renderer)
            self.chords_carousel.add_widget(slide)
            self.chord_renderers.append(renderer)
            self.chord_slides.append(slide)

        self.griff_container.add_widget(self.chords_carousel)

        self.griff_divider = MDBoxLayout(orientation='horizontal',
                                           size_hint=(1, None), height=dp(2),
                                           md_bg_color=DetailColors.get_divider(theme_id))

        content_scroll = self.content_scroll
        bottom_divider = self.bottom_divider
        if content_scroll in self.song_card.children:
            self.song_card.remove_widget(content_scroll)
        if bottom_divider in self.song_card.children:
            self.song_card.remove_widget(bottom_divider)

        self.song_card.add_widget(self.chord_name_section)
        self.song_card.add_widget(self.griff_container)
        self.song_card.add_widget(self.griff_divider)
        self.song_card.add_widget(content_scroll)
        self.song_card.add_widget(bottom_divider)
        self._griff_added = True

        self._current_chord_index = 0
        if self._song_chords:
            self._load_chord_variants(self._song_chords[0])
            self._update_chords_display()
            if self.chords_carousel and self.chord_slides:
                self.chords_carousel.load_slide(self.chord_slides[0])

    def _on_carousel_slide(self, instance, slide):
        if not self.chord_slides:
            return
        try:
            index = self.chord_slides.index(slide)
            if index != self._current_chord_index:
                self._current_chord_index = index
                self._update_chords_display()
        except ValueError:
            pass

    def _hide_chords_layer(self):
        if not self._griff_added:
            return
        content_scroll = self.content_scroll
        bottom_divider = self.bottom_divider
        for w in (self.chord_name_section, self.griff_container, self.griff_divider):
            if w and w in self.song_card.children:
                self.song_card.remove_widget(w)
        self.chord_name_section = None
        self.griff_container = None
        self.griff_divider = None
        self.chord_name_label = None
        if content_scroll not in self.song_card.children:
            self.song_card.add_widget(content_scroll)
        if bottom_divider not in self.song_card.children:
            self.song_card.add_widget(bottom_divider)
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
        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')
            variants = [c for c in chords_screen.all_chords
                         if c['short_name'].lower() == chord_name.lower()]
            variants.sort(key=lambda x: x['variant'])
            self.chord_variants = variants
            if variants:
                self.load_current_variant()

    def load_current_variant(self):
        if not self.chord_variants:
            return
        variant = self.chord_variants[self.chord_variant_index]
        chord_module = variant.get('module') or variant.get('module_1')
        if not chord_module:
            for key, value in variant.items():
                if 'module' in key.lower() and value:
                    chord_module = value
                    break
        if chord_module and self._current_chord_index < len(self.chord_renderers):
            renderer = self.chord_renderers[self._current_chord_index]
            renderer.load_chord(chord_module)
            renderer.set_mode(self.display_mode)

    def _update_chords_display(self):
        if not self._song_chords:
            return
        chord_name = self._song_chords[self._current_chord_index]
        if self.chord_name_label:
            self.chord_name_label.text = chord_name
        self._load_chord_variants(chord_name)

    def _extract_and_cache_chords(self):
        chords = set()
        for tab in self.tabs:
            content = tab.get('content', '')
            if content:
                cleaned = clean_text(content)
                chords.update(extract_chords_from_text(cleaned))
        self._song_chords = sorted(list(chords))

    def show_tonality_panel(self):
        self.is_tonality_mode = True

    def close_tonality_panel(self):
        self.is_tonality_mode = False

    def apply_tonality(self, step):
        transposed = self.transposed_text_cache.get(step)
        if transposed:
            self.content_label.text = transposed
            self.content_label.markup = True
            self._song_chords = self.transposed_chords_cache.get(step, [])
            if self.is_chords_mode and self.chord_name_label and self._song_chords:
                if self._current_chord_index >= len(self._song_chords):
                    self._current_chord_index = 0
                self._update_chords_display()

    def precompute_transpositions(self, cleaned_text):
        self.original_cleaned_text = cleaned_text
        self.transposed_text_cache[0] = highlight_chords_in_text(cleaned_text)
        self.transposed_chords_cache[0] = self._song_chords.copy()
        for step in [-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3]:
            self.transposed_text_cache[step] = transpose_text(cleaned_text, step)
            self.transposed_chords_cache[step] = transpose_chord_list(self._song_chords, step)

    def show_font_panel(self):
        self.is_font_mode = True

    def close_font_panel(self):
        self.is_font_mode = False

    def _get_font_multiplier(self, font_size):
        ratio = round(font_size / self.STANDARD_FONT_SIZE * 10) / 10
        return f"{int(ratio)}x" if ratio == int(ratio) else f"{ratio:.1f}x"

    def _toggle_theme(self, *args):
        app = MDApp.get_running_app()
        if not app:
            return
        current = settings_manager.theme
        new_theme = 'dark' if current == 'light' else ('green' if current == 'dark' else 'light')
        if hasattr(app, 'apply_theme'):
            app.apply_theme(new_theme)

    def reset_font_size(self):
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'content_label'):
            self.content_label.font_size = self.current_font_size
            self._update_content_height()

    def show_scroll_panel(self):
        self.is_scroll_mode = True
        self.toggle_scroll()

    def close_scroll_panel(self):
        if self.is_scrolling:
            self.stop_scroll()
        self.is_scroll_mode = False

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

        content = MDBoxLayout(orientation='vertical', spacing=dp(8),
                               padding=dp(16), size_hint_y=None, adaptive_height=True)
        for i in range(len(self.tabs)):
            btn = MDRaisedButton(
                text=f"{get_text('variant')} {i + 1}",
                size_hint=(1, None), height=dp(48),
                md_bg_color=accent if i == self.current_tab_index else [0.2, 0.2, 0.2, 0.8],
                text_color=[1, 1, 1, 1],
                on_release=lambda x, idx=i: self._select_tab(idx))
            content.add_widget(btn)
        dialog = MDDialog(title=get_text('choose_chord'), type="custom",
                           content_cls=content,
                           buttons=[MDRaisedButton(text=get_text('close'),
                                                    on_release=lambda x: dialog.dismiss())])
        dialog.open()
        self.tabs_dialog = dialog

    def _select_tab(self, index):
        if hasattr(self, 'tabs_dialog'):
            self.tabs_dialog.dismiss()
        self.current_tab_index = index
        self._load_current_tab()

    def _load_current_tab(self):
        if self.tabs and self.current_tab_index < len(self.tabs):
            cleaned = clean_text(self.tabs[self.current_tab_index].get('content', ''))
            if cleaned:
                self.content_label.text = highlight_chords_in_text(cleaned)
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
        if self.is_tonality_mode: self.close_tonality_panel()
        if self.is_font_mode: self.close_font_panel()
        if self.is_scroll_mode: self.close_scroll_panel()
        self.eye_active = False
        self._current_chord_index = 0
        self.reset_font_size()
        self.display_mode = "finger"
        self.chord_variants = []
        self.chord_variant_index = 0
        self.scroll_speed = 1.0
        self.is_scrolling = False

    def load_song_data(self):
        self.show_loading()
        api.get_tab(song_id=self.song_id,
                     on_success=self.on_song_loaded,
                     on_failure=self.on_load_failed,
                     force_refresh=False)

    def show_loading(self):
        if self.is_loading:
            return
        self.is_loading = True
        self.loading_spinner = LoadingSpinner()
        self.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            self.remove_widget(self.loading_spinner)
            self.loading_spinner = None

    def on_song_loaded(self, data):
        self.song_artist = data.get('artist') or self.song_artist or get_text('unknown_artist')
        self.song_title = data.get('title') or self.song_title or get_text('untitled')
        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'):
            self.tabs = [{'content': data.get('content', '')}]
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
            self.is_favorite = data.get('is_favorite', True)
        self.update_top_nav_title()
        self.hide_loading()
        for delay in [0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]:
            Clock.schedule_once(self._wait_for_ready_and_scroll, delay)

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
            if app and hasattr(app, 'open_profile'):
                app.open_profile()
            return

        def confirm(instance):
            dialog.dismiss()
            self._remove_from_favorites()

        dialog = MDDialog(
            title=get_text('remove_from_favorites'),
            text=f"{self.song_title}",
            buttons=[
                MDRaisedButton(text=get_text('close'), on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text=get_text('reset'),
                                on_release=confirm,
                                md_bg_color=[0.8, 0.3, 0.3, 1]),
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

        api.remove_from_favorites(song_id=self.song_id,
                                    on_success=on_success,
                                    on_failure=on_failure)

    def update_top_nav_title(self):
        app = MDApp.get_running_app()
        if not app or not hasattr(app, 'top_nav'):
            return
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)
        text_s = DetailColors.get_text_secondary(theme_id)

        container = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                                  spacing=dp(2), padding=[dp(8), dp(4), dp(8), dp(4)])
        title = MDLabel(text=self.song_title or get_text('artist_songs'),
                         font_size=sp(18), halign="center", valign="middle",
                         theme_text_color="Custom", text_color=text_p,
                         bold=True, shorten=True, shorten_from="right")
        artist = MDLabel(text=self.song_artist or "",
                          font_size=sp(12), halign="center", valign="middle",
                          theme_text_color="Custom", text_color=text_s,
                          shorten=True, shorten_from="right")
        container.add_widget(title)
        container.add_widget(artist)
        app.top_nav.set_custom_title_widget(container)

    def go_back(self, instance=None):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            app.top_nav.force_update_title(get_text('favorites'), show_back=False)
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('favorites')
        if self.manager and self.manager.has_screen('favorites'):
            self.manager.current = 'favorites'
        else:
            self.manager.current = 'home'

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if hasattr(app.top_nav, 'left_container'):
                app.top_nav.left_container.clear_widgets()
                app.top_nav.left_container.add_widget(app.top_nav.back_btn)
                app.top_nav.back_btn.on_release = self.go_back
            if hasattr(app.top_nav, 'right_container') and hasattr(app.top_nav, 'home_btn'):
                app.top_nav.right_container.clear_widgets()
                app.top_nav.right_container.add_widget(app.top_nav.home_btn)
        if self.song_title:
            self.update_top_nav_title()
        self.update_theme_colors()
        if self._floating_panel:
            def _init_panel(dt):
                self._floating_panel._init_position()
                self._floating_panel.hide()
            Clock.schedule_once(_init_panel, 0.1)

    def on_leave(self):
        logger.info("Выход из FavoriteDetailScreen")