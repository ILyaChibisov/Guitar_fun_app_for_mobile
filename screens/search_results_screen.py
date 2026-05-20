# screens/search_results_screen.py
"""
Экран результатов поиска - переведён на BaseScreen
"""
from kivymd.uix.label import MDLabel
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
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('SearchResults')

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
            text="Поиск...",
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


class SearchResultCard(MDCard):
    def __init__(self, song, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.song = song
        self.song_id = song.get('song_id', 0)
        self.artist = song.get('artist', '')
        self.title = song.get('title', '')
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.elevation = 2
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.15]
        self.line_color = [1, 1, 1, 0.1]
        self.line_width = 1

        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        self.text_container = MDBoxLayout(orientation='vertical', size_hint_x=1, spacing=dp(2))

        self.artist_label = MDLabel(
            text=self.artist,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        self.title_label = MDLabel(
            text=self.title,
            font_size=sp(14),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        self.text_container.add_widget(self.artist_label)
        self.text_container.add_widget(self.title_label)

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
            self.on_click_callback(self.song_id, self.title)


class SearchResultsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search_results'
        self.query = None
        self.results = []
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None

        self.init_ui()
        self.load_background()

        logger.info('Экран результатов поиска создан (BaseScreen)')

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
        # Получаем единые боковые отступы из layout_config
        content_padding = layout_config.get_content_padding()
        # content_padding = [left, top, right, bottom]

        # Верхняя панель
        top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[content_padding[0], dp(8), content_padding[2], dp(8)],  # left и right из layout_config
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

        self.search_icon = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.9],
            md_bg_color=[0, 0, 0, 0],
            disabled=True
        )

        self.info_label = MDLabel(
            text="",
            font_size=sp(14),
            halign="left",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True,
            shorten=True,
            shorten_from="right"
        )

        top_bar.add_widget(self.back_btn)
        top_bar.add_widget(self.search_icon)
        top_bar.add_widget(self.info_label)

        # Контент - с едиными отступами
        self.content_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[content_padding[0], dp(8), content_padding[2], content_padding[3]]  # все отступы из layout_config
        )

        # Строим UI
        self.build_ui(content_widget=self.content_container, top_widget=top_bar, use_scroll=True)

        logger.info(f"SearchResultsScreen: side_padding = {content_padding[0]}dp")

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

    def update_info_label(self, count):
        if count == 0:
            self.info_label.text = f"«{self.query}» — не найдено"
        elif count == 1:
            self.info_label.text = f"«{self.query}» — найдена 1 песня"
        elif 2 <= count <= 4:
            self.info_label.text = f"«{self.query}» — найдено {count} песни"
        else:
            self.info_label.text = f"«{self.query}» — найдено {count} песен"

    def display_results(self):
        self.content_container.clear_widgets()

        if not self.results:
            empty_card = MDCard(
                orientation='vertical',
                size_hint=(1, None),
                height=dp(180),
                padding=[dp(24), dp(24), dp(24), dp(24)],
                radius=[theme.CORNER_RADIUS_SMALL],
                md_bg_color=[0, 0, 0, 0.15],
                elevation=2
            )

            icon_label = MDLabel(
                text="🔍",
                font_size=sp(48),
                halign="center",
                size_hint_y=None,
                height=dp(60),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.7]
            )

            text_label = MDLabel(
                text="Ничего не найдено",
                halign="center",
                font_size=sp(16),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.9],
                size_hint_y=None,
                height=dp(40),
                bold=True
            )

            hint_label = MDLabel(
                text="Попробуйте изменить поисковый запрос",
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
            return

        for song in self.results:
            card = SearchResultCard(song=song, on_click=self.on_song_selected)
            self.content_container.add_widget(card)

        bottom_spacer = Widget(size_hint_y=None, height=dp(20))
        self.content_container.add_widget(bottom_spacer)

    def do_search(self, query):
        self.query = query
        self.update_info_label(0)
        self.show_loading()

        api.search_songs(
            query=query,
            limit=50,
            on_success=self.on_search_success,
            on_failure=self.on_search_failed
        )

    def on_search_success(self, results):
        if isinstance(results, dict):
            raw_results = results.get('results', [])
        elif isinstance(results, list):
            raw_results = results
        else:
            raw_results = []

        formatted_results = []
        for item in raw_results:
            if isinstance(item, dict):
                formatted_results.append({
                    'song_id': item.get('song_id', 0),
                    'artist': item.get('artist', ''),
                    'title': item.get('title', '')
                })

        self.results = formatted_results
        self.hide_loading()
        self.update_info_label(len(self.results))
        self.display_results()
        logger.info(f"Найдено {len(self.results)} результатов для '{self.query}'")

    def on_search_failed(self, req, error):
        self.results = []
        self.hide_loading()
        self.update_info_label(0)
        self.display_results()
        notify.error(f"Ошибка поиска: {error}")
        logger.error(f"Ошибка поиска: {error}")

    def on_song_selected(self, song_id, title):
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail = self.manager.get_screen('song_detail')
                song_detail.set_previous_screen('search_results')
                song_detail.set_song(song_id)
                self.manager.current = 'song_detail'

    def go_back(self, instance):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'songs'

    def on_pre_enter(self, *args):
        if self.results:
            self.update_info_label(len(self.results))
            self.display_results()
        elif self.query:
            self.update_info_label(0)
            self.display_results()
        return super().on_pre_enter()