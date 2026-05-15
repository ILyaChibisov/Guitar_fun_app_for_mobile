# screens/artist_songs_screen.py
"""
Экран списка песен выбранного исполнителя - исправленная версия
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
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
from config.system_bars import get_status_bar_height, get_navigation_bar_height
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

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
    """Переиспользуемая карточка песни"""

    title = StringProperty('')
    tabs_count = NumericProperty(0)
    song_id = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        self.md_bg_color = [0, 0, 0, 0.08]
        self.line_color = [1, 1, 1, 0.08]
        self.line_width = 1
        self._build_ui()

    def _build_ui(self):
        # Иконка
        self.icon = Image(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        if _shared_song_texture:
            self.icon.texture = _shared_song_texture
        else:
            self.icon.text = "🎵"

        # Текстовая часть
        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        self.title_label = MDLabel(
            font_size=sp(15),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right"
        )

        self.tabs_label = MDLabel(
            font_size=sp(11),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )

        text_layout.add_widget(self.title_label)
        text_layout.add_widget(self.tabs_label)

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

        self.add_widget(self.icon)
        self.add_widget(text_layout)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        self.title = data.get('title', '')
        self.tabs_count = data.get('tabs_count', 0)
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.title_label.text = self.title
        count = self.tabs_count
        if count == 1:
            suffix = "подбор"
        elif 2 <= count <= 4:
            suffix = "подбора"
        else:
            suffix = "подборов"
        self.tabs_label.text = f"{count} {suffix}"
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


class SongRecycleView(RecycleView):
    """Виртуализированный список песен"""

    def __init__(self, on_song_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_song_click = on_song_click
        self.animate_scroll = False
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(60)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(60) * 10,
            orientation='vertical',
            spacing=dp(6)
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
    """Экран списка песен исполнителя"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artist_songs'
        self.current_artist = None
        self._cache = {}
        self.recycle_view = None
        self.empty_label = None
        self.loading_label = None
        self.count_label = None
        self._pending_artist = None
        self.bg_image = None

        self.init_ui()
        self.load_background()

        Clock.schedule_once(lambda dt: init_shared_song_icon(), 0.1)
        logger.info('Экран песен исполнителя создан (BaseScreen)')

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
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # ============ ВЕРХНИЙ ОТСТУП ============
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

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
        main_layout.add_widget(self.count_label)

        # ============ КОНТЕЙНЕР ДЛЯ КАРТОЧЕК ============
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )

        self.recycle_view = SongRecycleView(on_song_click=self.on_song_selected)
        self.recycle_view.bar_width = 0
        self.recycle_view.bar_color = [0, 0, 0, 0]
        self.recycle_view.bar_inactive_color = [0, 0, 0, 0]

        cards_container.add_widget(self.recycle_view)
        main_layout.add_widget(cards_container)

        self.add_widget(main_layout)

    def on_enter(self):
        """Вызывается когда экран становится видимым"""
        logger.info(f"on_enter: current_artist={self.current_artist}, pending={self._pending_artist}")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if self.current_artist or self._pending_artist:
                artist_name = self.current_artist or self._pending_artist
                # Сокращаем длинное название
                if len(artist_name) > 25:
                    artist_name = artist_name[:22] + "..."
                # Обновляем верхнюю панель с названием исполнителя
                app.top_nav.update_title(artist_name)
                # Показываем стрелочку назад
                app.top_nav._show_back_button()
                # Устанавливаем callback для стрелки
                app.top_nav.back_btn.on_release = self.go_back
            else:
                app.top_nav.reset_to_default()

        if self._pending_artist:
            artist = self._pending_artist
            self._pending_artist = None
            self._do_load_artist(artist)
        elif self.current_artist:
            self._do_load_artist(self.current_artist)

    def set_artist(self, artist):
        logger.info(f"set_artist: {artist}")
        self.current_artist = artist

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            # Сокращаем длинное название
            artist_display = artist if len(artist) <= 25 else artist[:22] + "..."
            # Обновляем заголовок
            app.top_nav.update_title(artist_display)
            # Показываем стрелочку назад
            app.top_nav._show_back_button()
            # Устанавливаем callback для стрелки
            app.top_nav.back_btn.on_release = self.go_back

        if not self.manager or self.manager.current != self.name:
            logger.info(f"Экран не активен, сохраняем исполнителя {artist} для on_enter")
            self._pending_artist = artist
            return

        self._do_load_artist(artist)

    def go_back(self, instance=None):
        """Возврат на экран списка исполнителей (по буквам)"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'artists_by_letter'
            logger.info(f"Возврат на экран artists_by_letter")

    def _do_load_artist(self, artist):
        logger.info(f"_do_load_artist: {artist}")

        self.current_artist = artist

        if self.recycle_view:
            self.recycle_view.clear()

        self._hide_loading()
        self._hide_empty()
        self._update_count_label(0)

        if artist in self._cache:
            songs = self._cache[artist].get('songs', [])
            total = self._cache[artist].get('total', 0)
            self._display_songs(songs, total)
            return

        cached = api.get_songs_by_artist_from_cache(artist)
        if cached:
            songs = cached.get('songs', [])
            total = cached.get('total', 0)
            self._cache[artist] = {'songs': songs, 'total': total}
            self._display_songs(songs, total)
            return

        self._show_loading()

        api.get_songs_by_artist(
            artist=artist,
            limit=200,
            offset=0,
            on_success=self._on_songs_loaded,
            on_failure=self._on_load_failed
        )

    def _show_loading(self):
        if self.loading_label:
            return
        if self.recycle_view:
            self.recycle_view.clear()
        self.loading_label = self.show_loading("Загрузка песен...")

    def _hide_loading(self):
        if self.loading_label and self.loading_label.parent:
            self.loading_label.parent.remove_widget(self.loading_label)
        self.loading_label = None

    def _show_empty(self, text="Нет песен у этого исполнителя"):
        if self.empty_label:
            return
        self.empty_label = self.show_empty(text)

    def _hide_empty(self):
        if self.empty_label and self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)
        self.empty_label = None

    def _update_count_label(self, total, artist_name=None):
        """Обновляет счётчик песен с правильным склонением"""

        if total == 0:
            songs_word = "песен"
        elif total == 1:
            songs_word = "песня"
        elif 2 <= total <= 4:
            songs_word = "песни"
        else:
            songs_word = "песен"

        text = f"Найдено {total} {songs_word}"
        if self.count_label:
            self.count_label.text = text

    def _display_songs(self, songs, total):
        if songs is None:
            songs = []
        if total is None:
            total = 0

        logger.info(f"_display_songs: {len(songs)} песен, total={total}")

        self._hide_loading()
        self._hide_empty()
        self._update_count_label(total)

        if not songs:
            self._show_empty()
            if self.recycle_view:
                self.recycle_view.clear()
            return

        data = []
        for song in songs:
            if isinstance(song, dict):
                data.append({
                    'song_id': song.get('song_id', 0),
                    'title': song.get('title', ''),
                    'tabs_count': song.get('tabs_count', 1),
                    'on_click': self.on_song_selected
                })

        if self.recycle_view:
            self.recycle_view.data = data
            self.recycle_view.refresh_from_data()

        logger.info(f"Отображено {len(data)} песен для {self.current_artist}")

    def _on_songs_loaded(self, data):
        logger.info(f"_on_songs_loaded для {self.current_artist}")

        if data is None:
            data = {"songs": [], "total": 0}
        if not isinstance(data, dict):
            data = {"songs": [], "total": 0}
        songs = data.get('songs', [])
        total = data.get('total', 0)
        self._cache[self.current_artist] = {'songs': songs, 'total': total}
        self._display_songs(songs, total)

    def _on_load_failed(self, req, error):
        self._hide_loading()
        logger.error(f"Ошибка загрузки для {self.current_artist}: {error}")
        self._cache[self.current_artist] = {'songs': [], 'total': 0}
        if self.recycle_view:
            self.recycle_view.clear()
        self._update_count_label(0)
        self._show_empty("Ошибка загрузки\nПроверьте интернет")

    def on_song_selected(self, song_id, song_title):
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

