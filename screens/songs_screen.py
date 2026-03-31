# screens/songs_screen.py
"""
Экран песен с алфавитной навигацией и поиском
"""
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.progressbar import MDProgressBar
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from screens.components.alphabet_keyboard import AlphabetKeyboard

logger = screen_logger('Songs')


def show_snackbar(message, bg_color=None):
    """Показывает уведомление"""
    snack = MDSnackbar()
    snack.text = message
    snack.snackbar_x = "10dp"
    snack.snackbar_y = "10dp"
    snack.radius = [theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                    theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL]
    if bg_color:
        snack.md_bg_color = bg_color
    snack.open()


class LoadingSpinner(MDBoxLayout):
    """Индикатор загрузки"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(16)

        self.progress = MDProgressBar(
            size_hint=(0.8, None),
            height=dp(4),
            pos_hint={'center_x': 0.5},
            value=50,
            max=100
        )

        self.anim = None

        self.label = MDLabel(
            text="Загрузка...",
            halign="center",
            font_style="Body1",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30)
        )

        self.add_widget(self.progress)
        self.add_widget(self.label)

    def start_animation(self):
        """Запускает анимацию загрузки"""
        self.anim = Animation(value=100, duration=1) + Animation(value=0, duration=1)
        self.anim.repeat = True
        self.anim.start(self.progress)

    def stop_animation(self):
        """Останавливает анимацию загрузки"""
        if self.anim:
            self.anim.cancel(self.progress)
        self.progress.value = 0


class ArtistCard(MDCard):
    """Карточка исполнителя"""

    def __init__(self, artist, on_song_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist = artist
        self.on_song_click_callback = on_song_click
        self.expanded = False
        self.songs = []
        self.is_loading = False

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.md_bg_color = theme.SURFACE
        self.elevation = 1

        self.header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32))

        self.icon = MDLabel(text="🎸", font_size=dp(18), size_hint_x=0.1)
        self.title = MDLabel(text=artist, font_style="Subtitle1", size_hint_x=0.8, bold=True)
        self.arrow = MDIconButton(icon="chevron-down", size_hint_x=0.1,
                                  theme_text_color="Custom", text_color=theme.TEXT_SECONDARY)

        self.header.add_widget(self.icon)
        self.header.add_widget(self.title)
        self.header.add_widget(self.arrow)
        self.add_widget(self.header)

        self.songs_container = MDBoxLayout(orientation='vertical', spacing=dp(4), size_hint_y=None, opacity=0,
                                           disabled=True)
        self.add_widget(self.songs_container)

        self.loading_spinner = LoadingSpinner(size_hint_y=None, height=dp(60), opacity=0, disabled=True)
        self.add_widget(self.loading_spinner)

        self.bind(on_release=self.toggle)

    def load_songs(self):
        """Загружает песни исполнителя"""
        if self.songs:
            self.show_songs()
            return

        self.is_loading = True
        self.loading_spinner.opacity = 1
        self.loading_spinner.disabled = False
        self.loading_spinner.start_animation()
        self.songs_container.opacity = 0

        api.get_songs_by_artist(
            artist=self.artist,
            on_success=self.on_songs_loaded,
            on_failure=self.on_load_failed
        )

    def on_songs_loaded(self, songs):
        """Обработчик загрузки песен"""
        self.songs = songs
        self.is_loading = False
        self.loading_spinner.stop_animation()
        self.loading_spinner.opacity = 0
        self.loading_spinner.disabled = True
        self.show_songs()

    def on_load_failed(self, req, error):
        """Обработчик ошибки загрузки"""
        self.is_loading = False
        self.loading_spinner.stop_animation()
        self.loading_spinner.opacity = 0
        self.loading_spinner.disabled = True
        show_snackbar(f"Ошибка загрузки песен: {error}")

    def show_songs(self):
        """Отображает список песен"""
        self.songs_container.clear_widgets()

        for song in self.songs:
            tabs_count = song.get('tabs_count', 1)
            text = f"{song['title']} ({tabs_count} подборов)" if tabs_count > 1 else song['title']
            song_btn = MDRaisedButton(
                text=text,
                size_hint=(1, None),
                height=dp(40),
                md_bg_color=[0.95, 0.95, 0.95, 1],
                theme_text_color="Custom",
                text_color=theme.TEXT_PRIMARY,
                font_size=dp(12),
                on_release=lambda x, s=song: self._on_song_click(s)
            )
            song_btn.radius = [theme.CORNER_RADIUS_SMALL]
            self.songs_container.add_widget(song_btn)

        self.songs_container.height = len(self.songs) * dp(44)

        if self.expanded:
            self.songs_container.opacity = 1
            self.songs_container.disabled = False
            self.height = dp(48) + self.songs_container.height + dp(8)

    def toggle(self, instance):
        """Раскрывает/скрывает список песен"""
        if not self.expanded and not self.songs and not self.is_loading:
            self.load_songs()
            return

        self.expanded = not self.expanded
        self.songs_container.opacity = 1 if self.expanded else 0
        self.songs_container.disabled = not self.expanded
        self.arrow.icon = "chevron-up" if self.expanded else "chevron-down"

        if self.expanded:
            self.height = dp(48) + self.songs_container.height + dp(8)
        else:
            self.height = dp(48)

    def _on_song_click(self, song):
        """Обработчик нажатия на песню"""
        if self.on_song_click_callback:
            self.on_song_click_callback(song)


class ResultCard(MDCard):
    """Карточка результата поиска"""

    def __init__(self, song, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.song = song
        self.on_click_callback = on_click

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(70)
        self.padding = dp(10)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.md_bg_color = theme.SURFACE
        self.elevation = 1

        artist_label = MDLabel(
            text=f"🎸 {song.get('artist', '')}",
            font_style="Subtitle2",
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Primary",
            bold=True
        )

        title_label = MDLabel(
            text=song.get('title', ''),
            font_style="Body2",
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Secondary"
        )

        tabs_count = song.get('tabs_count', 1)
        info_label = MDLabel(
            text=f"{tabs_count} подборов" if tabs_count > 1 else "1 подбор",
            font_style="Caption",
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Hint"
        )

        self.add_widget(artist_label)
        self.add_widget(title_label)
        self.add_widget(info_label)

        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.song)


class SongsScreen(MDScreen):
    """Экран песен"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.current_language = 'ru'
        self.search_mode = False
        self.is_loading = False
        self.loading_spinner = None
        self.artists_cache = {}

        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.layout = MDBoxLayout(orientation='vertical', padding=dp(8), spacing=dp(8))

        # Поисковая строка
        self.search_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))

        self.search_field = MDTextField(
            hint_text="Поиск песен или исполнителей...",
            mode="round",
            size_hint_x=0.8,
            font_size=dp(13),
            height=dp(48)
        )

        self.search_btn = MDRaisedButton(
            text="Найти",
            size_hint_x=0.2,
            height=dp(48),
            md_bg_color=theme.PRIMARY,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=self.do_search
        )
        self.search_btn.radius = [theme.CORNER_RADIUS_SMALL]

        self.search_layout.add_widget(self.search_field)
        self.search_layout.add_widget(self.search_btn)
        self.layout.add_widget(self.search_layout)

        # Панель переключения алфавита
        self.lang_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(8))

        self.lang_left_btn = MDIconButton(icon="chevron-left", on_release=self.prev_language, size_hint_x=0.1)
        self.lang_label = MDLabel(text="🇷🇺 Русский", halign="center", font_style="Body2", size_hint_x=0.8)
        self.lang_right_btn = MDIconButton(icon="chevron-right", on_release=self.next_language, size_hint_x=0.1)

        self.lang_layout.add_widget(self.lang_left_btn)
        self.lang_layout.add_widget(self.lang_label)
        self.lang_layout.add_widget(self.lang_right_btn)
        self.layout.add_widget(self.lang_layout)

        # Клавиатура с буквами
        self.keyboard = AlphabetKeyboard()
        self.keyboard.on_letter_press = self.on_letter_press
        self.layout.add_widget(self.keyboard)

        # Контейнер для контента
        self.content_scroll = MDScrollView(size_hint=(1, 1))
        self.content_container = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None,
                                             adaptive_height=True)
        self.content_scroll.add_widget(self.content_container)
        self.layout.add_widget(self.content_scroll)

        self.add_widget(self.layout)

        # Загружаем буквы для алфавита
        self.load_letters()

        logger.info('Экран песен создан')

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def show_loading(self):
        """Показывает индикатор загрузки"""
        if self.is_loading:
            return

        self.is_loading = True
        self.content_container.clear_widgets()
        self.loading_spinner = LoadingSpinner()
        self.content_container.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()

    def hide_loading(self):
        """Скрывает индикатор загрузки"""
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
        self.content_container.clear_widgets()

    def prev_language(self, instance):
        """Предыдущий язык"""
        if self.current_language == 'ru':
            self.set_language('en')
        else:
            self.set_language('ru')

    def next_language(self, instance):
        """Следующий язык"""
        if self.current_language == 'ru':
            self.set_language('en')
        else:
            self.set_language('ru')

    def set_language(self, language):
        """Устанавливает язык алфавита"""
        self.current_language = language
        self.keyboard.set_language(language)
        self.lang_label.text = "🇷🇺 Русский" if language == 'ru' else "🇬🇧 English"
        self.artists_cache = {}

    def load_letters(self):
        """Загружает список букв, для которых есть песни"""
        self.show_loading()
        api.get_alphabet(
            on_success=self.on_letters_loaded,
            on_failure=self.on_load_failed
        )

    def on_letters_loaded(self, letters):
        """Обработчик загрузки букв"""
        self.hide_loading()
        logger.info(f"Активные буквы: {letters}")

    def on_letter_press(self, letter):
        """Обработчик нажатия на букву/цифру - переход на экран исполнителей"""
        logger.info(f"Выбрана буква/цифра: {letter}")

        if hasattr(self, 'manager') and self.manager:
            artists_screen = self.manager.get_screen('artists_by_letter')
            if artists_screen:
                artists_screen.set_letter(letter)
                self.manager.current = 'artists_by_letter'

    def load_artists_by_letter(self, letter):
        """Загружает исполнителей по букве"""
        print(f"DEBUG: load_artists_by_letter ВЫЗВАН для буквы: {letter}")
        self.show_loading()

        def on_success(artists):
            print(f"DEBUG: on_success ВЫЗВАН, artists count: {len(artists)}")
            self.on_artists_loaded(artists)

        def on_failure(req, error):
            print(f"DEBUG: on_failure ВЫЗВАН, error: {error}")
            self.on_load_failed(req, error)

        api.get_artists_by_letter(
            letter=letter,
            on_success=on_success,
            on_failure=on_failure
        )

    def on_artists_loaded(self, artists):
        """Отображает список исполнителей"""
        print(f"=== DEBUG: on_artists_loaded ===")
        print(f"Количество: {len(artists)}")

        self.hide_loading()
        self.content_container.clear_widgets()

        if not artists:
            no_data_label = MDLabel(
                text="Нет исполнителей на эту букву",
                halign="center",
                font_style="Body1",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(100)
            )
            self.content_container.add_widget(no_data_label)
            return

        for artist_data in artists:
            artist = artist_data.get('artist')
            if artist:
                # Упрощённая карточка исполнителя без загрузки песен внутри
                card = MDCard(
                    orientation='vertical',
                    size_hint=(1, None),
                    height=dp(50),
                    padding=dp(12),
                    radius=[theme.CORNER_RADIUS_SMALL],
                    md_bg_color=theme.SURFACE,
                    elevation=1,
                    on_release=lambda x, a=artist: self.on_artist_selected(a)
                )

                artist_label = MDLabel(
                    text=f"🎸 {artist}",
                    font_style="Subtitle1",
                    size_hint_y=None,
                    height=dp(30),
                    theme_text_color="Primary",
                    bold=True
                )
                card.add_widget(artist_label)
                self.content_container.add_widget(card)

    def on_artist_selected(self, artist):
        """Выбор исполнителя - переход на экран его песен"""
        logger.info(f"Выбран исполнитель: {artist}")

        if hasattr(self, 'manager') and self.manager:
            artist_songs_screen = self.manager.get_screen('artist_songs')
            if artist_songs_screen:
                artist_songs_screen.set_artist(artist)
                self.manager.current = 'artist_songs'

    def on_song_selected(self, song):
        """Обработчик выбора песни"""
        logger.info(f"Выбрана песня: {song}")

        self.show_loading()
        api.get_tabs_by_song(
            artist=song['artist'],
            title=song['title'],
            on_success=lambda tabs: self.on_tabs_loaded(song, tabs),
            on_failure=self.on_load_failed
        )

    def on_tabs_loaded(self, song, tabs):
        """Обработчик загрузки подборов песни"""
        self.hide_loading()

        if not tabs:
            show_snackbar("Нет доступных подборов для этой песни")
            return

        logger.info(f"Загружено {len(tabs)} подборов для песни: {song['artist']} - {song['title']}")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'switch_screen'):
            app.current_song_data = {
                'song_id': tabs[0]['id'],
                'artist': song['artist'],
                'title': song['title'],
                'tabs': tabs
            }
            app.switch_screen('song_detail')
        else:
            logger.error("Не удалось переключить экран")

    def do_search(self, instance):
        """Выполняет поиск"""
        query = self.search_field.text.strip()
        if len(query) < 2:
            show_snackbar("Введите минимум 2 символа для поиска")
            return

        logger.info(f"Поиск: {query}")
        self.search_mode = True
        self.search_results(query)

    def search_results(self, query):
        """Отображает результаты поиска"""
        self.show_loading()
        api.search_songs(
            query=query,
            search_type="general",
            limit=50,
            on_success=self.on_search_results,
            on_failure=self.on_load_failed
        )

    def on_search_results(self, results):
        """Отображает результаты поиска"""
        self.hide_loading()
        self.content_container.clear_widgets()

        if not results:
            no_results_label = MDLabel(
                text="Ничего не найдено",
                halign="center",
                font_style="Body1",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(100)
            )
            self.content_container.add_widget(no_results_label)
            return

        for song in results:
            card = ResultCard(
                song={
                    'artist': song.get('artist', ''),
                    'title': song.get('title', ''),
                    'tabs_count': song.get('tabs_count', 1),
                    'song_id': song.get('song_id', 0)
                },
                on_click=self.on_search_song_selected
            )
            self.content_container.add_widget(card)

    def on_search_song_selected(self, song):
        """Обработчик выбора песни из результатов поиска"""
        logger.info(f"Выбрана песня из поиска: {song}")

        self.show_loading()
        api.get_tabs_by_song(
            artist=song['artist'],
            title=song['title'],
            on_success=lambda tabs: self.on_tabs_loaded(song, tabs),
            on_failure=self.on_load_failed
        )

    def on_load_failed(self, req, error):
        """Обработчик ошибки загрузки"""
        self.hide_loading()
        show_snackbar(f"Ошибка загрузки: {error}")
        logger.error(f"Ошибка загрузки: {error}")