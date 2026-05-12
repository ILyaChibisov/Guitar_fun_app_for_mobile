# screens/search_screen.py
"""
Экран поиска (аккорды и песни) - АСИНХРОННАЯ ВЕРСИЯ - переведён на BaseScreen
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from io import BytesIO
from threading import Thread

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('SearchScreen')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class SearchBar(MDCard):
    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 1
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)
        self.line_color = [0.46, 0.70, 0.71, 0.4]
        self.line_width = 1.0

        self.search_field = MDTextField(
            hint_text="",
            size_hint_x=1,
            font_size=sp(15),
            height=dp(36),
            on_text_validate=self._on_search,
            mode="fill"
        )

        self.search_field.line_color_normal = [0, 0, 0, 0]
        self.search_field.line_color_focus = [0, 0, 0, 0]
        self.search_field.fill_color_normal = [1, 1, 1, 0]
        self.search_field.fill_color_focus = [1, 1, 1, 0]
        self.search_field.hint_text_color = [0.7, 0.7, 0.7, 1]
        self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]
        self.search_field.bind(text=self._on_text_change)

        self.clear_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            theme_icon_color="Custom",
            icon_color=[0.6, 0.6, 0.6, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear,
            opacity=0
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

        self.add_widget(self.search_field)
        self.add_widget(self.clear_btn)
        self.add_widget(self.search_icon)

    def _on_text_change(self, instance, text):
        self.clear_btn.opacity = 1 if text else 0

    def _on_search(self, instance):
        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear(self, instance):
        self.search_field.text = ""
        self.search_field.focus = True
        self.clear_btn.opacity = 0
        if self.on_clear:
            self.on_clear()

    def get_text(self):
        return self.search_field.text.strip()

    def set_text(self, text):
        self.search_field.text = text
        self.clear_btn.opacity = 1 if text else 0

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        self.search_field.focus = True


class ResultCard(MDCard):
    def __init__(self, title, result_type, subtitle, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.result_type = result_type
        self.subtitle = subtitle
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.elevation = 2
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.15]
        self.line_color = [1, 1, 1, 0.1]
        self.line_width = 1

        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        self.text_container = MDBoxLayout(orientation='vertical', size_hint_x=1, spacing=dp(2))

        self.title_label = MDLabel(
            text=self.title,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle"
        )

        self.subtitle_label = MDLabel(
            text=self.subtitle,
            font_size=sp(12),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            valign="middle"
        )

        self.text_container.add_widget(self.title_label)
        self.text_container.add_widget(self.subtitle_label)

        self.arrow_label = MDLabel(
            text="›",
            font_size=sp(28),
            size_hint_x=None,
            width=dp(32),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        self.add_widget(self.icon_image)
        self.add_widget(self.text_container)
        self.add_widget(self.arrow_label)

        self.bind(on_release=self.on_click)

    def _load_icon(self):
        icon_name = 'chord_png' if self.result_type == 'chord' else 'song_png'
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")
        self.icon_image.text = "🎸" if self.result_type == 'chord' else "🎵"

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.result_type, self.title)


class SearchScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search'
        self.chords_screen = None
        self.bg_image = None
        self.search_results = []
        self.is_loading = False
        self._search_thread = None
        self.loading_dialog = None

        self.init_ui()
        self.load_background()

        logger.info('Экран поиска создан (BaseScreen)')

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

    def set_chords_screen(self, chords_screen):
        self.chords_screen = chords_screen

    def init_ui(self):
        # Верхняя панель
        top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(12),
            md_bg_color=[0, 0, 0, 0]
        )

        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.go_back
        )

        title = MDLabel(
            text="Поиск песен и аккордов",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        top_bar.add_widget(self.back_btn)
        top_bar.add_widget(title)

        # Контент
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(0), dp(16), dp(0)]
        )

        self.search_bar = SearchBar(on_search=self.perform_search, on_clear=self.clear_results)
        content.add_widget(self.search_bar)

        self.results_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(0), dp(8), dp(0), dp(0)]
        )
        content.add_widget(self.results_container)

        # Строим UI
        self.build_ui(content_widget=content, top_widget=top_bar, use_scroll=True)

    def clear_results(self):
        self.results_container.clear_widgets()
        self.search_results = []

    def show_loading(self, show=True, text="Поиск..."):
        if show:
            if not self.loading_dialog:
                self.loading_dialog = MDDialog(title="", text=text, radius=[dp(20)] * 4)
            self.loading_dialog.open()
        else:
            if self.loading_dialog:
                self.loading_dialog.dismiss()
                self.loading_dialog = None

    def perform_search(self, query):
        if len(query) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        logger.info(f"🔍 Поиск: {query}")

        if self._search_thread and self._search_thread.is_alive():
            logger.info("Отменяем предыдущий поиск")
            self._search_thread = None

        self.clear_results()
        self.show_loading(True, f"Поиск '{query}'...")

        self._search_thread = Thread(target=self._do_search_worker, args=(query,), daemon=True)
        self._search_thread.start()

    def _do_search_worker(self, query):
        try:
            chord_results = self._search_chords_sync(query)
            song_results = self._search_songs_sync(query)
            Clock.schedule_once(lambda dt: self._on_search_complete(query, chord_results, song_results), 0)
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            Clock.schedule_once(lambda dt: self._on_search_error(str(e)), 0)

    def _search_chords_sync(self, query):
        if not self.chords_screen or not hasattr(self.chords_screen, 'all_chords'):
            return []

        results = []
        query_lower = query.lower()

        for chord in self.chords_screen.all_chords:
            chord_short = chord['short_name'].lower()
            chord_full = chord['name'].lower().replace('|', ' ').replace('$', '/')

            if query_lower in chord_short or query_lower in chord_full:
                if chord not in results:
                    results.append(chord)

        seen = set()
        unique_results = []
        for chord in results:
            if chord['short_name'] not in seen:
                seen.add(chord['short_name'])
                unique_results.append(chord)

        return unique_results[:10]

    def _search_songs_sync(self, query):
        try:
            result = api.search_songs_sync(query, limit=20)
            if isinstance(result, dict):
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Ошибка API поиска: {e}")
            return []

    def _on_search_complete(self, query, chord_results, song_results):
        self.show_loading(False)

        if not chord_results and not song_results:
            no_results = MDLabel(
                text=f"Ничего не найдено по запросу «{query}»",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.5],
                size_hint_y=None,
                height=dp(60)
            )
            self.results_container.add_widget(no_results)
            return

        if chord_results:
            chords_header = MDLabel(
                text="Аккорды",
                font_size=sp(16),
                bold=True,
                size_hint_y=None,
                height=dp(30),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.9]
            )
            self.results_container.add_widget(chords_header)

            for chord in chord_results:
                card = ResultCard(
                    title=chord['short_name'],
                    result_type="chord",
                    subtitle=f"Тональность: {self.extract_tonality(chord['name'])}",
                    on_click=self.on_result_selected
                )
                self.results_container.add_widget(card)

        if song_results:
            songs_header = MDLabel(
                text="Песни",
                font_size=sp(16),
                bold=True,
                size_hint_y=None,
                height=dp(30),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.9]
            )
            self.results_container.add_widget(songs_header)

            for song in song_results[:10]:
                card = ResultCard(
                    title=song.get('artist', ''),
                    result_type="song",
                    subtitle=song.get('title', ''),
                    on_click=self.on_result_selected
                )
                card.song_id = song.get('song_id')
                self.results_container.add_widget(card)

        bottom_spacer = Widget(size_hint_y=None, height=dp(20))
        self.results_container.add_widget(bottom_spacer)
        logger.info(f"Поиск завершён: {len(chord_results)} аккордов, {len(song_results)} песен")

    def _on_search_error(self, error_msg):
        self.show_loading(False)
        error_label = MDLabel(
            text=f"Ошибка поиска: {error_msg}",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None,
            height=dp(60)
        )
        self.results_container.add_widget(error_label)

    def on_result_selected(self, result_type, title):
        if result_type == "chord":
            self.select_chord(title)
        else:
            for child in self.results_container.children:
                if hasattr(child, 'song_id') and hasattr(child, 'title') and child.title == title:
                    self.select_song(child.song_id, title)
                    break

    def extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        import re
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def select_chord(self, chord_name):
        if self.chords_screen and hasattr(self.chords_screen, 'load_chord_by_name'):
            self.chords_screen.load_chord_by_name(chord_name)
        if self.manager and self.manager.has_screen('chords'):
            self.manager.current = 'chords'

    def select_song(self, song_id, song_name):
        if self.manager and self.manager.has_screen('song_detail'):
            song_detail = self.manager.get_screen('song_detail')
            song_detail.set_song(song_id)
            self.manager.current = 'song_detail'

    def go_back(self, instance):
        if self.manager:
            self.manager.current = 'songs'