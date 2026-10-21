# screens/dictionary_screen.py
"""
Экран словаря терминов - с единым меню.
Адаптирован под 3 темы и 6 языков.
"""
import importlib
import pkgutil
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
from kivy.graphics import Color, Line, Rectangle
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, ObjectProperty
from kivy.factory import Factory

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from utils.notifications import notify
from utils.screen_state import screen_state
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('Dictionary')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА ДЛЯ СЛОВАРЯ
# ============================================================

class DictionaryColors:
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
            return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        else:
            return [1, 1, 1, 0.6]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.1]
        else:
            return [0, 0, 0, 0.06]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        else:
            return [1, 1, 1, 0.05]

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        else:
            return [0.46, 0.70, 0.71, 1]


# ============ ГЛОБАЛЬНЫЕ ИКОНКИ ============
_shared_rus_flag_texture = None
_shared_eng_flag_texture = None


def load_shared_icons_sync():
    global _shared_rus_flag_texture, _shared_eng_flag_texture
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
        except Exception as e:
            logger.error(f"Ошибка загрузки иконок: {e}")


# ============ ПОИСКОВАЯ СТРОКА ============
class SearchBar(MDCard):
    _DEBOUNCE_SEC = 0.5

    def __init__(self, on_search=None, on_clear=None,
                 hint_text=None, button_text=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self._search_timer = None

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
            padding=[0, dp(10), 0, dp(4)], on_text_validate=self._on_search_pressed)
        self.search_field.bind(text=self._on_text_change)
        self.search_field.bind(focus=self._on_focus)

        self.clear_wrapper = MDCard(
            size_hint=(None, None), size=(dp(30), dp(30)), radius=[dp(15)],
            md_bg_color=[0, 0, 0, 0], elevation=0, pos_hint={'center_y': 0.5},
            opacity=0, disabled=True)

        self.clear_btn = MDIconButton(
            icon="close-circle-outline", size_hint=(1, 1), theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0], on_release=self._on_clear_pressed)
        self.clear_wrapper.add_widget(self.clear_btn)

        self.search_btn = MDRaisedButton(
            text="", size_hint=(None, None), size=(dp(64), dp(36)),
            text_color=[1, 1, 1, 1], font_size=sp(13), elevation=0,
            pos_hint={'center_y': 0.5})
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
        self.search_field.hint_text = get_text('search', 'Поиск')
        self.search_btn.text = get_text('find')

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = DictionaryColors.get_accent(theme_id)
        text_p = DictionaryColors.get_text_primary(theme_id)
        text_s = DictionaryColors.get_text_secondary(theme_id)
        line = DictionaryColors.get_card_line(theme_id)

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

        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if not text.strip():
            if self.on_clear:
                self.on_clear()
        else:
            self._search_timer = Clock.schedule_once(
                lambda dt: self._do_debounced_search(), self._DEBOUNCE_SEC)

    def _do_debounced_search(self):
        self._search_timer = None
        if self.on_search and self.current_query:
            t = self.current_query.strip()
            if t:
                self.on_search(t)

    def _on_search_pressed(self, *args):
        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None
        if self.on_search:
            t = self.search_field.text.strip()
            if t:
                self.on_search(t)

    def _on_clear_pressed(self, instance):
        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""
        if self.on_clear:
            self.on_clear()
        self.search_field.focus = False

    def _on_focus(self, instance, value):
        theme_id = settings_manager.theme
        base = 1.5 if theme_id in ('dark', 'light') else 1.4
        self.line_width = base + 0.3 if value else base

    def set_text(self, text):
        self.search_field.text = text or ""
        self._on_text_change(None, self.search_field.text)

    def clear(self):
        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None
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

        self.label = MDLabel(text=text.upper(), font_size=sp(16),
                             halign="center", valign="middle",
                             theme_text_color="Custom", bold=True,
                             size_hint=(1, 1))

        self.add_widget(self.label)
        self.bind(on_touch_down=self._on_touch_down)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)
        self._update_style()

    def _on_enter(self, *args):
        if not self.is_selected:
            self.md_bg_color = [1, 1, 1, 0.05]

    def _on_leave(self, *args):
        if not self.is_selected:
            self.md_bg_color = [0, 0, 0, 0]
            theme_id = settings_manager.theme
            self.label.text_color = DictionaryColors.get_text_secondary(theme_id)

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
        accent = DictionaryColors.get_accent(theme_id)
        if self.is_selected:
            self.md_bg_color = accent
            self.label.text_color = [1, 1, 1, 1]
            self.radius = [dp(8)]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = DictionaryColors.get_text_secondary(theme_id)
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

        container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 1))

        texture = None
        if flag_type == 'ru':
            texture = _shared_rus_flag_texture
        elif flag_type == 'en':
            texture = _shared_eng_flag_texture

        if texture:
            img = Image(
                texture=texture, size_hint=(None, None), size=(dp(22), dp(22)),
                allow_stretch=True, keep_ratio=True
            )
            container.add_widget(img)
        else:
            lbl = MDLabel(
                text="RU" if flag_type == 'ru' else "EN",
                font_size=sp(10), halign="center", valign="middle",
                theme_text_color="Custom", text_color=[1, 1, 1, 0.6], bold=True
            )
            container.add_widget(lbl)

        self.add_widget(container)


