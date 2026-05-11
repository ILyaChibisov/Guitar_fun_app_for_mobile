# screens/home_screen.py
"""
Главный экран гитарного приложения
"""
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.components.carousel import MainCarousel
from api.client import api
from utils.notifications import notify
from utils.kivy_imports import MDRaisedButton, MDIconButton, MDBoxLayout

logger = screen_logger('Home')


def hex_to_rgb(hex_color):
    """Конвертирует HEX цвет в RGB список"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


class WelcomePopup(MDCard):
    """Всплывающее окно приветствия"""

    def __init__(self, username, on_complete=None, **kwargs):
        super().__init__(**kwargs)
        self.username = username
        self.on_complete = on_complete

        self.orientation = 'vertical'
        self.size_hint = (0.85, None)
        self.height = dp(180)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 6
        self.radius = [theme.CORNER_RADIUS] * 4
        self.md_bg_color = [1, 1, 1, 0.95]
        self.padding = [dp(20), dp(20), dp(20), dp(20)]
        self.spacing = dp(10)

        guitar_icon = MDLabel(
            text="🎸",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1]
        )

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

        self.opacity = 0
        self.scale = 0.8
        anim = Animation(opacity=1, scale=1, duration=0.3, t='out_back')
        anim.start(self)

        Clock.schedule_once(self._fade_out, 3)

    def _fade_out(self, dt):
        anim = Animation(opacity=0, scale=0.8, duration=0.3, t='in_back')
        anim.bind(on_complete=lambda *args: self._on_complete())
        anim.start(self)

    def _on_complete(self):
        if self.parent:
            self.parent.remove_widget(self)
        if self.on_complete:
            self.on_complete()


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

        # Кнопка назад
        back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.close
        )
        self.add_widget(back_btn)

        # Заголовок
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

        # Поле username
        self.username_field = MDTextField(
            hint_text="Имя пользователя или Email",
            mode="fill",
            size_hint_y=None,
            height=dp(56),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.username_field)

        # Поле пароль
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

        # Кнопки
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

        # Кнопка назад
        back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.close
        )
        self.add_widget(back_btn)

        # Заголовок
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

        # Поле username
        self.username_field = MDTextField(
            hint_text="Имя пользователя",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.username_field)

        # Поле email
        self.email_field = MDTextField(
            hint_text="Email",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            font_size=dp(13)
        )
        self.add_widget(self.email_field)

        # Поле пароль
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

        # Поле подтверждения пароля
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

        # Кнопки
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
    """Главное модальное окно авторизации (выбор способа входа)"""

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

        # Заголовок
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

        # Подзаголовок
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

        # Кнопка входа через Google
        google_btn = MDRaisedButton(
            text="Войти через Google",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self._on_google_click
        )
        google_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(google_btn)

        # Кнопка входа по логину/паролю
        login_btn = MDRaisedButton(
            text="Войти по логину и паролю",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self._show_login_form
        )
        login_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(login_btn)

        # Кнопка регистрации
        register_btn = MDRaisedButton(
            text="Зарегистрироваться",
            size_hint=(0.9, None),
            height=dp(44),
            on_release=self._show_register
        )
        register_btn.pos_hint = {'center_x': 0.5}
        self.add_widget(register_btn)

        # Кнопка пропуска
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


class HomeScreen(BaseScreen):
    """Главный экран приложения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        self.user = None
        self.auth_check_done = False
        self.welcome_popup = None
        self.carousel = None

        self.init_ui()
        Clock.schedule_once(self._check_auth, 0.5)
        logger.info('Главный экран создан')

    def init_ui(self):
        """Инициализация интерфейса"""
        # Создаём заголовок (будет сверху)
        title = MDLabel(
            text="GuitarFuns",
            font_size=dp(42),
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            size_hint_y=None,
            height=dp(70)
        )

        # Создаём карусель
        self.carousel = MainCarousel(
            screen_manager=self.manager,
            on_item_selected=self._on_carousel_item_selected
        )

        # Используем базовый метод для построения UI
        # Передаём title как top_widget (он будет над каруселью)
        self.build_ui(content_widget=self.carousel, top_widget=title)

        # Добавляем растягивающиеся виджеты для вертикального центрирования
        # Находим контейнер и добавляем отступы сверху и снизу
        if self._content_container:
            # Убираем лишние отступы из контейнера
            self._content_container.padding = [
                layout_config.SIDE_PADDING,  # левый
                dp(20),  # верхний (отступ после заголовка)
                layout_config.SIDE_PADDING,  # правый
                layout_config.get_bottom_padding() + dp(20)  # нижний
            ]

    def _show_welcome(self, username):
        """Показывает всплывающее окно приветствия"""
        if self.welcome_popup and self.welcome_popup.parent:
            return

        self.welcome_popup = WelcomePopup(
            username,
            on_complete=self._on_welcome_closed
        )

        # Добавляем в основной контейнер
        if self._main_layout:
            self._main_layout.add_widget(self.welcome_popup)
        else:
            self.add_widget(self.welcome_popup)

    def _on_welcome_closed(self):
        """Обработчик закрытия окна приветствия"""
        self.welcome_popup = None

    def _check_auth(self, dt):
        """Проверяет авторизацию при запуске"""
        if self.auth_check_done:
            return
        self.auth_check_done = True

        if api.access_token:
            api.get_current_user(
                on_success=self._on_auth_success,
                on_failure=self._on_auth_failure
            )
        else:
            logger.info("Нет токена, показываем AuthModal")
            app = MDApp.get_running_app()
            if hasattr(app, 'open_profile'):
                Clock.schedule_once(lambda x: app.open_profile(), 0.1)

    def _on_auth_success(self, user):
        """Обработчик успешной авторизации"""
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        logger.info(f'Пользователь авторизован: {username}')
        Clock.schedule_once(lambda dt: self._show_welcome(username), 0.1)

    def _on_auth_failure(self, req, error):
        """Обработчик ошибки авторизации"""
        logger.warning(f'Авторизация не пройдена: {error}')
        app = MDApp.get_running_app()
        if hasattr(app, 'open_profile'):
            Clock.schedule_once(lambda x: app.open_profile(), 0.1)

    def on_login_success(self):
        """Обработчик успешного входа через модальное окно"""
        if api.access_token:
            api.get_current_user(
                on_success=self._on_user_data_loaded,
                on_failure=lambda req, err: None
            )

    def _on_user_data_loaded(self, user):
        """Обработчик загрузки данных пользователя"""
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        self._show_welcome(username)

    def _on_carousel_item_selected(self, screen_name):
        """Обработчик выбора элемента в карусели"""
        if screen_name == 'profile':
            self._open_profile()
        elif hasattr(self, 'manager') and self.manager:
            self.manager.transition.direction = 'left'
            self.manager.current = screen_name

    def _open_profile(self):
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

    def on_pre_enter(self):
        """Вызывается перед входом на экран"""
        if self.carousel:
            self.carousel.start_auto_scroll()
        return super().on_pre_enter()

    def on_leave(self):
        """Вызывается при выходе с экрана"""
        if self.carousel:
            self.carousel.stop_auto_scroll()
        return super().on_leave()