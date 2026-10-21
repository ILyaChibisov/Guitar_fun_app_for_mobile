# screens/songs_screen.py
"""
Экран песен - с единым меню (АЛФАВИТ) и поиском.
Поддерживает 3 темы (green, light, dark) и 6 языков.
Сохранение состояния и позиции скролла.
"""
import time
import re
import unicodedata
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from io import BytesIO
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.animation import Animation

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp

from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.factory import Factory

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
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
# ПРОВЕРКА СИМВОЛА
# ============================================================

def is_letter_or_digit(char):
    """True, если символ — буква или цифра. False для # ! ( ) - & эмодзи и т.п."""
    if not char:
        return False
    if char.isdigit():
        return True
    # Буква (включая кириллицу, латиницу, любые Unicode-буквы)
    if char.isalpha():
        return True
    return False


def is_non_letter_char(char):
    """
    True для '#' — если символ не буква (цифры, спецсимволы, эмодзи, знаки).
    То есть '#'-категория — это всё, что НЕ буква.
    """
    if not char:
        return False
    return not char.isalpha()


# ============================================================
# ЦВЕТА ДЛЯ ПЕСЕН
# ============================================================

class SongsColors:
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
    def get_hint_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        else:
            return [1, 1, 1, 0.5]


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
                img = CoreImage(BytesIO(rus_data), ext="png")
                _shared_rus_flag_texture = img.texture

            eng_data = load_asset_as_bytes('eng_png')
            if eng_data:
                img = CoreImage(BytesIO(eng_data), ext="png")
                _shared_eng_flag_texture = img.texture

            song_data = load_asset_as_bytes('song_png')
            if song_data:
                img = CoreImage(BytesIO(song_data), ext="png")
                _shared_song_icon_texture = img.texture

            artist_data = load_asset_as_bytes('artist_png')
            if artist_data:
                img = CoreImage(BytesIO(artist_data), ext="png")
                _shared_artist_icon_texture = img.texture

        except Exception as e:
            logger.error(f"Ошибка загрузки иконок: {e}")


# ============ ПОИСКОВАЯ СТРОКА ============

class SearchBar(MDCard):
    def __init__(self, on_search=None, on_clear=None,
                 hint_text=None, button_text=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(16)]
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
            size_hint=(None, None), size=(dp(30), dp(30)), radius=[dp(15)],
            md_bg_color=[0, 0, 0, 0], elevation=0, pos_hint={'center_y': 0.5},
            opacity=0, disabled=True,
        )

        self.clear_btn = MDIconButton(
            icon="close-circle-outline", size_hint=(1, 1), theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0], on_release=self._on_clear_pressed
        )
        self.clear_wrapper.add_widget(self.clear_btn)

        self.search_btn = MDRaisedButton(
            text="", size_hint=(None, None), size=(dp(64), dp(36)),
            text_color=[1, 1, 1, 1], font_size=sp(13), elevation=0,
            pos_hint={'center_y': 0.5}
        )
        try:
            self.search_btn._radius = dp(10)
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
            self.line_width = 1.5
            self.search_field.foreground_color = text_p
            self.search_field.hint_text_color = text_s
            self.search_field.cursor_color = accent
            self.clear_btn.icon_color = accent
            self.search_btn.md_bg_color = accent
        elif theme_id == 'dark':
            self.md_bg_color = [0.15, 0.15, 0.15, 1]
            self.line_color = line
            self.line_width = 1.5
            self.search_field.foreground_color = text_p
            self.search_field.hint_text_color = text_s
            self.search_field.cursor_color = accent
            self.clear_btn.icon_color = accent
            self.search_btn.md_bg_color = accent
        else:
            self.md_bg_color = [1, 1, 1, 1]
            self.line_color = [0.08, 0.35, 0.20, 1]
            self.line_width = 1.4
            self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]
            self.search_field.hint_text_color = [0.55, 0.55, 0.55, 1]
            self.search_field.cursor_color = [0.1, 0.1, 0.1, 1]
            self.clear_btn.icon_color = [0.4, 0.4, 0.4, 0.8]
            self.search_btn.md_bg_color = [0.10, 0.42, 0.25, 1]

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
        theme_id = settings_manager.theme
        base_width = 1.5 if theme_id in ('dark', 'light') else 1.4
        self.line_width = base_width + 0.3 if value else base_width

    def set_text(self, text):
        self.search_field.text = text or ""
        self._on_text_change(None, self.search_field.text)

    def clear(self):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""

    def focus(self):
        self.search_field.focus = True


