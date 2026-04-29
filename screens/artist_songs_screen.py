# screens/artist_songs_screen.py
"""
Экран списка песен выбранного исполнителя с бесконечной прокруткой
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
from kivy.clock import Clock
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


class ScrollTrigger(Widget):
    """Триггер для бесконечной прокрутки (невидимый)"""

    def __init__(self, on_load_more, **kwargs):
        super().__init__(**kwargs)
        self.on_load_more = on_load_more
        self.size_hint_y = None
        self.height = dp(20)
        self.opacity = 0
        self.loading = False
        self.scroll_view = None

    def on_parent(self, instance, parent):
        if parent and hasattr(parent, 'parent'):
            self.scroll_view = parent.parent
            if self.scroll_view:
                self.scroll_view.bind(scroll_y=self._check_scroll)

    def _check_scroll(self, instance, value):
        if value < 0.05 and not self.loading:
            self.loading = True
            Clock.schedule_once(lambda dt: self.on_load_more(), 0.1)

    def reset_loading(self):
        self.loading = False


class LoadingFooter(MDBoxLayout):
    """Футер загрузки (невидимый)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(20)
        self.opacity = 0
        self.md_bg_color = [0, 0, 0, 0]

    def show(self):
        pass

    def hide(self):
        pass


class SongCard(MDCard):
    """Карточка песни (только название, без количества подборов)"""

    def __init__(self, song, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.song_id = song.get('song_id')
        self.song_title = song.get('title', '')
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(55)
        self.padding = [dp(12), dp(6), dp(12), dp(6)]
        self.spacing = dp(10)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.elevation = 2
        self.ripple_behavior = True

        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.15]
        self.line_color = [1, 1, 1, 0.1]
        self.line_width = 1

        # Иконка
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        # Название песни (одна строка)
        self.title_label = MDLabel(
            text=self.song_title,
            font_size=sp(15),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        # Стрелка вправо
        self.arrow_label = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(28),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        self.add_widget(self.icon_image)
        self.add_widget(self.title_label)
        self.add_widget(self.arrow_label)

        self.bind(on_release=self.on_click)

    def _load_icon(self):
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('song_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки: {e}")
        self.icon_image.text = "🎵"

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.song_id, self.song_title)


class ArtistSongsScreen(MDScreen):
    """Экран списка песен исполнителя с пагинацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artist_songs'
        self.current_artist = None
        self.is_loading = False
        self.current_page = 0
        self.has_more = True
        self.total_count = 0
        self.songs_per_page = 50

        self.loading_spinner = None
        self.bg_image = None
        self.fade_layer = None
        self.footer = None
        self.scroll_trigger = None

        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Экран песен исполнителя создан')

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

    def init_ui(self):
        root_layout = FloatLayout()

        main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0
        )

        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # ============ ВЕРХНЯЯ ПАНЕЛЬ ============
        self.nav_row = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(70),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0]
        )

        # Контейнер для верхней строки с абсолютным позиционированием
        top_container = FloatLayout(size_hint_y=None, height=dp(36))

        # Кнопка назад (фиксированная позиция слева)
        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.go_back,
            pos_hint={'x': 0, 'center_y': 0.5}
        )

        # Центрированное название исполнителя
        self.artist_label = MDLabel(
            text="",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint_x=None,
            width=dp(250),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            shorten=True,
            shorten_from="right",
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        top_container.add_widget(self.back_btn)
        top_container.add_widget(self.artist_label)

        # Вторая строка: количество песен
        self.count_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        self.nav_row.add_widget(top_container)
        self.nav_row.add_widget(self.count_label)

        # ============ СПИСОК ПЕСЕН ============
        self.scroll_view = MDScrollView(
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
        self.scroll_view.add_widget(self.content_container)

        main_layout.add_widget(self.nav_row)
        main_layout.add_widget(self.scroll_view)

        # Затемнение
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

    def update_title(self, total):
        """Обновляет заголовок: название исполнителя и количество песен"""
        self.artist_label.text = self.current_artist if self.current_artist else ""

        if total == 0:
            count_text = "Найдено песен: 0"
        elif total == 1:
            count_text = "Найдена 1 песня"
        elif 2 <= total <= 4:
            count_text = f"Найдено {total} песни"
        else:
            count_text = f"Найдено {total} песен"

        self.count_label.text = count_text

    def set_artist(self, artist):
        """Устанавливает исполнителя и загружает первую страницу"""
        self.current_artist = artist
        self.current_page = 0
        self.has_more = True
        self.content_container.clear_widgets()
        self.update_title(0)
        self.load_songs()

    def load_songs(self, page=0):
        """Загружает страницу песен"""
        offset = page * self.songs_per_page

        if page == 0:
            self.show_loading()

        api.get_songs_by_artist(
            artist=self.current_artist,
            limit=self.songs_per_page,
            offset=offset,
            on_success=lambda data: self._on_songs_loaded(data, page),
            on_failure=lambda req, err: self._on_load_failed(err, page)
        )

    def _on_songs_loaded(self, data, page):
        """Обработчик загрузки песен"""
        songs = data.get('songs', [])
        total = data.get('total', 0)
        self.has_more = data.get('has_more', len(songs) == self.songs_per_page)
        self.current_page = page
        self.total_count = total

        self.update_title(total)

        if page == 0:
            self.hide_loading()
            self.content_container.clear_widgets()
        else:
            if self.scroll_trigger and self.scroll_trigger.parent:
                self.content_container.remove_widget(self.scroll_trigger)

        for song_data in songs:
            card = SongCard(song=song_data, on_click=self.on_song_selected)
            self.content_container.add_widget(card)

        if self.has_more:
            self.scroll_trigger = ScrollTrigger(
                on_load_more=lambda: self.load_songs(self.current_page + 1)
            )
            self.content_container.add_widget(self.scroll_trigger)
        else:
            bottom_spacer = Widget(size_hint_y=None, height=dp(80))
            self.content_container.add_widget(bottom_spacer)

        logger.info(f"Загружено {len(songs)}/{total} песен для {self.current_artist}")

    def _on_load_failed(self, error, page):
        """Ошибка загрузки"""
        if page == 0:
            self.hide_loading()
            notify.error("Ошибка загрузки песен")
            logger.error(f"Ошибка загрузки: {error}")

    def on_song_selected(self, song_id, song_title):
        """Выбор песни"""
        logger.info(f"Выбрана песня: {song_title}, id: {song_id}")

        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                song_detail_screen.set_previous_screen('artist_songs')
                song_detail_screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def go_back(self, instance):
        """Возврат на экран исполнителей"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'artists_by_letter'