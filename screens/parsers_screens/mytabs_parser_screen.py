# screens/parsers_screens/mytabs_parser_screen.py
"""
Экран управления парсером MyTabs - современный дизайн
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

logger = screen_logger('MyTabsParserScreen')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

MYTABS_LETTERS = [
    '0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М',
    'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ',
    'Ы', 'Э', 'Ю', 'Я'
]

LETTER_TO_PAGE_MYTABS = {letter: idx for idx, letter in enumerate(MYTABS_LETTERS)}


class MyTabsLetterButton(ButtonBehavior, BoxLayout):
    def __init__(self, letter, on_select, **kwargs):
        super().__init__(**kwargs)
        self.letter = letter
        self.on_select = on_select
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(48)
        letter_label = Label(text=letter, font_size=sp(16), color=[1, 1, 1, 1], bold=True,
                             halign='center', valign='middle')
        self.add_widget(letter_label)
        self.bind(on_release=self._on_release)

    def _on_release(self, instance):
        self.on_select(self.letter)


class MyTabsCloseButton(ButtonBehavior, BoxLayout):
    def __init__(self, on_close, **kwargs):
        super().__init__(**kwargs)
        self.on_close = on_close
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (dp(40), dp(40))
        close_label = Label(text="✕", font_size=sp(20), color=[0.9, 0.3, 0.3, 1],
                            bold=True, halign='center', valign='middle')
        self.add_widget(close_label)
        self.bind(on_release=lambda x: self.on_close())


class MyTabsLetterSelector(ButtonBehavior, BoxLayout):
    def __init__(self, title="Буква", on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (0.48, None)
        self.height = dp(42)
        self.on_select_callback = on_select
        self.current_letter = 'А'
        self.popup = None

        self.title_label = Label(text=title, font_size=sp(11), color=[0.7, 0.7, 0.7, 1],
                                 size_hint=(0.4, 1), halign='center', valign='middle')
        self.value_label = Label(text=self.current_letter, font_size=sp(16), color=[1, 1, 1, 1],
                                 bold=True, size_hint=(0.4, 1), halign='center', valign='middle')
        self.arrow_label = Label(text="▼", font_size=sp(12), color=[0.7, 0.7, 0.7, 1],
                                 size_hint=(0.2, 1), halign='center', valign='middle')
        self.add_widget(self.title_label)
        self.add_widget(self.value_label)
        self.add_widget(self.arrow_label)
        self.bind(on_release=self._open_popup)
        self._create_popup()

    def _create_popup(self):
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=[dp(16), dp(16), dp(16), dp(16)],
                            size_hint=(1, 1))
        header = BoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(50), spacing=dp(10))
        header_title = Label(text="ВЫБЕРИТЕ БУКВУ (MYTABS)", font_size=sp(16), color=[1, 1, 1, 1],
                             bold=True, size_hint_x=1)
        close_btn = MyTabsCloseButton(on_close=self._close_popup)
        header.add_widget(header_title)
        header.add_widget(close_btn)
        content.add_widget(header)
        grid = GridLayout(cols=8, spacing=dp(6), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        for letter in MYTABS_LETTERS:
            letter_btn = MyTabsLetterButton(letter=letter, on_select=self._select_letter)
            grid.add_widget(letter_btn)
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True)
        scroll.add_widget(grid)
        content.add_widget(scroll)
        self.popup = Popup(title="", content=content, size_hint=(1, 1), background_color=[0.08, 0.08, 0.08, 0.98],
                           separator_color=[0, 0, 0, 0], auto_dismiss=True, overlay_color=[0, 0, 0, 0.8])

    def _close_popup(self):
        if self.popup:
            self.popup.dismiss()

    def _open_popup(self, instance):
        if self.popup:
            self.popup.open()

    def _select_letter(self, letter):
        self.current_letter = letter
        self.value_label.text = letter
        self._close_popup()
        if self.on_select_callback:
            self.on_select_callback(letter)

    def get_letter(self):
        return self.current_letter


class MyTabsStatCard(MDCard):
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
        self.value_label = MDLabel(text=str(value), font_size=sp(28), bold=True, halign="center",
                                   size_hint_y=None, height=dp(36), theme_text_color="Custom",
                                   text_color=[color[0], color[1], color[2], 1])
        self.title_label = MDLabel(text=title, font_size=sp(9), halign="center", size_hint_y=None, height=dp(20),
                                   theme_text_color="Custom", text_color=[1, 1, 1, 0.6])
        self.add_widget(self.value_label)
        self.add_widget(self.title_label)

    def update_value(self, value):
        self.value_label.text = str(value)


class MyTabsRecentSongCard(MDCard):
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
            empty_label = MDLabel(text="Нет загруженных песен", halign="center", font_size=sp(12),
                                  theme_text_color="Custom", text_color=[0.5, 0.5, 0.5, 0.7])
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
        icon_image = Image(size_hint=(None, None), size=(dp(32), dp(32)), pos_hint={'center_y': 0.5},
                           allow_stretch=True, keep_ratio=True)
        if self.icon_data:
            try:
                img = CoreImage(BytesIO(self.icon_data), ext="png")
                icon_image.texture = img.texture
            except:
                pass
        name = filename.replace('.txt', '')
        if len(name) > 35:
            name = name[:32] + "..."
        name_label = MDLabel(text=name, font_size=sp(13), bold=True, size_hint_x=1,
                             theme_text_color="Custom", text_color=[1, 1, 1, 0.95], valign="middle")
        status_label = MDLabel(text=status_text, font_size=sp(10), size_hint_x=None, width=dp(70),
                               halign="center", bold=True, theme_text_color="Custom",
                               text_color=line_color, valign="middle")
        self.add_widget(icon_image)
        self.add_widget(name_label)
        self.add_widget(status_label)


class MyTabsParserScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'mytabs_parser'
        self.update_event = None
        self.is_on_screen = False
        self.last_song = None
        self.song_icon_data = None
        self.md_bg_color = [0, 0, 0, 0]
        self.load_icon()
        self.init_ui()
        logger.info('Экран MyTabs парсера создан')

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
        scroll = MDScrollView(size_hint=(1, 1), do_scroll_x=False)

        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(65), dp(16), dp(16)],
            spacing=dp(12),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

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
            text="MYTABS ПАРСЕР",
            font_size=sp(22),
            halign="center",
            bold=True,
            theme_text_color="Custom",
            text_color=[0.7, 0.5, 0.9, 1]
        )
        subtitle_label = MDLabel(
            text="загрузка аккордов с mytabs.ru",
            font_size=sp(11),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )
        title_card.add_widget(title_label)
        title_card.add_widget(subtitle_label)
        main_layout.add_widget(title_card)

        settings_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(180),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(12),
            radius=[16],
            md_bg_color=[0, 0, 0, 0.2],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1
        )

        self.subdomain_field = MDTextField(
            hint_text="Поддомен (mytabs)",
            mode="fill",
            size_hint_y=None,
            height=dp(50),
            text="mytabs"
        )
        settings_card.add_widget(self.subdomain_field)

        letters_layout = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(50))

        self.start_letter_selector = MyTabsLetterSelector(
            title="ОТ",
            on_select=self.on_start_letter_selected
        )

        self.end_letter_selector = MyTabsLetterSelector(
            title="ДО",
            on_select=self.on_end_letter_selected
        )

        letters_layout.add_widget(self.start_letter_selector)
        letters_layout.add_widget(self.end_letter_selector)
        settings_card.add_widget(letters_layout)
        main_layout.add_widget(settings_card)

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
            text="ЗАПУСТИТЬ",
            size_hint_x=0.45,
            md_bg_color=[0.2, 0.6, 0.2, 1],
            font_size=sp(13)
        )
        self.start_btn.bind(on_release=self.start_parser)

        self.stop_btn = MDRaisedButton(
            text="ОСТАНОВИТЬ",
            size_hint_x=0.45,
            disabled=True,
            md_bg_color=[0.6, 0.2, 0.2, 1],
            font_size=sp(13)
        )
        self.stop_btn.bind(on_release=self.stop_parser)

        self.exit_btn = MDRaisedButton(
            text="ВЫХОД",
            size_hint_x=0.45,
            md_bg_color=[0.4, 0.4, 0.8, 1],
            font_size=sp(13)
        )
        self.exit_btn.bind(on_release=self.exit_to_admin)

        buttons_layout.add_widget(self.start_btn)
        buttons_layout.add_widget(self.stop_btn)
        buttons_layout.add_widget(self.exit_btn)
        buttons_card.add_widget(buttons_layout)
        main_layout.add_widget(buttons_card)

        stats_grid = MDBoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(85))

        self.total_card = MyTabsStatCard("ВСЕГО", 0, [0.4, 0.7, 0.9])
        self.new_card = MyTabsStatCard("НОВЫЕ", 0, [0.3, 0.8, 0.3])
        self.dup_card = MyTabsStatCard("ПОВТОР", 0, [0.9, 0.7, 0.2])
        self.err_card = MyTabsStatCard("ОШИБКИ", 0, [0.9, 0.4, 0.4])

        stats_grid.add_widget(self.total_card)
        stats_grid.add_widget(self.new_card)
        stats_grid.add_widget(self.dup_card)
        stats_grid.add_widget(self.err_card)
        main_layout.add_widget(stats_grid)

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

    def on_start_letter_selected(self, letter):
        pass

    def on_end_letter_selected(self, letter):
        pass

    def _get_page_from_letter(self, letter):
        return LETTER_TO_PAGE_MYTABS.get(letter, 0)

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

    # ============ НОВЫЕ МЕТОДЫ ДЛЯ ФИЛЬТРАЦИИ ============

    def _is_real_song(self, filename, status):
        """
        Проверяет, является ли запись реальной песней.
        Возвращает True только для настоящих песен.
        """
        if status not in ['new', 'duplicate', 'error']:
            return False

        if not filename:
            return False

        # Проверяем, что это не служебное сообщение
        service_patterns = [
            'Буква:', 'Группа:', 'Цифра:', 'Обработка',
            'Найдено', 'Запуск', 'Завершение', 'Получение',
            'Поиск файлов', 'Удаление файлов', 'Список скачанных'
        ]

        filename_lower = filename.lower()
        for pattern in service_patterns:
            if pattern.lower() in filename_lower:
                return False

        # Реальная песня должна содержать дефис (Артист - Песня) или заканчиваться на .txt
        if ' - ' in filename or filename.endswith('.txt'):
            # Дополнительная проверка: не слишком короткое имя
            if len(filename) > 5:
                return True

        return False

    def _update_last_song_display(self, last_song):
        """Обновляет отображение последней песни, показывая только реальные песни"""
        if not last_song:
            if self.last_song_container.height != 0:
                self.last_song_container.height = dp(0)
                self.last_song_container.clear_widgets()
                self.last_song = None
            return

        filename = last_song.get('filename', '')
        status = last_song.get('status', 'unknown')

        # Показываем только реальные песни
        if self._is_real_song(filename, status):
            if self.last_song != filename:
                self.last_song = filename
                self.last_song_container.clear_widgets()
                self.last_song_container.height = dp(85)
                song_card = MyTabsRecentSongCard(song_data=last_song, icon_data=self.song_icon_data)
                self.last_song_container.add_widget(song_card)
        else:
            # Для служебных сообщений очищаем карточку
            if self.last_song_container.height != 0:
                self.last_song_container.height = dp(0)
                self.last_song_container.clear_widgets()
                self.last_song = None

    # ============ ОСНОВНЫЕ МЕТОДЫ ============

    def _check_status_loop(self, dt):
        if not self.is_on_screen:
            return
        self._fetch_status()

    def _fetch_status(self):
        try:
            result = api.get_mytabs_parser_status_sync()
            if result and result.get('success'):
                data = result.get('data', result)

                is_running = data.get('is_running', False)
                is_paused = data.get('is_paused', False)

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

                stats = data.get('stats', {})
                self.total_card.update_value(stats.get('total_songs', 0))
                self.new_card.update_value(stats.get('new_songs', 0))
                self.dup_card.update_value(stats.get('duplicates', 0))
                self.err_card.update_value(stats.get('errors', 0))

                last_song = data.get('last_song', {})

                # Используем фильтрацию для последней песни
                self._update_last_song_display(last_song)

        except Exception as e:
            print(f"DEBUG: Error in _fetch_status - {e}")

    def start_parser(self, *args):
        try:
            start_letter = self.start_letter_selector.get_letter()
            end_letter = self.end_letter_selector.get_letter()
            start_page = self._get_page_from_letter(start_letter)
            end_page = self._get_page_from_letter(end_letter)
            subdomain = self.subdomain_field.text.strip()

            if start_page > end_page:
                notify.error("Начальная буква не может быть позже конечной")
                return

            if not subdomain:
                notify.error("Введите поддомен (mytabs)")
                return

            result = api.start_mytabs_parser_sync(start_page, end_page, subdomain)
            if result and result.get('success'):
                notify.success(f"Парсер MyTabs запущен (буквы {start_letter}-{end_letter})")
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
            result = api.stop_mytabs_parser_sync()
            if result and result.get('success'):
                notify.info("Парсер MyTabs остановлен")
                self._fetch_status()
            else:
                api.stop_mytabs_parser(
                    on_success=lambda x: (notify.info("Парсер остановлен"), self._fetch_status()),
                    on_failure=lambda x, e: notify.error(f"Ошибка: {e}")
                )
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            notify.error(f"Ошибка: {e}")

    def on_enter(self):
        self.is_on_screen = True
        self.start_auto_update()

    def on_leave(self):
        self.is_on_screen = False
        self.stop_auto_update()