# screens/artist_songs_screen.py
"""
Экран списка песен выбранного исполнителя
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('ArtistSongs')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


    logger.warning("Модуль data не найден")


class LoadingSpinner(MDBoxLayout):
    """Индикатор загрузки"""

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
    """Красивая полупрозрачная карточка песни"""

    def __init__(self, song, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.song_id = song.get('song_id')
        self.song_title = song.get('title', '')
        self.tabs_count = song.get('tabs_count', 1)
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(70)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.elevation = 2
        self.ripple_behavior = True

        # Устанавливаем полупрозрачный фон
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.15]
        self.line_color = [1, 1, 1, 0.1]
        self.line_width = 1

        # Иконка песни из ассетов
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        # Контейнер для текстовой информации
        self.text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(4)
        )

        # Название песни
        self.title_label = MDLabel(
            text=self.song_title,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle"
        )

        # Количество подборов (с правильным склонением)
        if self.tabs_count % 10 == 1 and self.tabs_count % 100 != 11:
            tabs_word = "подбор"
        elif 2 <= self.tabs_count % 10 <= 4 and not (12 <= self.tabs_count % 100 <= 14):
            tabs_word = "подбора"
        else:
            tabs_word = "подборов"

        self.tabs_label = MDLabel(
            text=f"{self.tabs_count} {tabs_word}",
            font_size=sp(12),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            valign="middle"
        )

        self.text_container.add_widget(self.title_label)
        self.text_container.add_widget(self.tabs_label)

        # Стрелка вправо
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
        """Загружает иконку из ассетов"""
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('song_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки song_png: {e}")

        self.icon_image.text = "🎵"

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback({'song_id': self.song_id, 'title': self.song_title})


class ArtistSongsScreen(MDScreen):
    """Экран списка песен исполнителя"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artist_songs'
        self.artist = None
        self.songs = []
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.fade_layer = None
        self._showing_from_cache = False

        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Экран песен исполнителя создан')

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

    def init_ui(self):
        root_layout = FloatLayout()

        main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0
        )

        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # ============ СТРОКА: стрелка и название исполнителя ============
        self.nav_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(8),
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

        self.artist_title = MDLabel(
            text="",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        self.nav_row.add_widget(self.back_btn)
        self.nav_row.add_widget(self.artist_title)

        # ============ СПИСОК ПЕСЕН ============
        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_color=[1, 1, 1, 0.3],
            bar_width=dp(4)
        )

        self.content_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(12), dp(16), dp(20)]
        )
        self.content_scroll.add_widget(self.content_container)

        main_layout.add_widget(self.nav_row)
        main_layout.add_widget(self.content_scroll)

        # ============ ПРОЗРАЧНЫЙ СЛОЙ НАД НИЖНЕЙ НАВИГАЦИЕЙ ============
        self.fade_layer = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(80),
            pos_hint={'x': 0, 'y': 0},
            md_bg_color=[0, 0, 0, 0]
        )

        with self.fade_layer.canvas.before:
            Color(0, 0, 0, 0.6)
            self.fade_rect = Rectangle(pos=self.fade_layer.pos, size=self.fade_layer.size)

        self.fade_layer.bind(pos=self._update_fade, size=self._update_fade)

        root_layout.add_widget(main_layout)
        root_layout.add_widget(self.fade_layer)

        self.add_widget(root_layout)
        self.root_layout = root_layout

    def _update_fade(self, *args):
        if hasattr(self, 'fade_rect'):
            self.fade_rect.pos = self.fade_layer.pos
            self.fade_rect.size = self.fade_layer.size

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
            self.loading_spinner = None
        self.content_container.clear_widgets()

    def set_artist(self, artist):
        """Устанавливает исполнителя и загружает его песни"""
        self.artist = artist
        self.artist_title.text = artist

        # Сначала пробуем показать из кэша
        cached_songs = api.get_cached_songs_by_artist(artist)
        if cached_songs:
            logger.info(f"📦 Показываем песни исполнителя {artist} из кэша")
            self._showing_from_cache = True
            self.on_songs_loaded(cached_songs)
            # В фоне обновляем данные
            self.load_songs(force_refresh=True)
        else:
            self._showing_from_cache = False
            self.load_songs()

    def load_songs(self, force_refresh=False):
        """Загружает песни исполнителя"""
        self.show_loading()

        api.get_songs_by_artist(
            artist=self.artist,
            on_success=self.on_songs_loaded,
            on_failure=self.on_load_failed,
            force_refresh=force_refresh
        )

    def on_songs_loaded(self, songs):
        """Отображает список песен"""
        self.hide_loading()
        self._showing_from_cache = False
        self.songs = songs

        if not songs or len(songs) == 0:
            self._show_empty_state()
            return

        # Отображаем карточки песен
        for song_data in songs:
            card = SongCard(song=song_data, on_click=self.on_song_selected)
            self.content_container.add_widget(card)

        # Добавляем нижний спейсер
        bottom_spacer = Widget(size_hint_y=None, height=dp(80))
        self.content_container.add_widget(bottom_spacer)

        logger.info(f"Загружено {len(songs)} песен для {self.artist}")

    def _show_empty_state(self):
        """Показывает пустое состояние"""
        empty_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(160),
            padding=[dp(24), dp(24), dp(24), dp(24)],
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        icon_label = MDLabel(
            text="🎵",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        text_label = MDLabel(
            text="Нет песен у этого исполнителя",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_y=None,
            height=dp(40),
            bold=True
        )

        hint_label = MDLabel(
            text="Попробуйте выбрать другого исполнителя",
            halign="center",
            font_size=sp(12),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            size_hint_y=None,
            height=dp(30)
        )

        empty_card.add_widget(icon_label)
        empty_card.add_widget(text_label)
        empty_card.add_widget(hint_label)
        self.content_container.add_widget(empty_card)

    def on_song_selected(self, song_info):
        """Выбор песни - переход на экран деталей"""
        song_id = song_info.get('song_id')
        song_title = song_info.get('title', '')

        logger.info(f"Выбрана песня: {song_title}, song_id: {song_id}")

        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                if hasattr(song_detail_screen, 'set_song') and hasattr(song_detail_screen, 'set_previous_screen'):
                    song_detail_screen.set_previous_screen('artist_songs')
                    song_detail_screen.set_song(song_id)
                    self.manager.current = 'song_detail'
                elif hasattr(song_detail_screen, 'set_song'):
                    song_detail_screen.set_song(song_id)
                    self.manager.current = 'song_detail'
                else:
                    notify.info(f"Выбрана песня: {song_title}")
            else:
                notify.info(f"Выбрана песня: {song_title}")

    def on_load_failed(self, req, error):
        """Ошибка загрузки"""
        self.hide_loading()

        # Если показывали из кэша, просто показываем ошибку в лог
        if self._showing_from_cache:
            logger.warning(f"Ошибка обновления песен для {self.artist}: {error}")
        else:
            notify.error(f"Ошибка загрузки: {error}")
            logger.error(f"Ошибка загрузки: {error}")
            self._show_error_state()

    def _show_error_state(self):
        """Показывает состояние ошибки"""
        error_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(160),
            padding=[dp(24), dp(24), dp(24), dp(24)],
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        icon_label = MDLabel(
            text="⚠️",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=[1, 0.5, 0.3, 0.9]
        )

        text_label = MDLabel(
            text="Ошибка загрузки",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_y=None,
            height=dp(40),
            bold=True
        )

        hint_label = MDLabel(
            text="Проверьте подключение к интернету",
            halign="center",
            font_size=sp(12),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            size_hint_y=None,
            height=dp(30)
        )

        error_card.add_widget(icon_label)
        error_card.add_widget(text_label)
        error_card.add_widget(hint_label)
        self.content_container.add_widget(error_card)

    def go_back(self, instance):
        """Возврат на экран исполнителей по букве"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'artists_by_letter'