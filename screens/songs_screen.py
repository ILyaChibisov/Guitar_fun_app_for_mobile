# screens/songs_screen.py
"""
Экран песен:
  - алфавит сверху, показывается всегда;
  - карточки БЕЗ вертикального скролла — заполняют экран;
  - PAGE_SIZE рассчитывается от высоты экрана (on_size);
  - пагинация: динамические центрированные ряды цифр (без RecycleView);
  - ряд формируется по реальной ширине center_zone (3-9 цифр);
  - стрелки листают РЯДЫ (шаг = размер ряда);
  - короткий тап = 1 ряд, долгий (0.4с) = 10 рядов;
  - клик по цифре — переход;
  - текущая страница всегда в ряду (окно центрируется);
  - тема/язык применяются лениво (BaseScreen);
  - при ошибке сети кэш помечается failed, повторный клик = повторный запрос.

СОСТОЯНИЕ: используется только songs_state.save_alphabet / get_alphabet
и songs_state.save_search / get_search / invalidate_search.
"""
import time
import unicodedata
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from io import BytesIO
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.animation import Animation

from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout

from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
from state.songs_state import songs_state
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('Songs')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА
# ============================================================

class SongsColors:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        return [0.10, 0.42, 0.25, 1]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 1]
        return [1, 1, 1, 1]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        return [1, 1, 1, 0.7]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.1]
        return [0, 0, 0, 0.10]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        return [1, 1, 1, 0.25]

    @staticmethod
    def get_card_line_width(theme_id):
        return 2.0

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 1]
        return [1, 1, 1, 1]


# ============ ГЛОБАЛЬНЫЕ ИКОНКИ ============
_shared_rus_flag_texture = None
_shared_eng_flag_texture = None
_shared_song_icon_texture = None
_shared_artist_icon_texture = None


def load_shared_icons_sync():
    global _shared_rus_flag_texture, _shared_eng_flag_texture
    global _shared_song_icon_texture, _shared_artist_icon_texture
    if _shared_rus_flag_texture is not None:
        return
    if HAS_ASSETS:
        try:
            rus_data = load_asset_as_bytes('rus_png')
            if rus_data:
                _shared_rus_flag_texture = CoreImage(BytesIO(rus_data), ext="png").texture
            eng_data = load_asset_as_bytes('eng_png')
            if eng_data:
                _shared_eng_flag_texture = CoreImage(BytesIO(eng_data), ext="png").texture
            song_data = load_asset_as_bytes('song_png')
            if song_data:
                _shared_song_icon_texture = CoreImage(BytesIO(song_data), ext="png").texture
            artist_data = load_asset_as_bytes('artist_png')
            if artist_data:
                _shared_artist_icon_texture = CoreImage(BytesIO(artist_data), ext="png").texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконок: {e}")


# ============ ПОИСКОВАЯ СТРОКА ============

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
        self.search_field.hint_text = get_text('search')
        self.search_btn.text = get_text('find')

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = SongsColors.get_accent(theme_id)
        text_p = SongsColors.get_text_primary(theme_id)
        text_s = SongsColors.get_text_secondary(theme_id)
        line = SongsColors.get_card_line(theme_id)
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
            self.line_color = line
            self.line_width = 4.0
            self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]
            self.search_field.hint_text_color = [0.55, 0.55, 0.55, 1]
            self.search_field.cursor_color = [0.1, 0.1, 0.1, 1]
            self.clear_btn.icon_color = [0.4, 0.4, 0.4, 0.8]
            self.search_btn.md_bg_color = accent
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
        if self.on_clear:
            self.on_clear()
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""

    def _on_focus(self, instance, value):
        self.line_width = 5.0 if value else 4.0

    def set_text(self, text):
        self.search_field.text = text or ""
        self._on_text_change(None, self.search_field.text)

    def clear(self):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""


# ============ КОМПОНЕНТЫ АЛФАВИТА ============

class LetterButton(MDBoxLayout):
    def __init__(self, text, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press
        self.is_selected = False
        self.size_hint = (None, 1)
        self.width = dp(32)
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]
        self.label = MDLabel(
            text=text, font_size=sp(15), halign="center", valign="middle",
            theme_text_color="Custom", text_color=[1, 1, 1, 0.7], bold=True,
            size_hint=(1, 1)
        )
        self.add_widget(self.label)
        self.bind(on_touch_down=self._on_touch_down)
        self._update_style()

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
            self.md_bg_color = SongsColors.get_accent(theme_id)
            self.label.text_color = [1, 1, 1, 1]
            self.radius = [dp(8)]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = SongsColors.get_text_secondary(theme_id)
            self.radius = [0]


class FlagLabel(MDBoxLayout):
    def __init__(self, flag_type='ru', **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(38)
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]
        texture = (_shared_rus_flag_texture if flag_type == 'ru'
                   else _shared_eng_flag_texture if flag_type == 'en' else None)
        container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 1))
        if texture:
            container.add_widget(Image(
                texture=texture, size_hint=(None, None),
                size=(dp(22), dp(22)), allow_stretch=True, keep_ratio=True
            ))
        else:
            container.add_widget(MDLabel(
                text="RU" if flag_type == 'ru' else "EN",
                font_size=sp(10), halign="center", valign="middle",
                theme_text_color="Custom", text_color=[1, 1, 1, 0.6], bold=True
            ))
        self.add_widget(container)


