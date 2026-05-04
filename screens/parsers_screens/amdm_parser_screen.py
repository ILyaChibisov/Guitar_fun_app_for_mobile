# screens/parsers_screens/amdm_parser_screen.py
"""
Экран управления парсером AMDM - современный дизайн
"""
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from io import BytesIO

from utils.kivy_imports import (
    MDBoxLayout, MDLabel, MDCard, MDScreen,
    MDScrollView, MDRaisedButton
)
from kivymd.uix.textfield import MDTextField

from config.theme import theme
from config.logger_config import screen_logger
from utils.notifications import notify
from api.client import api

logger = screen_logger('AMDMParserScreen')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class StatCard(MDCard):
    """Карточка статистики (без иконок)"""

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
            text=str(value),
            font_size=sp(28),
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Custom",
            text_color=[color[0], color[1], color[2], 1]
        )

        self.title_label = MDLabel(
            text=title,
            font_size=sp(9),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )

        self.add_widget(self.value_label)
        self.add_widget(self.title_label)

    def update_value(self, value):
        self.value_label.text = str(value)


class RecentSongCard(MDCard):
    """Карточка последней песни с иконкой из ассета"""

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
        error = self.song_data.get('error', '')
        tab_number = self.song_data.get('tab_number', 0)

        if not filename:
            empty_label = MDLabel(
                text="Нет загруженных песен",
                halign="center",
                font_size=sp(12),
                theme_text_color="Custom",
                text_color=[0.5, 0.5, 0.5, 0.7]
            )
            self.add_widget(empty_label)
            return

        # Цвет фона в зависимости от статуса
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

        # Иконка из ассета
        icon_image = Image(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )

        if self.icon_data:
            try:
                img = CoreImage(BytesIO(self.icon_data), ext="png")
                icon_image.texture = img.texture
            except:
                pass

        # Название песни (будет растягиваться)
        name = filename.replace('.txt', '')
        if len(name) > 35:
            name = name[:32] + "..."

        name_label = MDLabel(
            text=name,
            font_size=sp(13),
            bold=True,
            size_hint_x=1,  # Растягивается на все доступное место
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            valign="middle"
        )

        # Статус
        status_label = MDLabel(
            text=status_text,
            font_size=sp(10),
            size_hint_x=None,
            width=dp(70),
            halign="center",
            bold=True,
            theme_text_color="Custom",
            text_color=line_color,
            valign="middle"
        )

        self.add_widget(icon_image)
        self.add_widget(name_label)
        self.add_widget(status_label)


