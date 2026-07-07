# screens/songs_screen.py
"""
Экран песен - с единым меню (БУКВЫ | ЯЗЫК) и поиском
Результаты поиска, исполнители по букве и песни исполнителя показываются на одном экране
С сохранением состояния и позиции скролла
"""
import time
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
from kivy.uix.scrollview import ScrollView

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state

logger = screen_logger('Songs')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# ============ ГЛОБАЛЬНЫЕ ИКОНКИ - ЗАГРУЖАЕМ СРАЗУ ============
_shared_rus_flag_texture = None
_shared_eng_flag_texture = None
_shared_song_icon_texture = None
_shared_artist_icon_texture = None


def load_shared_icons_sync():
    """Синхронная загрузка иконок - вызывается ДО создания UI"""
    global _shared_rus_flag_texture, _shared_eng_flag_texture
    global _shared_song_icon_texture, _shared_artist_icon_texture

    if _shared_rus_flag_texture is not None:
        return

    if HAS_ASSETS:
        try:
            # Загружаем русский флаг
            rus_data = load_asset_as_bytes('rus_png')
            if rus_data:
                img = CoreImage(BytesIO(rus_data), ext="png")
                _shared_rus_flag_texture = img.texture
                logger.info("✅ Русский флаг загружен синхронно")
            else:
                logger.warning("⚠️ Русский флаг не найден в ассетах")

            # Загружаем английский флаг
            eng_data = load_asset_as_bytes('eng_png')
            if eng_data:
                img = CoreImage(BytesIO(eng_data), ext="png")
                _shared_eng_flag_texture = img.texture
                logger.info("✅ Английский флаг загружен синхронно")
            else:
                logger.warning("⚠️ Английский флаг не найден в ассетах")

            # Загружаем иконку песни
            song_data = load_asset_as_bytes('song_png')
            if song_data:
                img = CoreImage(BytesIO(song_data), ext="png")
                _shared_song_icon_texture = img.texture
                logger.info("✅ Иконка песни загружена синхронно")
            else:
                logger.warning("⚠️ Иконка песни не найдена в ассетах")

            # Загружаем иконку исполнителя
            artist_data = load_asset_as_bytes('artist_png')
            if artist_data:
                img = CoreImage(BytesIO(artist_data), ext="png")
                _shared_artist_icon_texture = img.texture
                logger.info("✅ Иконка исполнителя загружена синхронно")
            else:
                logger.warning("⚠️ Иконка исполнителя не найдена в ассетах")

        except Exception as e:
            logger.error(f"Ошибка загрузки иконок: {e}")


# ============ СОВРЕМЕННАЯ ПОИСКОВАЯ СТРОКА ============

