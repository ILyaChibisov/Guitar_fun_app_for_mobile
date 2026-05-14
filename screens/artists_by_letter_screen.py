# screens/artists_by_letter_screen.py
"""
Экран списка исполнителей по выбранной букве - исправлены отступы
"""
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.system_bars import get_status_bar_height, get_navigation_bar_height
from config.layout_config import layout_config
from api.client import api
from screens.recycle_artist_card import ArtistRecycleView, set_shared_icon
from screens.base_screen import BaseScreen
from kivymd.app import MDApp

logger = screen_logger('ArtistsByLetter')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# Глобальный кэш для текстур
_shared_texture = None


def init_shared_icon():
    """ОДНОКРАТНО загружает иконку в память для всех карточек"""
    global _shared_texture
    if _shared_texture is not None:
        return _shared_texture

    if HAS_ASSETS:
        try:
            icon_data = load_asset_as_bytes('artist_png')
            if icon_data:
                img = CoreImage(BytesIO(icon_data), ext="png")
                _shared_texture = img.texture
                set_shared_icon(_shared_texture)
                logger.info("✅ Общая иконка загружена")
                return _shared_texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки: {e}")
    return None


class SimpleLoadingLabel(MDLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Загрузка исполнителей..."
        self.halign = "center"
        self.font_size = sp(14)
        self.theme_text_color = "Custom"
        self.text_color = [1, 1, 1, 0.6]
        self.size_hint_y = None
        self.height = dp(60)


class ArtistsByLetterScreen(BaseScreen):
    """Экран списка исполнителей по букве"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artists_by_letter'
        self.current_letter = None
        self._cache = {}
        self.recycle_view = None
        self.empty_label = None
        self.loading_label = None
        self.count_label = None
        self.letter_label = None
        self.back_btn = None
        self._pending_letter = None
        self._main_layout = None
        self.bg_image = None

        self.md_bg_color = [0, 0, 0, 0]
        self.init_ui()
        self.load_background()

        Clock.schedule_once(lambda dt: init_shared_icon(), 0.1)

        logger.info('Экран исполнителей создан (BaseScreen)')

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
        # Отступ сверху под статус-бар и TopNav
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # ============ СЧЁТЧИК ИСПОЛНИТЕЛЕЙ ============
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
        # Получаем высоту системной навигации
        nav_bar_height = get_navigation_bar_height()

        # Высота BottomNav из конфига (60dp для телефона)
        bottom_nav_height = dp(60)  # базовая высота BottomNav

        # Общая высота нижней части = BottomNav + системная навигация + зазор
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )

        # RecycleView для карточек
        self.recycle_view = ArtistRecycleView(on_artist_click=self.on_artist_selected)
        self.recycle_view.bar_width = 0
        self.recycle_view.bar_color = [0, 0, 0, 0]
        self.recycle_view.bar_inactive_color = [0, 0, 0, 0]

        cards_container.add_widget(self.recycle_view)
        main_layout.add_widget(cards_container)

        self.add_widget(main_layout)

    def on_enter(self):
        """Вызывается когда экран становится видимым"""
        logger.info(f"on_enter: current_letter={self.current_letter}, pending={self._pending_letter}")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if self.current_letter:
                app.top_nav.update_for_artists_screen(self.current_letter, show_back_button=True)
            elif self._pending_letter:
                app.top_nav.update_for_artists_screen(self._pending_letter, show_back_button=True)

        if self._pending_letter:
            letter = self._pending_letter
            self._pending_letter = None
            self._do_load_letter(letter)
        elif self.current_letter:
            self._do_load_letter(self.current_letter)

    def set_letter(self, letter):
        logger.info(f"set_letter: {letter}")
        self.current_letter = letter

        if not self.manager or self.manager.current != self.name:
            logger.info(f"Экран не активен, сохраняем букву {letter} для on_enter")
            self._pending_letter = letter
            return

        self._do_load_letter(letter)

    def _do_load_letter(self, letter):
        logger.info(f"_do_load_letter: {letter}")

        self.current_letter = letter

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.update_for_artists_screen(letter, show_back_button=True)

        if self.recycle_view:
            self.recycle_view.clear()

        self._hide_loading()
        self._hide_empty()
        self._update_count_label(0)

        if letter in self._cache:
            artists = self._cache[letter].get('artists', [])
            total = self._cache[letter].get('total', 0)
            self._display_artists(artists, total)
            return

        cached = api.get_artists_by_letter_from_cache(letter)
        if cached:
            artists = cached.get('artists', [])
            total = cached.get('total', 0)
            self._cache[letter] = {'artists': artists, 'total': total}
            self._display_artists(artists, total)
            return

        self._show_loading()

        if letter in ("digits", "0-9"):
            api.get_artists_by_digits(limit=200, offset=0,
                                      on_success=self._on_artists_loaded,
                                      on_failure=self._on_load_failed)
        else:
            api.get_artists_by_letter(letter=letter, limit=200, offset=0,
                                      on_success=self._on_artists_loaded,
                                      on_failure=self._on_load_failed)

    def _show_loading(self):
        if self.loading_label:
            return
        if self.recycle_view:
            self.recycle_view.clear()
        self.loading_label = SimpleLoadingLabel()
        # Добавляем в основную layout, а не в recycle_view
        if self._main_layout:
            self._main_layout.add_widget(self.loading_label)

    def _hide_loading(self):
        if self.loading_label and self.loading_label.parent:
            self.loading_label.parent.remove_widget(self.loading_label)
        self.loading_label = None

    def _show_empty(self, text="Нет исполнителей на эту букву"):
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

    def _display_artists(self, artists, total):
        if artists is None:
            artists = []
        if total is None:
            total = 0

        logger.info(f"_display_artists: {len(artists)} артистов, total={total}")

        self._hide_loading()
        self._hide_empty()
        self._update_count_label(total)

        if not artists:
            self._show_empty()
            if self.recycle_view:
                self.recycle_view.clear()
            return

        data = []
        for a in artists:
            name = a.get('artist') if isinstance(a, dict) else None
            count = a.get('songs_count', 0) if isinstance(a, dict) else 0
            if name:
                data.append({'artist': name, 'songs_count': count, 'on_click': self.on_artist_selected})

        if self.recycle_view:
            self.recycle_view.data = data
            self.recycle_view.refresh_from_data()

        logger.info(f"Отображено {len(data)} исполнителей для {self.current_letter}")

    def _update_count_label(self, total):
        if total == 0:
            text = "Найдено 0 исполнителей"
        elif total == 1:
            text = "Найден 1 исполнитель"
        elif 2 <= total <= 4:
            text = f"Найдено {total} исполнителя"
        else:
            text = f"Найдено {total} исполнителей"

        if self.count_label:
            self.count_label.text = text

    def _on_artists_loaded(self, data):
        logger.info(f"_on_artists_loaded для буквы {self.current_letter}")

        if data is None:
            data = {"artists": [], "total": 0}

        if not isinstance(data, dict):
            data = {"artists": [], "total": 0}

        artists = data.get('artists', [])
        total = data.get('total', 0)

        if not isinstance(artists, list):
            artists = []
            total = 0

        self._cache[self.current_letter] = {'artists': artists, 'total': total}
        self._display_artists(artists, total)

    def _on_load_failed(self, req, error):
        self._hide_loading()
        logger.error(f"Ошибка загрузки для буквы {self.current_letter}: {error}")

        self._cache[self.current_letter] = {'artists': [], 'total': 0}

        if self.recycle_view:
            self.recycle_view.clear()

        self._update_count_label(0)
        self._show_empty("Ошибка загрузки\nПроверьте интернет")

    def on_artist_selected(self, artist, songs_count):
        logger.info(f"Выбран: {artist}")
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artist_songs'):
                screen = self.manager.get_screen('artist_songs')
                screen.set_artist(artist)
                self.manager.current = 'artist_songs'

    def go_back(self, instance):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'songs'