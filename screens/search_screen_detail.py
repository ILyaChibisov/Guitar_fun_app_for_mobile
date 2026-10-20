# screens/search_screen_detail.py
"""
Экран просмотра песни ИЗ ОБЩЕГО ПОИСКА (search_screen).
Полная копия SongDetailScreen с возвратом в SearchScreen (С ЛАЙКОМ).
Адаптирован под 3 темы и 6 языков.
"""
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from io import BytesIO
import re
from kivy.utils import platform

from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.chord_renderer import ChordRenderer
from api.client import api
from utils.notifications import notify
from utils.settings_manager import settings_manager
from utils.localization import get_text
from utils.chord_highlighter import (
    ChordTextLabel,
    highlight_chords_in_text,
    extract_chords_from_text_wrapper as extract_chords_from_text,
)
from utils.transposer import transpose_text, transpose_chord_list

logger = screen_logger('SearchScreenDetail')

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
        return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        return [1, 1, 1, 0.7]

    @staticmethod
    def get_panel_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 0.9]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.08]
        return [0, 0, 0, 0.06]

    @staticmethod
    def get_divider(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 0.1]
        return [0.5, 0.5, 0.5, 0.3]


def clean_text(text):
    """Очищает текст от HTML тегов и специальных символов."""
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


class IconActionButton(MDIconButton):
    def __init__(self, icon_name, on_press_callback=None, icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press_callback
        self.size_hint = (1, None)
        self.height = dp(40)
        self.theme_icon_color = "Custom"
        self.icon_color = icon_color if icon_color else [0.5, 0.5, 0.5, 0.9]
        self.md_bg_color = [0, 0, 0, 0]
        self.icon = icon_name
        self.bind(on_release=self._on_press)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback()


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
            size_hint_y=None, height=dp(30)
        )
        self.add_widget(self.label)

    def start_animation(self):
        pass

    def stop_animation(self):
        pass


