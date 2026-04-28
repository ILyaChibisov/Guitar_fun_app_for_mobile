# screens/home_screen.py
"""
Главный экран гитарного приложения
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp

from config.theme import theme
from config.carousel_config import CarouselConfig
from config.logger_config import screen_logger
from screens.components.carousel import MainCarousel
from api.client import api
from utils.notifications import notify
from utils.kivy_imports import MDRaisedButton, MDIconButton, MDBoxLayout

logger = screen_logger('Home')


class LoginModal(MDCard):
    def __init__(self, parent_screen, on_close=None, on_login_success=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.on_close_callback = on_close
        self.on_login_success_callback = on_login_success

        self.orientation = 'vertical'
        self.size_hint = (0.85, None)
        self.height = dp(280)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 4
        self.radius = [theme.CORNER_RADIUS] * 4
        self.md_bg_color = theme.SURFACE
        self.padding = [dp(16), dp(16), dp(16), dp(16)]
        self.spacing = dp(12)

        back_btn = MDIconButton()
        back_btn.icon = "arrow-left"
        back_btn.pos_hint = {'x': 0, 'top': 1}
        back_btn.size_hint = (None, None)
        back_btn.size = (dp(32), dp(32))
        back_btn.theme_icon_color = "Custom"
        back_btn.icon_color = theme.TEXT_SECONDARY
        back_btn.on_release = self.close
        self.add_widget(back_btn)

        title = MDLabel(text="Вход в аккаунт", halign="center",
                        size_hint_y=None, height=dp(36), theme_text_color="Primary",
                        bold=True, font_size=dp(20))
        self.add_widget(title)

        self.username_field = MDTextField(hint_text="Имя пользователя или Email", mode="filled",
                                          size_hint_y=None, height=dp(56),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.username_field)

        self.password_field = MDTextField(hint_text="Пароль", mode="filled", password=True,
                                          size_hint_y=None, height=dp(56),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.password_field)

        buttons_box = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(44))

        cancel_btn = MDRaisedButton(text="Отмена", size_hint=(0.5, 1),
                                    on_release=self.close)

        login_btn = MDRaisedButton(text="Войти", size_hint=(0.5, 1),
                                   on_release=self.do_login)

        buttons_box.add_widget(cancel_btn)
        buttons_box.add_widget(login_btn)
        self.add_widget(buttons_box)

    def close(self, instance=None):
        if self.on_close_callback:
            self.on_close_callback()
        if self.parent:
            self.parent.remove_widget(self)

    def do_login(self, instance):
        username = self.username_field.text
        password = self.password_field.text
        if not username or not password:
            notify.warning("Заполните все поля")
            return
        api.login(username=username, password=password,
                  on_success=self.on_login_success, on_failure=self.on_login_failure)

    def on_login_success(self, result):
        notify.success("Вход выполнен успешно!")
        self.close()
        if self.on_login_success_callback:
            self.on_login_success_callback()

    def on_login_failure(self, req, error):
        notify.error("Неверное имя пользователя или пароль")


class RegisterModal(MDCard):
    def __init__(self, parent_screen, on_close=None, on_register_success=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.on_close_callback = on_close
        self.on_register_success_callback = on_register_success

        self.orientation = 'vertical'
        self.size_hint = (0.85, None)
        self.height = dp(340)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 4
        self.radius = [theme.CORNER_RADIUS] * 4
        self.md_bg_color = theme.SURFACE
        self.padding = [dp(16), dp(16), dp(16), dp(16)]
        self.spacing = dp(8)

        back_btn = MDIconButton()
        back_btn.icon = "arrow-left"
        back_btn.pos_hint = {'x': 0, 'top': 1}
        back_btn.size_hint = (None, None)
        back_btn.size = (dp(32), dp(32))
        back_btn.theme_icon_color = "Custom"
        back_btn.icon_color = theme.TEXT_SECONDARY
        back_btn.on_release = self.close
        self.add_widget(back_btn)

        title = MDLabel(text="Регистрация", halign="center",
                        size_hint_y=None, height=dp(32), theme_text_color="Primary",
                        bold=True, font_size=dp(20))
        self.add_widget(title)

        self.username_field = MDTextField(hint_text="Имя пользователя", mode="filled",
                                          size_hint_y=None, height=dp(52),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.username_field)

        self.email_field = MDTextField(hint_text="Email", mode="filled",
                                       size_hint_y=None, height=dp(52),
                                       padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.email_field)

        self.password_field = MDTextField(hint_text="Пароль", mode="filled", password=True,
                                          size_hint_y=None, height=dp(52),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.password_field)

        self.confirm_field = MDTextField(hint_text="Подтвердите пароль", mode="filled", password=True,
                                         size_hint_y=None, height=dp(52),
                                         padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.confirm_field)

        buttons_box = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(44))

        cancel_btn = MDRaisedButton(text="Отмена", size_hint=(0.5, 1),
                                    on_release=self.close)

        register_btn = MDRaisedButton(text="Зарегистрироваться", size_hint=(0.5, 1),
                                      on_release=self.do_register)

        buttons_box.add_widget(cancel_btn)
        buttons_box.add_widget(register_btn)
        self.add_widget(buttons_box)

    def close(self, instance=None):
        if self.on_close_callback:
            self.on_close_callback()
        if self.parent:
            self.parent.remove_widget(self)

    def do_register(self, instance):
        username = self.username_field.text
        email = self.email_field.text
        password = self.password_field.text
        confirm = self.confirm_field.text
        if not username or not email or not password:
            notify.warning("Заполните все поля")
            return
        if len(password) > 72:
            notify.warning("Пароль слишком длинный (максимум 72 символа)")
            return
        if password != confirm:
            notify.warning("Пароли не совпадают")
            return
        api.register(username=username, email=email, password=password, full_name=None,
                     on_success=self.on_register_success, on_failure=self.on_register_failure)

    def on_register_success(self, result):
        notify.success("Регистрация успешна! Теперь войдите.")
        self.close()
        if self.on_register_success_callback:
            self.on_register_success_callback()

    def on_register_failure(self, req, error):
        notify.error("Ошибка. Возможно, имя или email уже заняты.")


class AuthModal(MDCard):
    def __init__(self, parent_screen, on_close=None, on_login_success=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        self.on_close_callback = on_close
        self.on_login_success_callback = on_login_success

        self.orientation = 'vertical'
        self.size_hint = (0.85, None)
        self.height = dp(340)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 4
        self.radius = [theme.CORNER_RADIUS] * 4
        self.md_bg_color = theme.SURFACE
        self.padding = [dp(16), dp(16), dp(16), dp(16)]
        self.spacing = dp(10)

        title = MDLabel(text="Войдите в свой аккаунт", halign="center",
                        size_hint_y=None, height=dp(32), theme_text_color="Primary",
                        bold=True, font_size=dp(20))
        self.add_widget(title)

        subtitle = MDLabel(text="чтобы получить доступ ко всем функциям приложения",
                           halign="center", size_hint_y=None,
                           height=dp(28), theme_text_color="Secondary", font_size=dp(12))
        self.add_widget(subtitle)

        self.add_widget(MDBoxLayout(size_hint_y=None, height=dp(4)))

        google_btn = MDRaisedButton(
            text="Войти через Google",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self.on_google_click
        )
        google_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(google_btn)

        login_btn = MDRaisedButton(
            text="Войти по логину и паролю",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self.show_login_form
        )
        login_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(login_btn)

        register_btn = MDRaisedButton(
            text="Зарегистрироваться",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self.show_register
        )
        register_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(register_btn)

        skip_btn = MDRaisedButton(
            text="Пропустить",
            size_hint=(0.9, None),
            height=dp(40),
            on_release=self.close
        )
        skip_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(skip_btn)

        self.login_modal = None
        self.register_modal = None

    def on_google_click(self, instance):
        self.close()
        if self.on_login_success_callback:
            self.on_login_success_callback('google')

    def close(self, instance=None):
        if self.on_close_callback:
            self.on_close_callback()
        if self.parent:
            self.parent.remove_widget(self)

    def show_login_form(self, instance):
        self.close()
        Clock.schedule_once(lambda dt: self._show_login_modal(), 0.2)

    def _show_login_modal(self):
        if self.login_modal and self.login_modal.parent:
            return
        self.login_modal = LoginModal(
            parent_screen=self.parent_screen,
            on_close=self.on_login_close,
            on_login_success=self.on_login_form_success
        )
        self.parent_screen.add_widget(self.login_modal)

    def on_login_close(self):
        self.login_modal = None

    def on_login_form_success(self):
        self.login_modal = None
        Clock.schedule_once(
            lambda dt: self.on_login_success_callback('login_form') if self.on_login_success_callback else None, 0.1)

    def show_register(self, instance):
        self.close()
        Clock.schedule_once(lambda dt: self._show_register_modal(), 0.2)

    def _show_register_modal(self):
        if self.register_modal and self.register_modal.parent:
            return
        self.register_modal = RegisterModal(
            parent_screen=self.parent_screen,
            on_close=self.on_register_close,
            on_register_success=self.on_register_form_success
        )
        self.parent_screen.add_widget(self.register_modal)

    def on_register_close(self):
        self.register_modal = None

    def on_register_form_success(self):
        self.register_modal = None
        notify.success("Регистрация успешна! Теперь войдите.")


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        self.user = None
        self.auth_check_done = False
        self.welcome_popup = None

        # Делаем экран прозрачным
        self.md_bg_color = [0, 0, 0, 0]

        # Используем FloatLayout для возможности наложения виджетов
        self.root_layout = FloatLayout()

        # Основной контейнер
        self.layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(16), dp(16), dp(16)],
            spacing=dp(10)
        )

        # Верхний спейсер для центрирования
        self.top_spacer = BoxLayout(size_hint_y=0.2)

        # Заголовок
        self.title = MDLabel(
            text="GuitarFuns",
            font_size=dp(36),
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            size_hint_y=None,
            height=dp(50)
        )

        # Карусель
        self.carousel = MainCarousel(
            screen_manager=self.manager,
            on_item_selected=self._on_carousel_item_selected
        )

        # Нижний спейсер для центрирования
        self.bottom_spacer = BoxLayout(size_hint_y=0.2)

        self.layout.add_widget(self.top_spacer)
        self.layout.add_widget(self.title)
        self.layout.add_widget(self.carousel)
        self.layout.add_widget(self.bottom_spacer)

        self.root_layout.add_widget(self.layout)
        self.add_widget(self.root_layout)

        Clock.schedule_once(self.check_auth, 0.5)
        logger.info('Главный экран создан')

    def show_welcome(self, username):
        """Показывает красивое всплывающее приветствие"""
        from screens.home_screen import WelcomePopup
        if self.welcome_popup and self.welcome_popup.parent:
            return
        self.welcome_popup = WelcomePopup(username)
        self.root_layout.add_widget(self.welcome_popup)

    def check_auth(self, dt):
        """Проверяет авторизацию при запуске"""
        if self.auth_check_done:
            return
        self.auth_check_done = True

        if api.access_token:
            api.get_current_user(on_success=self.on_auth_success, on_failure=self.on_auth_failure)
        else:
            logger.info("Нет токена, показываем AuthModal")
            app = MDApp.get_running_app()
            if hasattr(app, 'open_profile'):
                Clock.schedule_once(lambda x: app.open_profile(), 0.1)

    def on_auth_success(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        logger.info(f'Пользователь авторизован: {username}')
        self.show_welcome(username)

    def on_auth_failure(self, req, error):
        error_msg = str(error)
        logger.warning(f'Авторизация не пройдена: {error_msg}')
        app = MDApp.get_running_app()
        if hasattr(app, 'open_profile'):
            Clock.schedule_once(lambda x: app.open_profile(), 0.1)

    def open_profile(self):
        """Открывает экран профиля"""
        if api.is_authenticated():
            if hasattr(self, 'manager') and self.manager:
                if 'profile' in self.manager.screen_names:
                    logger.info("Переход на профиль")
                    self.manager.current = 'profile'
        else:
            logger.info("Не авторизован, показываем AuthModal")
            app = MDApp.get_running_app()
            if hasattr(app, 'open_profile'):
                app.open_profile()

    def on_login_success(self):
        """Обработчик успешного входа (вызывается из main.py)"""
        if api.access_token:
            api.get_current_user(
                on_success=self.on_user_data_loaded,
                on_failure=lambda req, err: None
            )

    def on_user_data_loaded(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        self.show_welcome(username)

    def _on_carousel_item_selected(self, screen_name):
        """Обработчик выбора элемента из карусели"""
        if screen_name == 'profile':
            self.open_profile()
        elif hasattr(self, 'manager') and self.manager:
            self.manager.transition.direction = 'left'
            self.manager.current = screen_name

    def on_pre_enter(self):
        if hasattr(self, 'carousel'):
            self.carousel.start_auto_scroll()
        return super().on_pre_enter()

    def on_leave(self):
        if hasattr(self, 'carousel'):
            self.carousel.stop_auto_scroll()
        return super().on_leave()


class WelcomePopup(MDCard):
    """Красивое всплывающее приветствие"""

    def __init__(self, username, **kwargs):
        super().__init__(**kwargs)
        self.username = username

        self.orientation = 'vertical'
        self.size_hint = (0.85, None)
        self.height = dp(180)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 6
        self.radius = [theme.CORNER_RADIUS] * 4
        self.md_bg_color = [1, 1, 1, 0.95]
        self.padding = [dp(20), dp(20), dp(20), dp(20)]
        self.spacing = dp(10)

        # Иконка гитары
        guitar_icon = MDLabel(
            text="🎸",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1]
        )

        # Текст "Добро пожаловать"
        welcome_label = MDLabel(
            text="Добро пожаловать!",
            font_size=sp(18),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[0.2, 0.2, 0.2, 0.9],
            bold=True
        )

        # Имя пользователя
        name_label = MDLabel(
            text=username,
            font_size=sp(16),
            halign="center",
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            bold=True
        )

        self.add_widget(guitar_icon)
        self.add_widget(welcome_label)
        self.add_widget(name_label)

        # Анимация появления
        self.opacity = 0
        self.scale = 0.8
        anim = Animation(opacity=1, scale=1, duration=0.3, t='out_back')
        anim.start(self)

        # Автоматическое исчезновение через 3 секунды
        Clock.schedule_once(self.fade_out, 3)

    def fade_out(self, dt):
        """Плавное исчезновение"""
        anim = Animation(opacity=0, scale=0.8, duration=0.3, t='in_back')
        anim.bind(on_complete=lambda *args: self.parent.remove_widget(self) if self.parent else None)
        anim.start(self)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]