# ============ КОМПОНЕНТЫ МЕНЮ ============

class LetterButton(MDBoxLayout):
    def __init__(self, text, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press
        self.is_selected = False

        self.size_hint = (None, 1)
        self.width = dp(38)
        self.padding = [dp(2)] * 4
        self.spacing = 0
        self.md_bg_color = [0, 0, 0, 0]

        self.label = MDLabel(
            text=text, font_size=sp(16), halign="center", valign="middle",
            theme_text_color="Custom", text_color=[1, 1, 1, 0.7], bold=True,
            size_hint=(1, 1)
        )

        self.add_widget(self.label)

        self.bind(on_touch_down=self._on_touch_down)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)
        self._update_style()

    def _on_enter(self, *args):
        if not self.is_selected:
            self.md_bg_color = [1, 1, 1, 0.05]
            self.label.text_color = [1, 1, 1, 0.9]

    def _on_leave(self, *args):
        if not self.is_selected:
            self.md_bg_color = [0, 0, 0, 0]
            theme_id = settings_manager.theme
            self.label.text_color = SongsColors.get_text_secondary(theme_id)

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self.on_press_callback:
                self.on_press_callback(self.btn_text)
            return True
        return False

    def set_selected(self, selected):
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
    """Некликабельная иконка-флаг перед группой букв."""
    def __init__(self, flag_type='ru', **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(38)
        self.padding = [dp(2)] * 4
        self.spacing = 0
        self.md_bg_color = [0, 0, 0, 0]
        self.flag_type = flag_type

        texture = None
        if flag_type == 'ru':
            texture = _shared_rus_flag_texture
        elif flag_type == 'en':
            texture = _shared_eng_flag_texture

        # AnchorLayout с центрированием по X и Y
        container = AnchorLayout(
            anchor_x='center',
            anchor_y='center',
            size_hint=(1, 1)
        )

        if texture:
            img = Image(
                texture=texture,
                size_hint=(None, None),
                size=(dp(22), dp(22)),
                allow_stretch=True,
                keep_ratio=True
            )
            container.add_widget(img)
        else:
            lbl = MDLabel(
                text="RU" if flag_type == 'ru' else "EN",
                font_size=sp(10),
                halign="center",
                valign="middle",
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.6],
                bold=True
            )
            container.add_widget(lbl)

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
            on_release=lambda x: self.scroll(-1)
        )
        self.right_arrow = MDIconButton(
            icon="chevron-right", size_hint=(None, 1), width=dp(28),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll(1)
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
            groups = [
                ('ru', self.RU_LETTERS, True),
                ('symbols', self.DIGITS_LETTERS, False),
                ('en', self.EN_LETTERS, True),
            ]
        else:
            groups = [
                ('en', self.EN_LETTERS, True),
                ('symbols', self.DIGITS_LETTERS, False),
            ]

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
        scroll_amount = 0.2
        new_scroll = self.scroll_view.scroll_x + (direction * scroll_amount)
        new_scroll = max(0, min(1, new_scroll))
        anim = Animation(scroll_x=new_scroll, duration=0.2, t='out_quad')
        anim.start(self.scroll_view)

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
        theme_id = settings_manager.theme
        accent = SongsColors.get_accent(theme_id)
        self.left_arrow.icon_color = accent
        self.right_arrow.icon_color = accent
        for btn in self.buttons:
            btn._update_style()


class SongsMenu(MDCard):
    def __init__(self, on_language_toggle=None, on_letter_press=None,
                 current_language='ru', **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.radius = [dp(16)]
        self.elevation = 0
        self.padding = [dp(4)] * 4
        self.spacing = dp(0)

        self.alphabet_menu = AlphabetMenu(
            on_letter_press=on_letter_press,
            current_language=current_language
        )

        self.add_widget(self.alphabet_menu)
        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = SongsColors.get_card_bg(theme_id)
        self.line_color = SongsColors.get_card_line(theme_id)
        self.line_width = 1.5 if theme_id in ('dark', 'light') else 0.8
        if self.alphabet_menu:
            self.alphabet_menu.update_theme_colors()

    def set_language(self, language):
        self.alphabet_menu.set_language(language)

    def set_current_letter(self, letter):
        self.alphabet_menu.set_current(letter)


# ============ RECYCLEVIEW КАРТОЧКИ ============

class ArtistCard(RecycleDataViewBehavior, MDCard):
    artist_name = StringProperty('')
    songs_count = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.padding = [dp(10), dp(4), dp(10), dp(4)]
        self.spacing = dp(8)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self._build_ui()
        self.update_theme_colors()

    def _build_ui(self):
        self.icon = Image(
            size_hint=(None, 1), width=dp(28),
            allow_stretch=True, keep_ratio=True
        )
        if _shared_artist_icon_texture:
            self.icon.texture = _shared_artist_icon_texture
        else:
            self.icon.text = "🎤"

        self.artist_label = MDLabel(
            font_size=sp(15), theme_text_color="Custom",
            bold=True, shorten=True, shorten_from="right",
            valign="middle", size_hint_x=1
        )

        self.count_label = MDLabel(
            text="", font_size=sp(11), size_hint_x=None, width=dp(40),
            halign="right", valign="middle", theme_text_color="Custom"
        )

        arrow = MDLabel(
            text="›", font_size=sp(22), size_hint_x=None, width=dp(24),
            halign="center", valign="middle", theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon)
        self.add_widget(self.artist_label)
        self.add_widget(self.count_label)
        self.add_widget(arrow)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = SongsColors.get_card_bg(theme_id)
        self.line_color = SongsColors.get_card_line(theme_id)
        self.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5
        self.artist_label.text_color = SongsColors.get_text_primary(theme_id)
        self.count_label.text_color = SongsColors.get_text_secondary(theme_id)

    def refresh_view_attrs(self, rv, index, data):
        self.artist_name = data.get('artist', '')
        self.songs_count = data.get('songs_count', 0)
        self.on_click = data.get('on_click')
        self.artist_label.text = self.artist_name
        self.count_label.text = str(self.songs_count) if self.songs_count > 0 else ""
        self.update_theme_colors()
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.artist_name, self.songs_count)
            return True
        return super().on_touch_down(touch)


class SearchSongCard(RecycleDataViewBehavior, MDCard):
    title = StringProperty('')
    artist = StringProperty('')
    song_id = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.padding = [dp(10), dp(4), dp(10), dp(4)]
        self.spacing = dp(8)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self._build_ui()
        self.update_theme_colors()

    def _build_ui(self):
        self.icon = Image(
            size_hint=(None, 1), width=dp(28),
            allow_stretch=True, keep_ratio=True
        )
        if _shared_song_icon_texture:
            self.icon.texture = _shared_song_icon_texture
        else:
            self.icon.text = "🎵"

        text_layout = MDBoxLayout(
            orientation='vertical', size_hint_x=1,
            spacing=dp(2), pos_hint={'center_y': 0.5}
        )

        self.artist_label = MDLabel(
            font_size=sp(15), size_hint_y=None, height=dp(22),
            theme_text_color="Custom", bold=True,
            shorten=True, shorten_from="right", valign="middle"
        )

        self.title_label = MDLabel(
            font_size=sp(12), size_hint_y=None, height=dp(18),
            theme_text_color="Custom", valign="middle"
        )

        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)

        arrow = MDLabel(
            text="›", font_size=sp(22), size_hint_x=None, width=dp(24),
            halign="center", valign="middle", theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon)
        self.add_widget(text_layout)
        self.add_widget(arrow)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = SongsColors.get_card_bg(theme_id)
        self.line_color = SongsColors.get_card_line(theme_id)
        self.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5
        self.artist_label.text_color = SongsColors.get_text_primary(theme_id)
        self.title_label.text_color = SongsColors.get_text_secondary(theme_id)

    def refresh_view_attrs(self, rv, index, data):
        self.artist = data.get('artist', '')
        self.title = data.get('title', '')
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.artist_label.text = self.artist
        self.title_label.text = self.title
        self.update_theme_colors()
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


