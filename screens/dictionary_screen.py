# screens/dictionary_screen.py
"""
Экран словаря терминов.
Состояние — в state/dictionary_state.py.
Оформление — идентично songs_screen: обводки, падинги, шаг пагинации,
белые стрелки в green-теме.
Пагинация снизу — и для алфавита, и для поиска, с адаптивным шагом.
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
from kivymd.app import MDApp

from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivy.factory import Factory

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from utils.notifications import notify
from utils.screen_state import screen_state
from state.dictionary_state import dictionary_state
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
# ЦВЕТА
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
        return [1, 1, 1, 0.95]

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
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
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
                _shared_rus_flag_texture = CoreImage(BytesIO(rus_data), ext="png").texture
            eng_data = load_asset_as_bytes('eng_png')
            if eng_data:
                _shared_eng_flag_texture = CoreImage(BytesIO(eng_data), ext="png").texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконок: {e}")


# ============ ПОИСКОВАЯ СТРОКА ============

class SearchBar(MDCard):
    _DEBOUNCE_SEC = 0.5

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self._search_timer = None

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(16)] * 4
        self.elevation = 0
        self.padding = [dp(12), dp(4), dp(6), dp(4)]
        self.spacing = dp(6)
        self.theme_line_color = "Custom"
        self.theme_bg_color = "Custom"

        self.search_field = TextInput(
            multiline=False, size_hint_x=1, height=dp(40), font_size=sp(16),
            background_color=[1, 1, 1, 0], background_normal="", background_active="",
            padding=[0, dp(10), 0, dp(4)], on_text_validate=self._on_search_pressed)
        self.search_field.bind(text=self._on_text_change)
        self.search_field.bind(focus=self._on_focus)

        self.clear_wrapper = MDCard(
            size_hint=(None, None), size=(dp(30), dp(30)), radius=[dp(15)] * 4,
            md_bg_color=[0, 0, 0, 0], elevation=0, pos_hint={'center_y': 0.5},
            opacity=0, disabled=True)
        self.clear_btn = MDIconButton(
            icon="close-circle-outline", size_hint=(1, 1), theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0], on_release=self._on_clear_pressed, ripple_scale=0)
        self.clear_wrapper.add_widget(self.clear_btn)

        self.search_btn = MDRaisedButton(
            text="", size_hint=(None, None), size=(dp(64), dp(36)),
            text_color=[1, 1, 1, 1], font_size=sp(13), elevation=0,
            pos_hint={'center_y': 0.5})
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
        self.line_width = 5.0 if value else 4.0

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
        self.width = dp(32)
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]
        self.label = MDLabel(text=text.upper(), font_size=sp(15),
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
            self.label.text_color = DictionaryColors.get_text_secondary(settings_manager.theme)

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
                size=(dp(22), dp(22)), allow_stretch=True, keep_ratio=True))
        else:
            container.add_widget(MDLabel(
                text="RU" if flag_type == 'ru' else "EN",
                font_size=sp(10), halign="center", valign="middle",
                theme_text_color="Custom", text_color=[1, 1, 1, 0.6], bold=True))
        self.add_widget(container)


class AlphabetMenu(MDBoxLayout):
    RU_LETTERS = list('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    EN_LETTERS = list('abcdefghijklmnopqrstuvwxyz')

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
            on_release=lambda x: self.scroll(-1), ripple_scale=0)
        self.right_arrow = MDIconButton(
            icon="chevron-right", size_hint=(None, 1), width=dp(28),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll(1), ripple_scale=0)
        self.add_widget(self.left_arrow)

        self.scroll_view = ScrollView(
            size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False,
            bar_width=0, bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0], bar_margin=0)
        self.container = MDBoxLayout(
            orientation='horizontal', size_hint_x=None,
            spacing=dp(2), padding=[dp(4)] * 4)
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
        new_scroll = max(0, min(1, self.scroll_view.scroll_x + direction * 0.2))
        Animation(scroll_x=new_scroll, duration=0.2, t='out_quad').start(self.scroll_view)

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
        if theme_id == 'green':
            arrow_color = [1, 1, 1, 1]
        else:
            arrow_color = DictionaryColors.get_accent(theme_id)
        self.left_arrow.icon_color = arrow_color
        self.right_arrow.icon_color = arrow_color
        for btn in self.buttons:
            btn._update_style()


class DictionaryMenu(MDBoxLayout):
    def __init__(self, on_letter_press=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.md_bg_color = [0, 0, 0, 0]
        self.alphabet_menu = AlphabetMenu(
            on_letter_press=on_letter_press,
            current_language=settings_manager.language)
        self.add_widget(self.alphabet_menu)

    def update_theme_colors(self):
        if self.alphabet_menu:
            self.alphabet_menu.update_theme_colors()

    def set_language(self, language):
        self.alphabet_menu.set_language(language)

    def set_current_letter(self, letter):
        self.alphabet_menu.set_current(letter)


# ============ ПАГИНАЦИЯ ============

class PageButton(ButtonBehavior, MDBoxLayout):
    def __init__(self, text, index, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = dp(48)
        self.md_bg_color = [0, 0, 0, 0]
        self.is_selected = False
        self.page_index = index
        self.on_click_callback = on_click
        self.label = MDLabel(
            text=text, font_size=sp(14), halign="center", valign="middle",
            theme_text_color="Custom", text_color=[1, 1, 1, 0.7],
            bold=True, size_hint=(None, 1), width=dp(44),
            pos_hint={'center_x': 0.5})
        self.add_widget(self.label)
        self.bind(on_release=self._on_release)

    def _on_release(self, *args):
        if self.on_click_callback:
            self.on_click_callback(self.page_index)

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        theme_id = settings_manager.theme
        accent = DictionaryColors.get_accent(theme_id)
        text_s = DictionaryColors.get_text_secondary(theme_id)
        if self.is_selected:
            self.md_bg_color = accent
            self.label.text_color = [1, 1, 1, 1]
            self.radius = [dp(8)]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = text_s
            self.radius = [0]


class PaginationBar(MDBoxLayout):
    CENTERED_MAX_BUTTONS = 6

    def __init__(self, on_page_select=None, **kwargs):
        super().__init__(**kwargs)
        self.on_page_select = on_page_select
        self.current_page_index = 0
        self.total_pages = 1
        self._last_total = None
        self._last_per_page = None
        self.page_buttons = []
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.spacing = dp(2)
        self.md_bg_color = [0, 0, 0, 0]
        self.padding = [dp(4), dp(2), dp(4), dp(2)]

        self.left_arrow = MDIconButton(
            icon="chevron-left", size_hint=(None, 1), width=dp(32),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll_strip(-1), ripple_scale=0)
        self.right_arrow = MDIconButton(
            icon="chevron-right", size_hint=(None, 1), width=dp(32),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll_strip(1), ripple_scale=0)
        self.add_widget(self.left_arrow)

        self.center_zone = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1), md_bg_color=[0, 0, 0, 0])
        self.add_widget(self.center_zone)
        self.add_widget(self.right_arrow)

        self.container = MDBoxLayout(
            orientation='horizontal', size_hint=(None, 1),
            spacing=dp(4), padding=[dp(4)] * 4, md_bg_color=[0, 0, 0, 0])
        self.scroll_view = None
        self._centered_mode = None
        self.update_theme_colors()

    def _rebuild_center_zone(self, force_center):
        if self._centered_mode == force_center and self.center_zone.children:
            return
        self._centered_mode = force_center
        if self.container.parent:
            self.container.parent.remove_widget(self.container)
        self.center_zone.clear_widgets()
        self.scroll_view = None
        if force_center:
            anchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 1))
            self.container.size_hint = (None, 1)
            self.container.pos_hint = {}
            anchor.add_widget(self.container)
            self.center_zone.add_widget(anchor)
        else:
            self.container.size_hint = (None, 1)
            self.container.pos_hint = {}
            self.scroll_view = ScrollView(
                size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False,
                bar_width=0, bar_color=[0, 0, 0, 0],
                bar_inactive_color=[0, 0, 0, 0], bar_margin=0)
            self.scroll_view.add_widget(self.container)
            self.center_zone.add_widget(self.scroll_view)

    def _apply_layout_mode(self):
        n = len(self.page_buttons)
        if n == 0:
            return
        self._rebuild_center_zone(n <= self.CENTERED_MAX_BUTTONS)

    def set_total(self, total_items, per_page, current_page=0, on_click=None):
        if on_click:
            self.on_page_select = on_click
        if self._last_total == total_items and self._last_per_page == per_page:
            self.set_current_page(current_page)
            return
        self._last_total = total_items
        self._last_per_page = per_page
        self.container.clear_widgets()
        self.page_buttons = []
        self.total_pages = max(1, (total_items + per_page - 1) // per_page)
        self.current_page_index = current_page
        if self.total_pages <= 1:
            self._rebuild_center_zone(True)
            self.container.width = 0
            self.update_theme_colors()
            return
        for i in range(self.total_pages):
            count = min((i + 1) * per_page, total_items)
            btn = PageButton(text=str(count), index=i, on_click=self._on_page_click)
            self.page_buttons.append(btn)
            self.container.add_widget(btn)
        content_w = (
            sum(b.width for b in self.page_buttons)
            + max(0, len(self.page_buttons) - 1) * self.container.spacing
            + self.container.padding[0] + self.container.padding[2])
        self.container.width = content_w
        self._apply_layout_mode()
        self.update_theme_colors()
        Clock.schedule_once(lambda dt: self._scroll_to_current(force=True), 0.1)

    def set_current_page(self, page):
        if not self.page_buttons:
            self.current_page_index = page
            return
        if page == self.current_page_index:
            for i, btn in enumerate(self.page_buttons):
                btn.set_selected(i == page)
            return
        self.current_page_index = page
        for i, btn in enumerate(self.page_buttons):
            btn.set_selected(i == page)
        if self._centered_mode is False and self.scroll_view:
            Clock.schedule_once(lambda dt: self._scroll_to_current(force=False), 0.05)

    def _on_page_click(self, index):
        if index == self.current_page_index:
            return
        self.current_page_index = index
        for i, btn in enumerate(self.page_buttons):
            btn.set_selected(i == index)
        if self.on_page_select:
            self.on_page_select(index)

    def scroll_strip(self, direction):
        if not self.scroll_view:
            return
        new_scroll = max(0, min(1, self.scroll_view.scroll_x + direction * 0.2))
        Animation(scroll_x=new_scroll, duration=0.2, t='out_quad').start(self.scroll_view)

    def _scroll_to_current(self, force=False):
        if self._centered_mode is not False:
            return
        if not self.scroll_view or not self.page_buttons:
            return
        idx = min(self.current_page_index, len(self.page_buttons) - 1)
        btn = self.page_buttons[idx]
        if btn.width <= 0:
            return
        total_width = self.container.width - self.scroll_view.width
        if total_width <= 0:
            return
        if not force:
            viewport_w = self.scroll_view.width
            content_w = self.container.width
            if content_w > 0 and viewport_w > 0:
                current_left = self.scroll_view.scroll_x * max(0, content_w - viewport_w)
                current_right = current_left + viewport_w
                if current_left <= btn.x and btn.x + btn.width <= current_right:
                    return
        scroll_x = max(0, min(1, (btn.x - dp(4)) / total_width))
        Animation(scroll_x=scroll_x, duration=0.2, t='out_quad').start(self.scroll_view)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        if theme_id == 'green':
            arrow_color = [1, 1, 1, 1]
        else:
            arrow_color = DictionaryColors.get_accent(theme_id)
        self.left_arrow.icon_color = arrow_color
        self.right_arrow.icon_color = arrow_color
        for i, btn in enumerate(self.page_buttons):
            btn.set_selected(i == self.current_page_index)

    def on_size(self, *args):
        if not getattr(self, 'page_buttons', None):
            return
        if not getattr(self, 'container', None) or not getattr(self, 'center_zone', None):
            return
        Clock.schedule_once(lambda dt: self._apply_layout_mode(), 0.05)


# ============ КАРТОЧКА ТЕРМИНА ============

class SearchTermCard(RecycleDataViewBehavior, MDCard):
    term_name = StringProperty('')
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self.theme_line_color = "Custom"
        self.theme_bg_color = "Custom"
        self.padding = [0, dp(4), 0, dp(4)]
        self.spacing = dp(8)
        self._build_ui()
        self.update_theme_colors()

    def _build_ui(self):
        content = MDBoxLayout(
            orientation='horizontal',
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0])
        self.icon = MDIconButton(
            icon="book-open-variant", size_hint=(None, None),
            size=(dp(24), dp(24)), theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0], pos_hint={'center_y': 0.5},
            ripple_scale=0)
        self.term_label = MDLabel(
            font_size=sp(15), theme_text_color="Custom", bold=True,
            shorten=True, shorten_from="right", valign="middle", size_hint_x=1)
        self.arrow = MDLabel(
            text="›", font_size=sp(20), size_hint_x=None, width=dp(20),
            halign="center", valign="middle", theme_text_color="Custom")
        content.add_widget(self.icon)
        content.add_widget(self.term_label)
        content.add_widget(self.arrow)
        self.add_widget(content)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = DictionaryColors.get_accent(theme_id)
        self.md_bg_color = DictionaryColors.get_card_bg(theme_id)
        self.line_color = DictionaryColors.get_card_line(theme_id)
        self.line_width = DictionaryColors.get_card_line_width(theme_id)
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
        self.scroll_type = ['bars', 'content']
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)), default_size_hint=(1, None),
            size_hint_y=None, height=dp(48) * 50,
            orientation='vertical', spacing=dp(6),
            padding=[dp(4), dp(8), dp(4), dp(8)])
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.viewclass = 'SearchTermCard'
        self.add_widget(self.layout_manager)

    def set_terms(self, terms, on_click):
        self.data = [{'term_name': t, 'on_click': on_click} for t in terms]
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

        # Пагинация алфавита
        self._page = 0
        self._total_terms = 0
        self._page_terms = []

        # Пагинация поиска
        self._search_page = 0
        self._search_page_size_default = 10  # fallback

        # Оптимизация
        self._last_display_key = None
        self._last_search_display_key = None

        self.search_bar = None
        self._main_label = None
        self._result_label = None
        self.dictionary_menu = None
        self._hint_timer = None
        self.search_recycle_view = None
        self._pagination_bar = None
        self._search_pagination_bar = None

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
                    self.texture = CoreImage(BytesIO(bg_data), ext="jpg").texture
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
        if self.search_bar:
            self.search_bar.update_theme_colors()
        if self.dictionary_menu:
            self.dictionary_menu.update_theme_colors()
        if self._pagination_bar:
            self._pagination_bar.update_theme_colors()
        if self._search_pagination_bar:
            self._search_pagination_bar.update_theme_colors()
        if self._main_label:
            self._main_label.text_color = DictionaryColors.get_text_secondary(theme_id)
        if self._result_label:
            self._result_label.text_color = DictionaryColors.get_hint_color(theme_id)
        if self.search_recycle_view:
            for child in self.search_recycle_view.layout_manager.children:
                if hasattr(child, 'update_theme_colors'):
                    child.update_theme_colors()

    def update_language(self):
        if self.search_bar:
            self.search_bar.update_language()
        self._restore_hint()
        if self.dictionary_menu and self.dictionary_menu.alphabet_menu:
            self.dictionary_menu.alphabet_menu._populate_items()
        if self._result_label and self._result_label.opacity > 0:
            if self.is_search_mode:
                self._update_search_result_label()
            elif self.current_letter:
                self._update_result_label_for_letter()

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))
        self._main_layout = main_layout

        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        padding = layout_config.get_content_padding()

        # 1. Поиск
        search_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(52),
            padding=[padding[0], 0, padding[2], 0])
        self.search_bar = SearchBar(on_search=self.do_search, on_clear=self.clear_search)
        search_container.add_widget(self.search_bar)
        main_layout.add_widget(search_container)
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # 2. Top section (лейбл + меню алфавита)
        top_section = MDBoxLayout(
            orientation='vertical', size_hint_y=None, height=dp(80))
        self._main_label = MDLabel(
            text=get_text('search_by_alphabet'), font_size=sp(14), halign="center",
            size_hint_y=None, height=dp(24), theme_text_color="Custom")
        top_section.add_widget(self._main_label)

        menu_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=dp(56),
            md_bg_color=[0, 0, 0, 0], padding=[padding[0], 0, padding[2], 0])
        self.dictionary_menu = DictionaryMenu(on_letter_press=self.on_letter_press)
        menu_container.add_widget(self.dictionary_menu)
        top_section.add_widget(menu_container)
        main_layout.add_widget(top_section)

        # 3. Result label
        self._result_label = MDLabel(
            text="", font_size=sp(13), halign="center",
            size_hint_y=None, height=dp(20),
            theme_text_color="Custom",
            text_color=DictionaryColors.get_hint_color(settings_manager.theme),
            opacity=0, bold=True)
        main_layout.add_widget(self._result_label)

        # 4. Список
        wrapper = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            spacing=0, padding=[padding[0], dp(4), padding[2], dp(0)],
            md_bg_color=[0, 0, 0, 0])
        self.search_recycle_view = TermRecycleView(on_term_click=self.on_term_selected)
        wrapper.add_widget(self.search_recycle_view)
        main_layout.add_widget(wrapper)

        # 5. Пагинация алфавита
        self._pagination_bar = PaginationBar(
            on_page_select=self._on_page_selected_from_bar)
        self._pagination_bar.height = 0
        self._pagination_bar.opacity = 0
        self._pagination_bar.disabled = True
        main_layout.add_widget(self._pagination_bar)

        # 6. Пагинация поиска
        self._search_pagination_bar = PaginationBar(
            on_page_select=self._on_search_page_selected)
        self._search_pagination_bar.height = 0
        self._search_pagination_bar.opacity = 0
        self._search_pagination_bar.disabled = True
        main_layout.add_widget(self._search_pagination_bar)

        # 7. Отступ под BottomNav
        bottom_padding = layout_config.get_bottom_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))

        self.clear_widgets()
        self.add_widget(main_layout)
        self.update_theme_colors()

    # ============ АДАПТИВНЫЙ ШАГ ============

    def _get_page_size(self):
        """Адаптивный шаг для алфавита."""
        total = self._total_terms
        if total <= 100:
            return 10
        elif total <= 300:
            return 25
        else:
            return 50

    def _get_search_page_size(self):
        """Адаптивный шаг для поиска."""
        total = len(self.search_results)
        if total <= 100:
            return 10
        elif total <= 300:
            return 25
        else:
            return 50

    def _ensure_valid_page(self):
        page_size = self._get_page_size()
        if self._total_terms <= 0:
            self._page = 0
            return
        max_page = (self._total_terms - 1) // page_size
        if self._page > max_page:
            self._page = max_page

    def _ensure_valid_search_page(self):
        page_size = self._get_search_page_size()
        total = len(self.search_results)
        if total <= 0:
            self._search_page = 0
            return
        max_page = (total - 1) // page_size
        if self._search_page > max_page:
            self._search_page = max_page

    # ============ ПОИСК / АЛФАВИТ ============

    def _show_hint(self, text):
        if self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None
        if self._main_label:
            self._main_label.text = text

    def _show_temporary_hint(self, text, duration=1.5):
        if self._main_label:
            self._main_label.text = text
            if self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._restore_hint(), duration)

    def _restore_hint(self):
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

    def _update_result_label_for_letter(self):
        if self.current_letter:
            page_size = self._get_page_size()
            if self._total_terms > page_size:
                current_count = min((self._page + 1) * page_size, self._total_terms)
                self._show_result_label(
                    f"{get_text('terms_by_letter')} {self.current_letter.upper()}: "
                    f"{current_count} {get_text('of')} {self._total_terms}")
            else:
                self._show_result_label(
                    f"{get_text('terms_by_letter')} {self.current_letter.upper()}")

    def _update_search_result_label(self):
        if not self.search_results:
            self._hide_result_label()
            return
        page_size = self._get_search_page_size()
        total = len(self.search_results)
        if total > page_size:
            start = self._search_page * page_size
            end = min(start + page_size, total)
            current = end - start
            self._show_result_label(
                f"{get_text('found_terms')}: {current} {get_text('of')} {total}")
        else:
            self._show_result_label(
                f"{get_text('found_terms')}: {total}")

    # ============ ПАГИНАЦИЯ АЛФАВИТА ============

    def _hide_pagination(self):
        if not self._pagination_bar:
            return
        self._pagination_bar.height = 0
        self._pagination_bar.opacity = 0
        self._pagination_bar.disabled = True

    def _show_pagination_bar(self):
        if not self._pagination_bar:
            return
        page_size = self._get_page_size()
        if self._total_terms <= page_size:
            self._hide_pagination()
            return
        self._pagination_bar.height = dp(48)
        self._pagination_bar.opacity = 1
        self._pagination_bar.disabled = False
        self._pagination_bar.set_total(self._total_terms, page_size, self._page)

    def _on_page_selected_from_bar(self, page_index):
        if page_index == self._page:
            return
        self._page = page_index
        self._display_letter_page()

    def _display_letter_page(self):
        if not self.current_letter:
            return
        terms = self.terms_by_letter.get(self.current_letter, [])
        self._total_terms = len(terms)
        self._ensure_valid_page()
        page_size = self._get_page_size()
        start = self._page * page_size
        end = min(start + page_size, self._total_terms)
        page_terms = terms[start:end]
        self._page_terms = page_terms
        if page_terms:
            self._set_terms_view(page_terms)
            self._update_result_label_for_letter()
        else:
            self.search_recycle_view.clear()
            self._show_result_label(
                f"{get_text('no_terms_for_letter')} {self.current_letter.upper()}")
        if self._total_terms > page_size:
            self._show_pagination_bar()
        else:
            self._hide_pagination()

    def _show_letter_terms(self, letter):
        self.current_letter = letter
        self._page = 0
        terms = self.terms_by_letter.get(letter, [])
        self._total_terms = len(terms)
        self._ensure_valid_page()
        if terms:
            self._display_letter_page()
        else:
            self.search_recycle_view.clear()
            self._page_terms = []
            self._show_result_label(
                f"{get_text('no_terms_for_letter')} {letter.upper()}")
            self._hide_pagination()

    def _set_terms_view(self, terms):
        first = terms[0] if terms else ''
        display_key = ('letter', self.current_letter, self._page, len(terms), first)
        if self._last_display_key != display_key:
            self.search_recycle_view.set_terms(terms, self.on_term_selected)
            self._last_display_key = display_key
            Clock.schedule_once(
                lambda dt: setattr(self.search_recycle_view, 'scroll_y', 1.0), 0.1)

    # ============ ПАГИНАЦИЯ ПОИСКА ============

    def _hide_search_pagination(self):
        if not self._search_pagination_bar:
            return
        self._search_pagination_bar.height = 0
        self._search_pagination_bar.opacity = 0
        self._search_pagination_bar.disabled = True

    def _show_search_pagination_bar(self):
        if not self._search_pagination_bar:
            return
        page_size = self._get_search_page_size()
        total = len(self.search_results)
        if total <= page_size:
            self._hide_search_pagination()
            return
        self._search_pagination_bar.height = dp(48)
        self._search_pagination_bar.opacity = 1
        self._search_pagination_bar.disabled = False
        self._search_pagination_bar.set_total(total, page_size, self._search_page)

    def _on_search_page_selected(self, page_index):
        if page_index == self._search_page:
            return
        self._show_search_page(page_index)

    def _show_search_page(self, page_idx):
        if not self.search_results:
            self._hide_search_pagination()
            return
        self._search_page = page_idx
        self._ensure_valid_search_page()
        page_size = self._get_search_page_size()
        start = self._search_page * page_size
        end = min(start + page_size, len(self.search_results))
        page_slice = self.search_results[start:end]

        first = page_slice[0] if page_slice else ''
        display_key = ('search', self._search_page, len(page_slice), first)
        if self._last_search_display_key != display_key:
            self.search_recycle_view.set_terms(page_slice, self.on_term_selected)
            self._last_search_display_key = display_key
            Clock.schedule_once(
                lambda dt: setattr(self.search_recycle_view, 'scroll_y', 1.0), 0.1)

        self._update_search_result_label()

        if len(self.search_results) > page_size:
            self._show_search_pagination_bar()
        else:
            self._hide_search_pagination()

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
        self._hide_pagination()

        query_words = query_lower.split()
        exact, prefix, contains, word_m = [], [], [], []

        for term_name in self.all_terms:
            term_lower = term_name.lower()
            if term_lower == query_lower:
                if term_name not in exact:
                    exact.append(term_name)
                continue
            if term_lower.startswith(query_lower):
                if term_name not in prefix:
                    prefix.append(term_name)
                continue
            if query_lower in term_lower:
                if term_name not in contains:
                    contains.append(term_name)
                continue
            for w in query_words:
                if len(w) >= 2 and w in term_lower:
                    if term_name not in word_m:
                        word_m.append(term_name)
                    break

        results = []
        for lst in (exact, prefix, contains, word_m):
            for r in lst:
                if r not in results:
                    results.append(r)
        self.search_results = results
        self._search_page = 0
        self._last_search_display_key = None

        if not self.search_results:
            self.search_recycle_view.clear()
            self._last_display_key = None
            self._hide_result_label()
            self._hide_search_pagination()
            self._show_hint(f'{get_text("nothing_found")}: "{query}"')
        else:
            self._show_search_page(0)

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self._search_page = 0
        self.search_bar.clear()
        self.search_recycle_view.clear()
        self._last_query = ""
        self._last_display_key = None
        self._last_search_display_key = None
        self._hide_result_label()
        self._hide_pagination()
        self._hide_search_pagination()
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
        self._last_display_key = None
        self._last_search_display_key = None
        self._hide_search_pagination()
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
        if not term_name:
            return None
        clean = term_name.lstrip('«»"\'')
        if not clean:
            return None
        c = clean[0].lower()
        if ('а' <= c <= 'я') or ('a' <= c <= 'z'):
            return c
        return None

    # ============ СОСТОЯНИЕ ============

    def save_current_state(self):
        scroll = 1.0
        if self.search_recycle_view:
            scroll = self.search_recycle_view.get_scroll_position()
        dictionary_state.save({
            'current_letter': self.current_letter,
            'is_search_mode': self.is_search_mode,
            'current_language': self.current_language,
            'query': self._last_query,
            'page': self._page,
            'search_page': self._search_page,
            'total_terms': self._total_terms,
            'scroll_position': scroll,
        })

    def restore_state(self):
        saved = dictionary_state.get(allow_stale=True)
        if not saved:
            return False
        try:
            self.current_letter = saved.get('current_letter')
            self.is_search_mode = saved.get('is_search_mode', False)
            self.current_language = saved.get('current_language', 'ru')
            self._last_query = saved.get('query', '')
            self._page = saved.get('page', 0)
            self._search_page = saved.get('search_page', 0)
            self._total_terms = saved.get('total_terms', 0)
            scroll = saved.get('scroll_position', 1.0)
            self._last_display_key = None
            self._last_search_display_key = None

            if self.dictionary_menu:
                self.dictionary_menu.set_language(self.current_language)

            if self.is_search_mode and self._last_query:
                self.search_bar.set_text(self._last_query)
                self.is_search_mode = True
                self._hide_pagination()
                # Восстанавливаем query и страницу, но результаты в памяти — если есть
                if self.search_results:
                    self._show_search_page(self._search_page)
                else:
                    self._hide_search_pagination()
                    self._show_hint(get_text('search_results'))
            elif self.current_letter:
                self.dictionary_menu.set_current_letter(self.current_letter)
                terms = self.terms_by_letter.get(self.current_letter, [])
                self._total_terms = len(terms)
                self._ensure_valid_page()
                self._display_letter_page()
            else:
                self.search_recycle_view.clear()
                self._show_hint(get_text('search_by_alphabet'))
                self._hide_result_label()
                self._hide_pagination()
                self._hide_search_pagination()

            def restore_scroll(dt):
                if self.search_recycle_view:
                    self.search_recycle_view.set_scroll_position(scroll)

            Clock.schedule_once(restore_scroll, 0.1)
            Clock.schedule_once(restore_scroll, 0.2)
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

        if self._last_display_key is not None and not self.is_search_mode:
            self._update_result_label_for_letter()
            return

        restored = self.restore_state()
        if not restored:
            self._show_hint(get_text('search_by_alphabet'))
            self._hide_result_label()
            self.search_recycle_view.clear()
            self.current_letter = None
            self._last_display_key = None
            if self.dictionary_menu:
                self.dictionary_menu.set_current_letter(None)

    def on_leave(self):
        self.save_current_state()
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'