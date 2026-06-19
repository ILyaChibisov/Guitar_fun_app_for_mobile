# screens/favorites_screen.py
"""
Экран избранного - список любимых песен пользователя
"""
from kivymd.app import MDApp
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
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
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

# Глобальная текстура для иконки песни
_shared_song_texture = None


def init_shared_song_icon():
    """Загружает общую иконку для всех карточек"""
    global _shared_song_texture
    if _shared_song_texture is not None:
        return _shared_song_texture

    if HAS_ASSETS:
        try:
            icon_data = load_asset_as_bytes('song_png')
            if icon_data:
                img = CoreImage(BytesIO(icon_data), ext="png")
                _shared_song_texture = img.texture
                logger.info("✅ Общая иконка песни загружена для избранного")
                return _shared_song_texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки песни: {e}")
    return None


class FavoriteSongCard(MDCard):
    """Карточка избранной песни"""

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
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.spacing = dp(10)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.08]
        self.line_color = [1, 1, 1, 0.08]
        self.line_width = 1

        self._build_ui()

    def _build_ui(self):
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        if _shared_song_texture:
            self.icon_image.texture = _shared_song_texture
        else:
            self.icon_image.text = "🎵"

        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        self.artist_label = MDLabel(
            text=self.artist,
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

        self.title_label = MDLabel(
            text=self.song_title,
            font_size=sp(11),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)

        arrow = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(28),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )

        self.add_widget(self.icon_image)
        self.add_widget(text_layout)
        self.add_widget(arrow)

        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback and self.song_id:
            self.on_click_callback(self.song_id, self.song_title)


class AuthMessageCard(MDCard):
    """Карточка сообщения для неавторизованных пользователей (в стиле аккордов)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(150)
        self.padding = [dp(20), dp(24), dp(20), dp(24)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.08]
        self.line_color = [1, 1, 1, 0.25]
        self.line_width = 1

        # Иконка
        self.icon_label = MDLabel(
            text="🔒",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        # Заголовок
        self.title_label = MDLabel(
            text="Требуется авторизация",
            font_size=sp(16),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        # Текст сообщения
        self.message_label = MDLabel(
            text="Чтобы увидеть ваши избранные треки,\nнеобходимо войти в аккаунт",
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            line_height=1.4
        )

        self.add_widget(self.icon_label)
        self.add_widget(self.title_label)
        self.add_widget(self.message_label)


class FavoritesScreen(BaseScreen):
    """Экран избранного"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'
        self.favorites = []
        self.is_loading = False
        self.bg_image = None
        self.cards_container = None
        self.count_label = None
        self._main_layout = None
        self.loading_label = None

        self.init_ui()
        self.load_background()
        Clock.schedule_once(lambda dt: init_shared_song_icon(), 0.1)

        logger.info('Экран избранного создан')

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
        """Инициализирует UI вручную"""

        # Основной контейнер
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        self._main_layout = main_layout

        # Верхний отступ
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Счётчик песен (будет скрыт для неавторизованных)
        self.count_label = MDLabel(
            text="",
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            size_hint_y=None,
            height=dp(32),
            padding=[0, dp(4), 0, dp(4)]
        )
        main_layout.add_widget(self.count_label)

        # Контейнер для карточек с отступами снизу
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )

        # ScrollView для карточек
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0]
        )

        self.cards_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(6),
            size_hint_y=None,
            adaptive_height=True
        )
        self.cards_container.bind(minimum_height=self.cards_container.setter('height'))

        scroll.add_widget(self.cards_container)
        cards_container.add_widget(scroll)
        main_layout.add_widget(cards_container)

        self.add_widget(main_layout)
        logger.info("UI избранного построен")

    def _show_auth_message(self):
        """Показывает сообщение о необходимости авторизации"""
        self.cards_container.clear_widgets()
        self.count_label.opacity = 0  # Скрываем счётчик
        auth_card = AuthMessageCard()
        self.cards_container.add_widget(auth_card)

    def _show_loading(self):
        """Показывает состояние загрузки"""
        if self.loading_label:
            return
        self.cards_container.clear_widgets()
        self.count_label.opacity = 1
        self.loading_label = MDLabel(
            text="Загрузка избранного...",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_y=None,
            height=dp(60)
        )
        self.cards_container.add_widget(self.loading_label)

    def _show_empty(self):
        """Показывает пустое состояние (нет избранных, но пользователь авторизован)"""
        self.cards_container.clear_widgets()
        self.count_label.opacity = 1
        self._update_count_label(0)

        empty_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            radius=[theme.CORNER_RADIUS_SMALL] * 4,
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            line_color=[1, 1, 1, 0.25],
            line_width=1
        )

        icon_label = MDLabel(
            text="❤️",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        text_label = MDLabel(
            text="Нет избранных песен",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            bold=True
        )

        empty_card.add_widget(icon_label)
        empty_card.add_widget(text_label)
        self.cards_container.add_widget(empty_card)

    def _clear_loading(self):
        """Убирает индикатор загрузки"""
        if self.loading_label and self.loading_label.parent:
            self.cards_container.remove_widget(self.loading_label)
        self.loading_label = None

    def _update_count_label(self, total):
        """Обновляет счётчик с правильным склонением"""
        if total == 0:
            text = "Нет избранных песен"
        elif total == 1:
            text = "1 избранная песня"
        elif 2 <= total <= 4:
            text = f"{total} избранные песни"
        else:
            text = f"{total} избранных песен"

        if self.count_label:
            self.count_label.text = text

    def load_favorites(self):
        """Загружает избранные песни"""
        self._show_loading()
        self._update_count_label(0)

        api.get_favorites(
            on_success=self.on_favorites_loaded,
            on_failure=self.on_load_failed
        )

    def on_favorites_loaded(self, favorites):
        """Обработчик успешной загрузки избранного"""
        self._clear_loading()
        self.cards_container.clear_widgets()
        self.count_label.opacity = 1

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
            self._show_empty()
            return

        self._update_count_label(len(self.favorites))

        for song_data in self.favorites:
            card = FavoriteSongCard(song=song_data, on_click=self.on_song_selected)
            self.cards_container.add_widget(card)

        bottom_spacer = Widget(size_hint_y=None, height=dp(20))
        self.cards_container.add_widget(bottom_spacer)

        logger.info(f"Загружено {len(self.favorites)} избранных песен")

    def on_load_failed(self, req, error):
        """Обработчик ошибки загрузки"""
        self._clear_loading()
        self.cards_container.clear_widgets()

        if "401" in str(error) or "Unauthorized" in str(error):
            # Не авторизован - показываем красивое сообщение
            self._show_auth_message()
            self.count_label.opacity = 0  # Скрываем счётчик
        else:
            logger.error(f"Ошибка загрузки избранного: {error}")
            self._show_empty()
            notify.error("Ошибка загрузки избранного")

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

    def on_pre_enter(self):
        """Вызывается перед входом на экран"""
        if not api.is_authenticated():
            self._show_auth_message()
            self.count_label.opacity = 0  # Скрываем счётчик
            return

        self.count_label.opacity = 1
        self.load_favorites()

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в экран избранного")
        if api.is_authenticated():
            self.load_favorites()

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана избранного")
        self._clear_loading()