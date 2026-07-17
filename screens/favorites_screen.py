# screens/favorites_screen.py
"""
Экран избранного - список любимых песен пользователя
СТАТИЧНЫЙ ЗАГОЛОВОК В TopNav: "Избранное"
Количество песен показывается на самом экране
Карточки как были - исполнитель + название в две строки
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
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
from screens.base_screen import BaseScreen
from screens.components.loading_spinner import LoadingSpinner
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state

logger = screen_logger('Favorites')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None

# ============ ГЛОБАЛЬНАЯ ТЕКСТУРА ============
_shared_song_texture = None


def init_shared_song_icon():
    global _shared_song_texture
    if _shared_song_texture is not None:
        return _shared_song_texture

    if HAS_ASSETS:
        try:
            icon_data = load_asset_as_bytes('song_png')
            if icon_data:
                img = CoreImage(BytesIO(icon_data), ext="png")
                _shared_song_texture = img.texture
                logger.info("✅ Общая иконка песни загружена")
                return _shared_song_texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки: {e}")
    return None


# ============ КАРТОЧКА ИЗБРАННОЙ ПЕСНИ (ОРИГИНАЛЬНЫЙ ДИЗАЙН) ============
class FavoriteSongCard(MDCard):
    """Карточка избранной песни - исполнитель + название в две строки"""

    _shared_texture = None

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
        self.height = dp(56)
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.spacing = dp(10)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self.clip = True

        self._build_ui()

    def _build_ui(self):
        # Иконка песни
        self.icon_image = Image(
            size_hint=(None, 1),
            width=dp(28),
            allow_stretch=True,
            keep_ratio=True
        )

        if FavoriteSongCard._shared_texture:
            self.icon_image.texture = FavoriteSongCard._shared_texture
        else:
            FavoriteSongCard._shared_texture = init_shared_song_icon()
            if FavoriteSongCard._shared_texture:
                self.icon_image.texture = FavoriteSongCard._shared_texture
            else:
                self.icon_image.text = "🎵"

        # Текстовый блок - исполнитель и название в две строки
        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        # Исполнитель - жирный, крупный
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

        # Название песни - мелкий, серый
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

        # Стрелка
        arrow = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(28),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon_image)
        self.add_widget(text_layout)
        self.add_widget(arrow)

        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback and self.song_id:
            self.on_click_callback(self.song_id, self.song_title)


# ============ КАРТОЧКА АВТОРИЗАЦИИ ============
class AuthMessageCard(MDCard):
    """Карточка сообщения для неавторизованных пользователей"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(140)
        self.padding = [dp(20), dp(20), dp(20), dp(20)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.5
        self.clip = True

        self.icon_label = MDLabel(
            text="🔒",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(56),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

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


# ============ ОСНОВНОЙ ЭКРАН ============
class FavoritesScreen(BaseScreen):
    """Экран избранного - СТАТИЧНЫЙ ЗАГОЛОВОК В TopNav"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'
        self.favorites = []
        self.is_loading = False
        self.bg_image = None
        self.cards_container = None
        self._main_layout = None
        self.loading_spinner = None
        self._top_spacer = None
        self._last_load_time = 0
        self._top_nav_updated = False
        self._pending_refresh = False
        self.count_label = None

        self.init_ui()
        self.load_background()

        Clock.schedule_once(lambda dt: init_shared_song_icon(), 0.05)
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
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        self._main_layout = main_layout

        top_padding = layout_config.get_top_padding()
        top_padding = top_padding - dp(8)
        if top_padding < dp(20):
            top_padding = dp(20)

        self._top_spacer = Widget(size_hint_y=None, height=top_padding)
        main_layout.add_widget(self._top_spacer)

        # ============ КОЛИЧЕСТВО ПЕСЕН НА ЭКРАНЕ ============
        self.count_label = MDLabel(
            text="",
            font_size=sp(13),
            halign="center",
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            opacity=0,
            bold=True
        )
        main_layout.add_widget(self.count_label)

        # ============ КАРТОЧКИ ============
        bottom_padding = layout_config.get_bottom_padding()

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), bottom_padding]
        )
        cards_container.clip = True

        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0]
        )
        scroll.clip = True

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
        logger.info(f"UI избранного построен, bottom_padding={bottom_padding}dp")

    def _update_top_nav(self):
        """Обновляет TopNav - форсированно и мгновенно"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            # ✅ Используем форсированное обновление
            app.top_nav.force_update_title("Избранное", show_back=False)
            self._top_nav_updated = True
            logger.info("✅ TopNav форсированно обновлён: Избранное")

    def _update_count_label(self, total):
        """Обновляет лейбл с количеством песен на экране"""
        if self.count_label:
            if total == 0:
                self.count_label.text = "Нет песен"
            elif total == 1:
                self.count_label.text = "1 песня"
            elif 2 <= total <= 4:
                self.count_label.text = f"{total} песни"
            else:
                self.count_label.text = f"{total} песен"
            self.count_label.opacity = 1
            logger.info(f"✅ Количество песен обновлено: {total}")

    def _show_auth_message(self):
        self.cards_container.clear_widgets()
        auth_card = AuthMessageCard()
        self.cards_container.add_widget(auth_card)
        self._update_top_nav()
        self.count_label.opacity = 0

    def _show_loading(self):
        if self.loading_spinner:
            return

        self.cards_container.clear_widgets()
        self.loading_spinner = LoadingSpinner(text="Загрузка избранного...")
        self.loading_spinner.start_animation()

        if self._main_layout:
            if self.loading_spinner.parent:
                self.loading_spinner.parent.remove_widget(self.loading_spinner)
            index = self._main_layout.children.index(self._top_spacer) + 1
            self._main_layout.add_widget(self.loading_spinner, index)

        self.count_label.opacity = 0

    def _hide_loading(self):
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            if self.loading_spinner.parent:
                self.loading_spinner.parent.remove_widget(self.loading_spinner)
        self.loading_spinner = None

    def _show_empty(self):
        self.cards_container.clear_widgets()
        self._update_top_nav()
        self._update_count_label(0)

        empty_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            radius=[theme.CORNER_RADIUS_SMALL] * 4,
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.15],
            line_width=0.5
        )

        icon_label = MDLabel(
            text="❤️",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(56),
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

    def load_favorites(self, force_refresh=False):
        """Загружает избранные песни"""
        if not api.is_authenticated():
            self._show_auth_message()
            return

        if self.favorites and not force_refresh:
            logger.info(f"📦 Показываем кэшированное избранное: {len(self.favorites)} песен")
            self._show_favorites(self.favorites)
            return

        self._show_loading()
        self._update_top_nav()

        api.get_favorites(
            on_success=self.on_favorites_loaded,
            on_failure=self.on_load_failed,
            force_refresh=force_refresh
        )

    def refresh_favorites(self):
        """Принудительно обновляет избранное с сервера"""
        logger.info("🔄 Принудительное обновление избранного")
        self._pending_refresh = True
        self.load_favorites(force_refresh=True)

    def on_favorites_loaded(self, favorites):
        """Обработчик успешной загрузки избранного"""
        self._hide_loading()
        self._pending_refresh = False

        formatted_favorites = []
        for item in favorites:
            if isinstance(item, dict):
                if 'id' in item and 'song_id' not in item:
                    item['song_id'] = item['id']
                formatted_favorites.append(item)
            elif isinstance(item, str):
                parts = item.split(' - ', 1)
                if len(parts) == 2:
                    formatted_favorites.append({
                        'artist': parts[0],
                        'title': parts[1],
                        'id': 0,
                        'song_id': 0
                    })
                else:
                    formatted_favorites.append({
                        'artist': '',
                        'title': item,
                        'id': 0,
                        'song_id': 0
                    })

        self.favorites = formatted_favorites

        screen_state.cache_screen_data('favorites', formatted_favorites)
        self._last_load_time = 0

        self._show_favorites(formatted_favorites)

    def _show_favorites(self, favorites):
        """Отображает список избранных песен"""
        self.cards_container.clear_widgets()

        if not favorites:
            self._show_empty()
            return

        self._update_top_nav()
        self._update_count_label(len(favorites))

        for song_data in favorites:
            card = FavoriteSongCard(song=song_data, on_click=self.on_song_selected)
            self.cards_container.add_widget(card)

        bottom_spacer = Widget(size_hint_y=None, height=dp(12))
        self.cards_container.add_widget(bottom_spacer)

        logger.info(f"Отображено {len(favorites)} избранных песен")

    def on_load_failed(self, req, error):
        self._hide_loading()
        self._pending_refresh = False
        self.cards_container.clear_widgets()

        error_str = str(error)
        if "401" in error_str or "Unauthorized" in error_str:
            self._show_auth_message()
        else:
            logger.error(f"Ошибка загрузки избранного: {error}")
            if self.favorites:
                logger.info("📦 Показываем устаревший кэш избранного")
                self._show_favorites(self.favorites)
                notify.error("Ошибка обновления, показан кэш")
            else:
                self._show_empty()
                notify.error("Ошибка загрузки избранного")

    def on_song_selected(self, song_id, song_title):
        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        artist = ""
        for song in self.favorites:
            if song.get('song_id') == song_id or song.get('id') == song_id:
                artist = song.get('artist', '')
                break

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('favorite_detail'):
                favorite_detail_screen = self.manager.get_screen('favorite_detail')
                favorite_detail_screen.set_song(song_id, artist, song_title)
                self.manager.current = 'favorite_detail'
                logger.info(f"✅ Переход на FavoriteDetailScreen: {song_title}")
            else:
                if self.manager.has_screen('song_detail'):
                    screen_state.set_previous_screen('favorites')
                    song_detail_screen = self.manager.get_screen('song_detail')
                    song_detail_screen.set_previous_screen('favorites')
                    song_detail_screen.set_song(song_id)
                    self.manager.current = 'song_detail'

    def go_back(self, instance=None):
        logger.info("🔙 go_back: возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_pre_enter(self):
        logger.info("on_pre_enter: подготовка к показу")

    def on_enter(self):
        """При входе на экран - загружаем данные"""
        logger.info("Вход в экран избранного")

        # ✅ TopNav уже обновлён в on_pre_enter, но на всякий случай обновляем ещё раз
        self._update_top_nav()

        if not api.is_authenticated():
            self._show_auth_message()
            return

        # Проверяем кэш состояния
        cached_favorites = screen_state.get_cached_screen_data('favorites', max_age=60)

        if cached_favorites:
            logger.info(f"📦 Показываем избранное из кэша состояния: {len(cached_favorites)} песен")
            self.favorites = cached_favorites
            self._show_favorites(cached_favorites)
            Clock.schedule_once(lambda dt: self._check_and_refresh(), 0.5)
            return

        if self.favorites:
            self._show_favorites(self.favorites)
            Clock.schedule_once(lambda dt: self._check_and_refresh(), 0.5)
            return

        self.load_favorites(force_refresh=False)

    def _check_and_refresh(self):
        if not api.is_authenticated():
            return

        if self._pending_refresh:
            return

        cached = api._load_favorites_cache()
        if cached is None:
            logger.info("🔄 Кэш устарел, обновляем в фоне")
            api.get_favorites(
                on_success=self.on_favorites_loaded,
                on_failure=lambda req, err: None,
                force_refresh=True
            )

    def on_login_success(self):
        logger.info("✅ Успешная авторизация — обновляем избранное")
        self._top_nav_updated = False
        self.load_favorites(force_refresh=True)

    def on_leave(self):
        logger.info("Выход из экрана избранного")
        self._hide_loading()
        self._top_nav_updated = False

    @staticmethod
    def pre_update_top_nav():
        """Статический метод для обновления TopNav ДО перехода на экран"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Избранное")
            app.top_nav.back_btn.on_release = lambda: None
            logger.info("✅ TopNav обновлён: Избранное (до перехода)")