# screens/parsers_screens/amdm_parser_screen.py
"""
Экран управления парсером AMDM для KivyMD 1.2
"""
from kivy.clock import Clock
from kivy.metrics import dp, sp

from utils.kivy_imports import (
    MDBoxLayout, MDLabel, MDCard, MDScreen,
    MDScrollView, MDRaisedButton, MDFlatButton
)
from kivymd.uix.textfield import MDTextField

from config.theme import theme
from config.logger_config import screen_logger
from utils.notifications import notify
from api.client import api

logger = screen_logger('AMDMParserScreen')


class RecentSongCard(MDCard):
    """Карточка для отображения последней песни"""

    def __init__(self, song_data=None, **kwargs):
        super().__init__(**kwargs)
        self.song_data = song_data or {}
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(80)
        self.padding = [dp(16), dp(12), dp(16), dp(12)]
        self.spacing = dp(4)
        self.radius = [theme.CORNER_RADIUS_SMALL]
        self.elevation = 2
        self.line_width = 1

        self.update_content()

    def update_content(self, song_data=None):
        """Обновить содержимое карточки"""
        if song_data:
            self.song_data = song_data

        self.clear_widgets()

        filename = self.song_data.get('filename', 'Нет данных')
        status = self.song_data.get('status', 'unknown')
        error = self.song_data.get('error', '')
        url = self.song_data.get('url', '')
        tab_number = self.song_data.get('tab_number', 0)

        # Определяем цвет и иконку в зависимости от статуса
        if status == 'new':
            bg_color = [0.2, 0.6, 0.2, 0.3]
            line_color = [0.3, 0.8, 0.3, 0.8]
            icon = "✅"
            status_text = "НОВАЯ"
        elif status == 'duplicate':
            bg_color = [0.8, 0.6, 0.1, 0.3]
            line_color = [0.9, 0.7, 0.2, 0.8]
            icon = "⚠️"
            status_text = "ДУБЛИКАТ"
        elif status == 'error':
            bg_color = [0.8, 0.2, 0.2, 0.3]
            line_color = [0.9, 0.3, 0.3, 0.8]
            icon = "❌"
            status_text = "ОШИБКА"
        elif status == 'db_error':
            bg_color = [0.6, 0.3, 0.6, 0.3]
            line_color = [0.7, 0.4, 0.7, 0.8]
            icon = "💾"
            status_text = "ОШИБКА БД"
        else:
            bg_color = [0.3, 0.3, 0.3, 0.3]
            line_color = [0.5, 0.5, 0.5, 0.8]
            icon = "⏸"
            status_text = "ОЖИДАНИЕ"

        self.md_bg_color = bg_color
        self.line_color = line_color

        header_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=dp(8))

        icon_label = MDLabel(text=icon, font_size=sp(20), size_hint_x=None, width=dp(32), halign="center")
        name_label = MDLabel(text=filename[:40] + "..." if len(filename) > 40 else filename, font_size=sp(13),
                             bold=True, size_hint_x=0.7)
        status_label = MDLabel(text=status_text, font_size=sp(11), size_hint_x=None, width=dp(85), halign="center",
                               bold=True)

        header_layout.add_widget(icon_label)
        header_layout.add_widget(name_label)
        header_layout.add_widget(status_label)

        footer_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(25), spacing=dp(8))

        if error:
            error_label = MDLabel(text=f"⚠️ {error[:50]}", font_size=sp(10),
                                  theme_text_color="Custom",
                                  text_color=[0.9, 0.7, 0.3, 1])
            footer_layout.add_widget(error_label)
        elif url:
            url_label = MDLabel(text=f"🔗 {url[:50]}..." if len(url) > 50 else f"🔗 {url}", font_size=sp(9),
                                theme_text_color="Custom", text_color=[0.7, 0.7, 0.7, 0.8])
            footer_layout.add_widget(url_label)

        if tab_number:
            tab_label = MDLabel(text=f"подбор {tab_number}", font_size=sp(10), size_hint_x=None, width=dp(60),
                                halign="right", theme_text_color="Custom", text_color=[0.7, 0.7, 0.7, 0.6])
            footer_layout.add_widget(tab_label)

        self.add_widget(header_layout)
        self.add_widget(footer_layout)


