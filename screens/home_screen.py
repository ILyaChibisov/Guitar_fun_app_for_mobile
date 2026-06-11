# screens/home_screen.py - с горизонтальным скроллом разделов
"""
Главный экран гитарного приложения - с горизонтальным скроллом разделов
"""
from kivy.uix.floatlayout import FloatLayout
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
from screens.components.sections_scroll import SectionsScroll
from api.client import api
from utils.notifications import notify

logger = screen_logger('Home')


def hex_to_rgb(hex_color):
    """Конвертирует HEX цвет в RGB список"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


class AnimatedWelcomeLabel(FloatLayout):
    """Плавающий анимированный текст приветствия"""

    def __init__(self, username, on_complete=None, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.on_complete = on_complete

        self.size_hint = (1, 1)
        self.pos = (0, 0)

        top_padding = layout_config.get_top_padding() + dp(20)
        bottom_nav_height = dp(60)
        nav_bar_height = dp(48)
        bottom_padding = layout_config.get_bottom_padding() + bottom_nav_height + nav_bar_height + dp(20)

        self.container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(20), top_padding, dp(20), bottom_padding]
        )

        self.text_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(10)
        )

        self.line1 = MDLabel(
            text="Добро пожаловать,",
            font_size=sp(28),
            halign="center",
            valign="middle",
            size_hint=(1, 0.5),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=False
        )

        self.line2 = MDLabel(
            text=username,
            font_size=sp(36),
            halign="center",
            valign="middle",
            size_hint=(1, 0.5),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            bold=True
        )

        self.text_container.add_widget(self.line1)
        self.text_container.add_widget(self.line2)
        self.container.add_widget(self.text_container)
        self.add_widget(self.container)

        self.container.opacity = 0
        appear_anim = Animation(opacity=1, duration=0.4, t='out_quad')
        appear_anim.start(self.container)
        Clock.schedule_once(self._start_fade_out, 2.5)

    def _start_fade_out(self, dt):
        fade_anim = Animation(opacity=0, duration=0.3, t='in_quad')
        fade_anim.bind(on_complete=lambda *args: self._on_complete())
        fade_anim.start(self.container)

    def _on_complete(self):
        if self.parent:
            self.parent.remove_widget(self)
        if self.on_complete:
            self.on_complete()


class AnimatedLogoLabel(FloatLayout):
    """Плавающий анимированный текст логотипа"""

    def __init__(self, on_complete=None, **kwargs):
        super().__init__(**kwargs)
        self.on_complete = on_complete

        self.size_hint = (1, 1)
        self.pos = (0, 0)

        top_padding = layout_config.get_top_padding() + dp(20)
        bottom_nav_height = dp(60)
        nav_bar_height = dp(48)
        bottom_padding = layout_config.get_bottom_padding() + bottom_nav_height + nav_bar_height + dp(20)

        self.container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(20), top_padding, dp(20), bottom_padding]
        )

        self.text_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(8)
        )

        self.logo_label = MDLabel(
            text="GuitarFuns",
            font_size=sp(44),
            halign="center",
            valign="middle",
            size_hint=(1, 0.6),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            bold=True
        )

        self.subtitle = MDLabel(
            text="твои любимые песни и аккорды",
            font_size=sp(14),
            halign="center",
            valign="middle",
            size_hint=(1, 0.4),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            bold=False
        )

        self.text_container.add_widget(self.logo_label)
        self.text_container.add_widget(self.subtitle)
        self.container.add_widget(self.text_container)
        self.add_widget(self.container)

        self.container.opacity = 0
        self.container.scale = 0.85
        anim = Animation(opacity=1, scale=1, duration=0.4, t='out_back')
        anim.start(self.container)
        Clock.schedule_once(self._start_fade_out, 1.8)

    def _start_fade_out(self, dt):
        fade_anim = Animation(opacity=0, duration=0.3, t='in_quad')
        fade_anim.bind(on_complete=lambda *args: self._on_complete())
        fade_anim.start(self.container)

    def _on_complete(self):
        if self.parent:
            self.parent.remove_widget(self)
        if self.on_complete:
            self.on_complete()


class HomeScreen(BaseScreen):
    """Главный экран приложения с горизонтальным скроллом разделов"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        self.user = None
        self.auth_check_done = False
        self.welcome_label = None
        self.logo_label = None
        self.sections_scroll = None
        self.title = None
        self.section_title = None

        self.init_ui()
        Clock.schedule_once(self._check_auth, 0.5)
        logger.info('Главный экран создан')

    def init_ui(self):
        """Инициализирует UI с горизонтальным скроллом разделов"""

        # Основной контейнер
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ (под статус-бар и TopNav)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Дополнительный отступ сверху для эстетики
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))

        # Заголовок "GuitarFuns"
        self.title = MDLabel(
            text="GuitarFuns",
            font_size=dp(42),
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            size_hint_y=None,
            height=dp(60),
            opacity=0
        )
        main_layout.add_widget(self.title)

        # Небольшой отступ
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(16)))

        # Заголовок "РАЗДЕЛЫ ПРИЛОЖЕНИЯ" по центру
        self.section_title = MDLabel(
            text="РАЗДЕЛЫ ПРИЛОЖЕНИЯ",
            font_size=sp(16),
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            size_hint_y=None,
            height=dp(30),
            opacity=0
        )
        main_layout.add_widget(self.section_title)

        # Небольшой отступ перед карточками
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Горизонтальный скролл с карточками разделов
        self.sections_scroll = SectionsScroll(
            screen_manager=self.manager,
            on_section_selected=self._on_section_selected
        )
        self.sections_scroll.opacity = 0
        main_layout.add_widget(self.sections_scroll)

        # Добавляем растягивающийся виджет, чтобы прижать контент к верху
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

    def _show_welcome_sequence(self, username):
        """Показывает анимацию приветствия"""
        if self.welcome_label and self.welcome_label.parent:
            return
        if self.logo_label and self.logo_label.parent:
            return

        self.welcome_label = AnimatedWelcomeLabel(
            username,
            on_complete=self._on_welcome_closed
        )
        self.add_widget(self.welcome_label)

    def _on_welcome_closed(self):
        """После приветствия показываем логотип"""
        self.welcome_label = None

        self.logo_label = AnimatedLogoLabel(
            on_complete=self._on_logo_closed
        )
        self.add_widget(self.logo_label)

    def _on_logo_closed(self):
        """После логотипа показываем основной контент"""
        self.logo_label = None
        self._show_main_content()

    def _show_main_content(self):
        """Показывает основной контент с анимацией"""
        anim = Animation(opacity=1, duration=0.4, t='out_quad')
        anim.start(self.title)
        anim.start(self.section_title)
        anim.start(self.sections_scroll)

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
            logger.info("Нет токена, показываем основной контент")
            self._show_main_content()

    def _on_auth_success(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        logger.info(f'Пользователь авторизован: {username}')
        Clock.schedule_once(lambda dt: self._show_welcome_sequence(username), 0.2)

    def _on_auth_failure(self, req, error):
        logger.warning(f'Авторизация не пройдена: {error}')
        self._show_main_content()

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
        self._show_welcome_sequence(username)

    def on_pre_enter(self):
        """Перед входом на экран"""
        return super().on_pre_enter()

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в главный экран")

    def on_leave(self):
        """При выходе с экрана"""
        return super().on_leave()