class SearchBar(MDCard):
    """Поисковая строка в стиле Google с красивой обводкой"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self._search_timer = None

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [1, 1, 1, 1]
        self.elevation = 0
        self.padding = [dp(12), dp(4), dp(8), dp(4)]
        self.spacing = dp(4)

        self.line_color = [0.1, 0.1, 0.1, 0.3]
        self.line_width = 1.6

        self.search_field = MDTextField(
            hint_text="Поиск песен...",
            size_hint_x=1,
            font_size=sp(15),
            height=dp(42),
            on_text_validate=self._on_search,
            mode="fill"
        )

        self.search_field.line_color_normal = [0, 0, 0, 0]
        self.search_field.line_color_focus = [0, 0, 0, 0]
        self.search_field.fill_color_normal = [1, 1, 1, 0]
        self.search_field.fill_color_focus = [1, 1, 1, 0]
        self.search_field.hint_text_color = [0.6, 0.6, 0.6, 1]
        self.search_field.theme_text_color = "Custom"
        self.search_field.text_color = [0.1, 0.1, 0.1, 1]

        self.search_field.bind(text=self._on_text_change)

        self.clear_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear,
            opacity=0,
            disabled=True,
            pos_hint={'center_y': 0.5}
        )

        self.search_icon = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search,
            pos_hint={'center_y': 0.5}
        )

        self.add_widget(self.search_icon)
        self.add_widget(self.search_field)
        self.add_widget(self.clear_btn)

        self.search_field.bind(focus=self._on_focus)

    def _on_text_change(self, instance, text):
        self.current_query = text
        if text.strip():
            self.clear_btn.opacity = 1
            self.clear_btn.disabled = False
        else:
            self.clear_btn.opacity = 0
            self.clear_btn.disabled = True

        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if not text.strip():
            if self.on_clear:
                self.on_clear()
        else:
            self._search_timer = Clock.schedule_once(lambda dt: self._do_search(), 0.5)

    def _do_search(self):
        if self.on_search and self.current_query:
            text = self.current_query.strip()
            if text:
                self.on_search(text)

    def _on_search(self, instance):
        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear(self, instance):
        self.search_field.text = ""
        self.clear_btn.opacity = 0
        self.clear_btn.disabled = True
        self.current_query = ""
        if self.on_clear:
            self.on_clear()
        self.search_field.focus = True

    def _on_focus(self, instance, value):
        if value:
            self.line_color = [0.1, 0.1, 0.1, 0.3]
            self.line_width = 1.8
        else:
            self.line_color = [0.1, 0.1, 0.1, 0.3]
            self.line_width = 1.5

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0
        self.clear_btn.disabled = True
        self.current_query = ""

    def focus(self):
        self.search_field.focus = True


# ============ КОМПОНЕНТЫ МЕНЮ ============

class FlagToggle(ButtonBehavior, MDBoxLayout):
    """Кнопка-флаг для переключения языка с подписью"""

    def __init__(self, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press
        self.current_language = 'ru'

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = dp(1)
        self.md_bg_color = [0, 0, 0, 0]

        flag_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(28),
            md_bg_color=[0, 0, 0, 0]
        )

        self.flag_image = Image(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        flag_container.add_widget(self.flag_image)

        self.label = MDLabel(
            text="RUS",
            font_size=sp(9),
            halign="center",
            valign="top",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            bold=True,
            size_hint_y=None,
            height=dp(14)
        )

        self.add_widget(flag_container)
        self.add_widget(self.label)

        self._update_flag()

        self.flag_image.bind(on_touch_down=self._on_press)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _on_enter(self, *args):
        self.md_bg_color = [1, 1, 1, 0.05]

    def _on_leave(self, *args):
        self.md_bg_color = [0, 0, 0, 0]

    def _on_press(self, instance, touch):
        if self.collide_point(*touch.pos) and self.on_press_callback:
            self.on_press_callback()
            return True
        return False

    def _update_flag(self):
        if self.current_language == 'ru':
            if _shared_rus_flag_texture:
                self.flag_image.texture = _shared_rus_flag_texture
            else:
                self.flag_image.text = "🇷🇺"
            self.label.text = "RUS"
        elif self.current_language == 'en':
            if _shared_eng_flag_texture:
                self.flag_image.texture = _shared_eng_flag_texture
            else:
                self.flag_image.text = "🇬🇧"
            self.label.text = "ENG"
        else:  # digits - используем Material Design иконку
            self.flag_image.text = "🔢"
            self.label.text = "0-9"

    def set_language(self, language):
        self.current_language = language
        self._update_flag()


class LetterButton(MDBoxLayout):
    """Кнопка буквы в меню (как в аккордах)"""

    def __init__(self, text, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press
        self.is_selected = False

        self.size_hint = (None, 1)
        self.width = dp(32)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = 0
        self.md_bg_color = [0, 0, 0, 0]

        display_text = text

        self.label = MDLabel(
            text=display_text,
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            bold=True,
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
            self.label.text_color = [1, 1, 1, 0.7]

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
        if self.is_selected:
            self.md_bg_color = [0.0, 0.74, 0.83, 1]
            self.label.text_color = [1, 1, 1, 1]
            self.radius = [dp(6), dp(6), dp(6), dp(6)]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = [1, 1, 1, 0.7]
            self.radius = [0, 0, 0, 0]


class AlphabetMenu(MDBoxLayout):
    """Меню с буквами алфавита (скроллится) - слева от флага"""

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
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.md_bg_color = [0, 0, 0, 0]

        self.scroll = None
        self.container = None
        self.buttons = []

        self._build_ui()

    def _build_ui(self):
        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        self.container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(3),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )
        self.container.bind(minimum_width=self.container.setter('width'))

        self._populate_items()

        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def _populate_items(self):
        self.container.clear_widgets()
        self.buttons = []

        if self.current_language == 'ru':
            letters = self.RU_LETTERS
        elif self.current_language == 'en':
            letters = self.EN_LETTERS
        else:  # digits
            letters = self.DIGITS_LETTERS

        for letter in letters:
            btn = LetterButton(
                text=letter,
                on_press=self._on_letter_press
            )
            if letter == self.current_selection:
                btn.set_selected(True)
            self.buttons.append(btn)
            self.container.add_widget(btn)

        self.container.width = sum(btn.width + dp(3) for btn in self.buttons) + dp(8)

    def _on_letter_press(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)
        if self.on_letter_press:
            self.on_letter_press(letter)

    def set_language(self, language):
        if self.current_language == language and self.buttons:
            return
        self.current_language = language
        self.current_selection = None
        self._populate_items()

    def set_current(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)


class SongsMenu(MDCard):
    """Единое меню: БУКВЫ (скролл) | ЯЗЫК (флаг с подписью) - флаг справа"""

    def __init__(self,
                 on_language_toggle=None,
                 on_letter_press=None,
                 current_language='ru',
                 **kwargs):
        super().__init__(**kwargs)

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0, 0, 0, 0.08]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.8
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        # 1. БУКВЫ (слева)
        self.alphabet_menu = AlphabetMenu(
            on_letter_press=on_letter_press,
            current_language=current_language
        )

        # 2. ЯЗЫК (флаг с подписью) - справа
        self.flag_toggle = FlagToggle(
            on_press=on_language_toggle
        )
        self.flag_toggle.current_language = current_language
        self.flag_toggle._update_flag()

        flag_container = MDBoxLayout(
            size_hint_x=None,
            width=dp(44),
            orientation='vertical'
        )
        flag_container.add_widget(self.flag_toggle)

        self.add_widget(self.alphabet_menu)
        self.add_widget(self._create_divider())
        self.add_widget(flag_container)

    def _create_divider(self):
        return MDBoxLayout(
            size_hint_x=None,
            width=dp(1),
            md_bg_color=[1, 1, 1, 0.1]
        )

    def set_language(self, language):
        self.flag_toggle.set_language(language)
        self.alphabet_menu.set_language(language)

    def set_current_letter(self, letter):
        self.alphabet_menu.set_current(letter)


# ============ МЕНЮ С ПЕСНЯМИ ИСПОЛНИТЕЛЯ ============

class ArtistSongsMenu(MDCard):
    """Меню с горизонтальным списком песен исполнителя"""

    def __init__(self,
                 songs=None,
                 on_song_select=None,
                 on_back_press=None,
                 **kwargs):
        super().__init__(**kwargs)

        self.songs = songs or []
        self.on_song_select = on_song_select
        self.on_back_press = on_back_press

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0, 0, 0, 0.08]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.8
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        self._build_ui()

    def _build_ui(self):
        # Стрелка назад (слева)
        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, 1),
            width=dp(44),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_back,
            ripple_scale=0
        )

        # Контейнер с песнями
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(6),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )
        container.bind(minimum_width=container.setter('width'))

        for song in self.songs:
            btn = MDRaisedButton(
                text=song.get('title', ''),
                size_hint=(None, 1),
                width=self._get_button_width(song.get('title', '')),
                md_bg_color=[0, 0, 0, 0],
                text_color=[1, 1, 1, 0.8],
                font_size=sp(12),
                elevation=0,
                on_release=lambda x, s=song: self._on_song_select(s)
            )
            container.add_widget(btn)

        # Добавляем ширину контейнера
        if self.songs:
            container.width = sum(btn.width + dp(6) for btn in container.children) + dp(8)

        scroll.add_widget(container)

        # Собираем UI
        self.add_widget(self.back_btn)
        self.add_widget(self._create_divider())
        self.add_widget(scroll)

    def _create_divider(self):
        return MDBoxLayout(
            size_hint_x=None,
            width=dp(1),
            md_bg_color=[1, 1, 1, 0.1]
        )

    def _get_button_width(self, text):
        base_width = dp(30)
        char_width = dp(7)
        padding = dp(16)
        min_width = dp(36)
        max_width = dp(120)

        width = base_width + len(text) * char_width + padding
        width = max(min_width, min(width, max_width))
        return width

    def _on_back(self, instance):
        if self.on_back_press:
            self.on_back_press()

    def _on_song_select(self, song):
        if self.on_song_select:
            song_id = song.get('song_id', 0)
            title = song.get('title', '')
            self.on_song_select(song_id, title)

    def update_songs(self, songs):
        """Обновляет список песен"""
        self.songs = songs
        self.clear_widgets()
        self._build_ui()


# ============ RECYCLEVIEW КАРТОЧКИ ============

class ArtistCard(RecycleDataViewBehavior, MDCard):
    """Карточка исполнителя с иконкой artist_png"""

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
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self.clip = True
        self._build_ui()

    def _build_ui(self):
        self.icon = Image(
            size_hint=(None, 1),
            width=dp(28),
            allow_stretch=True,
            keep_ratio=True
        )

        if _shared_artist_icon_texture:
            self.icon.texture = _shared_artist_icon_texture
        else:
            self.icon.text = "🎤"

        self.artist_label = MDLabel(
            font_size=sp(15),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right",
            valign="middle",
            size_hint_x=1
        )

        self.count_label = MDLabel(
            text="",
            font_size=sp(11),
            size_hint_x=None,
            width=dp(40),
            halign="right",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4]
        )

        arrow = MDLabel(
            text="›",
            font_size=sp(22),
            size_hint_x=None,
            width=dp(24),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon)
        self.add_widget(self.artist_label)
        self.add_widget(self.count_label)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        self.artist_name = data.get('artist', '')
        self.songs_count = data.get('songs_count', 0)
        self.on_click = data.get('on_click')
        self.artist_label.text = self.artist_name
        self.count_label.text = str(self.songs_count) if self.songs_count > 0 else ""
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.artist_name, self.songs_count)
            return True
        return super().on_touch_down(touch)


class SongCard(RecycleDataViewBehavior, MDCard):
    """Карточка песни - такой же стиль как у исполнителей, иконка song_png"""

    title = StringProperty('')
    tabs_count = NumericProperty(0)
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
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self.clip = True
        self._build_ui()

    def _build_ui(self):
        # Иконка песни
        self.icon = Image(
            size_hint=(None, 1),
            width=dp(28),
            allow_stretch=True,
            keep_ratio=True
        )
        if _shared_song_icon_texture:
            self.icon.texture = _shared_song_icon_texture
        else:
            self.icon.text = "🎵"

        # Название песни
        self.title_label = MDLabel(
            font_size=sp(15),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right",
            valign="middle",
            size_hint_x=1
        )

        # Количество подборов (просто цифра)
        self.count_label = MDLabel(
            text="",
            font_size=sp(11),
            size_hint_x=None,
            width=dp(40),
            halign="right",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4]
        )

        # Стрелка
        arrow = MDLabel(
            text="›",
            font_size=sp(22),
            size_hint_x=None,
            width=dp(24),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon)
        self.add_widget(self.title_label)
        self.add_widget(self.count_label)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        self.title = data.get('title', '')
        self.tabs_count = data.get('tabs_count', 0)
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.title_label.text = self.title
        self.count_label.text = str(self.tabs_count) if self.tabs_count > 0 else ""
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


class SearchSongCard(RecycleDataViewBehavior, MDCard):
    """Карточка песни для поиска"""

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
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self.clip = True
        self._build_ui()

    def _build_ui(self):
        self.icon = Image(
            size_hint=(None, 1),
            width=dp(28),
            allow_stretch=True,
            keep_ratio=True
        )
        if _shared_song_icon_texture:
            self.icon.texture = _shared_song_icon_texture
        else:
            self.icon.text = "🎵"

        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        self.artist_label = MDLabel(
            font_size=sp(15),
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right",
            valign="middle"
        )

        self.title_label = MDLabel(
            font_size=sp(12),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle"
        )

        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)

        arrow = MDLabel(
            text="›",
            font_size=sp(22),
            size_hint_x=None,
            width=dp(24),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon)
        self.add_widget(text_layout)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        self.artist = data.get('artist', '')
        self.title = data.get('title', '')
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.artist_label.text = self.artist
        self.title_label.text = self.title
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


# ============ RECYCLEVIEW ============

class SongsRecycleView(RecycleView):
    """Виртуализированный список"""

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
    """Экран песен с единым меню БУКВЫ | ЯЗЫК"""

    # Список языков для переключения
    LANGUAGES = ['ru', 'en', 'digits']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.current_artist = None
        self.is_search_mode = False
        self.search_results = []
        self.current_language = 'ru'
        self._lang_index = 0
        self._selected_song_id = None
        self._temp_scroll_position = None
        self._is_restoring = False
        self._saved_scroll_position = 1.0  # позиция скролла в списке исполнителей
        self._is_artist_songs_mode = False  # режим отображения песен исполнителя

        # Для загрузки исполнителей
        self._all_artists = []
        self._page = 0
        self._limit = 200
        self._is_loading_more = False
        self._has_more = True
        self._loading_all = False
        self._total_artists = 0

        # Для загрузки песен исполнителя
        self._all_songs = []
        self._page_songs = 0
        self._is_loading_more_songs = False
        self._has_more_songs = True
        self._total_songs = 0

        self.search_bar = None
        self._main_label = None
        self._result_label = None
        self.songs_menu = None
        self._songs_menu_widget = None  # для хранения меню с песнями
        self._hint_timer = None
        self.recycle_view = None
        self._main_layout = None
        self._menu_container = None  # контейнер для меню

        load_shared_icons_sync()

        self.init_ui()
        self.load_background()

        logger.info('Экран песен создан с объединенной логикой')

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

    def init_ui(self):
        """Инициализирует UI с единым меню и RecycleView"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))
        self._main_layout = main_layout

        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        content_padding = layout_config.get_content_padding()
        padding = content_padding

        # ============ 1. ПОИСК ============
        search_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(48),
            padding=[padding[0], 0, padding[2], 0]
        )
        self.search_bar = SearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        search_container.add_widget(self.search_bar)
        main_layout.add_widget(search_container)

        main_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # ============ 2. ОСНОВНОЙ ЛЕЙБЛ ============
        self._main_label = MDLabel(
            text="Поиск исполнителей по алфавиту",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
        )
        main_layout.add_widget(self._main_label)

        main_layout.add_widget(Widget(size_hint_y=None, height=dp(2)))

        # ============ 3. МЕНЮ ============
        menu_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(56),
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

        # ============ 4. ЛЕЙБЛ С РЕЗУЛЬТАТАМИ ============
        self._result_label = MDLabel(
            text="",
            font_size=sp(13),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            opacity=0,
            bold=True
        )
        main_layout.add_widget(self._result_label)

        # ============ 5. RECYCLEVIEW ============
        bottom_padding = layout_config.get_bottom_padding()

        wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0,
            padding=[padding[0], dp(4), padding[2], bottom_padding]
        )

        self.recycle_view = SongsRecycleView(
            on_item_click=self.on_item_selected,
            viewclass='ArtistCard'
        )
        wrapper.add_widget(self.recycle_view)

        main_layout.add_widget(wrapper)

        self.clear_widgets()
        self.add_widget(main_layout)

        logger.info(f"UI песен построен")

    def _toggle_language(self):
        """Переключение языка по кругу: ru -> en -> digits -> ru"""
        self._lang_index = (self._lang_index + 1) % len(self.LANGUAGES)
        self.current_language = self.LANGUAGES[self._lang_index]

        lang_names = {'ru': 'Русский', 'en': 'English', 'digits': '0-9'}
        self._show_temporary_hint(f"Выбран {lang_names[self.current_language]}", 1.2)

        self.songs_menu.set_language(self.current_language)
        self.current_letter = None
        self.current_artist = None
        self.clear_search()

        logger.info(f"🔤 Язык изменён на: {self.current_language}")

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
            self._main_label.text = "Результаты поиска песен"
        elif self.current_artist and self._is_artist_songs_mode:
            self._main_label.text = f"Песни исполнителя: {self.current_artist}"
        elif self.current_artist:
            self._main_label.text = f"Песни исполнителя: {self.current_artist}"
        else:
            self._main_label.text = "Поиск исполнителей по алфавиту"

    def _show_result_label(self, text):
        """Показывает лейбл с информацией о результатах"""
        if self._result_label:
            self._result_label.text = text
            self._result_label.opacity = 1

    def _hide_result_label(self):
        """Скрывает лейбл с результатами"""
        if self._result_label:
            self._result_label.text = ""
            self._result_label.opacity = 0

    def _show_empty(self, text="Нет исполнителей"):
        """Показывает сообщение об отсутствии исполнителей в лейбле результатов"""
        self._show_result_label(text)

    def _hide_empty(self):
        """Скрывает сообщение об отсутствии - просто убираем лейбл"""
        self._hide_result_label()

    def _show_loading(self, text="Идёт загрузка данных..."):
        """Показывает текст загрузки в основном лейбле"""
        self._show_hint(text)

    def _hide_loading(self):
        """Скрывает текст загрузки - восстанавливает подсказку"""
        self._restore_hint()

    # ============ ПЕРЕКЛЮЧЕНИЕ МЕЖДУ РЕЖИМАМИ ============

    def switch_to_artist_songs(self):
        """Переключает меню на список песен исполнителя"""
        if not self.current_artist or not self._all_songs:
            return

        logger.info(f"🎵 Переключение на меню песен исполнителя: {self.current_artist}")

        # Сохраняем текущую позицию скролла в списке исполнителей
        if self.recycle_view and not self.is_search_mode:
            self._saved_scroll_position = self.recycle_view.scroll_y
            logger.info(f"📜 Сохранена позиция скролла исполнителей: {self._saved_scroll_position:.2f}")

        # Создаём меню с песнями
        self._songs_menu_widget = ArtistSongsMenu(
            songs=self._all_songs,
            on_song_select=self.on_song_selected,
            on_back_press=self.switch_to_artists_mode
        )

        # Заменяем меню
        if self.songs_menu and self._menu_container:
            if self.songs_menu in self._menu_container.children:
                self._menu_container.remove_widget(self.songs_menu)
            if self._songs_menu_widget not in self._menu_container.children:
                self._menu_container.add_widget(self._songs_menu_widget)

        self._is_artist_songs_mode = True

        # Обновляем лейбл
        self._main_label.text = f"Песни исполнителя: {self.current_artist}"

        # Скрываем результат
        self._hide_result_label()

        # Обновляем TopNav — показываем настройки
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title("Песни")
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

    def switch_to_artists_mode(self):
        """Возвращает меню к алфавиту"""
        logger.info("🔙 Возврат к меню алфавита")

        # Удаляем меню с песнями
        if self._songs_menu_widget and self._menu_container:
            if self._songs_menu_widget in self._menu_container.children:
                self._menu_container.remove_widget(self._songs_menu_widget)
            self._songs_menu_widget = None

        # Восстанавливаем стандартное меню
        if self.songs_menu and self._menu_container:
            if self.songs_menu not in self._menu_container.children:
                self._menu_container.add_widget(self.songs_menu)

        # Восстанавливаем текущую букву в меню
        if self.songs_menu and self.current_letter:
            self.songs_menu.set_current_letter(self.current_letter)

        self._is_artist_songs_mode = False

        # Восстанавливаем лейбл
        if self.is_search_mode:
            self._main_label.text = "Результаты поиска песен"
        elif self.current_letter:
            self._main_label.text = "Поиск исполнителей по алфавиту"
        else:
            self._main_label.text = "Поиск исполнителей по алфавиту"

        # Восстанавливаем позицию скролла в списке исполнителей
        def restore_artists_scroll(dt):
            if self.recycle_view and self._saved_scroll_position is not None:
                self.recycle_view.scroll_y = self._saved_scroll_position
                logger.info(f"📜 Восстановлена позиция скролла исполнителей: {self._saved_scroll_position:.2f}")

        Clock.schedule_once(restore_artists_scroll, 0.1)
        Clock.schedule_once(restore_artists_scroll, 0.2)

        # Скрываем результат
        self._hide_result_label()

        # Обновляем TopNav — показываем настройки
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title("Песни")
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

    # ============ ЗАГРУЗКА ИСПОЛНИТЕЛЕЙ ============

    def _load_artists(self, letter):
        """Загружает исполнителей для буквы с пагинацией"""
        logger.info(f"_load_artists: {letter}")

        self.current_artist = None
        self.current_letter = letter

        # Если мы в режиме песен — возвращаемся к алфавиту
        if self._is_artist_songs_mode:
            self.switch_to_artists_mode()

        # Для цифр показываем специальную подсказку
        if self.current_language == 'digits':
            display_letter = '#' if letter == '#' else letter
            self._show_loading(f"Загрузка исполнителей на '{display_letter}'...")
        else:
            self._show_loading(f"Загрузка исполнителей на букву '{letter}'...")

        self._hide_result_label()

        self._page = 0
        self._all_artists = []
        self._has_more = True
        self._is_loading_more = False
        self._total_artists = 0

        self.recycle_view.viewclass = 'ArtistCard'
        self.recycle_view.clear()
        self._hide_empty()

        if self.current_language == 'digits':
            api.get_artists_by_digits(
                limit=self._limit,
                offset=0,
                on_success=self._on_digits_first_page_loaded,
                on_failure=self._on_artists_page_failed
            )
        else:
            api.get_artists_by_letter(
                letter=letter,
                limit=self._limit,
                offset=0,
                on_success=self._on_artists_first_page_loaded,
                on_failure=self._on_artists_page_failed
            )

    def _on_digits_first_page_loaded(self, data):
        """Обработчик первой страницы цифр - фильтруем по выбранной цифре или #"""
        if data is None:
            data = {"artists": [], "total": 0}
        if not isinstance(data, dict):
            data = {"artists": [], "total": 0}

        artists = data.get('artists', [])
        total = data.get('total', 0)

        if not isinstance(artists, list):
            artists = []
            total = 0

        # Фильтруем исполнителей по выбранной цифре или #
        filtered_artists = []
        for a in artists:
            name = a.get('artist') if isinstance(a, dict) else None
            if name:
                first_char = name[0] if name else ''
                if self.current_letter == '#':
                    is_cyrillic = ('А' <= first_char <= 'Я') or ('а' <= first_char <= 'я') or first_char in ['Ё', 'ё']
                    is_latin = ('A' <= first_char <= 'Z') or ('a' <= first_char <= 'z')
                    is_digit = first_char.isdigit()

                    if not is_cyrillic and not is_latin and not is_digit:
                        filtered_artists.append(a)
                else:
                    if first_char == self.current_letter:
                        filtered_artists.append(a)

        self._total_artists = len(filtered_artists)

        for a in filtered_artists:
            name = a.get('artist') if isinstance(a, dict) else None
            count = a.get('songs_count', 0) if isinstance(a, dict) else 0
            if name:
                self._all_artists.append({'artist': name, 'songs_count': count})

        logger.info(
            f"📄 Первая страница цифр: {len(self._all_artists)} из {self._total_artists} для '{self.current_letter}'")

        if len(self._all_artists) >= self._total_artists:
            self._has_more = False
            self._display_artists()
            return

        self._load_next_digits_pages()

    def _load_next_digits_pages(self):
        """Загружает остальные страницы цифр"""
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
            limit=self._limit,
            offset=offset,
            on_success=self._on_digits_next_page_loaded,
            on_failure=self._on_artists_page_failed
        )

    def _on_digits_next_page_loaded(self, data):
        """Обработчик следующей страницы цифр - фильтруем"""
        self._is_loading_more = False

        if data is None:
            data = {"artists": [], "total": 0}
        if not isinstance(data, dict):
            data = {"artists": [], "total": 0}

        artists = data.get('artists', [])
        if not isinstance(artists, list) or not artists:
            self._has_more = False
            self._display_artists()
            return

        for a in artists:
            name = a.get('artist') if isinstance(a, dict) else None
            if name:
                first_char = name[0] if name else ''
                if self.current_letter == '#':
                    is_cyrillic = ('А' <= first_char <= 'Я') or ('а' <= first_char <= 'я') or first_char in ['Ё', 'ё']
                    is_latin = ('A' <= first_char <= 'Z') or ('a' <= first_char <= 'z')
                    is_digit = first_char.isdigit()

                    if not is_cyrillic and not is_latin and not is_digit:
                        self._all_artists.append({
                            'artist': name,
                            'songs_count': a.get('songs_count', 0) if isinstance(a, dict) else 0
                        })
                else:
                    if first_char == self.current_letter:
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
        """Обработчик первой страницы исполнителей"""
        if data is None:
            data = {"artists": [], "total": 0}
        if not isinstance(data, dict):
            data = {"artists": [], "total": 0}

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

        logger.info(f"📄 Первая страница исполнителей: {len(self._all_artists)} из {total}")

        if len(self._all_artists) >= total:
            self._has_more = False
            self._display_artists()
            return

        self._load_next_artists_pages()

    def _load_next_artists_pages(self):
        """Загружает остальные страницы исполнителей"""
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
            letter=self.current_letter,
            limit=self._limit,
            offset=offset,
            on_success=self._on_artists_next_page_loaded,
            on_failure=self._on_artists_page_failed
        )

    def _on_artists_next_page_loaded(self, data):
        """Обработчик следующей страницы исполнителей"""
        self._is_loading_more = False

        if data is None:
            data = {"artists": [], "total": 0}
        if not isinstance(data, dict):
            data = {"artists": [], "total": 0}

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
        """Показывает список исполнителей"""
        self._hide_loading()

        # Если мы в режиме песен — возвращаемся к алфавиту
        if self._is_artist_songs_mode:
            self.switch_to_artists_mode()

        if not self._all_artists:
            self._show_empty("Нет исполнителей")
            self.recycle_view.clear()
            return

        self._hide_empty()
        self.recycle_view.viewclass = 'ArtistCard'
        self.recycle_view.set_items(self._all_artists, self.on_artist_selected)
        Clock.schedule_once(lambda dt: setattr(self.recycle_view, 'scroll_y', 1.0), 0.1)
        self._show_result_label(f"Исполнители: {len(self._all_artists)}")

        # Привязываем отслеживание скролла для дозагрузки
        self._bind_scroll_for_load()

    def _on_artists_page_failed(self, req, error):
        """Обработчик ошибки загрузки исполнителей"""
        self._is_loading_more = False
        self._hide_loading()
        logger.error(f"❌ Ошибка загрузки исполнителей: {error}")
        self._show_empty("Ошибка загрузки\nПроверьте интернет")

    # ============ ЗАГРУЗКА ПЕСЕН ИСПОЛНИТЕЛЯ ============

    def _load_artist_songs(self, artist):
        """Загружает песни исполнителя с пагинацией"""
        logger.info(f"_load_artist_songs: {artist}")

        self.current_artist = artist
        self.current_letter = None
        if self.songs_menu:
            self.songs_menu.set_current_letter(None)
        self._show_loading("Идёт загрузка данных...")
        self._hide_result_label()

        self._page_songs = 0
        self._all_songs = []
        self._has_more_songs = True
        self._is_loading_more_songs = False
        self._total_songs = 0

        self.recycle_view.viewclass = 'SongCard'
        self.recycle_view.clear()
        self._hide_empty()

        api.get_songs_by_artist(
            artist=artist,
            limit=self._limit,
            offset=0,
            on_success=self._on_songs_first_page_loaded,
            on_failure=self._on_songs_page_failed
        )

    def _on_songs_first_page_loaded(self, data):
        """Обработчик первой страницы песен"""
        if data is None:
            data = {"songs": [], "total": 0}
        if not isinstance(data, dict):
            data = {"songs": [], "total": 0}

        songs = data.get('songs', [])
        total = data.get('total', 0)

        if not isinstance(songs, list):
            songs = []
            total = 0

        self._total_songs = total

        for song in songs:
            self._all_songs.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'tabs_count': song.get('tabs_count', 1),
                'on_click': self.on_song_selected
            })

        logger.info(f"📄 Первая страница песен: {len(self._all_songs)} из {total}")

        if len(self._all_songs) >= total:
            self._has_more_songs = False
            self._display_songs()
            return

        self._load_next_songs_pages()

    def _load_next_songs_pages(self):
        """Загружает остальные страницы песен"""
        if not self._has_more_songs or self._is_loading_more_songs:
            return

        if self._total_songs > 0 and len(self._all_songs) >= self._total_songs:
            self._has_more_songs = False
            self._display_songs()
            return

        self._is_loading_more_songs = True
        self._page_songs += 1
        offset = self._page_songs * self._limit

        api.get_songs_by_artist(
            artist=self.current_artist,
            limit=self._limit,
            offset=offset,
            on_success=self._on_songs_next_page_loaded,
            on_failure=self._on_songs_page_failed
        )

    def _on_songs_next_page_loaded(self, data):
        """Обработчик следующей страницы песен"""
        self._is_loading_more_songs = False

        if data is None:
            data = {"songs": [], "total": 0}
        if not isinstance(data, dict):
            data = {"songs": [], "total": 0}

        songs = data.get('songs', [])
        if not isinstance(songs, list) or not songs:
            self._has_more_songs = False
            self._display_songs()
            return

        for song in songs:
            self._all_songs.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'tabs_count': song.get('tabs_count', 1),
                'on_click': self.on_song_selected
            })

        if len(self._all_songs) >= self._total_songs:
            self._has_more_songs = False
            self._display_songs()
            return

        Clock.schedule_once(lambda dt: self._load_next_songs_pages(), 0.1)

    def _display_songs(self):
        """Показывает список песен и переключает меню"""
        self._hide_loading()

        if not self._all_songs:
            self._show_empty("Нет песен")
            self.recycle_view.clear()
            return

        self._hide_empty()
        self.recycle_view.viewclass = 'SongCard'
        self.recycle_view.set_items(self._all_songs, self.on_song_selected)
        Clock.schedule_once(lambda dt: setattr(self.recycle_view, 'scroll_y', 1.0), 0.1)
        self._show_result_label(f"Песни: {len(self._all_songs)}")

        # ✅ Переключаем меню на песни исполнителя
        self.switch_to_artist_songs()

        # Привязываем отслеживание скролла для дозагрузки
        self._bind_scroll_for_load()

    def _on_songs_page_failed(self, req, error):
        """Обработчик ошибки загрузки песен"""
        self._is_loading_more_songs = False
        self._hide_loading()
        logger.error(f"❌ Ошибка загрузки песен: {error}")
        self._show_empty("Ошибка загрузки\nПроверьте интернет")

    # ============ ОТСЛЕЖИВАНИЕ СКРОЛЛА ДЛЯ ДОГРУЗКИ ============

    def _bind_scroll_for_load(self):
        """Привязывает отслеживание скролла для дозагрузки"""
        if self.recycle_view:
            try:
                self.recycle_view.unbind(scroll_y=self._check_scroll_for_load)
            except:
                pass
            self.recycle_view.bind(scroll_y=self._check_scroll_for_load)

    def _check_scroll_for_load(self, instance, value):
        """Проверяет скролл и при необходимости догружает данные"""
        if value > 0.05:
            return

        if self._is_loading_more or self._is_loading_more_songs or self._is_restoring:
            return

        if self.current_artist and self._has_more_songs and len(self._all_songs) < self._total_songs:
            logger.info(f"🔄 Догружаем песни при скролле (scroll_y={value:.2f})...")
            self._load_remaining_songs()
        elif self.current_letter and self._has_more and len(self._all_artists) < self._total_artists:
            logger.info(f"🔄 Догружаем исполнителей при скролле (scroll_y={value:.2f})...")
            self._load_remaining_artists()

    # ============ ОБРАБОТЧИКИ ============

    def on_letter_press(self, letter):
        """Обработчик выбора буквы - загружает исполнителей"""
        logger.info(f"Выбрана буква: {letter}")

        # Если мы в режиме песен — возвращаемся к алфавиту
        if self._is_artist_songs_mode:
            self.switch_to_artists_mode()

        self.is_search_mode = False
        self.current_artist = None
        self.search_bar.clear()
        if self.songs_menu:
            self.songs_menu.set_current_letter(letter)
        self._load_artists(letter)

    def on_artist_selected(self, artist, songs_count):
        """Обработчик выбора исполнителя - загружает песни и переключает меню"""
        logger.info(f"Выбран исполнитель: {artist}")

        # Загружаем песни
        self.current_artist = artist
        self.is_search_mode = False
        self.search_bar.clear()
        if self.songs_menu:
            self.songs_menu.set_current_letter(None)
        self._load_artist_songs(artist)

    def on_song_selected(self, song_id, title):
        """Обработчик выбора песни"""
        logger.info(f"Выбрана песня: {title}, id: {song_id}")

        # ✅ СОХРАНЯЕМ ID ВЫБРАННОЙ ПЕСНИ
        self._selected_song_id = song_id

        # ✅ СОХРАНЯЕМ ПОЗИЦИЮ СКРОЛЛА ПЕРЕД ПЕРЕХОДОМ
        if self.recycle_view:
            self._temp_scroll_position = self.recycle_view.scroll_y
            logger.info(f"📜 Сохраняем позицию перед переходом: {self._temp_scroll_position:.2f}")

        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        # ✅ СОХРАНЯЕМ СОСТОЯНИЕ ПЕРЕД ПЕРЕХОДОМ
        self.save_current_state()

        # ✅ СОХРАНЯЕМ, ЧТО ПРИШЛИ ИЗ songs
        screen_state.set_previous_screen('songs')

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                song_detail_screen.set_previous_screen('songs')
                song_detail_screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def do_search(self, query):
        """Выполняет поиск песен"""
        logger.info(f"🔍 Поиск: {query}")
        query = query.strip()

        if len(query) < 2:
            self._show_temporary_hint("Введите минимум 2 символа", 1.5)
            return

        # Если мы в режиме песен — возвращаемся к алфавиту
        if self._is_artist_songs_mode:
            self.switch_to_artists_mode()

        self.is_search_mode = True
        self.current_letter = None
        self.current_artist = None
        if self.songs_menu:
            self.songs_menu.set_current_letter(None)
        self._show_loading("Идёт загрузка данных...")
        self.recycle_view.clear()
        self.recycle_view.viewclass = 'SearchSongCard'

        api.search_songs(
            query=query,
            limit=50,
            on_success=self._on_search_success,
            on_failure=self._on_search_failed
        )

    def _on_search_success(self, results):
        """Обработчик успешного поиска"""
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
            self._show_empty("Ничего не найдено")
        else:
            self.recycle_view.set_songs(self.search_results, self.on_song_selected)
            self._show_result_label(f"Найдено песен: {len(self.search_results)}")

    def _on_search_failed(self, req, error):
        """Обработчик ошибки поиска"""
        self.search_results = []
        self.recycle_view.clear()
        self._hide_result_label()
        self._show_empty("Ошибка поиска\nПроверьте интернет")
        logger.error(f"Ошибка поиска: {error}")

    def clear_search(self):
        """Очищает поиск"""
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

        # Если мы в режиме песен — возвращаемся к алфавиту
        if self._is_artist_songs_mode:
            self.switch_to_artists_mode()

        self._show_hint("Поиск исполнителей по алфавиту")

    def on_item_selected(self, item_type, *args):
        pass

    # ============ ДОГРУЗКА ДАННЫХ ============

    def _load_remaining_artists(self):
        """Догружает остальных исполнителей в фоне"""
        if not self.current_letter:
            return

        if self._is_loading_more:
            return

        if len(self._all_artists) >= self._total_artists:
            self._has_more = False
            return

        self._is_loading_more = True

        next_page = self._page + 1
        offset = next_page * self._limit

        logger.info(f"🔄 Догружаем исполнителей: страница {next_page + 1}, offset={offset}")

        if self.current_language == 'digits':
            api.get_artists_by_digits(
                limit=self._limit,
                offset=offset,
                on_success=lambda data: self._append_artists(data, next_page),
                on_failure=self._on_artists_page_failed
            )
        else:
            api.get_artists_by_letter(
                letter=self.current_letter,
                limit=self._limit,
                offset=offset,
                on_success=lambda data: self._append_artists(data, next_page),
                on_failure=self._on_artists_page_failed
            )

    def _append_artists(self, data, page):
        """Добавляет загруженных исполнителей и обновляет UI"""
        self._is_loading_more = False

        if data is None:
            return
        if not isinstance(data, dict):
            return

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
        self._show_result_label(f"Исполнители: {len(self._all_artists)} из {self._total_artists}")
        logger.info(f"📄 Загружено {len(self._all_artists)} из {self._total_artists} исполнителей")

        if not self._has_more:
            self._hide_loading()

    def _load_remaining_songs(self):
        """Догружает остальные песни в фоне"""
        if not self.current_artist:
            return

        if self._is_loading_more_songs:
            return

        if len(self._all_songs) >= self._total_songs:
            self._has_more_songs = False
            return

        self._is_loading_more_songs = True

        next_page = self._page_songs + 1
        offset = next_page * self._limit

        logger.info(f"🔄 Догружаем песни: страница {next_page + 1}, offset={offset}")

        api.get_songs_by_artist(
            artist=self.current_artist,
            limit=self._limit,
            offset=offset,
            on_success=lambda data: self._append_songs(data, next_page),
            on_failure=self._on_songs_page_failed
        )

    def _append_songs(self, data, page):
        """Добавляет загруженные песни и обновляет UI"""
        self._is_loading_more_songs = False

        if data is None:
            return
        if not isinstance(data, dict):
            return

        songs = data.get('songs', [])
        if not songs:
            self._has_more_songs = False
            return

        for song in songs:
            self._all_songs.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'tabs_count': song.get('tabs_count', 1),
                'on_click': self.on_song_selected
            })

        self._page_songs = page
        self._has_more_songs = len(self._all_songs) < self._total_songs

        self.recycle_view.set_items(self._all_songs, self.on_song_selected)
        self._show_result_label(f"Песни: {len(self._all_songs)} из {self._total_songs}")
        logger.info(f"📄 Загружено {len(self._all_songs)} из {self._total_songs} песен")

        if not self._has_more_songs:
            self._hide_loading()

    # ============ СОХРАНЕНИЕ СОСТОЯНИЯ ============

    def save_current_state(self):
        """Сохраняет текущее состояние экрана песен"""
        logger.info("=" * 50)
        logger.info("💾 СОХРАНЕНИЕ СОСТОЯНИЯ SongsScreen")

        # Определяем режим
        if self.current_artist and self._all_songs:
            mode = 'songs'
        elif self.is_search_mode and self._all_songs:
            mode = 'search'
        elif self.current_letter and self._all_artists:
            mode = 'artists'
        else:
            mode = 'empty'

        # Сохраняем позицию скролла
        scroll_position = 1.0
        if hasattr(self, '_temp_scroll_position') and self._temp_scroll_position is not None:
            scroll_position = self._temp_scroll_position
            logger.info(f"📜 Используем сохранённую позицию: {scroll_position:.2f}")
        elif self.recycle_view:
            scroll_position = self.recycle_view.scroll_y
            logger.info(f"📜 Текущая позиция скролла: {scroll_position:.2f}")

        state = {
            'mode': mode,
            'current_letter': self.current_letter,
            'current_artist': self.current_artist,
            'is_search_mode': self.is_search_mode,
            'current_language': self.current_language,
            'search_query': self.search_bar.current_query if self.search_bar else '',
            'all_artists': self._all_artists,
            'all_songs': self._all_songs,
            'total_artists': self._total_artists,
            'total_songs': self._total_songs,
            'page': self._page,
            'page_songs': self._page_songs,
            'has_artists': len(self._all_artists) > 0,
            'has_songs': len(self._all_songs) > 0,
            'has_more_artists': self._has_more,
            'has_more_songs': self._has_more_songs,
            'scroll_position': scroll_position,
            'selected_song_id': self._selected_song_id if hasattr(self, '_selected_song_id') else None,
            'is_artist_songs_mode': self._is_artist_songs_mode,
            'saved_scroll_position': self._saved_scroll_position,
        }

        logger.info(f"📦 Сохраняем: mode={mode}, artist={state.get('current_artist')}, "
                    f"artists={len(state.get('all_artists', []))}/{self._total_artists}, "
                    f"songs={len(state.get('all_songs', []))}/{self._total_songs}, "
                    f"scroll={state.get('scroll_position', 1.0):.2f}, "
                    f"songs_mode={state.get('is_artist_songs_mode')}")

        screen_state.save_screen_state('songs', state)
        logger.info("=" * 50)

    def restore_state(self):
        """Восстанавливает состояние экрана песен"""
        logger.info("=" * 50)
        logger.info("📂 ВОССТАНОВЛЕНИЕ СОСТОЯНИЯ SongsScreen")

        state = screen_state.get_screen_state('songs', max_age=300)

        if not state:
            logger.info("❌ Нет сохранённого состояния")
            logger.info("=" * 50)
            return False

        try:
            logger.info(f"📦 Получено состояние: {list(state.keys())}")

            self._is_restoring = True

            # Восстанавливаем базовые данные
            self.current_letter = state.get('current_letter')
            self.current_artist = state.get('current_artist')
            self.is_search_mode = state.get('is_search_mode', False)
            self.current_language = state.get('current_language', 'ru')
            self._total_artists = state.get('total_artists', 0)
            self._total_songs = state.get('total_songs', 0)
            self._page = state.get('page', 0)
            self._page_songs = state.get('page_songs', 0)
            self._has_more = state.get('has_more_artists', True)
            self._has_more_songs = state.get('has_more_songs', True)

            # Восстанавливаем ВСЕ данные
            restored_artists = state.get('all_artists', [])
            restored_songs = state.get('all_songs', [])

            # Получаем режим и позицию скролла
            mode = state.get('mode', 'empty')
            scroll_position = state.get('scroll_position', 1.0)
            saved_scroll_position = state.get('saved_scroll_position', 1.0)
            is_artist_songs_mode = state.get('is_artist_songs_mode', False)

            # Сохраняем позицию скролла для исполнителей
            self._saved_scroll_position = saved_scroll_position

            # Восстанавливаем язык
            if self.current_language in ['ru', 'en', 'digits']:
                self._lang_index = ['ru', 'en', 'digits'].index(self.current_language)
                if self.songs_menu:
                    self.songs_menu.set_language(self.current_language)

            # Восстанавливаем поисковый запрос
            search_query = state.get('search_query', '')
            if search_query and self.search_bar:
                self.search_bar.search_field.text = search_query
                logger.info(f"🔍 Восстановлен запрос: {search_query}")

            # ============ ВОССТАНАВЛИВАЕМ ОТОБРАЖЕНИЕ ============
            if mode == 'songs' and self.current_artist:
                if restored_songs:
                    self._all_songs = restored_songs
                    self.recycle_view.viewclass = 'SongCard'
                    self.recycle_view.set_items(self._all_songs, self.on_song_selected)
                    self._show_result_label(f"Песни: {len(self._all_songs)} из {self._total_songs}")
                    logger.info(f"🎵 Восстановлено {len(self._all_songs)} песен исполнителя {self.current_artist}")

                    # Переключаем меню на песни, если был в этом режиме
                    if is_artist_songs_mode:
                        self.switch_to_artist_songs()
                    else:
                        # Если не были в режиме песен, но есть песни — переключаем
                        self.switch_to_artist_songs()

                    # Если есть ещё страницы — догружаем
                    if self._has_more_songs and len(self._all_songs) < self._total_songs:
                        logger.info(f"🔄 Догружаем остальные песни...")
                        Clock.schedule_once(lambda dt: self._load_remaining_songs(), 0.3)
                else:
                    self._load_artist_songs(self.current_artist)

            elif mode == 'search' and search_query:
                self.do_search(search_query)
                logger.info(f"🔍 Восстановлен поиск: {search_query}")

            elif mode == 'artists' and self.current_letter:
                if restored_artists:
                    self._all_artists = restored_artists
                    self.recycle_view.viewclass = 'ArtistCard'
                    self.recycle_view.set_items(self._all_artists, self.on_artist_selected)
                    self._show_result_label(f"Исполнители: {len(self._all_artists)} из {self._total_artists}")
                    if self.songs_menu and self.current_letter:
                        self.songs_menu.set_current_letter(self.current_letter)
                    logger.info(f"🎤 Восстановлено {len(self._all_artists)} исполнителей на букву {self.current_letter}")

                    # Если были в режиме песен — возвращаемся к алфавиту
                    if is_artist_songs_mode:
                        self.switch_to_artists_mode()

                    if self._has_more and len(self._all_artists) < self._total_artists:
                        logger.info(f"🔄 Догружаем остальных исполнителей...")
                        Clock.schedule_once(lambda dt: self._load_remaining_artists(), 0.3)
                else:
                    self._load_artists(self.current_letter)

            else:
                self.recycle_view.clear()
                self._show_hint("Поиск исполнителей по алфавиту")
                self._hide_result_label()
                logger.info("📄 Пустое состояние")
                self._is_restoring = False
                logger.info("=" * 50)
                return True

            # ============ ВОССТАНАВЛИВАЕМ ПОЗИЦИЮ СКРОЛЛА ============
            def restore_scroll(dt):
                if self.recycle_view:
                    self.recycle_view.scroll_y = scroll_position
                    logger.info(f"📜 Восстановлена позиция скролла: {scroll_position:.2f}")
                    self._bind_scroll_for_load()

            Clock.schedule_once(restore_scroll, 0.1)
            Clock.schedule_once(restore_scroll, 0.2)
            Clock.schedule_once(restore_scroll, 0.3)

            self._is_restoring = False
            logger.info("✅ Восстановление завершено")
            logger.info("=" * 50)
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка восстановления: {e}")
            import traceback
            traceback.print_exc()
            self._is_restoring = False
            logger.info("=" * 50)
            return False

    # ============ on_enter, on_pre_leave, on_leave ============

    def on_pre_leave(self):
        """Вызывается перед тем, как экран будет покинут"""
        logger.info("🚪 on_pre_leave: сохранение состояния перед выходом")

        if self.recycle_view:
            self._temp_scroll_position = self.recycle_view.scroll_y
            logger.info(f"📜 on_pre_leave: позиция скролла: {self._temp_scroll_position:.2f}")

        self.save_current_state()
        return super().on_pre_leave()

    def on_enter(self):
        logger.info("🚪 Вход в экран песен")

        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title("Песни")
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

        restored = self.restore_state()
        logger.info(f"📊 Результат восстановления: {restored}")

        if not restored:
            self._show_hint("Поиск исполнителей по алфавиту")
            self._hide_result_label()
            self.recycle_view.clear()
            logger.info("📄 Показано начальное состояние")

    def on_leave(self):
        logger.info("🚪 Выход из экрана песен")
        logger.info("=" * 50)

        if self.recycle_view:
            self._temp_scroll_position = self.recycle_view.scroll_y
            logger.info(f"📜 on_leave: позиция скролла: {self._temp_scroll_position:.2f}")

        self.save_current_state()

        self.clear_search()
        self._hide_loading()
        self._hide_empty()

        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

        logger.info("=" * 50)

    def go_back(self, instance=None):
        logger.warning("⚠️ go_back вызван на songs_screen, но здесь не должно быть стрелки назад")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'