class AMDMParserScreen(MDScreen):
    """Экран управления парсером AMDM"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'amdm_parser'
        self.update_event = None
        self.is_on_screen = False
        self.last_song = None
        self.song_icon_data = None
        self.md_bg_color = [0, 0, 0, 0]
        self.load_icon()
        self.init_ui()
        logger.info('Экран AMDM парсера создан')

    def load_icon(self):
        """Загрузить иконку песни из ассетов"""
        if HAS_ASSETS:
            try:
                self.song_icon_data = load_asset_as_bytes('song_png')
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки: {e}")

    def init_ui(self):
        scroll = MDScrollView(size_hint=(1, 1), do_scroll_x=False)

        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(65), dp(16), dp(16)],
            spacing=dp(12),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

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
            text="AMDM ПАРСЕР",
            font_size=sp(22),
            halign="center",
            bold=True,
            theme_text_color="Custom",
            text_color=[0.4, 0.7, 0.9, 1]
        )
        subtitle_label = MDLabel(
            text="загрузка аккордов с amdm.ru",
            font_size=sp(11),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )
        title_card.add_widget(title_label)
        title_card.add_widget(subtitle_label)
        main_layout.add_widget(title_card)

        # Настройки
        settings_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(170),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(12),
            radius=[16],
            md_bg_color=[0, 0, 0, 0.2],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1
        )

        # Поддомен
        self.subdomain_field = MDTextField(
            hint_text="Поддомен (amdm или 1-999)",
            mode="fill",
            size_hint_y=None,
            height=dp(50),
            text="amdm"
        )
        settings_card.add_widget(self.subdomain_field)

        # Диапазон страниц
        range_layout = MDBoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None, height=dp(70))

        range_label = MDLabel(
            text="ДИАПАЗОН СТРАНИЦ",
            font_size=sp(10),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6]
        )
        range_layout.add_widget(range_label)

        pages_row = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(42))

        self.start_page_field = MDTextField(
            hint_text="Страница от",
            mode="fill",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(42),
            text="0",
            input_filter="int"
        )

        self.end_page_field = MDTextField(
            hint_text="Страница до",
            mode="fill",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(42),
            text="54",
            input_filter="int"
        )

        pages_row.add_widget(self.start_page_field)
        pages_row.add_widget(self.end_page_field)
        range_layout.add_widget(pages_row)

        settings_card.add_widget(range_layout)
        main_layout.add_widget(settings_card)

        # Кнопки управления
        buttons_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(65),
            padding=[dp(12), dp(8), dp(12), dp(8)],
            radius=[12],
            md_bg_color=[0, 0, 0, 0.2],
            elevation=0
        )

        buttons_layout = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(48))

        self.start_btn = MDRaisedButton(
            text="ЗАПУСТИТЬ",
            size_hint_x=0.7,
            md_bg_color=[0.2, 0.6, 0.2, 1],
            font_size=sp(14)
        )
        self.start_btn.bind(on_release=self.start_parser)

        self.stop_btn = MDRaisedButton(
            text="ОСТАНОВИТЬ",
            size_hint_x=0.3,
            disabled=True,
            md_bg_color=[0.6, 0.2, 0.2, 1],
            font_size=sp(14)
        )
        self.stop_btn.bind(on_release=self.stop_parser)

        buttons_layout.add_widget(self.start_btn)
        buttons_layout.add_widget(self.stop_btn)
        buttons_card.add_widget(buttons_layout)
        main_layout.add_widget(buttons_card)

        # 4 карточки статистики (без иконок)
        stats_grid = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(85))

        self.total_card = StatCard("ВСЕГО", 0, [0.4, 0.7, 0.9])
        self.new_card = StatCard("НОВЫХ", 0, [0.3, 0.8, 0.3])
        self.dup_card = StatCard("ПОВТОРОВ", 0, [0.9, 0.7, 0.2])
        self.err_card = StatCard("ОШИБОК", 0, [0.9, 0.4, 0.4])

        stats_grid.add_widget(self.total_card)
        stats_grid.add_widget(self.new_card)
        stats_grid.add_widget(self.dup_card)
        stats_grid.add_widget(self.err_card)
        main_layout.add_widget(stats_grid)

        # Карточка последней песни (с иконкой из ассета)
        self.last_song_container = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(0))
        main_layout.add_widget(self.last_song_container)

        # Статус
        self.status_label = MDLabel(
            text="Готов к работе",
            halign="center",
            size_hint_y=None,
            height=dp(35),
            font_size=sp(11),
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 1]
        )
        main_layout.add_widget(self.status_label)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

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
            self.stop_auto_update()
            return
        self._fetch_status()

    def _fetch_status(self):
        try:
            result = api.get_amdm_parser_status_sync()

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
                    if self.update_event:
                        self.stop_auto_update()
                    return

                stats = data.get('stats', {})
                self.total_card.update_value(stats.get('total_songs', 0))
                self.new_card.update_value(stats.get('new_songs', 0))
                self.dup_card.update_value(stats.get('duplicates', 0))
                self.err_card.update_value(stats.get('errors', 0))

                last_song = data.get('last_song', {})

                if last_song and last_song.get('filename'):
                    if self.last_song != last_song.get('filename'):
                        self.last_song = last_song.get('filename')
                        self.last_song_container.clear_widgets()
                        self.last_song_container.height = dp(85)
                        song_card = RecentSongCard(song_data=last_song, icon_data=self.song_icon_data)
                        self.last_song_container.add_widget(song_card)
                elif self.last_song_container.height != 0:
                    self.last_song_container.height = dp(0)
                    self.last_song_container.clear_widgets()

        except Exception as e:
            print(f"DEBUG: Error - {e}")

    def start_parser(self, *args):
        try:
            start_page = int(self.start_page_field.text)
            end_page = int(self.end_page_field.text)
            subdomain = self.subdomain_field.text.strip()

            if start_page < 0 or start_page > 54:
                notify.error("Начальная страница должна быть от 0 до 54")
                return

            if end_page < 0 or end_page > 54:
                notify.error("Конечная страница должна быть от 0 до 54")
                return

            if start_page > end_page:
                notify.error("Начальная страница не может быть больше конечной")
                return

            if not subdomain:
                notify.error("Введите поддомен (amdm или 1-999)")
                return

            result = api.start_amdm_parser_sync(start_page, end_page, subdomain)
            if result and result.get('success'):
                notify.success(f"Парсер запущен (страницы {start_page}-{end_page})")
                self.last_song = None
                self.last_song_container.height = dp(0)
                self.last_song_container.clear_widgets()
                self.start_auto_update()
            else:
                msg = result.get('message', 'Ошибка') if result else 'Ошибка соединения'
                notify.error(f"Ошибка: {msg}")

        except ValueError:
            notify.error("Введите корректные номера страниц")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            notify.error(f"Ошибка: {e}")

    def stop_parser(self, *args):
        try:
            result = api.stop_amdm_parser_sync()
            if result and result.get('success'):
                notify.info("Парсер остановлен")
                self.stop_auto_update()
                self.status_label.text = "ПАРСЕР ОСТАНОВЛЕН"
                self.start_btn.disabled = False
                self.start_btn.md_bg_color = [0.2, 0.6, 0.2, 1]
                self.stop_btn.disabled = True
            else:
                api.stop_amdm_parser(
                    on_success=lambda x: (notify.info("Парсер остановлен"), self.stop_auto_update()),
                    on_failure=lambda x, e: notify.error(f"Ошибка: {e}")
                )
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            notify.error(f"Ошибка: {e}")

    def on_enter(self):
        self.is_on_screen = True
        self._fetch_status()

    def on_leave(self):
        self.is_on_screen = False
        self.stop_auto_update()