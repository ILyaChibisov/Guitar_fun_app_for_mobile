# screens/search_detail_screen.py
"""
Экран просмотра песни ИЗ ПОИСКА (songs_screen)
Возврат только в SongsScreen с сохранением результатов поиска
Полная копия SongDetailScreen с возвратом в SongsScreen
"""
from kivymd.app import MDApp
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
from kivy.uix.behaviors import ButtonBehavior
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
from utils.chord_highlighter import (
    ChordTextLabel,
    highlight_chords_in_text,
    extract_chords_from_text_wrapper as extract_chords_from_text,
    init_chord_patterns,
    CHORD_PATTERN
)
from utils.transposer import transpose_text, transpose_chord_list, set_transpose_system

logger = screen_logger('SearchDetail')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


def clean_text(text):
    """Очищает текст от HTML тегов и специальных символов"""
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
    """Кнопка действия в верхней панели"""

    def __init__(self, icon_name, on_press_callback=None, icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press_callback
        self.size_hint = (1, None)
        self.height = dp(40)
        self.theme_icon_color = "Custom"
        if icon_color:
            self.icon_color = icon_color
        else:
            self.icon_color = [0.5, 0.5, 0.5, 0.9]
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
        self.progress = None
        self.anim = None
        self.label = MDLabel(
            text="Загрузка...",
            halign="center",
            font_size=sp(16),
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(self.label)

    def start_animation(self):
        pass

    def stop_animation(self):
        pass


class SearchDetailScreen(BaseScreen):
    """
    Экран просмотра песни ИЗ ПОИСКА (songs_screen)
    Полная копия SongDetailScreen с возвратом в SongsScreen
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search_detail'
        self.song_id = None
        self.song_title = None
        self.song_artist = None
        self.is_liked = False
        self.is_favorite = False
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.previous_screen = 'songs'
        self.current_tonality = 0
        self.tabs = []
        self.current_tab_index = 0

        # Настройки размера шрифта
        if platform == 'android':
            self.STANDARD_FONT_SIZE = 42
            self.MIN_FONT_SIZE = 30
            self.MAX_FONT_SIZE = 60
        else:
            self.STANDARD_FONT_SIZE = 20
            self.MIN_FONT_SIZE = 14
            self.MAX_FONT_SIZE = 32
        self.current_font_size = self.STANDARD_FONT_SIZE

        # Для смены темы текста
        self.is_light_theme = False

        # Для меню аккордов
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

        # Секция с названием аккорда
        self.chord_name_section = None
        self.chord_name_label = None
        self.chord_pag_prev = None
        self.chord_pag_next = None

        # Для кэширования транспонирования
        self.transposed_chords_cache = {}
        self.transposed_text_cache = {}
        self.original_cleaned_text = ""

        # Для панели тональности
        self.is_tonality_mode = False

        # Для панели шрифта
        self.is_font_mode = False

        # Для автопрокрутки текста
        self.is_scroll_mode = False
        self.scroll_speed = 1.0
        self.scroll_animation = None
        self.is_scrolling = False

        # Панель-контейнер
        self.panel_container = None
        self.current_panel_type = 'main'

        # Кнопки для панели (как в SongDetailScreen)
        self.chords_btn = None
        self.tonality_btn = None
        self.scroll_btn = None
        self.tabs_btn = None
        self.font_btn = None
        self.favorite_btn = None
        self.like_btn = None

        self.init_ui()
        self.load_background()
        logger.info('Экран поискового просмотра песни создан')

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

    def _toggle_theme(self, *args):
        if not hasattr(self, '_current_theme'):
            self._current_theme = 'green'

        if self._current_theme == 'green':
            self._set_light_theme()
            self._current_theme = 'light'
        elif self._current_theme == 'light':
            self._set_dark_theme()
            self._current_theme = 'dark'
        else:
            self._set_green_theme()
            self._current_theme = 'green'

        if hasattr(self, 'theme_btn'):
            if self._current_theme == 'green':
                self.theme_btn.icon = "weather-sunny"
                self.theme_btn.icon_color = [0.46, 0.70, 0.71, 1]
            elif self._current_theme == 'light':
                self.theme_btn.icon = "white-balance-sunny"
                self.theme_btn.icon_color = [1, 1, 1, 1]
            else:
                self.theme_btn.icon = "weather-night"
                self.theme_btn.icon_color = [0.3, 0.3, 0.3, 1]

    def _set_green_theme(self):
        self.is_light_theme = False
        self.content_label.text_color = [1, 1, 1, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [0, 0, 0, 0]
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "weather-sunny"
            self.theme_btn.icon_color = [0.46, 0.70, 0.71, 1]

    def _set_light_theme(self):
        self.is_light_theme = True
        self.content_label.text_color = [0, 0, 0, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [1, 1, 1, 1]
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "white-balance-sunny"
            self.theme_btn.icon_color = [1, 1, 1, 1]

    def _set_dark_theme(self):
        self.is_light_theme = False
        self.content_label.text_color = [1, 1, 1, 0.95]
        if hasattr(self, '_text_container') and self._text_container:
            self._text_container.md_bg_color = [0.05, 0.05, 0.05, 1]
        if hasattr(self, 'theme_btn'):
            self.theme_btn.icon = "weather-night"
            self.theme_btn.icon_color = [0.3, 0.3, 0.3, 1]

    def init_ui(self):
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 0, 0, 0])

        top_padding_for_nav = layout_config.get_top_padding()
        if platform == 'android':
            min_top_padding = dp(48)
            if top_padding_for_nav < min_top_padding:
                top_padding_for_nav = min_top_padding
            else:
                top_padding_for_nav = top_padding_for_nav + dp(8)

        self._top_spacer_song = Widget(size_hint_y=None, height=top_padding_for_nav)
        main_container.add_widget(self._top_spacer_song)

        bottom_nav_total = layout_config.get_bottom_nav_total_height()
        bottom_padding_for_card = bottom_nav_total

        card_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1), padding=[0, 0, 0, 0])

        self.song_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, bottom_padding_for_card],
            spacing=0,
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0
        )

        self.top_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
        )
        self.song_card.add_widget(self.top_divider)

        self.panel_container = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(52),
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            radius=[0, 0, 0, 0],
            padding=[0, 0, 0, 0],
            spacing=0
        )
        self.song_card.add_widget(self.panel_container)

        self.panel_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
        )
        self.song_card.add_widget(self.panel_divider)

        self.chord_name_section = None
        self.chord_name_label = None
        self.chord_pag_prev = None
        self.chord_pag_next = None
        self.griff_container = None
        self.griff_divider = None

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
            padding=[dp(16), dp(16), dp(16), dp(4)],
            adaptive_height=True,
            md_bg_color=[0, 0, 0, 0]
        )

        self.content_label = ChordTextLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            valign="top",
            line_height=1.5,
            markup=True
        )
        self.content_label.bind(texture_size=self._update_content_height)
        self._text_container.add_widget(self.content_label)

        self.content_scroll.add_widget(self._text_container)
        self.song_card.add_widget(self.content_scroll)

        self.bottom_divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
        )
        self.song_card.add_widget(self.bottom_divider)

        card_container.add_widget(self.song_card)
        main_container.add_widget(card_container)

        self.add_widget(main_container)

        if hasattr(self, '_top_spacer') and self._top_spacer:
            self._top_spacer.height = 0
        if hasattr(self, '_bottom_spacer') and self._bottom_spacer:
            self._bottom_spacer.height = 0

        self._create_main_panel()

        Clock.schedule_once(lambda dt: self._update_card_size(), 0.1)
        Clock.schedule_once(lambda dt: self._update_card_size(), 0.3)

    def _update_card_size(self, *args):
        if hasattr(self, 'song_card') and self.song_card:
            self.song_card.size_hint = (1, 1)
            self.song_card.height = self.height - self._top_spacer_song.height
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

    def _create_main_panel(self):
        """Создаёт основную панель с кнопками (как в SongDetailScreen)"""
        self.panel_container.clear_widgets()

        panel = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(2), dp(2), dp(2), dp(2)],
            spacing=dp(1)
        )

        # 1. Аккорды - бирюзовый
        self.chords_btn = IconActionButton(
            icon_name="music",
            on_press_callback=self.on_chords_press,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        # 2. Тональность - золотистый/оранжевый
        self.tonality_btn = IconActionButton(
            icon_name="tune",
            on_press_callback=self.show_tonality_panel,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )

        # 3. Прокрутка текста (плей) - синий
        self.scroll_btn = IconActionButton(
            icon_name="play-circle",
            on_press_callback=self.show_scroll_panel,
            icon_color=[0.2, 0.5, 0.9, 0.9]
        )

        # 4. Подборы (варианты) - серый
        self.tabs_btn = IconActionButton(
            icon_name="folder-music",
            on_press_callback=self.show_tabs_picker,
            icon_color=[0.5, 0.5, 0.5, 0.8]
        )

        # 5. Настройки (шестерёнка) - ЯРКО БЕЛАЯ
        self.font_btn = IconActionButton(
            icon_name="cog",
            on_press_callback=self.show_font_panel,
            icon_color=[1, 1, 1, 1]
        )

        # 6. Звёздочка (избранное) - золотистый
        self.favorite_btn = IconActionButton(
            icon_name="star-outline",
            on_press_callback=self.toggle_favorite,
            icon_color=[0.9, 0.7, 0.2, 0.9]
        )

        # 7. Лайк (сердце) - красный
        self.like_btn = IconActionButton(
            icon_name="heart-outline",
            on_press_callback=self.toggle_like,
            icon_color=[0.8, 0.3, 0.3, 0.9]
        )

        panel.add_widget(self.chords_btn)
        panel.add_widget(self.tonality_btn)
        panel.add_widget(self.scroll_btn)
        panel.add_widget(self.tabs_btn)
        panel.add_widget(self.font_btn)
        panel.add_widget(self.favorite_btn)
        panel.add_widget(self.like_btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'main'
        logger.info("✅ Создана основная панель")

    def _create_chords_panel(self):
        """Создаёт панель управления аккордами"""
        self.panel_container.clear_widgets()

        panel = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(2), dp(2), dp(2), dp(2)],
            spacing=dp(1)
        )

        self.variant_btn = MDIconButton(
            icon="format-list-bulleted-square",
            size_hint=(1, None),
            height=dp(40),
            theme_icon_color="Custom",
            icon_color=[0.3, 0.5, 0.9, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._next_chord_variant,
            ripple_scale=0
        )

        self.mode_btn = MDIconButton(
            icon="music-note",
            size_hint=(1, None),
            height=dp(40),
            theme_icon_color="Custom",
            icon_color=[1.0, 0.55, 0.0, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._toggle_display_mode,
            ripple_scale=0
        )

        self.eye_btn = MDIconButton(
            icon="eye",
            size_hint=(1, None),
            height=dp(40),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.2, 0.2, 1] if self.eye_active else [0.6, 0.6, 0.6, 0.8],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._toggle_eye,
            ripple_scale=0
        )

        self.griff_zoom_btn = MDIconButton(
            icon="magnify",
            size_hint=(1, None),
            height=dp(40),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._toggle_griff_zoom,
            ripple_scale=0
        )

        self.chords_close_btn = MDIconButton(
            icon="check",
            size_hint=(1, None),
            height=dp(40),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.close_chords_section,
            ripple_scale=0
        )

        panel.add_widget(self.variant_btn)
        panel.add_widget(self.mode_btn)
        panel.add_widget(self.eye_btn)
        panel.add_widget(self.griff_zoom_btn)
        panel.add_widget(self.chords_close_btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'chords'

    def _create_font_panel(self):
        """Создаёт панель шрифта"""
        self.panel_container.clear_widgets()

        panel = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)],
            spacing=dp(2)
        )

        center_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
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
                closest = min(font_sizes, key=lambda x: abs(x - size))
                return font_sizes.index(closest)

        def slider_to_size(slider_value):
            idx = int(round(slider_value))
            if idx < 0:
                idx = 0
            elif idx > total_steps:
                idx = total_steps
            return font_sizes[idx]

        current_slider_value = size_to_slider(self.current_font_size)

        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(14),
            spacing=dp(0)
        )

        left_spacer = MDLabel(text="", size_hint_x=None, width=dp(2))

        self.font_value_label = MDLabel(
            text=self._get_font_multiplier(self.current_font_size),
            font_size=sp(10),
            halign="center",
            valign="bottom",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        right_spacer = MDLabel(text="", size_hint_x=None, width=dp(2))

        top_row.add_widget(left_spacer)
        top_row.add_widget(self.font_value_label)
        top_row.add_widget(right_spacer)

        slider_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            padding=[dp(2), dp(0), dp(2), dp(0)]
        )

        self.font_slider = MDSlider(
            min=-0.01,
            max=float(total_steps + 0.01),
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            hint=False
        )
        self.font_slider.ripple_scale = 0

        bi_color = [0.46, 0.70, 0.71, 1]

        self.font_slider.thumb_color_active = bi_color
        self.font_slider.thumb_color_inactive = bi_color
        self.font_slider.thumb_color_disabled = bi_color
        self.font_slider.track_color_active = [0.46, 0.70, 0.71, 0.6]
        self.font_slider.track_color_inactive = [1, 1, 1, 0.3]
        self.font_slider.color = bi_color

        def on_slider_change(instance, value):
            int_value = int(round(value))
            if int_value < 0:
                int_value = 0
            elif int_value > total_steps:
                int_value = total_steps

            if self.font_slider.value != int_value:
                self.font_slider.value = int_value

            bi_color = [0.46, 0.70, 0.71, 1]
            self.font_slider.thumb_color_active = bi_color
            self.font_slider.thumb_color_inactive = bi_color
            self.font_slider.thumb_color_disabled = bi_color

            new_size = slider_to_size(int_value)

            if self.current_font_size != new_size:
                self.current_font_size = new_size
                self.font_value_label.text = self._get_font_multiplier(new_size)

                if hasattr(self, 'content_label'):
                    self.content_label.font_size = self.current_font_size
                    self._update_content_height()

                    delays = [0.0, 0.01, 0.03, 0.05, 0.08, 0.12, 0.2, 0.3, 0.5, 0.8]
                    for delay in delays:
                        Clock.schedule_once(lambda dt, d=delay: setattr(self.content_scroll, 'scroll_y', 1.0), delay)

        self.font_slider.bind(value=on_slider_change)

        slider_container.add_widget(self.font_slider)

        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        right_buttons = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(80),
            spacing=dp(4)
        )

        self.theme_btn = IconActionButton(
            icon_name="weather-sunny",
            on_press_callback=self._toggle_theme,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        self.font_apply_btn = IconActionButton(
            icon_name="check",
            on_press_callback=self.close_font_panel,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        right_buttons.add_widget(self.theme_btn)
        right_buttons.add_widget(self.font_apply_btn)

        panel.add_widget(center_container)
        panel.add_widget(right_buttons)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'font'

        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.1)
        Clock.schedule_once(lambda dt: self._fix_slider_thumb(self.font_slider), 0.3)

    def _create_tonality_panel(self):
        """Создаёт панель выбора тональности"""
        self.panel_container.clear_widgets()

        panel = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)],
            spacing=dp(4)
        )

        title_label = MDLabel(
            text="Тональность",
            font_size=sp(12),
            halign="left",
            valign="middle",
            size_hint_x=None,
            width=dp(100),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        center_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        from kivymd.uix.slider import MDSlider

        current_slider_value = int(round(self.current_tonality * 2))

        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(14),
            spacing=dp(0)
        )

        minus_label = MDLabel(
            text="-",
            font_size=sp(12),
            halign="center",
            valign="bottom",
            size_hint_x=None,
            width=dp(20),
            theme_text_color="Custom",
            text_color=[0.8, 0.3, 0.3, 0.9],
            bold=True
        )

        self.tonality_value_label = MDLabel(
            text="0" if current_slider_value == 0 else f"{current_slider_value:+d}",
            font_size=sp(10),
            halign="center",
            valign="bottom",
            size_hint_x=1,
            theme_text_color="Custom",
            bold=True
        )
        self._update_tonality_label_color(current_slider_value)

        plus_label = MDLabel(
            text="+",
            font_size=sp(12),
            halign="center",
            valign="bottom",
            size_hint_x=None,
            width=dp(20),
            theme_text_color="Custom",
            text_color=[0.3, 0.7, 0.3, 0.9],
            bold=True
        )

        top_row.add_widget(minus_label)
        top_row.add_widget(self.tonality_value_label)
        top_row.add_widget(plus_label)

        slider_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            padding=[dp(2), dp(0), dp(2), dp(0)]
        )

        self.tonality_slider = MDSlider(
            min=-6.01,
            max=6.01,
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            hint=False
        )
        self.tonality_slider.ripple_scale = 0

        bi_color = [0.46, 0.70, 0.71, 1]

        self.tonality_slider.thumb_color_active = bi_color
        self.tonality_slider.thumb_color_inactive = bi_color
        self.tonality_slider.thumb_color_disabled = bi_color
        self.tonality_slider.track_color_active = [0.46, 0.70, 0.71, 0.5]
        self.tonality_slider.track_color_inactive = [0.85, 0.85, 0.85, 1]
        self.tonality_slider.color = bi_color

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

            if int_value == 0:
                self.tonality_value_label.text = "0"
            else:
                self.tonality_value_label.text = f"{int_value:+d}"

            self._update_tonality_label_color(int_value)
            step = int_value / 2
            if step != self.current_tonality:
                self.current_tonality = step
                self.apply_tonality(self.current_tonality)

        self.tonality_slider.bind(value=on_slider_change)

        def on_minus(*args):
            new_value = max(-6, self.tonality_slider.value - 1)
            self.tonality_slider.value = new_value

        def on_plus(*args):
            new_value = min(6, self.tonality_slider.value + 1)
            self.tonality_slider.value = new_value

        minus_label.bind(on_touch_down=lambda x, y: on_minus())
        plus_label.bind(on_touch_down=lambda x, y: on_plus())

        center_container.add_widget(top_row)
        center_container.add_widget(slider_container)

        self.tonality_apply_btn = IconActionButton(
            icon_name="check",
            on_press_callback=self.close_tonality_panel,
            icon_color=[0.46, 0.70, 0.71, 1]
        )
        self.tonality_apply_btn.size_hint = (None, None)
        self.tonality_apply_btn.size = (dp(36), dp(36))

        panel.add_widget(title_label)
        panel.add_widget(center_container)
        panel.add_widget(self.tonality_apply_btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'tonality'

    def _create_scroll_panel(self):
        """Создаёт панель прокрутки текста"""
        self.panel_container.clear_widgets()

        panel = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)],
            spacing=dp(4)
        )

        center_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(0),
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        from kivymd.uix.slider import MDSlider

        def speed_to_slider(speed):
            if speed <= 0.5:
                return int(1 + (speed - 0.2) / 0.03)
            else:
                return int(10 + (speed - 0.5) / 0.1)

        def slider_to_speed(slider_value):
            if slider_value <= 10:
                return 0.2 + (slider_value - 1) * 0.03
            else:
                return 0.5 + (slider_value - 10) * 0.1

        current_slider_value = speed_to_slider(self.scroll_speed)

        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(14),
            spacing=dp(0)
        )

        left_spacer = MDLabel(text="", size_hint_x=None, width=dp(4))

        self.scroll_speed_value_label = MDLabel(
            text=f"{self.scroll_speed:.1f}x",
            font_size=sp(10),
            halign="center",
            valign="bottom",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            bold=True
        )

        right_spacer = MDLabel(text="", size_hint_x=None, width=dp(4))

        top_row.add_widget(left_spacer)
        top_row.add_widget(self.scroll_speed_value_label)
        top_row.add_widget(right_spacer)

        slider_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            padding=[dp(2), dp(0), dp(2), dp(0)]
        )

        self.scroll_speed_slider = MDSlider(
            min=0.99,
            max=28.01,
            value=current_slider_value,
            step=1,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(28),
            hint=False
        )
        self.scroll_speed_slider.ripple_scale = 0

        bi_color = [0.46, 0.70, 0.71, 1]
        self.scroll_speed_slider.thumb_color_active = bi_color
        self.scroll_speed_slider.thumb_color_inactive = bi_color
        self.scroll_speed_slider.thumb_color_disabled = bi_color
        self.scroll_speed_slider.track_color_active = [0.46, 0.70, 0.71, 0.6]
        self.scroll_speed_slider.track_color_inactive = [1, 1, 1, 0.3]
        self.scroll_speed_slider.color = bi_color

        def on_slider_change(instance, value):
            if value < 1:
                int_value = 1
            elif value > 28:
                int_value = 28
            else:
                int_value = int(round(value))

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
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(80),
            spacing=dp(2)
        )

        self.play_pause_btn = IconActionButton(
            icon_name="play",
            on_press_callback=self.toggle_scroll,
            icon_color=[0.46, 0.70, 0.71, 1]
        )

        self.stop_btn = IconActionButton(
            icon_name="stop",
            on_press_callback=self.reset_scroll_position,
            icon_color=[0.8, 0.3, 0.3, 0.9]
        )

        buttons_container.add_widget(self.play_pause_btn)
        buttons_container.add_widget(self.stop_btn)

        self.scroll_close_btn = IconActionButton(
            icon_name="check",
            on_press_callback=self.close_scroll_panel,
            icon_color=[0.46, 0.70, 0.71, 1]
        )
        self.scroll_close_btn.size_hint = (None, None)
        self.scroll_close_btn.size = (dp(36), dp(36))

        panel.add_widget(center_container)
        panel.add_widget(buttons_container)
        panel.add_widget(self.scroll_close_btn)

        self.panel_container.add_widget(panel)
        self.current_panel_type = 'scroll'

    # ============ МЕТОДЫ УПРАВЛЕНИЯ ПАНЕЛЯМИ ============

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
            notify.info("Аккорды не найдены в тексте песни")
            return

        if self.is_chords_mode:
            self.close_chords_section()
            return

        self._create_chords_panel()
        self.is_chords_mode = True
        self._show_chords_layer()

    def _show_chords_layer(self):
        if hasattr(self, '_griff_added') and self._griff_added:
            return

        from kivy.uix.carousel import Carousel

        self.chord_name_section = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(30),
            md_bg_color=[0, 0, 0, 0],
            padding=[dp(8), dp(2), dp(8), dp(2)],
            spacing=dp(4)
        )

        self.chord_pag_prev = MDIconButton(
            icon="chevron-left",
            size_hint=(None, 1),
            width=dp(24),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 0.3],
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0
        )

        self.chord_name_label = MDLabel(
            text="",
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            font_size=sp(18)
        )

        self.chord_pag_next = MDIconButton(
            icon="chevron-right",
            size_hint=(None, 1),
            width=dp(24),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 0.3],
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0
        )

        self.chord_name_section.add_widget(self.chord_pag_prev)
        self.chord_name_section.add_widget(self.chord_name_label)
        self.chord_name_section.add_widget(self.chord_pag_next)

        griff_height = dp(120)
        self.griff_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=griff_height,
            padding=[dp(10), dp(4), dp(10), dp(4)],
            md_bg_color=[0, 0, 0, 0]
        )

        self.chords_carousel = Carousel(
            direction='right',
            loop=True,
            size_hint=(1, 1),
            anim_move_duration=0.3
        )
        self.chords_carousel.bind(current_slide=self._on_carousel_slide)

        self.chord_renderers = []
        self.chord_slides = []

        for i, chord_name in enumerate(self._song_chords):
            slide = MDBoxLayout(
                orientation='vertical',
                size_hint=(1, 1),
                md_bg_color=[0, 0, 0, 0]
            )

            renderer = ChordRenderer()
            renderer.size_hint = (1, 1)
            renderer.chord_name = chord_name
            renderer.index = i

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
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(2),
            md_bg_color=[0.5, 0.5, 0.5, 0.3],
            padding=[0, 0, 0, 0]
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
        if hasattr(self, '_griff_added') and self._griff_added:
            content_scroll = self.content_scroll
            bottom_divider = self.bottom_divider

            if hasattr(self, 'chord_name_section') and self.chord_name_section:
                if self.chord_name_section in self.song_card.children:
                    self.song_card.remove_widget(self.chord_name_section)
                    self.chord_name_section = None
                    self.chord_name_label = None
                    self.chord_pag_prev = None
                    self.chord_pag_next = None

            if hasattr(self, 'griff_container') and self.griff_container:
                if self.griff_container in self.song_card.children:
                    self.song_card.remove_widget(self.griff_container)
                    self.griff_container = None

            if hasattr(self, 'griff_divider') and self.griff_divider:
                if self.griff_divider in self.song_card.children:
                    self.song_card.remove_widget(self.griff_divider)
                    self.griff_divider = None

            if content_scroll not in self.song_card.children:
                self.song_card.add_widget(content_scroll)
            if bottom_divider not in self.song_card.children:
                self.song_card.add_widget(bottom_divider)

            self.chords_carousel = None
            self.chord_renderers = []
            self.chord_slides = []
            self._griff_added = False

    def close_chords_section(self, *args):
        if hasattr(self, 'eye_active') and self.eye_active:
            self._create_main_panel()
            self.is_chords_mode = False
            return

        self._create_main_panel()
        self.is_chords_mode = False
        self._hide_chords_layer()

    def _toggle_eye(self, *args):
        self.eye_active = not self.eye_active
        if self.eye_active:
            self.eye_btn.icon_color = [0.8, 0.2, 0.2, 1]
        else:
            self.eye_btn.icon_color = [0.6, 0.6, 0.6, 0.8]

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

    def _fix_slider_thumb(self, slider):
        if slider:
            bi_color = [0.46, 0.70, 0.71, 1]
            slider.thumb_color_active = bi_color
            slider.thumb_color_inactive = bi_color
            slider.thumb_color_disabled = bi_color
            current = slider.value
            slider.value = current + 0.01
            Clock.schedule_once(lambda dt: setattr(slider, 'value', current), 0.01)

    def _toggle_display_mode(self, *args):
        if self.display_mode == "finger":
            self.display_mode = "notes"
            self.mode_btn.icon = "gesture-tap"
            self.mode_btn.icon_color = [1.0, 0.55, 0.0, 1]
        else:
            self.display_mode = "finger"
            self.mode_btn.icon = "music-note"
            self.mode_btn.icon_color = [0.9, 0.2, 0.2, 1]

        if self._current_chord_index < len(self.chord_renderers):
            self.chord_renderers[self._current_chord_index].set_mode(self.display_mode)

    def _toggle_griff_zoom(self, *args):
        if not hasattr(self, 'griff_container') or not self.griff_container:
            return

        zoom_levels = [1.0, 1.3, 1.6]
        current = self.griff_scale
        if current in zoom_levels:
            current_index = zoom_levels.index(current)
            next_index = (current_index + 1) % len(zoom_levels)
            new_scale = zoom_levels[next_index]
        else:
            new_scale = 1.0

        self.griff_scale = new_scale
        base_height = dp(120)
        new_height = int(base_height * new_scale)
        self.griff_container.height = new_height

        if new_scale == 1.0:
            self.griff_zoom_btn.icon = "magnify"
            self.griff_zoom_btn.icon_color = [1, 1, 1, 1]
        elif new_scale == 1.3:
            self.griff_zoom_btn.icon = "magnify-plus"
            self.griff_zoom_btn.icon_color = [0.46, 0.70, 0.71, 1]
        else:
            self.griff_zoom_btn.icon = "magnify-plus"
            self.griff_zoom_btn.icon_color = [0.9, 0.7, 0.2, 1]

    def _update_chords_display(self):
        if not self._song_chords:
            return

        chord_name = self._song_chords[self._current_chord_index]
        if hasattr(self, 'chord_name_label') and self.chord_name_label:
            self.chord_name_label.text = chord_name
        self._load_chord_variants(chord_name)

    def _load_chord_variants(self, chord_name):
        self.chord_variants = []
        self.chord_variant_index = 0

        if self.manager and self.manager.has_screen('chords'):
            chords_screen = self.manager.get_screen('chords')
            variants = []
            for chord in chords_screen.all_chords:
                if chord['short_name'].lower() == chord_name.lower():
                    variants.append(chord)

            variants.sort(key=lambda x: x['variant'])
            self.chord_variants = variants
            self._update_variant_icon()

            if self.chord_variants:
                self.load_current_variant()

    def _update_variant_icon(self):
        total = len(self.chord_variants)
        if hasattr(self, 'variant_btn'):
            if total <= 1:
                self.variant_btn.opacity = 0.5
            else:
                self.variant_btn.opacity = 1

    def load_current_variant(self):
        if not self.chord_variants:
            return

        variant = self.chord_variants[self.chord_variant_index]
        chord_module = None
        if 'module' in variant:
            chord_module = variant['module']
        elif 'module_1' in variant:
            chord_module = variant['module_1']
        else:
            for key, value in variant.items():
                if 'module' in key.lower() and value:
                    chord_module = value
                    break

        if chord_module:
            if self._current_chord_index < len(self.chord_renderers):
                renderer = self.chord_renderers[self._current_chord_index]
                renderer.load_chord(chord_module)
                renderer.set_mode(self.display_mode)

        self._update_variant_icon()

    def _next_chord_variant(self, *args):
        if not self.chord_variants:
            return
        total = len(self.chord_variants)
        self.chord_variant_index = (self.chord_variant_index + 1) % total
        self.load_current_variant()

    def _extract_and_cache_chords(self):
        chords = set()
        for tab in self.tabs:
            content = tab.get('content', '')
            if content:
                cleaned = clean_text(content)
                extracted = extract_chords_from_text(cleaned)
                chords.update(extracted)
        self._song_chords = sorted(list(chords))

    def precompute_transpositions(self, cleaned_text):
        self.original_cleaned_text = cleaned_text
        self.transposed_text_cache[0] = highlight_chords_in_text(cleaned_text)
        self.transposed_chords_cache[0] = self._song_chords.copy()

        steps = [-3, -2.5, -2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2, 2.5, 3]
        for step in steps:
            transposed = transpose_text(cleaned_text, step)
            self.transposed_text_cache[step] = transposed
            transposed_chords = transpose_chord_list(self._song_chords, step)
            self.transposed_chords_cache[step] = transposed_chords

    def apply_tonality(self, step):
        transposed_text = self.transposed_text_cache.get(step)
        if transposed_text:
            self.content_label.text = transposed_text
            self.content_label.markup = True
            self._song_chords = self.transposed_chords_cache.get(step, [])
            if self.is_chords_mode and hasattr(self, 'chord_name_label'):
                if self._song_chords:
                    if self._current_chord_index >= len(self._song_chords):
                        self._current_chord_index = 0
                    self._update_chords_display()

    def _update_tonality_label_color(self, value):
        if hasattr(self, 'tonality_value_label'):
            if value < 0:
                self.tonality_value_label.text_color = [0.8, 0.3, 0.3, 1]
            elif value > 0:
                self.tonality_value_label.text_color = [0.3, 0.7, 0.3, 1]
            else:
                self.tonality_value_label.text_color = [0.46, 0.70, 0.71, 1]

    def show_tabs_picker(self):
        if not self.tabs or len(self.tabs) <= 1:
            notify.info("Только один подбор")
            return

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        for i, tab in enumerate(self.tabs):
            btn = MDRaisedButton(
                text=f"Подбор {i + 1}",
                size_hint=(1, None),
                height=dp(48),
                md_bg_color=[0.46, 0.70, 0.71, 1] if i == self.current_tab_index else [0.2, 0.2, 0.2, 0.8],
                text_color=[1, 1, 1, 1],
                on_release=lambda x, idx=i: self._select_tab(idx)
            )
            content.add_widget(btn)

        dialog = MDDialog(
            title="Выберите подбор",
            type="custom",
            content_cls=content,
            buttons=[MDRaisedButton(text="Закрыть", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()
        self.tabs_dialog = dialog

    def _select_tab(self, index):
        if hasattr(self, 'tabs_dialog'):
            self.tabs_dialog.dismiss()
        self.current_tab_index = index
        self._load_current_tab()

    def reset_font_size(self):
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'content_label'):
            self.content_label.font_size = self.current_font_size
            self._update_content_height()

    def set_song(self, song_id):
        """Устанавливает песню для просмотра"""
        self.song_id = song_id
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
        if hasattr(self, '_current_theme') and self._current_theme != 'green':
            self._set_green_theme()
            self._current_theme = 'green'

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
        artist = data.get('artist') or self.song_artist or 'Неизвестный'
        title = data.get('title') or self.song_title or 'Без названия'
        self.song_artist = artist
        self.song_title = title
        self.tabs = data.get('tabs', [])
        if not self.tabs and data.get('content'):
            self.tabs = [{'content': data.get('content', '')}]
        self.current_tab_index = 0

        if self.tabs:
            raw_content = self.tabs[0].get('content', 'Текст не загружен')
            cleaned = clean_text(raw_content)
            self._extract_and_cache_chords()
            self.precompute_transpositions(cleaned)
            original_text = self.transposed_text_cache.get(0, cleaned)
            self.content_label.text = original_text
            self.content_label.markup = True
            self._update_content_height()

        self.is_liked = data.get('is_liked', False)
        self.is_favorite = data.get('is_favorite', False)

        # Обновляем иконки в панели
        if hasattr(self, 'like_btn') and self.like_btn:
            self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
        if hasattr(self, 'favorite_btn') and self.favorite_btn:
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
        self.content_label.text = "Ошибка загрузки\nПроверьте интернет"
        notify.error("Ошибка загрузки песни")

    def toggle_like(self, *args):
        if not api.is_authenticated():
            app = MDApp.get_running_app()
            if app and hasattr(app, 'open_profile'):
                app.open_profile()
            return

        def on_success(result):
            self.is_liked = result.get('liked', not self.is_liked)
            if hasattr(self, 'like_btn') and self.like_btn:
                self.like_btn.icon = "heart" if self.is_liked else "heart-outline"
            notify.success("Лайк поставлен!" if self.is_liked else "Лайк убран")

        def on_failure(req, error):
            notify.error("Ошибка")

        api.toggle_like(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def toggle_favorite(self, *args):
        if not api.is_authenticated():
            app = MDApp.get_running_app()
            if app and hasattr(app, 'open_profile'):
                app.open_profile()
            return

        if self.is_favorite:
            def on_success(result):
                self.is_favorite = False
                if hasattr(self, 'favorite_btn') and self.favorite_btn:
                    self.favorite_btn.icon = "star-outline"
                api._clear_favorites_cache()
                notify.success("Удалено из избранного")

            def on_failure(req, error):
                notify.error("Ошибка")

            api.remove_from_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)
        else:
            def on_success(result):
                self.is_favorite = True
                if hasattr(self, 'favorite_btn') and self.favorite_btn:
                    self.favorite_btn.icon = "star"
                api._clear_favorites_cache()
                notify.success("Добавлено в избранное")

            def on_failure(req, error):
                notify.error("Ошибка")

            api.add_to_favorites(song_id=self.song_id, on_success=on_success, on_failure=on_failure)

    def update_top_nav_title(self):
        app = MDApp.get_running_app()
        if not app or not hasattr(app, 'top_nav'):
            return

        title_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(2),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        song_name = self.song_title if self.song_title else "Подбор"
        song_title_label = MDLabel(
            text=song_name,
            font_size=sp(18),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            shorten=True,
            shorten_from="right"
        )

        artist_name = self.song_artist if self.song_artist else ""
        artist_label = MDLabel(
            text=artist_name,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.9, 0.9, 0.9, 0.8],
            shorten=True,
            shorten_from="right"
        )

        title_container.add_widget(song_title_label)
        title_container.add_widget(artist_label)

        app.top_nav.set_custom_title_widget(title_container)

    # ============ ПРОКРУТКА ТЕКСТА ============

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
            scroll_step = 0.0004 * self.scroll_speed
            new_y = self.content_scroll.scroll_y - scroll_step
            if new_y <= 0:
                self.content_scroll.scroll_y = 0
                self.stop_scroll()
                self.play_pause_btn.icon = "play"
                return False
            else:
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

    def _get_font_multiplier(self, font_size):
        ratio = font_size / self.STANDARD_FONT_SIZE
        rounded = round(ratio * 10) / 10
        if rounded == int(rounded):
            return f"{int(rounded)}x"
        return f"{rounded:.1f}x"

    def go_back(self, instance=None):
        """Возврат ТОЛЬКО в SongsScreen с сохранением результатов поиска"""
        logger.info(f"🔙 Возврат из поискового просмотра в SongsScreen")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('songs')

        if self.manager and self.manager.has_screen('songs'):
            songs_screen = self.manager.get_screen('songs')
            Clock.schedule_once(lambda dt: songs_screen.restore_state(), 0.1)
            self.manager.current = 'songs'
            logger.info("✅ Возврат на SongsScreen")
        else:
            self.manager.current = 'home'
            logger.info("⚠️ SongsScreen не найден, возврат на home")

    def on_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            # Настраиваем левую кнопку - стрелка назад
            if hasattr(app.top_nav, 'left_container'):
                app.top_nav.left_container.clear_widgets()
                app.top_nav.left_container.add_widget(app.top_nav.back_btn)
                app.top_nav.back_btn.on_release = self.go_back

            # ✅ ВОССТАНАВЛИВАЕМ ПРАВЫЕ КНОПКИ - иконка домой (как в SongDetailScreen)
            if hasattr(app.top_nav, 'right_container'):
                # Проверяем, есть ли home_btn
                if hasattr(app.top_nav, 'home_btn'):
                    app.top_nav.right_container.clear_widgets()
                    app.top_nav.right_container.add_widget(app.top_nav.home_btn)
                    logger.info("✅ Восстановлена иконка домой (как в SongDetailScreen)")

        if self.song_title:
            self.update_top_nav_title()

        if hasattr(self, '_top_spacer_song'):
            top_padding = layout_config.get_top_padding()
            if platform == 'android':
                top_padding = top_padding + dp(16)
            self._top_spacer_song.height = top_padding

    def on_leave(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            if hasattr(app.top_nav, '_update_right_buttons'):
                app.top_nav._update_right_buttons('songs')