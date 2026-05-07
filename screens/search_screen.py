# screens/search_screen.py
"""
Экран поиска (аккорды и песни) - АСИНХРОННАЯ ВЕРСИЯ
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from io import BytesIO
from threading import Thread

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton

from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('SearchScreen')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


def hex_to_rgb(hex_color):
    """Конвертирует hex цвет в RGB список от 0 до 1"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


# ============ ПОИСКОВАЯ СТРОКА (КАК В SONGS_SCREEN) ============

class SearchBar(MDCard):
    """Поисковая строка для экрана поиска - единый дизайн с songs_screen"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 1
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)

        self.line_color = [0.46, 0.70, 0.71, 0.4]
        self.line_width = 1.0

        self.search_field = MDTextField(
            hint_text="",
            size_hint_x=1,
            font_size=sp(15),
            height=dp(36),
            on_text_validate=self._on_search,
            mode="fill"
        )

        self.search_field.line_color_normal = [0, 0, 0, 0]
        self.search_field.line_color_focus = [0, 0, 0, 0]
        self.search_field.fill_color_normal = [1, 1, 1, 0]
        self.search_field.fill_color_focus = [1, 1, 1, 0]
        self.search_field.hint_text_color = [0.7, 0.7, 0.7, 1]
        self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]

        self.search_field.bind(text=self._on_text_change)

        self.clear_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            theme_icon_color="Custom",
            icon_color=[0.6, 0.6, 0.6, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear,
            opacity=0
        )

        self.search_icon = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search,
            pos_hint={'center_y': 0.5}
        )

        self.add_widget(self.search_field)
        self.add_widget(self.clear_btn)
        self.add_widget(self.search_icon)

    def _on_text_change(self, instance, text):
        self.clear_btn.opacity = 1 if text else 0

    def _on_search(self, instance):
        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear(self, instance):
        self.search_field.text = ""
        self.search_field.focus = True
        self.clear_btn.opacity = 0
        if self.on_clear:
            self.on_clear()

    def get_text(self):
        return self.search_field.text.strip()

    def set_text(self, text):
        self.search_field.text = text
        self.clear_btn.opacity = 1 if text else 0

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        self.search_field.focus = True


class ResultCard(MDCard):
    """Красивая полупрозрачная карточка результата поиска"""

    def __init__(self, title, result_type, subtitle, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.result_type = result_type
        self.subtitle = subtitle
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

        self.text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2)
        )

        self.title_label = MDLabel(
            text=self.title,
            font_size=sp(16),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle"
        )

        self.subtitle_label = MDLabel(
            text=self.subtitle,
            font_size=sp(12),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            valign="middle"
        )

        self.text_container.add_widget(self.title_label)
        self.text_container.add_widget(self.subtitle_label)

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
        icon_name = 'chord_png' if self.result_type == 'chord' else 'song_png'

        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        if self.result_type == 'chord':
            self.icon_image.text = "🎸"
        else:
            self.icon_image.text = "🎵"

    def on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.result_type, self.title)


class SearchScreen(MDScreen):
    """Экран поиска (АСИНХРОННЫЙ)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search'
        self.chords_screen = None
        self.bg_image = None
        self.search_results = []
        self.is_loading = False
        self.fade_layer = None
        self._search_thread = None  # Для отмены предыдущего поиска
        self.loading_dialog = None

        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Экран поиска создан (асинхронная версия)')

    def load_background(self):
        """Загружает фоновое изображение"""
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

    def set_chords_screen(self, chords_screen):
        """Устанавливает ссылку на экран аккордов"""
        self.chords_screen = chords_screen

    def init_ui(self):
        root_layout = FloatLayout()

        main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0
        )

        from config.system_bars import get_status_bar_height
        from config.theme import theme
        status_h = get_status_bar_height()
        total_top_padding = status_h + theme.TOP_NAV_HEIGHT
        top_spacer = Widget(size_hint_y=None, height=dp(total_top_padding))
        main_layout.add_widget(top_spacer)

        # ============ ВЕРХНЯЯ ПАНЕЛЬ ============
        nav_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
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

        title = MDLabel(
            text="Поиск песен и аккордов",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        nav_row.add_widget(self.back_btn)
        nav_row.add_widget(title)

        # ============ ПОЛЕ ПОИСКА ============
        search_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(70),
            padding=[dp(16), dp(8), dp(16), dp(8)]
        )

        self.search_bar = SearchBar(
            on_search=self.perform_search,
            on_clear=self.clear_results
        )
        search_container.add_widget(self.search_bar)

        # ============ РЕЗУЛЬТАТЫ ПОИСКА ============
        self.results_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_color=[1, 1, 1, 0.3],
            bar_width=dp(4),
            bar_inactive_color=[1, 1, 1, 0.1]
        )

        self.results_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(12), dp(16), dp(20)]
        )
        self.results_scroll.add_widget(self.results_container)

        main_layout.add_widget(nav_row)
        main_layout.add_widget(search_container)
        main_layout.add_widget(self.results_scroll)

        # ============ ПРОЗРАЧНЫЙ СЛОЙ НАД НИЖНЕЙ НАВИГАЦИЕЙ ============
        self.fade_layer = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(80),
            pos_hint={'x': 0, 'y': 0},
            md_bg_color=[0, 0, 0, 0]
        )

        with self.fade_layer.canvas.before:
            Color(0, 0, 0, 0.6)
            self.fade_rect = Rectangle(pos=self.fade_layer.pos, size=self.fade_layer.size)

        self.fade_layer.bind(pos=self._update_fade, size=self._update_fade)

        root_layout.add_widget(main_layout)
        root_layout.add_widget(self.fade_layer)

        self.add_widget(root_layout)

    def _update_fade(self, *args):
        if hasattr(self, 'fade_rect'):
            self.fade_rect.pos = self.fade_layer.pos
            self.fade_rect.size = self.fade_layer.size

    def clear_results(self):
        """Очищает результаты поиска"""
        self.results_container.clear_widgets()
        self.search_results = []

    def show_loading(self, show=True, text="Поиск..."):
        """Показывает/скрывает диалог загрузки"""
        if show:
            if not self.loading_dialog:
                self.loading_dialog = MDDialog(
                    title="",
                    text=text,
                    radius=[dp(20), dp(20), dp(20), dp(20)],
                )
            self.loading_dialog.open()
        else:
            if self.loading_dialog:
                self.loading_dialog.dismiss()
                self.loading_dialog = None

    def perform_search(self, query):
        """Выполняет поиск АСИНХРОННО (не блокирует UI)"""
        if len(query) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        logger.info(f"🔍 Поиск: {query}")

        # Отменяем предыдущий поиск, если он ещё выполняется
        if self._search_thread and self._search_thread.is_alive():
            logger.info("Отменяем предыдущий поиск")
            # Не можем принудительно остановить поток, просто игнорируем его результат
            self._search_thread = None

        self.clear_results()
        self.show_loading(True, f"Поиск '{query}'...")

        # Запускаем поиск в отдельном потоке
        self._search_thread = Thread(
            target=self._do_search_worker,
            args=(query,),
            daemon=True
        )
        self._search_thread.start()

    def _do_search_worker(self, query):
        """Рабочий поток для поиска (НЕ БЛОКИРУЕТ UI)"""
        try:
            # Вызываем синхронный метод API в отдельном потоке
            chord_results = self._search_chords_sync(query)
            song_results = self._search_songs_sync(query)

            # Возвращаем результат в UI поток
            Clock.schedule_once(
                lambda dt: self._on_search_complete(query, chord_results, song_results),
                0
            )
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            Clock.schedule_once(lambda dt: self._on_search_error(str(e)), 0)

    def _search_chords_sync(self, query):
        """Синхронный поиск аккордов (работает в фоновом потоке)"""
        if not self.chords_screen or not hasattr(self.chords_screen, 'all_chords'):
            return []

        results = []
        query_lower = query.lower()

        for chord in self.chords_screen.all_chords:
            chord_short = chord['short_name'].lower()
            chord_full = chord['name'].lower().replace('|', ' ').replace('$', '/')

            if query_lower in chord_short or query_lower in chord_full:
                if chord not in results:
                    results.append(chord)

        seen = set()
        unique_results = []
        for chord in results:
            if chord['short_name'] not in seen:
                seen.add(chord['short_name'])
                unique_results.append(chord)

        return unique_results[:10]

    def _search_songs_sync(self, query):
        """Синхронный поиск песен через API (работает в фоновом потоке)"""
        try:
            result = api.search_songs_sync(query, limit=20)
            if isinstance(result, dict):
                return result.get('results', [])
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Ошибка API поиска: {e}")
            return []

    def _on_search_complete(self, query, chord_results, song_results):
        """Обработчик завершения поиска (в UI потоке)"""
        self.show_loading(False)

        if not chord_results and not song_results:
            no_results = MDLabel(
                text=f"Ничего не найдено по запросу «{query}»",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.5],
                size_hint_y=None,
                height=dp(60)
            )
            self.results_container.add_widget(no_results)
            return

        # Аккорды
        if chord_results:
            chords_header = MDLabel(
                text="Аккорды",
                font_size=sp(16),
                bold=True,
                size_hint_y=None,
                height=dp(30),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.9]
            )
            self.results_container.add_widget(chords_header)

            for chord in chord_results:
                card = ResultCard(
                    title=chord['short_name'],
                    result_type="chord",
                    subtitle=f"Тональность: {self.extract_tonality(chord['name'])}",
                    on_click=self.on_result_selected
                )
                self.results_container.add_widget(card)

        # Песни
        if song_results and len(song_results) > 0:
            songs_header = MDLabel(
                text="Песни",
                font_size=sp(16),
                bold=True,
                size_hint_y=None,
                height=dp(30),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.9]
            )
            self.results_container.add_widget(songs_header)

            limit = min(10, len(song_results))
            for i in range(limit):
                song = song_results[i]
                card = ResultCard(
                    title=song.get('artist', ''),
                    result_type="song",
                    subtitle=song.get('title', ''),
                    on_click=self.on_result_selected
                )
                card.song_id = song.get('song_id')
                self.results_container.add_widget(card)

        # Нижний спейсер
        bottom_spacer = Widget(size_hint_y=None, height=dp(80))
        self.results_container.add_widget(bottom_spacer)

        logger.info(f"Поиск завершён: {len(chord_results)} аккордов, {len(song_results)} песен")

    def _on_search_error(self, error_msg):
        """Обработчик ошибки поиска"""
        self.show_loading(False)

        error_label = MDLabel(
            text=f"Ошибка поиска: {error_msg}",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None,
            height=dp(60)
        )
        self.results_container.add_widget(error_label)
        logger.error(f"Ошибка поиска: {error_msg}")

    def on_result_selected(self, result_type, title):
        """Обработка выбора результата"""
        if result_type == "chord":
            self.select_chord(title)
        else:
            for child in self.results_container.children:
                if hasattr(child, 'song_id') and hasattr(child, 'title') and child.title == title:
                    self.select_song(child.song_id, title)
                    break

    def extract_tonality(self, chord_name):
        """Извлекает тональность из названия аккорда"""
        if not chord_name:
            return ""
        import re
        match = re.match(r'^([A-H][#b]?)', chord_name)
        return match.group(1) if match else (chord_name[0] if chord_name else "")

    def select_chord(self, chord_name):
        """Выбирает аккорд"""
        if self.chords_screen and hasattr(self.chords_screen, 'load_chord_by_name'):
            self.chords_screen.load_chord_by_name(chord_name)

        if self.manager and self.manager.has_screen('chords'):
            self.manager.current = 'chords'

    def select_song(self, song_id, song_name):
        """Выбирает песню"""
        if self.manager and self.manager.has_screen('song_detail'):
            song_detail = self.manager.get_screen('song_detail')
            song_detail.set_song(song_id)
            self.manager.current = 'song_detail'

    def go_back(self, instance):
        """Возврат на экран песен"""
        if self.manager:
            self.manager.current = 'songs'