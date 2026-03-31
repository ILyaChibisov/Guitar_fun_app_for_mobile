# screens/home_screen.py
"""
Главный экран с компактным модальным окном авторизации
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.snackbar import MDSnackbar
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api

logger = screen_logger('Home')


def show_snackbar(message):
    """Показывает уведомление"""
    snack = MDSnackbar()
    snack.text = message
    snack.snackbar_x = "10dp"
    snack.snackbar_y = "10dp"
    snack.radius = [theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                    theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL]
    snack.open()


class AuthButton(MDRaisedButton):
    def __init__(self, icon, text, bg_color, text_color=[1, 1, 1, 1], **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.text = text
        self.md_bg_color = bg_color
        self.theme_text_color = "Custom"
        self.text_color = text_color
        self.size_hint = (0.9, None)
        self.height = dp(44)
        self.font_size = dp(13)
        self.ripple_behavior = True
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4

    def on_press(self):
        anim = Animation(opacity=0.8, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)


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

        back_btn = MDIconButton(icon="arrow-left", pos_hint={'x': 0, 'top': 1},
                                size_hint=(None, None), size=(dp(32), dp(32)),
                                theme_text_color="Custom", text_color=theme.TEXT_SECONDARY,
                                on_release=self.close)
        self.add_widget(back_btn)

        title = MDLabel(text="Вход в аккаунт", font_style="H6", halign="center",
                        size_hint_y=None, height=dp(36), theme_text_color="Primary", bold=True)
        self.add_widget(title)

        self.username_field = MDTextField(hint_text="Имя пользователя или Email", mode="round",
                                          size_hint_y=None, height=dp(56),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.username_field)

        self.password_field = MDTextField(hint_text="Пароль", mode="round", password=True,
                                          size_hint_y=None, height=dp(56),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.password_field)

        buttons_box = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(44))

        cancel_btn = MDRaisedButton(text="Отмена", size_hint=(0.5, 1),
                                    md_bg_color=[0.95, 0.95, 0.95, 1],
                                    theme_text_color="Custom", text_color=theme.TEXT_SECONDARY,
                                    on_release=self.close)
        cancel_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        login_btn = MDRaisedButton(text="Войти", size_hint=(0.5, 1),
                                   md_bg_color=theme.PRIMARY,
                                   theme_text_color="Custom", text_color=[1, 1, 1, 1],
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
            show_snackbar("Заполните все поля")
            return
        api.login(username=username, password=password,
                  on_success=self.on_login_success, on_failure=self.on_login_failure)

    def on_login_success(self, result):
        show_snackbar("✅ Вход выполнен успешно!")
        self.close()
        if self.on_login_success_callback:
            self.on_login_success_callback()

    def on_login_failure(self, req, error):
        show_snackbar("❌ Неверное имя пользователя или пароль")


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

        back_btn = MDIconButton(icon="arrow-left", pos_hint={'x': 0, 'top': 1},
                                size_hint=(None, None), size=(dp(32), dp(32)),
                                theme_text_color="Custom", text_color=theme.TEXT_SECONDARY,
                                on_release=self.close)
        self.add_widget(back_btn)

        title = MDLabel(text="Регистрация", font_style="H6", halign="center",
                        size_hint_y=None, height=dp(32), theme_text_color="Primary", bold=True)
        self.add_widget(title)

        self.username_field = MDTextField(hint_text="Имя пользователя", mode="round",
                                          size_hint_y=None, height=dp(52),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.username_field)

        self.email_field = MDTextField(hint_text="Email", mode="round",
                                       size_hint_y=None, height=dp(52),
                                       padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.email_field)

        self.password_field = MDTextField(hint_text="Пароль", mode="round", password=True,
                                          size_hint_y=None, height=dp(52),
                                          padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.password_field)

        self.confirm_field = MDTextField(hint_text="Подтвердите пароль", mode="round", password=True,
                                         size_hint_y=None, height=dp(52),
                                         padding=[dp(12), dp(6), dp(12), dp(6)], font_size=dp(13))
        self.add_widget(self.confirm_field)

        buttons_box = MDBoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(44))

        cancel_btn = MDRaisedButton(text="Отмена", size_hint=(0.5, 1),
                                    md_bg_color=[0.95, 0.95, 0.95, 1],
                                    theme_text_color="Custom", text_color=theme.TEXT_SECONDARY,
                                    on_release=self.close)
        cancel_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        register_btn = MDRaisedButton(text="Зарегистрироваться", size_hint=(0.5, 1),
                                      md_bg_color=theme.PRIMARY,
                                      theme_text_color="Custom", text_color=[1, 1, 1, 1],
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
            show_snackbar("Заполните все поля")
            return
        if len(password) > 72:
            show_snackbar("Пароль слишком длинный (максимум 72 символа)")
            return
        if password != confirm:
            show_snackbar("Пароли не совпадают")
            return
        api.register(username=username, email=email, password=password, full_name=None,
                     on_success=self.on_register_success, on_failure=self.on_register_failure)

    def on_register_success(self, result):
        show_snackbar("✅ Регистрация успешна! Теперь войдите.")
        self.close()
        if self.on_register_success_callback:
            self.on_register_success_callback()

    def on_register_failure(self, req, error):
        show_snackbar("❌ Ошибка. Возможно, имя или email уже заняты.")


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

        title = MDLabel(text="Войдите в свой аккаунт", font_style="H6", halign="center",
                        size_hint_y=None, height=dp(32), theme_text_color="Primary", bold=True)
        self.add_widget(title)

        subtitle = MDLabel(text="чтобы получить доступ ко всем функциям приложения",
                           font_style="Caption", halign="center", size_hint_y=None,
                           height=dp(28), theme_text_color="Secondary")
        self.add_widget(subtitle)

        self.add_widget(MDBoxLayout(size_hint_y=None, height=dp(4)))

        google_btn = AuthButton(icon="google", text="Войти через Google",
                                bg_color=[0.96, 0.96, 0.96, 1], text_color=[0.2, 0.2, 0.2, 1])
        google_btn.pos_hint = {'center_x': 0.5}
        google_btn.bind(on_release=self.on_google_click)
        self.add_widget(google_btn)

        login_btn = AuthButton(icon="account", text="Войти по логину и паролю",
                               bg_color=theme.PRIMARY_LIGHT, text_color=[1, 1, 1, 1])
        login_btn.pos_hint = {'center_x': 0.5}
        login_btn.bind(on_release=self.show_login_form)
        self.add_widget(login_btn)

        register_btn = AuthButton(icon="account-plus", text="Зарегистрироваться",
                                  bg_color=theme.PRIMARY, text_color=[1, 1, 1, 1])
        register_btn.pos_hint = {'center_x': 0.5}
        register_btn.bind(on_release=self.show_register)
        self.add_widget(register_btn)

        skip_btn = MDRaisedButton(text="Пропустить", size_hint=(0.9, None), height=dp(40),
                                  md_bg_color=[0.95, 0.95, 0.95, 1],
                                  theme_text_color="Custom", text_color=theme.TEXT_SECONDARY,
                                  on_release=self.close)
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
        show_snackbar("✅ Регистрация успешна! Теперь войдите.")


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = None
        self.auth_modal = None
        self.auth_check_done = False  # Флаг для предотвращения повторной проверки

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

        title = MDLabel(text="GuitarFuns", font_style="H3", halign="center",
                        size_hint_y=None, height=dp(80), theme_text_color="Primary", bold=True)
        self.auth_status = MDLabel(text="", halign="center", size_hint_y=None, height=dp(30),
                                   theme_text_color="Secondary", font_style="Caption")
        quick_title = MDLabel(text="Быстрый доступ", font_style="H6", halign="center",
                              size_hint_y=None, height=dp(36), theme_text_color="Primary", bold=True)

        buttons_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(156))

        tuner_btn = MDRaisedButton(text="Тюнер", icon="tune", size_hint=(0.8, None), height=dp(44),
                                   pos_hint={"center_x": 0.5}, md_bg_color=theme.PRIMARY,
                                   theme_text_color="Custom", text_color=[1, 1, 1, 1],
                                   on_release=lambda x: self.navigate_to('tuner'))
        tuner_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        songs_btn = MDRaisedButton(text="Песни", icon="music-note", size_hint=(0.8, None), height=dp(44),
                                   pos_hint={"center_x": 0.5}, md_bg_color=theme.PRIMARY,
                                   on_release=lambda x: self.navigate_to('songs'))
        songs_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        chords_btn = MDRaisedButton(text="Аккорды", icon="guitar-acoustic", size_hint=(0.8, None), height=dp(44),
                                    pos_hint={"center_x": 0.5}, md_bg_color=theme.PRIMARY,
                                    on_release=lambda x: self.navigate_to('chords'))
        chords_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

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
        # Защита от повторного вызова
        if self.auth_check_done:
            return
        self.auth_check_done = True

        print(f"🔴 check_auth ВЫЗВАН, api.access_token = {api.access_token}")
        if api.access_token:
            self.auth_status.text = "🔐 Проверка..."
            api.get_current_user(on_success=self.on_auth_success, on_failure=self.on_auth_failure)
        else:
            self.auth_status.text = "👤 Гость"
            self.show_auth_modal()

    def on_auth_success(self, user):
        print("🔴 on_auth_success ВЫЗВАН")
        self.user = user
        self.auth_status.text = f"✅ {user.get('username')}"
        logger.info(f'Пользователь авторизован: {user.get("username")}')
        # НЕ ПЕРЕХОДИМ В ПРОФИЛЬ АВТОМАТИЧЕСКИ

    def on_auth_failure(self, req, error):
        """Ошибка авторизации"""
        error_msg = str(error)
        logger.warning(f'Авторизация не пройдена: {error_msg}')

        if 'Not authenticated' in error_msg or 'Invalid token' in error_msg:
            # Токен недействителен, очищаем его
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
        show_snackbar(f"Добро пожаловать, {user.get('username')}! 🎸")
        logger.info(f'Пользователь авторизован: {user.get("username")}')
        api.user_data = user

    def on_oauth_failure(self, req, error):
        self.auth_status.text = "👤 Гость"
        show_snackbar("❌ Ошибка авторизации через Google")
        logger.error(f'OAuth ошибка: {error}')

    def open_profile(self):
        """Открывает профиль - вызывается из верхней панели"""
        if api.is_authenticated():
            if hasattr(self, 'manager') and self.manager:
                if 'profile' in self.manager.screen_names:
                    self.manager.current = 'profile'
                else:
                    show_snackbar(f"Вы вошли как {api.user_data.get('username')} 🎸")
            else:
                show_snackbar(f"Вы вошли как {api.user_data.get('username')} 🎸")
        else:
            logger.info('Не авторизован, показываем окно авторизации')
            self.show_auth_modal()

    def on_pre_enter(self):
        """Вызывается перед входом на экран"""
        print("🔴 HOME SCREEN: on_pre_enter ВЫЗВАН")
        return super().on_pre_enter()