class SearchScreenDetail(BaseScreen):
    """
    Экран просмотра песни ИЗ ОБЩЕГО ПОИСКА.
    Адаптирован под 3 темы и 6 языков (С ЛАЙКОМ).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search_screen_detail'
        self._manage_padding_manually = True

        self.song_id = None
        self.song_title = None
        self.song_artist = None
        self.is_favorite = False
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self.texture = None
        self.previous_screen = 'search'
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
        self.chord_pag_prev = None
        self.chord_pag_next = None

        self.transposed_chords_cache = {}
        self.transposed_text_cache = {}
        self.original_cleaned_text = ""

        self.is_tonality_mode = False
        self.is_font_mode = False
        self.is_scroll_mode = False
        self.scroll_speed = 1.0
        self.scroll_animation = None
        self.is_scrolling = False
        self.panel_container = None
        self.current_panel_type = 'main'

        self.chords_btn = None
        self.tonality_btn = None
        self.scroll_btn = None
        self.tabs_btn = None
        self.font_btn = None
        self.favorite_btn = None

        self.load_background()
        self.init_ui()
        logger.info('Экран просмотра песни из общего поиска создан (с лайком)')

    # ============ ФОН ============

    def load_background(self):
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        try:
            if HAS_ASSETS:
                for name in ["background_jpg", "background", "bg", "BACKGROUND_JPG"]:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        img = CoreImage(BytesIO(bg_data), ext="jpg")
                        self.texture = img.texture
                        logger.info(f"Фон загружен: {name}")
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

    # ============ ТЕМА / ЯЗЫК ============

    def update_theme_colors(self):
        self.update_screen_background()
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)
        div_color = DetailColors.get_divider(theme_id)
        panel_bg = DetailColors.get_panel_bg(theme_id)

        if hasattr(self, 'content_label'):
            self.content_label.text_color = text_p
        for div in (getattr(self, 'top_divider', None),
                    getattr(self, 'panel_divider', None),
                    getattr(self, 'bottom_divider', None)):
            if div:
                div.md_bg_color = div_color
        if self.panel_container:
            self.panel_container.md_bg_color = panel_bg
        if hasattr(self, 'griff_divider') and self.griff_divider:
            self.griff_divider.md_bg_color = div_color
        if hasattr(self, 'chord_name_label') and self.chord_name_label:
            self.chord_name_label.text_color = text_p

        if self.chord_renderers:
            fret_color = "black" if theme_id == "light" else "white"
            for r in self.chord_renderers:
                try:
                    r.set_fret_color(fret_color)
                except Exception:
                    pass
        self._rebuild_current_panel()

    def _rebuild_current_panel(self):
        pt = self.current_panel_type
        if pt == 'main':
            self._create_main_panel()
        elif pt == 'chords' and self.is_chords_mode:
            self._create_chords_panel()
        elif pt == 'tonality' and self.is_tonality_mode:
            self._create_tonality_panel()
        elif pt == 'font' and self.is_font_mode:
            self._create_font_panel()
        elif pt == 'scroll' and self.is_scroll_mode:
            self._create_scroll_panel()

    def update_language(self):
        if self.song_title:
            self.update_top_nav_title()

    # ============ UI ============

    def init_ui(self):
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
        top_offset = layout_config.get_top_padding(include_top_nav=True)
        bottom_nav_total = layout_config.get_bottom_nav_total_height()

        card_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            padding=[0, top_offset, 0, 0]
        )

        self.song_card = MDCard(
            orientation='vertical', size_hint=(1, 1),
            padding=[0, 0, 0, bottom_nav_total], spacing=0,
            radius=[0, 0, 0, 0], md_bg_color=[0, 0, 0, 0], elevation=0
        )

        self.top_divider = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(2)
        )
        self.song_card.add_widget(self.top_divider)

        self.panel_container = MDCard(
            orientation='vertical', size_hint=(1, None), height=dp(52),
            elevation=0, radius=[0, 0, 0, 0], padding=[0, 0, 0, 0], spacing=0
        )
        self.song_card.add_widget(self.panel_container)

        self.panel_divider = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(2)
        )
        self.song_card.add_widget(self.panel_divider)

        self.content_scroll = MDScrollView(
            size_hint=(1, 1), do_scroll_x=False, bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.3],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        self._text_container = MDBoxLayout(
            orientation='vertical', size_hint_y=None, spacing=4,
            padding=[dp(16), dp(16), dp(16), dp(4)],
            adaptive_height=True, md_bg_color=[0, 0, 0, 0]
        )

        self.content_label = ChordTextLabel(
            text="", font_size=self.current_font_size, size_hint_y=None,
            theme_text_color="Custom", valign="top", line_height=1.5, markup=True
        )
        self.content_label.bind(texture_size=self._update_content_height)
        self._text_container.add_widget(self.content_label)

        self.content_scroll.add_widget(self._text_container)
        self.song_card.add_widget(self.content_scroll)

        self.bottom_divider = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(2)
        )
        self.song_card.add_widget(self.bottom_divider)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)
        self.add_widget(main_container)

        self._create_main_panel()
        Clock.schedule_once(lambda dt: self._update_card_size(), 0.1)
        Clock.schedule_once(lambda dt: self._update_card_size(), 0.3)
        Clock.schedule_once(lambda dt: self.update_theme_colors(), 0.2)

    def _update_card_size(self, *args):
        if hasattr(self, 'song_card') and self.song_card:
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
            if hasattr(self.content_label.parent, 'minimum_height'):
                self.content_label.parent.minimum_height = text_height + dp(16)
        self.content_scroll.scroll_y = 1.0

    # ============ ОСНОВНАЯ ПАНЕЛЬ ============

    def _create_main_panel(self):
        if not self.panel_container:
            return
        self.panel_container.clear_widgets()
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)
        secondary = DetailColors.get_text_secondary(theme_id)

        panel = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            padding=[dp(2)] * 4, spacing=dp(1)
        )

        self.chords_btn = IconActionButton("music", self.on_chords_press, accent)
        self.tonality_btn = IconActionButton("tune", self.show_tonality_panel, accent)
        self.scroll_btn = IconActionButton("play-circle", self.show_scroll_panel, accent)
        self.tabs_btn = IconActionButton("folder-music", self.show_tabs_picker, secondary)
        self.font_btn = IconActionButton("cog", self.show_font_panel, accent)
        self.favorite_btn = IconActionButton(
            "star" if self.is_favorite else "star-outline",
            self.toggle_favorite, accent
        )

        for btn in (self.chords_btn, self.tonality_btn, self.scroll_btn,
                    self.tabs_btn, self.font_btn, self.favorite_btn):
            panel.add_widget(btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'main'

    # ============ АККОРДЫ ============

    def on_chords_press(self):
        self.show_chords_section()

    def show_chords_section(self):
        if self.is_tonality_mode:
            self.close_tonality_panel()
        if self.is_font_mode:
            self.close_font_panel()
        if self.is_scroll_mode:
            self.close_scroll_panel()
        if not self._song_chords:
            notify.info(get_text('no_chords'))
            return
        if self.is_chords_mode:
            self.close_chords_section()
            return
        self._create_chords_panel()
        self.is_chords_mode = True
        self._show_chords_layer()

    def _create_chords_panel(self):
        self.panel_container.clear_widgets()
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)
        secondary = DetailColors.get_text_secondary(theme_id)

        panel = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            padding=[dp(2)] * 4, spacing=dp(1)
        )

        self.variant_btn = MDIconButton(
            icon="format-list-bulleted-square", size_hint=(1, None),
            height=dp(40), theme_icon_color="Custom", icon_color=accent,
            md_bg_color=[0, 0, 0, 0], on_release=self._next_chord_variant,
            ripple_scale=0
        )
        self.mode_btn = MDIconButton(
            icon="music-note", size_hint=(1, None), height=dp(40),
            theme_icon_color="Custom", icon_color=accent,
            md_bg_color=[0, 0, 0, 0], on_release=self._toggle_display_mode,
            ripple_scale=0
        )
        self.eye_btn = MDIconButton(
            icon="eye", size_hint=(1, None), height=dp(40),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.2, 0.2, 1] if self.eye_active else secondary,
            md_bg_color=[0, 0, 0, 0], on_release=self._toggle_eye,
            ripple_scale=0
        )
        self.griff_zoom_btn = MDIconButton(
            icon="magnify", size_hint=(1, None), height=dp(40),
            theme_icon_color="Custom", icon_color=accent,
            md_bg_color=[0, 0, 0, 0], on_release=self._toggle_griff_zoom,
            ripple_scale=0
        )
        self.chords_close_btn = MDIconButton(
            icon="check", size_hint=(1, None), height=dp(40),
            theme_icon_color="Custom", icon_color=accent,
            md_bg_color=[0, 0, 0, 0], on_release=self.close_chords_section,
            ripple_scale=0
        )

        for btn in (self.variant_btn, self.mode_btn, self.eye_btn,
                    self.griff_zoom_btn, self.chords_close_btn):
            panel.add_widget(btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'chords'

    def _show_chords_layer(self):
        if self._griff_added:
            return
        from kivy.uix.carousel import Carousel
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)
        secondary = DetailColors.get_text_secondary(theme_id)

        self.chord_name_section = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(30),
            padding=[dp(8), dp(2), dp(8), dp(2)], spacing=dp(4)
        )
        self.chord_pag_prev = MDIconButton(
            icon="chevron-left", size_hint=(None, 1), width=dp(24),
            theme_icon_color="Custom", icon_color=secondary,
            md_bg_color=[0, 0, 0, 0], ripple_scale=0
        )
        self.chord_name_label = MDLabel(
            text="", halign="center", valign="middle", size_hint_x=1,
            theme_text_color="Custom", text_color=text_p,
            bold=True, font_size=sp(18)
        )
        self.chord_pag_next = MDIconButton(
            icon="chevron-right", size_hint=(None, 1), width=dp(24),
            theme_icon_color="Custom", icon_color=secondary,
            md_bg_color=[0, 0, 0, 0], ripple_scale=0
        )
        self.chord_name_section.add_widget(self.chord_pag_prev)
        self.chord_name_section.add_widget(self.chord_name_label)
        self.chord_name_section.add_widget(self.chord_pag_next)

        self.griff_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(120),
            padding=[dp(10), dp(4), dp(10), dp(4)]
        )

        self.chords_carousel = Carousel(
            direction='right', loop=True, size_hint=(1, 1), anim_move_duration=0.3
        )
        self.chords_carousel.bind(current_slide=self._on_carousel_slide)
        self.chord_renderers = []
        self.chord_slides = []

        for i, chord_name in enumerate(self._song_chords):
            slide = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
            renderer = ChordRenderer(size_hint=(1, 1))
            renderer.chord_name = chord_name
            renderer.index = i
            try:
                renderer.set_fret_color("black" if theme_id == "light" else "white")
            except Exception:
                pass
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

        self.griff_divider = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(2),
            md_bg_color=DetailColors.get_divider(theme_id)
        )

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
        self.chord_pag_prev = None
        self.chord_pag_next = None
        if content_scroll not in self.song_card.children:
            self.song_card.add_widget(content_scroll)
        if bottom_divider not in self.song_card.children:
            self.song_card.add_widget(bottom_divider)
        self.chords_carousel = None
        self.chord_renderers = []
        self.chord_slides = []
        self._griff_added = False

    def close_chords_section(self, *args):
        if self.eye_active:
            self._create_main_panel()
            self.is_chords_mode = False
            return
        self._create_main_panel()
        self.is_chords_mode = False
        self._hide_chords_layer()

    def _toggle_eye(self, *args):
        self.eye_active = not self.eye_active
        theme_id = settings_manager.theme
        self.eye_btn.icon_color = (
            [0.8, 0.2, 0.2, 1] if self.eye_active
            else DetailColors.get_text_secondary(theme_id)
        )

    def _toggle_display_mode(self, *args):
        accent = DetailColors.get_accent(settings_manager.theme)
        if self.display_mode == "finger":
            self.display_mode = "notes"
            self.mode_btn.icon = "gesture-tap"
        else:
            self.display_mode = "finger"
            self.mode_btn.icon = "music-note"
        self.mode_btn.icon_color = accent
        if self._current_chord_index < len(self.chord_renderers):
            self.chord_renderers[self._current_chord_index].set_mode(self.display_mode)

    def _toggle_griff_zoom(self, *args):
        if not self.griff_container:
            return
        zoom_levels = [1.0, 1.3, 1.6]
        current = self.griff_scale
        if current in zoom_levels:
            next_index = (zoom_levels.index(current) + 1) % len(zoom_levels)
            new_scale = zoom_levels[next_index]
        else:
            new_scale = 1.0
        self.griff_scale = new_scale
        self.griff_container.height = int(dp(120) * new_scale)
        accent = DetailColors.get_accent(settings_manager.theme)
        self.griff_zoom_btn.icon = "magnify" if new_scale == 1.0 else "magnify-plus"
        self.griff_zoom_btn.icon_color = accent

    def _load_chord_variants(self, chord_name):
        self.chord_variants = []
        self.chord_variant_index = 0
        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')
            variants = [
                c for c in chords_screen.all_chords
                if c['short_name'].lower() == chord_name.lower()
            ]
            variants.sort(key=lambda x: x['variant'])
            self.chord_variants = variants
            self._update_variant_icon()
            if variants:
                self.load_current_variant()

    def _update_variant_icon(self):
        if hasattr(self, 'variant_btn'):
            self.variant_btn.opacity = 0.5 if len(self.chord_variants) <= 1 else 1

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
        self._update_variant_icon()

    def _next_chord_variant(self, *args):
        if not self.chord_variants:
            return
        self.chord_variant_index = (
            (self.chord_variant_index + 1) % len(self.chord_variants)
        )
        self.load_current_variant()

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

    # ============ ТОНАЛЬНОСТЬ ============

    def show_tonality_panel(self):
        if self.is_chords_mode:
            self.close_chords_section()
        if self.is_font_mode:
            self.close_font_panel()
        if self.is_scroll_mode:
            self.close_scroll_panel()
        self._create_tonality_panel()
        self.is_tonality_mode = True

    def close_tonality_panel(self):
        self._create_main_panel()
        self.is_tonality_mode = False

    def _create_tonality_panel(self):
        self.panel_container.clear_widgets()
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)
        text_p = DetailColors.get_text_primary(theme_id)

        panel = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)], spacing=dp(4)
        )

        title_label = MDLabel(
            text=get_text('tonality'), font_size=sp(12), halign="left",
            valign="middle", size_hint_x=None, width=dp(100),
            theme_text_color="Custom", text_color=text_p, bold=True
        )

        center_container = MDBoxLayout(
            orientation='vertical', size_hint_x=1, spacing=0
        )
        from kivymd.uix.slider import MDSlider
        current_slider_value = int(round(self.current_tonality * 2))

        top_row = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(14), spacing=0
        )
        minus_label = MDLabel(
            text="-", font_size=sp(12), halign="center", valign="bottom",
            size_hint_x=None, width=dp(20), theme_text_color="Custom",
            text_color=[0.8, 0.3, 0.3, 0.9], bold=True
        )
        self.tonality_value_label = MDLabel(
            text="0" if current_slider_value == 0 else f"{current_slider_value:+d}",
            font_size=sp(10), halign="center", valign="bottom",
            size_hint_x=1, theme_text_color="Custom", bold=True
        )
        self._update_tonality_label_color(current_slider_value)
        plus_label = MDLabel(
            text="+", font_size=sp(12), halign="center", valign="bottom",
            size_hint_x=None, width=dp(20), theme_text_color="Custom",
            text_color=[0.3, 0.7, 0.3, 0.9], bold=True
        )
        top_row.add_widget(minus_label)
        top_row.add_widget(self.tonality_value_label)
        top_row.add_widget(plus_label)

        slider_container = MDBoxLayout(
            orientation='horizontal', size_hint_x=1, size_hint_y=None,
            height=dp(28), padding=[dp(2), 0, dp(2), 0]
        )
        self.tonality_slider = MDSlider(
            min=-6.01, max=6.01, value=current_slider_value, step=1,
            size_hint_x=1, size_hint_y=None, height=dp(28), hint=False
        )
        self.tonality_slider.ripple_scale = 0
        self.tonality_slider.thumb_color_active = accent
        self.tonality_slider.thumb_color_inactive = accent
        self.tonality_slider.thumb_color_disabled = accent
        self.tonality_slider.track_color_active = accent[:3] + [0.5]
        self.tonality_slider.track_color_inactive = [0.85, 0.85, 0.85, 1]
        self.tonality_slider.color = accent
        slider_container.add_widget(self.tonality_slider)

        def on_slider_change(instance, value):
            if value < -6:
                int_value = -6
            elif value > 6:
                int_value = 6
            else:
                int_value = int(round(value))
            if self.tonality_slider.value != int_value:
                self.tonality_slider.value = int_value
            self.tonality_value_label.text = "0" if int_value == 0 else f"{int_value:+d}"
            self._update_tonality_label_color(int_value)
            step = int_value / 2
            if step != self.current_tonality:
                self.current_tonality = step
                self.apply_tonality(self.current_tonality)

        self.tonality_slider.bind(value=on_slider_change)
        minus_label.bind(
            on_touch_down=lambda w, t: setattr(
                self.tonality_slider, 'value', max(-6, self.tonality_slider.value - 1)
            )
        )
        plus_label.bind(
            on_touch_down=lambda w, t: setattr(
                self.tonality_slider, 'value', min(6, self.tonality_slider.value + 1)
            )
        )

        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        self.tonality_apply_btn = IconActionButton("check", self.close_tonality_panel, accent)
        self.tonality_apply_btn.size_hint = (None, None)
        self.tonality_apply_btn.size = (dp(36), dp(36))

        panel.add_widget(title_label)
        panel.add_widget(center_container)
        panel.add_widget(self.tonality_apply_btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'tonality'

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

    def _update_tonality_label_color(self, value):
        if not hasattr(self, 'tonality_value_label'):
            return
        if value < 0:
            self.tonality_value_label.text_color = [0.8, 0.3, 0.3, 1]
        elif value > 0:
            self.tonality_value_label.text_color = [0.3, 0.7, 0.3, 1]
        else:
            self.tonality_value_label.text_color = DetailColors.get_accent(
                settings_manager.theme
            )

    def precompute_transpositions(self, cleaned_text):
        self.original_cleaned_text = cleaned_text
        self.transposed_text_cache[0] = highlight_chords_in_text(cleaned_text)
        self.transposed_chords_cache[0] = self._song_chords.copy()
        for step in [-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3]:
            self.transposed_text_cache[step] = transpose_text(cleaned_text, step)
            self.transposed_chords_cache[step] = transpose_chord_list(
                self._song_chords, step
            )

    # ============ ШРИФТ ============

    def show_font_panel(self):
        if self.is_chords_mode:
            self.close_chords_section()
        if self.is_tonality_mode:
            self.close_tonality_panel()
        if self.is_scroll_mode:
            self.close_scroll_panel()
        self._create_font_panel()
        self.is_font_mode = True

    def close_font_panel(self):
        self._create_main_panel()
        self.is_font_mode = False

    def _create_font_panel(self):
        self.panel_container.clear_widgets()
        theme_id = settings_manager.theme
        accent = DetailColors.get_accent(theme_id)

        panel = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)], spacing=dp(2)
        )
        center_container = MDBoxLayout(
            orientation='vertical', size_hint_x=1, spacing=0
        )
        from kivymd.uix.slider import MDSlider

        if platform == 'android':
            font_sizes = [30, 34, 38, 42, 46, 50, 54, 58, 60]
        else:
            font_sizes = [14, 16, 18, 20, 22, 24, 26, 28, 30, 32]
        total_steps = len(font_sizes) - 1

        def size_to_slider(size):
            try:
                return font_sizes.index(size)
            except ValueError:
                return font_sizes.index(min(font_sizes, key=lambda x: abs(x - size)))

        def slider_to_size(value):
            idx = max(0, min(total_steps, int(round(value))))
            return font_sizes[idx]

        current_slider_value = size_to_slider(self.current_font_size)

        top_row = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(14), spacing=0
        )
        top_row.add_widget(MDLabel(text="", size_hint_x=None, width=dp(2)))
        self.font_value_label = MDLabel(
            text=self._get_font_multiplier(self.current_font_size),
            font_size=sp(10), halign="center", valign="bottom",
            size_hint_x=1, theme_text_color="Custom",
            text_color=accent, bold=True
        )
        top_row.add_widget(self.font_value_label)
        top_row.add_widget(MDLabel(text="", size_hint_x=None, width=dp(2)))

        slider_container = MDBoxLayout(
            orientation='horizontal', size_hint_x=1, size_hint_y=None,
            height=dp(28), padding=[dp(2), 0, dp(2), 0]
        )
        self.font_slider = MDSlider(
            min=-0.01, max=float(total_steps + 0.01),
            value=current_slider_value, step=1,
            size_hint_x=1, size_hint_y=None, height=dp(28), hint=False
        )
        self.font_slider.ripple_scale = 0
        self.font_slider.thumb_color_active = accent
        self.font_slider.thumb_color_inactive = accent
        self.font_slider.thumb_color_disabled = accent
        self.font_slider.track_color_active = accent[:3] + [0.6]
        self.font_slider.track_color_inactive = [1, 1, 1, 0.3]
        self.font_slider.color = accent

        def on_slider_change(instance, value):
            int_value = max(0, min(total_steps, int(round(value))))
            if self.font_slider.value != int_value:
                self.font_slider.value = int_value
            self.font_slider.thumb_color_active = accent
            self.font_slider.thumb_color_inactive = accent
            self.font_slider.thumb_color_disabled = accent
            new_size = slider_to_size(int_value)
            if self.current_font_size != new_size:
                self.current_font_size = new_size
                self.font_value_label.text = self._get_font_multiplier(new_size)
                self.content_label.font_size = new_size
                self._update_content_height()
                for delay in [0.0, 0.01, 0.03, 0.05, 0.08, 0.12, 0.2, 0.3, 0.5, 0.8]:
                    Clock.schedule_once(
                        lambda dt: setattr(self.content_scroll, 'scroll_y', 1.0),
                        delay
                    )

        self.font_slider.bind(value=on_slider_change)
        slider_container.add_widget(self.font_slider)
        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        right_buttons = MDBoxLayout(
            orientation='horizontal', size_hint=(None, 1), width=dp(80), spacing=dp(4)
        )
        self.theme_btn = IconActionButton("weather-sunny", self._toggle_theme, accent)
        self.font_apply_btn = IconActionButton("check", self.close_font_panel, accent)
        right_buttons.add_widget(self.theme_btn)
        right_buttons.add_widget(self.font_apply_btn)

        panel.add_widget(center_container)
        panel.add_widget(right_buttons)
        self.panel_container.add_widget(panel)
        self.current_panel_type = 'font'

        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.1)
        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.3)

    def _toggle_theme(self, *args):
        """Переключение глобальной темы через settings_manager."""
        order = ['green', 'light', 'dark']
        cur = settings_manager.theme
        try:
            idx = order.index(cur)
        except ValueError:
            idx = 0
        new_theme = order[(idx + 1) % len(order)]
        settings_manager.theme = new_theme
        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_theme'):
            app.apply_theme()
        else:
            self.update_theme_colors()

    def _fix_slider_thumb(self, slider):
        if slider:
            accent = DetailColors.get_accent(settings_manager.theme)
            slider.thumb_color_active = accent
            slider.thumb_color_inactive = accent
            slider.thumb_color_disabled = accent
            current = slider.value
            slider.value = current + 0.01
            Clock.schedule_once(lambda dt: setattr(slider, 'value', current), 0.01)

    def _get_font_multiplier(self, font_size):
        ratio = round(font_size / self.STANDARD_FONT_SIZE * 10) / 10
        return f"{int(ratio)}x" if ratio == int(ratio) else f"{ratio:.1f}x"

    def reset_font_size(self):
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'content_label'):
            self.content_label.font_size = self.current_font_size
            self._update_content_height()

    # ============ ПРОКРУТКА ============

    def show_scroll_panel(self):
        if self.is_chords_mode:
            self.close_chords_section()
        if self.is_tonality_mode:
            self.close_tonality_panel()
        if self.is_font_mode:
            self.close_font_panel()
        self._create_scroll_panel()
        self.is_scroll_mode = True

    def close_scroll_panel(self):
        if self.is_scrolling:
            self.stop_scroll()
        self._create_main_panel()
        self.is_scroll_mode = False

    def _create_scroll_panel(self):
        self.panel_container.clear_widgets()
        accent = DetailColors.get_accent(settings_manager.theme)

        panel = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)], spacing=dp(4)
        )
        center_container = MDBoxLayout(
            orientation='vertical', size_hint_x=1, spacing=0
        )
        from kivymd.uix.slider import MDSlider

        def speed_to_slider(speed):
            return int(1 + (speed - 0.2) / 0.03) if speed <= 0.5 else int(10 + (speed - 0.5) / 0.1)

        def slider_to_speed(value):
            return 0.2 + (value - 1) * 0.03 if value <= 10 else 0.5 + (value - 10) * 0.1

        current_slider_value = speed_to_slider(self.scroll_speed)

        top_row = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(14), spacing=0
        )
        top_row.add_widget(MDLabel(text="", size_hint_x=None, width=dp(4)))
        self.scroll_speed_value_label = MDLabel(
            text=f"{self.scroll_speed:.1f}x", font_size=sp(10),
            halign="center", valign="bottom", size_hint_x=1,
            theme_text_color="Custom", text_color=accent, bold=True
        )
        top_row.add_widget(self.scroll_speed_value_label)
        top_row.add_widget(MDLabel(text="", size_hint_x=None, width=dp(4)))

        slider_container = MDBoxLayout(
            orientation='horizontal', size_hint_x=1, size_hint_y=None,
            height=dp(28), padding=[dp(2), 0, dp(2), 0]
        )
        self.scroll_speed_slider = MDSlider(
            min=0.99, max=28.01, value=current_slider_value, step=1,
            size_hint_x=1, size_hint_y=None, height=dp(28), hint=False
        )
        self.scroll_speed_slider.ripple_scale = 0
        self.scroll_speed_slider.thumb_color_active = accent
        self.scroll_speed_slider.thumb_color_inactive = accent
        self.scroll_speed_slider.thumb_color_disabled = accent
        self.scroll_speed_slider.track_color_active = accent[:3] + [0.6]
        self.scroll_speed_slider.track_color_inactive = [1, 1, 1, 0.3]
        self.scroll_speed_slider.color = accent

        def on_slider_change(instance, value):
            int_value = max(1, min(28, int(round(value))))
            if self.scroll_speed_slider.value != int_value:
                self.scroll_speed_slider.value = int_value
            self.scroll_speed = slider_to_speed(int_value)
            self.scroll_speed_value_label.text = f"{self.scroll_speed:.1f}x"
            if self.is_scrolling:
                self.stop_scroll()
                self.start_scroll()

        self.scroll_speed_slider.bind(value=on_slider_change)
        slider_container.add_widget(self.scroll_speed_slider)
        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        buttons_container = MDBoxLayout(
            orientation='horizontal', size_hint=(None, 1), width=dp(80), spacing=dp(2)
        )
        self.play_pause_btn = IconActionButton("play", self.toggle_scroll, accent)
        self.stop_btn = IconActionButton(
            "stop", self.reset_scroll_position, [0.8, 0.3, 0.3, 0.9]
        )
        buttons_container.add_widget(self.play_pause_btn)
        buttons_container.add_widget(self.stop_btn)

        self.scroll_close_btn = IconActionButton("check", self.close_scroll_panel, accent)
        self.scroll_close_btn.size_hint = (None, None)
        self.scroll_close_btn.size = (dp(36), dp(36))

        panel.add_widget(center_container)
        panel.add_widget(buttons_container)
        panel.add_widget(self.scroll_close_btn)
        self.panel_container.add_widget(panel)
        self.current_panel_type = 'scroll'

    def toggle_scroll(self):
        if not self.is_scrolling and self.content_scroll.scroll_y <= 0.01:
            self.reset_scroll_position()
        if not self.is_scrolling:
            self.start_scroll()
            self.play_pause_btn.icon = "pause"
        else:
            self.stop_scroll()
            self.play_pause_btn.icon = "play"

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
                self.play_pause_btn.icon = "play"
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
            self.play_pause_btn.icon = "play"
        self.content_scroll.scroll_y = 1.0

    # ============ ВЫБОР ПОДБОРА ============

    def show_tabs_picker(self):
        if not self.tabs or len(self.tabs) <= 1:
            notify.info(get_text('no_variants'))
            return
        accent = DetailColors.get_accent(settings_manager.theme)

        content = MDBoxLayout(
            orientation='vertical', spacing=dp(8), padding=dp(16),
            size_hint_y=None, adaptive_height=True
        )
        for i, tab in enumerate(self.tabs):
            btn = MDRaisedButton(
                text=f"{get_text('variant')} {i + 1}",
                size_hint=(1, None), height=dp(48),
                md_bg_color=accent if i == self.current_tab_index else [0.2, 0.2, 0.2, 0.8],
                text_color=[1, 1, 1, 1],
                on_release=lambda x, idx=i: self._select_tab(idx)
            )
            content.add_widget(btn)
        dialog = MDDialog(
            title=get_text('choose_chord'), type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(
                text=get_text('close'),
                on_release=lambda x: dialog.dismiss()
            )]
        )
        dialog.open()
        self.tabs_dialog = dialog

    def _select_tab(self, index):
        if hasattr(self, 'tabs_dialog'):
            self.tabs_dialog.dismiss()
        self.current_tab_index = index
        self._load_current_tab()

    def _load_current_tab(self):
        if self.tabs and self.current_tab_index < len(self.tabs):
            tab = self.tabs[self.current_tab_index]
            cleaned = clean_text(tab.get('content', ''))
            if cleaned:
                self.content_label.text = highlight_chords_in_text(cleaned)
                self.content_label.markup = True
            else:
                self.content_label.text = get_text('loading_error')
                self.content_label.markup = False
            self._update_content_height()
            Clock.schedule_once(
                lambda dt: setattr(self.content_scroll, 'scroll_y', 1), 0.1
            )

    # ============ ЖИЗНЕННЫЙ ЦИКЛ / ДАННЫЕ ============

    def set_song(self, song_id, artist="", title=""):
        self.song_id = song_id
        self.song_artist = artist
        self.song_title = title
        self.reset_screen_state()
        self.load_song_data()

    def reset_screen_state(self):
        self.current_tonality = 0
        self.transposed_chords_cache = {}
        self.transposed_text_cache = {}
        self.original_cleaned_text = ""

        if self.is_chords_mode:
            self.close_chords_section()
        if self.is_tonality_mode:
            self.close_tonality_panel()
        if self.is_font_mode:
            self.close_font_panel()
        if self.is_scroll_mode:
            self.close_scroll_panel()

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

        self.is_favorite = data.get('is_favorite', False)
        if hasattr(api, 'is_song_favorited'):
            try:
                self.is_favorite = api.is_song_favorited(self.song_id)
            except Exception:
                pass
        if self.favorite_btn:
            self.favorite_btn.icon = "star" if self.is_favorite else "star-outline"

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

    # ============ ЛАЙК ============

    def toggle_favorite(self, *args):
        if not api.is_authenticated():
            app = MDApp.get_running_app()
            if app and hasattr(app, 'open_profile'):
                app.open_profile()
            return

        if self.is_favorite:
            def on_success(result):
                self.is_favorite = False
                if self.favorite_btn:
                    self.favorite_btn.icon = "star-outline"
                notify.success(get_text('favorite_removed'))

            def on_failure(req, error):
                self.is_favorite = True
                if self.favorite_btn:
                    self.favorite_btn.icon = "star"
                notify.error(get_text('favorite_error'))

            api.remove_from_favorites(
                song_id=self.song_id,
                on_success=on_success,
                on_failure=on_failure
            )
        else:
            def on_success(result):
                self.is_favorite = True
                if self.favorite_btn:
                    self.favorite_btn.icon = "star"
                notify.success(get_text('favorite_added'))

            def on_failure(req, error):
                self.is_favorite = False
                if self.favorite_btn:
                    self.favorite_btn.icon = "star-outline"
                notify.error(get_text('favorite_error'))

            api.add_to_favorites(
                song_id=self.song_id,
                song_data={
                    'artist': self.song_artist or '',
                    'title': self.song_title or '',
                },
                on_success=on_success,
                on_failure=on_failure
            )

    # ============ TOP NAV ============

    def update_top_nav_title(self):
        app = MDApp.get_running_app()
        if not app or not hasattr(app, 'top_nav'):
            return
        theme_id = settings_manager.theme
        text_p = DetailColors.get_text_primary(theme_id)
        text_s = DetailColors.get_text_secondary(theme_id)

        container = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1), spacing=dp(2),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )
        title = MDLabel(
            text=self.song_title or get_text('songs'),
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

    def go_back(self, instance=None):
        logger.info("Возврат из общего поиска в SearchScreen")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('search')

        if self.manager and self.manager.has_screen('search'):
            self.manager.current = 'search'
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

    def on_leave(self):
        pass