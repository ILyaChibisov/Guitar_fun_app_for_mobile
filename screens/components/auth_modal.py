# screens/components/auth_modal.py
import re
from io import BytesIO
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from api.client import api
from utils.notifications import notify
from screens.components.language_selector import LanguageSelector

logger = get_logger('AuthModal')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


class AuthModal(ModalView):
    """
    Красивое всплывающее окно авторизации.
    В фирменном зелёном стиле (подходит для любой темы).
    """

    def __init__(self, parent_screen=None, on_close=None, on_login_success=None, **kwargs):
        super().__init__(
            size_hint=(1, 1),
            auto_dismiss=False,
            background_color=(0, 0, 0, 0),  # Полностью прозрачный фон
            background='',
            **kwargs
        )
        self.parent_screen = parent_screen
        self.on_close_callback = on_close
        self.on_login_success_callback = on_login_success

        self._is_login_mode = True

        root_layout = FloatLayout()

        # --- КАРТОЧКА (Фирменный стиль) ---
        self.card = MDCard(
            orientation='vertical',
            size_hint=(0.9, None),
            height=dp(540),  # Увеличили высоту из-за кнопки "Забыли пароль"
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            padding=[dp(24), dp(16), dp(24), dp(24)],
            spacing=dp(8),
            radius=[dp(24)] * 4,
            md_bg_color=[0.12, 0.25, 0.22, 0.95],
            elevation=15,
            line_color=[0.46, 0.70, 0.71, 0.4],
            line_width=1.5
        )

        # --- ЛОГОТИП И ЯЗЫК ---
        top_bar = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))

        self.logo_image = Image(
            size_hint=(None, None),
            size=(dp(120), dp(40)),
            pos_hint={'center_y': 0.5}
        )
        self._load_logo()
        top_bar.add_widget(self.logo_image)

        top_bar.add_widget(BoxLayout())  # Отступ

        self.lang_selector = LanguageSelector(on_language_change=self._on_language_change)
        self.lang_selector.size_hint = (None, None)
        self.lang_selector.size = (dp(50), dp(36))
        self.lang_selector.pos_hint = {'center_y': 0.5}
        top_bar.add_widget(self.lang_selector)

        self.card.add_widget(top_bar)

        # --- ЗАГОЛОВОК ---
        self.title_label = MDLabel(
            text="С возвращением!",
            font_size=sp(24),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )
        self.card.add_widget(self.title_label)

        # --- ЛЕЙБЛ ОШИБКИ ---
        self.error_label = MDLabel(
            text="",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 1],
            opacity=0,
            bold=True
        )
        self.card.add_widget(self.error_label)

        # --- ФОРМА ---
        self.form_box = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, adaptive_height=True)

        # 1. Email / Логин
        self.email_field = MDTextField(
            hint_text="Email или Логин",
            mode="fill",
            size_hint_y=None,
            height=dp(50),
            font_size=sp(14),
            icon_left="account-outline",
            fill_color_normal=[0, 0, 0, 0.2],
            fill_color_focus=[0, 0, 0, 0.3],
            text_color_normal=[1, 1, 1, 1]
        )
        self.form_box.add_widget(self.email_field)

        # 2. Логин
        self.username_field = MDTextField(
            hint_text="Придумайте логин",
            mode="fill",
            size_hint_y=None,
            height=dp(50),
            font_size=sp(14),
            icon_left="account-plus-outline",
            opacity=0,
            disabled=True,
            fill_color_normal=[0, 0, 0, 0.2],
            fill_color_focus=[0, 0, 0, 0.3],
            text_color_normal=[1, 1, 1, 1]
        )
        self.form_box.add_widget(self.username_field)

        # 3. Пароль
        self.password_field = MDTextField(
            hint_text="Пароль (мин. 6 символов)",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(50),
            font_size=sp(14),
            icon_left="lock-outline",
            fill_color_normal=[0, 0, 0, 0.2],
            fill_color_focus=[0, 0, 0, 0.3],
            text_color_normal=[1, 1, 1, 1]
        )
        self.form_box.add_widget(self.password_field)

        # 4. Подтверждение
        self.confirm_field = MDTextField(
            hint_text="Повторите пароль",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(50),
            font_size=sp(14),
            icon_left="lock-check-outline",
            opacity=0,
            disabled=True,
            fill_color_normal=[0, 0, 0, 0.2],
            fill_color_focus=[0, 0, 0, 0.3],
            text_color_normal=[1, 1, 1, 1]
        )
        self.form_box.add_widget(self.confirm_field)

        self.card.add_widget(self.form_box)

        # --- КНОПКА ДЕЙСТВИЯ ---
        self.action_btn = MDRaisedButton(
            text="Войти",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=theme.PRIMARY,
            text_color=[1, 1, 1, 1],
            font_size=sp(16),
            on_release=self._on_action_press
        )
        self.card.add_widget(self.action_btn)

        # --- КНОПКА "ЗАБЫЛИ ПАРОЛЬ?" ---
        self.forgot_btn = MDFlatButton(
            text="Забыли пароль?",
            font_size=sp(12),
            theme_text_color="Custom",
            text_color=[0.8, 0.8, 0.8, 1],
            pos_hint={'center_x': 0.5},
            on_release=self._show_forgot_password
        )
        self.card.add_widget(self.forgot_btn)

        # --- ПЕРЕКЛЮЧАТЕЛЬ РЕЖИМА ---
        self.switch_box = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None),
            height=dp(40), spacing=dp(4), pos_hint={'center_x': 0.5}
        )
        self.switch_label = MDLabel(
            text="Нет аккаунта?", font_size=sp(13),
            halign="right", theme_text_color="Custom", text_color=[0.8, 0.8, 0.8, 1]
        )
        self.switch_btn = MDFlatButton(
            text="Зарегистрироваться", font_size=sp(13),
            theme_text_color="Custom", text_color=theme.PRIMARY,
            on_release=self._toggle_mode
        )
        self.switch_box.add_widget(self.switch_label)
        self.switch_box.add_widget(self.switch_btn)
        self.card.add_widget(self.switch_box)

        root_layout.add_widget(self.card)
        self.add_widget(root_layout)

        Clock.schedule_once(lambda dt: self.email_field.focus, 0.5)

    def _load_logo(self):
        if HAS_ASSETS:
            try:
                logo_data = load_asset_as_bytes("logo_name_png")
                if logo_data:
                    img = CoreImage(BytesIO(logo_data), ext="png")
                    self.logo_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки логотипа: {e}")
        self.logo_image.source = ""

    def _show_error(self, text):
        self.error_label.text = text
        self.error_label.opacity = 1
        Animation(opacity=1, duration=0.2).start(self.error_label)

    def _clear_error(self):
        self.error_label.text = ""
        self.error_label.opacity = 0

    def _on_language_change(self, lang_code):
        from state.settings_state import settings_state
        settings_state.set_language(lang_code)
        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_language'):
            app.apply_language(lang_code)
        notify.info(f"Язык изменен на {lang_code.upper()}")

    def _toggle_mode(self, *args):
        self._clear_error()
        self._is_login_mode = not self._is_login_mode

        if self._is_login_mode:
            self.title_label.text = "С возвращением!"
            self.action_btn.text = "Войти"
            self.switch_label.text = "Нет аккаунта?"
            self.switch_btn.text = "Зарегистрироваться"
            self.forgot_btn.opacity = 1
            self.forgot_btn.disabled = False

            self.username_field.opacity = 0
            self.username_field.disabled = True
            self.confirm_field.opacity = 0
            self.confirm_field.disabled = True
            self.email_field.hint_text = "Email или Логин"

            new_height = dp(540)
        else:
            self.title_label.text = "Создать аккаунт"
            self.action_btn.text = "Зарегистрироваться"
            self.switch_label.text = "Уже есть аккаунт?"
            self.switch_btn.text = "Войти"
            self.forgot_btn.opacity = 0
            self.forgot_btn.disabled = True

            self.username_field.opacity = 1
            self.username_field.disabled = False
            self.confirm_field.opacity = 1
            self.confirm_field.disabled = False
            self.email_field.hint_text = "Email"

            new_height = dp(620)

        Animation(height=new_height, duration=0.2).start(self.card)

    def _on_action_press(self, *args):
        self._clear_error()
        email = self.email_field.text.strip()
        password = self.password_field.text

        if not email or not password:
            self._show_error("Заполните все поля")
            return

        if self._is_login_mode:
            self._do_login(email, password)
        else:
            username = self.username_field.text.strip()

            if not username or len(username) < 3:
                self._show_error("Логин должен быть не менее 3 символов")
                return

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                self._show_error("Введите корректный Email")
                return

            if len(password) < 6:
                self._show_error("Пароль должен быть не менее 6 символов")
                return

            confirm = self.confirm_field.text
            if password != confirm:
                self._show_error("Пароли не совпадают")
                return

            self._do_register(username, email, password)

    # ============ ЛОГИКА ВХОДА ============
    def _do_login(self, username, password):
        self.action_btn.text = "Вход..."
        self.action_btn.disabled = True

        api.login(
            username=username,
            password=password,
            on_success=self._on_login_success,
            on_failure=self._on_login_failure
        )

    def _on_login_success(self, result):
        self.action_btn.text = "Войти"
        self.action_btn.disabled = False
        api.get_current_user(on_success=self._on_user_loaded)
        notify.success("Вход выполнен успешно!")
        logger.info("✅ Вход выполнен")

    def _on_login_failure(self, req, error):
        self.action_btn.text = "Войти"
        self.action_btn.disabled = False

        if "401" in str(error) or "Unauthorized" in str(error) or "Invalid credentials" in str(error):
            self._show_error("Неверный логин/Email или пароль")
        else:
            self._show_error(f"Ошибка входа. Проверьте интернет.")

    def _on_user_loaded(self, user):
        api.user_data = user
        if self.on_login_success_callback:
            self.on_login_success_callback()
        self.dismiss()
        if self.on_close_callback:
            self.on_close_callback()

    # ============ ЛОГИКА РЕГИСТРАЦИИ ============
    def _do_register(self, username, email, password):
        self.action_btn.text = "Отправка кода..."
        self.action_btn.disabled = True

        api.send_verification_code(
            email=email,
            on_success=lambda res: self._on_code_sent(username, email, password),
            on_failure=self._on_code_send_failure
        )

    def _on_code_sent(self, username, email, password):
        self.action_btn.text = "Зарегистрироваться"
        self.action_btn.disabled = False
        self._show_error("")

        self.code_field = MDTextField(
            hint_text="Код из письма (4 цифры)",
            mode="fill",
            size_hint_y=None,
            height=dp(56),
            font_size=sp(20),
            halign="center",
            input_filter="int",
            max_text_length=4
        )

        self.code_dialog = MDDialog(
            title="Проверьте почту",
            text=f"Мы отправили код на {email}.",
            type="custom",
            content_cls=self.code_field,
            buttons=[
                MDFlatButton(
                    text="Отмена",
                    on_release=lambda x: self.code_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Подтвердить",
                    md_bg_color=theme.PRIMARY,
                    on_release=lambda x: self._verify_and_register(username, email, password)
                ),
            ],
        )
        self.code_dialog.open()

    def _verify_and_register(self, username, email, password):
        code = self.code_field.text.strip()
        if len(code) != 4:
            notify.warning("Введите 4-значный код")
            return

        self.code_dialog.dismiss()
        self.action_btn.text = "Создание аккаунта..."
        self.action_btn.disabled = True

        api.register_with_code(
            username=username,
            email=email,
            password=password,
            code=code,
            on_success=self._on_register_success,
            on_failure=self._on_register_failure
        )

    def _on_register_success(self, result):
        self.action_btn.text = "Зарегистрироваться"
        self.action_btn.disabled = False

        api.get_current_user(on_success=lambda user: setattr(api, 'user_data', user))

        success_label = MDLabel(
            text="Ваш аккаунт успешно создан!\nДобро пожаловать в GuitarFuns.",
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            size_hint_y=None,
            height=dp(60)
        )

        self.success_dialog = MDDialog(
            title="Успешная регистрация! 🎸",
            type="custom",
            content_cls=success_label,
            buttons=[
                MDRaisedButton(
                    text="Поехали!",
                    md_bg_color=theme.PRIMARY,
                    on_release=self._close_on_success
                ),
            ],
        )
        self.success_dialog.open()

    def _close_on_success(self, *args):
        self.success_dialog.dismiss()
        if self.on_login_success_callback:
            self.on_login_success_callback()
        self.dismiss()
        if self.on_close_callback:
            self.on_close_callback()

    def _on_register_failure(self, req, error):
        self.action_btn.text = "Зарегистрироваться"
        self.action_btn.disabled = False

        if "Email already exists" in error:
            self._show_error("Эта почта уже зарегистрирована")
        elif "Username already exists" in error:
            self._show_error("Этот логин уже занят")
        else:
            self._show_error(error)

    def _on_code_send_failure(self, req, error):
        self.action_btn.text = "Зарегистрироваться"
        self.action_btn.disabled = False

        if "Email already exists" in error:
            self._show_error("Эта почта уже зарегистрирована")
        else:
            self._show_error(error)

    # ============ ВОССТАНОВЛЕНИЕ ПАРОЛЯ ============
    def _show_forgot_password(self, instance):
        """Шаг 1: Проверка пользователя и отправка кода"""
        if not self._is_login_mode:
            return

        email_input = MDTextField(
            hint_text="Email или Логин",
            mode="fill",
            size_hint_y=None,
            height=dp(56)
        )

        def send_reset_code(btn):
            identifier = email_input.text.strip()
            if not identifier:
                notify.warning("Введите Email или Логин")
                return

            dialog.dismiss()

            # 1. Сначала проверяем, есть ли такой пользователь
            def on_check_success(res):
                # Пользователь найден! Берем его реальный email из ответа сервера
                real_email = res.get("email")
                if not real_email:
                    notify.error("У пользователя не указан Email")
                    return

                # 2. Теперь отправляем код на этот реальный email
                api.send_verification_code(
                    email=real_email,
                    on_success=lambda r: self._on_reset_code_sent(real_email),
                    on_failure=lambda req, err: notify.error(f"Ошибка отправки: {err}")
                )

            def on_check_failure(req, err):
                notify.error(err)

            # Вызываем проверку
            api.check_user_exists(identifier, on_success=on_check_success, on_failure=on_check_failure)

        dialog = MDDialog(
            title="Восстановление пароля",
            text="Введите почту или логин, указанные при регистрации.",
            type="custom",
            content_cls=email_input,
            buttons=[
                MDFlatButton(text="Отмена", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="Продолжить",
                    md_bg_color=theme.PRIMARY,
                    on_release=send_reset_code
                )
            ]
        )
        dialog.open()

    def _on_reset_code_sent(self, email):
        """Пользователь получил код, просим ввести его и новый пароль"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            size_hint_y=None,
            height=dp(180)  # Увеличили высоту под 3 поля
        )

        code_input = MDTextField(
            hint_text="Код из письма (4 цифры)",
            mode="fill",
            size_hint_y=None,
            height=dp(50),
            input_filter="int",
            max_text_length=4
        )

        new_password_input = MDTextField(
            hint_text="Новый пароль",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(50)
        )

        confirm_password_input = MDTextField(
            hint_text="Подтвердите новый пароль",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(50)
        )

        content.add_widget(code_input)
        content.add_widget(new_password_input)
        content.add_widget(confirm_password_input)

        def reset_password(btn):
            code = code_input.text.strip()
            new_pass = new_password_input.text
            confirm_pass = confirm_password_input.text

            if len(code) != 4:
                notify.warning("Введите 4-значный код")
                return
            if len(new_pass) < 6:
                notify.warning("Пароль должен быть не менее 6 символов")
                return
            if new_pass != confirm_pass:
                notify.warning("Пароли не совпадают")
                return

            def on_success(res):
                notify.success("Пароль успешно изменен! Войдите с новым паролем.")
                dialog.dismiss()

            def on_failure(req, err):
                notify.error(f"Ошибка: {err}")

            api.reset_password(email=email, code=code, new_password=new_pass,
                               on_success=on_success, on_failure=on_failure)

        dialog = MDDialog(
            title="Новый пароль",
            text=f"Введите код из письма и придумайте новый пароль для {email}.",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Отмена", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="Изменить пароль",  # Переименовали кнопку
                    md_bg_color=theme.PRIMARY,
                    on_release=reset_password
                )
            ]
        )
        dialog.open()



    def on_dismiss(self):
        pass