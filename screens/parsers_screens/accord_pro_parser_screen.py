# screens/parsers_screens/accord_pro_parser_screen.py
"""
Экран управления парсером Akkords.Pro - переведён на BaseParserScreen
"""
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from io import BytesIO

from utils.kivy_imports import (
    MDBoxLayout, MDLabel, MDCard,
    MDScrollView, MDRaisedButton
)

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from utils.notifications import notify
from api import parser_client
from .base_parser_screen import BaseParserScreen

logger = screen_logger('AccordProParserScreen')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class AccordProStatCard(MDCard):
    def __init__(self, title, value, color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (0.23, None)
        self.height = dp(70)
        self.padding = dp(8)
        self.spacing = dp(2)
        self.radius = [12]
        self.elevation = 2
        self.md_bg_color = [color[0], color[1], color[2], 0.12]
        self.line_color = [color[0], color[1], color[2], 0.4]
        self.line_width = 1

        self.value_label = MDLabel(
            text=str(value), font_size=sp(28), bold=True, halign="center",
            size_hint_y=None, height=dp(36), theme_text_color="Custom",
            text_color=[color[0], color[1], color[2], 1]
        )
        self.title_label = MDLabel(
            text=title, font_size=sp(9), halign="center",
            size_hint_y=None, height=dp(20), theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )
        self.add_widget(self.value_label)
        self.add_widget(self.title_label)

    def update_value(self, value):
        self.value_label.text = str(value)


class AccordProRecentSongCard(MDCard):
    def __init__(self, song_data=None, icon_data=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(75)
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.spacing = dp(10)
        self.radius = [12]
        self.elevation = 2
        self.line_width = 1
        self.song_data = song_data or {}
        self.icon_data = icon_data
        self.update_content()

    def update_content(self, song_data=None):
        if song_data:
            self.song_data = song_data
        self.clear_widgets()

        filename = self.song_data.get('filename', '')
        status = self.song_data.get('status', 'unknown')

        if not filename:
            empty_label = MDLabel(
                text="Нет загруженных песен", halign="center",
                font_size=sp(12), theme_text_color="Custom",
                text_color=[0.5, 0.5, 0.5, 0.7]
            )
            self.add_widget(empty_label)
            return

        if status == 'new':
            bg_color = [0.2, 0.7, 0.2, 0.2]
            line_color = [0.2, 0.8, 0.2, 0.8]
            status_text = "НОВАЯ"
        elif status == 'duplicate':
            bg_color = [0.8, 0.6, 0.1, 0.2]
            line_color = [0.9, 0.7, 0.2, 0.8]
            status_text = "ДУБЛИКАТ"
        elif status == 'error':
            bg_color = [0.8, 0.2, 0.2, 0.2]
            line_color = [0.9, 0.3, 0.3, 0.8]
            status_text = "ОШИБКА"
        else:
            bg_color = [0.3, 0.3, 0.3, 0.2]
            line_color = [0.5, 0.5, 0.5, 0.8]
            status_text = "ОЖИДАНИЕ"

        self.md_bg_color = bg_color
        self.line_color = line_color

        icon_image = Image(
            size_hint=(None, None), size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5}, allow_stretch=True, keep_ratio=True
        )
        if self.icon_data:
            try:
                img = CoreImage(BytesIO(self.icon_data), ext="png")
                icon_image.texture = img.texture
            except:
                pass

        name = filename.replace('.txt', '')
        if len(name) > 35:
            name = name[:32] + "..."

        name_label = MDLabel(
            text=name, font_size=sp(13), bold=True, size_hint_x=1,
            theme_text_color="Custom", text_color=[1, 1, 1, 0.95], valign="middle"
        )
        status_label = MDLabel(
            text=status_text, font_size=sp(10), size_hint_x=None, width=dp(70),
            halign="center", bold=True, theme_text_color="Custom",
            text_color=line_color, valign="middle"
        )

        self.add_widget(icon_image)
        self.add_widget(name_label)
        self.add_widget(status_label)


class AccordProParserScreen(BaseParserScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'accord_pro_parser'
        self.update_event = None
        self.is_on_screen = False
        self.last_song = None
        self.song_icon_data = None
        self.load_icon()
        self.init_ui()
        logger.info('Экран Akkords.Pro парсера создан (BaseParserScreen)')

    def load_icon(self):
        if HAS_ASSETS:
            try:
                self.song_icon_data = load_asset_as_bytes('song_png')
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки: {e}")

    def exit_to_admin(self, *args):
        try:
            self.manager.current = 'admin'
            logger.info("Возврат в админ панель")
        except Exception as e:
            logger.error(f"Ошибка возврата: {e}")
            notify.error("Ошибка возврата")

    def init_ui(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(0), dp(16), dp(0)]
        )

        # Заголовок
        title_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(65),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            radius=[16, 16, 16, 16],
            md_bg_color=[0.15, 0.25, 0.35, 0.5],
            elevation=0
        )
        title_label = MDLabel(
            text="AKKORDS.PRO ПАРСЕР", font_size=sp(22), halign="center",
            bold=True, theme_text_color="Custom", text_color=[0.9, 0.6, 0.3, 1]
        )
        subtitle_label = MDLabel(
            text="загрузка аккордов с akkords.pro", font_size=sp(11),
            halign="center", theme_text_color="Custom", text_color=[1, 1, 1, 0.5]
        )
        title_card.add_widget(title_label)
        title_card.add_widget(subtitle_label)
        content.add_widget(title_card)

        # Информационная карточка
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(100),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(8),
            radius=[16],
            md_bg_color=[0, 0, 0, 0.2],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1
        )
        info_text = MDLabel(
            text="Парсер загружает все группы подряд\nот начала до конца. Для остановки\nиспользуйте кнопку ОСТАНОВИТЬ",
            font_size=sp(12), halign="center", theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )
        info_card.add_widget(info_text)
        content.add_widget(info_card)

        # Кнопки управления
        buttons_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(85),
            padding=[dp(12), dp(8), dp(12), dp(8)],
            radius=[12],
            md_bg_color=[0, 0, 0, 0.2],
            elevation=0
        )
        buttons_layout = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(48))

        self.start_btn = MDRaisedButton(
            text="ЗАПУСТИТЬ", size_hint_x=0.45,
            md_bg_color=[0.2, 0.6, 0.2, 1], font_size=sp(13)
        )
        self.start_btn.bind(on_release=self.start_parser)

        self.stop_btn = MDRaisedButton(
            text="ОСТАНОВИТЬ", size_hint_x=0.45,
            disabled=True, md_bg_color=[0.6, 0.2, 0.2, 1], font_size=sp(13)
        )
        self.stop_btn.bind(on_release=self.stop_parser)

        self.exit_btn = MDRaisedButton(
            text="ВЫХОД", size_hint_x=0.45,
            md_bg_color=[0.4, 0.4, 0.8, 1], font_size=sp(13)
        )
        self.exit_btn.bind(on_release=self.exit_to_admin)

        buttons_layout.add_widget(self.start_btn)
        buttons_layout.add_widget(self.stop_btn)
        buttons_layout.add_widget(self.exit_btn)
        buttons_card.add_widget(buttons_layout)
        content.add_widget(buttons_card)

        # Статистика
        stats_grid = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(85))
        self.total_card = AccordProStatCard("ВСЕГО", 0, [0.4, 0.7, 0.9])
        self.new_card = AccordProStatCard("НОВЫЕ", 0, [0.3, 0.8, 0.3])
        self.dup_card = AccordProStatCard("ПОВТОР", 0, [0.9, 0.7, 0.2])
        self.err_card = AccordProStatCard("ОШИБКИ", 0, [0.9, 0.4, 0.4])
        stats_grid.add_widget(self.total_card)
        stats_grid.add_widget(self.new_card)
        stats_grid.add_widget(self.dup_card)
        stats_grid.add_widget(self.err_card)
        content.add_widget(stats_grid)

        # Последняя песня
        self.last_song_container = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(0))
        content.add_widget(self.last_song_container)

        # Статус
        self.status_label = MDLabel(
            text="Готов к работе", halign="center", size_hint_y=None,
            height=dp(35), font_size=sp(11), theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )
        content.add_widget(self.status_label)

        self.build_ui(content, scroll=True)

    def _is_real_song(self, filename, status):
        if status not in ['new', 'duplicate', 'error']:
            return False
        if not filename:
            return False
        service_patterns = [
            'Группа:', 'Обработка', 'Найдено', 'Запуск',
            'Завершение', 'Получение', 'Поиск файлов', 'Удаление файлов'
        ]
        filename_lower = filename.lower()
        for pattern in service_patterns:
            if pattern.lower() in filename_lower:
                return False
        if ' - ' in filename or filename.endswith('.txt'):
            if len(filename) > 5:
                return True
        return False

    def _update_last_song_display(self, last_song):
        if not last_song:
            if self.last_song_container.height != 0:
                self.last_song_container.height = dp(0)
                self.last_song_container.clear_widgets()
                self.last_song = None
            return

        filename = last_song.get('filename', '')
        status = last_song.get('status', 'unknown')

        if self._is_real_song(filename, status):
            if self.last_song != filename:
                self.last_song = filename
                self.last_song_container.clear_widgets()
                self.last_song_container.height = dp(85)
                song_card = AccordProRecentSongCard(song_data=last_song, icon_data=self.song_icon_data)
                self.last_song_container.add_widget(song_card)
        else:
            if self.last_song_container.height != 0:
                self.last_song_container.height = dp(0)
                self.last_song_container.clear_widgets()
                self.last_song = None

    def start_auto_update(self):
        if not self.is_on_screen:
            return
        if self.update_event:
            self.update_event.cancel()
        self.update_event = Clock.schedule_interval(self._check_status_loop, 2)

    def stop_auto_update(self):
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def _check_status_loop(self, dt):
        if not self.is_on_screen:
            return
        self._fetch_status()

    def _fetch_status(self):
        try:
            result = parser_client.get_accord_pro_parser_status_sync()
            if result and result.get('success'):
                data = result.get('data', result)
                is_running = data.get('is_running', False)

                if is_running:
                    self.start_btn.disabled = True
                    self.start_btn.md_bg_color = [0.3, 0.3, 0.3, 1]
                    self.stop_btn.disabled = False
                    self.status_label.text = "ПАРСЕР АКТИВЕН"
                    self.status_label.text_color = [0.3, 0.8, 0.3, 1]
                else:
                    self.start_btn.disabled = False
                    self.start_btn.md_bg_color = [0.2, 0.6, 0.2, 1]
                    self.stop_btn.disabled = True
                    self.status_label.text = "ПАРСЕР ОСТАНОВЛЕН"
                    self.status_label.text_color = [0.6, 0.6, 0.6, 1]

                stats = data.get('stats', {})
                self.total_card.update_value(stats.get('total_songs', 0))
                self.new_card.update_value(stats.get('new_songs', 0))
                self.dup_card.update_value(stats.get('duplicates', 0))
                self.err_card.update_value(stats.get('errors', 0))

                last_song = data.get('last_song', {})
                self._update_last_song_display(last_song)

        except Exception as e:
            print(f"DEBUG: Error in _fetch_status - {e}")

    def start_parser(self, *args):
        try:
            result = parser_client.star_accord_pro_parser_sync(0, 999)
            if result and result.get('success'):
                notify.success("Парсер Akkords.Pro запущен")
                self.last_song = None
                self.last_song_container.height = dp(0)
                self.last_song_container.clear_widgets()
                self._fetch_status()
            else:
                msg = result.get('message', 'Ошибка') if result else 'Ошибка соединения'
                notify.error(f"Ошибка: {msg}")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            notify.error(f"Ошибка: {e}")

    def stop_parser(self, *args):
        try:
            result = parser_client.stop_accord_pro_parser_sync()
            if result and result.get('success'):
                notify.info("Парсер Akkords.Pro остановлен")
                self._fetch_status()
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            notify.error(f"Ошибка: {e}")

    def on_enter(self):
        self.is_on_screen = True
        self.start_auto_update()

    def on_leave(self):
        self.is_on_screen = False
        self.stop_auto_update()