# screens/artists_by_letter_screen.py
"""
Экран списка исполнителей по выбранной букве - с двухстрочным заголовком в TopNav
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
from kivy.uix.scrollview import ScrollView
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.system_bars import get_status_bar_height, get_navigation_bar_height
from config.layout_config import layout_config
from api.client import api
from screens.recycle_artist_card import ArtistRecycleView, set_shared_icon
from screens.base_screen import BaseScreen
from kivymd.app import MDApp
from utils.screen_state import screen_state

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
    """Экран списка исполнителей по букве с двухстрочным заголовком в TopNav"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artists_by_letter'
        self.current_letter = None
        self.recycle_view = None
        self.empty_label = None
        self.loading_label = None
        self.letter_label = None
        self.back_btn = None
        self._pending_letter = None
        self._main_layout = None
        self.bg_image = None
        self._top_spacer = None
        self._total_artists = 0

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

    def _create_top_nav_title(self):
        """Создаёт двухстрочный заголовок для TopNav (буква и количество)"""
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        from kivy.metrics import sp, dp

        title_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(2),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        # Буква - большая, жирная
        letter_display = self.current_letter.upper() if self.current_letter else ""
        if letter_display == '0-9':
            letter_display = '0-9'
        letter_label = MDLabel(
            text=letter_display,
            font_size=sp(22),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            shorten=True,
            shorten_from="right"
        )

        # Количество исполнителей
        total = self._total_artists
        count_text = self._get_count_text(total)
        count_label = MDLabel(
            text=count_text,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.9, 0.9, 0.9, 0.8],
            shorten=True,
            shorten_from="right"
        )

        title_container.add_widget(letter_label)
        title_container.add_widget(count_label)

        return title_container

    def _get_count_text(self, total):
        """Возвращает текст с количеством исполнителей с правильным склонением"""
        if total == 0:
            return "Нет исполнителей"
        elif total == 1:
            return "1 исполнитель"
        elif 2 <= total <= 4:
            return f"{total} исполнителя"
        else:
            return f"{total} исполнителей"

    def _update_top_nav(self):
        """Обновляет TopNav с двухстрочным заголовком"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            if self.current_letter:
                title_container = self._create_top_nav_title()
                app.top_nav.set_custom_title_widget(title_container)
                app.top_nav._show_back_button()
                app.top_nav.back_btn.on_release = self.go_back
                logger.info(f"✅ TopNav обновлён: {self.current_letter} ({self._total_artists} исполнителей)")
            else:
                logger.warning("⚠️ Не удалось обновить TopNav: current_letter отсутствует")

    def _restore_top_nav(self, *args):
        """Принудительное восстановление заголовка с задержкой"""
        if self.current_letter:
            self._update_top_nav()
            logger.info(f"   ✅ Принудительно восстановлен заголовок: {self.current_letter} ({self._total_artists} исполнителей)")

    def init_ui(self):
        """Инициализирует UI с уменьшенным верхним отступом"""

        # Создаём вертикальный контейнер
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        self._main_layout = main_layout

        # ============ ВЕРХНИЙ ОТСТУП (УМЕНЬШЕННЫЙ) ============
        top_padding = layout_config.get_top_padding()
        # Уменьшаем отступ на 8dp, чтобы карточки были ближе к TopNav
        top_padding = top_padding - dp(8)
        if top_padding < dp(20):
            top_padding = dp(20)

        self._top_spacer = Widget(size_hint_y=None, height=top_padding)
        main_layout.add_widget(self._top_spacer)

        # ============ КОНТЕЙНЕР ДЛЯ КАРТОЧЕК ============
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(12)

        cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )
        cards_container.clip = True
        cards_container.adaptive_height = False

        # RecycleView для карточек
        self.recycle_view = ArtistRecycleView(on_artist_click=self.on_artist_selected)
        self.recycle_view.bar_width = 0
        self.recycle_view.bar_color = [0, 0, 0, 0]
        self.recycle_view.bar_inactive_color = [0, 0, 0, 0]
        self.recycle_view.clip = True

        cards_container.add_widget(self.recycle_view)
        main_layout.add_widget(cards_container)

        self.add_widget(main_layout)

    def on_enter(self):
        """Вызывается когда экран становится видимым"""
        logger.info(f"on_enter: current_letter={self.current_letter}, pending={self._pending_letter}")

        # ============ ПРИНУДИТЕЛЬНО ВОССТАНАВЛИВАЕМ ЗАГОЛОВОК ============
        if self.current_letter:
            # Сразу восстанавливаем
            self._restore_top_nav()
            # Дополнительные задержки для гарантии
            Clock.schedule_once(self._restore_top_nav, 0.1)
            Clock.schedule_once(self._restore_top_nav, 0.3)
            Clock.schedule_once(self._restore_top_nav, 0.5)
            logger.info(f"   ✅ Восстановлен заголовок: {self.current_letter}")

        if self._pending_letter:
            letter = self._pending_letter
            self._pending_letter = None
            self._do_load_letter(letter)
        elif self.current_letter:
            self._do_load_letter(self.current_letter)

    def set_letter(self, letter):
        logger.info(f"set_letter: {letter}")
        self.current_letter = letter
        self._total_artists = 0

        # Обновляем TopNav с заглушкой
        self._update_top_nav()

        if not self.manager or self.manager.current != self.name:
            logger.info(f"Экран не активен, сохраняем букву {letter} для on_enter")
            self._pending_letter = letter
            return

        self._do_load_letter(letter)

    def _do_load_letter(self, letter):
        """Загружает исполнителей для буквы с сервера"""
        logger.info(f"_do_load_letter: {letter}")

        self.current_letter = letter

        if self.recycle_view:
            self.recycle_view.clear()

        self._hide_loading()
        self._hide_empty()

        # Всегда идем на сервер — кэш убран
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
        self._total_artists = total

        self._hide_loading()
        self._hide_empty()

        # Обновляем TopNav с реальным количеством
        self._update_top_nav()

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

        self._display_artists(artists, total)

    def _on_load_failed(self, req, error):
        self._hide_loading()
        logger.error(f"Ошибка загрузки для буквы {self.current_letter}: {error}")

        self._total_artists = 0

        if self.recycle_view:
            self.recycle_view.clear()

        self._show_empty("Ошибка загрузки\nПроверьте интернет")
        self._update_top_nav()

    def on_artist_selected(self, artist, songs_count):
        logger.info(f"Выбран исполнитель: {artist}")
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artist_songs'):
                screen = self.manager.get_screen('artist_songs')
                screen.set_artist(artist)
                self.manager.current = 'artist_songs'

    def go_back(self, instance=None):
        """Возврат на экран песен (songs)"""
        logger.info("🔙 go_back: возврат на songs")
        # Очищаем кастомный заголовок
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            app.top_nav.update_title('songs')
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'songs'

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана исполнителей")
        # Не очищаем заголовок при выходе, если переходим на artist_songs
        if self.manager and self.manager.current not in ['artist_songs', 'song_detail']:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.clear_custom_title_widget()
                app.top_nav.update_title('songs')