class AlphabetMenu(MDBoxLayout):
    RU_LETTERS = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И',
                  'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т',
                  'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь',
                  'Э', 'Ю', 'Я']
    EN_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                  'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                  'U', 'V', 'W', 'X', 'Y', 'Z']
    DIGITS_LETTERS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '#']

    def __init__(self, on_letter_press=None, current_language='ru', **kwargs):
        super().__init__(**kwargs)
        self.on_letter_press = on_letter_press
        self.current_language = current_language
        self.current_selection = None
        self.orientation = 'horizontal'
        self.size_hint = (1, 1)
        self.spacing = dp(2)
        self.padding = [dp(4)] * 4
        self.md_bg_color = [0, 0, 0, 0]

        self.left_arrow = MDIconButton(
            icon="chevron-left", size_hint=(None, 1), width=dp(28),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll(-1), ripple_scale=0, ripple_alpha=0
        )
        self.right_arrow = MDIconButton(
            icon="chevron-right", size_hint=(None, 1), width=dp(28),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll(1), ripple_scale=0, ripple_alpha=0
        )
        self.add_widget(self.left_arrow)

        self.scroll_view = ScrollView(
            size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False,
            bar_width=0, bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0], bar_margin=0
        )
        self.container = MDBoxLayout(
            orientation='horizontal', size_hint_x=None,
            spacing=dp(2), padding=[dp(4)] * 4
        )
        self.container.bind(minimum_width=self.container.setter('width'))
        self.scroll_view.add_widget(self.container)
        self.add_widget(self.scroll_view)
        self.add_widget(self.right_arrow)

        self.buttons = []
        self._flag_widgets = []
        self._populate_items()
        self.update_theme_colors()

    def _populate_items(self):
        self.container.clear_widgets()
        self.buttons = []
        self._flag_widgets = []
        user_lang = settings_manager.language
        if user_lang == 'ru':
            groups = [('ru', self.RU_LETTERS, True),
                      ('symbols', self.DIGITS_LETTERS, False),
                      ('en', self.EN_LETTERS, True)]
        else:
            groups = [('en', self.EN_LETTERS, True),
                      ('symbols', self.DIGITS_LETTERS, False)]
        total_width = dp(8)
        for group_type, letters, show_flag in groups:
            if show_flag:
                flag = FlagLabel(flag_type=group_type)
                self.container.add_widget(flag)
                self._flag_widgets.append(flag)
                total_width += flag.width + dp(2)
            for letter in letters:
                btn = LetterButton(text=letter, on_press=self._on_letter_press)
                if letter == self.current_selection:
                    btn.set_selected(True)
                self.buttons.append(btn)
                self.container.add_widget(btn)
                total_width += btn.width + dp(2)
        self.container.width = total_width + dp(8)

    def scroll(self, direction):
        new_scroll = max(0, min(1, self.scroll_view.scroll_x + direction * 0.2))
        Animation(scroll_x=new_scroll, duration=0.2, t='out_quad').start(self.scroll_view)

    def _on_letter_press(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)
        if self.on_letter_press:
            self.on_letter_press(letter)

    def set_language(self, language):
        self.current_language = language
        self.current_selection = None
        self._populate_items()

    def set_current(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)

    def update_theme_colors(self):
        arrow_color = [0, 0, 0, 1] if settings_manager.theme == 'light' else [1, 1, 1, 1]
        self.left_arrow.icon_color = arrow_color
        self.right_arrow.icon_color = arrow_color
        for btn in self.buttons:
            btn._update_style()


