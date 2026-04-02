# screens/home_screen.py
"""
Главный экран с компактным модальным окном авторизации
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import (
    MDButton, MDButtonText, MDIconButton, MDButtonIcon
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

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

        # Кнопка "Назад"
        back_btn = MDIconButton()
        back_btn.icon = "arrow-left"
        back_btn.icon_color = theme.TEXT_SECONDARY
        back_btn.theme_icon_color = "Custom"
        back_btn.pos_hint = {'x': 0, 'top': 1}
        back_btn.size_hint = (None, None)
        back_btn.size = (dp(32), dp(32))
        back_btn.bind(on_release=self.close)
        self.add_widget(back_btn)

        title = MDLabel(text="Вход в аккаунт", font_size=sp(18), halign="center",
                        size_hint_y=None, height=dp(36), theme_text_color="Primary", bold=True)
        self.add_widget(title)

        self.username_field = MDTextField(hint_text="Имя пользователя или Email", mode="filled",
                                          size_hint_y=None, height=dp(56),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.username_field)

        self.password_field = MDTextField(hint_text="Пароль", mode="filled", password=True,
                                          size_hint_y=None, height=dp(56),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.password_field)

        # Контейнер для кнопок
        buttons_box = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(44))

        # Кнопка "Отмена"
        cancel_btn = MDButton(style="filled")
        cancel_btn.size_hint = (0.5, 1)
        cancel_btn.md_bg_color = [0.95, 0.95, 0.95, 1]
        cancel_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        cancel_btn.bind(on_release=self.close)
        cancel_btn_text = MDButtonText(text="Отмена", theme_text_color="Custom", text_color=theme.TEXT_SECONDARY)
        cancel_btn.add_widget(cancel_btn_text)

        # Кнопка "Войти"
        login_btn = MDButton(style="filled")
        login_btn.size_hint = (0.5, 1)
        login_btn.md_bg_color = theme.PRIMARY
        login_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        login_btn.bind(on_release=self.do_login)
        login_btn_text = MDButtonText(text="Войти", theme_text_color="Custom", text_color=[1, 1, 1, 1])
        login_btn.add_widget(login_btn_text)

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
        back_btn.icon_color = theme.TEXT_SECONDARY
        back_btn.theme_icon_color = "Custom"
        back_btn.pos_hint = {'x': 0, 'top': 1}
        back_btn.size_hint = (None, None)
        back_btn.size = (dp(32), dp(32))
        back_btn.bind(on_release=self.close)
        self.add_widget(back_btn)

        title = MDLabel(text="Регистрация", font_size=sp(18), halign="center",
                        size_hint_y=None, height=dp(32), theme_text_color="Primary", bold=True)
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

        cancel_btn = MDButton(style="filled")
        cancel_btn.size_hint = (0.5, 1)
        cancel_btn.md_bg_color = [0.95, 0.95, 0.95, 1]
        cancel_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        cancel_btn.bind(on_release=self.close)
        cancel_btn_text = MDButtonText(text="Отмена", theme_text_color="Custom", text_color=theme.TEXT_SECONDARY)
        cancel_btn.add_widget(cancel_btn_text)

        register_btn = MDButton(style="filled")
        register_btn.size_hint = (0.5, 1)
        register_btn.md_bg_color = theme.PRIMARY
        register_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        register_btn.bind(on_release=self.do_register)
        register_btn_text = MDButtonText(text="Зарегистрироваться", theme_text_color="Custom", text_color=[1, 1, 1, 1])
        register_btn.add_widget(register_btn_text)

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
        self.height = dp(420)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 4
        self.radius = [theme.CORNER_RADIUS] * 4
        self.md_bg_color = theme.SURFACE
        self.padding = [dp(16), dp(16), dp(16), dp(16)]
        self.spacing = dp(10)

        title = MDLabel(text="Войдите в свой аккаунт", font_size=sp(18), halign="center",
                        size_hint_y=None, height=dp(32), theme_text_color="Primary", bold=True)
        self.add_widget(title)

        subtitle = MDLabel(text="чтобы получить доступ ко всем функциям приложения",
                           font_size=sp(12), halign="center", size_hint_y=None,
                           height=dp(28), theme_text_color="Secondary")
        self.add_widget(subtitle)

        self.add_widget(MDBoxLayout(size_hint_y=None, height=dp(8)))

        # Кнопка "Войти через Google"
        google_btn = MDButton(style="filled")
        google_btn.size_hint = (0.9, None)
        google_btn.height = dp(48)
        google_btn.pos_hint = {'center_x': 0.5}
        google_btn.md_bg_color = [0.96, 0.96, 0.96, 1]
        google_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        google_btn.bind(on_release=self.on_google_click)
        google_btn_icon = MDButtonIcon(icon="google", theme_icon_color="Custom", icon_color=[0.2, 0.2, 0.2, 1])
        google_btn_text = MDButtonText(text="Войти через Google", theme_text_color="Custom",
                                       text_color=[0.2, 0.2, 0.2, 1], font_size=dp(13))
        google_btn.add_widget(google_btn_icon)
        google_btn.add_widget(google_btn_text)
        self.add_widget(google_btn)

        # Кнопка "Войти по логину и паролю"
        login_btn = MDButton(style="filled")
        login_btn.size_hint = (0.9, None)
        login_btn.height = dp(48)
        login_btn.pos_hint = {'center_x': 0.5}
        login_btn.md_bg_color = theme.PRIMARY_LIGHT
        login_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        login_btn.bind(on_release=self.show_login_form)
        login_btn_icon = MDButtonIcon(icon="account", theme_icon_color="Custom", icon_color=[1, 1, 1, 1])
        login_btn_text = MDButtonText(text="Войти по логину и паролю", theme_text_color="Custom",
                                      text_color=[1, 1, 1, 1], font_size=dp(13))
        login_btn.add_widget(login_btn_icon)
        login_btn.add_widget(login_btn_text)
        self.add_widget(login_btn)

        # Кнопка "Зарегистрироваться"
        register_btn = MDButton(style="filled")
        register_btn.size_hint = (0.9, None)
        register_btn.height = dp(48)
        register_btn.pos_hint = {'center_x': 0.5}
        register_btn.md_bg_color = theme.PRIMARY
        register_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        register_btn.bind(on_release=self.show_register)
        register_btn_icon = MDButtonIcon(icon="account-plus", theme_icon_color="Custom", icon_color=[1, 1, 1, 1])
        register_btn_text = MDButtonText(text="Зарегистрироваться", theme_text_color="Custom", text_color=[1, 1, 1, 1],
                                         font_size=dp(13))
        register_btn.add_widget(register_btn_icon)
        register_btn.add_widget(register_btn_text)
        self.add_widget(register_btn)

        # Кнопка "Пропустить"
        skip_btn = MDButton(style="filled")
        skip_btn.size_hint = (0.9, None)
        skip_btn.height = dp(44)
        skip_btn.pos_hint = {'center_x': 0.5}
        skip_btn.md_bg_color = [0.95, 0.95, 0.95, 1]
        skip_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        skip_btn.bind(on_release=self.close)
        skip_btn_text = MDButtonText(text="Пропустить", theme_text_color="Custom", text_color=theme.TEXT_SECONDARY,
                                     font_size=dp(13))
        skip_btn.add_widget(skip_btn_text)
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

        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        from kivymd.uix.scrollview import MDScrollView

        scroll = MDScrollView(size_hint=(1, 1), bar_width=dp(4), bar_color=theme.PRIMARY_LIGHT)

        layout = MDBoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20),
                             size_hint_y=None, adaptive_height=True)

        title = MDLabel(text="GuitarFuns", font_size=sp(32), halign="center",
                        size_hint_y=None, height=dp(80), theme_text_color="Primary", bold=True)
        self.auth_status = MDLabel(text="", halign="center", size_hint_y=None, height=dp(30),
                                   theme_text_color="Secondary", font_size=sp(12))
        quick_title = MDLabel(text="Быстрый доступ", font_size=sp(18), halign="center",
                              size_hint_y=None, height=dp(36), theme_text_color="Primary", bold=True)

        buttons_layout = MDBoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(180))

        # Функция для создания кнопки на главном экране
        def create_main_button(text, icon_name, callback):
            btn = MDButton(style="filled")
            # Важно: устанавливаем theme_width="Custom" и задаем конкретную ширину
            btn.theme_width = "Custom"
            btn.width = dp(200)  # Фиксированная ширина
            btn.size_hint_x = None  # Отключаем автоматическое масштабирование по горизонтали
            btn.size_hint = (None, None)  # Полностью отключаем size_hint
            btn.width = dp(200)
            btn.height = dp(56)
            btn.pos_hint = {"center_x": 0.5}
            btn.md_bg_color = theme.PRIMARY
            btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
            btn.bind(on_release=callback)

            # Иконка
            btn_icon = MDButtonIcon(
                icon=icon_name,
                theme_icon_color="Custom",
                icon_color=[1, 1, 1, 1]
            )

            # Текст
            btn_text = MDButtonText(
                text=text,
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1],
                font_size=dp(14)
            )

            btn.add_widget(btn_icon)
            btn.add_widget(btn_text)

            # Принудительно обновляем позиции дочерних элементов
            Clock.schedule_once(lambda dt: btn.adjust_pos(), 0.1)
            Clock.schedule_once(lambda dt: btn.adjust_width(), 0.1)

            return btn

        tuner_btn = create_main_button("Тюнер", "tune", lambda x: self.navigate_to('tuner'))
        songs_btn = create_main_button("Песни", "music-note", lambda x: self.navigate_to('songs'))
        chords_btn = create_main_button("Аккорды", "guitar-acoustic", lambda x: self.navigate_to('chords'))

        buttons_layout.add_widget(tuner_btn)
        buttons_layout.add_widget(songs_btn)
        buttons_layout.add_widget(chords_btn)

        layout.add_widget(title)
        layout.add_widget(self.auth_status)
        layout.add_widget(quick_title)
        layout.add_widget(buttons_layout)

        spacer = MDBoxLayout(size_hint_y=None, height=dp(20))
        layout.add_widget(spacer)

        scroll.add_widget(layout)
        self.add_widget(scroll)

        Clock.schedule_once(self.check_auth, 1)
        logger.info('Главный экран создан')

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def navigate_to(self, screen_name):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = screen_name

    def check_auth(self, dt):
        if self.auth_check_done:
            return
        self.auth_check_done = True

        if api.access_token:
            self.auth_status.text = "🔐 Проверка..."
            api.get_current_user(on_success=self.on_auth_success, on_failure=self.on_auth_failure)
        else:
            self.auth_status.text = "👤 Гость"
            self.show_auth_modal()

    def on_auth_success(self, user):
        self.user = user
        self.auth_status.text = f"✅ {user.get('username')}"
        logger.info(f'Пользователь авторизован: {user.get("username")}')

    def on_auth_failure(self, req, error):
        error_msg = str(error)
        logger.warning(f'Авторизация не пройдена: {error_msg}')

        if 'Not authenticated' in error_msg or 'Invalid token' in error_msg:
            api._clear_tokens()
            self.auth_status.text = "👤 Гость"
            self.show_auth_modal()
        else:
            self.auth_status.text = "👤 Гость"
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
        self.auth_status.text = "🌐 Открываем Google..."

        api.google_login(
            on_success=self.on_oauth_success,
            on_failure=self.on_oauth_failure
        )

    def on_oauth_success(self, user):
        self.user = user
        self.auth_status.text = f"✅ {user.get('username')}"
        notify.success(f"Добро пожаловать, {user.get('username')}! 🎸")
        logger.info(f'Пользователь авторизован: {user.get("username")}')
        api.user_data = user

    def on_oauth_failure(self, req, error):
        self.auth_status.text = "👤 Гость"
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
        return super().on_pre_enter()