# screens/search_screen.py
"""
Экран поиска (аккорды, песни и термины).
Адаптирован под 3 темы и 6 языков.
"""
import threading
import traceback
import time
import re
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from io import BytesIO
from threading import Thread

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('SearchScreen')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА ДЛЯ ПОИСКА
# ============================================================

class SearchColors:
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
            return [1, 1, 1, 0.5]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.08]
        else:
            return [0, 0, 0, 0.08]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        else:
            return [1, 1, 1, 0.08]

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        else:
            return [1, 1, 1, 0.5]


# ============ ПОИСКОВАЯ СТРОКА ============

class SearchBar(MDCard):
    def __init__(self, on_search=None, on_clear=None, on_text_change=None,
                 hint_text=None, button_text=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.on_text_change = on_text_change
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
        self.search_btn.text = get_text('find', 'Найти')

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = SearchColors.get_accent(theme_id)
        text_p = SearchColors.get_text_primary(theme_id)
        text_s = SearchColors.get_text_secondary(theme_id)
        line = SearchColors.get_card_line(theme_id)

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
        if self.on_text_change:
            self.on_text_change(text)

    def _on_search_pressed(self, *args):
        if self.on_search:
            t = self.search_field.text.strip()
            if t:
                self.on_search(t)

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
        base = 1.5 if theme_id in ('dark', 'light') else 1.4
        self.line_width = base + 0.3 if value else base

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


# ============ КАРТОЧКА РЕЗУЛЬТАТА ============

class ResultCard(MDCard):
    def __init__(self, title, result_type, subtitle, song_id=None,
                 chord_name=None, term_name=None, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.result_type = result_type
        self.subtitle = subtitle
        self.song_id = song_id
        self.chord_name = chord_name
        self.term_name = term_name
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.spacing = dp(10)
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True

        self._build_ui()
        self.update_theme_colors()

    def _build_ui(self):
        self.icon_image = Image(size_hint=(None, None), size=(dp(28), dp(28)),
                                 pos_hint={'center_y': 0.5}, allow_stretch=True, keep_ratio=True)
        self._load_icon()

        text_layout = MDBoxLayout(orientation='vertical', size_hint_x=1,
                                   spacing=dp(2), pos_hint={'center_y': 0.5})

        self.title_label = MDLabel(
            text=self.title, font_size=sp(15), size_hint_y=None, height=dp(24),
            theme_text_color="Custom", bold=True, valign="middle",
            shorten=True, shorten_from="right")
        self.subtitle_label = MDLabel(
            text=self.subtitle, font_size=sp(11), size_hint_y=None, height=dp(18),
            theme_text_color="Custom", valign="middle",
            shorten=True, shorten_from="right")

        text_layout.add_widget(self.title_label)
        text_layout.add_widget(self.subtitle_label)

        self.arrow = MDLabel(text="›", font_size=sp(24), size_hint_x=None,
                              width=dp(28), halign="center", theme_text_color="Custom")

        self.add_widget(self.icon_image)
        self.add_widget(text_layout)
        self.add_widget(self.arrow)

        self.bind(on_release=self._on_click)

    def _load_icon(self):
        icon_name = 'song_png'
        if self.result_type == 'chord':
            icon_name = 'chord_png'
        elif self.result_type == 'term':
            icon_name = 'dictionary_png'

        if HAS_ASSETS:
            try:
                data = load_asset_as_bytes(icon_name)
                if data:
                    img = CoreImage(BytesIO(data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        if self.result_type == 'chord':
            self.icon_image.text = "🎸"
        elif self.result_type == 'term':
            self.icon_image.text = "📖"
        else:
            self.icon_image.text = "🎵"

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = SearchColors.get_accent(theme_id)
        self.md_bg_color = SearchColors.get_card_bg(theme_id)
        self.line_color = SearchColors.get_card_line(theme_id)
        self.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5
        self.title_label.text_color = SearchColors.get_text_primary(theme_id)
        self.subtitle_label.text_color = SearchColors.get_text_secondary(theme_id)
        self.arrow.text_color = accent

    def _on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.result_type, self.chord_name, self.song_id, self.term_name)


# ============ ОСНОВНОЙ ЭКРАН ============

class SearchScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search'
        self.chords_screen = None
        self.dictionary_screen = None
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self._search_thread = None
        self._is_searching = False
        self.current_query = ""

        self._saved_scroll_position = 1.0
        self._is_restoring = False
        self._last_results = []
        self._state_restored = False
        self._block_transition = False

        self.load_background()
        self.init_ui()
        logger.info('Экран поиска создан')

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
        if hasattr(self, 'search_bar'): self.search_bar.update_theme_colors()
        if hasattr(self, 'title_label'):
            self.title_label.text_color = SearchColors.get_hint_color(theme_id)
        if hasattr(self, 'results_list'):
            for child in self.results_list.children:
                if hasattr(child, 'update_theme_colors'):
                    child.update_theme_colors()
                elif isinstance(child, MDLabel):
                    child.text_color = SearchColors.get_text_primary(theme_id)

    def update_language(self):
        if self.search_bar: self.search_bar.update_language()
        if hasattr(self, 'title_label'):
            self.title_label.text = get_text('what_to_search', 'Что будем искать?')
        # Перерисовываем заголовки групп, если есть результаты
        if self._last_results:
            self._redraw_results()

    def set_chords_screen(self, chords_screen):
        self.chords_screen = chords_screen

    def set_dictionary_screen(self, dictionary_screen):
        self.dictionary_screen = dictionary_screen

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        main_layout.add_widget(Widget(size_hint_y=None, height=layout_config.get_top_padding()))
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(16)))

        self.title_label = MDLabel(
            text=get_text('what_to_search', 'Что будем искать?'),
            font_size=sp(16), halign="center",
            size_hint_y=None, height=dp(36),
            theme_text_color="Custom", bold=True)
        main_layout.add_widget(self.title_label)
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        search_container = MDBoxLayout(orientation='vertical', size_hint=(1, None),
                                        height=dp(52), padding=[dp(16), 0, dp(16), 0])
        self.search_bar = SearchBar(
            on_search=self.perform_search, on_clear=self.clear_search,
            on_text_change=self.on_text_changed)
        search_container.add_widget(self.search_bar)
        main_layout.add_widget(search_container)
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        bottom_padding = layout_config.get_bottom_padding()
        cards_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                                       padding=[dp(12), dp(8), dp(12), bottom_padding])
        cards_container.clip = True

        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False,
                                  bar_width=0, bar_color=[0, 0, 0, 0],
                                  bar_inactive_color=[0, 0, 0, 0])
        self.scroll.clip = True

        self.results_list = MDBoxLayout(orientation='vertical', spacing=dp(8),
                                         size_hint_y=None, adaptive_height=True)
        self.results_list.bind(minimum_height=self.results_list.setter('height'))

        self.scroll.add_widget(self.results_list)
        cards_container.add_widget(self.scroll)
        main_layout.add_widget(cards_container)

        self.add_widget(main_layout)
        self.update_theme_colors()

    def _redraw_results(self):
        """Перерисовка результатов при смене языка (заголовки групп)."""
        self.results_list.clear_widgets()
        self._show_results(
            self.current_query,
            [r for r in self._last_results if r.get('result_type') == 'chord'],
            [r for r in self._last_results if r.get('result_type') == 'song'],
            [r.get('term_name', '') for r in self._last_results if r.get('result_type') == 'term'],
            force_redraw=True)

    # ============ СОХРАНЕНИЕ / ВОССТАНОВЛЕНИЕ ============

    def save_current_state(self):
        if self._block_transition:
            return
        scroll_position = 1.0
        if hasattr(self, 'scroll') and self.scroll:
            scroll_position = self.scroll.scroll_y
        results_data = []
        for child in self.results_list.children:
            if isinstance(child, ResultCard):
                results_data.append({
                    'title': child.title,
                    'result_type': child.result_type,
                    'subtitle': child.subtitle,
                    'song_id': child.song_id,
                    'chord_name': child.chord_name,
                    'term_name': child.term_name,
                })
        state = {
            'current_query': self.current_query,
            'results': results_data,
            'scroll_position': scroll_position,
            'has_results': len(results_data) > 0,
        }
        screen_state.save_screen_state('search', state)

    def restore_state(self):
        if self._block_transition or self._state_restored:
            return self._state_restored

        state = screen_state.get_screen_state('search', max_age=300)
        if not state:
            return False
        try:
            self._is_restoring = True
            current_query = state.get('current_query', '')
            results_data = state.get('results', [])
            scroll_position = state.get('scroll_position', 1.0)

            if current_query and self.search_bar:
                self.search_bar.set_text(current_query)
                self.current_query = current_query

            if results_data:
                self._last_results = results_data
                self._show_restored_results(results_data)
                def restore_scroll(dt):
                    if hasattr(self, 'scroll') and self.scroll:
                        self.scroll.scroll_y = scroll_position
                Clock.schedule_once(restore_scroll, 0.1)
            else:
                self.results_list.clear_widgets()
                self.title_label.opacity = 1

            self._state_restored = True
            self._is_restoring = False
            return True
        except Exception as e:
            logger.error(f"Ошибка восстановления: {e}")
            self._is_restoring = False
            return False

    def _show_restored_results(self, results_data):
        self.results_list.clear_widgets()
        self.title_label.opacity = 0
        chords = [i for i in results_data if i.get('result_type') == 'chord']
        songs = [i for i in results_data if i.get('result_type') == 'song']
        terms = [i for i in results_data if i.get('result_type') == 'term']

        if chords:
            self.results_list.add_widget(self._group_header(get_text('found_chords', 'Найденные аккорды')))
            for item in chords:
                self.results_list.add_widget(ResultCard(
                    title=item.get('title', ''),
                    result_type="chord",
                    subtitle=item.get('subtitle', ''),
                    chord_name=item.get('chord_name'),
                    on_click=self.on_result_selected))

        if songs:
            self.results_list.add_widget(self._group_header(get_text('found_songs', 'Найденные песни')))
            for item in songs:
                self.results_list.add_widget(ResultCard(
                    title=item.get('title', ''),
                    result_type="song",
                    subtitle=item.get('subtitle', ''),
                    song_id=item.get('song_id'),
                    on_click=self.on_result_selected))

        if terms:
            self.results_list.add_widget(self._group_header(get_text('found_terms', 'Найденные термины')))
            for item in terms:
                self.results_list.add_widget(ResultCard(
                    title=item.get('title', ''),
                    result_type="term",
                    subtitle=item.get('subtitle', ''),
                    term_name=item.get('term_name'),
                    on_click=self.on_result_selected))

    def _group_header(self, text):
        theme_id = settings_manager.theme
        return MDLabel(
            text=text, font_size=sp(14), bold=True, halign="center",
            size_hint_y=None, height=dp(30),
            theme_text_color="Custom",
            text_color=SearchColors.get_text_primary(theme_id))

    # ============ ЖИЗНЕННЫЙ ЦИКЛ ============

    def on_pre_enter(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title(get_text('search'))
            if hasattr(app.top_nav, 'right_container'):
                if hasattr(app.top_nav, 'home_btn'):
                    app.top_nav.right_container.clear_widgets()
                    app.top_nav.right_container.add_widget(app.top_nav.home_btn)

    def on_enter(self):
        self._block_transition = False
        if not self._state_restored:
            restored = self.restore_state()
            if not restored:
                self.clear_search()
                self.search_bar.focus()
        else:
            if hasattr(self, '_saved_scroll_position') and self.scroll:
                Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', self._saved_scroll_position), 0.1)

        if not self.dictionary_screen:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                for screen in app.screen_manager.screens:
                    if screen.name == 'dictionary':
                        self.dictionary_screen = screen
                        break

    def on_pre_leave(self):
        if not self._block_transition:
            self.save_current_state()
        return super().on_pre_leave()

    def on_leave(self):
        self._is_searching = False
        if self._search_thread and self._search_thread.is_alive():
            self._search_thread = None

    def on_text_changed(self, text):
        pass

    def clear_search(self):
        self._is_searching = False
        if self._search_thread and self._search_thread.is_alive():
            self._search_thread = None
        self.title_label.opacity = 1
        self.results_list.clear_widgets()
        self.current_query = ""
        self._last_results = []
        self._state_restored = False
        self.search_bar.clear()

    def perform_search(self, query):
        query = query.strip()
        self.current_query = query
        self._state_restored = False
        if not query:
            self.clear_search()
            return
        if self._is_searching:
            return
        self._is_searching = True
        self.title_label.opacity = 0
        self.results_list.clear_widgets()
        loading_label = MDLabel(
            text=get_text('searching', 'Поиск...'), halign="center",
            font_size=sp(14), theme_text_color="Custom",
            text_color=SearchColors.get_hint_color(settings_manager.theme),
            size_hint_y=None, height=dp(40))
        self.results_list.add_widget(loading_label)

        if self._search_thread and self._search_thread.is_alive():
            self._search_thread = None
        self._search_thread = Thread(target=self._search_worker, args=(query,), daemon=True)
        self._search_thread.start()

    def _search_worker(self, query):
        try:
            chord_results = self._search_chords(query)
            song_results = self._search_songs(query)
            term_results = self._search_terms(query)
            Clock.schedule_once(
                lambda dt: self._show_results(query, chord_results, song_results, term_results),
                0)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка поиска: {error_msg}")
            traceback.print_exc()
            Clock.schedule_once(lambda dt: self._search_error(error_msg), 0)

    def _search_chords(self, query):
        query_lower = query.lower().strip()
        if not query_lower:
            return []
        results, seen = [], set()

        if self.chords_screen and hasattr(self.chords_screen, 'all_chords'):
            for chord in self._search_chords_local(query_lower, self.chords_screen.all_chords):
                key = chord['short_name']
                if key not in seen:
                    seen.add(key)
                    results.append(chord)

        try:
            for item in self._search_chords_on_server(query):
                main_name = item.get('main_name')
                if not main_name or main_name in seen:
                    continue
                seen.add(main_name)
                results.append({
                    'short_name': main_name,
                    'name': ' | '.join(item.get('synonyms') or [main_name]),
                    'type': item.get('chord_type', ''),
                    'description': '',
                    'module': None,
                    'server_data': item,
                })
        except Exception as e:
            logger.warning(f"Ошибка серверного поиска аккордов: {e}")

        return results[:15]

    def _search_chords_local(self, query_lower, all_chords):
        results = []
        alt_map = {
            'bb': 'a#', 'a#': 'bb', 'db': 'c#', 'c#': 'db',
            'eb': 'd#', 'd#': 'eb', 'gb': 'f#', 'f#': 'gb',
            'ab': 'g#', 'g#': 'ab',
        }
        alt_query = alt_map.get(query_lower)
        query_words = query_lower.split()
        for chord in all_chords:
            short_lower = chord['short_name'].lower()
            full_lower = chord['name'].lower()
            if short_lower == query_lower:
                results.append(chord); continue
            if alt_query and short_lower == alt_query:
                results.append(chord); continue
            for part in full_lower.split('|'):
                part_clean = part.strip().replace('$', '/')
                if part_clean == query_lower:
                    results.append(chord); break
                if len(query_words) > 1 and all(w in part_clean for w in query_words):
                    results.append(chord); break
        unique, seen = [], set()
        for c in results:
            if c['short_name'] not in seen:
                seen.add(c['short_name'])
                unique.append(c)
        return unique

    def _search_chords_on_server(self, query):
        try:
            import urllib.parse
            from api.client import api
            from config.app_config import config
            q_enc = urllib.parse.quote(query, safe="")
            url = f"{config.API_BASE_URL}/chords/search?query={q_enc}"
            result = api._request_sync(url, method="GET", include_auth=False)
            if not result or not isinstance(result, dict):
                return []
            return result.get('results') or []
        except Exception as e:
            logger.error(f"Ошибка _search_chords_on_server: {e}")
            return []

    def _search_songs(self, query):
        if len(query) < 2:
            return []
        try:
            result = api.search_songs_sync(query, limit=15)
            if isinstance(result, dict):
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Ошибка поиска песен: {e}")
            return []

    def _search_terms(self, query):
        if not self.dictionary_screen:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                for screen in app.screen_manager.screens:
                    if screen.name == 'dictionary':
                        self.dictionary_screen = screen
                        break
        if not self.dictionary_screen or not hasattr(self.dictionary_screen, 'all_terms'):
            return []

        results = []
        query_lower = query.lower().strip()
        for term_name in self.dictionary_screen.all_terms:
            term_lower = term_name.lower()
            if term_lower == query_lower or term_lower.startswith(query_lower) or query_lower in term_lower:
                if term_name not in results:
                    results.append(term_name)
        return results[:15]

    def _extract_tonality(self, chord_name):
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def _show_results(self, query, chord_results, song_results, term_results, force_redraw=False):
        self.results_list.clear_widgets()
        self._is_searching = False
        self._last_results = []

        if not chord_results and not song_results and not term_results:
            no_results = MDLabel(
                text=f"{get_text('nothing_found')}: «{query}»",
                halign="center", font_size=sp(14),
                theme_text_color="Custom",
                text_color=SearchColors.get_hint_color(settings_manager.theme),
                size_hint_y=None, height=dp(60))
            self.results_list.add_widget(no_results)
            self.save_current_state()
            return

        all_results = []

        if chord_results:
            self.results_list.add_widget(self._group_header(get_text('found_chords', 'Найденные аккорды')))
            for chord in chord_results:
                main_name = chord.get('short_name') or ""
                tonality = self._extract_tonality(chord.get('name', main_name))
                synonyms = []
                for part in chord.get('name', '').split('|'):
                    p = part.strip().replace('$', '/')
                    if p and p != main_name and p not in synonyms:
                        synonyms.append(p)
                subtitle = f"{get_text('tonality', 'Тональность')}: {tonality}"
                if synonyms:
                    subtitle += f" · {', '.join(synonyms[:3])}"
                self.results_list.add_widget(ResultCard(
                    title=main_name, result_type="chord", subtitle=subtitle,
                    chord_name=main_name, on_click=self.on_result_selected))
                all_results.append({
                    'title': main_name, 'result_type': 'chord',
                    'subtitle': subtitle, 'chord_name': main_name,
                })

        if song_results:
            self.results_list.add_widget(self._group_header(get_text('found_songs', 'Найденные песни')))
            for song in song_results[:15]:
                self.results_list.add_widget(ResultCard(
                    title=song.get('artist', get_text('unknown_artist', 'Неизвестный')),
                    result_type="song",
                    subtitle=song.get('title', get_text('untitled', 'Без названия')),
                    song_id=song.get('song_id'),
                    on_click=self.on_result_selected))
                all_results.append({
                    'title': song.get('artist', get_text('unknown_artist', 'Неизвестный')),
                    'result_type': 'song',
                    'subtitle': song.get('title', get_text('untitled', 'Без названия')),
                    'song_id': song.get('song_id'),
                })

        if term_results:
            self.results_list.add_widget(self._group_header(get_text('found_terms', 'Найденные термины')))
            for term_name in term_results:
                term_data = self.dictionary_screen.all_terms.get(term_name, {}) if self.dictionary_screen else {}
                description = term_data.get('description', '')
                if len(description) > 50:
                    description = description[:47] + "..."
                self.results_list.add_widget(ResultCard(
                    title=term_name.capitalize(), result_type="term",
                    subtitle=description, term_name=term_name,
                    on_click=self.on_result_selected))
                all_results.append({
                    'title': term_name.capitalize(), 'result_type': 'term',
                    'subtitle': description, 'term_name': term_name,
                })

        self._last_results = all_results
        self._state_restored = True
        self.save_current_state()

    def _search_error(self, error_msg):
        self.results_list.clear_widgets()
        self._is_searching = False
        self.results_list.add_widget(MDLabel(
            text=get_text('search_error', 'Ошибка поиска'),
            halign="center", font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None, height=dp(60)))

    # ============ ОБРАБОТЧИКИ РЕЗУЛЬТАТОВ ============

    def on_result_selected(self, result_type, chord_name, song_id, term_name):
        if result_type == "chord" and chord_name:
            self.select_chord(chord_name)
        elif result_type == "song" and song_id:
            self.select_song(song_id)
        elif result_type == "term" and term_name:
            self.select_term(term_name)

    def select_chord(self, chord_name):
        self.save_current_state()
        screen_state.set_previous_screen('search')
        screen_state.set_pending_chord(chord_name)
        if self.manager and self.manager.has_screen('chord_detail'):
            self.manager.current = 'chord_detail'
        elif self.manager and self.manager.has_screen('chords'):
            self.manager.current = 'chords'
        else:
            notify.error(get_text('chords_not_found', 'Экран аккордов не найден'))

    def select_song(self, song_id):
        self.save_current_state()
        artist = ""
        title = ""
        for child in self.results_list.children:
            if hasattr(child, 'song_id') and child.song_id == song_id:
                artist = getattr(child, 'title', '')
                title = getattr(child, 'subtitle', '')
                break
        screen_state.set_previous_screen('search')
        if self.manager and self.manager.has_screen('search_screen_detail'):
            screen = self.manager.get_screen('search_screen_detail')
            screen.set_song(song_id, artist, title)
            self.manager.current = 'search_screen_detail'
        elif self.manager and self.manager.has_screen('song_detail'):
            screen = self.manager.get_screen('song_detail')
            screen.set_previous_screen('search')
            screen.set_song(song_id)
            self.manager.current = 'song_detail'
        else:
            notify.error(get_text('song_not_found', 'Экран песни не найден'))

    def select_term(self, term_name):
        self.save_current_state()
        if not self.dictionary_screen:
            notify.error(get_text('navigation_error', 'Ошибка навигации'))
            return
        term_data = self.dictionary_screen.all_terms.get(term_name)
        if not term_data:
            notify.error(get_text('term_not_found', 'Термин не найден'))
            return
        screen_state.set_previous_screen('search')
        if self.manager and self.manager.has_screen('search_term_detail'):
            screen = self.manager.get_screen('search_term_detail')
            screen.set_term(term_name, term_data)
            self.manager.current = 'search_term_detail'
        elif self.manager and self.manager.has_screen('term_detail'):
            screen = self.manager.get_screen('term_detail')
            screen.set_term(term_name, term_data, 'search')
            self.manager.current = 'term_detail'
        else:
            notify.error(get_text('term_not_found', 'Термин не найден'))

    def refresh_search(self):
        if self.current_query and not self.results_list.children:
            self.perform_search(self.current_query)
        elif not self.current_query:
            self.clear_search()

    def go_back(self, instance=None):
        self.save_current_state()
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'