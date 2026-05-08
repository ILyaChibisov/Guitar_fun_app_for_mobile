# screens/artists_by_letter_screen.py (исправленная версия)
"""
Экран списка исполнителей по выбранной букве - МАКСИМАЛЬНО ОПТИМИЗИРОВАНАЯ ВЕРСИЯ
"""
from kivymd.uix.screen import MDScreen
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
from config.system_bars import get_status_bar_height
from api.client import api
from screens.recycle_artist_card import ArtistRecycleView, set_shared_icon

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
    """Максимально лёгкий спиннер (без анимации прогресса)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Загрузка исполнителей..."
        self.halign = "center"
        self.font_size = sp(14)
        self.theme_text_color = "Custom"
        self.text_color = [1, 1, 1, 0.6]
        self.size_hint_y = None
        self.height = dp(60)


class ArtistsByLetterScreen(MDScreen):
    """Экран списка исполнителей по букве - максимально быстрый"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artists_by_letter'
        self.current_letter = None
        self._cache = {}  # Кэш уже загруженных списков
        self.recycle_view = None
        self.empty_label = None
        self.loading_label = None
        self.count_label = None
        self.letter_label = None
        self.top_bar = None
        self.back_btn = None
        self._pending_letter = None  # Буква, которую нужно загрузить после инициализации

        self.md_bg_color = [0, 0, 0, 0]
        self.init_ui()

        # Предзагружаем иконку в фоне
        Clock.schedule_once(lambda dt: init_shared_icon(), 0.1)

        logger.info('Экран исполнителей создан (RecycleView)')

    def init_ui(self):
        root = MDFloatLayout()

        # Основной вертикальный контейнер
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Отступ под системные панели
        status_h = get_status_bar_height()
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(status_h + theme.TOP_NAV_HEIGHT)))

        # Верхняя панель
        self.top_bar = MDBoxLayout(
            size_hint_y=None,
            height=dp(64),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            md_bg_color=[0, 0, 0, 0]
        )

        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            on_release=self.go_back
        )

        self.letter_label = MDLabel(
            text="",
            font_size=sp(24),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        self.count_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_y=None,
            height=dp(24)
        )

        self.top_bar.add_widget(self.back_btn)
        self.top_bar.add_widget(self.letter_label)
        self.top_bar.add_widget(Widget(size_hint_x=0.2))  # Баланс

        # Виртуализированный список (RecycleView)
        self.recycle_view = ArtistRecycleView(on_artist_click=self.on_artist_selected)

        main_layout.add_widget(self.top_bar)
        main_layout.add_widget(self.count_label)
        main_layout.add_widget(self.recycle_view)

        root.add_widget(main_layout)
        self.add_widget(root)

    def on_enter(self):
        """Вызывается когда экран становится видимым"""
        logger.info(f"on_enter: current_letter={self.current_letter}, pending={self._pending_letter}")

        # Если есть ожидающая буква, загружаем её
        if self._pending_letter:
            letter = self._pending_letter
            self._pending_letter = None
            self._do_load_letter(letter)

    def set_letter(self, letter):
        """Устанавливает букву для загрузки"""
        logger.info(f"set_letter: {letter}")

        # Обновляем заголовок сразу
        display = "0-9" if letter in ("digits", "0-9") else letter.upper()
        self.letter_label.text = display

        # Если экран ещё не активен, сохраняем букву для on_enter
        if not self.manager or self.manager.current != self.name:
            logger.info(f"Экран не активен, сохраняем букву {letter} для on_enter")
            self._pending_letter = letter
            return

        # Иначе загружаем сразу
        self._do_load_letter(letter)

    def _do_load_letter(self, letter):
        """Реальная загрузка данных для буквы"""
        logger.info(f"_do_load_letter: {letter}")

        self.current_letter = letter

        # ОЧИЩАЕМ старые данные
        if self.recycle_view:
            self.recycle_view.data = []

        # Убираем пустой лейбл если был
        if self.empty_label and self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)

        # Проверяем кэш экрана
        if letter in self._cache:
            artists = self._cache[letter]['artists']
            total = self._cache[letter]['total']
            self._display_artists(artists, total)
            return

        # Проверяем кэш API (предзагрузка)
        cached = api.get_artists_by_letter_from_cache(letter)
        if cached:
            artists = cached.get('artists', [])
            total = cached.get('total', 0)
            self._cache[letter] = {'artists': artists, 'total': total}
            self._display_artists(artists, total)
            return

        # Нет в кэше - загружаем
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
        """Показывает индикатор загрузки"""
        if self.loading_label:
            return

        # Очищаем RecycleView
        if self.recycle_view:
            self.recycle_view.data = []

        self.loading_label = SimpleLoadingLabel()
        self.recycle_view.add_widget(self.loading_label)

    def _hide_loading(self):
        if self.loading_label and self.loading_label.parent:
            self.loading_label.parent.remove_widget(self.loading_label)
        self.loading_label = None

    def _display_artists(self, artists, total):
        """Мгновенное отображение через RecycleView"""
        logger.info(f"_display_artists: {len(artists)} артистов, total={total}")

        self._hide_loading()

        # Обновляем счётчик
        self._update_count_label(total)

        # Убираем пустой лейбл если был
        if self.empty_label and self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)

        if not artists:
            # Пустое состояние
            if self.recycle_view:
                self.recycle_view.data = []
            if not self.empty_label:
                self.empty_label = MDLabel(
                    text="Нет исполнителей на эту букву",
                    halign="center",
                    font_size=sp(14),
                    theme_text_color="Custom",
                    text_color=[1, 1, 1, 0.4],
                    size_hint_y=None,
                    height=dp(60)
                )
            self.recycle_view.add_widget(self.empty_label)
            return

        # Массовое обновление - самая быстрая операция
        data = []
        for a in artists:
            name = a.get('artist')
            count = a.get('songs_count', 0)
            if name:
                data.append({'artist': name, 'songs_count': count, 'on_click': self.on_artist_selected})

        # Применяем за один кадр
        if self.recycle_view:
            self.recycle_view.data = data
            # Принудительно обновляем view
            self.recycle_view.refresh_from_data()
        logger.info(f"Отображено {len(data)} исполнителей для {self.current_letter}")

    def _update_count_label(self, total):
        """Обновляет счётчик исполнителей"""
        if total == 0:
            text = "0 исполнителей"
        elif total == 1:
            text = "1 исполнитель"
        elif 2 <= total <= 4:
            text = f"{total} исполнителя"
        else:
            text = f"{total} исполнителей"
        if self.count_label:
            self.count_label.text = text

    def _on_artists_loaded(self, data):
        """Callback после загрузки из API"""
        artists = data.get('artists', [])
        total = data.get('total', 0)
        self._cache[self.current_letter] = {'artists': artists, 'total': total}
        self._display_artists(artists, total)

    def _on_load_failed(self, req, error):
        """Обработчик ошибки"""
        self._hide_loading()
        logger.error(f"Ошибка загрузки: {error}")

        if self.recycle_view:
            self.recycle_view.data = []

        error_label = MDLabel(
            text="Ошибка загрузки\nПроверьте интернет",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None,
            height=dp(60)
        )
        self.recycle_view.add_widget(error_label)

    def on_artist_selected(self, artist, songs_count):
        """Обработчик выбора исполнителя"""
        logger.info(f"Выбран: {artist}")
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artist_songs'):
                screen = self.manager.get_screen('artist_songs')
                screen.set_artist(artist)
                self.manager.current = 'artist_songs'

    def go_back(self, instance):
        """Возврат на экран выбора буквы"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'songs'