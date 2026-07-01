# screens/songs_screen.py
"""
Экран песен - с единым меню (ЯЗЫК | БУКВЫ) и поиском
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


def load_shared_icons_sync():
    """Синхронная загрузка иконок - вызывается ДО создания UI"""
    global _shared_rus_flag_texture, _shared_eng_flag_texture, _shared_song_icon_texture

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

        # ============ КРАСИВАЯ ОБВОДКА ============
        self.line_color = [0.1, 0.1, 0.1, 0.3]
        self.line_width = 1.6

        # ============ ПОЛЕ ВВОДА (ПРОЗРАЧНОЕ) ============
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

        # ============ КНОПКА ОЧИСТКИ ============
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

        # ============ ИКОНКА ЛУПЫ ============
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

        # Собираем UI
        self.add_widget(self.search_icon)
        self.add_widget(self.search_field)
        self.add_widget(self.clear_btn)

        # Привязываем фокус для изменения обводки
        self.search_field.bind(focus=self._on_focus)

    def _on_text_change(self, instance, text):
        self.current_query = text
        # Управляем видимостью крестика
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
        """Обработчик фокуса - меняет цвет обводки"""
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

        # Контейнер для флага
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

        # Подпись
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

        # Устанавливаем флаг (иконки уже загружены)
        self._update_flag()

        # Привязываем события
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
        else:
            if _shared_eng_flag_texture:
                self.flag_image.texture = _shared_eng_flag_texture
            else:
                self.flag_image.text = "🇬🇧"
            self.label.text = "ENG"

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

        display_text = '0-9' if text == '09' else text

        self.label = MDLabel(
            text=display_text,
            font_size=sp(11) if text == '09' else sp(13),
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
                letter = '0-9' if self.btn_text == '09' else self.btn_text
                self.on_press_callback(letter)
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
    """Меню с буквами алфавита (скроллится)"""

    RU_LETTERS = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И',
                  'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т',
                  'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь',
                  'Э', 'Ю', 'Я', '#', '09']

    EN_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                  'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                  'U', 'V', 'W', 'X', 'Y', 'Z', '#', '09']

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

        letters = self.RU_LETTERS if self.current_language == 'ru' else self.EN_LETTERS

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
    """Единое меню: ЯЗЫК (флаг с подписью) | БУКВЫ (скролл)"""

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

        self.flag_toggle = FlagToggle(
            on_press=on_language_toggle
        )
        self.flag_toggle.current_language = current_language
        self.flag_toggle._update_flag()

        self.alphabet_menu = AlphabetMenu(
            on_letter_press=on_letter_press,
            current_language=current_language
        )

        flag_container = MDBoxLayout(
            size_hint_x=None,
            width=dp(44),
            orientation='vertical'
        )
        flag_container.add_widget(self.flag_toggle)

        self.add_widget(flag_container)
        self.add_widget(self._create_divider())
        self.add_widget(self.alphabet_menu)

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


# ============ RECYCLEVIEW ДЛЯ РЕЗУЛЬТАТОВ ПОИСКА ============

class SearchSongCard(RecycleDataViewBehavior, MDCard):
    """Карточка песни для RecycleView"""

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


class SongRecycleView(RecycleView):
    """Виртуализированный список песен"""

    def __init__(self, on_song_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_song_click = on_song_click
        self.animate_scroll = False
        self.size_hint = (1, 1)
        self.clip = True
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(48) * 50,
            orientation='vertical',
            spacing=dp(2)
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.viewclass = 'SearchSongCard'
        self.add_widget(self.layout_manager)

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
    """Экран песен с единым меню ЯЗЫК | БУКВЫ"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.is_search_mode = False
        self.search_results = []
        self.current_language = 'ru'

        self.search_bar = None
        self._main_label = None
        self._result_label = None
        self.songs_menu = None
        self._hint_timer = None
        self.search_recycle_view = None

        # ============ ЗАГРУЖАЕМ ИКОНКИ СИНХРОННО ПЕРЕД СОЗДАНИЕМ UI ============
        load_shared_icons_sync()

        self.init_ui()
        self.load_background()

        logger.info('Экран песен создан')

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
        """Инициализирует UI с единым меню"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))

        # Верхний отступ
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

        # Отступ после поиска
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # ============ 2. ОСНОВНОЙ ЛЕЙБЛ ============
        self._main_label = MDLabel(
            text="Поиск исполнителей по алфавиту",  # Изменено
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
        )
        main_layout.add_widget(self._main_label)

        # Отступ
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(2)))

        # ============ 3. МЕНЮ ============
        menu_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(56),
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

        # ============ 5. RECYCLEVIEW С КАРТОЧКАМИ ============
        bottom_padding = layout_config.get_bottom_padding()

        wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0,
            padding=[padding[0], dp(4), padding[2], bottom_padding]
        )

        self.search_recycle_view = SongRecycleView(
            on_song_click=self.on_song_selected
        )
        wrapper.add_widget(self.search_recycle_view)

        main_layout.add_widget(wrapper)

        self.clear_widgets()
        self.add_widget(main_layout)

        logger.info(f"UI песен построен")

    def _toggle_language(self):
        """Переключение языка"""
        if self.current_language == 'ru':
            self.current_language = 'en'
            self._show_temporary_hint("Выбран английский язык", 1.2)
        else:
            self.current_language = 'ru'
            self._show_temporary_hint("Выбран русский язык", 1.2)

        self.songs_menu.set_language(self.current_language)
        self.current_letter = None
        self.clear_search()

        logger.info(f"🔤 Язык изменён на: {self.current_language}")

    def _show_hint(self, text):
        """Показывает подсказку в основном лейбле"""
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None
        if self._main_label:
            self._main_label.text = text

    def _show_temporary_hint(self, text, duration=1.5):
        """Показывает временную подсказку"""
        if self._main_label:
            self._main_label.text = text
            if hasattr(self, '_hint_timer') and self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._restore_hint(), duration)

    def _restore_hint(self):
        """Восстанавливает стандартную подсказку"""
        if hasattr(self, '_hint_timer'):
            self._hint_timer = None
        if self.is_search_mode:
            self._main_label.text = "Результаты поиска песен"  # Изменено
        else:
            self._main_label.text = "Поиск исполнителей по алфавиту"  # Изменено

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

    # ============ ОБРАБОТЧИКИ ============

    def on_letter_press(self, letter):
        """Обработчик выбора буквы - переход на экран исполнителей"""
        logger.info(f"Выбрана буква: {letter}")
        self.current_letter = letter
        self.songs_menu.set_current_letter(letter)
        self.clear_search()
        self._show_hint(f"Исполнители на букву '{letter}'")

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artists_by_letter'):
                artists_screen = self.manager.get_screen('artists_by_letter')
                artists_screen.set_letter(letter)
                self.manager.current = 'artists_by_letter'

    def do_search(self, query):
        """Выполняет поиск песен"""
        logger.info(f"🔍 Поиск: {query}")
        query = query.strip()

        if len(query) < 2:
            self._show_temporary_hint("Введите минимум 2 символа", 1.5)
            return

        self.is_search_mode = True
        self.current_letter = None
        self.songs_menu.set_current_letter(None)
        self._show_hint("Результаты поиска песен")  # Изменено
        self.search_recycle_view.clear()

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
            self.search_recycle_view.clear()
            self._hide_result_label()
            self._show_hint("Ничего не найдено")
        else:
            self.search_recycle_view.set_songs(self.search_results, self.on_song_selected)
            self._show_result_label(f"Найдено песен: {len(self.search_results)}")

    def _on_search_failed(self, req, error):
        """Обработчик ошибки поиска"""
        self.search_results = []
        self.search_recycle_view.clear()
        self._hide_result_label()
        self._show_hint(f"Ошибка поиска: {error}")
        logger.error(f"Ошибка поиска: {error}")

    def clear_search(self):
        """Очищает поиск"""
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.clear()
        self.search_recycle_view.clear()
        self._hide_result_label()
        self._show_hint("Поиск исполнителей по алфавиту")  # Изменено

    def on_song_selected(self, song_id, title):
        """Обработчик выбора песни"""
        logger.info(f"Выбрана песня: {title}, id: {song_id}")
        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                song_detail_screen.set_previous_screen('songs')
                song_detail_screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в экран песен")

        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title("Песни")
                app.top_nav._show_back_button()
                app.top_nav.back_btn.on_release = self.go_back
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

        self._show_hint("Поиск исполнителей по алфавиту")  # Изменено
        self._hide_result_label()

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана песен")
        self.clear_search()
        self.current_letter = None
        self.songs_menu.set_current_letter(None)

        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        """Возврат на home"""
        logger.info("🔙 Возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'