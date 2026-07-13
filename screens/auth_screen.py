# screens/auth_screen.py
"""
Экран авторизации с красивым дизайном
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from io import BytesIO

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.dialog import MDDialog
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('AuthScreen')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# Константа для логотипа
ASSET_LOGO_NAME_PNG = "logo_name_png"


class AuthScreen(BaseScreen):
    """Экран авторизации"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'auth_screen'
        self.bg_image = None
        self._login_mode = True  # True = вход, False = регистрация
        self._register_dialog = None

        self.init_ui()
        self.load_background()

        logger.info('Экран авторизации создан')

    def load_background(self):
        try:
            if HAS_ASSETS:
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
                        self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                    self.bind(pos=self._update_bg, size=self._update_bg)
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def init_ui(self):
        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(24), dp(0), dp(24), dp(0)]
        )

        # Верхний отступ (под TopNav)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding + dp(20)))

        # Центрирующий контейнер
        center_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            spacing=dp(16)
        )

        # ============ ЛОГОТИП ============
        logo_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            md_bg_color=[0, 0, 0, 0]
        )

        self.logo_image = Image(
            size_hint=(None, None),
            size=(dp(200), dp(80)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )

        if HAS_ASSETS:
            try:
                logo_data = load_asset_as_bytes(ASSET_LOGO_NAME_PNG)
                if logo_data:
                    img = CoreImage(BytesIO(logo_data), ext="png")
                    self.logo_image.texture = img.texture
                    logger.info("✅ Логотип загружен")
            except Exception as e:
                logger.error(f"Ошибка загрузки логотипа: {e}")

        logo_container.add_widget(self.logo_image)
        center_container.add_widget(logo_container)

        # ============ ЗАГОЛОВОК ============
        self.title_label = MDLabel(
            text="Добро пожаловать!",
            font_size=sp(24),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )
        center_container.add_widget(self.title_label)

        # ============ КАРТОЧКА С ФОРМОЙ ============
        self.card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(360),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            spacing=dp(12),
            radius=[theme.CORNER_RADIUS_MEDIUM] * 4,
            md_bg_color=[0.08, 0.08, 0.08, 0.85],
            elevation=4,
            line_color=[1, 1, 1, 0.1],
            line_width=0.5
        )

        # Поле для ввода email/username
        self.email_field = MDTextField(
            hint_text="Email или имя пользователя",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
            font_size=sp(14),
            foreground_color=[1, 1, 1, 1],  # Исправлено: text_color -> foreground_color
            hint_text_color=[0.6, 0.6, 0.6, 1],
            line_color_focus=[0.46, 0.70, 0.71, 1],
            fill_color_normal=[0, 0, 0, 0.3],
            fill_color_focus=[0, 0, 0, 0.2]
        )
        self.card.add_widget(self.email_field)

        # Поле для пароля
        self.password_field = MDTextField(
            hint_text="Пароль",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(52),
            font_size=sp(14),
            foreground_color=[1, 1, 1, 1],  # Исправлено: text_color -> foreground_color
            hint_text_color=[0.6, 0.6, 0.6, 1],
            line_color_focus=[0.46, 0.70, 0.71, 1],
            fill_color_normal=[0, 0, 0, 0.3],
            fill_color_focus=[0, 0, 0, 0.2]
        )
        self.card.add_widget(self.password_field)

        # Поле для подтверждения пароля (только при регистрации)
        self.confirm_field = MDTextField(
            hint_text="Подтвердите пароль",
            mode="fill",
            password=True,
            size_hint_y=None,
            height=dp(52),
            font_size=sp(14),
            foreground_color=[1, 1, 1, 1],  # Исправлено: text_color -> foreground_color
            hint_text_color=[0.6, 0.6, 0.6, 1],
            line_color_focus=[0.46, 0.70, 0.71, 1],
            fill_color_normal=[0, 0, 0, 0.3],
            fill_color_focus=[0, 0, 0, 0.2],
            opacity=0,
            disabled=True
        )
        self.card.add_widget(self.confirm_field)

        # Кнопка действия
        self.action_btn = MDRaisedButton(
            text="Войти",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=[0.46, 0.70, 0.71, 1],
            text_color=[1, 1, 1, 1],
            font_size=sp(16),
            on_release=self._on_action_press
        )
        self.card.add_widget(self.action_btn)

        # Переключатель режима
        self.switch_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]
        )

        self.switch_label = MDLabel(
            text="Нет аккаунта?",
            font_size=sp(13),
            halign="right",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            size_hint_x=1
        )

        self.switch_btn = MDIconButton(
            icon="arrow-right",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._toggle_mode
        )

        self.switch_layout.add_widget(self.switch_label)
        self.switch_layout.add_widget(self.switch_btn)
        self.card.add_widget(self.switch_layout)

        center_container.add_widget(self.card)
        center_container.add_widget(Widget(size_hint_y=1))

        main_layout.add_widget(center_container)

        # Нижний отступ
        bottom_padding = layout_config.get_bottom_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding + dp(20)))

        self.add_widget(main_layout)

        # Устанавливаем фокус на первое поле
        Clock.schedule_once(lambda dt: self.email_field.focus, 0.5)

    def _toggle_mode(self, instance):
        """Переключает режим входа/регистрации"""
        self._login_mode = not self._login_mode

        if self._login_mode:
            # Режим входа
            self.title_label.text = "Добро пожаловать!"
            self.action_btn.text = "Войти"
            self.switch_label.text = "Нет аккаунта?"
            self.switch_btn.icon = "arrow-right"
            self.confirm_field.opacity = 0
            self.confirm_field.disabled = True
            self.card.height = dp(340)
        else:
            # Режим регистрации
            self.title_label.text = "Создать аккаунт"
            self.action_btn.text = "Зарегистрироваться"
            self.switch_label.text = "Уже есть аккаунт?"
            self.switch_btn.icon = "arrow-left"
            self.confirm_field.opacity = 1
            self.confirm_field.disabled = False
            self.card.height = dp(400)

        # Очищаем поля
        self.email_field.text = ""
        self.password_field.text = ""
        self.confirm_field.text = ""

        logger.info(f"🔄 Режим: {'Вход' if self._login_mode else 'Регистрация'}")

    def _on_action_press(self, instance):
        """Обработчик нажатия на главную кнопку"""
        email = self.email_field.text.strip()
        password = self.password_field.text

        if not email or not password:
            notify.warning("Заполните все поля")
            return

        if self._login_mode:
            self._do_login(email, password)
        else:
            confirm = self.confirm_field.text
            if password != confirm:
                notify.warning("Пароли не совпадают")
                return
            if len(password) < 4:
                notify.warning("Пароль должен быть не менее 4 символов")
                return
            self._do_register(email, password)

    def _do_login(self, username, password):
        """Выполняет вход"""
        self.action_btn.text = "Вход..."
        self.action_btn.disabled = True

        api.login(
            username=username,
            password=password,
            on_success=self._on_login_success,
            on_failure=self._on_login_failure
        )

    def _on_login_success(self, result):
        """Обработчик успешного входа"""
        self.action_btn.text = "Войти"
        self.action_btn.disabled = False

        # Загружаем данные пользователя
        api.get_current_user(
            on_success=self._on_user_loaded,
            on_failure=lambda req, err: None
        )

        notify.success("Вход выполнен успешно!")
        logger.info("✅ Вход выполнен")

        # Возвращаемся на главный экран
        Clock.schedule_once(self._go_home, 0.3)

    def _on_user_loaded(self, user):
        """Загружены данные пользователя"""
        api.user_data = user
        logger.info(f"👤 Пользователь: {user.get('username', '')}")

    def _on_login_failure(self, req, error):
        """Обработчик ошибки входа"""
        self.action_btn.text = "Войти"
        self.action_btn.disabled = False
        notify.error("Неверное имя пользователя или пароль")
        logger.error(f"❌ Ошибка входа: {error}")

    def _do_register(self, username, password):
        """Выполняет регистрацию"""
        self.action_btn.text = "Регистрация..."
        self.action_btn.disabled = True

        api.register(
            username=username,
            password=password,
            full_name=None,
            on_success=self._on_register_success,
            on_failure=self._on_register_failure
        )

    def _on_register_success(self, result):
        """Обработчик успешной регистрации"""
        self.action_btn.text = "Зарегистрироваться"
        self.action_btn.disabled = False

        notify.success("Регистрация успешна! Теперь войдите.")
        logger.info("✅ Регистрация выполнена")

        # Переключаемся на режим входа
        self._toggle_mode(None)

    def _on_register_failure(self, req, error):
        """Обработчик ошибки регистрации"""
        self.action_btn.text = "Зарегистрироваться"
        self.action_btn.disabled = False
        notify.error("Ошибка регистрации. Возможно, имя уже занято.")
        logger.error(f"❌ Ошибка регистрации: {error}")

    def _go_home(self, dt):
        """Переход на главный экран"""
        if hasattr(self, 'manager') and self.manager:
            # Обновляем состояние Sidebar
            app = MDApp.get_running_app()
            if app and hasattr(app, 'sidebar'):
                app.sidebar.update_user_info()
            self.manager.current = 'home'

    def on_enter(self):
        """При входе на экран"""
        logger.info("🚪 Вход в экран авторизации")

        # Если уже авторизован - сразу переходим на главную
        if api.is_authenticated():
            Clock.schedule_once(self._go_home, 0.1)
            return

        # Обновляем TopNav
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title("Авторизация")
                app.top_nav.back_btn.on_release = self.go_back
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

        # Очищаем поля
        self.email_field.text = ""
        self.password_field.text = ""
        self.confirm_field.text = ""

        # Если в режиме регистрации - переключаем на вход
        if not self._login_mode:
            self._toggle_mode(None)

        Clock.schedule_once(lambda dt: self.email_field.focus, 0.3)

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("🚪 Выход из экрана авторизации")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.reset_to_default()

    def go_back(self, instance=None):
        """Возврат на главный экран"""
        logger.info("🔙 Возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'