Factory.register('ArtistCard', cls=ArtistCard)
Factory.register('SearchSongCard', cls=SearchSongCard)


class SongsRecycleView(RecycleView):
    def __init__(self, on_item_click=None, viewclass='ArtistCard', **kwargs):
        super().__init__(**kwargs)
        self.on_item_click = on_item_click
        self.animate_scroll = False
        self.size_hint = (1, 1)
        self.clip = True
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]
        self.viewclass = viewclass

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(48) * 50,
            orientation='vertical',
            spacing=dp(2)
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.add_widget(self.layout_manager)

    def set_items(self, items, on_click):
        data = []
        for item in items:
            item_data = item.copy()
            item_data['on_click'] = on_click
            data.append(item_data)
        self.data = data
        self.refresh_from_data()

    def set_songs(self, songs, on_click):
        data = []
        for song in songs:
            data.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'artist': song.get('artist', ''),
                'on_click': on_click
            })
        self.data = data
        self.refresh_from_data()

    def clear(self):
        self.data = []
        self.refresh_from_data()


# ============ ОСНОВНОЙ ЭКРАН ============

class SongsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.current_artist = None
        self.is_search_mode = False
        self.search_results = []
        self.current_language = 'ru'
        self._selected_song_id = None
        self._temp_scroll_position = None
        self._is_restoring = False
        self._saved_scroll_position = 1.0
        self._is_artist_songs_mode = False

        self._all_artists = []
        self._page = 0
        self._limit = 200
        self._is_loading_more = False
        self._has_more = True
        self._loading_all = False
        self._total_artists = 0

        self.search_bar = None
        self._main_label = None
        self._result_label = None
        self._songs_count_label = None
        self.songs_menu = None
        self._songs_menu_widget = None
        self._hint_timer = None
        self.recycle_view = None
        self._main_layout = None
        self._menu_container = None

        self._search_query = ""
        self._search_results = []
        self._is_search_mode = False

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
        if not hasattr(self, 'bg_color_inst'): return
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
        if self._main_label:
            theme_id = settings_manager.theme
            self._main_label.text_color = SongsColors.get_text_secondary(theme_id)
        if self._result_label:
            theme_id = settings_manager.theme
            self._result_label.text_color = SongsColors.get_hint_color(theme_id)
        if self.recycle_view:
            for child in self.recycle_view.layout_manager.children:
                if hasattr(child, 'update_theme_colors'):
                    child.update_theme_colors()

    def update_language(self):
        if self.search_bar:
            self.search_bar.update_language()
        self._restore_hint()
        if self.songs_menu and self.songs_menu.alphabet_menu:
            self.songs_menu.alphabet_menu._populate_items()
        if self._result_label and self._result_label.opacity > 0:
            if self.is_search_mode:
                self._result_label.text = f"{get_text('songs_found')}: {len(self.search_results)}"
            elif self.current_letter and self._all_artists:
                self._result_label.text = f"{get_text('artists')}: {len(self._all_artists)} / {self._total_artists}"

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))
        self._main_layout = main_layout

        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        content_padding = layout_config.get_content_padding()
        padding = content_padding

        search_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(52),
            padding=[padding[0], 0, padding[2], 0]
        )
        self.search_bar = SearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        search_container.add_widget(self.search_bar)
        main_layout.add_widget(search_container)

        main_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

        self._main_label = MDLabel(
            text=get_text('search_artists'),
            font_size=sp(14), halign="center",
            size_hint_y=None, height=dp(24),
            theme_text_color="Custom"
        )
        main_layout.add_widget(self._main_label)

        main_layout.add_widget(Widget(size_hint_y=None, height=dp(2)))

        menu_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(56),
            md_bg_color=[0, 0, 0, 0],
            padding=[padding[0], 0, padding[2], 0]
        )
        self._menu_container = menu_container

        self.songs_menu = SongsMenu(
            on_language_toggle=self._toggle_language,
            on_letter_press=self.on_letter_press,
            current_language=self.current_language
        )
        menu_container.add_widget(self.songs_menu)
        main_layout.add_widget(menu_container)

        self._result_label = MDLabel(
            text="", font_size=sp(13), halign="center",
            size_hint_y=None, height=dp(20),
            theme_text_color="Custom", opacity=0, bold=True
        )
        main_layout.add_widget(self._result_label)

        bottom_padding = layout_config.get_bottom_padding()

        wrapper = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            spacing=0, padding=[padding[0], dp(4), padding[2], bottom_padding]
        )

        self.recycle_view = SongsRecycleView(
            on_item_click=self.on_item_selected, viewclass='ArtistCard'
        )
        wrapper.add_widget(self.recycle_view)

        main_layout.add_widget(wrapper)

        self.clear_widgets()
        self.add_widget(main_layout)

        self.update_theme_colors()

        logger.info(f"UI песен построен")

    def _toggle_language(self):
        pass

    def _show_hint(self, text):
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None
        if self._main_label:
            self._main_label.text = text

    def _show_temporary_hint(self, text, duration=1.5):
        if self._main_label:
            self._main_label.text = text
            if hasattr(self, '_hint_timer') and self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._restore_hint(), duration)

    def _restore_hint(self):
        if hasattr(self, '_hint_timer'):
            self._hint_timer = None
        if self.is_search_mode:
            self._main_label.text = get_text('search_results')
        elif self.current_artist:
            self._main_label.text = f"{get_text('artist_songs')}: {self.current_artist}"
        else:
            self._main_label.text = get_text('search_artists')

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
        self._show_hint(text or get_text('loading'))

    def _hide_loading(self):
        self._restore_hint()

    # ============ ФИЛЬТРАЦИЯ ПО СИМВОЛУ ============

    def _matches_letter(self, name, letter):
        """Проверяет, подходит ли имя исполнителя под выбранный символ."""
        if not name or not letter:
            return False
        first = name[0]
        if letter == '#':
            # ✅ "#" — только спецсимволы:
            # пунктуация (P*), валюта (Sc), математика (Sm), модификаторы (Sk).
            # Исключаем буквы (L*), цифры (N*), эмодзи/смайлы (So), пробелы (Z*), прочее (C*).
            cat = unicodedata.category(first)
            return cat.startswith('P') or cat in ('Sc', 'Sm', 'Sk')
        return first == letter

    # ============ ЗАГРУЗКА ИСПОЛНИТЕЛЕЙ ============

    def _load_artists(self, letter):
        self.current_artist = None
        self.current_letter = letter
        self._show_loading()
        self._hide_result_label()

        self._page = 0
        self._all_artists = []
        self._has_more = True
        self._is_loading_more = False
        self._total_artists = 0

        self.recycle_view.viewclass = 'ArtistCard'
        self.recycle_view.clear()
        self._hide_empty()

        # ✅ Только '#' идёт через digits, всё остальное (включая 0-9) — через букву
        if letter == '#':
            api.get_artists_by_digits(
                limit=self._limit, offset=0,
                on_success=self._on_digits_first_page_loaded,
                on_failure=self._on_artists_page_failed
            )
        else:
            api.get_artists_by_letter(
                letter=letter, limit=self._limit, offset=0,
                on_success=self._on_artists_first_page_loaded,
                on_failure=self._on_artists_page_failed
            )

    def _on_digits_first_page_loaded(self, data):
        if data is None: data = {"artists": [], "total": 0}
        if not isinstance(data, dict): data = {"artists": [], "total": 0}

        artists = data.get('artists', [])
        total = data.get('total', 0)
        if not isinstance(artists, list):
            artists = []
            total = 0

        # ✅ Фильтрация для '#' — все не-буквенные (цифры, #, спецсимволы, эмодзи)
        filtered_artists = []
        for a in artists:
            name = a.get('artist') if isinstance(a, dict) else None
            if self._matches_letter(name, self.current_letter):
                filtered_artists.append(a)

        self._total_artists = len(filtered_artists)
        for a in filtered_artists:
            name = a.get('artist') if isinstance(a, dict) else None
            count = a.get('songs_count', 0) if isinstance(a, dict) else 0
            if name:
                self._all_artists.append({'artist': name, 'songs_count': count})

        if len(self._all_artists) >= self._total_artists:
            self._has_more = False
            self._display_artists()
            return
        self._load_next_digits_pages()

    def _load_next_digits_pages(self):
        if not self._has_more or self._is_loading_more:
            return
        if self._total_artists > 0 and len(self._all_artists) >= self._total_artists:
            self._has_more = False
            self._display_artists()
            return

        self._is_loading_more = True
        self._page += 1
        offset = self._page * self._limit

        api.get_artists_by_digits(
            limit=self._limit, offset=offset,
            on_success=self._on_digits_next_page_loaded,
            on_failure=self._on_artists_page_failed
        )

    def _on_digits_next_page_loaded(self, data):
        self._is_loading_more = False
        if data is None: data = {"artists": [], "total": 0}
        if not isinstance(data, dict): data = {"artists": [], "total": 0}

        artists = data.get('artists', [])
        if not isinstance(artists, list) or not artists:
            self._has_more = False
            self._display_artists()
            return

        for a in artists:
            name = a.get('artist') if isinstance(a, dict) else None
            if self._matches_letter(name, self.current_letter):
                self._all_artists.append({
                    'artist': name,
                    'songs_count': a.get('songs_count', 0) if isinstance(a, dict) else 0
                })

        if len(self._all_artists) >= self._total_artists:
            self._has_more = False
            self._display_artists()
            return
        Clock.schedule_once(lambda dt: self._load_next_digits_pages(), 0.1)

    def _on_artists_first_page_loaded(self, data):
        if data is None: data = {"artists": [], "total": 0}
        if not isinstance(data, dict): data = {"artists": [], "total": 0}

        artists = data.get('artists', [])
        total = data.get('total', 0)
        if not isinstance(artists, list):
            artists = []
            total = 0

        self._total_artists = total
        for a in artists:
            name = a.get('artist') if isinstance(a, dict) else None
            count = a.get('songs_count', 0) if isinstance(a, dict) else 0
            if name:
                self._all_artists.append({'artist': name, 'songs_count': count})

        if len(self._all_artists) >= total:
            self._has_more = False
            self._display_artists()
            return
        self._load_next_artists_pages()

    def _load_next_artists_pages(self):
        if not self._has_more or self._is_loading_more:
            return
        if self._total_artists > 0 and len(self._all_artists) >= self._total_artists:
            self._has_more = False
            self._display_artists()
            return

        self._is_loading_more = True
        self._page += 1
        offset = self._page * self._limit

        api.get_artists_by_letter(
            letter=self.current_letter, limit=self._limit, offset=offset,
            on_success=self._on_artists_next_page_loaded,
            on_failure=self._on_artists_page_failed
        )

    def _on_artists_next_page_loaded(self, data):
        self._is_loading_more = False
        if data is None: data = {"artists": [], "total": 0}
        if not isinstance(data, dict): data = {"artists": [], "total": 0}

        artists = data.get('artists', [])
        if not isinstance(artists, list) or not artists:
            self._has_more = False
            self._display_artists()
            return

        for artist in artists:
            name = artist.get('artist') if isinstance(artist, dict) else None
            count = artist.get('songs_count', 0) if isinstance(artist, dict) else 0
            if name:
                self._all_artists.append({'artist': name, 'songs_count': count})

        if len(self._all_artists) >= self._total_artists:
            self._has_more = False
            self._display_artists()
            return
        Clock.schedule_once(lambda dt: self._load_next_artists_pages(), 0.1)

    def _display_artists(self):
        self._hide_loading()
        if not self._all_artists:
            self._show_empty()
            self.recycle_view.clear()
            return
        self._hide_empty()
        self.recycle_view.viewclass = 'ArtistCard'
        self.recycle_view.set_items(self._all_artists, self.on_artist_selected)
        Clock.schedule_once(lambda dt: setattr(self.recycle_view, 'scroll_y', 1.0), 0.1)
        self._show_result_label(f"{get_text('artists')}: {len(self._all_artists)}")
        self._bind_scroll_for_load()

    def _on_artists_page_failed(self, req, error):
        self._is_loading_more = False
        self._hide_loading()
        logger.error(f"❌ Ошибка загрузки исполнителей: {error}")
        self._show_empty(get_text('loading_error'))

    # ============ ОТСЛЕЖИВАНИЕ СКРОЛЛА ============

    def _bind_scroll_for_load(self):
        if self.recycle_view:
            try:
                self.recycle_view.unbind(scroll_y=self._check_scroll_for_load)
            except:
                pass
            self.recycle_view.bind(scroll_y=self._check_scroll_for_load)

    def _check_scroll_for_load(self, instance, value):
        if value > 0.05: return
        if self._is_loading_more or self._is_restoring: return
        if self.current_letter and self._has_more and len(self._all_artists) < self._total_artists:
            self._load_remaining_artists()

    # ============ ОБРАБОТЧИКИ ============

    def on_letter_press(self, letter):
        self.is_search_mode = False
        self.current_artist = None
        self.search_bar.clear()
        if self.songs_menu:
            self.songs_menu.set_current_letter(letter)
        self._load_artists(letter)

    def on_artist_selected(self, artist, songs_count):
        if self.recycle_view:
            self._saved_scroll_position = self.recycle_view.scroll_y

        self.save_current_state()
        screen_state.set_previous_screen('songs')
        screen_state.set_artist_songs_data(artist, 1.0)

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artist_songs'):
                artist_songs_screen = self.manager.get_screen('artist_songs')
                artist_songs_screen.artist_name = artist
                artist_songs_screen._total_songs = 0
                artist_songs_screen._page = 0
                artist_songs_screen._artist_songs = []
                artist_songs_screen._has_more = True
                artist_songs_screen._is_loading_more = False
                artist_songs_screen._is_loading = False
                artist_songs_screen._update_top_nav_title(artist)
                artist_songs_screen._load_artist_songs(artist)
                self.manager.current = 'artist_songs'

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
        self._show_loading()
        self.recycle_view.clear()
        self.recycle_view.viewclass = 'SearchSongCard'

        api.search_songs(
            query=query, limit=50,
            on_success=self._on_search_success,
            on_failure=self._on_search_failed
        )

    def _on_search_success(self, results):
        if isinstance(results, dict):
            raw_results = results.get('results', [])
        elif isinstance(results, list):
            raw_results = results
        else:
            raw_results = []

        formatted_results = []
        for item in raw_results:
            if isinstance(item, dict):
                formatted_results.append({
                    'song_id': item.get('song_id', 0),
                    'artist': item.get('artist', ''),
                    'title': item.get('title', '')
                })

        self.search_results = formatted_results
        if not self.search_results:
            self.recycle_view.clear()
            self._hide_result_label()
            self._show_empty(get_text('nothing_found'))
        else:
            self.recycle_view.set_songs(self.search_results, self.on_song_selected)
            self._show_result_label(f"{get_text('songs_found')}: {len(self.search_results)}")
            self._show_hint(get_text('search_results'))

    def _on_search_failed(self, req, error):
        self.search_results = []
        self.recycle_view.clear()
        self._hide_result_label()
        self._show_empty(get_text('search_error'))
        logger.error(f"Ошибка поиска: {error}")

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.clear()
        self.recycle_view.clear()
        self._hide_result_label()
        self._hide_loading()
        self._hide_empty()
        self.current_letter = None
        self.current_artist = None
        if self.songs_menu:
            self.songs_menu.set_current_letter(None)
        self._show_hint(get_text('search_artists'))

    def on_item_selected(self, item_type, *args):
        pass

    def on_song_selected(self, song_id, title):
        if not song_id:
            notify.error(get_text('load_error'))
            return

        self.save_search_state()
        self.save_current_state()
        screen_state.set_previous_screen('songs')

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('search_detail'):
                search_detail_screen = self.manager.get_screen('search_detail')
                search_detail_screen.set_song(song_id)
                self.manager.current = 'search_detail'
            else:
                if self.manager.has_screen('song_detail'):
                    song_detail_screen = self.manager.get_screen('song_detail')
                    song_detail_screen.set_previous_screen('songs')
                    song_detail_screen.set_song(song_id)
                    self.manager.current = 'song_detail'

    def _load_remaining_artists(self):
        if not self.current_letter: return
        if self._is_loading_more: return
        if len(self._all_artists) >= self._total_artists:
            self._has_more = False
            return

        self._is_loading_more = True
        next_page = self._page + 1
        offset = next_page * self._limit

        if self.current_letter == '#':
            api.get_artists_by_digits(
                limit=self._limit, offset=offset,
                on_success=lambda data: self._append_artists(data, next_page),
                on_failure=self._on_artists_page_failed
            )
        else:
            api.get_artists_by_letter(
                letter=self.current_letter, limit=self._limit, offset=offset,
                on_success=lambda data: self._append_artists(data, next_page),
                on_failure=self._on_artists_page_failed
            )

    def _append_artists(self, data, page):
        self._is_loading_more = False
        if data is None: return
        if not isinstance(data, dict): return

        artists = data.get('artists', [])
        if not artists:
            self._has_more = False
            return

        for artist in artists:
            name = artist.get('artist') if isinstance(artist, dict) else None
            count = artist.get('songs_count', 0) if isinstance(artist, dict) else 0
            if name:
                self._all_artists.append({'artist': name, 'songs_count': count})

        self._page = page
        self._has_more = len(self._all_artists) < self._total_artists

        self.recycle_view.set_items(self._all_artists, self.on_artist_selected)
        self._show_result_label(f"{get_text('artists')}: {len(self._all_artists)} / {self._total_artists}")

        if not self._has_more:
            self._hide_loading()

    # ============ СОХРАНЕНИЕ СОСТОЯНИЯ ============

    def save_current_state(self):
        scroll_position = 1.0
        if self.recycle_view:
            scroll_position = self.recycle_view.scroll_y

        state = {
            'current_letter': self.current_letter,
            'current_language': self.current_language,
            'is_search_mode': self.is_search_mode,
            'all_artists': self._all_artists,
            'total_artists': self._total_artists,
            'page': self._page,
            'has_more': self._has_more,
            'scroll_position': scroll_position,
        }
        screen_state.save_screen_state('songs', state)

    def save_search_state(self):
        self._search_query = self.search_bar.current_query if self.search_bar else ""
        self._search_results = self.search_results
        self._is_search_mode = self.is_search_mode

    def restore_search_state(self):
        if self._is_search_mode and self._search_query:
            self.search_bar.set_text(self._search_query)
            self.is_search_mode = True
            self.current_letter = None
            self.current_artist = None
            if self.songs_menu:
                self.songs_menu.set_current_letter(None)
            self.recycle_view.viewclass = 'SearchSongCard'
            self.recycle_view.set_songs(self._search_results, self.on_song_selected)
            self._show_result_label(f"{get_text('songs_found')}: {len(self._search_results)}")
            self._show_hint(get_text('search_results'))

    def restore_state(self):
        if self.manager and self.manager.current != 'songs':
            return False

        state = screen_state.get_screen_state('songs', max_age=300)
        if not state:
            return False

        try:
            self._is_restoring = True
            self.current_letter = state.get('current_letter')
            self.is_search_mode = state.get('is_search_mode', False)
            self.current_language = state.get('current_language', 'ru')
            self._total_artists = state.get('total_artists', 0)
            self._page = state.get('page', 0)
            self._has_more = state.get('has_more', True)

            restored_artists = state.get('all_artists', [])
            scroll_position = state.get('scroll_position', 1.0)

            if self.songs_menu:
                self.songs_menu.set_language(self.current_language)

            if self.current_letter and self.songs_menu:
                self.songs_menu.set_current_letter(self.current_letter)

            if restored_artists:
                self._all_artists = restored_artists
                self.recycle_view.viewclass = 'ArtistCard'
                self.recycle_view.set_items(self._all_artists, self.on_artist_selected)
                self._show_result_label(f"{get_text('artists')}: {len(self._all_artists)} / {self._total_artists}")

                self._bind_scroll_for_load()

                def restore_scroll(dt):
                    if self.recycle_view:
                        self.recycle_view.scroll_y = scroll_position
                Clock.schedule_once(restore_scroll, 0.1)
                Clock.schedule_once(restore_scroll, 0.2)

                if self._has_more and len(self._all_artists) < self._total_artists:
                    Clock.schedule_once(lambda dt: self._load_remaining_artists(), 0.3)
            else:
                self.recycle_view.clear()
                self._show_hint(get_text('search_artists'))
                self._hide_result_label()

            self._is_restoring = False
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка восстановления: {e}")
            import traceback
            traceback.print_exc()
            self._is_restoring = False
            return False

    def on_pre_leave(self):
        self.save_search_state()
        if self.recycle_view:
            self._temp_scroll_position = self.recycle_view.scroll_y
        self.save_current_state()
        return super().on_pre_leave()

    def on_enter(self):
        self.restore_search_state()
        restored = self.restore_state()
        if not restored and not self._is_search_mode:
            self._show_hint(get_text('search_artists'))
            self._hide_result_label()
            self.recycle_view.clear()

    def on_leave(self):
        if self.recycle_view:
            self._temp_scroll_position = self.recycle_view.scroll_y
        self.save_current_state()
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'