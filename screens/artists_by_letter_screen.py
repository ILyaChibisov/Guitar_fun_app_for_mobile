# screens/artists_by_letter_screen.py
"""
Экран списка исполнителей по выбранной букве с бесконечной прокруткой
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

logger = screen_logger('ArtistsByLetter')

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
    """Карточка исполнителя"""

    def __init__(self, artist, songs_count=0, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.artist = artist
        self.songs_count = songs_count
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
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

        # Название исполнителя
        self.artist_label = MDLabel(
            text=artist,
            font_size=sp(15),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle"
        )

        # Количество песен
        if songs_count == 1:
            songs_text = "песня"
        elif 2 <= songs_count <= 4:
            songs_text = "песни"
        else:
            songs_text = "песен"

        self.songs_label = MDLabel(
            text=f"{songs_count} {songs_text}",
            font_size=sp(11),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_x=None,
            width=dp(60)
        )

        self.add_widget(self.icon_image)
        self.add_widget(self.artist_label)
        self.add_widget(self.songs_label)

        self.bind(on_release=self.on_click)

    def _load_icon(self):
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('artist_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки: {e}")
        self.icon_image.text = "🎸"

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.artist, self.songs_count)


class ScrollTrigger(Widget):
    """Триггер для бесконечной прокрутки"""

    def __init__(self, on_load_more, **kwargs):
        super().__init__(**kwargs)
        self.on_load_more = on_load_more
        self.size_hint_y = None
        self.height = dp(50)
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
    """Футер загрузки"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(12)
        self.md_bg_color = [0, 0, 0, 0.15]

        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            active=True,
            color=theme.PRIMARY
        )
        self.label = MDLabel(
            text="Загрузка...",
            font_size=sp(12),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        self.add_widget(self.spinner)
        self.add_widget(self.label)

    def show(self):
        self.opacity = 1
        self.disabled = False
        self.spinner.active = True

    def hide(self):
        self.opacity = 0
        self.disabled = True
        self.spinner.active = False


class ArtistsByLetterScreen(MDScreen):
    """Экран списка исполнителей по букве с пагинацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artists_by_letter'
        self.current_letter = None
        self.is_loading = False
        self.current_page = 0
        self.has_more = True
        self.total_count = 0
        self.artists_per_page = 50

        self.loading_spinner = None
        self.bg_image = None
        self.fade_layer = None
        self.footer = None
        self.scroll_trigger = None

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

        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # Верхняя панель
        self.nav_row = MDBoxLayout(
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

        self.title_label = MDLabel(
            text="",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        self.nav_row.add_widget(self.back_btn)
        self.nav_row.add_widget(self.title_label)

        # Список
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

    def show_footer(self):
        if self.footer and self.footer.parent:
            return
        self.footer = LoadingFooter()
        self.content_container.add_widget(self.footer)
        self.footer.show()

    def hide_footer(self):
        if self.footer and self.footer.parent:
            self.content_container.remove_widget(self.footer)
        self.footer = None

    def set_letter(self, letter):
        """Устанавливает букву и загружает первую страницу"""
        self.current_letter = letter
        self.title_label.text = f"Буква {letter}"
        self.current_page = 0
        self.has_more = True
        self.content_container.clear_widgets()
        self.load_artists()

    def load_artists(self, page=0):
        """Загружает страницу исполнителей"""
        offset = page * self.artists_per_page

        if page == 0:
            self.show_loading()
        else:
            self.show_footer()

        if self.current_letter == "digits" or self.current_letter == "0-9":
            api.get_artists_by_digits(
                limit=self.artists_per_page,
                offset=offset,
                on_success=lambda data: self._on_artists_loaded(data, page),
                on_failure=lambda req, err: self._on_load_failed(err, page)
            )
        else:
            api.get_artists_by_letter(
                letter=self.current_letter,
                limit=self.artists_per_page,
                offset=offset,
                on_success=lambda data: self._on_artists_loaded(data, page),
                on_failure=lambda req, err: self._on_load_failed(err, page)
            )

    def _on_artists_loaded(self, data, page):
        """Обработчик загрузки исполнителей"""
        self.hide_loading()
        self.hide_footer()

        artists = data.get('artists', [])
        self.total_count = data.get('total', 0)
        self.has_more = data.get('has_more', len(artists) == self.artists_per_page)
        self.current_page = page

        # Удаляем старый триггер если есть
        if self.scroll_trigger and self.scroll_trigger.parent:
            self.content_container.remove_widget(self.scroll_trigger)

        # Добавляем карточки
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

        # Добавляем триггер для следующей страницы
        if self.has_more:
            self.scroll_trigger = ScrollTrigger(
                on_load_more=lambda: self.load_artists(self.current_page + 1)
            )
            self.content_container.add_widget(self.scroll_trigger)
        else:
            # Добавляем нижний спейсер
            bottom_spacer = Widget(size_hint_y=None, height=dp(80))
            self.content_container.add_widget(bottom_spacer)

        logger.info(f"Загружено {len(artists)}/{self.total_count} исполнителей")

    def _on_load_failed(self, error, page):
        """Ошибка загрузки"""
        self.hide_loading()
        self.hide_footer()

        if page == 0:
            notify.error("Ошибка загрузки исполнителей")
            logger.error(f"Ошибка загрузки: {error}")

    def on_artist_selected(self, artist, songs_count):
        """Выбор исполнителя"""
        logger.info(f"Выбран исполнитель: {artist}")

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artist_songs'):
                artist_songs_screen = self.manager.get_screen('artist_songs')
                artist_songs_screen.set_artist(artist)
                self.manager.current = 'artist_songs'
            else:
                notify.info(f"Выбран исполнитель: {artist}")

    def go_back(self, instance):
        """Возврат на экран выбора буквы"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'songs'


# Импорт MDSpinner
from kivymd.uix.spinner import MDSpinner