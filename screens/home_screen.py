# screens/home_screen.py
"""
Главный экран гитарного приложения - с каруселью разделов и приветствием
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.components.section_carousel import SectionCarousel
from api.client import api

logger = screen_logger('Home')


def hex_to_rgb(hex_color):
    """Конвертирует HEX цвет в RGB список"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


class HomeScreen(BaseScreen):
    """Главный экран приложения с каруселью разделов и приветствием"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        self.user = None
        self.auth_check_done = False
        self.section_carousel = None
        self.welcome_line1 = None
        self.welcome_line2 = None

        self.init_ui()
        Clock.schedule_once(self._check_auth, 0.5)
        logger.info('Главный экран создан')

    def init_ui(self):
        """Инициализирует UI с каруселью разделов и приветствием"""

        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ (под статус-бар и TopNav)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Дополнительный отступ сверху
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Карусель с карточками разделов
        self.section_carousel = SectionCarousel(
            screen_manager=self.manager,
            on_section_selected=self._on_section_selected
        )
        main_layout.add_widget(self.section_carousel)

        # Приветствие под карточками
        welcome_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(80),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            padding=[dp(20), dp(8), dp(20), dp(8)]
        )

        self.welcome_line1 = MDLabel(
            text="",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            bold=False
        )

        self.welcome_line2 = MDLabel(
            text="",
            font_size=sp(20),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(32),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            bold=True
        )

        welcome_container.add_widget(self.welcome_line1)
        welcome_container.add_widget(self.welcome_line2)
        main_layout.add_widget(welcome_container)

        # Растягивающийся виджет
        main_layout.add_widget(Widget(size_hint_y=1))

        self.add_widget(main_layout)

        logger.info(f"HomeScreen: top_padding = {top_padding}dp")

    def _on_section_selected(self, screen_name):
        """Обработчик выбора раздела"""
        if screen_name and hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen(screen_name):
                self.manager.transition.direction = 'left'
                self.manager.current = screen_name
            else:
                logger.warning(f"Экран {screen_name} не найден")

    def _update_welcome(self, username):
        """Обновляет приветствие с именем пользователя"""
        if self.welcome_line1:
            self.welcome_line1.text = "Добро пожаловать,"
        if self.welcome_line2:
            self.welcome_line2.text = username
        logger.info(f"Приветствие обновлено для: {username}")

    def _check_auth(self, dt):
        """Проверяет авторизацию"""
        if self.auth_check_done:
            return
        self.auth_check_done = True

        if api.access_token:
            api.get_current_user(
                on_success=self._on_auth_success,
                on_failure=self._on_auth_failure
            )
        else:
            logger.info("Нет токена, показываем гостя")
            self._update_welcome("Гость")

    def _on_auth_success(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        logger.info(f'Пользователь авторизован: {username}')
        self._update_welcome(username)

    def _on_auth_failure(self, req, error):
        logger.warning(f'Авторизация не пройдена: {error}')
        self._update_welcome("Гость")

    def on_login_success(self):
        """Обработчик успешного входа"""
        if api.access_token:
            api.get_current_user(
                on_success=self._on_user_data_loaded,
                on_failure=lambda req, err: None
            )

    def _on_user_data_loaded(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        self._update_welcome(username)

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в главный экран")

    def on_leave(self):
        """При выходе с экрана"""
        return super().on_leave()