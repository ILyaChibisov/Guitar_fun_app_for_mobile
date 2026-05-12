# screens/favorites_screen.py
"""
Экран избранного - список любимых песен пользователя - переведён на BaseScreen
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
from kivy.clock import Clock
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('Favorites')

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
            text="Загрузка избранного...",
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


class FavoriteSongCard(MDCard):
    def __init__(self, song, on_click=None, **kwargs):
        super().__init__(**kwargs)

        if isinstance(song, dict):
            self.song_id = song.get('id') or song.get('song_id')
            self.song_title = song.get('title', '')
            self.artist = song.get('artist', '')
        elif isinstance(song, str):
            parts = song.split(' - ', 1)
            if len(parts) == 2:
                self.artist, self.song_title = parts[0], parts[1]
            else:
                self.artist, self.song_title = '', song
            self.song_id = 0
        else:
            self.song_id = 0
            self.song_title = ''
            self.artist = ''

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
            text=self.song_title,
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
        if self.on_click_callback and self.song_id:
            self.on_click_callback(self.song_id, self.song_title)


class FavoritesScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'
        self.favorites = []
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.fade_layer = None

        self.init_ui()
        self.load_background()

        logger.info('Экран избранного создан (BaseScreen)')

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
        # Верхняя панель
        top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(12),
            md_bg_color=[0, 0, 0, 0]
        )

        title = MDLabel(
            text="Избранное",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )
        top_bar.add_widget(title)

        # Контент
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(12), dp(16), dp(20)]
        )

        self.content_container = content

        # Счётчик
        self.count_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        # Строим UI
        self.build_ui(content_widget=content, top_widget=top_bar, use_scroll=True)
        self.add_content_widget(self.count_label, index=1)

    def show_loading_state(self):
        self.is_loading = True
        self.content_container.clear_widgets()
        self.loading_spinner = LoadingSpinner()
        self.content_container.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()
        self.count_label.text = ""

    def hide_loading_state(self):
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
        self.content_container.clear_widgets()

    def on_pre_enter(self):
        if not api.is_authenticated():
            self.show_empty_state(is_authenticated=False)
            return
        self.load_favorites()

    def load_favorites(self):
        self.show_loading_state()
        api.get_favorites(
            on_success=self.on_favorites_loaded,
            on_failure=self.on_load_failed
        )

    def on_favorites_loaded(self, favorites):
        self.hide_loading_state()

        formatted_favorites = []
        for item in favorites:
            if isinstance(item, dict):
                formatted_favorites.append(item)
            elif isinstance(item, str):
                parts = item.split(' - ', 1)
                if len(parts) == 2:
                    formatted_favorites.append({'artist': parts[0], 'title': parts[1], 'id': 0})
                else:
                    formatted_favorites.append({'artist': '', 'title': item, 'id': 0})

        self.favorites = formatted_favorites

        if not self.favorites:
            self.show_empty_state()
            self.count_label.text = "0 песен"
            return

        total = len(self.favorites)
        if total == 1:
            self.count_label.text = "1 песня"
        elif 2 <= total <= 4:
            self.count_label.text = f"{total} песни"
        else:
            self.count_label.text = f"{total} песен"

        for song_data in self.favorites:
            card = FavoriteSongCard(song=song_data, on_click=self.on_song_selected)
            self.content_container.add_widget(card)

        bottom_spacer = Widget(size_hint_y=None, height=dp(20))
        self.content_container.add_widget(bottom_spacer)
        logger.info(f"Загружено {len(self.favorites)} избранных песен")

    def show_empty_state(self, is_authenticated=True):
        self.hide_loading_state()
        self.content_container.clear_widgets()

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
            text="❤️" if is_authenticated else "🔒",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        if is_authenticated:
            text_label = MDLabel(
                text="Нет избранных песен",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.8],
                size_hint_y=None,
                height=dp(40),
                bold=True
            )
            hint_label = MDLabel(
                text="Добавляйте песни в избранное\nиз карточки песни",
                halign="center",
                font_size=sp(12),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.5],
                size_hint_y=None,
                height=dp(50),
                markup=True
            )
        else:
            text_label = MDLabel(
                text="Требуется авторизация",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.8],
                size_hint_y=None,
                height=dp(40),
                bold=True
            )
            hint_label = MDLabel(
                text="Войдите в аккаунт, чтобы\nвидеть избранные песни",
                halign="center",
                font_size=sp(12),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.5],
                size_hint_y=None,
                height=dp(50),
                markup=True
            )

        empty_card.add_widget(icon_label)
        empty_card.add_widget(text_label)
        empty_card.add_widget(hint_label)
        self.content_container.add_widget(empty_card)
        self.count_label.text = "0 песен"

    def on_song_selected(self, song_id, song_title):
        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                song_detail_screen.set_previous_screen('favorites')
                song_detail_screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def on_load_failed(self, req, error):
        self.hide_loading_state()
        if "401" in str(error) or "Unauthorized" in str(error):
            notify.warning("Сессия истекла. Пожалуйста, войдите снова.")
            if hasattr(self, 'manager') and self.manager:
                self.manager.current = 'home'
        else:
            logger.error(f"Ошибка загрузки избранного: {error}")
            self.show_empty_state()