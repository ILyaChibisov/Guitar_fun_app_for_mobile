# screens/songs_screen.py
"""
Экран песен с оптимизированной раскладкой.
"""
import time
import unicodedata
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from io import BytesIO
from kivy.uix.floatlayout import FloatLayout
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
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
from state.songs_state import songs_state
from utils.settings_manager import settings_manager
from utils.localization import get_text

from screens.components.loading_spinner import LoadingSpinner

from utils.perf import perf, perf_registry
from kivy.logger import Logger

_perf_log = Logger.getChild('Songs:Perf')

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

    @staticmethod
    def get_arrow_color(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 1]
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
    with perf('songs.load_shared_icons', log_every=False):
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

        self._built_language = None

        self.left_arrow = MDIconButton(
            icon="chevron-left", size_hint=(None, 1), width=dp(32),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll(-1), ripple_scale=0, ripple_alpha=0
        )
        self.right_arrow = MDIconButton(
            icon="chevron-right", size_hint=(None, 1), width=dp(32),
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

    def _populate_items(self, force=False):
        if (not force
                and self._built_language == self.current_language
                and self.buttons):
            return

        with perf('songs.alphabet.populate_items', log_every=False):
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
            self._built_language = self.current_language

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
        if self.current_language == language and self._built_language == language:
            return
        self.current_language = language
        self.current_selection = None
        self._populate_items(force=True)

    def set_current(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)

    def update_theme_colors(self):
        arrow_color = SongsColors.get_arrow_color(settings_manager.theme)
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
        self.height = dp(40)  # ✅ Уменьшили, так как контейнер теперь даёт отступ снизу
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


# ============ LONG PRESS MIXIN ============

class LongPressCardMixin:
    TAP_THRESHOLD = dp(15)
    LONG_PRESS_TIME = 0.5
    LONG_PRESS_MOVE_TOLERANCE = dp(10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._touch_down_pos = None
        self._long_press_event = None
        self._long_press_triggered = False

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        self._touch_down_pos = touch.pos
        self._long_press_triggered = False
        self._long_press_event = Clock.schedule_once(
            self._trigger_long_press, self.LONG_PRESS_TIME
        )
        return True

    def on_touch_move(self, touch):
        if self._touch_down_pos is None:
            return super().on_touch_move(touch)

        dx = touch.x - self._touch_down_pos[0]
        dy = touch.y - self._touch_down_pos[1]
        if (abs(dx) > self.LONG_PRESS_MOVE_TOLERANCE
                or abs(dy) > self.LONG_PRESS_MOVE_TOLERANCE):
            self._cancel_long_press()

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._touch_down_pos is None:
            return super().on_touch_up(touch)

        self._cancel_long_press()

        dx = touch.x - self._touch_down_pos[0]
        dy = touch.y - self._touch_down_pos[1]
        was_long = self._long_press_triggered
        self._touch_down_pos = None
        self._long_press_triggered = False

        if was_long:
            return True

        if abs(dx) < self.TAP_THRESHOLD and abs(dy) < self.TAP_THRESHOLD:
            self._handle_normal_click()

        return True

    def _trigger_long_press(self, dt):
        self._long_press_event = None
        if self._touch_down_pos is None:
            return
        self._long_press_triggered = True
        self._handle_long_press()

    def _cancel_long_press(self):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None

    def _flash_feedback(self):
        if not hasattr(self, 'md_bg_color'):
            return
        accent = SongsColors.get_accent(settings_manager.theme)
        bright = [min(1.0, c * 1.4 + 0.15) for c in accent[:3]] + [0.7]
        original = list(self.md_bg_color)

        anim = (
                Animation(md_bg_color=bright, duration=0.1, t='out_quad') +
                Animation(md_bg_color=original, duration=0.3, t='in_quad')
        )
        anim.start(self)

    def _handle_normal_click(self):
        pass

    def _handle_long_press(self):
        pass


# ============ КАРТОЧКИ ============

class StaticArtistCard(LongPressCardMixin, MDCard):
    CARD_HEIGHT = dp(48)

    def __init__(self, artist_name='', songs_count=0, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist_name = artist_name
        self.songs_count = songs_count
        self.on_click_callback = on_click

        self.size_hint_y = None
        self.height = self.CARD_HEIGHT

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

        self.update_theme_colors()

    def _handle_normal_click(self):
        if self.on_click_callback:
            self.on_click_callback(self.artist_name, self.songs_count)

    def _handle_long_press(self):
        self._flash_feedback()
        if self.on_click_callback:
            Clock.schedule_once(
                lambda dt: self.on_click_callback(
                    self.artist_name, self.songs_count
                ),
                0.15
            )

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


class StaticSearchSongCard(LongPressCardMixin, MDCard):
    CARD_HEIGHT = dp(48)

    def __init__(self, artist='', title='', song_id=0, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist = artist
        self.title = title
        self.song_id = song_id
        self.on_click_callback = on_click

        self.size_hint_y = None
        self.height = self.CARD_HEIGHT

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

        self.update_theme_colors()

    def _handle_normal_click(self):
        if self.on_click_callback:
            self.on_click_callback(self.song_id, self.title)

    def _handle_long_press(self):
        self._flash_feedback()
        if self.on_click_callback:
            Clock.schedule_once(
                lambda dt: self.on_click_callback(self.song_id, self.title),
                0.15
            )

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
    CARD_TYPE_ARTISTS = 'artists'
    CARD_TYPE_SONGS = 'songs'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(4)
        self.md_bg_color = [0, 0, 0, 0]
        self.cards = []
        self.padding = [0, 0, 0, 0]
        self._current_type = None

    def set_artists(self, artists, on_click):
        with perf('songs.cards.set_artists', log_every=False):
            if self._current_type != self.CARD_TYPE_ARTISTS:
                self.clear_widgets()
                self.cards = []
                self._current_type = self.CARD_TYPE_ARTISTS

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
            self.add_widget(Widget(size_hint_y=1))

    def set_songs(self, songs, on_click):
        with perf('songs.cards.set_songs', log_every=False):
            if self._current_type != self.CARD_TYPE_SONGS:
                self.clear_widgets()
                self.cards = []
                self._current_type = self.CARD_TYPE_SONGS

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
            self.add_widget(Widget(size_hint_y=1))

    def clear(self):
        self.clear_widgets()
        self.cards = []
        self._current_type = None

    def update_theme_colors(self):
        for c in self.cards:
            c.update_theme_colors()


# ============ ОБЁРТКА СО СВАЙПОМ ============

class SwipeableCardsWrapper(MDBoxLayout):
    SWIPE_THRESHOLD = dp(40)
    SWIPE_TIME_LIMIT = 0.5

    def __init__(self, on_swipe_up=None, on_swipe_down=None, **kwargs):
        super().__init__(**kwargs)
        self.on_swipe_up = on_swipe_up
        self.on_swipe_down = on_swipe_down
        self._touch_start = None
        self._touch_start_time = None
        self._swipe_handled = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start = touch.pos
            self._touch_start_time = time.perf_counter()
            self._swipe_handled = False
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._touch_start is None:
            return super().on_touch_up(touch)

        if self._swipe_handled:
            self._touch_start = None
            return super().on_touch_up(touch)

        dx = touch.x - self._touch_start[0]
        dy = touch.y - self._touch_start[1]
        dt = time.perf_counter() - self._touch_start_time

        if (abs(dy) > self.SWIPE_THRESHOLD
                and abs(dy) > abs(dx) * 1.2
                and dt < self.SWIPE_TIME_LIMIT):
            self._swipe_handled = True
            if dy > 0:
                if self.on_swipe_down:
                    self.on_swipe_down()
            else:
                if self.on_swipe_up:
                    self.on_swipe_up()

        self._touch_start = None
        return super().on_touch_up(touch)


# ============ ПАГИНАЦИЯ ============

class PaginationArrow(MDBoxLayout):
    DEFAULT_WIDTH = dp(40)

    def __init__(self, icon_name, on_press=None,
                 icon_color=None, width=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = width if width else self.DEFAULT_WIDTH
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]

        self._on_press = on_press
        self._enabled = True
        self._pressed = False

        container = AnchorLayout(anchor_x='center', anchor_y='center',
                                 size_hint=(1, 1))
        self.icon_widget = MDIcon(
            icon=icon_name, font_size=sp(22),
            theme_text_color="Custom",
            text_color=icon_color if icon_color else [1, 1, 1, 1],
            size_hint=(None, None), size=(dp(24), dp(24)),
        )
        container.add_widget(self.icon_widget)
        self.add_widget(container)

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.opacity = 1.0 if enabled else 0.3

    def set_color(self, color):
        self.icon_widget.text_color = color

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if not self._enabled:
            return True
        self._pressed = True
        touch.grab(self)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        if self._pressed:
            self._pressed = False
            if self._enabled and self.collide_point(*touch.pos) and self._on_press:
                self._on_press()
        return True


class PaginationBar(MDBoxLayout):
    def __init__(self, on_page_select=None, **kwargs):
        super().__init__(**kwargs)
        self.on_page_select = on_page_select
        self.current_page_index = 0
        self.total_pages = 1
        self._last_total = None
        self._last_per_page = None
        self._rebuild_count = 0
        self._total_rebuilds = 0

        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.height = dp(48)
        self.padding = [dp(4), 0, dp(4), 0]
        self.spacing = dp(4)  # немного увеличим для красоты, так как стрелок стало меньше
        self.md_bg_color = [0, 0, 0, 0]

        # ❌ Убрали first_arrow

        self.jump_back_arrow = PaginationArrow(
            icon_name="chevron-double-left",
            on_press=self._go_back_10,
            width=dp(36),
        )
        self.add_widget(self.jump_back_arrow)

        self.prev_arrow = PaginationArrow(
            icon_name="chevron-left",
            on_press=self._go_prev_page,
            width=dp(36),
        )
        self.add_widget(self.prev_arrow)

        self.page_label = MDLabel(
            text="1",
            font_size=sp(16),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            size_hint=(None, 1),
            width=dp(40),
        )
        self.add_widget(self.page_label)

        self.next_arrow = PaginationArrow(
            icon_name="chevron-right",
            on_press=self._go_next_page,
            width=dp(36),
        )
        self.add_widget(self.next_arrow)

        self.jump_forward_arrow = PaginationArrow(
            icon_name="chevron-double-right",
            on_press=self._go_forward_10,
            width=dp(36),
        )
        self.add_widget(self.jump_forward_arrow)

        # ❌ Убрали last_arrow

        self._update_width()
        self.update_theme_colors()

    def on_touch_down(self, touch):
        if self.parent is not None and self.parent.height < dp(10):
            return False
        return super().on_touch_down(touch)

    def _update_width(self):
        w = (
                dp(4) + dp(4)
                + self.jump_back_arrow.width + self.spacing
                + self.prev_arrow.width + self.spacing
                + self.page_label.width + self.spacing
                + self.next_arrow.width + self.spacing
                + self.jump_forward_arrow.width
        )
        self.width = w

    def set_total(self, total_items, per_page, current_page=0, on_click=None):
        with perf('songs.pagination.set_total', log_every=False):
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
            self._apply_page()
            self.update_theme_colors()

    def set_current_page(self, page):
        with perf('songs.pagination.set_current_page', log_every=False):
            self.current_page_index = max(0, min(page, self.total_pages - 1))
            self._apply_page()

    def _apply_page(self):
        self.page_label.text = str(self.current_page_index + 1)
        digits = len(str(self.total_pages))
        self.page_label.width = dp(12) * max(2, digits) + dp(4)

        at_first = self.current_page_index == 0
        at_last = self.current_page_index >= self.total_pages - 1

        # ❌ Убрали first_arrow и last_arrow
        self.jump_back_arrow.set_enabled(not at_first)
        self.prev_arrow.set_enabled(not at_first)
        self.next_arrow.set_enabled(not at_last)
        self.jump_forward_arrow.set_enabled(not at_last)

        self._update_width()
        self._rebuild_count += 1
        self._total_rebuilds += 1

    def _go_first_page(self):
        if self.current_page_index == 0:
            return
        with perf('songs.pagination.go_first', log_every=False):
            self.current_page_index = 0
            self._apply_page()
            if self.on_page_select:
                self.on_page_select(0)
        _perf_log.info("📄 page_click index=0 (first)")

    def _go_back_10(self):
        if self.current_page_index <= 0:
            return
        with perf('songs.pagination.go_back_10', log_every=False):
            new_index = max(0, self.current_page_index - 10)
            self.current_page_index = new_index
            self._apply_page()
            if self.on_page_select:
                self.on_page_select(new_index)
        _perf_log.info(f"📄 page_click index={new_index} (back 10)")

    def _go_prev_page(self):
        if self.current_page_index <= 0:
            return
        with perf('songs.pagination.go_prev_page', log_every=False):
            new_index = self.current_page_index - 1
            self.current_page_index = new_index
            self._apply_page()
            if self.on_page_select:
                self.on_page_select(new_index)
        _perf_log.info(f"📄 page_click index={new_index} (prev)")

    def _go_next_page(self):
        if self.current_page_index >= self.total_pages - 1:
            return
        with perf('songs.pagination.go_next_page', log_every=False):
            new_index = self.current_page_index + 1
            self.current_page_index = new_index
            self._apply_page()
            if self.on_page_select:
                self.on_page_select(new_index)
        _perf_log.info(f"📄 page_click index={new_index} (next)")

    def _go_forward_10(self):
        if self.current_page_index >= self.total_pages - 1:
            return
        with perf('songs.pagination.go_forward_10', log_every=False):
            new_index = min(self.total_pages - 1, self.current_page_index + 10)
            self.current_page_index = new_index
            self._apply_page()
            if self.on_page_select:
                self.on_page_select(new_index)
        _perf_log.info(f"📄 page_click index={new_index} (forward 10)")

    def _go_last_page(self):
        last = self.total_pages - 1
        if self.current_page_index >= last:
            return
        with perf('songs.pagination.go_last', log_every=False):
            self.current_page_index = last
            self._apply_page()
            if self.on_page_select:
                self.on_page_select(last)
        _perf_log.info(f"📄 page_click index={last} (last)")

    def update_theme_colors(self):
        with perf('songs.pagination.update_theme', log_every=False):
            theme_id = settings_manager.theme
            arrow_color = SongsColors.get_arrow_color(theme_id)

            # ❌ Убрали first_arrow и last_arrow
            self.jump_back_arrow.set_color(arrow_color)
            self.jump_forward_arrow.set_color(arrow_color)
            self.prev_arrow.set_color(arrow_color)
            self.next_arrow.set_color(arrow_color)
            self.page_label.text_color = SongsColors.get_text_primary(theme_id)


# ============ ОСНОВНОЙ ЭКРАН ============

class SongsScreen(BaseScreen):
    MIN_PAGE_SIZE = 3
    MAX_PAGE_SIZE = 12
    PAGINATION_HEIGHT = dp(48) + dp(1) + dp(2)

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
        self._page_size = 6
        self._page_size_locked = False
        self._last_window_size = None
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
        self._result_label = None
        self.songs_menu = None
        self._hint_timer = None
        self.cards_container = None
        self._cards_wrapper = None
        self._pagination_bar = None
        self._search_pagination_bar = None
        self._pagination_container = None
        self._search_pagination_container = None
        self._pagination_anchor = None
        self._search_pagination_anchor = None
        self._loading_spinner = None
        self._loading_spinner_widget = None

        with perf('songs.init.load_shared_icons', log_every=False):
            load_shared_icons_sync()
        with perf('songs.init.init_ui', log_every=False):
            self.init_ui()
        with perf('songs.init.load_background', log_every=False):
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
        with perf('songs.update_theme_colors', log_every=False):
            self.update_screen_background()
            if self.search_bar:
                self.search_bar.update_theme_colors()
            if self.songs_menu:
                self.songs_menu.update_theme_colors()
            if self._pagination_bar:
                self._pagination_bar.update_theme_colors()
            if self._search_pagination_bar:
                self._search_pagination_bar.update_theme_colors()
            if self._result_label:
                self._result_label.text_color = SongsColors.get_hint_color(settings_manager.theme)
            if self.cards_container:
                self.cards_container.update_theme_colors()

    def update_language(self):
        with perf('songs.update_language', log_every=False):
            if self.search_bar:
                self.search_bar.update_language()
            if self.songs_menu:
                self.songs_menu.set_language(settings_manager.language)
            if self._result_label and self._result_label.opacity > 0:
                if self.is_search_mode:
                    self._update_search_result_label()
                elif self.current_letter and self._all_artists:
                    self._update_result_label_for_artists()

    def init_ui(self):
        with perf('songs.init_ui.build', log_every=False):
            main_layout = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))

            top_padding = layout_config.get_top_padding()
            main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

            padding = layout_config.get_content_padding()

            # === АЛФЕВИТ ===
            menu_container = MDBoxLayout(
                orientation='vertical', size_hint=(1, None), height=dp(48),  # Общая высота контейнера
                md_bg_color=[0, 0, 0, 0],
                padding=[padding[0], 0, padding[2], dp(8)]  # ✅ Отступ СНИЗУ 8dp
            )
            self.songs_menu = SongsMenu(
                on_language_toggle=self._toggle_language,
                on_letter_press=self.on_letter_press,
                current_language=self.current_language
            )
            self.songs_menu.height = dp(40)  # ✅ Высота самих букв 40dp
            menu_container.add_widget(self.songs_menu)
            main_layout.add_widget(menu_container)

            # === ПОИСК ===
            search_container = MDBoxLayout(
                orientation='vertical', size_hint=(1, None), height=dp(48),
                padding=[padding[0], 0, padding[2], 0]  # Без лишних отступов
            )
            self.search_bar = SearchBar(on_search=self.do_search, on_clear=self.clear_search)
            search_container.add_widget(self.search_bar)
            main_layout.add_widget(search_container)

            # ✅ Отступ между поиском и результатами (оставляем 4dp)
            main_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

            # === RESULT LABEL (объединённый) ===
            self._result_label = MDLabel(
                text="", font_size=sp(12), halign="center",
                size_hint_y=None, height=dp(22),
                theme_text_color="Custom",
                text_color=SongsColors.get_hint_color(settings_manager.theme),
                opacity=0, bold=True
            )
            main_layout.add_widget(self._result_label)

            # === КАРТОЧКИ ===
            self._cards_wrapper = SwipeableCardsWrapper(
                on_swipe_up=self._on_swipe_up,
                on_swipe_down=self._on_swipe_down,
                orientation='vertical',
                size_hint=(1, 1),
                spacing=0,
                padding=[padding[0], dp(4), padding[2], dp(4)],
                md_bg_color=[0, 0, 0, 0]
            )
            self._cards_wrapper.clip = True
            self.cards_container = PageCardsContainer()
            self._cards_wrapper.add_widget(self.cards_container)
            main_layout.add_widget(self._cards_wrapper)

            # === ПАГИНАЦИЯ АРТИСТОВ ===
            self._pagination_container = MDBoxLayout(
                orientation='vertical',
                size_hint=(1, None),
                height=0,
                md_bg_color=[0, 0, 0, 0],
                padding=[padding[0], dp(0), padding[2], dp(0)],
            )
            self._pagination_container.clip = True

            self._pagination_anchor = FloatLayout(size_hint=(1, 1))

            self._pagination_bar = PaginationBar(
                on_page_select=self._on_page_selected_from_bar,
            )
            self._pagination_bar.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            self._pagination_anchor.add_widget(self._pagination_bar)
            self._pagination_container.add_widget(self._pagination_anchor)
            main_layout.add_widget(self._pagination_container)

            # === ПАГИНАЦИЯ ПОИСКА ===
            self._search_pagination_container = MDBoxLayout(
                orientation='vertical',
                size_hint=(1, None),
                height=0,
                md_bg_color=[0, 0, 0, 0],
                padding=[padding[0], dp(0), padding[2], dp(0)],
            )
            self._search_pagination_container.clip = True

            self._search_pagination_anchor = FloatLayout(size_hint=(1, 1))

            self._search_pagination_bar = PaginationBar(
                on_page_select=self._on_search_page_selected,
            )
            self._search_pagination_bar.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            self._search_pagination_anchor.add_widget(self._search_pagination_bar)
            self._search_pagination_container.add_widget(self._search_pagination_anchor)
            main_layout.add_widget(self._search_pagination_container)

            # ✅ Немного уменьшаем отступ снизу, чтобы пагинация прижалась к меню
            bottom_padding = max(layout_config.get_bottom_padding() - dp(10), dp(4))
            main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))

            self.clear_widgets()
            self.add_widget(main_layout)
            self.update_theme_colors()

            Clock.schedule_once(lambda dt: self._recalc_page_size(force=True), 0.3)

    def _toggle_language(self):
        pass

    # ---------- СВАЙП ----------

    def _on_swipe_up(self):
        """
        Свайп ВВЕРХ (палец движется вверх) -> Следующая страница (в конец).
        """
        if self.is_search_mode:
            if not self._all_search_results:
                return
            total_pages = (len(self._all_search_results) + self._page_size - 1) // self._page_size
            if self._search_page < total_pages - 1:
                self._show_search_page(self._search_page + 1)
        else:
            if self._total_artists <= 0:
                return
            max_page = (self._total_artists - 1) // self._page_size
            if self._page < max_page:
                self._load_page(self._page + 1)

    def _on_swipe_down(self):
        """
        Свайп ВНИЗ (палец движется вниз) -> Предыдущая страница (в начало).
        """
        if self.is_search_mode:
            if not self._all_search_results:
                return
            if self._search_page > 0:
                self._show_search_page(self._search_page - 1)
        else:
            if self._total_artists <= 0:
                return
            if self._page > 0:
                self._load_page(self._page - 1)

    # ---------- РАЗМЕР СТРАНИЦЫ ----------

    def _calc_page_size(self):
        fixed_h = (
                layout_config.get_top_padding()
                + dp(48)  # алфавит (было 44, стало 48)
                + dp(48)  # поиск
                + dp(4)  # отступ поиск → результаты
                + dp(22)  # result label
                + dp(8)  # padding карточек сверху/снизу
                + self.PAGINATION_HEIGHT  # пагинация
                + max(layout_config.get_bottom_padding() - dp(10), dp(4))
        )
        available_h = Window.height - fixed_h
        if available_h <= 0:
            return self.MIN_PAGE_SIZE

        card_h = StaticArtistCard.CARD_HEIGHT + self.cards_container.spacing
        if card_h <= 0:
            card_h = dp(52)

        n = int(available_h / card_h)
        return max(self.MIN_PAGE_SIZE, min(self.MAX_PAGE_SIZE, n))

    def _recalc_page_size(self, force=False):
        with perf('songs._recalc_page_size', log_every=False):
            if self._page_size_locked and not force:
                return
            new_size = self._calc_page_size()
            if new_size == self._page_size:
                if not self._page_size_locked:
                    self._page_size_locked = True
                    logger.info(f"📐 PAGE_SIZE зафиксирован: {new_size}")
                return
            self._page_size = new_size
            self._page_size_locked = True
            logger.info(f"📐 PAGE_SIZE определён: {new_size}")
            if self.current_letter:
                self._ensure_valid_page()
                self._display_current_page()

    def on_size(self, *args):
        current_size = (Window.width, Window.height)
        if self._last_window_size is not None:
            old_w, old_h = self._last_window_size
            if (abs(old_w - current_size[0]) < dp(50)
                    and abs(old_h - current_size[1]) < dp(50)):
                return
        self._last_window_size = current_size

        if self._page_size_locked:
            Clock.schedule_once(lambda dt: self._recalc_on_rotation(), 0.3)

    def _recalc_on_rotation(self):
        new_size = self._calc_page_size()
        if new_size != self._page_size:
            self._page_size = new_size
            logger.info(f"📐 PAGE_SIZE пересчитан (real resize): {new_size}")
            if self.current_letter:
                self._ensure_valid_page()
                self._display_current_page()

    def _ensure_valid_page(self):
        if self._total_artists <= 0:
            self._page = 0
            return
        max_page = (self._total_artists - 1) // self._page_size
        if self._page > max_page:
            self._page = max_page

    # ---------- АНИМИРОВАННЫЙ ЗАГРУЗЧИК (MDSPINNER) ----------

    def _show_loading_spinner(self):
        if self._loading_spinner:
            return

        overlay = FloatLayout(size_hint=(1, 1))

        spinner = LoadingSpinner(text=get_text('loading', 'Загрузка'))
        spinner.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        overlay_color = spinner.get_overlay_color()
        with overlay.canvas.before:
            Color(*overlay_color)
            rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(
            pos=lambda inst, val: setattr(rect, 'pos', val),
            size=lambda inst, val: setattr(rect, 'size', val),
        )

        overlay.add_widget(spinner)
        spinner.start_animation()

        self._loading_spinner = overlay
        self._loading_spinner_widget = spinner
        self.add_widget(overlay)

    def _hide_loading_spinner(self):
        if not self._loading_spinner:
            return
        if self._loading_spinner_widget:
            self._loading_spinner_widget.stop_animation()
            self._loading_spinner_widget = None
        if self._loading_spinner.parent:
            self._loading_spinner.parent.remove_widget(self._loading_spinner)
        self._loading_spinner = None

    # ---------- ПОИСК ----------

    def _show_search_page(self, page_idx):
        with perf('songs._show_search_page', log_every=False):
            if not self._all_search_results:
                self._hide_search_pagination()
                return
            self._search_page = page_idx
            start = page_idx * self._page_size
            end = min(start + self._page_size, len(self._all_search_results))
            page_slice = self._all_search_results[start:end][:self._page_size]

            total_pages = (len(self._all_search_results) + self._page_size - 1) // self._page_size
            if total_pages > 1:
                self._search_pagination_container.height = self.PAGINATION_HEIGHT
                self._search_pagination_container.opacity = 1
                self._search_pagination_container.disabled = False
                self._search_pagination_bar.set_total(
                    len(self._all_search_results), self._page_size, self._search_page,
                    on_click=self._on_search_page_selected
                )
            else:
                self._hide_search_pagination()

            first_song = page_slice[0]['song_id'] if page_slice else 0
            display_key = (
                self._search_page,
                len(page_slice),
                first_song,
                self._page_size,
            )
            if self._last_search_display_key != display_key:
                self.cards_container.set_songs(page_slice, self.on_song_selected)
                self._last_search_display_key = display_key

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
            f"{get_text('songs_found')}: {end} "
            f"{get_text('of')} {len(self._all_search_results)}"
        )

    def _hide_search_pagination(self):
        if not self._search_pagination_container:
            return
        self._search_pagination_container.height = 0
        self._search_pagination_container.opacity = 0
        self._search_pagination_container.disabled = True

    def _on_search_page_selected(self, page_index):
        if page_index == self._search_page:
            return
        with perf('songs.action.search_page_switch.total'):
            self._show_search_page(page_index)

    # ---------- ПАГИНАЦИЯ АРТИСТОВ ----------

    def _hide_pagination(self):
        if not self._pagination_container:
            return
        self._pagination_container.height = 0
        self._pagination_container.opacity = 0
        self._pagination_container.disabled = True

    def _show_pagination_bar(self):
        with perf('songs._show_pagination_bar', log_every=False):
            if not self._pagination_bar:
                return
            if self._total_artists <= self._page_size:
                self._hide_pagination()
                return
            self._pagination_container.height = self.PAGINATION_HEIGHT
            self._pagination_container.opacity = 1
            self._pagination_container.disabled = False
            self._pagination_bar.set_total(
                self._total_artists, self._page_size, self._page
            )

    def _on_page_selected_from_bar(self, page_index):
        if page_index == self._page:
            return
        with perf('songs.action.page_switch.total'):
            self._load_page(page_index)

    # ---------- КЭШ И ЗАГРУЗКА АРТИСТОВ ----------

    def _is_page_cached(self, cache, page):
        with perf('songs._is_page_cached', log_every=False):
            start = page * self._page_size
            total = cache['total']
            end = min(start + self._page_size, total) if total else start + self._page_size
            for idx in range(start, end):
                if idx not in cache['items']:
                    return False
            return True

    def _build_page_slice(self, cache, page):
        with perf('songs._build_page_slice', log_every=False):
            start = page * self._page_size
            end = start + self._page_size
            total = cache['total']
            if total:
                end = min(end, total)
            return [cache['items'][i] for i in range(start, end) if i in cache['items']]

    def _load_page(self, page):
        with perf('songs._load_page', log_every=False):
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
        self._show_loading_spinner()

        t_net = time.perf_counter()

        def _on_success(data):
            if my_token != self._load_token:
                return

            if isinstance(data, dict) and data.get('error'):
                self._batch_loading = False
                self._hide_loading_spinner()
                cache['failed'] = True
                logger.warning(f"⚠️ Сетевая ошибка для '{letter}': {data.get('error')}")

                self.cards_container.clear()
                self._show_result_label("Нет ответа от сервера. Проверьте интернет.", is_error=True)
                return

            dt_net = (time.perf_counter() - t_net) * 1000.0
            _perf_log.info(
                f"🌐 GET artists '{letter}' offset={batch_offset} OK {dt_net:.1f} ms"
            )
            perf_registry.add('songs.net.artists', dt_net)
            try:
                with perf('songs._load_batch.process', log_every=False):
                    self._batch_loading = False
                    cache['failed'] = False
                    if not isinstance(data, dict):
                        data = {"artists": [], "total": 0}
                    artists = data.get('artists', []) or []
                    total = data.get('total', 0) or 0

                    if total == 0 and len(artists) == 0:
                        self._hide_loading_spinner()
                        self.cards_container.clear()
                        self._show_result_label("Исполнителей не найдено")
                        self._hide_pagination()
                        return

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
                            self._hide_loading_spinner()
                            self._all_artists = self._build_page_slice(cache, self._page)
                            self._display_current_page()
                            return
                        batch_offset2 = (self._page * self._page_size) // self._batch_size * self._batch_size
                        self._load_batch(letter=letter, batch_offset=batch_offset2, target_page=self._page)
                        return
                    self._hide_loading_spinner()
                    self._all_artists = self._build_page_slice(cache, self._page)
                    self._display_current_page()
            except Exception as e:
                self._batch_loading = False
                self._pending_page = None
                self._hide_loading_spinner()
                logger.error(f"❌ Ошибка _on_success: {e}")
                self._show_result_label("Ошибка загрузки", is_error=True)

        def _on_error(req, err):
            if my_token != self._load_token:
                return
            dt_net = (time.perf_counter() - t_net) * 1000.0
            _perf_log.warning(
                f"🌐 GET artists '{letter}' FAIL {dt_net:.1f} ms err={err}"
            )
            self._batch_loading = False
            self._pending_page = None
            self._hide_loading_spinner()
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
        self._show_result_label(
            "Нет ответа. Нажмите букву ещё раз",
            is_error=True
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
        with perf('songs._load_artists', log_every=False):
            self.current_artist = None
            self.current_letter = letter
            self._hide_result_label()
            self._page = 0
            self._batch_loading = False
            self._pending_page = None

            cache = self._artists_cache.get(letter)
            if (cache is not None
                    and not cache.get('failed')
                    and (cache.get('total', 0) > 0 or cache.get('batches'))):
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
        with perf('songs.action.on_song_selected', log_every=False):
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
        with perf('songs.action.on_letter_press', log_every=False):
            if self.songs_menu:
                self.songs_menu.set_current_letter(letter)

            self.is_search_mode = False
            self.current_artist = None
            self.search_bar.clear()

            self.cards_container.clear()
            self._hide_pagination()
            self._hide_result_label()

            Clock.schedule_once(lambda dt: self._load_artists(letter), 0.05)

    def on_artist_selected(self, artist, songs_count):
        with perf('songs.action.on_artist_selected', log_every=False):
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
        with perf('songs.action.do_search', log_every=False):
            query = query.strip()
            if len(query) < 2:
                self._show_temporary_hint(get_text('min_chars'), 1.5)
                return
            self.is_search_mode = True
            self.current_letter = None
            self.current_artist = None
            if self.songs_menu:
                self.songs_menu.set_current_letter(None)

            self._hide_pagination()
            self._hide_search_pagination()
            self._hide_result_label()
            self.cards_container.clear()

            self._search_token = str(time.time())
            token = self._search_token
            self._search_in_progress = True
            self._last_search_display_key = None
            songs_state.save_search({'query': query, 'search_page': 0})

            self._show_loading_spinner()

            t_net = time.perf_counter()

            def _on_success(res):
                dt_net = (time.perf_counter() - t_net) * 1000.0
                n = len(res.get('results', []) if isinstance(res, dict) else res) if res else 0
                _perf_log.info(f"🌐 GET search '{query}' OK {dt_net:.1f} ms  results={n}")
                perf_registry.add('songs.net.search', dt_net)
                Clock.schedule_once(
                    lambda dt: self._on_search_success(res, token), 0
                )

            def _on_failure(req, err):
                dt_net = (time.perf_counter() - t_net) * 1000.0
                _perf_log.warning(f"🌐 GET search '{query}' FAIL {dt_net:.1f} ms err={err}")
                Clock.schedule_once(
                    lambda dt: self._on_search_failed(req, err, token), 0
                )

            api.search_songs(
                query=query, limit=100,
                on_success=_on_success,
                on_failure=_on_failure
            )

    def _on_search_success(self, results, token):
        with perf('songs._on_search_success', log_every=False):
            if token != self._search_token:
                return
            self._search_in_progress = False
            self._hide_loading_spinner()

            if isinstance(results, dict) and results.get('error'):
                self._all_search_results = []
                self.cards_container.clear()
                self._hide_search_pagination()
                self._show_result_label("Нет ответа от сервера. Проверьте интернет.", is_error=True)
                return

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
                self._show_result_label(get_text('nothing_found', 'Ничего не найдено'))
                self._hide_search_pagination()
            else:
                self._show_search_page(0)

    def _on_search_failed(self, req, error, token):
        if token != self._search_token:
            return
        self._search_in_progress = False
        self._hide_loading_spinner()
        self._all_search_results = []
        self._search_results = []
        self.cards_container.clear()
        self._hide_result_label()
        self._hide_search_pagination()
        self._show_result_label("Нет ответа от сервера. Проверьте интернет.", is_error=True)
        logger.error(f"Ошибка поиска: {error}")

    def clear_search(self):
        with perf('songs.action.clear_search', log_every=False):
            self.is_search_mode = False
            self.search_results = []
            self._all_search_results = []
            self._search_in_progress = False
            self._search_token = str(time.time())
            self._last_search_display_key = None
            songs_state.invalidate_search()
            self._hide_result_label()
            self._hide_loading_spinner()
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
        with perf('songs._display_current_page', log_every=False):
            self._hide_loading_spinner()
            self._hide_search_pagination()
            if not self._all_artists:
                self._show_empty()
                self.cards_container.clear()
                self._hide_pagination()
                return
            self._hide_empty()

            if self._total_artists > self._page_size:
                self._show_pagination_bar()
            else:
                self._hide_pagination()

            artists_to_show = self._all_artists[:self._page_size]

            first_artist = artists_to_show[0].get('artist', '') if artists_to_show else ''
            display_key = (
                self.current_letter,
                self._page,
                len(artists_to_show),
                first_artist,
                self._page_size,
            )
            if self._last_display_key != display_key:
                self.cards_container.set_artists(artists_to_show, self.on_artist_selected)
                self._last_display_key = display_key

            current_count = min((self._page + 1) * self._page_size, self._total_artists)
            self._show_result_label(
                f"{get_text('artists')}: {current_count} "
                f"{get_text('of')} {self._total_artists}"
            )
            self.save_current_state()

    def _show_temporary_hint(self, text, duration=1.5):
        self._show_result_label(text)
        if self._hint_timer:
            Clock.unschedule(self._hint_timer)
        self._hint_timer = Clock.schedule_once(lambda dt: self._restore_hint(), duration)

    def _restore_hint(self):
        self._hint_timer = None
        if self._all_artists:
            self._update_result_label_for_artists()
        elif self._all_search_results:
            self._update_search_result_label()
        elif self._result_label:
            self._hide_result_label()

    def _show_result_label(self, text, is_error=False):
        if self._result_label:
            self._result_label.text = text
            self._result_label.opacity = 1
            if is_error:
                self._result_label.text_color = [0.8, 0.3, 0.3, 1]  # Красный для ошибок
            else:
                self._result_label.text_color = SongsColors.get_hint_color(settings_manager.theme)

    def _hide_result_label(self):
        if self._result_label:
            self._result_label.text = ""
            self._result_label.opacity = 0

    def _show_empty(self, text=None):
        self._show_result_label(text or get_text('no_artists'))

    def _hide_empty(self):
        self._hide_result_label()

    def _show_loading(self, text=None):
        self._show_result_label(text or get_text('loading', 'Загрузка'))
        self._show_loading_spinner()

    def _hide_loading(self):
        self._hide_loading_spinner()

    # ---------- СОХРАНЕНИЕ / ВОССТАНОВЛЕНИЕ ----------

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
        with perf('songs.restore_search_state', log_every=False):
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
                self._show_loading_spinner()
                token = str(time.time())
                self._search_token = token

                t_net = time.perf_counter()

                def _on_success(res):
                    dt_net = (time.perf_counter() - t_net) * 1000.0
                    _perf_log.info(f"🌐 GET search (restore) '{query}' OK {dt_net:.1f} ms")
                    perf_registry.add('songs.net.search_restore', dt_net)
                    self._on_search_success(res, token)

                def _on_failure(req, err):
                    dt_net = (time.perf_counter() - t_net) * 1000.0
                    _perf_log.warning(f"🌐 GET search (restore) FAIL {dt_net:.1f} ms err={err}")
                    self._on_search_failed(req, err, token)

                api.search_songs(
                    query=query, limit=100,
                    on_success=_on_success,
                    on_failure=_on_failure
                )

    def restore_state(self):
        with perf('songs.restore_state', log_every=False):
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
        with perf('songs.on_pre_leave', log_every=False):
            self.save_search_state()
            self.save_current_state()
        return super().on_pre_leave()

    def on_enter(self):
        with perf('songs.on_enter.total'):
            super().on_enter()

            if self._last_display_key is not None and not self.is_search_mode:
                self._update_result_label_for_artists()
                return

            with perf('songs.on_enter.restore_search', log_every=False):
                self.restore_search_state()
            with perf('songs.on_enter.restore_state', log_every=False):
                restored = self.restore_state()
            if not restored and not self.is_search_mode:
                self._restore_hint()
                self._hide_result_label()
                self.cards_container.clear()
                self._hide_pagination()
                self._hide_search_pagination()

            if self.is_search_mode and self._all_search_results:
                self._last_search_display_key = None
                self._show_search_page(self._search_page)

    def on_leave(self):
        try:
            total_rebuilds = 0
            if self._pagination_bar:
                total_rebuilds += self._pagination_bar._total_rebuilds
            if self._search_pagination_bar:
                total_rebuilds += self._search_pagination_bar._total_rebuilds
            _perf_log.info(f"📊 total_pagination_rebuilds={total_rebuilds}")
        except Exception:
            pass

        perf_registry.dump(prefix=f'[{self.name}]')
        self.save_current_state()
        if self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        if self.manager:
            self.manager.current = 'home'