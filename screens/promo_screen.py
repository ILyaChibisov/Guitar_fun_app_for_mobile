# screens/promo_screen.py
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.animation import Animation
from io import BytesIO

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('Promo')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


# Цвета inline-статуса
COLOR_SUCCESS = [0.20, 0.75, 0.35, 1.0]
COLOR_ERROR = [0.90, 0.30, 0.30, 1.0]
COLOR_INFO = [0.46, 0.70, 0.71, 1.0]


class PromoScreen(BaseScreen):
    """Экран активации промокода"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'promo'
        self.bg_image = None
        self._status_hide_event = None

        self.init_ui()
        self.load_background()
        logger.info('Экран промокода создан')

    # ============ ФОН ============

    def load_background(self):
        try:
            if HAS_ASSETS:
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
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

    # ============ UI ============

    def init_ui(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        # Заголовок
        title = MDLabel(
            text="🎫 Активация промокода",
            font_size=sp(22),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )
        content.add_widget(title)

        subtitle = MDLabel(
            text="Введите код, чтобы получить дополнительные дни подписки",
            font_size=sp(13),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[0.7, 0.7, 0.7, 1]
        )
        content.add_widget(subtitle)

        # Карточка
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(230),  # +30 под inline-статус
            padding=[dp(24), dp(24), dp(24), dp(24)],
            radius=[theme.CORNER_RADIUS_MEDIUM] * 4,
            md_bg_color=[0.12, 0.12, 0.12, 0.85],
            elevation=4,
            line_color=[1, 1, 1, 0.1],
            line_width=1,
            spacing=dp(12)
        )

        self.promo_input = MDTextField(
            hint_text="Например: GUITAR20",
            mode="fill",
            size_hint_y=None,
            height=dp(56),
            font_size=sp(18),
            halign="center",
            fill_color_normal=[0, 0, 0, 0.2],
            fill_color_focus=[0, 0, 0, 0.3],
            text_color_normal=[1, 1, 1, 1]
        )
        info_card.add_widget(self.promo_input)

        # ---- INLINE-СТАТУС ----
        self.status_label = MDLabel(
            text="",
            font_size=sp(13),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(26),
            theme_text_color="Custom",
            text_color=COLOR_INFO,
            opacity=0,
        )
        info_card.add_widget(self.status_label)

        self.activate_btn = MDRaisedButton(
            text="Активировать",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=theme.PRIMARY,
            text_color=[1, 1, 1, 1],
            font_size=sp(16),
            on_release=self._activate_promo
        )
        info_card.add_widget(self.activate_btn)

        content.add_widget(info_card)
        content.add_widget(Widget(size_hint_y=1))

        self.build_ui(content_widget=content, use_scroll=True)

    # ============ INLINE-СТАТУС ============

    def _show_status(self, text: str, color, auto_hide: float = 0.0):
        """Показывает inline-сообщение под полем."""
        if self._status_hide_event:
            self._status_hide_event.cancel()
            self._status_hide_event = None

        self.status_label.text = text
        self.status_label.text_color = color
        Animation(opacity=1, duration=0.15).start(self.status_label)

        if auto_hide > 0:
            self._status_hide_event = Clock.schedule_once(
                lambda dt: Animation(opacity=0, duration=0.3).start(self.status_label),
                auto_hide,
            )

    def _clear_status(self):
        if self._status_hide_event:
            self._status_hide_event.cancel()
            self._status_hide_event = None
        self.status_label.text = ""
        self.status_label.opacity = 0

    # ============ АКТИВАЦИЯ ============

    def _activate_promo(self, instance):
        code = self.promo_input.text.strip().upper()
        if not code:
            self._show_status("Введите промокод", COLOR_ERROR, auto_hide=3.0)
            return

        self._clear_status()
        self.activate_btn.text = "Проверка..."
        self.activate_btn.disabled = True
        self.promo_input.disabled = True

        def on_success(res):
            self.activate_btn.text = "Активировать"
            self.activate_btn.disabled = False
            self.promo_input.disabled = False

            days = res.get("days_added") if isinstance(res, dict) else None
            msg = (res.get("message") if isinstance(res, dict) else None) \
                  or "Промокод активирован!"

            if days:
                self._show_status(f"✅ {msg} (+{days} дн.)", COLOR_SUCCESS, auto_hide=6.0)
            else:
                self._show_status(f"✅ {msg}", COLOR_SUCCESS, auto_hide=6.0)

            notify.success(msg)
            self.promo_input.text = ""

            # Обновляем данные пользователя и подписку
            self._refresh_user_and_subscription()

        def on_failure(req, err):
            self.activate_btn.text = "Активировать"
            self.activate_btn.disabled = False
            self.promo_input.disabled = False

            err_text = str(err) if err else "Не удалось активировать промокод"
            self._show_status(f"❌ {err_text}", COLOR_ERROR, auto_hide=5.0)
            notify.error(err_text)

        api.activate_promo(code, on_success=on_success, on_failure=on_failure)

    # ============ ОБНОВЛЕНИЕ ПОДПИСКИ ПОСЛЕ АКТИВАЦИИ ============

    def _refresh_user_and_subscription(self):
        """
        После успешной активации:
        - перезагружаем user_data;
        - запрашиваем статус подписки;
        - показываем плашку на home, если она есть.
        """
        def _on_user(user):
            api.user_data = user
            self._check_and_show_subscription()

        api.get_current_user(on_success=_on_user)

    def _check_and_show_subscription(self):
        def _on_status(status_data):
            # Обновляем плашку на HomeScreen, если он есть в памяти
            try:
                app = MDApp.get_running_app()
                if app and app.screen_manager and app.screen_manager.has_screen('home'):
                    home = app.screen_manager.get_screen('home')
                    if hasattr(home, 'show_subscription_status'):
                        home.show_subscription_status(status_data)
            except Exception as e:
                logger.debug(f"Не удалось обновить плашку подписки: {e}")

            # Также обновляем надпись подписки в профиле (если открыт)
            try:
                app = MDApp.get_running_app()
                if app and app.screen_manager and app.screen_manager.has_screen('profile'):
                    profile = app.screen_manager.get_screen('profile')
                    if hasattr(profile, 'update_ui') and getattr(profile, 'user', None):
                        profile.update_ui()
            except Exception as e:
                logger.debug(f"Не удалось обновить профиль: {e}")

        api.check_subscription(
            on_success=_on_status,
            on_failure=lambda req, err: logger.warning(f"check_subscription: {err}")
        )

    # ============ ЖИЗНЕННЫЙ ЦИКЛ ============

    def on_enter(self):
        super().on_enter()

        self._clear_status()

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Промокод")
            app.top_nav.back_btn.on_release = self.go_back

        # Фокус на поле через мгновение
        Clock.schedule_once(lambda dt: setattr(self.promo_input, 'focus', True), 0.3)

    def on_leave(self):
        self._clear_status()
        # Возвращаем кнопку «назад» в исходное состояние (её могли переопределить)
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            try:
                app.top_nav.reset_to_default()
            except Exception:
                pass
        super().on_leave()

    def go_back(self, instance=None):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'