class SongsMenu(MDBoxLayout):
    def __init__(self, on_language_toggle=None, on_letter_press=None,
                 current_language='ru', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.md_bg_color = [0, 0, 0, 0]
        self.alphabet_menu = AlphabetMenu(
            on_letter_press=on_letter_press,
            current_language=current_language
        )
        self.add_widget(self.alphabet_menu)

    def update_theme_colors(self):
        if self.alphabet_menu:
            self.alphabet_menu.update_theme_colors()

    def set_language(self, language):
        self.alphabet_menu.set_language(language)

    def set_current_letter(self, letter):
        self.alphabet_menu.set_current(letter)


# ============ КАРТОЧКИ БЕЗ СКРОЛЛА (с переиспользованием) ============

class StaticArtistCard(MDCard):
    def __init__(self, artist_name='', songs_count=0, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist_name = artist_name
        self.songs_count = songs_count
        self.on_click_callback = on_click

        self.size_hint_y = 1
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self.theme_line_color = "Custom"
        self.theme_bg_color = "Custom"
        self.padding = [0, dp(4), 0, dp(4)]
        self.spacing = dp(8)

        content = MDBoxLayout(
            orientation='horizontal',
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]
        )
        self.icon = Image(
            size_hint=(None, 1), width=dp(24),
            allow_stretch=True, keep_ratio=True
        )
        if _shared_artist_icon_texture:
            self.icon.texture = _shared_artist_icon_texture
        else:
            self.icon.text = "🎤"
        self.artist_label = MDLabel(
            font_size=sp(15), theme_text_color="Custom",
            bold=True, shorten=True, shorten_from="right",
            valign="middle", size_hint_x=1,
        )
        self.count_label = MDLabel(
            text="", font_size=sp(12), size_hint_x=None, width=dp(40),
            halign="right", valign="middle", theme_text_color="Custom"
        )
        self.arrow = MDLabel(
            text="›", font_size=sp(20), size_hint_x=None, width=dp(20),
            halign="center", valign="middle", theme_text_color="Custom"
        )
        content.add_widget(self.icon)
        content.add_widget(self.artist_label)
        content.add_widget(self.count_label)
        content.add_widget(self.arrow)
        self.add_widget(content)

        self.artist_label.text = artist_name
        self.count_label.text = str(songs_count) if songs_count > 0 else ""

        self.bind(on_touch_down=self._handle_touch)
        self.update_theme_colors()

    def _handle_touch(self, instance, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self.on_click_callback:
            self.on_click_callback(self.artist_name, self.songs_count)
        return True

    def update_data(self, artist_name, songs_count, on_click):
        self.artist_name = artist_name
        self.songs_count = songs_count
        self.on_click_callback = on_click
        self.artist_label.text = artist_name
        self.count_label.text = str(songs_count) if songs_count > 0 else ""

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = SongsColors.get_card_bg(theme_id)
        self.line_color = SongsColors.get_card_line(theme_id)
        self.line_width = SongsColors.get_card_line_width(theme_id)
        self.artist_label.text_color = SongsColors.get_text_primary(theme_id)
        self.count_label.text_color = SongsColors.get_text_secondary(theme_id)
        self.arrow.text_color = [0, 0, 0, 0.6] if theme_id == 'light' else [1, 1, 1, 0.3]


class StaticSearchSongCard(MDCard):
    def __init__(self, artist='', title='', song_id=0, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist = artist
        self.title = title
        self.song_id = song_id
        self.on_click_callback = on_click

        self.size_hint_y = 1
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self.theme_line_color = "Custom"
        self.theme_bg_color = "Custom"
        self.padding = [0, dp(4), 0, dp(4)]
        self.spacing = dp(8)

        content = MDBoxLayout(
            orientation='horizontal',
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]
        )
        self.icon = Image(
            size_hint=(None, 1), width=dp(24),
            allow_stretch=True, keep_ratio=True
        )
        if _shared_song_icon_texture:
            self.icon.texture = _shared_song_icon_texture
        else:
            self.icon.text = "🎵"
        text_layout = MDBoxLayout(
            orientation='vertical', size_hint_x=1,
            spacing=dp(1), pos_hint={'center_y': 0.5}
        )
        self.artist_label = MDLabel(
            font_size=sp(15), size_hint_y=None, height=dp(20),
            theme_text_color="Custom", bold=True,
            shorten=True, shorten_from="right", valign="middle"
        )
        self.title_label = MDLabel(
            font_size=sp(12), size_hint_y=None, height=dp(16),
            theme_text_color="Custom", valign="middle",
            shorten=True, shorten_from="right"
        )
        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)
        self.arrow = MDLabel(
            text="›", font_size=sp(20), size_hint_x=None, width=dp(20),
            halign="center", valign="middle", theme_text_color="Custom"
        )
        content.add_widget(self.icon)
        content.add_widget(text_layout)
        content.add_widget(self.arrow)
        self.add_widget(content)

        self.artist_label.text = artist
        self.title_label.text = title

        self.bind(on_touch_down=self._handle_touch)
        self.update_theme_colors()

    def _handle_touch(self, instance, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self.on_click_callback:
            self.on_click_callback(self.song_id, self.title)
        return True

    def update_data(self, artist, title, song_id, on_click):
        self.artist = artist
        self.title = title
        self.song_id = song_id
        self.on_click_callback = on_click
        self.artist_label.text = artist
        self.title_label.text = title

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = SongsColors.get_card_bg(theme_id)
        self.line_color = SongsColors.get_card_line(theme_id)
        self.line_width = SongsColors.get_card_line_width(theme_id)
        self.artist_label.text_color = SongsColors.get_text_primary(theme_id)
        self.title_label.text_color = SongsColors.get_text_secondary(theme_id)
        self.arrow.text_color = [0, 0, 0, 0.6] if theme_id == 'light' else [1, 1, 1, 0.3]


class PageCardsContainer(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(6)
        self.md_bg_color = [0, 0, 0, 0]
        self.cards = []

    def set_artists(self, artists, on_click):
        if len(self.cards) == len(artists):
            for card, data in zip(self.cards, artists):
                card.update_data(
                    artist_name=data.get('artist', ''),
                    songs_count=data.get('songs_count', 0),
                    on_click=on_click,
                )
            return
        self.clear_widgets()
        self.cards = []
        for a in artists:
            card = StaticArtistCard(
                artist_name=a.get('artist', ''),
                songs_count=a.get('songs_count', 0),
                on_click=on_click,
            )
            self.add_widget(card)
            self.cards.append(card)

    def set_songs(self, songs, on_click):
        if len(self.cards) == len(songs):
            for card, data in zip(self.cards, songs):
                card.update_data(
                    artist=data.get('artist', ''),
                    title=data.get('title', ''),
                    song_id=data.get('song_id', 0),
                    on_click=on_click,
                )
            return
        self.clear_widgets()
        self.cards = []
        for s in songs:
            card = StaticSearchSongCard(
                artist=s.get('artist', ''),
                title=s.get('title', ''),
                song_id=s.get('song_id', 0),
                on_click=on_click,
            )
            self.add_widget(card)
            self.cards.append(card)

    def clear(self):
        self.clear_widgets()
        self.cards = []

    def update_theme_colors(self):
        for c in self.cards:
            c.update_theme_colors()


# ============ ПАГИНАЦИЯ: ДИНАМИЧЕСКИЕ ЦЕНТРИРОВАННЫЕ РЯДЫ ============

class ArrowButton(MDBoxLayout):
    LONG_PRESS_TIME = 0.4

    def __init__(self, icon_name, short_press=None, long_press=None,
                 icon_color=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = dp(28)
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]

        self._on_short_press = short_press
        self._on_long_press = long_press
        self._long_press_event = None
        self._long_press_fired = False
        self._pressed = False
        self._enabled = True

        container = AnchorLayout(anchor_x='center', anchor_y='center',
                                  size_hint=(1, 1))
        self.icon_widget = MDIcon(
            icon=icon_name,
            font_size=sp(24),
            theme_text_color="Custom",
            text_color=icon_color if icon_color else [1, 1, 1, 1],
            size_hint=(None, None),
            size=(dp(24), dp(24)),
        )
        container.add_widget(self.icon_widget)
        self.add_widget(container)

        self.bind(on_touch_down=self._handle_touch_down,
                  on_touch_up=self._handle_touch_up)

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.opacity = 1.0 if enabled else 0.4

    def set_color(self, color):
        self.icon_widget.text_color = color

    def _handle_touch_down(self, instance, touch):
        if not self.collide_point(*touch.pos):
            return False
        if not self._enabled:
            return True
        self._pressed = True
        self._long_press_fired = False
        self._long_press_event = Clock.schedule_once(
            lambda dt: self._fire_long_press(), self.LONG_PRESS_TIME
        )
        return True

    def _fire_long_press(self):
        self._long_press_fired = True
        self._long_press_event = None
        if self._on_long_press and self._pressed and self._enabled:
            self._on_long_press()

    def _handle_touch_up(self, instance, touch):
        if not self._pressed:
            return False
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
        if (not self._long_press_fired and self._enabled
                and self.collide_point(*touch.pos)
                and self._on_short_press):
            self._on_short_press()
        self._pressed = False
        return True


class PageButton(MDBoxLayout):
    def __init__(self, text, index, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.size_hint_x = None
        self.size_hint_y = 1
        self.width = dp(32)
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]
        self.is_selected = False
        self.page_index = index
        self.on_click_callback = on_click

        self.label = MDLabel(
            text=text, font_size=sp(15), halign="center", valign="middle",
            theme_text_color="Custom", text_color=[1, 1, 1, 0.7],
            bold=True, size_hint=(1, 1),
        )
        self.add_widget(self.label)
        self.bind(on_touch_down=self._handle_touch_down)
        self.update_style()

    def _handle_touch_down(self, instance, touch):
        if not self.collide_point(*touch.pos):
            return False
        if self.on_click_callback:
            self.on_click_callback(self.page_index)
        return True

    def set_selected(self, selected):
        if self.is_selected == selected:
            return
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        theme_id = settings_manager.theme
        accent = SongsColors.get_accent(theme_id)
        text_s = SongsColors.get_text_secondary(theme_id)
        if self.is_selected:
            self.md_bg_color = accent
            self.label.text_color = [1, 1, 1, 1]
            self.label.bold = True
            self.radius = [dp(8)]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = text_s
            self.label.bold = False
            self.radius = [0]


class PaginationBar(MDBoxLayout):
    """
    Пагинация с динамическими центрированными рядами цифр.
    center_zone БЕЗ padding — клик по краю цифры работает.
    """
    LONG_PRESS_JUMP_ROWS = 10
    MIN_ROW_SIZE = 3
    MAX_ROW_SIZE = 9
    BTN_WIDTH = dp(32)
    BTN_SPACING = dp(2)

    def __init__(self, on_page_select=None, **kwargs):
        super().__init__(**kwargs)
        self.on_page_select = on_page_select
        self.current_page_index = 0
        self.total_pages = 1
        self._last_total = None
        self._last_per_page = None
        self._window_start = 0
        self.page_buttons = []

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.spacing = dp(2)
        self.md_bg_color = [0, 0, 0, 0]
        self.padding = [dp(4)] * 4

        self.left_arrow = ArrowButton(
            icon_name="chevron-left",
            short_press=self._go_prev_row,
            long_press=self._jump_prev_rows,
        )
        self.add_widget(self.left_arrow)

        self.center_zone = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0],
            padding=[dp(0)] * 4,
        )
        self.add_widget(self.center_zone)

        anchor = AnchorLayout(
            anchor_x='center', anchor_y='center',
            size_hint=(1, 1),
        )
        self.center_zone.add_widget(anchor)

        self.container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            size_hint_x=None,
            size_hint_y=1,
            spacing=self.BTN_SPACING,
            padding=[dp(0)] * 4,
            md_bg_color=[0, 0, 0, 0],
        )
        anchor.add_widget(self.container)

        self.right_arrow = ArrowButton(
            icon_name="chevron-right",
            short_press=self._go_next_row,
            long_press=self._jump_next_rows,
        )
        self.add_widget(self.right_arrow)

        self.update_theme_colors()

    def _calc_row_size(self):
        try:
            avail = self.center_zone.width
        except Exception:
            avail = 0
        if avail <= 0:
            return self.MIN_ROW_SIZE
        unit = self.BTN_WIDTH + self.BTN_SPACING
        n = int((avail + self.BTN_SPACING) / unit)
        return max(self.MIN_ROW_SIZE, min(self.MAX_ROW_SIZE, n))

    def _max_window_start(self):
        row_size = self._calc_row_size()
        return max(0, self.total_pages - row_size)

    def _clamp_window_start(self, start):
        return max(0, min(start, self._max_window_start()))

    def _center_window_on(self, page_index):
        row_size = self._calc_row_size()
        half = row_size // 2
        start = page_index - half
        self._window_start = self._clamp_window_start(start)

    def _window_contains(self, page_index):
        row_size = self._calc_row_size()
        return self._window_start <= page_index < self._window_start + row_size

    def _rebuild_row(self):
        self.container.clear_widgets()
        self.page_buttons = []

        if self.total_pages <= 0:
            self.container.width = 0
            self._update_arrows()
            return

        row_size = self._calc_row_size()
        start = self._window_start
        end = min(start + row_size, self.total_pages)

        if (end - start < row_size) and start > 0:
            start = max(0, self.total_pages - row_size)
            end = min(start + row_size, self.total_pages)
            self._window_start = start

        total_w = 0
        for idx, i in enumerate(range(start, end)):
            btn = PageButton(
                text=str(i + 1),
                index=i,
                on_click=self._on_page_click,
            )
            btn.set_selected(i == self.current_page_index)
            self.page_buttons.append(btn)
            self.container.add_widget(btn)
            total_w += btn.width
            if idx > 0:
                total_w += self.container.spacing

        self.container.width = total_w
        self._update_arrows()

    def _update_arrows(self):
        self.left_arrow.set_enabled(self._window_start > 0)
        can_next = self._window_start < self._max_window_start()
        self.right_arrow.set_enabled(can_next)

    def set_total(self, total_items, per_page, current_page=0, on_click=None):
        if on_click:
            self.on_page_select = on_click
        new_total_pages = max(1, (total_items + per_page - 1) // per_page)

        if (self._last_total == total_items
                and self._last_per_page == per_page
                and self.total_pages == new_total_pages):
            self.set_current_page(current_page)
            return

        self._last_total = total_items
        self._last_per_page = per_page
        self.total_pages = new_total_pages
        self.current_page_index = max(0, min(current_page, self.total_pages - 1))
        self._center_window_on(self.current_page_index)
        self._rebuild_row()
        self.update_theme_colors()

    def set_current_page(self, page):
        self.current_page_index = max(0, min(page, self.total_pages - 1))
        if not self._window_contains(self.current_page_index):
            self._center_window_on(self.current_page_index)
            self._rebuild_row()
        else:
            for btn in self.page_buttons:
                btn.set_selected(btn.page_index == self.current_page_index)
            self._update_arrows()
        # update_theme_colors не вызываем — set_selected уже сделал всё

    def _on_page_click(self, index):
        if index == self.current_page_index:
            return
        self.set_current_page(index)
        if self.on_page_select:
            self.on_page_select(index)

    def _go_prev_row(self):
        if self._window_start <= 0:
            return
        step = self._calc_row_size()
        self._window_start = self._clamp_window_start(self._window_start - step)
        self._rebuild_row()
        self.update_theme_colors()

    def _go_next_row(self):
        if self._window_start >= self._max_window_start():
            return
        step = self._calc_row_size()
        self._window_start = self._clamp_window_start(self._window_start + step)
        self._rebuild_row()
        self.update_theme_colors()

    def _jump_prev_rows(self):
        step = self._calc_row_size() * self.LONG_PRESS_JUMP_ROWS
        self._window_start = self._clamp_window_start(self._window_start - step)
        self._rebuild_row()
        self.update_theme_colors()

    def _jump_next_rows(self):
        step = self._calc_row_size() * self.LONG_PRESS_JUMP_ROWS
        self._window_start = self._clamp_window_start(self._window_start + step)
        self._rebuild_row()
        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        arrow_color = [0, 0, 0, 1] if theme_id == 'light' else [1, 1, 1, 1]
        self.left_arrow.set_color(arrow_color)
        self.right_arrow.set_color(arrow_color)
        for btn in self.page_buttons:
            btn.set_selected(btn.page_index == self.current_page_index)

    def on_size(self, *args):
        if not self.page_buttons and self.total_pages <= 1:
            return
        Clock.schedule_once(lambda dt: self._rebuild_row(), 0)


# ============ ОСНОВНОЙ ЭКРАН ============

class SongsScreen(BaseScreen):
    MIN_PAGE_SIZE = 3

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.current_artist = None
        self.is_search_mode = False
        self.search_results = []
        self.current_language = 'ru'

        self._all_artists = []
        self._page = 0
        self._page_size = 8
        self._batch_size = 200
        self._total_artists = 0
        self._artists_cache = {}
        self._batch_loading = False
        self._pending_page = None

        self._all_search_results = []
        self._search_page = 0
        self._search_token = ""
        self._search_in_progress = False

        self._load_token = 0
        self._last_display_key = None
        self._last_search_display_key = None

        self.search_bar = None
        self._hint_label = None
        self._result_label = None
        self.songs_menu = None
        self._hint_timer = None
        self.cards_container = None
        self._cards_wrapper = None
        self._pagination_bar = None
        self._search_pagination_bar = None

        load_shared_icons_sync()
        self.init_ui()
        self.load_background()
        logger.info('Экран песен создан')

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
                    self.texture = CoreImage(BytesIO(bg_data), ext="jpg").texture
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')
        self.update_screen_background()

    def _update_rect(self, *args):
        if hasattr(self, 'bg_rect') and self.bg_rect:
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def update_screen_background(self):
        if not hasattr(self, 'bg_color_inst'):
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
        if self.search_bar:
            self.search_bar.update_theme_colors()
        if self.songs_menu:
            self.songs_menu.update_theme_colors()
        if self._pagination_bar:
            self._pagination_bar.update_theme_colors()
        if self._search_pagination_bar:
            self._search_pagination_bar.update_theme_colors()
        if self._hint_label:
            self._hint_label.text_color = SongsColors.get_text_secondary(settings_manager.theme)
        if self._result_label:
            self._result_label.text_color = SongsColors.get_hint_color(settings_manager.theme)
        if self.cards_container:
            self.cards_container.update_theme_colors()

    def update_language(self):
        if self.search_bar:
            self.search_bar.update_language()
        self._restore_hint()
        if self.songs_menu and self.songs_menu.alphabet_menu:
            self.songs_menu.alphabet_menu._populate_items()
        if self._result_label and self._result_label.opacity > 0:
            if self.is_search_mode:
                self._update_search_result_label()
            elif self.current_letter and self._all_artists:
                self._update_result_label_for_artists()

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))

        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        padding = layout_config.get_content_padding()

        menu_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(56),
            md_bg_color=[0, 0, 0, 0],
            padding=[padding[0], 0, padding[2], 0]
        )
        self.songs_menu = SongsMenu(
            on_language_toggle=self._toggle_language,
            on_letter_press=self.on_letter_press,
            current_language=self.current_language
        )
        menu_container.add_widget(self.songs_menu)
        main_layout.add_widget(menu_container)

        main_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

        search_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(52),
            padding=[padding[0], 0, padding[2], 0]
        )
        self.search_bar = SearchBar(on_search=self.do_search, on_clear=self.clear_search)
        search_container.add_widget(self.search_bar)
        main_layout.add_widget(search_container)

        main_layout.add_widget(Widget(size_hint_y=None, height=dp(2)))

        self._hint_label = MDLabel(
            text=get_text('search_artists'),
            font_size=sp(13), halign="center",
            size_hint_y=None, height=dp(20),
            theme_text_color="Custom",
            text_color=SongsColors.get_text_secondary(settings_manager.theme),
            bold=False
        )
        main_layout.add_widget(self._hint_label)

        self._result_label = MDLabel(
            text="", font_size=sp(12), halign="center",
            size_hint_y=None, height=dp(18),
            theme_text_color="Custom",
            text_color=SongsColors.get_hint_color(settings_manager.theme),
            opacity=0, bold=True
        )
        main_layout.add_widget(self._result_label)

        self._cards_wrapper = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            spacing=0, padding=[padding[0], dp(4), padding[2], dp(0)],
            md_bg_color=[0, 0, 0, 0]
        )
        self.cards_container = PageCardsContainer()
        self._cards_wrapper.add_widget(self.cards_container)
        main_layout.add_widget(self._cards_wrapper)

        self._pagination_bar = PaginationBar(on_page_select=self._on_page_selected_from_bar)
        self._pagination_bar.height = 0
        self._pagination_bar.opacity = 0
        self._pagination_bar.disabled = True
        main_layout.add_widget(self._pagination_bar)

        self._search_pagination_bar = PaginationBar(on_page_select=self._on_search_page_selected)
        self._search_pagination_bar.height = 0
        self._search_pagination_bar.opacity = 0
        self._search_pagination_bar.disabled = True
        main_layout.add_widget(self._search_pagination_bar)

        bottom_padding = layout_config.get_bottom_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))

        self.clear_widgets()
        self.add_widget(main_layout)
        self.update_theme_colors()

        Clock.schedule_once(lambda dt: self._recalc_page_size(), 0.1)

    def _toggle_language(self):
        pass

    def _calc_page_size(self):
        try:
            wrapper_h = self._cards_wrapper.height
        except Exception:
            wrapper_h = 0
        if wrapper_h <= 0:
            return 8
        card_h = dp(48) + dp(6)
        n = int(wrapper_h / card_h)
        return max(self.MIN_PAGE_SIZE, n)

    def _recalc_page_size(self):
        new_size = self._calc_page_size()
        if new_size == self._page_size:
            return
        old_page = self._page
        self._page_size = new_size
        if self.current_letter:
            self._page = old_page
            self._ensure_valid_page()
            self._display_current_page()

    def on_size(self, *args):
        Clock.schedule_once(lambda dt: self._recalc_page_size(), 0.15)

    def _ensure_valid_page(self):
        if self._total_artists <= 0:
            self._page = 0
            return
        max_page = (self._total_artists - 1) // self._page_size
        if self._page > max_page:
            self._page = max_page

    # ---------- ПОИСК ----------

    def _show_search_page(self, page_idx):
        if not self._all_search_results:
            self._hide_search_pagination()
            return
        self._search_page = page_idx
        start = page_idx * self._page_size
        end = min(start + self._page_size, len(self._all_search_results))
        page_slice = self._all_search_results[start:end]

        first_song = page_slice[0]['song_id'] if page_slice else 0
        display_key = (self._search_page, len(page_slice), first_song)
        if self._last_search_display_key != display_key:
            self.cards_container.set_songs(page_slice, self.on_song_selected)
            self._last_search_display_key = display_key

        total_pages = (len(self._all_search_results) + self._page_size - 1) // self._page_size
        if total_pages > 1:
            self._show_search_pagination(len(self._all_search_results))
        else:
            self._hide_search_pagination()

        self._update_search_result_label()
        songs_state.save_search({
            'query': self.search_bar.current_query if self.search_bar else "",
            'search_page': self._search_page,
        })

    def _update_search_result_label(self):
        if not self._all_search_results:
            self._hide_result_label()
            return
        start = self._search_page * self._page_size
        end = min(start + self._page_size, len(self._all_search_results))
        self._show_result_label(
            f"{get_text('songs_found')}: {end - start} "
            f"{get_text('of')} {len(self._all_search_results)}"
        )

    def _hide_search_pagination(self):
        if not self._search_pagination_bar:
            return
        self._search_pagination_bar.height = 0
        self._search_pagination_bar.opacity = 0
        self._search_pagination_bar.disabled = True

    def _show_search_pagination(self, total_items):
        if not self._search_pagination_bar:
            return
        self._search_pagination_bar.height = dp(56)
        self._search_pagination_bar.opacity = 1
        self._search_pagination_bar.disabled = False
        self._search_pagination_bar.set_total(
            total_items, self._page_size, self._search_page,
            on_click=self._on_search_page_selected
        )

    def _on_search_page_selected(self, page_index):
        if page_index == self._search_page:
            return
        self._show_search_page(page_index)

    # ---------- ПАГИНАЦИЯ АРТИСТОВ ----------

    def _hide_pagination(self):
        if not self._pagination_bar:
            return
        self._pagination_bar.height = 0
        self._pagination_bar.opacity = 0
        self._pagination_bar.disabled = True

    def _show_pagination_bar(self):
        if not self._pagination_bar:
            return
        if self._total_artists <= self._page_size:
            self._hide_pagination()
            return
        self._pagination_bar.height = dp(56)
        self._pagination_bar.opacity = 1
        self._pagination_bar.disabled = False
        self._pagination_bar.set_total(
            self._total_artists, self._page_size, self._page
        )

    def _on_page_selected_from_bar(self, page_index):
        if page_index == self._page:
            return
        self._load_page(page_index)

    # ---------- КЭШ И ЗАГРУЗКА АРТИСТОВ ----------

    def _is_page_cached(self, cache, page):
        start = page * self._page_size
        total = cache['total']
        end = min(start + self._page_size, total) if total else start + self._page_size
        for idx in range(start, end):
            if idx not in cache['items']:
                return False
        return True

    def _build_page_slice(self, cache, page):
        start = page * self._page_size
        end = start + self._page_size
        total = cache['total']
        if total:
            end = min(end, total)
        return [cache['items'][i] for i in range(start, end) if i in cache['items']]

    def _load_page(self, page):
        if not self.current_letter:
            return
        cache = self._artists_cache.get(self.current_letter)
        if cache is None:
            return
        if cache.get('failed'):
            self._load_batch(letter=self.current_letter, batch_offset=0, target_page=page)
            return
        self._total_artists = cache['total']
        self._page = page
        if self._is_page_cached(cache, page):
            self._all_artists = self._build_page_slice(cache, page)
            self._display_current_page()
            return
        if self._batch_loading:
            self._pending_page = page
            return
        batch_offset = (page * self._page_size) // self._batch_size * self._batch_size
        self._load_batch(letter=self.current_letter, batch_offset=batch_offset, target_page=page)

    def _load_batch(self, letter, batch_offset, target_page):
        cache = self._artists_cache.get(letter)
        if cache is None:
            cache = {'items': {}, 'total': 0, 'batches': set(), 'failed': False}
            self._artists_cache[letter] = cache
        if batch_offset in cache['batches']:
            self._batch_loading = False
            self._all_artists = self._build_page_slice(cache, target_page)
            self._display_current_page()
            return

        self._load_token += 1
        my_token = self._load_token
        self._batch_loading = True
        self._show_loading()

        def _on_success(data):
            if my_token != self._load_token:
                return
            try:
                self._batch_loading = False
                cache['failed'] = False
                if not isinstance(data, dict):
                    data = {"artists": [], "total": 0}
                artists = data.get('artists', []) or []
                total = data.get('total', 0) or 0
                for i, a in enumerate(artists):
                    name = a.get('artist') if isinstance(a, dict) else None
                    count = a.get('songs_count', 0) if isinstance(a, dict) else 0
                    if name and (letter != '#' or self._matches_letter(name, '#')):
                        cache['items'][batch_offset + i] = {
                            'artist': name, 'songs_count': count,
                        }
                if total > 0:
                    cache['total'] = total
                cache['batches'].add(batch_offset)
                self._total_artists = cache['total']
                logger.info(
                    f"📦 Батч '{letter}' offset={batch_offset}: "
                    f"+{len(artists)} (в кеше {len(cache['items'])}/{cache['total']})"
                )
                show_page = self._pending_page
                self._pending_page = None
                if show_page is None:
                    show_page = target_page
                self._page = show_page
                self._ensure_valid_page()
                if not self._is_page_cached(cache, self._page):
                    if cache['total'] and self._page * self._page_size >= cache['total']:
                        self._hide_loading()
                        self._all_artists = self._build_page_slice(cache, self._page)
                        self._display_current_page()
                        return
                    batch_offset2 = (self._page * self._page_size) // self._batch_size * self._batch_size
                    self._load_batch(letter=letter, batch_offset=batch_offset2, target_page=self._page)
                    return
                self._hide_loading()
                self._all_artists = self._build_page_slice(cache, self._page)
                self._display_current_page()
            except Exception as e:
                self._batch_loading = False
                self._pending_page = None
                self._hide_loading()
                logger.error(f"❌ Ошибка _on_success: {e}")
                self._show_empty(get_text('loading_error'))

        def _on_error(req, err):
            if my_token != self._load_token:
                return
            self._batch_loading = False
            self._pending_page = None
            self._hide_loading()
            cache['failed'] = True
            logger.warning(f"⚠️ Ошибка загрузки '{letter}': {err}")
            self._show_retry_error(letter)

        if letter == '#':
            api.get_artists_by_digits(
                limit=self._batch_size, offset=batch_offset,
                on_success=_on_success, on_failure=_on_error
            )
        else:
            api.get_artists_by_letter(
                letter=letter, limit=self._batch_size, offset=batch_offset,
                on_success=_on_success, on_failure=_on_error
            )

    def _show_retry_error(self, letter):
        self.cards_container.clear()
        self._show_result_label(get_text('loading_error'))
        self._hint_label.text = get_text(
            'tap_letter_to_retry',
            'Нажмите букву ещё раз, чтобы повторить'
        )

    def _matches_letter(self, name, letter):
        if not name or not letter:
            return False
        first = name[0]
        if letter == '#':
            cat = unicodedata.category(first)
            return cat.startswith('P') or cat in ('Sc', 'Sm', 'Sk')
        return first == letter

    def _load_artists(self, letter):
        self.current_artist = None
        self.current_letter = letter
        self._hide_result_label()
        self._page = 0
        self._batch_loading = False
        self._pending_page = None

        cache = self._artists_cache.get(letter)
        if cache is not None and not cache.get('failed') and (cache['batches'] or cache['total'] > 0):
            self._total_artists = cache['total']
            if self._is_page_cached(cache, 0):
                self._all_artists = self._build_page_slice(cache, 0)
                self._display_current_page()
            else:
                self._load_page(0)
            return

        self._all_artists = []
        self._total_artists = 0
        self.cards_container.clear()
        self._hide_empty()
        self._hide_pagination()
        self._artists_cache[letter] = {'items': {}, 'total': 0, 'batches': set(), 'failed': False}
        self._load_batch(letter=letter, batch_offset=0, target_page=0)

    # ---------- КЛИКИ ----------

    def on_song_selected(self, song_id, title):
        if not song_id:
            notify.error(get_text('load_error'))
            return
        self.save_search_state()
        self.save_current_state()
        screen_state.set_previous_screen('songs')
        if self.manager:
            if self.manager.has_screen('search_detail'):
                self.manager.get_screen('search_detail').set_song(song_id)
                self.manager.current = 'search_detail'
            elif self.manager.has_screen('song_detail'):
                scr = self.manager.get_screen('song_detail')
                scr.set_previous_screen('songs')
                scr.set_song(song_id)
                self.manager.current = 'song_detail'

    def on_letter_press(self, letter):
        self.is_search_mode = False
        self.current_artist = None
        self.search_bar.clear()
        if self.songs_menu:
            self.songs_menu.set_current_letter(letter)
        self._load_artists(letter)

    def on_artist_selected(self, artist, songs_count):
        self.save_current_state()
        screen_state.set_previous_screen('songs')
        screen_state.set_artist_songs_data(artist, 1.0)
        if self.manager and self.manager.has_screen('artist_songs'):
            scr = self.manager.get_screen('artist_songs')
            scr.artist_name = artist
            scr._total_songs = 0
            scr._page = 0
            scr._is_loading = False
            scr._batch_loading = False
            scr._pending_page = None
            scr._update_top_nav_title(artist)
            scr._load_artist_songs(artist)
            self.manager.current = 'artist_songs'

    # ---------- ПОИСК ----------

    def do_search(self, query):
        query = query.strip()
        if len(query) < 2:
            self._show_temporary_hint(get_text('min_chars'), 1.5)
            return
        self.is_search_mode = True
        self.current_letter = None
        self.current_artist = None
        if self.songs_menu:
            self.songs_menu.set_current_letter(None)
        self._search_token = str(time.time())
        token = self._search_token
        self._search_in_progress = True
        self._last_search_display_key = None
        songs_state.save_search({'query': query, 'search_page': 0})
        self._hide_result_label()
        self._show_loading()
        self.cards_container.clear()
        self._hide_pagination()
        self._hide_search_pagination()
        api.search_songs(
            query=query, limit=100,
            on_success=lambda res: self._on_search_success(res, token),
            on_failure=lambda req, err: self._on_search_failed(req, err, token)
        )

    def _on_search_success(self, results, token):
        if token != self._search_token:
            return
        self._search_in_progress = False
        raw = results.get('results', []) if isinstance(results, dict) else (
            results if isinstance(results, list) else []
        )
        self._all_search_results = [
            {'song_id': r.get('song_id', 0),
             'artist': r.get('artist', ''),
             'title': r.get('title', '')}
            for r in raw if isinstance(r, dict)
        ]
        self._search_results = self._all_search_results
        self._search_page = 0
        self._last_search_display_key = None
        if not self._all_search_results:
            self.cards_container.clear()
            self._hide_result_label()
            self._show_empty(get_text('nothing_found'))
            self._hide_search_pagination()
        else:
            self._show_search_page(0)

    def _on_search_failed(self, req, error, token):
        if token != self._search_token:
            return
        self._search_in_progress = False
        self._all_search_results = []
        self._search_results = []
        self.cards_container.clear()
        self._hide_result_label()
        self._hide_search_pagination()
        self._show_empty(get_text('search_error'))
        logger.error(f"Ошибка поиска: {error}")

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self._all_search_results = []
        self._search_in_progress = False
        self._search_token = str(time.time())
        self._last_search_display_key = None
        songs_state.invalidate_search()
        self._hide_result_label()
        self._hide_loading()
        self._hide_empty()
        self._hide_pagination()
        self._hide_search_pagination()
        self.current_letter = None
        self.current_artist = None
        if self.songs_menu:
            self.songs_menu.set_current_letter(None)
        self.cards_container.clear()

    # ---------- ОТОБРАЖЕНИЕ ----------

    def _display_current_page(self):
        self._hide_loading()
        self._hide_search_pagination()
        if not self._all_artists:
            self._show_empty()
            self.cards_container.clear()
            self._hide_pagination()
            return
        self._hide_empty()
        first_artist = self._all_artists[0].get('artist', '') if self._all_artists else ''
        display_key = (self.current_letter, self._page, len(self._all_artists), first_artist)
        if self._last_display_key != display_key:
            self.cards_container.set_artists(self._all_artists, self.on_artist_selected)
            self._last_display_key = display_key
        current_count = min((self._page + 1) * self._page_size, self._total_artists)
        self._show_result_label(
            f"{get_text('artists')}: {current_count} "
            f"{get_text('of')} {self._total_artists}"
        )
        self.save_current_state()
        if self._total_artists > self._page_size:
            self._show_pagination_bar()
        else:
            self._hide_pagination()

    def _show_temporary_hint(self, text, duration=1.5):
        if self._hint_label:
            self._hint_label.text = text
            if self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._restore_hint(), duration)

    def _restore_hint(self):
        self._hint_timer = None
        if self._hint_label is None:
            return
        if self.is_search_mode:
            self._hint_label.text = ""
        elif self.current_artist:
            self._hint_label.text = f"{get_text('artist_songs')}: {self.current_artist}"
        else:
            self._hint_label.text = get_text('search_artists')

    def _show_result_label(self, text):
        if self._result_label:
            self._result_label.text = text
            self._result_label.opacity = 1

    def _hide_result_label(self):
        if self._result_label:
            self._result_label.text = ""
            self._result_label.opacity = 0

    def _show_empty(self, text=None):
        self._show_result_label(text or get_text('no_artists'))

    def _hide_empty(self):
        self._hide_result_label()

    def _show_loading(self, text=None):
        if self._hint_label:
            self._hint_label.text = text or get_text('loading', 'Загрузка...')

    def _hide_loading(self):
        self._restore_hint()

    # ---------- СОХРАНЕНИЕ / ВОССТАНОВЛЕНИЕ (save_alphabet / get_alphabet) ----------

    def save_current_state(self):
        songs_state.save_alphabet({
            'current_letter': self.current_letter,
            'current_language': self.current_language,
            'page': self._page,
            'total_artists': self._total_artists,
            'has_more': True,
            'scroll_position': 1.0,
        })

    def save_search_state(self):
        if not self.is_search_mode:
            return
        songs_state.save_search({
            'query': self.search_bar.current_query if self.search_bar else "",
            'search_page': self._search_page,
        })

    def restore_search_state(self):
        saved = songs_state.get_search()
        if not saved:
            return
        query = saved.get('query', '')
        if not query:
            return
        self.search_bar.set_text(query)
        self.is_search_mode = True
        self.current_letter = None
        self.current_artist = None
        if self.songs_menu:
            self.songs_menu.set_current_letter(None)
        self._search_page = saved.get('search_page', 0)
        if self._all_search_results:
            self._show_search_page(self._search_page)
        else:
            self._show_loading()
            token = str(time.time())
            self._search_token = token
            api.search_songs(
                query=query, limit=100,
                on_success=lambda res: self._on_search_success(res, token),
                on_failure=lambda req, err: self._on_search_failed(req, err, token)
            )

    def restore_state(self):
        if self.manager and self.manager.current != 'songs':
            return False
        saved = songs_state.get_alphabet(allow_stale=True)
        if not saved:
            return False
        try:
            self.current_letter = saved.get('current_letter')
            self.current_language = saved.get('current_language', 'ru')
            self._total_artists = saved.get('total_artists', 0)
            self._page = saved.get('page', 0)
            if self.songs_menu:
                self.songs_menu.set_language(self.current_language)
            if self.current_letter and self.songs_menu:
                self.songs_menu.set_current_letter(self.current_letter)
            if self.current_letter and self.current_letter in self._artists_cache:
                cache = self._artists_cache[self.current_letter]
                self._total_artists = cache['total']
                self._ensure_valid_page()
                if self._is_page_cached(cache, self._page):
                    self._all_artists = self._build_page_slice(cache, self._page)
                    self._display_current_page()
                else:
                    self._load_page(self._page)
            else:
                self.cards_container.clear()
                self._restore_hint()
                self._hide_result_label()
                self._hide_pagination()
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления: {e}")
            return False

    def _update_result_label_for_artists(self):
        if self.current_letter and self._all_artists:
            current_count = min((self._page + 1) * self._page_size, self._total_artists)
            self._show_result_label(
                f"{get_text('artists')}: {current_count} "
                f"{get_text('of')} {self._total_artists}"
            )

    # ---------- LIFECYCLE ----------

    def on_pre_leave(self):
        self.save_search_state()
        self.save_current_state()
        return super().on_pre_leave()

    def on_enter(self):
        super().on_enter()
        Clock.schedule_once(lambda dt: self._recalc_page_size(), 0.05)

        if self._last_display_key is not None and not self.is_search_mode:
            self._update_result_label_for_artists()
            return
        self.restore_search_state()
        restored = self.restore_state()
        if not restored and not self.is_search_mode:
            self._restore_hint()
            self._hide_result_label()
            self.cards_container.clear()
            self._hide_pagination()
            self._hide_search_pagination()

    def on_leave(self):
        self.save_current_state()
        if self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        if self.manager:
            self.manager.current = 'home'