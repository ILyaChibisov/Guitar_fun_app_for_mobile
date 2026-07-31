# screens/artist_songs_screen.py
"""
Экран списка песен исполнителя - с именем в TopNav
и количеством песен на экране (как в избранном)
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.graphics import Color, Rectangle
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.components.loading_spinner import LoadingSpinner
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state

logger = screen_logger('ArtistSongs')

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
            logger.error(f"Ошибка загрузки иконки песни: {e}")
    return None


class RecycleSongCard(RecycleDataViewBehavior, MDCard):
    """
    Карточка песни - ТОЧНО КАК В SongsScreen
    Название слева, количество подборов справа
    """

    title = StringProperty('')
    tabs_count = NumericProperty(0)
    song_id = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.padding = [dp(10), dp(4), dp(10), dp(4)]
        self.spacing = dp(8)
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
        self.icon = Image(
            size_hint=(None, 1),
            width=dp(28),
            allow_stretch=True,
            keep_ratio=True
        )
        if _shared_song_texture:
            self.icon.texture = _shared_song_texture
        else:
            self.icon.text = "🎵"

        self.title_label = MDLabel(
            font_size=sp(15),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right",
            valign="middle",
            size_hint_x=1
        )

        self.count_label = MDLabel(
            text="",
            font_size=sp(11),
            size_hint_x=None,
            width=dp(40),
            halign="right",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4]
        )

        arrow = MDLabel(
            text="›",
            font_size=sp(22),
            size_hint_x=None,
            width=dp(24),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon)
        self.add_widget(self.title_label)
        self.add_widget(self.count_label)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        self.title = data.get('title', '')
        self.tabs_count = data.get('tabs_count', 0)
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.title_label.text = self.title
        self.count_label.text = str(self.tabs_count) if self.tabs_count > 0 else ""
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


class SongRecycleView(RecycleView):
    """Виртуализированный список песен - оптимизированный"""

    def __init__(self, on_song_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_song_click = on_song_click
        self.animate_scroll = False
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]
        self.clip = True

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(48) * 50,
            orientation='vertical',
            spacing=dp(2)
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.viewclass = 'RecycleSongCard'
        self.add_widget(self.layout_manager)

    def set_songs(self, songs, on_click):
        data = []
        for song in songs:
            data.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'tabs_count': song.get('tabs_count', 1),
                'on_click': on_click
            })
        self.data = data
        self.refresh_from_data()

    def clear(self):
        self.data = []
        self.refresh_from_data()


class ArtistSongsScreen(BaseScreen):
    """Экран списка песен исполнителя - с именем в TopNav, количеством на экране"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artist_songs'
        self.artist_name = ''
        self.artist_songs = []
        self._pending_artist = None

        # Для загрузки песен
        self._page = 0
        self._limit = 200
        self._is_loading_more = False
        self._has_more = True
        self._total_songs = 0

        # Для сохранения состояния
        self._saved_scroll_position = 1.0
        self._is_restoring = False
        self._temp_scroll_position = None
        self._is_loading = False

        # UI элементы
        self.recycle_view = None
        self._hint_timer = None
        self._main_layout = None
        self._top_spacer = None
        self.loading_spinner = None
        self.empty_label = None
        self.bg_image = None

        # Количество песен на экране (как в избранном)
        self.count_label = None

        # Флаг, что экран уже был инициализирован
        self._initialized = False
        # Флаг защиты от повторного возврата
        self._going_back = False

        init_shared_song_icon()

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
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        self._main_layout = main_layout

        top_padding = layout_config.get_top_padding()
        top_padding = top_padding - dp(8)
        if top_padding < dp(20):
            top_padding = dp(20)

        self._top_spacer = Widget(size_hint_y=None, height=top_padding)
        main_layout.add_widget(self._top_spacer)

        # ============ КОЛИЧЕСТВО ПЕСЕН НА ЭКРАНЕ (как в избранном) ============
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

        # ============ СПИСОК ПЕСЕН ============
        bottom_padding = layout_config.get_bottom_padding()

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), bottom_padding]
        )

        self.recycle_view = SongRecycleView(on_song_click=self.on_song_selected)

        cards_container.add_widget(self.recycle_view)
        main_layout.add_widget(cards_container)

        self.add_widget(main_layout)
        self._initialized = True
        logger.info(f"UI построен, bottom_padding={bottom_padding}dp")

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

    def _update_top_nav_title(self, artist=None):
        """Обновляет заголовок в TopNav (только имя исполнителя)"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            artist_name = artist if artist is not None else self.artist_name

            if artist_name:
                display_name = artist_name if len(artist_name) <= 25 else artist_name[:22] + "..."
                app.top_nav.set_custom_title(display_name)
                logger.info(f"✅ TopNav обновлён: {display_name}")
            else:
                logger.warning("⚠️ Не удалось обновить TopNav: artist_name отсутствует")

    def set_artist(self, artist):
        """Устанавливает исполнителя и загружает песни"""
        logger.info(f"set_artist: {artist}")

        self.artist_name = artist
        self._total_songs = 0
        self._page = 0
        self._artist_songs = []
        self._has_more = True
        self._is_loading_more = False
        self._is_loading = False

        self._update_top_nav_title(artist)
        self._update_count_label(0)

        if self.manager and self.manager.current == self.name:
            self._load_artist_songs(artist)
        else:
            self._pending_artist = artist
            logger.info(f"ℹ️ Экран не активен, сохраняем {artist} для on_enter")

    def _load_artist_songs(self, artist):
        """Загружает песни исполнителя (с защитой от дублирования)"""
        if self._is_loading:
            logger.info(f"⏳ Уже идёт загрузка для {artist}, пропускаем")
            return

        logger.info(f"_load_artist_songs: {artist}")
        self._is_loading = True
        self.artist_name = artist

        self._page = 0
        self._artist_songs = []
        self._has_more = True
        self._is_loading_more = False

        if self.recycle_view:
            self.recycle_view.clear()

        self._hide_loading()
        self._hide_empty()
        self._show_loading()

        api.get_songs_by_artist(
            artist=artist,
            limit=self._limit,
            offset=0,
            on_success=self._on_first_page_loaded,
            on_failure=self._on_load_failed
        )

    def _on_first_page_loaded(self, data):
        """Обработчик первой страницы"""
        self._is_loading = False

        if data is None:
            data = {"songs": [], "total": 0}
        if not isinstance(data, dict):
            data = {"songs": [], "total": 0}

        songs = data.get('songs', [])
        total = data.get('total', 0)

        if not isinstance(songs, list):
            songs = []
            total = 0

        self._total_songs = total

        for song in songs:
            self._artist_songs.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'tabs_count': song.get('tabs_count', 1),
                'on_click': self.on_song_selected
            })

        logger.info(f"📄 Первая страница: {len(self._artist_songs)} из {total} песен")

        self._update_top_nav_title(self.artist_name)
        self._update_count_label(self._total_songs)
        self._display_songs()

        if len(self._artist_songs) >= total:
            self._has_more = False
            self._hide_loading()
            return

        self._load_next_pages()

    def _load_next_pages(self):
        """Загружает остальные страницы последовательно"""
        if not self._has_more or self._is_loading_more:
            return

        if self._total_songs > 0 and len(self._artist_songs) >= self._total_songs:
            self._has_more = False
            self._hide_loading()
            self._update_top_nav_title(self.artist_name)
            self._update_count_label(self._total_songs)
            return

        self._is_loading_more = True
        self._page += 1

        offset = self._page * self._limit

        logger.info(f"🔄 Фоновая загрузка страницы {self._page + 1} (offset={offset})")

        api.get_songs_by_artist(
            artist=self.artist_name,
            limit=self._limit,
            offset=offset,
            on_success=self._on_next_page_loaded,
            on_failure=self._on_load_failed
        )

    def _on_next_page_loaded(self, data):
        """Обработчик загрузки следующей страницы"""
        self._is_loading_more = False

        if data is None:
            data = {"songs": [], "total": 0}
        if not isinstance(data, dict):
            data = {"songs": [], "total": 0}

        songs = data.get('songs', [])
        total = data.get('total', 0)

        if not isinstance(songs, list):
            songs = []

        if not songs:
            self._has_more = False
            self._hide_loading()
            self._update_top_nav_title(self.artist_name)
            self._update_count_label(self._total_songs)
            return

        for song in songs:
            self._artist_songs.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'tabs_count': song.get('tabs_count', 1),
                'on_click': self.on_song_selected
            })

        new_count = len(self._artist_songs)
        logger.info(f"✅ Загружено {new_count} из {total} песен")

        self._update_top_nav_title(self.artist_name)
        self._update_count_label(self._total_songs)
        self._display_songs()

        if new_count >= total:
            self._has_more = False
            self._hide_loading()
            self._update_top_nav_title(self.artist_name)
            self._update_count_label(self._total_songs)
            return

        Clock.schedule_once(lambda dt: self._load_next_pages(), 0.1)

    def _display_songs(self):
        """Показывает текущий список песен"""
        if not self._artist_songs:
            self._show_empty()
            if self.recycle_view:
                self.recycle_view.clear()
            return

        self._hide_empty()
        if self.recycle_view:
            current_data = self.recycle_view.data
            new_data = []
            for song in self._artist_songs:
                new_data.append({
                    'song_id': song.get('song_id', 0),
                    'title': song.get('title', ''),
                    'tabs_count': song.get('tabs_count', 1),
                    'on_click': self.on_song_selected
                })

            if current_data != new_data:
                self.recycle_view.set_songs(self._artist_songs, self.on_song_selected)

            if self._saved_scroll_position < 1.0:
                Clock.schedule_once(lambda dt: setattr(self.recycle_view, 'scroll_y', self._saved_scroll_position), 0.1)
            else:
                Clock.schedule_once(lambda dt: setattr(self.recycle_view, 'scroll_y', 1.0), 0.1)

        logger.info(f"📄 Отображено {len(self._artist_songs)} песен для {self.artist_name}")

    def _show_loading(self):
        if self.loading_spinner:
            return
        if self.recycle_view:
            self.recycle_view.clear()

        self.loading_spinner = LoadingSpinner(text="Загрузка песен...")
        self.loading_spinner.start_animation()

        if self._main_layout:
            self._main_layout.add_widget(self.loading_spinner)

    def _hide_loading(self):
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            if self.loading_spinner.parent:
                self.loading_spinner.parent.remove_widget(self.loading_spinner)
        self.loading_spinner = None

    def _show_empty(self, text="Нет песен у этого исполнителя"):
        if self.empty_label:
            return
        self.empty_label = MDLabel(
            text=text,
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4],
            size_hint_y=None,
            height=dp(60)
        )
        if self._main_layout:
            self._main_layout.add_widget(self.empty_label)

    def _hide_empty(self):
        if self.empty_label and self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)
        self.empty_label = None

    def _on_load_failed(self, req, error):
        self._is_loading = False
        self._is_loading_more = False
        self._hide_loading()
        logger.error(f"Ошибка загрузки для {self.artist_name}: {error}")

        if self.recycle_view:
            self.recycle_view.clear()
        self._update_top_nav_title(self.artist_name)
        self._update_count_label(0)
        self._show_empty("Ошибка загрузки\nПроверьте интернет")

    # ============ ВЫБОР ПЕСНИ ============

    def on_song_selected(self, song_id, song_title):
        """Обработчик выбора песни - переход на SongDetailScreen"""
        logger.info(f"🎵 Выбрана песня: {song_title}, id: {song_id}")
        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        if self.recycle_view:
            self._saved_scroll_position = self.recycle_view.scroll_y

        screen_state.set_previous_screen('artist_songs')
        screen_state.set_artist_songs_data(self.artist_name, self._saved_scroll_position)

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                song_detail_screen.set_previous_screen('artist_songs')
                song_detail_screen.set_song(song_id)
                self.manager.current = 'song_detail'
                logger.info(f"✅ Переход на SongDetailScreen: {song_title}")
            else:
                logger.error("❌ Экран song_detail не найден")
                notify.error("Ошибка навигации")

    # ============ НАВИГАЦИЯ ============

    def go_back(self, instance=None):
        """Возврат на SongsScreen - вызывается из TopNav"""
        logger.info(f"🔙 go_back вызван для ArtistSongsScreen")

        if self._going_back:
            logger.info("⏭️ Уже выполняется возврат, пропускаем")
            return
        self._going_back = True

        Clock.schedule_once(lambda dt: setattr(self, '_going_back', False), 0.8)

        # Очищаем заголовок TopNav
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('songs'):
                songs_screen = self.manager.get_screen('songs')
                Clock.schedule_once(lambda dt: songs_screen.restore_state(), 0.1)
                self.manager.current = 'songs'
                logger.info("✅ Возврат на SongsScreen")
            else:
                self.manager.current = 'home'
                logger.info("⚠️ SongsScreen не найден, возврат на home")

    # ============ ЖИЗНЕННЫЙ ЦИКЛ ============

    def on_enter(self):
        """При входе на экран"""
        logger.info(f"🚪 Вход в ArtistSongsScreen: {self.artist_name}")

        # Обновляем заголовок в TopNav и количество на экране
        if self.artist_name:
            self._update_top_nav_title(self.artist_name)
            self._update_count_label(self._total_songs)

        # Если есть отложенный исполнитель - загружаем
        if hasattr(self, '_pending_artist') and self._pending_artist:
            artist = self._pending_artist
            self._pending_artist = None
            self._load_artist_songs(artist)
            return

        if self.artist_name and not self._artist_songs:
            self._load_artist_songs(self.artist_name)
            return

        if self._artist_songs:
            self._display_songs()
            logger.info(f"📄 Показаны существующие песни: {len(self._artist_songs)}")

    def on_leave(self):
        """При выходе с экрана"""
        logger.info(f"🚪 Выход из ArtistSongsScreen: {self.artist_name}")
        self._hide_loading()

        if self.manager and self.manager.current != 'song_detail':
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.clear_custom_title_widget()