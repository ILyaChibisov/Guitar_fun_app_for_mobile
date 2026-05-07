# screens/artists_by_letter_screen.py
"""
Экран списка исполнителей по выбранной букве - ОПТИМИЗИРОВАННЫЙ
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
from config.system_bars import get_status_bar_height
from api.client import api
from utils.notifications import notify
from utils.icon_cache import get_icon_texture

logger = screen_logger('ArtistsByLetter')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


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
            text="Загрузка исполнителей...",
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


class ArtistCard(MDCard):
    """Карточка исполнителя - использует предзагруженную иконку"""

    # СТАТИЧЕСКАЯ ТЕКСТУРА ДЛЯ ВСЕХ КАРТОЧЕК (общая)
    _shared_texture = None

    @classmethod
    def init_shared_texture(cls):
        """Один раз загружает текстуру для всех карточек"""
        if cls._shared_texture is None:
            cls._shared_texture = get_icon_texture('artist_png')
            if cls._shared_texture:
                logger.info("✅ Общая текстура иконки загружена")

    def __init__(self, artist, songs_count, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist = artist
        self.songs_count = songs_count
        self.on_click_callback = on_click

        # Инициализируем общую текстуру
        ArtistCard.init_shared_texture()

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = [dp(16), dp(8), dp(12), dp(8)]
        self.spacing = dp(12)
        self.radius = [dp(12), dp(12), dp(12), dp(12)]
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [1, 1, 1, 0.12]
        self.line_color = [0.46, 0.70, 0.71, 0.25]
        self.line_width = 1.0

        # Иконка - используем общую текстуру
        if ArtistCard._shared_texture:
            self.icon_image = Image(
                texture=ArtistCard._shared_texture,
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                pos_hint={'center_y': 0.5},
                allow_stretch=True,
                keep_ratio=True
            )
        else:
            # Заглушка если текстура не загрузилась
            self.icon_image = MDLabel(
                text="♪",
                font_size=sp(24),
                size_hint_x=None,
                width=dp(36),
                halign="center",
                theme_text_color="Custom",
                text_color=[0.46, 0.70, 0.71, 1]
            )

        # Контейнер для текста
        self.text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        # Название исполнителя
        self.artist_label = MDLabel(
            text=artist,
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

        # Количество песен
        if songs_count == 1:
            songs_word = "песня"
        elif 2 <= songs_count <= 4:
            songs_word = "песни"
        else:
            songs_word = "песен"

        self.songs_label = MDLabel(
            text=f"• {songs_count} {songs_word}",
            font_size=sp(11),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle"
        )

        self.text_container.add_widget(self.artist_label)
        self.text_container.add_widget(self.songs_label)

        # Стрелка
        self.arrow_label = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(24),
            halign="center",
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 0.5]
        )

        self.add_widget(self.icon_image)
        self.add_widget(self.text_container)
        self.add_widget(self.arrow_label)

        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.artist, self.songs_count)


class ArtistsByLetterScreen(MDScreen):
    """Экран списка исполнителей по букве"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artists_by_letter'
        self.current_letter = None
        self.is_loading = False
        self._artists_cache = {}

        self.loading_spinner = None
        self.bg_image = None
        self.fade_layer = None

        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Экран исполнителей по букве создан')

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

        status_h = get_status_bar_height()
        total_top_padding = status_h + theme.TOP_NAV_HEIGHT
        top_spacer = Widget(size_hint_y=None, height=dp(total_top_padding))
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

        top_container = FloatLayout(size_hint_y=None, height=dp(40))

        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.go_back,
            pos_hint={'x': 0, 'center_y': 0.5}
        )

        self.letter_label = MDLabel(
            text="",
            font_size=sp(22),
            halign="center",
            valign="middle",
            size_hint_x=None,
            width=dp(100),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        top_container.add_widget(self.back_btn)
        top_container.add_widget(self.letter_label)

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

        # ============ СПИСОК ИСПОЛНИТЕЛЕЙ ============
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
            padding=[dp(16), dp(8), dp(16), dp(80)]
        )
        self.scroll_view.add_widget(self.content_container)

        main_layout.add_widget(self.nav_row)
        main_layout.add_widget(self.scroll_view)

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

    def update_title(self, total):
        if self.current_letter == "digits" or self.current_letter == "0-9":
            display_letter = "0-9"
        else:
            display_letter = self.current_letter

        self.letter_label.text = display_letter

        if total == 0:
            count_text = "Найдено 0 исполнителей"
        elif total % 10 == 1 and total % 100 != 11:
            count_text = f"Найден {total} исполнитель"
        elif 2 <= total % 10 <= 4 and not (12 <= total % 100 <= 14):
            count_text = f"Найдено {total} исполнителя"
        else:
            count_text = f"Найдено {total} исполнителей"

        self.count_label.text = count_text

    def set_letter(self, letter):
        """Устанавливает букву и загружает исполнителей"""
        logger.info(f"set_letter: {letter}")

        if self.current_letter == letter and self._artists_cache.get(letter):
            self._display_artists(self._artists_cache[letter]['artists'],
                                  self._artists_cache[letter]['total'])
            return

        self.current_letter = letter
        self.load_artists()

    def load_artists(self):
        """Загружает исполнителей (сначала из кэша API, потом из API)"""
        cached_data = api.get_artists_by_letter_from_cache(self.current_letter)

        if cached_data:
            artists = cached_data.get('artists', [])
            total = cached_data.get('total', 0)
            self._artists_cache[self.current_letter] = {'artists': artists, 'total': total}
            self._display_artists(artists, total)
            return

        self.show_loading()

        if self.current_letter == "digits" or self.current_letter == "0-9":
            api.get_artists_by_digits(
                limit=200,
                offset=0,
                on_success=self._on_artists_loaded,
                on_failure=self._on_load_failed
            )
        else:
            api.get_artists_by_letter(
                letter=self.current_letter,
                limit=200,
                offset=0,
                on_success=self._on_artists_loaded,
                on_failure=self._on_load_failed
            )

    def _display_artists(self, artists, total):
        """Быстро отображает список исполнителей"""
        logger.info(f"_display_artists: {len(artists)} артистов, total={total}")

        self.update_title(total)
        self.hide_loading()

        if not artists:
            empty_label = MDLabel(
                text="Нет исполнителей на эту букву",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.5],
                size_hint_y=None,
                height=dp(60)
            )
            self.content_container.add_widget(empty_label)
            return

        # ПАКЕТНОЕ ДОБАВЛЕНИЕ КАРТОЧЕК (быстрее)
        for artist_data in artists:
            artist_name = artist_data.get('artist')
            songs_count = artist_data.get('songs_count', 0)
            if artist_name:
                card = ArtistCard(
                    artist=artist_name,
                    songs_count=songs_count,
                    on_click=self.on_artist_selected
                )
                self.content_container.add_widget(card)

        logger.info(f"Отображено {len(artists)} исполнителей для буквы {self.current_letter}")

    def _on_artists_loaded(self, data):
        """Обработчик загрузки из API"""
        artists = data.get('artists', [])
        total = data.get('total', 0)
        self._artists_cache[self.current_letter] = {'artists': artists, 'total': total}
        self._display_artists(artists, total)

    def _on_load_failed(self, req, error):
        """Обработчик ошибки загрузки"""
        self.hide_loading()
        logger.error(f"Ошибка загрузки: {error}")

        error_label = MDLabel(
            text="Ошибка загрузки исполнителей. Проверьте интернет.",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 1],
            size_hint_y=None,
            height=dp(60)
        )
        self.content_container.add_widget(error_label)

    def on_artist_selected(self, artist, songs_count):
        """Выбор исполнителя"""
        logger.info(f"Выбран исполнитель: {artist}")

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artist_songs'):
                artist_songs_screen = self.manager.get_screen('artist_songs')
                artist_songs_screen.set_artist(artist)
                self.manager.current = 'artist_songs'

    def go_back(self, instance):
        """Возврат на экран выбора буквы"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'songs'