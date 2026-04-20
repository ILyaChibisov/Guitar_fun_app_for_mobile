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
        back_btn.theme_text_color = "Custom"
        back_btn.text_color = theme.TEXT_SECONDARY
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
        cancel_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        login_btn = MDRaisedButton(text="Войти", size_hint=(0.5, 1),
                                   on_release=self.do_login)
        login_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

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
        back_btn.theme_text_color = "Custom"
        back_btn.text_color = theme.TEXT_SECONDARY
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
        cancel_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        register_btn = MDRaisedButton(text="Зарегистрироваться", size_hint=(0.5, 1),
                                      on_release=self.do_register)
        register_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

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
        google_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.add_widget(google_btn)

        login_btn = MDRaisedButton(
            text="Войти по логину и паролю",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self.show_login_form
        )
        login_btn.pos_hint = {'center_x': 0.5}
        login_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.add_widget(login_btn)

        register_btn = MDRaisedButton(
            text="Зарегистрироваться",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self.show_register
        )
        register_btn.pos_hint = {'center_x': 0.5}
        register_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.add_widget(register_btn)

        skip_btn = MDRaisedButton(
            text="Пропустить",
            size_hint=(0.9, None),
            height=dp(40),
            on_release=self.close
        )
        skip_btn.pos_hint = {'center_x': 0.5}
        skip_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
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
        if self.on_login_success_callback:
            self.on_login_success_callback('login_form')

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
        self.auth_modal = None
        self.auth_check_done = False

        # Делаем экран прозрачным
        self.md_bg_color = [0, 0, 0, 0]

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

        # Добавляем всё в layout
        self.layout.add_widget(self.top_spacer)
        self.layout.add_widget(self.title)
        self.layout.add_widget(self.carousel)
        self.layout.add_widget(self.bottom_spacer)

        self.add_widget(self.layout)

        Clock.schedule_once(self.check_auth, 1)
        logger.info('Главный экран создан')

    def _on_carousel_item_selected(self, screen_name):
        """Обработчик выбора элемента из карусели"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.transition.direction = 'left'
            self.manager.current = screen_name

    def check_auth(self, dt):
        if self.auth_check_done:
            return
        self.auth_check_done = True

        if api.access_token:
            api.get_current_user(on_success=self.on_auth_success, on_failure=self.on_auth_failure)
        else:
            self.show_auth_modal()

    def on_auth_success(self, user):
        self.user = user
        logger.info(f'Пользователь авторизован: {user.get("username")}')

    def on_auth_failure(self, req, error):
        error_msg = str(error)
        logger.warning(f'Авторизация не пройдена: {error_msg}')

        if 'Not authenticated' in error_msg or 'Invalid token' in error_msg:
            api._clear_tokens()
            self.show_auth_modal()
        else:
            self.show_auth_modal()

    def show_auth_modal(self):
        if self.auth_modal and self.auth_modal.parent:
            return
        self.auth_modal = AuthModal(
            parent_screen=self,
            on_close=self.on_modal_close,
            on_login_success=self.on_login_success
        )
        self.add_widget(self.auth_modal)

    def on_modal_close(self):
        self.auth_modal = None

    def on_login_success(self, provider=None):
        self.auth_modal = None
        if provider == 'google':
            self.login_google()
        elif provider == 'login_form':
            self.check_auth(0)
        else:
            self.check_auth(0)

    def login_google(self):
        api.google_login(
            on_success=self.on_oauth_success,
            on_failure=self.on_oauth_failure
        )

    def on_oauth_success(self, user):
        self.user = user
        notify.success(f"Добро пожаловать, {user.get('username')}! 🎸")
        logger.info(f'Пользователь авторизован: {user.get("username")}')
        api.user_data = user

    def on_oauth_failure(self, req, error):
        notify.error("Ошибка авторизации через Google")
        logger.error(f'OAuth ошибка: {error}')

    def open_profile(self):
        if api.is_authenticated():
            if hasattr(self, 'manager') and self.manager:
                if 'profile' in self.manager.screen_names:
                    self.manager.current = 'profile'
                else:
                    notify.info(f"Вы вошли как {api.user_data.get('username')} 🎸")
            else:
                notify.info(f"Вы вошли как {api.user_data.get('username')} 🎸")
        else:
            logger.info('Не авторизован, показываем окно авторизации')
            self.show_auth_modal()

    def on_pre_enter(self):
        if hasattr(self, 'carousel'):
            self.carousel.start_auto_scroll()
        return super().on_pre_enter()

    def on_leave(self):
        if hasattr(self, 'carousel'):
            self.carousel.stop_auto_scroll()
        return super().on_leave()