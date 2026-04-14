# screens/home_screen.py
"""
Главный экран гитарного приложения
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.utils import rgba
from kivy.animation import Animation
from kivy.clock import Clock
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify
from utils.kivy_imports import MDRaisedButton, MDIconButton, MDBoxLayout
import os

# Импортируем ассеты из пакета data
try:
    from data import Assets, load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    print("⚠️ Модуль data не найден")

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

        # Фоновое изображение
        self.bg_image = None
        self.load_background()

        # Основной контейнер
        self.layout = MDBoxLayout(orientation='vertical', padding=[dp(20), dp(40), dp(20), dp(20)])

        # Заголовок
        title = MDLabel(
            text="GuitarFuns",
            font_size=dp(36),
            bold=True,
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            size_hint_y=None,
            height=dp(80)
        )
        self.layout.add_widget(title)

        # Статус авторизации
        self.auth_status = MDLabel(
            text="",
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            font_size=dp(12)
        )
        self.layout.add_widget(self.auth_status)

        # Быстрый доступ
        quick_title = MDLabel(
            text="Быстрый доступ",
            halign="center",
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            font_size=dp(18)
        )
        self.layout.add_widget(quick_title)

        # Кнопки
        buttons_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(156))

        tuner_btn = MDRaisedButton(
            text="Тюнер",
            size_hint=(0.8, None),
            height=dp(44),
            on_release=lambda x: self.navigate_to('tuner')
        )
        tuner_btn.pos_hint = {"center_x": 0.5}
        tuner_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        songs_btn = MDRaisedButton(
            text="Песни",
            size_hint=(0.8, None),
            height=dp(44),
            on_release=lambda x: self.navigate_to('songs')
        )
        songs_btn.pos_hint = {"center_x": 0.5}
        songs_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        chords_btn = MDRaisedButton(
            text="Аккорды",
            size_hint=(0.8, None),
            height=dp(44),
            on_release=lambda x: self.navigate_to('chords')
        )
        chords_btn.pos_hint = {"center_x": 0.5}
        chords_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        buttons_layout.add_widget(tuner_btn)
        buttons_layout.add_widget(songs_btn)
        buttons_layout.add_widget(chords_btn)
        self.layout.add_widget(buttons_layout)

        self.add_widget(self.layout)

        Clock.schedule_once(self.check_auth, 1)
        logger.info('Главный экран создан')

    def load_background(self):
        """Загружает фоновое изображение из встроенных ассетов"""
        try:
            from kivy.core.image import Image as CoreImage
            from io import BytesIO

            if HAS_ASSETS:
                # Варианты названий ассета
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]

                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        logger.info(f"Фон загружен из ассета: {name}")
                        break

                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")

                    with self.canvas.before:
                        Color(1, 1, 1, 1)
                        self.bg_image = Rectangle(
                            texture=img.texture,
                            pos=self.pos,
                            size=self.size
                        )
                    self.bind(pos=self._update_bg_image, size=self._update_bg_image)
                    logger.info('Фон успешно загружен из встроенных ассетов')
                    return
                else:
                    logger.warning('Ассет фона не найден, пробуем загрузить из файла')
            else:
                logger.warning('Модуль data не найден, пробуем загрузить из файла')

        except ImportError as e:
            logger.warning(f'Модуль data не найден: {e}')
        except Exception as e:
            logger.error(f'Ошибка загрузки фона из ассетов: {e}')

        # Fallback: загружаем из файловой системы
        self.load_background_from_file()

    def load_background_from_file(self):
        """Загружает фон из файловой системы (fallback)"""
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'background.jpg'),
            os.path.join(os.path.dirname(__file__), '..', 'assets', 'background.jpg'),
            'assets/background.jpg',
        ]

        bg_path = None
        for path in possible_paths:
            if os.path.exists(path):
                bg_path = path
                break

        if bg_path:
            try:
                with self.canvas.before:
                    Color(1, 1, 1, 1)
                    self.bg_image = Rectangle(
                        source=bg_path,
                        pos=self.pos,
                        size=self.size
                    )
                self.bind(pos=self._update_bg_image, size=self._update_bg_image)
                logger.info(f'Фон загружен из файла: {bg_path}')
            except Exception as e:
                logger.error(f'Ошибка загрузки фона из файла: {e}')
                self.set_default_background()
        else:
            logger.warning('Фоновое изображение не найдено')
            self.set_default_background()

    def _update_bg_image(self, *args):
        """Обновляет позицию и размер фона"""
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def set_default_background(self):
        """Устанавливает стандартный цвет фона"""
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        if hasattr(self, 'bg_rect'):
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