# screens/artists_by_letter_screen.py
"""
Экран списка исполнителей по выбранной букве
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from kivy.animation import Animation
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify
from utils.kivy_imports import MDIconButton, MDBoxLayout, MDProgressBar

logger = screen_logger('ArtistsByLetter')


class LoadingSpinner(MDBoxLayout):
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
            text="Загрузка исполнителей...",
            halign="center",
            font_style="Body1",
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


class ArtistCard(MDCard):
    """Карточка исполнителя"""

    def __init__(self, artist, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist = artist
        self.on_click_callback = on_click

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.padding = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.md_bg_color = theme.SURFACE
        self.elevation = 1

        artist_label = MDLabel(
            text=f"🎸 {artist}",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(32),
            theme_text_color="Primary",
            bold=True
        )
        self.add_widget(artist_label)
        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.artist)


class ArtistsByLetterScreen(MDScreen):
    """Экран списка исполнителей по букве"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artists_by_letter'
        self.current_letter = None
        self.is_loading = False
        self.loading_spinner = None

        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

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
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=self.go_back
        )

        self.title_label = MDLabel(
            text="",
            font_style="H6",
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

        logger.info('Экран исполнителей по букве создан')

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

    def set_letter(self, letter):
        """Устанавливает букву и загружает исполнителей"""
        self.current_letter = letter
        self.title_label.text = f"📋 Исполнители на букву {letter}"
        self.load_artists()

    def load_artists(self):
        """Загружает исполнителей по букве/цифре"""
        self.show_loading()

        letter = self.current_letter

        api.get_artists_by_letter(
            letter=letter,
            on_success=self.on_artists_loaded,
            on_failure=self.on_load_failed
        )

    def on_artists_loaded(self, artists):
        """Отображает список исполнителей"""
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
                card = ArtistCard(artist=artist, on_click=self.on_artist_selected)
                self.content_container.add_widget(card)

        logger.info(f"Загружено {len(artists)} исполнителей на букву {self.current_letter}")

    def on_artist_selected(self, artist):
        """Выбор исполнителя - переход на экран его песен"""
        logger.info(f"Выбран исполнитель: {artist}")

        if hasattr(self, 'manager') and self.manager:
            artist_songs_screen = self.manager.get_screen('artist_songs')
            if artist_songs_screen:
                artist_songs_screen.set_artist(artist)
                self.manager.current = 'artist_songs'

    def on_load_failed(self, req, error):
        """Ошибка загрузки"""
        self.hide_loading()
        notify.error(f"Ошибка загрузки: {error}")
        logger.error(f"Ошибка загрузки: {error}")

    def go_back(self, instance):
        """Возврат на экран песен (с алфавитом)"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'songs'