class AlphabetMenu(MDBoxLayout):
    RU_LETTERS = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и',
                  'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т',
                  'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь',
                  'э', 'ю', 'я']
    EN_LETTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                  'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                  'u', 'v', 'w', 'x', 'y', 'z']

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

        # ✅ В словаре показываем ТОЛЬКО выбранный алфавит (один)
        if user_lang == 'ru':
            groups = [('ru', self.RU_LETTERS, True)]
        else:
            groups = [('en', self.EN_LETTERS, True)]

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
        if self.current_language == language and self.buttons:
            return
        self.current_language = language
        self.current_selection = None
        self._populate_items()

    def set_current(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = DictionaryColors.get_accent(theme_id)
        self.left_arrow.icon_color = accent
        self.right_arrow.icon_color = accent
        for btn in self.buttons:
            btn._update_style()


class DictionaryMenu(MDCard):
    def __init__(self, on_letter_press=None, **kwargs):
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
            current_language=settings_manager.language
        )

        self.add_widget(self.alphabet_menu)
        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        self.md_bg_color = DictionaryColors.get_card_bg(theme_id)
        self.line_color = DictionaryColors.get_card_line(theme_id)
        self.line_width = 1.5 if theme_id in ('dark', 'light') else 0.8
        if self.alphabet_menu:
            self.alphabet_menu.update_theme_colors()

    def set_language(self, language):
        self.alphabet_menu.set_language(language)

    def set_current_letter(self, letter):
        self.alphabet_menu.set_current(letter)


# ============ RECYCLEVIEW ============

class SearchTermCard(RecycleDataViewBehavior, MDCard):
    term_name = StringProperty('')
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.padding = [dp(10), dp(4), dp(10), dp(4)]
        self.spacing = dp(8)
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self._build_ui()
        self.update_theme_colors()

    def _build_ui(self):
        self.icon = MDIconButton(icon="book-open-variant", size_hint=(None, None),
                                  size=(dp(28), dp(28)), theme_icon_color="Custom",
                                  md_bg_color=[0, 0, 0, 0], pos_hint={'center_y': 0.5})
        self.term_label = MDLabel(font_size=sp(15), theme_text_color="Custom",
                                   bold=True, shorten=True, shorten_from="right",
                                   valign="middle", size_hint_x=1)
        self.arrow = MDLabel(text="›", font_size=sp(22), size_hint_x=None,
                              width=dp(24), halign="center", valign="middle",
                              theme_text_color="Custom")
        self.add_widget(self.icon)
        self.add_widget(self.term_label)
        self.add_widget(self.arrow)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = DictionaryColors.get_accent(theme_id)
        self.md_bg_color = DictionaryColors.get_card_bg(theme_id)
        self.line_color = DictionaryColors.get_card_line(theme_id)
        self.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5
        self.icon.icon_color = accent
        self.term_label.text_color = DictionaryColors.get_text_primary(theme_id)
        self.arrow.text_color = accent

    def refresh_view_attrs(self, rv, index, data):
        self.term_name = data.get('term_name', '')
        self.on_click = data.get('on_click')
        self.term_label.text = self.term_name.capitalize()
        self.update_theme_colors()
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.term_name)
            return True
        return super().on_touch_down(touch)


Factory.register('SearchTermCard', cls=SearchTermCard)


