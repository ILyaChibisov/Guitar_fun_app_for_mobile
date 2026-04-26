# screens/search_screen.py
"""
Экран поиска (аккорды и песни)
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField, MDTextFieldLeadingIcon
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView

from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('SearchScreen')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


class SearchScreen(MDScreen):
    """Экран поиска"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search'
        self.chords_screen = None
        self.bg_image = None
        self.search_results = []
        self.is_loading = False

        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Экран поиска создан')

    def load_background(self):
        """Загружает фоновое изображение"""
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
        """Устанавливает ссылку на экран аккордов"""
        self.chords_screen = chords_screen

    def init_ui(self):
        from kivy.uix.widget import Widget

        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0
        )

        # Отступ сверху для компенсации верхней панели
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # ============ ВЕРХНЯЯ ПАНЕЛЬ ============
        nav_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(12),
            md_bg_color=[0, 0, 0, 0]
        )

        # Кнопка назад
        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.go_back
        )

        # Заголовок
        title = MDLabel(
            text="Поиск",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        # Пустой виджет для баланса
        nav_row.add_widget(self.back_btn)
        nav_row.add_widget(title)
        nav_row.add_widget(MDBoxLayout(size_hint_x=None, width=dp(36)))

        # ============ ПОЛЕ ВВОДА ============
        input_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            padding=[dp(20), dp(16), dp(20), dp(8)]
        )

        self.search_input = MDTextField(
            mode="filled",
            size_hint_x=1,
            height=dp(48),
            radius=[dp(24), dp(24), dp(24), dp(24)],
            on_text_validate=self.perform_search,
            theme_line_color="Custom",
            line_color_normal=[0, 0, 0, 0],
            line_color_focus=[0, 0, 0, 0],
            theme_bg_color="Custom",
            fill_color_normal=[1, 1, 1, 1],  # Белый фон
            fill_color_focus=[1, 1, 1, 1],   # Белый фон при фокусе
            text_color_normal=[0, 0, 0, 0.85],  # Чёрный текст
            text_color_focus=[0, 0, 0, 0.85],
            font_size=sp(14),
            hint_text="Введите название песни или аккорда",
            hint_text_color=[0.5, 0.5, 0.5, 0.6],
            padding=[dp(44), dp(12), dp(40), dp(12)]
        )

        # Иконка лупы слева
        search_icon = MDTextFieldLeadingIcon(
            icon="magnify",
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 0.7]
        )
        self.search_input.add_widget(search_icon)

        # Кнопка поиска (лупа справа)
        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=theme.PRIMARY,
            md_bg_color=[0, 0, 0, 0],
            on_release=self.perform_search,
            pos_hint={'center_y': 0.5}
        )
        self.search_input.add_widget(self.search_btn)

        # Кнопка очистки (крестик) справа
        self.clear_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(22), dp(22)),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 0.5],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.clear_text,
            pos_hint={'center_y': 0.5}
        )
        self.clear_btn.opacity = 0
        self.search_input.add_widget(self.clear_btn)

        self.search_input.bind(text=self.on_text_change)

        input_container.add_widget(self.search_input)

        # ============ РЕЗУЛЬТАТЫ ПОИСКА ============
        self.results_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_color=[1, 1, 1, 0.3],
            bar_width=dp(4)
        )

        self.results_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(8), dp(16), dp(85)]
        )
        self.results_scroll.add_widget(self.results_container)

        main_layout.add_widget(nav_row)
        main_layout.add_widget(input_container)
        main_layout.add_widget(self.results_scroll)

        self.add_widget(main_layout)

    def on_text_change(self, instance, text):
        """Показывает/скрывает кнопку очистки"""
        self.clear_btn.opacity = 1 if text else 0

    def clear_text(self, instance):
        """Очищает поле ввода и результаты"""
        self.search_input.text = ""
        self.search_input.focus = True
        self.clear_results()

    def clear_results(self):
        """Очищает результаты поиска"""
        self.results_container.clear_widgets()
        self.search_results = []

    def perform_search(self, instance=None):
        """Выполняет поиск (по Enter или нажатию на лупу)"""
        query = self.search_input.text.strip()
        if len(query) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        logger.info(f"🔍 Поиск: {query}")
        self.clear_results()

        # Показываем индикатор загрузки
        loading_label = MDLabel(
            text="Поиск...",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_y=None,
            height=dp(50)
        )
        self.results_container.add_widget(loading_label)

        Clock.schedule_once(lambda dt: self.do_search(query, loading_label), 0.1)

    def do_search(self, query, loading_label):
        """Реальная логика поиска"""
        if loading_label in self.results_container.children:
            self.results_container.remove_widget(loading_label)

        # Ищем аккорды
        chord_results = self.search_chords(query)

        # Ищем песни
        song_results = self.search_songs(query)

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

        # Аккорды
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
                result_card = self.create_result_card(
                    chord_name=chord['short_name'],
                    result_type="chord",
                    subtitle=f"Тональность: {self.extract_tonality(chord['name'])}"
                )
                self.results_container.add_widget(result_card)

        # Песни
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
                result_card = self.create_result_card(
                    chord_name=song.get('title', ''),
                    result_type="song",
                    subtitle=f"{song.get('artist', '')} • {song.get('tabs_count', 1)} подборов",
                    song_id=song.get('song_id')
                )
                self.results_container.add_widget(result_card)

    def search_chords(self, query):
        """Ищет аккорды в локальных данных"""
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

    def search_songs(self, query):
        """Ищет песни через API"""
        try:
            return api.search_songs_sync(query, "general", 20)
        except Exception as e:
            logger.error(f"Ошибка поиска песен: {e}")
            return []

    def extract_tonality(self, chord_name):
        """Извлекает тональность из названия аккорда"""
        if not chord_name:
            return ""
        import re
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def create_result_card(self, chord_name, result_type, subtitle, song_id=None):
        """Создаёт карточку результата поиска"""
        card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(70),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            ripple_behavior=True
        )

        container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=dp(12)
        )

        icon = "🎸" if result_type == "chord" else "🎵"
        icon_label = MDLabel(
            text=icon,
            font_size=sp(28),
            size_hint_x=None,
            width=dp(48),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9]
        )

        info_box = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2)
        )

        name_label = MDLabel(
            text=chord_name,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )

        subtitle_label = MDLabel(
            text=subtitle,
            font_size=sp(12),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        info_box.add_widget(name_label)
        info_box.add_widget(subtitle_label)

        arrow_label = MDLabel(
            text="›",
            font_size=sp(28),
            size_hint_x=None,
            width=dp(32),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        container.add_widget(icon_label)
        container.add_widget(info_box)
        container.add_widget(arrow_label)

        card.add_widget(container)

        if result_type == "chord":
            card.bind(on_release=lambda x, name=chord_name: self.select_chord(name))
        else:
            card.bind(on_release=lambda x, sid=song_id: self.select_song(sid, chord_name))

        return card

    def select_chord(self, chord_name):
        """Выбирает аккорд"""
        if self.chords_screen and hasattr(self.chords_screen, 'load_chord_by_name'):
            self.chords_screen.load_chord_by_name(chord_name)

        if self.manager and self.manager.has_screen('chords'):
            self.manager.current = 'chords'

    def select_song(self, song_id, song_name):
        """Выбирает песню"""
        if self.manager and self.manager.has_screen('song_detail'):
            song_detail = self.manager.get_screen('song_detail')
            song_detail.set_song(song_id)
            self.manager.current = 'song_detail'

    def go_back(self, instance):
        """Возврат на предыдущий экран"""
        if self.manager:
            self.manager.current = 'songs'