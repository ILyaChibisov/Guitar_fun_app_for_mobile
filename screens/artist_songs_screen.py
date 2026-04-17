# screens/artist_songs_screen.py
"""
Экран списка песен выбранного исполнителя
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.uix.progressbar import ProgressBar
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('ArtistSongs')


class LoadingSpinner(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(16)

        self.progress = ProgressBar(
            size_hint=(0.8, None),
            height=dp(4),
            pos_hint={'center_x': 0.5},
            value=50,
            max=100
        )
        self.anim = None
        self.label = MDLabel(
            text="Загрузка песен...",
            halign="center",
            font_size=sp(14),
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(30)
        )
        self.add_widget(self.progress)
        self.add_widget(self.label)

    def start_animation(self):
        self.anim = Animation(value=100, duration=1) + Animation(value=0, duration=1)
        self.anim.repeat = True
        self.anim.start(self.progress)

    def stop_animation(self):
        if self.anim:
            self.anim.cancel(self.progress)
        self.progress.value = 0


class SongCard(MDCard):
    """Карточка песни"""

    def __init__(self, song, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.song = song
        self.on_click_callback = on_click

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.md_bg_color = theme.SURFACE
        self.elevation = 1

        # Название песни
        title_label = MDLabel(
            text=song['title'],
            font_size=sp(14),
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Primary",
            bold=True
        )

        # Количество подборов
        tabs_count = song.get('tabs_count', 1)
        info_label = MDLabel(
            text=f"{tabs_count} подборов" if tabs_count > 1 else "1 подбор",
            font_size=sp(11),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Hint"
        )

        self.add_widget(title_label)
        self.add_widget(info_label)

        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.song)


class ArtistSongsScreen(MDScreen):
    """Экран списка песен исполнителя"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artist_songs'
        self.artist = None
        self.songs = []
        self.is_loading = False
        self.loading_spinner = None

        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        # with self.canvas.before:
        #     Color(*rgba(theme.BACKGROUND))
        #     self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        # self.bind(pos=self._update_bg, size=self._update_bg)

        # Верхняя панель
        self.top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            padding=[dp(8), dp(8), dp(8), dp(8)],
            spacing=dp(8),
            md_bg_color=theme.PRIMARY
        )

        self.back_btn = MDIconButton(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            on_release=self.go_back
        )
        self.back_btn.icon = "arrow-left"
        self.back_btn.icon_color = [1, 1, 1, 1]
        self.back_btn.theme_icon_color = "Custom"

        self.title_label = MDLabel(
            text="",
            font_size=sp(18),
            size_hint_x=0.7,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        self.top_bar.add_widget(self.back_btn)
        self.top_bar.add_widget(self.title_label)

        # Контейнер для контента
        self.content_scroll = MDScrollView(size_hint=(1, 1))
        self.content_container = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None,
                                             adaptive_height=True)
        self.content_scroll.add_widget(self.content_container)

        # Основной layout
        self.main_layout = MDBoxLayout(orientation='vertical')
        self.main_layout.add_widget(self.top_bar)
        self.main_layout.add_widget(self.content_scroll)

        self.add_widget(self.main_layout)

        logger.info('Экран песен исполнителя создан')

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def show_loading(self):
        if self.is_loading:
            return
        self.is_loading = True
        self.content_container.clear_widgets()
        self.loading_spinner = LoadingSpinner()
        self.content_container.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
        self.content_container.clear_widgets()

    def set_artist(self, artist):
        """Устанавливает исполнителя и загружает его песни"""
        self.artist = artist
        self.title_label.text = f"🎸 {artist}"
        self.load_songs()

    def load_songs(self):
        """Загружает песни исполнителя"""
        self.show_loading()
        api.get_songs_by_artist(
            artist=self.artist,
            on_success=self.on_songs_loaded,
            on_failure=self.on_load_failed
        )

    def on_songs_loaded(self, songs):
        """Отображает список песен"""
        self.hide_loading()
        self.songs = songs
        self.content_container.clear_widgets()

        if not songs:
            no_data_label = MDLabel(
                text="Нет песен у этого исполнителя",
                halign="center",
                font_size=sp(14),
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(100)
            )
            self.content_container.add_widget(no_data_label)
            return

        for song in songs:
            card = SongCard(song=song, on_click=self.on_song_selected)
            self.content_container.add_widget(card)

        logger.info(f"Загружено {len(songs)} песен для {self.artist}")

    def on_song_selected(self, song):
        """Выбор песни - переход на экран деталей с song_id"""
        logger.info(f"Выбрана песня: {song['title']}, song_id: {song.get('song_id')}")

        if hasattr(self, 'manager') and self.manager:
            song_detail_screen = self.manager.get_screen('song_detail')
            if song_detail_screen:
                song_detail_screen.set_song(song.get('song_id'))
                self.manager.current = 'song_detail'

    def on_load_failed(self, req, error):
        """Ошибка загрузки"""
        self.hide_loading()
        notify.error(f"Ошибка загрузки: {error}")
        logger.error(f"Ошибка загрузки: {error}")

    def go_back(self, instance):
        """Возврат на экран исполнителей по букве"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'artists_by_letter'