class TermRecycleView(RecycleView):
    def __init__(self, on_term_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_term_click = on_term_click
        self.animate_scroll = False
        self.size_hint = (1, 1)
        self.clip = True
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)), default_size_hint=(1, None),
            size_hint_y=None, height=dp(48) * 50,
            orientation='vertical', spacing=dp(2))
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.viewclass = 'SearchTermCard'
        self.add_widget(self.layout_manager)

    def set_terms(self, terms, on_click):
        data = [{'term_name': t, 'on_click': on_click} for t in terms]
        self.data = data
        self.refresh_from_data()

    def clear(self):
        self.data = []
        self.refresh_from_data()

    def get_scroll_position(self):
        return self.scroll_y

    def set_scroll_position(self, position):
        if 0 <= position <= 1:
            self.scroll_y = position


# ============ ОСНОВНОЙ ЭКРАН ============

class DictionaryScreen(BaseScreen):
    RU_LETTERS = AlphabetMenu.RU_LETTERS
    EN_LETTERS = AlphabetMenu.EN_LETTERS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dictionary'
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None

        self.all_terms = {}
        self.terms_by_letter = {}
        self.current_letter = None
        self.is_search_mode = False
        self.search_results = []
        self._last_query = ""
        self.current_language = settings_manager.language
        self._saved_scroll_position = 1.0

        self.search_bar = None
        self._main_label = None
        self._result_label = None
        self.dictionary_menu = None
        self._hint_timer = None
        self.search_recycle_view = None

        load_shared_icons_sync()

        self.load_background()
        self.init_ui()
        self.scan_terms()

        logger.info('Экран словаря создан')

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
        if self.search_bar: self.search_bar.update_theme_colors()
        if self.dictionary_menu: self.dictionary_menu.update_theme_colors()
        if self._main_label:
            self._main_label.text_color = DictionaryColors.get_text_secondary(theme_id)
        if self._result_label:
            self._result_label.text_color = DictionaryColors.get_hint_color(theme_id)
        if self.search_recycle_view:
            for child in self.search_recycle_view.layout_manager.children:
                if hasattr(child, 'update_theme_colors'):
                    child.update_theme_colors()

    def update_language(self):
        if self.search_bar: self.search_bar.update_language()
        self._restore_hint()
        if self.dictionary_menu and self.dictionary_menu.alphabet_menu:
            self.dictionary_menu.alphabet_menu._populate_items()
        if self._result_label and self._result_label.opacity > 0:
            if self.is_search_mode:
                self._result_label.text = f"{get_text('found_terms')}: {len(self.search_results)}"
            elif self.current_letter:
                self._result_label.text = f"{get_text('terms_by_letter')} {self.current_letter.upper()}"

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))
        top_padding = layout_config.get_top_padding()
        padding = layout_config.get_content_padding()

        top_zone = MDBoxLayout(
            orientation='vertical', size_hint=(1, None),
            height=top_padding + dp(8) + dp(52) + dp(4) + dp(24) + dp(2) + dp(56) + dp(20),
            spacing=0)

        top_zone.add_widget(Widget(size_hint_y=None, height=top_padding))
        top_zone.add_widget(Widget(size_hint_y=None, height=dp(8)))

        search_container = MDBoxLayout(orientation='vertical', size_hint=(1, None),
                                        height=dp(52),
                                        padding=[padding[0], 0, padding[2], 0])
        self.search_bar = SearchBar(on_search=self.do_search, on_clear=self.clear_search)
        search_container.add_widget(self.search_bar)
        top_zone.add_widget(search_container)
        top_zone.add_widget(Widget(size_hint_y=None, height=dp(4)))

        self._main_label = MDLabel(
            text=get_text('search_by_alphabet'), font_size=sp(14), halign="center",
            size_hint_y=None, height=dp(24), theme_text_color="Custom")
        top_zone.add_widget(self._main_label)
        top_zone.add_widget(Widget(size_hint_y=None, height=dp(2)))

        menu_container = MDBoxLayout(orientation='vertical', size_hint=(1, None),
                                      height=dp(56), md_bg_color=[0, 0, 0, 0],
                                      padding=[padding[0], 0, padding[2], 0])
        self.dictionary_menu = DictionaryMenu(
            on_letter_press=self.on_letter_press
        )
        menu_container.add_widget(self.dictionary_menu)
        top_zone.add_widget(menu_container)

        self._result_label = MDLabel(
            text="", font_size=sp(13), halign="center",
            size_hint_y=None, height=dp(20),
            theme_text_color="Custom", opacity=0, bold=True)
        top_zone.add_widget(self._result_label)

        main_layout.add_widget(top_zone)

        bottom_padding = layout_config.get_bottom_padding()
        wrapper = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                              spacing=0, padding=[padding[0], dp(4), padding[2], bottom_padding])
        self.search_recycle_view = TermRecycleView(on_term_click=self.on_term_selected)
        wrapper.add_widget(self.search_recycle_view)
        main_layout.add_widget(wrapper)

        self.clear_widgets()
        self.add_widget(main_layout)

        self.update_theme_colors()

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
        else:
            self._main_label.text = get_text('search_by_alphabet')

    def _show_result_label(self, text):
        if self._result_label:
            self._result_label.text = text
            self._result_label.opacity = 1

    def _hide_result_label(self):
        if self._result_label:
            self._result_label.text = ""
            self._result_label.opacity = 0

    def _show_letter_terms(self, letter):
        terms = self.terms_by_letter.get(letter, [])
        if terms:
            self.search_recycle_view.set_terms(terms, self.on_term_selected)
            self._show_result_label(f"{get_text('terms_by_letter')} {letter.upper()}")
        else:
            self.search_recycle_view.clear()
            self._show_result_label(f"{get_text('no_terms_for_letter')} {letter.upper()}")

    def do_search(self, query):
        query_lower = query.strip().lower()
        self._last_query = query

        if len(query_lower) < 2:
            self._show_temporary_hint(get_text('min_chars'), 1.5)
            return

        self.is_search_mode = True
        self.current_letter = None
        self.dictionary_menu.set_current_letter(None)
        self._show_hint(get_text('search_results'))

        query_words = query_lower.split()
        exact, prefix, contains, word_m = [], [], [], []

        for term_name in self.all_terms:
            term_lower = term_name.lower()
            if term_lower == query_lower:
                if term_name not in exact: exact.append(term_name)
                continue
            if term_lower.startswith(query_lower):
                if term_name not in prefix: prefix.append(term_name)
                continue
            if query_lower in term_lower:
                if term_name not in contains: contains.append(term_name)
                continue
            for w in query_words:
                if len(w) >= 2 and w in term_lower:
                    if term_name not in word_m: word_m.append(term_name)
                    break

        results = []
        for lst in (exact, prefix, contains, word_m):
            for r in lst:
                if r not in results:
                    results.append(r)
        self.search_results = results

        if not self.search_results:
            self.search_recycle_view.clear()
            self._hide_result_label()
            self._show_hint(f'{get_text("nothing_found")}: "{query}"')
        else:
            self.search_recycle_view.set_terms(self.search_results, self.on_term_selected)
            self._show_result_label(f"{get_text('found_terms')}: {len(self.search_results)}")

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.clear()
        self.search_recycle_view.clear()
        self._last_query = ""
        self._hide_result_label()
        self.current_letter = None
        self.dictionary_menu.set_current_letter(None)
        self._show_hint(get_text('search_by_alphabet'))

    def on_letter_press(self, letter):
        self.save_current_state()
        self.current_letter = letter
        self.dictionary_menu.set_current_letter(letter)
        self.is_search_mode = False
        self.search_bar.clear()
        self._last_query = ""
        self._show_letter_terms(letter)

    def on_term_selected(self, term_name):
        term_data = self.all_terms.get(term_name)
        if not term_data:
            self._show_temporary_hint(get_text('term_not_found'), 1.5)
            return
        self.save_current_state()
        screen_state.set_previous_screen('dictionary')
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('term_detail'):
                term_detail = self.manager.get_screen('term_detail')
                term_detail.set_term(term_name, term_data, self.name)
                self.manager.current = 'term_detail'

    def scan_terms(self):
        self.all_terms.clear()
        self.terms_by_letter.clear()
        try:
            import dicts
            try:
                from dicts.ru import RU_TERMS_BY_LETTER, get_all_ru_terms
                ru_terms = get_all_ru_terms()
                for name, data in ru_terms.items():
                    self.all_terms[name] = data.to_dict() if hasattr(data, 'to_dict') else data
                for letter, terms in RU_TERMS_BY_LETTER.items():
                    if terms:
                        for t in terms:
                            first = self._get_first_letter(t)
                            if first:
                                self.terms_by_letter.setdefault(first, []).append(t)
            except ImportError as e:
                logger.error(f"Ошибка русских терминов: {e}")
            try:
                from dicts.en import EN_TERMS_BY_LETTER, get_all_en_terms
                en_terms = get_all_en_terms()
                for name, data in en_terms.items():
                    self.all_terms[name] = data.to_dict() if hasattr(data, 'to_dict') else data
                for letter, terms in EN_TERMS_BY_LETTER.items():
                    if terms:
                        for t in terms:
                            first = self._get_first_letter(t)
                            if first:
                                self.terms_by_letter.setdefault(first, []).append(t)
            except ImportError as e:
                logger.error(f"Ошибка английских терминов: {e}")
        except ImportError as e:
            logger.error(f"Пакет dicts не найден: {e}")
        self.all_terms = dict(sorted(self.all_terms.items()))
        for letter in self.terms_by_letter:
            self.terms_by_letter[letter].sort()

    def _get_first_letter(self, term_name):
        if not term_name: return None
        clean = term_name.lstrip('«»"\'')
        if not clean: return None
        c = clean[0].lower()
        if ('а' <= c <= 'я') or ('a' <= c <= 'z'):
            return c
        return None

    def save_current_state(self):
        scroll_position = 1.0
        if self.search_recycle_view:
            scroll_position = self.search_recycle_view.get_scroll_position()
        state = {
            'current_letter': self.current_letter,
            'is_search_mode': self.is_search_mode,
            'current_language': self.current_language,
            'search_query': self._last_query,
            'search_results': self.search_results[:50],
            'scroll_position': scroll_position,
        }
        screen_state.save_screen_state('dictionary', state)

    def restore_state(self):
        state = screen_state.get_screen_state('dictionary', max_age=300)
        if not state:
            return False
        try:
            self.current_letter = state.get('current_letter')
            self.is_search_mode = state.get('is_search_mode', False)
            self.current_language = state.get('current_language', 'ru')
            self._last_query = state.get('search_query', '')
            self.search_results = state.get('search_results', [])
            scroll_position = state.get('scroll_position', 1.0)

            if self.dictionary_menu:
                self.dictionary_menu.set_language(self.current_language)

            if self.is_search_mode and self.search_results:
                self.search_recycle_view.set_terms(self.search_results, self.on_term_selected)
                self._show_result_label(f"{get_text('found_terms')}: {len(self.search_results)}")
                if self._last_query:
                    self._show_hint(f"{get_text('search_results')}: {self._last_query}")
            elif self.current_letter:
                terms = self.terms_by_letter.get(self.current_letter, [])
                if terms:
                    self.search_recycle_view.set_terms(terms, self.on_term_selected)
                    self._show_result_label(f"{get_text('terms_by_letter')} {self.current_letter.upper()}")
                    if self.dictionary_menu:
                        self.dictionary_menu.set_current_letter(self.current_letter)
                else:
                    self.search_recycle_view.clear()
                    self._show_result_label(f"{get_text('no_terms_for_letter')} {self.current_letter.upper()}")
            else:
                self.search_recycle_view.clear()
                self._show_hint(get_text('search_by_alphabet'))
                self._hide_result_label()

            def restore_scroll(dt):
                if self.search_recycle_view:
                    self.search_recycle_view.set_scroll_position(scroll_position)
            Clock.schedule_once(restore_scroll, 0.1)
            Clock.schedule_once(restore_scroll, 0.2)
            Clock.schedule_once(restore_scroll, 0.3)
            return True
        except Exception as e:
            logger.error(f"Ошибка восстановления: {e}")
            return False

    def on_pre_leave(self):
        self.save_current_state()
        return super().on_pre_leave()

    def on_enter(self):
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title(get_text('dictionary'))
                app.top_nav.back_btn.on_release = self.go_back
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

        restored = self.restore_state()
        if not restored:
            self._show_hint(get_text('search_by_alphabet'))
            self._hide_result_label()
            self.search_recycle_view.clear()
            self.current_letter = None
            if self.dictionary_menu:
                self.dictionary_menu.set_current_letter(None)

    def on_leave(self):
        self.save_current_state()
        self.clear_search()
        self.current_letter = None
        if self.dictionary_menu:
            self.dictionary_menu.set_current_letter(None)
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'