# screens/search_screen.py
"""
Экран поиска (аккорды и песни) - с сохранением состояния
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
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
from config.system_bars import get_navigation_bar_height
from config.layout_config import layout_config
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

    def __init__(self, on_search=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search

        self.orientation = 'horizontal'
        self.size_hint = (0.85, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 0
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)

        self.search_field = MDTextField(
            hint_text="Поиск",
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
        if self.on_search:
            self.on_search("")

    def get_text(self):
        return self.search_field.text.strip()

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        self.search_field.focus = True


class ResultCard(MDCard):
    """Карточка результата поиска"""

    def __init__(self, title, result_type, subtitle, song_id=None, chord_name=None, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.result_type = result_type
        self.subtitle = subtitle
        self.song_id = song_id
        self.chord_name = chord_name
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.spacing = dp(10)
        self.radius = [theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                       theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL]
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.08]
        self.line_color = [1, 1, 1, 0.08]
        self.line_width = 0.5

        self._build_ui()

    def _build_ui(self):
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

    def _on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.result_type, self.chord_name, self.song_id)


class SearchScreen(BaseScreen):
    """Экран поиска с сохранением состояния"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search'
        self.chords_screen = None
        self.bg_image = None
        self._search_thread = None
        self._restoring = False

        # Состояние
        self.last_query = ""
        self.has_results = False
        self.chord_results = []
        self.song_results = []

        self.init_ui()
        self.load_background()

        logger.info('Экран поиска создан')

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
        from kivy.core.window import Window
        from kivy.uix.floatlayout import FloatLayout
        root = FloatLayout()

        # Рассчитываем центр экрана
        search_height = dp(48)
        center_y = (Window.height - search_height) / 2

        # Заголовок над поиском
        self.title_label = MDLabel(
            text="Что будем искать?",
            font_size=sp(16),
            halign="center",
            size_hint=(1, None),
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            bold=True,
            y=center_y + dp(50)
        )

        # Поисковая строка
        self.search_bar = SearchBar(on_search=self.perform_search)
        self.search_bar.pos_hint = {'center_x': 0.5}
        self.search_bar.y = center_y

        # Контейнер для результатов
        top_padding = layout_config.get_top_padding()
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)
        results_top_padding = top_padding + dp(8)

        self.results_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), results_top_padding, dp(12), total_bottom]
        )

        self.results_scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(4),
            bar_color=[1, 1, 1, 0.2],
            bar_inactive_color=[1, 1, 1, 0.05]
        )

        self.results_list = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True
        )
        self.results_list.bind(minimum_height=self.results_list.setter('height'))
        self.results_scroll.add_widget(self.results_list)
        self.results_container.add_widget(self.results_scroll)

        root.add_widget(self.title_label)
        root.add_widget(self.search_bar)
        root.add_widget(self.results_container)

        self.results_container.opacity = 0

        self.add_widget(root)

    def save_current_state(self):
        """Сохраняет текущее состояние экрана"""
        if self.has_results:
            state = {
                'last_query': self.last_query,
                'has_results': True,
                'chord_results': self.chord_results,
                'song_results': self.song_results
            }
            screen_state.save_state(self.name, state)
            logger.debug(f"Сохранено состояние поиска: {self.last_query}")
        else:
            screen_state.clear_state(self.name)

    def restore_state(self):
        """Восстанавливает сохранённое состояние"""
        state = screen_state.get_state(self.name)
        if state and state.get('has_results'):
            self._restoring = True
            self.last_query = state['last_query']
            self.chord_results = state['chord_results']
            self.song_results = state['song_results']
            self.has_results = True

            # Восстанавливаем UI
            self.title_label.opacity = 0
            self.search_bar.opacity = 0
            self.results_container.opacity = 1

            # Отображаем результаты
            self._display_results(self.last_query, self.chord_results, self.song_results)

            logger.debug(f"Восстановлено состояние поиска: {self.last_query}")
            self._restoring = False
            return True
        return False

    def _display_results(self, query, chord_results, song_results):
        """Отображает результаты поиска"""
        self.results_list.clear_widgets()

        if not chord_results and not song_results:
            no_results = MDLabel(
                text=f"По запросу «{query}» ничего не найдено",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.5],
                size_hint_y=None,
                height=dp(60)
            )
            self.results_list.add_widget(no_results)
            return

        if chord_results:
            chords_header = MDLabel(
                text=self._get_chord_header(len(chord_results)),
                font_size=sp(14),
                halign="center",
                bold=True,
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
                text=self._get_song_header(len(song_results)),
                font_size=sp(14),
                halign="center",
                bold=True,
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

        bottom_spacer = Widget(size_hint_y=None, height=dp(20))
        self.results_list.add_widget(bottom_spacer)

    def perform_search(self, query):
        """Выполняет поиск"""
        query = query.strip()

        if not query:
            self._clear_results()
            return

        # Если такой же запрос уже есть - не повторяем
        if query == self.last_query and self.has_results:
            return

        self.last_query = query
        self.has_results = False

        logger.info(f"🔍 Поиск: {query}")

        # Скрываем строку поиска и заголовок
        self.title_label.opacity = 0
        self.search_bar.opacity = 0

        # Показываем контейнер результатов
        self.results_container.opacity = 1

        # Очищаем и показываем индикатор загрузки
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

        # Запускаем поиск в потоке
        if self._search_thread and self._search_thread.is_alive():
            self._search_thread = None

        self._search_thread = Thread(target=self._do_search_worker, args=(query,), daemon=True)
        self._search_thread.start()

    def _clear_results(self):
        """Очищает результаты поиска"""
        self.last_query = ""
        self.has_results = False
        self.chord_results = []
        self.song_results = []
        self.title_label.opacity = 1
        self.search_bar.opacity = 1
        self.results_container.opacity = 0
        self.results_list.clear_widgets()
        screen_state.clear_state(self.name)

    def _do_search_worker(self, query):
        try:
            chord_results = self._search_chords_sync(query)
            song_results = []

            if len(query) >= 2:
                song_results = self._search_songs_sync(query)

            Clock.schedule_once(lambda dt: self._on_search_complete(query, chord_results, song_results), 0)
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            Clock.schedule_once(lambda dt: self._on_search_error(str(e)), 0)

    def _search_chords_sync(self, query):
        if not self.chords_screen or not hasattr(self.chords_screen, 'all_chords'):
            return []

        results = []
        query_lower = query.lower().strip()

        alt_map = {
            'bb': 'a#', 'a#': 'bb',
            'db': 'c#', 'c#': 'db',
            'eb': 'd#', 'd#': 'eb',
            'gb': 'f#', 'f#': 'gb',
            'ab': 'g#', 'g#': 'ab'
        }
        alt_query = alt_map.get(query_lower, None)

        for chord in self.chords_screen.all_chords:
            short_name_lower = chord['short_name'].lower()
            if short_name_lower == query_lower or (alt_query and short_name_lower == alt_query):
                if chord not in results:
                    results.append(chord)

        unique_results = []
        seen_names = set()
        for chord in results:
            if chord['short_name'] not in seen_names:
                seen_names.add(chord['short_name'])
                unique_results.append(chord)

        return unique_results[:15]

    def _search_songs_sync(self, query):
        if len(query) < 2:
            return []
        try:
            result = api.search_songs_sync(query, limit=20)
            if isinstance(result, dict):
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Ошибка API поиска: {e}")
            return []

    def _extract_tonality(self, chord_name):
        if not chord_name:
            return ""
        import re
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def _get_chord_header(self, count):
        return "Найден аккорд" if count == 1 else "Найдены аккорды"

    def _get_song_header(self, count):
        return "Найдена песня" if count == 1 else "Найдены песни"

    def _on_search_complete(self, query, chord_results, song_results):
        self.chord_results = chord_results
        self.song_results = song_results
        self.has_results = True

        self._display_results(query, chord_results, song_results)

        # Сохраняем состояние
        self.save_current_state()

        logger.info(f"Поиск завершён: {len(chord_results)} аккордов, {len(song_results)} песен")

    def _on_search_error(self, error_msg):
        self.results_list.clear_widgets()
        error_label = MDLabel(
            text=f"Ошибка поиска: {error_msg}",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None,
            height=dp(60)
        )
        self.results_list.add_widget(error_label)

    def on_result_selected(self, result_type, chord_name, song_id):
        # Сохраняем состояние перед переходом
        self.save_current_state()

        if result_type == "chord" and chord_name:
            self.select_chord(chord_name)
        elif result_type == "song" and song_id:
            self.select_song(song_id, "")

    def select_chord(self, chord_name):
        if self.chords_screen:
            target_chord = None
            for chord in self.chords_screen.all_chords:
                if chord['short_name'].lower() == chord_name.lower():
                    target_chord = chord
                    break

            if target_chord:
                tonality = self.chords_screen.extract_tonality(target_chord['name'])

                if tonality in self.chords_screen.TONALITIES:
                    self.chords_screen.current_tonality = tonality
                    self.chords_screen.current_tonality_index = self.chords_screen.TONALITIES.index(tonality)
                    self.chords_screen.tonality_card.update_value(tonality)

                    chord_type = target_chord.get('type', 'Major')
                    if chord_type in self.chords_screen.CHORD_TYPES:
                        self.chords_screen.current_type = chord_type
                        self.chords_screen.type_card.update_value(chord_type)

                    self.chords_screen.update_available_chords()

                    if chord_name in self.chords_screen.available_chords:
                        self.chords_screen.current_chord_name = chord_name
                        self.chords_screen.current_chord_index = self.chords_screen.available_chords.index(chord_name)
                        self.chords_screen.chord_card.update_value(chord_name)
                        self.chords_screen._load_variants_for_chord(chord_name)
                        self.chords_screen.load_current_variant()

        if self.manager and self.manager.has_screen('chords'):
            self.manager.current = 'chords'

    def select_song(self, song_id, song_name):
        if self.manager and self.manager.has_screen('song_detail'):
            song_detail = self.manager.get_screen('song_detail')
            song_detail.set_song(song_id)
            self.manager.current = 'song_detail'

    def on_enter(self):
        """При входе на экран - пробуем восстановить состояние"""
        from kivy.core.window import Window

        # Пробуем восстановить состояние
        if self.restore_state():
            # Состояние восстановлено
            return

        # Если не восстановили - сбрасываем
        self._clear_results()

        # Возвращаем позицию
        search_height = dp(48)
        center_y = (Window.height - search_height) / 2
        self.title_label.y = center_y + dp(50)
        self.search_bar.y = center_y
        self.search_bar.clear()

        # Фокус на поле поиска
        Clock.schedule_once(lambda dt: setattr(self.search_bar.search_field, 'focus', True), 0.1)

    def on_leave(self):
        """При выходе с экрана - сохраняем состояние"""
        self.save_current_state()