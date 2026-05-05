# screens/parsers_screens/accord_pro_parser_screen.py
"""
Экран управления парсером Akkords.Pro - простой запуск/остановка
Особенность: парсит по группам, не требует выбора букв
"""
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from io import BytesIO

from utils.kivy_imports import (
    MDBoxLayout, MDLabel, MDCard, MDScreen,
    MDScrollView, MDRaisedButton, MDFlatButton
)
from kivymd.uix.textfield import MDTextField

from config.theme import theme
from config.logger_config import screen_logger
from utils.notifications import notify
from api.client import api

logger = screen_logger('AccordProParserScreen')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class AccordProStatCard(MDCard):
    """Карточка статистики"""

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


class AccordProRecentSongCard(MDCard):
    """Карточка последней песни"""

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
                text="Нет загруженных песен",
                halign="center",
                font_size=sp(12),
                theme_text_color="Custom",
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

        name = filename.replace('.txt', '')
        if len(name) > 35:
            name = name[:32] + "..."

        name_label = MDLabel(
            text=name,
            font_size=sp(13),
            bold=True,
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            valign="middle"
        )

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


class AccordProParserScreen(MDScreen):
    """Экран управления парсером Akkords.Pro"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'accord_pro_parser'
        self.update_event = None
        self.is_on_screen = False
        self.last_song = None
        self.song_icon_data = None
        self.md_bg_color = [0, 0, 0, 0]
        self.load_icon()
        self.init_ui()
        logger.info('Экран Akkords.Pro парсера создан')

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
            text="AKKORDS.PRO ПАРСЕР",
            font_size=sp(22),
            halign="center",
            bold=True,
            theme_text_color="Custom",
            text_color=[0.9, 0.6, 0.3, 1]
        )
        subtitle_label = MDLabel(
            text="загрузка аккордов с akkords.pro",
            font_size=sp(11),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )
        title_card.add_widget(title_label)
        title_card.add_widget(subtitle_label)
        main_layout.add_widget(title_card)

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
            text="Парсер загружает все группы подряд\n"
                 "от начала до конца. Для остановки\n"
                 "используйте кнопку ОСТАНОВИТЬ",
            font_size=sp(12),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )
        info_card.add_widget(info_text)
        main_layout.add_widget(info_card)

        # Кнопки управления
        buttons_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            padding=[dp(12), dp(12), dp(12), dp(12)],
            spacing=dp(12),
            radius=[12],
            md_bg_color=[0, 0, 0, 0.2],
            elevation=0
        )

        self.start_btn = MDRaisedButton(
            text="ЗАПУСТИТЬ ПАРСЕР",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=[0.2, 0.6, 0.2, 1],
            font_size=sp(14)
        )
        self.start_btn.bind(on_release=self.start_parser)

        self.stop_btn = MDRaisedButton(
            text="ОСТАНОВИТЬ ПАРСЕР",
            size_hint=(1, None),
            height=dp(48),
            disabled=True,
            md_bg_color=[0.6, 0.2, 0.2, 1],
            font_size=sp(14)
        )
        self.stop_btn.bind(on_release=self.stop_parser)

        buttons_card.add_widget(self.start_btn)
        buttons_card.add_widget(self.stop_btn)
        main_layout.add_widget(buttons_card)

        # 4 карточки статистики
        stats_grid = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(85))

        self.total_card = AccordProStatCard("ВСЕГО", 0, [0.4, 0.7, 0.9])
        self.new_card = AccordProStatCard("НОВЫЕ", 0, [0.3, 0.8, 0.3])
        self.dup_card = AccordProStatCard("ПОВТОР", 0, [0.9, 0.7, 0.2])
        self.err_card = AccordProStatCard("ОШИБКИ", 0, [0.9, 0.4, 0.4])

        stats_grid.add_widget(self.total_card)
        stats_grid.add_widget(self.new_card)
        stats_grid.add_widget(self.dup_card)
        stats_grid.add_widget(self.err_card)
        main_layout.add_widget(stats_grid)

        # Карточка текущей группы
        self.group_card = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            radius=[12],
            md_bg_color=[0.2, 0.3, 0.4, 0.3],
            elevation=0
        )

        self.group_label = MDLabel(
            text="Текущая группа: --",
            font_size=sp(13),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8]
        )
        self.group_card.add_widget(self.group_label)
        main_layout.add_widget(self.group_card)

        # Карточка последней песни
        self.last_song_container = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(0))
        main_layout.add_widget(self.last_song_container)

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
        """Начать автоматическое обновление статуса"""
        if not self.is_on_screen:
            return
        if self.update_event:
            self.update_event.cancel()
        self.update_event = Clock.schedule_interval(self._check_status_loop, 2)

    def stop_auto_update(self):
        """Остановить автоматическое обновление"""
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def _check_status_loop(self, dt):
        """Периодическая проверка статуса"""
        if not self.is_on_screen:
            return
        self._fetch_status()

    def _fetch_status(self):
        """Выполнить запрос статуса парсера Akkords.Pro"""
        try:
            result = api.get_accord_pro_parser_status_sync()

            if result and result.get('success'):
                data = result.get('data', result)

                is_running = data.get('is_running', False)
                is_paused = data.get('is_paused', False)
                current_group = data.get('current_group', 0)
                start_group = data.get('start_group', 0)
                end_group = data.get('end_group', 0)

                # Обновляем отображение текущей группы
                if start_group != end_group:
                    self.group_label.text = f"Группа: {current_group + 1} / {end_group + 1}"
                else:
                    self.group_label.text = f"Текущая группа: {current_group + 1}"

                if is_running and not is_paused:
                    self.start_btn.disabled = True
                    self.start_btn.md_bg_color = [0.3, 0.3, 0.3, 1]
                    self.stop_btn.disabled = False
                    self.status_label.text = "ПАРСЕР АКТИВЕН"
                    self.status_label.text_color = [0.3, 0.8, 0.3, 1]
                elif is_running and is_paused:
                    self.start_btn.disabled = True
                    self.stop_btn.disabled = False
                    self.status_label.text = "ПАРСЕР НА ПАУЗЕ"
                    self.status_label.text_color = [0.9, 0.6, 0.1, 1]
                else:
                    self.start_btn.disabled = False
                    self.start_btn.md_bg_color = [0.2, 0.6, 0.2, 1]
                    self.stop_btn.disabled = True
                    self.status_label.text = "ПАРСЕР ОСТАНОВЛЕН"
                    self.status_label.text_color = [0.6, 0.6, 0.6, 1]

                # Обновляем статистику
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
                        song_card = AccordProRecentSongCard(song_data=last_song, icon_data=self.song_icon_data)
                        self.last_song_container.add_widget(song_card)
                elif self.last_song_container.height != 0:
                    self.last_song_container.height = dp(0)
                    self.last_song_container.clear_widgets()

        except Exception as e:
            print(f"DEBUG: Error in _fetch_status - {e}")

    def start_parser(self, *args):
        """Запустить парсер - парсит все группы от начала до конца"""
        try:
            # Запускаем парсер с диапазоном от 0 до большого числа (все группы)
            # Парсер сам ограничит количество доступных групп
            result = api.start_accord_pro_parser_sync(0, 999)

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
        """Остановить парсер"""
        try:
            result = api.stop_accord_pro_parser_sync()
            if result and result.get('success'):
                notify.info("Парсер Akkords.Pro остановлен")
                self._fetch_status()
            else:
                api.stop_accord_pro_parser(
                    on_success=lambda x: (notify.info("Парсер остановлен"), self._fetch_status()),
                    on_failure=lambda x, e: notify.error(f"Ошибка: {e}")
                )
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            notify.error(f"Ошибка: {e}")

    def on_enter(self):
        """При входе на экран"""
        self.is_on_screen = True
        self.start_auto_update()

    def on_leave(self):
        """При выходе с экрана"""
        self.is_on_screen = False
        self.stop_auto_update()