# screens/search_screen.py - с поиском терминов (без изменения дизайна)
"""
Экран поиска (аккорды, песни и термины)
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
from kivy.core.window import Window
from io import BytesIO
from threading import Thread

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
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

logger = screen_logger('SearchScreen')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class SearchBar(MDCard):
    """Поисковая строка"""

    def __init__(self, on_search=None, on_clear=None, on_text_change=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.on_text_change = on_text_change

        self.orientation = 'horizontal'
        self.size_hint = (0.9, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 0
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)
        self.pos_hint = {'center_x': 0.5}

        self.search_field = MDTextField(
            hint_text="Поиск аккордов или песен...",
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
        if self.on_text_change:
            self.on_text_change(text)

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

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        self.search_field.focus = True


class ResultCard(MDCard):
    """Карточка результата поиска"""

    def __init__(self, title, result_type, subtitle, song_id=None, chord_name=None, term_name=None, on_click=None,
                 **kwargs):
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
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False  # Отключаем для производительности
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.08]
        self.line_color = [1, 1, 1, 0.08]
        self.line_width = 0.5
        self.clip = True

        self._build_ui()

    def _build_ui(self):
        # Иконка в зависимости от типа
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        self.title_label = MDLabel(
            text=self.title,
            font_size=sp(15),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        self.subtitle_label = MDLabel(
            text=self.subtitle,
            font_size=sp(11),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        text_layout.add_widget(self.title_label)
        text_layout.add_widget(self.subtitle_label)

        arrow = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(28),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )

        self.add_widget(self.icon_image)
        self.add_widget(text_layout)
        self.add_widget(arrow)

        self.bind(on_release=self._on_click)

    def _load_icon(self):
        """Загружает иконку в зависимости от типа результата"""
        if self.result_type == 'chord':
            icon_name = 'chord_png'
        elif self.result_type == 'term':
            icon_name = 'dictionary_png'
        else:
            icon_name = 'song_png'

        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        # Заглушки
        if self.result_type == 'chord':
            self.icon_image.text = "🎸"
        elif self.result_type == 'term':
            self.icon_image.text = "📖"
        else:
            self.icon_image.text = "🎵"

    def _on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.result_type, self.chord_name, self.song_id, self.term_name)


class SearchScreen(BaseScreen):
    """Экран поиска - аккорды, песни и термины"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search'
        self.chords_screen = None
        self.dictionary_screen = None
        self.bg_image = None
        self._search_thread = None
        self._is_searching = False
        self.current_query = ""

        self.init_ui()
        self.load_background()

        logger.info('✅ Экран поиска создан')

    def load_background(self):
        """Загружает фоновое изображение"""
        try:
            if HAS_ASSETS:
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        logger.info(f"🖼️ Фон загружен из ассета: {name}")
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
        """Устанавливает ссылку на экран аккордов"""
        self.chords_screen = chords_screen
        logger.info("🎸 Установлен chords_screen")

    def set_dictionary_screen(self, dictionary_screen):
        """Устанавливает ссылку на экран словаря"""
        self.dictionary_screen = dictionary_screen
        logger.info("📚 Установлен dictionary_screen")

    def init_ui(self):
        """Инициализирует UI с правильными отступами"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ (под статус-бар и TopNav)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Небольшой отступ сверху для эстетики
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))

        # Заголовок
        self.title_label = MDLabel(
            text="Что будем искать?",
            font_size=sp(16),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            bold=True
        )
        main_layout.add_widget(self.title_label)

        # Небольшой отступ между заголовком и строкой поиска
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(16)))

        # Поисковая строка
        self.search_bar = SearchBar(
            on_search=self.perform_search,
            on_clear=self.clear_search,
            on_text_change=self.on_text_changed
        )
        main_layout.add_widget(self.search_bar)

        # Небольшой отступ перед результатами
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Контейнер для результатов с правильными отступами снизу
        bottom_padding = layout_config.get_bottom_padding()

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(8), dp(12), bottom_padding]
        )
        cards_container.clip = True

        # ScrollView для результатов (скрываем скроллбар)
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0]
        )
        scroll.clip = True

        self.results_list = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True
        )
        self.results_list.bind(minimum_height=self.results_list.setter('height'))

        scroll.add_widget(self.results_list)
        cards_container.add_widget(scroll)
        main_layout.add_widget(cards_container)

        self.add_widget(main_layout)

        logger.info(f"✅ UI поиска построен, bottom_padding={bottom_padding}dp")

    def on_enter(self):
        logger.info("🚪 on_enter вызван")
        self.clear_search()
        self.search_bar.focus()

        if not self.dictionary_screen:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                for screen in app.screen_manager.screens:
                    if screen.name == 'dictionary':
                        self.dictionary_screen = screen
                        break

    def on_leave(self):
        logger.info("🚪 on_leave вызван")
        self._is_searching = False
        if self._search_thread and self._search_thread.is_alive():
            self._search_thread = None

    def on_text_changed(self, text):
        """Только отслеживаем изменение текста, поиск только по Enter или кнопке"""
        pass

    def clear_search(self):
        logger.info("🧹 clear_search вызван")
        self._is_searching = False
        if self._search_thread and self._search_thread.is_alive():
            self._search_thread = None

        self.title_label.opacity = 1
        self.results_list.clear_widgets()
        self.current_query = ""
        self.search_bar.clear()
        logger.info("✅ Поиск очищен")

    def perform_search(self, query):
        """Выполняет поиск только по Enter или кнопке"""
        logger.info(f"🔍 perform_search: query='{query}'")
        query = query.strip()
        self.current_query = query

        if not query:
            self.clear_search()
            return

        if self._is_searching:
            return

        self._is_searching = True
        self.title_label.opacity = 0
        self.results_list.clear_widgets()

        loading_label = MDLabel(
            text="Поиск...",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            size_hint_y=None,
            height=dp(40)
        )
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
            Clock.schedule_once(lambda dt: self._show_results(query, chord_results, song_results, term_results), 0)
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            Clock.schedule_once(lambda dt: self._search_error(str(e)), 0)

    def _search_chords(self, query):
        """Поиск аккордов - точное совпадение и по альтернативным названиям"""
        if not self.chords_screen or not hasattr(self.chords_screen, 'all_chords'):
            return []

        results = []
        query_lower = query.lower().strip()
        query_words = query_lower.split()

        alt_map = {
            'bb': 'a#', 'a#': 'bb', 'db': 'c#', 'c#': 'db',
            'eb': 'd#', 'd#': 'eb', 'gb': 'f#', 'f#': 'gb',
            'ab': 'g#', 'g#': 'ab'
        }
        alt_query = alt_map.get(query_lower, None)

        for chord in self.chords_screen.all_chords:
            short_name_lower = chord['short_name'].lower()
            full_name_lower = chord['name'].lower()

            if short_name_lower == query_lower:
                if chord not in results:
                    results.append(chord)
                continue

            if alt_query and short_name_lower == alt_query:
                if chord not in results:
                    results.append(chord)
                continue

            name_parts = full_name_lower.split('|')
            for part in name_parts:
                part_clean = part.strip().replace('$', '/')
                if part_clean == query_lower:
                    if chord not in results:
                        results.append(chord)
                    break

                if len(query_words) > 1:
                    all_words_found = True
                    for word in query_words:
                        if word not in part_clean:
                            all_words_found = False
                            break
                    if all_words_found:
                        if chord not in results:
                            results.append(chord)
                        break

        unique = []
        seen = set()
        for chord in results:
            if chord['short_name'] not in seen:
                seen.add(chord['short_name'])
                unique.append(chord)

        logger.info(f"🔍 Найдено аккордов: {len(unique)}")
        return unique[:15]

    def _search_songs(self, query):
        """Поиск песен через API"""
        if len(query) < 2:
            return []
        try:
            result = api.search_songs_sync(query, limit=15)
            if isinstance(result, dict):
                songs = result.get('results', [])
            else:
                songs = result if isinstance(result, list) else []
            logger.info(f"🔍 Найдено песен: {len(songs)}")
            return songs
        except Exception as e:
            logger.error(f"❌ Ошибка поиска песен: {e}")
            return []

    def _search_terms(self, query):
        """Поиск терминов из словаря"""
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

        for term_name, term_data in self.dictionary_screen.all_terms.items():
            term_lower = term_name.lower()
            description = term_data.get('description', '').lower()

            if term_lower == query_lower:
                if term_name not in results:
                    results.append(term_name)
                continue

            if term_lower.startswith(query_lower):
                if term_name not in results:
                    results.append(term_name)
                continue

            if query_lower in term_lower:
                if term_name not in results:
                    results.append(term_name)
                continue

        logger.info(f"🔍 Найдено терминов: {len(results)}")
        return results[:15]

    def _extract_tonality(self, chord_name):
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def _show_results(self, query, chord_results, song_results, term_results):
        logger.info(f"📊 _show_results: chords={len(chord_results)}, songs={len(song_results)}, terms={len(term_results)}")

        self.results_list.clear_widgets()
        self._is_searching = False

        if not chord_results and not song_results and not term_results:
            no_results = MDLabel(
                text=f"По запросу «{query}» ничего не найдено",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.4],
                size_hint_y=None,
                height=dp(60)
            )
            self.results_list.add_widget(no_results)
            return

        if chord_results:
            chords_header = MDLabel(
                text="Найденные аккорды",
                font_size=sp(14),
                bold=True,
                halign="center",
                size_hint_y=None,
                height=dp(30),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.8]
            )
            self.results_list.add_widget(chords_header)

            for chord in chord_results:
                tonality = self._extract_tonality(chord['name'])
                card = ResultCard(
                    title=chord['short_name'],
                    result_type="chord",
                    subtitle=f"Тональность: {tonality}",
                    chord_name=chord['short_name'],
                    on_click=self.on_result_selected
                )
                self.results_list.add_widget(card)

        if song_results:
            songs_header = MDLabel(
                text="Найденные песни",
                font_size=sp(14),
                bold=True,
                halign="center",
                size_hint_y=None,
                height=dp(30),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.8]
            )
            self.results_list.add_widget(songs_header)

            for song in song_results[:15]:
                card = ResultCard(
                    title=song.get('artist', 'Неизвестный'),
                    result_type="song",
                    subtitle=song.get('title', 'Без названия'),
                    song_id=song.get('song_id'),
                    on_click=self.on_result_selected
                )
                self.results_list.add_widget(card)

        if term_results:
            terms_header = MDLabel(
                text="Найденные термины",
                font_size=sp(14),
                bold=True,
                halign="center",
                size_hint_y=None,
                height=dp(30),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.8]
            )
            self.results_list.add_widget(terms_header)

            for term_name in term_results:
                term_data = self.dictionary_screen.all_terms.get(term_name, {})
                description = term_data.get('description', '')
                if len(description) > 50:
                    description = description[:47] + "..."

                card = ResultCard(
                    title=term_name.capitalize(),
                    result_type="term",
                    subtitle=description,
                    term_name=term_name,
                    on_click=self.on_result_selected
                )
                self.results_list.add_widget(card)

    def _search_error(self, error_msg):
        self.results_list.clear_widgets()
        self._is_searching = False
        error_label = MDLabel(
            text="Ошибка поиска",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None,
            height=dp(60)
        )
        self.results_list.add_widget(error_label)

    def on_result_selected(self, result_type, chord_name, song_id, term_name):
        """Обработчик выбора результата"""
        if result_type == "chord" and chord_name:
            self.select_chord(chord_name)
        elif result_type == "song" and song_id:
            self.select_song(song_id)
        elif result_type == "term" and term_name:
            self.select_term(term_name)

    def select_chord(self, chord_name):
        """Выбор аккорда"""
        logger.info(f"🎸 Выбран аккорд: {chord_name}")

        if not self.chords_screen:
            notify.error("Ошибка навигации")
            return

        if hasattr(self.chords_screen, 'select_chord_by_name'):
            self.chords_screen.select_chord_by_name(chord_name)
        elif hasattr(self.chords_screen, 'load_chord_by_name'):
            self.chords_screen.load_chord_by_name(chord_name)

        screen_state.set_previous_screen('search')

        if self.manager and self.manager.has_screen('chords'):
            self.manager.current = 'chords'

    def select_song(self, song_id):
        logger.info(f"🎵 Выбрана песня: {song_id}")
        if self.manager and self.manager.has_screen('song_detail'):
            song_detail = self.manager.get_screen('song_detail')
            song_detail.set_previous_screen('search')
            song_detail.set_song(song_id)
            self.manager.current = 'song_detail'

    def select_term(self, term_name):
        """Выбор термина"""
        logger.info(f"📚 Выбран термин: {term_name}")

        if not self.dictionary_screen:
            notify.error("Ошибка навигации")
            return

        term_data = self.dictionary_screen.all_terms.get(term_name)
        if not term_data:
            notify.error("Термин не найден")
            return

        if self.manager and self.manager.has_screen('term_detail'):
            term_detail = self.manager.get_screen('term_detail')
            term_detail.set_term(term_name, term_data, 'search')
            self.manager.current = 'term_detail'

    def refresh_search(self):
        logger.info("🔄 refresh_search вызван")
        if self.current_query:
            self.perform_search(self.current_query)
        else:
            self.clear_search()