class AMDMParserScreen(MDScreen):
    """Экран управления парсером AMDM"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'amdm_parser'
        self.update_event = None
        self.is_parser_running = False
        self.md_bg_color = [0, 0, 0, 0]
        self.last_song = None
        self.init_ui()
        logger.info('Экран AMDM парсера создан')

    def init_ui(self):
        scroll = MDScrollView(size_hint=(1, 1), do_scroll_x=False)

        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(65), dp(16), dp(16)],
            spacing=dp(12),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        title_label = MDLabel(text="🎵 Парсер AMDM.RU", font_size=sp(22), halign="center", size_hint_y=None,
                              height=dp(50), bold=True)
        main_layout.add_widget(title_label)

        # Карточка настроек
        settings_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(280),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(10),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        # Поле поддомена (KivyMD 1.2: mode="fill")
        self.subdomain_field = MDTextField(
            hint_text="Поддомен (amdm или 1-999)",
            mode="fill",
            size_hint_y=None,
            height=dp(55),
            text="amdm"
        )
        settings_card.add_widget(self.subdomain_field)

        # Контейнер для полей страниц
        pages_layout = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(55))

        # Поле "Страница от"
        self.start_page_field = MDTextField(
            hint_text="Страница от",
            mode="fill",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(55),
            text="0"
        )

        # Поле "Страница до"
        self.end_page_field = MDTextField(
            hint_text="Страница до",
            mode="fill",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(55),
            text="54"
        )

        pages_layout.add_widget(self.start_page_field)
        pages_layout.add_widget(self.end_page_field)

        settings_card.add_widget(pages_layout)

        # Кнопки управления
        buttons_layout = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(48))

        self.start_btn = MDRaisedButton(text="▶ ЗАПУСК", size_hint_x=0.33, on_release=self.start_parser)
        self.pause_btn = MDFlatButton(text="⏸ ПАУЗА", size_hint_x=0.33, disabled=True)
        self.pause_btn.bind(on_release=self.pause_parser)
        self.stop_btn = MDFlatButton(text="⏹ СТОП", size_hint_x=0.34, disabled=True)
        self.stop_btn.bind(on_release=self.stop_parser)

        buttons_layout.add_widget(self.start_btn)
        buttons_layout.add_widget(self.pause_btn)
        buttons_layout.add_widget(self.stop_btn)

        settings_card.add_widget(buttons_layout)
        main_layout.add_widget(settings_card)

        # Карточка статистики
        stats_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(100),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(8),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15]
        )

        self.stats_label = MDLabel(text="📊 Всего: 0 | 🆕 Новых: 0 | ❌ Ошибок: 0", halign="center",
                                   size_hint_y=None, height=dp(35), font_size=sp(13), bold=True)
        stats_card.add_widget(self.stats_label)

        self.status_label = MDLabel(text="⏸ Парсер не запущен", halign="center", size_hint_y=None,
                                    height=dp(30), font_size=sp(12))
        stats_card.add_widget(self.status_label)

        main_layout.add_widget(stats_card)

        # Карточка последней песни
        last_song_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(100),
            padding=[dp(8), dp(8), dp(8), dp(8)],
            spacing=dp(4),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15]
        )

        last_song_header = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30),
                                       padding=[dp(8), dp(0), dp(8), dp(0)])
        last_song_header.add_widget(MDLabel(text="🎵 ПОСЛЕДНЯЯ ПЕСНЯ", font_size=sp(12), bold=True))
        last_song_card.add_widget(last_song_header)

        self.last_song_container = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(70))
        last_song_card.add_widget(self.last_song_container)

        main_layout.add_widget(last_song_card)

        bottom_spacer = MDBoxLayout(size_hint_y=None, height=dp(20))
        main_layout.add_widget(bottom_spacer)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

    def start_auto_update(self):
        if self.update_event:
            self.update_event.cancel()
        self.update_event = Clock.schedule_interval(self._check_status_loop, 2)

    def stop_auto_update(self):
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def _check_status_loop(self, dt):
        """Периодическая проверка статуса"""
        self._fetch_status()

    def _fetch_status(self):
        """Выполнить запрос статуса"""
        try:
            result = api.get_amdm_parser_status_sync()
            print(f"DEBUG: Status result = {result}")

            if result and result.get('success'):
                # Для KivyMD 1.2 данные приходят напрямую, без вложенного 'data'
                data = result.get('data', result)

                # Проверяем структуру - если есть поле 'stats' значит это data
                if 'stats' in data:
                    # Уже в правильном формате
                    pass
                elif 'total_songs' in data:
                    # Данные пришли как есть
                    data = {'stats': data, 'is_running': data.get('is_running', False)}

                is_running = data.get('is_running', False)
                is_paused = data.get('is_paused', False)

                # Обновляем кнопки
                if is_running and not is_paused:
                    self.start_btn.disabled = True
                    self.pause_btn.disabled = False
                    self.stop_btn.disabled = False
                    self.status_label.text = "🟢 Парсер запущен и работает"
                elif is_running and is_paused:
                    self.start_btn.disabled = True
                    self.pause_btn.disabled = True
                    self.stop_btn.disabled = False
                    self.status_label.text = "⏸ Парсер на паузе"
                else:
                    self.start_btn.disabled = False
                    self.pause_btn.disabled = True
                    self.stop_btn.disabled = True
                    self.status_label.text = "⏹ Парсер остановлен"

                # Обновляем статистику
                stats = data.get('stats', {})
                total = stats.get('total_songs', 0)
                new_songs = stats.get('new_songs', 0)
                errors = stats.get('errors', 0)
                duplicates = stats.get('duplicates', 0)

                self.stats_label.text = f"📊 Всего: {total} | 🆕 Новых: {new_songs} | ⚠️ Повторов: {duplicates} | ❌ Ошибок: {errors}"

                # Обновляем последнюю песню (проверяем оба возможных формата)
                recent_songs = stats.get('recent_songs', [])
                last_song = data.get('last_song', {})

                # Если есть массив recent_songs, берем первый элемент
                if recent_songs and len(recent_songs) > 0:
                    song_data = recent_songs[0]
                elif last_song and last_song.get('filename'):
                    song_data = last_song
                else:
                    song_data = None

                if song_data and song_data.get('filename'):
                    if self.last_song != song_data.get('filename'):
                        self.last_song = song_data.get('filename')
                        self.last_song_container.clear_widgets()
                        song_card = RecentSongCard(song_data=song_data)
                        self.last_song_container.add_widget(song_card)
                        print(f"DEBUG: Updated last song: {song_data.get('filename')}")

        except Exception as e:
            print(f"DEBUG: Error in _fetch_status - {e}")

    def start_parser(self, *args):
        try:
            start_page = int(self.start_page_field.text)
            end_page = int(self.end_page_field.text)
            subdomain = self.subdomain_field.text.strip()

            if start_page > end_page:
                notify.error("Начальная страница не может быть больше конечной")
                return

            if not subdomain:
                notify.error("Введите поддомен (amdm или 1-999)")
                return

            result = api.start_amdm_parser_sync(start_page, end_page, subdomain)
            if result and result.get('success'):
                notify.success(f"Парсер AMDM запущен (страницы {start_page}-{end_page})")
                self.last_song = None
                self.last_song_container.clear_widgets()
                self.start_auto_update()
            else:
                msg = result.get('message', 'Неизвестная ошибка') if result else 'Ошибка соединения'
                notify.error(f"Ошибка запуска: {msg}")

        except ValueError:
            notify.error("Введите корректные номера страниц")
        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
            notify.error(f"Ошибка: {e}")

    def pause_parser(self, *args):
        try:
            api.pause_amdm_parser(
                on_success=lambda x: notify.info("Парсер на паузе"),
                on_failure=lambda x, e: notify.error(f"Ошибка: {e}")
            )
        except Exception as e:
            logger.error(f"Ошибка паузы: {e}")

    def stop_parser(self, *args):
        try:
            api.stop_amdm_parser(
                on_success=lambda x: (notify.info("Парсер остановлен"), self.stop_auto_update()),
                on_failure=lambda x, e: notify.error(f"Ошибка: {e}")
            )
        except Exception as e:
            logger.error(f"Ошибка остановки: {e}")

    def on_enter(self):
        """При входе на экран"""
        self.start_auto_update()

    def on_leave(self):
        """При выходе с экрана"""
        self.stop_auto_update()