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
from kivymd.uix.snackbar import Snackbar
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
import threading
import webbrowser
import http.server
import socketserver
import urllib.parse

logger = screen_logger('Home')


# ============ Локальный сервер для OAuth callback ============

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик callback от Google OAuth"""

    tokens = None

    def do_GET(self):
        """Обрабатывает GET запрос с токенами"""
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        # Извлекаем токены
        access_token = query.get('access_token', [None])[0]
        refresh_token = query.get('refresh_token', [None])[0]

        if access_token:
            OAuthCallbackHandler.tokens = {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            # Используем обычную строку, закодированную в utf-8
            html = """
            <html>
            <body style="text-align:center; padding:50px; font-family:sans-serif;">
            <h2>✅ Авторизация успешна!</h2>
            <p>Можете закрыть это окно и вернуться в приложение.</p>
            <script>setTimeout(window.close, 2000);</script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <html>
            <body style="text-align:center; padding:50px;font-family:sans-serif;">
            <h2>🔄 Авторизация...</h2>
            <p>Подождите, идёт обработка...</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        """Отключаем логи сервера"""
        pass


class OAuthServer:
    """Локальный сервер для приёма Google OAuth callback"""

    _instance = None
    port = 8080

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.server = None
        self.thread = None

    def start(self):
        """Запускает сервер в отдельном потоке"""
        if self.server:
            return

        handler = OAuthCallbackHandler
        self.server = socketserver.TCPServer(("127.0.0.1", self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"OAuth сервер запущен на порту {self.port}")

    def stop(self):
        """Останавливает сервер"""
        if self.server:
            self.server.shutdown()
            self.server = None
            logger.info("OAuth сервер остановлен")

    def get_tokens(self):
        """Возвращает полученные токены и очищает их"""
        tokens = OAuthCallbackHandler.tokens
        OAuthCallbackHandler.tokens = None
        return tokens


# Глобальный экземпляр OAuth сервера
oauth_server = OAuthServer()


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
        self.radius = [theme.CORNER_RADIUS_SMALL]

    def on_press(self):
        anim = Animation(opacity=0.8, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)


class AuthModal(MDCard):
    def __init__(self, on_close=None, on_login_success=None, **kwargs):
        super().__init__(**kwargs)
        self.on_close_callback = on_close
        self.on_login_success_callback = on_login_success
        self.waiting_for_callback = False

        self.orientation = 'vertical'
        self.size_hint = (0.85, None)
        self.height = dp(340)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 4
        self.radius = [theme.CORNER_RADIUS, theme.CORNER_RADIUS, theme.CORNER_RADIUS, theme.CORNER_RADIUS]
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
        google_btn.bind(on_release=self.login_google)
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
        skip_btn.radius = [theme.CORNER_RADIUS_SMALL]
        self.add_widget(skip_btn)

        self.login_modal = None
        self.register_modal = None

        # Запускаем OAuth сервер
        oauth_server.start()

    def close(self, instance=None):
        if self.waiting_for_callback:
            Clock.unschedule(self.check_callback)
        if self.on_close_callback:
            self.on_close_callback()
        self.parent.remove_widget(self)

    def login_google(self, instance):
        """Вход через Google"""
        self.close()
        self.start_google_oauth()

    def start_google_oauth(self):
        """Запускает Google OAuth процесс"""
        self.waiting_for_callback = True

        # Формируем URL с локальным callback
        redirect_uri = f"http://127.0.0.1:{oauth_server.port}/callback"
        auth_url = f"{api.config.API_BASE_URL}/auth/google/login?redirect_uri={urllib.parse.quote(redirect_uri)}"

        # Открываем браузер
        webbrowser.open(auth_url)

        # Начинаем ожидание callback
        Clock.schedule_interval(self.check_callback, 1)

    def check_callback(self, dt):
        """Проверяет, пришёл ли callback"""
        if not self.waiting_for_callback:
            return False

        tokens = oauth_server.get_tokens()
        if tokens and tokens.get('access_token'):
            self.waiting_for_callback = False
            Clock.unschedule(self.check_callback)
            self.process_tokens(tokens['access_token'], tokens.get('refresh_token'))
            return False
        return True

    def process_tokens(self, access_token, refresh_token):
        """Обрабатывает полученные токены"""
        api.access_token = access_token
        api.refresh_token = refresh_token
        api._save_tokens()

        api.get_current_user(
            on_success=self.on_oauth_success,
            on_failure=self.on_oauth_failure
        )

    def on_oauth_success(self, user):
        """Успешный OAuth вход"""
        Snackbar(text=f"Добро пожаловать, {user.get('username')}! 🎸").open()
        if self.on_login_success_callback:
            self.on_login_success_callback()

    def on_oauth_failure(self, req, error):
        """Ошибка OAuth входа"""
        Snackbar(text="❌ Ошибка авторизации через Google").open()

    def show_login_form(self, instance):
        self.close()
        Clock.schedule_once(lambda dt: self.show_login_modal(), 0.2)

    def show_login_modal(self):
        if self.login_modal and self.login_modal.parent:
            return
        self.login_modal = LoginModal(on_close=self.on_login_close, on_login_success=self.on_login_success)
        self.parent.add_widget(self.login_modal)

    def on_login_close(self):
        self.login_modal = None

    def show_register(self, instance):
        self.close()
        Clock.schedule_once(lambda dt: self.show_register_modal(), 0.2)

    def show_register_modal(self):
        if self.register_modal and self.register_modal.parent:
            return
        self.register_modal = RegisterModal(on_close=self.on_register_close,
                                            on_register_success=self.on_register_success)
        self.parent.add_widget(self.register_modal)

    def on_register_close(self):
        self.register_modal = None

    def on_register_success(self):
        self.register_modal = None
        Snackbar(text="✅ Регистрация успешна! Теперь войдите.").open()

    def on_login_success(self):
        self.login_modal = None
        if self.on_login_success_callback:
            self.on_login_success_callback()


class LoginModal(MDCard):
    def __init__(self, on_close=None, on_login_success=None, **kwargs):
        super().__init__(**kwargs)
        self.on_close_callback = on_close
        self.on_login_success_callback = on_login_success

        self.orientation = 'vertical'
        self.size_hint = (0.85, None)
        self.height = dp(280)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 4
        self.radius = [theme.CORNER_RADIUS, theme.CORNER_RADIUS, theme.CORNER_RADIUS, theme.CORNER_RADIUS]
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
        cancel_btn.radius = [theme.CORNER_RADIUS_SMALL]

        login_btn = MDRaisedButton(text="Войти", size_hint=(0.5, 1),
                                   md_bg_color=theme.PRIMARY,
                                   theme_text_color="Custom", text_color=[1, 1, 1, 1],
                                   on_release=self.do_login)
        login_btn.radius = [theme.CORNER_RADIUS_SMALL]

        buttons_box.add_widget(cancel_btn)
        buttons_box.add_widget(login_btn)
        self.add_widget(buttons_box)

    def close(self, instance=None):
        if self.on_close_callback:
            self.on_close_callback()
        self.parent.remove_widget(self)

    def do_login(self, instance):
        username = self.username_field.text
        password = self.password_field.text
        if not username or not password:
            Snackbar(text="Заполните все поля").open()
            return
        api.login(username=username, password=password,
                  on_success=self.on_login_success, on_failure=self.on_login_failure)

    def on_login_success(self, result):
        Snackbar(text="✅ Вход выполнен успешно!").open()
        self.close()
        if self.on_login_success_callback:
            self.on_login_success_callback()

    def on_login_failure(self, req, error):
        Snackbar(text="❌ Неверное имя пользователя или пароль").open()


class RegisterModal(MDCard):
    def __init__(self, on_close=None, on_register_success=None, **kwargs):
        super().__init__(**kwargs)
        self.on_close_callback = on_close
        self.on_register_success_callback = on_register_success

        self.orientation = 'vertical'
        self.size_hint = (0.85, None)
        self.height = dp(340)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.elevation = 4
        self.radius = [theme.CORNER_RADIUS, theme.CORNER_RADIUS, theme.CORNER_RADIUS, theme.CORNER_RADIUS]
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
        cancel_btn.radius = [theme.CORNER_RADIUS_SMALL]

        register_btn = MDRaisedButton(text="Зарегистрироваться", size_hint=(0.5, 1),
                                      md_bg_color=theme.PRIMARY,
                                      theme_text_color="Custom", text_color=[1, 1, 1, 1],
                                      on_release=self.do_register)
        register_btn.radius = [theme.CORNER_RADIUS_SMALL]

        buttons_box.add_widget(cancel_btn)
        buttons_box.add_widget(register_btn)
        self.add_widget(buttons_box)

    def close(self, instance=None):
        if self.on_close_callback:
            self.on_close_callback()
        self.parent.remove_widget(self)

    def do_register(self, instance):
        username = self.username_field.text
        email = self.email_field.text
        password = self.password_field.text
        confirm = self.confirm_field.text
        if not username or not email or not password:
            Snackbar(text="Заполните все поля").open()
            return
        if password != confirm:
            Snackbar(text="Пароли не совпадают").open()
            return
        api.register(username=username, email=email, password=password, full_name=None,
                     on_success=self.on_register_success, on_failure=self.on_register_failure)

    def on_register_success(self, result):
        self.close()
        if self.on_register_success_callback:
            self.on_register_success_callback()

    def on_register_failure(self, req, error):
        Snackbar(text="❌ Ошибка. Возможно, имя или email уже заняты.").open()


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = None
        self.auth_modal = None

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
        tuner_btn.radius = [theme.CORNER_RADIUS_SMALL]

        songs_btn = MDRaisedButton(text="Песни", icon="music-note", size_hint=(0.8, None), height=dp(44),
                                   pos_hint={"center_x": 0.5}, md_bg_color=theme.PRIMARY,
                                   on_release=lambda x: self.navigate_to('songs'))
        songs_btn.radius = [theme.CORNER_RADIUS_SMALL]

        chords_btn = MDRaisedButton(text="Аккорды", icon="guitar-acoustic", size_hint=(0.8, None), height=dp(44),
                                    pos_hint={"center_x": 0.5}, md_bg_color=theme.PRIMARY,
                                    on_release=lambda x: self.navigate_to('chords'))
        chords_btn.radius = [theme.CORNER_RADIUS_SMALL]

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
        self.auth_status.text = "👤 Гость"
        self.show_auth_modal()

    def show_auth_modal(self):
        if self.auth_modal and self.auth_modal.parent:
            return
        self.auth_modal = AuthModal(on_close=self.on_modal_close, on_login_success=self.on_login_success)
        self.add_widget(self.auth_modal)

    def on_modal_close(self):
        self.auth_modal = None

    def on_login_success(self):
        self.auth_modal = None
        self.check_auth(0)

    def open_profile(self):
        """Открывает профиль - вызывается из верхней панели"""
        if api.is_authenticated():
            Snackbar(text=f"Вы вошли как {api.user_data.get('username')} 🎸").open()
            logger.info(f'Открыт профиль: {api.user_data.get("username")}')
        else:
            logger.info('Не авторизован, показываем окно авторизации')
            self.show_auth_modal()