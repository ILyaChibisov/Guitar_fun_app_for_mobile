# screens/favorites_screen.py
"""
Экран избранного - список любимых песен пользователя
Стилизован под artist_songs_screen
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

# Глобальная текстура для иконки песни (как в artist_songs_screen)
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
    """Карточка избранной песни в стиле artist_songs_screen"""

    def __init__(self, song, on_click=None, **kwargs):
        super().__init__(**kwargs)

        # Извлекаем данные из песни
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

        # Стилизация как в artist_songs_screen
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.spacing = dp(10)
        self.radius = [theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                       theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL]
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.08]  # Прозрачность как в artist_songs_screen
        self.line_color = [1, 1, 1, 0.08]
        self.line_width = 1

        self._build_ui()

    def _build_ui(self):
        # Иконка песни
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

        # Текстовая часть
        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        # Исполнитель (как название песни в artist_songs_screen)
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

        # Название песни (как количество подборов)
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
            text_color=[1, 1, 1, 0.5]
        )

        self.add_widget(self.icon_image)
        self.add_widget(text_layout)
        self.add_widget(arrow)

        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        if self.on_click_callback and self.song_id:
            self.on_click_callback(self.song_id, self.song_title)


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


class FavoritesScreen(BaseScreen):
    """Экран избранного - в стиле artist_songs_screen"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'
        self.favorites = []
        self.is_loading = False
        self.loading_spinner = None
        self.bg_image = None
        self.recycle_view = None
        self.empty_label = None
        self.loading_label = None
        self.count_label = None
        self._main_layout = None

        self.init_ui()
        self.load_background()
        Clock.schedule_once(lambda dt: init_shared_song_icon(), 0.1)

        logger.info('Экран избранного создан (в стиле artist_songs_screen)')

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
        # Создаём вертикальный контейнер
        self._main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # ============ ВЕРХНИЙ ОТСТУП ============
        top_padding = layout_config.get_top_padding()
        self._main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # ============ СЧЁТЧИК ПЕСЕН ============
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
        self._main_layout.add_widget(self.count_label)

        # ============ КОНТЕЙНЕР ДЛЯ КАРТОЧЕК ============
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )

        # Контейнер для карточек (будет заполняться динамически)
        self.cards_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(6),
            size_hint_y=None,
            adaptive_height=True
        )

        # Оборачиваем в ScrollView для прокрутки
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,  # Невидимый скроллбар
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0]
        )
        scroll.add_widget(self.cards_container)
        cards_container.add_widget(scroll)

        self._main_layout.add_widget(cards_container)

        self.add_widget(self._main_layout)

    def show_loading_state(self):
        """Показывает индикатор загрузки"""
        self.is_loading = True
        self.cards_container.clear_widgets()
        self.loading_spinner = LoadingSpinner()
        self.cards_container.add_widget(self.loading_spinner)
        self.loading_spinner.start_animation()
        self._update_count_label(0)

    def hide_loading_state(self):
        """Скрывает индикатор загрузки"""
        self.is_loading = False
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
        self.cards_container.clear_widgets()

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

    def show_empty_state(self, is_authenticated=True):
        """Показывает пустое состояние"""
        self.hide_loading_state()
        self.cards_container.clear_widgets()
        self._update_count_label(0)

        if is_authenticated:
            empty_text = "Нет избранных песен"
            hint_text = "Добавляйте песни в избранное\nиз карточки песни"
        else:
            empty_text = "Требуется авторизация"
            hint_text = "Войдите в аккаунт, чтобы\nвидеть избранные песни"

        empty_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(160),
            padding=[dp(24), dp(24), dp(24), dp(24)],
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.08],  # Такая же прозрачность как у карточек
            elevation=0,
            line_color=[1, 1, 1, 0.08],
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

        text_label = MDLabel(
            text=empty_text,
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_y=None,
            height=dp(40),
            bold=True
        )

        hint_label = MDLabel(
            text=hint_text,
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
        self.cards_container.add_widget(empty_card)

    def on_pre_enter(self):
        """Вызывается перед входом на экран"""
        if not api.is_authenticated():
            self.show_empty_state(is_authenticated=False)
            return

        # Обновляем заголовок в верхней панели (если нужно)
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.update_title('favorites')

        self.load_favorites()

    def load_favorites(self):
        """Загружает избранные песни"""
        self.show_loading_state()
        api.get_favorites(
            on_success=self.on_favorites_loaded,
            on_failure=self.on_load_failed
        )

    def on_favorites_loaded(self, favorites):
        """Обработчик успешной загрузки избранного"""
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
            return

        total = len(self.favorites)
        self._update_count_label(total)

        # Добавляем карточки
        for song_data in self.favorites:
            card = FavoriteSongCard(song=song_data, on_click=self.on_song_selected)
            self.cards_container.add_widget(card)

        # Добавляем нижний отступ
        bottom_spacer = Widget(size_hint_y=None, height=dp(20))
        self.cards_container.add_widget(bottom_spacer)

        logger.info(f"Загружено {len(self.favorites)} избранных песен")

    def on_load_failed(self, req, error):
        """Обработчик ошибки загрузки"""
        self.hide_loading_state()
        if "401" in str(error) or "Unauthorized" in str(error):
            notify.warning("Сессия истекла. Пожалуйста, войдите снова.")
            if hasattr(self, 'manager') and self.manager:
                self.manager.current = 'home'
        else:
            logger.error(f"Ошибка загрузки избранного: {error}")
            self.show_empty_state()
            notify.error("Ошибка загрузки избранного")

    def on_song_selected(self, song_id, song_title):
        """Обработчик выбора песни"""
        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                song_detail_screen.set_previous_screen('favorites')
                song_detail_screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в экран избранного")
        # Обновляем список при входе
        if api.is_authenticated():
            self.load_favorites()

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана избранного")