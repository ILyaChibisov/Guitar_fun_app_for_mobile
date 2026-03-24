# screens/home_screen.py
"""
Главный экран с авторизацией через Google и VK
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api

logger = screen_logger('Home')


class AuthButton(MDRaisedButton):
    """Кнопка авторизации"""

    def __init__(self, icon, text, bg_color, text_color=[1, 1, 1, 1], **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.text = text
        self.md_bg_color = bg_color
        self.theme_text_color = "Custom"
        self.text_color = text_color
        self.size_hint = (1, None)
        self.height = dp(56)
        self.font_size = dp(16)
        self.ripple_behavior = True
        self.radius = [theme.CORNER_RADIUS_SMALL]

    def on_press(self):
        anim = Animation(opacity=0.8, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)


class HomeScreen(MDScreen):
    """Главный экран с авторизацией через Google и VK"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.user = None

        # Устанавливаем цвет фона
        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Главный контейнер
        from kivymd.uix.scrollview import MDScrollView
        scroll = MDScrollView(size_hint=(1, 1), bar_width=dp(4), bar_color=theme.PRIMARY_LIGHT)

        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20),
            size_hint_y=None,
            adaptive_height=True
        )

        # Заголовок
        title = MDLabel(
            text="GuitarFuns",
            font_style="H3",
            halign="center",
            size_hint_y=None,
            height=dp(100),
            theme_text_color="Primary",
            bold=True
        )

        # Статус авторизации
        self.auth_status = MDLabel(
            text="",
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Secondary",
            font_style="Caption"
        )

        # Карточка авторизации
        auth_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(200),
            padding=dp(16),
            spacing=dp(12),
            elevation=4,
            radius=[theme.CORNER_RADIUS],
            md_bg_color=theme.SURFACE
        )

        auth_title = MDLabel(
            text="Вход через соцсети",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Primary",
            bold=True
        )

        # Кнопка Google
        self.google_btn = AuthButton(
            icon="google",
            text="Войти через Google",
            bg_color=[0.96, 0.96, 0.96, 1],
            text_color=[0.2, 0.2, 0.2, 1]
        )
        self.google_btn.bind(on_release=self.login_google)

        # Кнопка VK
        self.vk_btn = AuthButton(
            icon="vk",
            text="Войти через ВКонтакте",
            bg_color=[0.27, 0.55, 0.76, 1],
            text_color=[1, 1, 1, 1]
        )
        self.vk_btn.bind(on_release=self.login_vk)

        # Кнопка выхода (показывается только когда авторизован)
        self.logout_btn = AuthButton(
            icon="logout",
            text="Выйти",
            bg_color=[0.9, 0.9, 0.9, 1],
            text_color=[0.5, 0.5, 0.5, 1]
        )
        self.logout_btn.bind(on_release=self.logout)
        self.logout_btn.opacity = 0
        self.logout_btn.disabled = True

        auth_card.add_widget(auth_title)
        auth_card.add_widget(self.google_btn)
        auth_card.add_widget(self.vk_btn)
        auth_card.add_widget(self.logout_btn)

        # Быстрый доступ
        quick_title = MDLabel(
            text="Быстрый доступ",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Primary",
            bold=True
        )

        buttons_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(170)
        )

        tuner_btn = MDRaisedButton(
            text="Открыть тюнер",
            icon="tune",
            size_hint=(0.8, None),
            height=dp(48),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=lambda x: self.navigate_to('tuner')
        )
        tuner_btn.radius = [theme.CORNER_RADIUS_SMALL]

        songs_btn = MDRaisedButton(
            text="Список песен",
            icon="music-note",
            size_hint=(0.8, None),
            height=dp(48),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            on_release=lambda x: self.navigate_to('songs')
        )
        songs_btn.radius = [theme.CORNER_RADIUS_SMALL]

        chords_btn = MDRaisedButton(
            text="Аккорды",
            icon="guitar-acoustic",
            size_hint=(0.8, None),
            height=dp(48),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            on_release=lambda x: self.navigate_to('chords')
        )
        chords_btn.radius = [theme.CORNER_RADIUS_SMALL]

        buttons_layout.add_widget(tuner_btn)
        buttons_layout.add_widget(songs_btn)
        buttons_layout.add_widget(chords_btn)

        layout.add_widget(title)
        layout.add_widget(self.auth_status)
        layout.add_widget(auth_card)
        layout.add_widget(quick_title)
        layout.add_widget(buttons_layout)

        spacer = MDBoxLayout(size_hint_y=None, height=dp(20))
        layout.add_widget(spacer)

        scroll.add_widget(layout)
        self.add_widget(scroll)

        # Проверяем авторизацию при запуске
        Clock.schedule_once(self.check_auth, 1)

        logger.info('Главный экран создан (Google/VK авторизация)')

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def navigate_to(self, screen_name):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = screen_name

    def check_auth(self, dt):
        """Проверяет авторизацию при запуске"""
        if api.access_token:
            self.auth_status.text = "🔐 Проверка авторизации..."
            api.get_current_user(
                on_success=self.on_auth_success,
                on_failure=self.on_auth_failure
            )
        else:
            self.auth_status.text = "👤 Не авторизован"

    def on_auth_success(self, user):
        """Успешная авторизация"""
        self.user = user
        self.auth_status.text = f"✅ Авторизован: {user.get('username')}"

        # Скрываем кнопки входа, показываем кнопку выхода
        self.google_btn.opacity = 0
        self.google_btn.disabled = True
        self.vk_btn.opacity = 0
        self.vk_btn.disabled = True
        self.logout_btn.opacity = 1
        self.logout_btn.disabled = False

        Snackbar(text=f"Добро пожаловать, {user.get('username')}! 🎸").open()
        logger.info(f'Пользователь авторизован: {user.get("username")}')

    def on_auth_failure(self, req, error):
        """Ошибка авторизации"""
        self.auth_status.text = "👤 Не авторизован"
        logger.warning('Авторизация не пройдена')

    def login_google(self, instance):
        """Вход через Google"""
        logger.info("Попытка входа через Google")

        self.auth_status.text = "⏳ Вход через Google..."

        # TODO: Реальная интеграция с Google OAuth
        # Сейчас имитация успешного входа
        Clock.schedule_once(lambda dt: self.simulate_auth_success(
            username="google_user",
            email="user@gmail.com"
        ), 1)

    def login_vk(self, instance):
        """Вход через ВКонтакте"""
        logger.info("Попытка входа через ВКонтакте")

        self.auth_status.text = "⏳ Вход через ВКонтакте..."

        # TODO: Реальная интеграция с VK OAuth
        # Сейчас имитация успешного входа
        Clock.schedule_once(lambda dt: self.simulate_auth_success(
            username="vk_user",
            email="user@vk.com"
        ), 1)

    def simulate_auth_success(self, username, email):
        """Имитация успешной авторизации (временная заглушка)"""
        # Сохраняем токены (заглушка)
        api.access_token = "mock_access_token"
        api.refresh_token = "mock_refresh_token"
        api._save_tokens()

        # Сохраняем данные пользователя
        self.user = {
            'id': 1,
            'username': username,
            'email': email,
            'full_name': None,
            'avatar_url': None
        }
        api.user_data = self.user

        self.on_auth_success(self.user)

    def logout(self, instance):
        """Выход из аккаунта"""
        self.auth_status.text = "⏳ Выход..."

        api.logout(
            on_success=self.on_logout_success,
            on_failure=self.on_logout_failure
        )

    def on_logout_success(self, result):
        """Успешный выход"""
        self.user = None
        self.auth_status.text = "👤 Не авторизован"

        # Показываем кнопки входа, скрываем кнопку выхода
        self.google_btn.opacity = 1
        self.google_btn.disabled = False
        self.vk_btn.opacity = 1
        self.vk_btn.disabled = False
        self.logout_btn.opacity = 0
        self.logout_btn.disabled = True

        Snackbar(text="👋 Вы вышли из аккаунта").open()
        logger.info('Пользователь вышел')

    def on_logout_failure(self, req, error):
        """Ошибка выхода"""
        self.auth_status.text = "👤 Не авторизован"
        Snackbar(text="Ошибка выхода").open()