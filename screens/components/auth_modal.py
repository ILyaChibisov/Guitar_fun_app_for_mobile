# screens/components/auth_modal.py
"""
Модальное окно авторизации
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField

from config.theme import theme
from api.client import api
from utils.notifications import notify


class LoginModal(MDCard):
    """Модальное окно входа по логину/паролю"""

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

        back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.close
        )
        self.add_widget(back_btn)

        title = MDLabel(
            text="Вход в аккаунт",
            halign="center",
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Primary",
            bold=True,
            font_size=dp(20)
        )
        self.add_widget(title)

        self.username_field = MDTextField(
            hint_text="Имя пользователя или Email",
            mode="fill",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.username_field)

        self.password_field = MDTextField(
            hint_text="Пароль",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(56),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.password_field)

        buttons_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(44)
        )

        cancel_btn = MDRaisedButton(
            text="Отмена",
            size_hint=(0.5, 1),
            on_release=self.close
        )

        login_btn = MDRaisedButton(
            text="Войти",
            size_hint=(0.5, 1),
            on_release=self._do_login
        )

        buttons_box.add_widget(cancel_btn)
        buttons_box.add_widget(login_btn)
        self.add_widget(buttons_box)

    def close(self, instance=None):
        if self.on_close_callback:
            self.on_close_callback()
        if self.parent:
            self.parent.remove_widget(self)

    def _do_login(self, instance):
        username = self.username_field.text.strip()
        password = self.password_field.text.strip()

        if not username or not password:
            notify.warning("Заполните все поля")
            return

        api.login(
            username=username,
            password=password,
            on_success=self._on_login_success,
            on_failure=self._on_login_failure
        )

    def _on_login_success(self, result):
        notify.success("Вход выполнен успешно!")
        self.close()
        if self.on_login_success_callback:
            self.on_login_success_callback()

    def _on_login_failure(self, req, error):
        notify.error("Неверное имя пользователя или пароль")


class RegisterModal(MDCard):
    """Модальное окно регистрации"""

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

        back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.close
        )
        self.add_widget(back_btn)

        title = MDLabel(
            text="Регистрация",
            halign="center",
            size_hint_y=None,
            height=dp(32),
            theme_text_color="Primary",
            bold=True,
            font_size=dp(20)
        )
        self.add_widget(title)

        self.username_field = MDTextField(
            hint_text="Имя пользователя",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.username_field)

        self.email_field = MDTextField(
            hint_text="Email",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.email_field)

        self.password_field = MDTextField(
            hint_text="Пароль",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(52),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.password_field)

        self.confirm_field = MDTextField(
            hint_text="Подтвердите пароль",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(52),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.confirm_field)

        buttons_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(44)
        )

        cancel_btn = MDRaisedButton(
            text="Отмена",
            size_hint=(0.5, 1),
            on_release=self.close
        )

        register_btn = MDRaisedButton(
            text="Зарегистрироваться",
            size_hint=(0.5, 1),
            on_release=self._do_register
        )

        buttons_box.add_widget(cancel_btn)
        buttons_box.add_widget(register_btn)
        self.add_widget(buttons_box)

    def close(self, instance=None):
        if self.on_close_callback:
            self.on_close_callback()
        if self.parent:
            self.parent.remove_widget(self)

    def _do_register(self, instance):
        username = self.username_field.text.strip()
        email = self.email_field.text.strip()
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

        api.register(
            username=username,
            email=email,
            password=password,
            full_name=None,
            on_success=self._on_register_success,
            on_failure=self._on_register_failure
        )

    def _on_register_success(self, result):
        notify.success("Регистрация успешна! Теперь войдите.")
        self.close()
        if self.on_register_success_callback:
            self.on_register_success_callback()

    def _on_register_failure(self, req, error):
        notify.error("Ошибка. Возможно, имя или email уже заняты.")


class AuthModal(MDCard):
    """Главное модальное окно авторизации"""

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

        self.login_modal = None
        self.register_modal = None

        title = MDLabel(
            text="Войдите в свой аккаунт",
            halign="center",
            size_hint_y=None,
            height=dp(32),
            theme_text_color="Primary",
            bold=True,
            font_size=dp(20)
        )
        self.add_widget(title)

        subtitle = MDLabel(
            text="чтобы получить доступ ко всем функциям приложения",
            halign="center",
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Secondary",
            font_size=dp(12)
        )
        self.add_widget(subtitle)

        self.add_widget(MDBoxLayout(size_hint_y=None, height=dp(4)))

        google_btn = MDRaisedButton(
            text="Войти через Google",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self._on_google_click
        )
        google_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(google_btn)

        login_btn = MDRaisedButton(
            text="Войти по логину и паролю",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self._show_login_form
        )
        login_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(login_btn)

        register_btn = MDRaisedButton(
            text="Зарегистрироваться",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self._show_register
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

    def _on_google_click(self, instance):
        self.close()
        if self.on_login_success_callback:
            self.on_login_success_callback('google')

    def close(self, instance=None):
        if self.on_close_callback:
            self.on_close_callback()
        if self.parent:
            self.parent.remove_widget(self)

    def _show_login_form(self, instance):
        self.close()
        Clock.schedule_once(lambda dt: self._create_login_modal(), 0.2)

    def _create_login_modal(self):
        if self.login_modal and self.login_modal.parent:
            return
        self.login_modal = LoginModal(
            parent_screen=self.parent_screen,
            on_close=self._on_login_close,
            on_login_success=self._on_login_form_success
        )
        self.parent_screen.add_widget(self.login_modal)

    def _on_login_close(self):
        self.login_modal = None

    def _on_login_form_success(self):
        self.login_modal = None
        if self.on_login_success_callback:
            Clock.schedule_once(lambda dt: self.on_login_success_callback('login_form'), 0.1)

    def _show_register(self, instance):
        self.close()
        Clock.schedule_once(lambda dt: self._create_register_modal(), 0.2)

    def _create_register_modal(self):
        if self.register_modal and self.register_modal.parent:
            return
        self.register_modal = RegisterModal(
            parent_screen=self.parent_screen,
            on_close=self._on_register_close,
            on_register_success=self._on_register_form_success
        )
        self.parent_screen.add_widget(self.register_modal)

    def _on_register_close(self):
        self.register_modal = None

    def _on_register_form_success(self):
        self.register_modal = None
        notify.success("Регистрация успешна! Теперь войдите.")