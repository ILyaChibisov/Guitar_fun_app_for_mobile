# screens/parsers_screens/amdm_parser_screen.py
"""
Экран управления парсером AMDM
"""
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.progressbar import ProgressBar

from utils.kivy_imports import (
    MDBoxLayout, MDLabel, MDCard, MDScreen,
    MDScrollView, MDRaisedButton, MDFlatButton
)
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.list import MDList, MDListItem, MDListItemHeadlineText, MDListItemSupportingText

from config.theme import theme
from config.logger_config import screen_logger
from utils.notifications import notify
from api.client import api

logger = screen_logger('AMDMParserScreen')


class AMDMParserScreen(MDScreen):
    """Экран управления парсером AMDM"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'amdm_parser'
        self.update_event = None
        self.md_bg_color = [0, 0, 0, 0]
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

        # ============ Заголовок ============
        title_label = MDLabel(
            text="🎵 Парсер AMDM.RU",
            font_size=sp(22),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            bold=True
        )
        main_layout.add_widget(title_label)

        # ============ Карточка настроек ============
        settings_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(320),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(10),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=2,
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        # Поддомен
        self.subdomain_field = MDTextField(
            mode="filled",
            size_hint_y=None,
            height=dp(65)
        )
        self.subdomain_field.add_widget(MDTextFieldHintText(text="Поддомен (amdm или 1-999)"))
        self.subdomain_field.text = "amdm"
        settings_card.add_widget(self.subdomain_field)

        # Страницы
        pages_layout = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(65))

        self.start_page_field = MDTextField(
            mode="filled",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(65)
        )
        self.start_page_field.add_widget(MDTextFieldHintText(text="Страница от"))
        self.start_page_field.text = "0"
        pages_layout.add_widget(self.start_page_field)

        self.end_page_field = MDTextField(
            mode="filled",
            size_hint_x=0.5,
            size_hint_y=None,
            height=dp(65)
        )
        self.end_page_field.add_widget(MDTextFieldHintText(text="Страница до"))
        self.end_page_field.text = "54"
        pages_layout.add_widget(self.end_page_field)

        settings_card.add_widget(pages_layout)

        # Кнопки управления
        buttons_layout = MDBoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(48))

        self.start_btn = MDRaisedButton(
            text="▶ ЗАПУСК",
            size_hint_x=0.25,
            on_release=self.start_parser
        )

        self.pause_btn = MDFlatButton(
            text="⏸ ПАУЗА",
            size_hint_x=0.25,
            disabled=True
        )
        self.pause_btn.bind(on_release=self.pause_parser)

        self.resume_btn = MDFlatButton(
            text="▶ ВОЗОБН.",
            size_hint_x=0.25,
            disabled=True
        )
        self.resume_btn.bind(on_release=self.resume_parser)

        self.stop_btn = MDFlatButton(
            text="⏹ СТОП",
            size_hint_x=0.25,
            disabled=True
        )
        self.stop_btn.bind(on_release=self.stop_parser)

        buttons_layout.add_widget(self.start_btn)
        buttons_layout.add_widget(self.pause_btn)
        buttons_layout.add_widget(self.resume_btn)
        buttons_layout.add_widget(self.stop_btn)

        settings_card.add_widget(buttons_layout)
        main_layout.add_widget(settings_card)

        # ============ Карточка прогресса ============
        progress_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(110),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(8),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15]
        )

        self.progress_label = MDLabel(
            text="Прогресс: 0%",
            halign="center",
            size_hint_y=None,
            height=dp(30),
            font_size=sp(14)
        )
        progress_card.add_widget(self.progress_label)

        # Используем обычный ProgressBar из Kivy вместо MDProgressBar
        self.progress_bar = ProgressBar(
            value=0,
            height=dp(8),
            size_hint_y=None
        )
        progress_card.add_widget(self.progress_bar)

        self.current_page_label = MDLabel(
            text="Текущая страница: -",
            halign="center",
            size_hint_y=None,
            height=dp(25),
            font_size=sp(12)
        )
        progress_card.add_widget(self.current_page_label)

        main_layout.add_widget(progress_card)

        # ============ Карточка статистики ============
        stats_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(90),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(8),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15]
        )

        self.stats_label = MDLabel(
            text="📊 Всего: 0 | 🆕 Новых: 0 | ❌ Ошибок: 0",
            halign="center",
            size_hint_y=None,
            height=dp(35),
            font_size=sp(12)
        )
        stats_card.add_widget(self.stats_label)

        self.status_label = MDLabel(
            text="⏸ Парсер не запущен",
            halign="center",
            size_hint_y=None,
            height=dp(30),
            font_size=sp(12)
        )
        stats_card.add_widget(self.status_label)

        main_layout.add_widget(stats_card)

        # ============ Список последних песен ============
        recent_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(350),
            padding=[dp(8), dp(8), dp(8), dp(8)],
            spacing=dp(4),
            radius=[theme.CORNER_RADIUS_SMALL],
            md_bg_color=[0, 0, 0, 0.15]
        )

        recent_header = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            padding=[dp(8), dp(0), dp(8), dp(0)]
        )
        recent_header.add_widget(MDLabel(
            text="📜 Последние песни",
            font_size=sp(14),
            bold=True
        ))

        recent_card.add_widget(recent_header)

        self.recent_list = MDList()
        recent_scroll = MDScrollView(size_hint=(1, 1))
        recent_scroll.add_widget(self.recent_list)
        recent_card.add_widget(recent_scroll)

        main_layout.add_widget(recent_card)

        # Кнопка обновить внизу
        refresh_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            padding=[dp(0), dp(8), dp(0), dp(0)]
        )

        self.refresh_btn = MDRaisedButton(
            text="🔄 ОБНОВИТЬ СТАТУС",
            size_hint_x=1,
            on_release=self.manual_refresh
        )
        refresh_layout.add_widget(self.refresh_btn)

        main_layout.add_widget(refresh_layout)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

        # Начинаем автоматическое обновление
        self.start_auto_update()

    def start_auto_update(self):
        """Начать автоматическое обновление статуса"""
        if self.update_event:
            self.update_event.cancel()
        self.update_event = Clock.schedule_interval(self.update_status, 2)

    def stop_auto_update(self):
        """Остановить автоматическое обновление"""
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def manual_refresh(self, *args):
        """Ручное обновление"""
        self.update_status()
        notify.info("Статус обновлен")

    def update_status(self, *args):
        """Обновить статус парсера"""
        try:
            result = api.get_amdm_parser_status_sync()
            if result and result.get('success'):
                data = result.get('data', {})

                # Обновляем прогресс
                progress = data.get('progress', 0)
                self.progress_bar.value = progress
                self.progress_label.text = f"Прогресс: {progress}%"

                # Текущая страница
                current_page = data.get('current_page', 0)
                self.current_page_label.text = f"Страница: {current_page}"

                # Статистика
                stats = data.get('stats', {})
                total = stats.get('total_songs', 0)
                new_songs = stats.get('new_songs', 0)
                errors = stats.get('errors', 0)
                self.stats_label.text = f"📊 Всего: {total} | 🆕 Новых: {new_songs} | ❌ Ошибок: {errors}"

                # Статус парсера
                is_running = data.get('is_running', False)
                is_paused = data.get('is_paused', False)

                if is_running and not is_paused:
                    self.status_label.text = "🟢 Парсер запущен и работает"
                    self.start_btn.disabled = True
                    self.pause_btn.disabled = False
                    self.stop_btn.disabled = False
                    self.resume_btn.disabled = True
                elif is_running and is_paused:
                    self.status_label.text = "⏸ Парсер на паузе"
                    self.start_btn.disabled = True
                    self.pause_btn.disabled = True
                    self.stop_btn.disabled = False
                    self.resume_btn.disabled = False
                else:
                    self.status_label.text = "⏹ Парсер остановлен"
                    self.start_btn.disabled = False
                    self.pause_btn.disabled = True
                    self.stop_btn.disabled = True
                    self.resume_btn.disabled = True

                # Обновляем список последних песен
                recent_songs = stats.get('recent_songs', [])
                self.recent_list.clear_widgets()

                if recent_songs:
                    for song in recent_songs[:10]:
                        filename = song.get('filename', 'Unknown')
                        status = song.get('status', 'unknown')

                        status_icon = "✅" if status == "new" else "⚠️" if status == "duplicate" else "❌"

                        item = MDListItem()
                        item.add_widget(MDListItemHeadlineText(text=f"{status_icon} {filename}"))
                        item.add_widget(MDListItemSupportingText(text=f"Статус: {status}"))
                        self.recent_list.add_widget(item)
                else:
                    empty_label = MDLabel(
                        text="Нет обработанных песен",
                        halign="center",
                        size_hint_y=None,
                        height=dp(40)
                    )
                    self.recent_list.add_widget(empty_label)

        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")

    def start_parser(self, *args):
        """Запустить парсер"""
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
                self.update_status()
            else:
                msg = result.get('message', 'Неизвестная ошибка') if result else 'Ошибка соединения'
                notify.error(f"Ошибка запуска: {msg}")

        except ValueError:
            notify.error("Введите корректные номера страниц")
        except Exception as e:
            logger.error(f"Ошибка запуска: {e}")
            notify.error(f"Ошибка: {e}")

    def pause_parser(self, *args):
        """Поставить на паузу"""
        try:
            api.pause_amdm_parser(
                on_success=lambda x: (notify.info("Парсер на паузе"), self.update_status()),
                on_failure=lambda x, e: notify.error(f"Ошибка: {e}")
            )
        except Exception as e:
            logger.error(f"Ошибка паузы: {e}")

    def resume_parser(self, *args):
        """Возобновить работу"""
        try:
            api.resume_amdm_parser(
                on_success=lambda x: (notify.success("Парсер возобновлен"), self.update_status()),
                on_failure=lambda x, e: notify.error(f"Ошибка: {e}")
            )
        except Exception as e:
            logger.error(f"Ошибка возобновления: {e}")

    def stop_parser(self, *args):
        """Остановить парсер"""
        try:
            api.stop_amdm_parser(
                on_success=lambda x: (notify.info("Парсер остановлен"), self.update_status()),
                on_failure=lambda x, e: notify.error(f"Ошибка: {e}")
            )
        except Exception as e:
            logger.error(f"Ошибка остановки: {e}")

    def on_enter(self):
        """При входе на экран"""
        self.start_auto_update()
        self.update_status()

    def on_leave(self):
        """При выходе с экрана"""
        self.stop_auto_update()