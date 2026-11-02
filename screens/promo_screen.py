# screens/promo_screen.py
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from io import BytesIO
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivy.animation import Animation

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


class PromoScreen(BaseScreen):
    """Экран активации промокода"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'promo'
        self.bg_image = None

        self.init_ui()
        self.load_background()
        logger.info('Экран промокода создан')

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

    def init_ui(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        # Иконка и заголовок
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
            height=dp(200),
            padding=[dp(24), dp(24), dp(24), dp(24)],
            radius=[theme.CORNER_RADIUS_MEDIUM] * 4,
            md_bg_color=[0.12, 0.12, 0.12, 0.85],
            elevation=4,
            line_color=[1, 1, 1, 0.1],
            line_width=1,
            spacing=dp(16)
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

    def _activate_promo(self, instance):
        code = self.promo_input.text.strip().upper()
        if not code:
            notify.warning("Введите промокод")
            return

        self.activate_btn.text = "Проверка..."
        self.activate_btn.disabled = True

        def on_success(res):
            self.activate_btn.text = "Активировать"
            self.activate_btn.disabled = False

            # Красивое уведомление об успехе
            notify.success(res.get("message", "Промокод активирован!"))
            self.promo_input.text = ""

            # Обновляем данные пользователя
            api.get_current_user(on_success=lambda u: setattr(api, 'user_data', u))

        def on_failure(req, err):
            self.activate_btn.text = "Активировать"
            self.activate_btn.disabled = False
            notify.error(err)

        api.activate_promo(code, on_success=on_success, on_failure=on_failure)

    def on_enter(self):
        super().on_enter()
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Промокод")
            app.top_nav.back_btn.on_release = self.go_back

    def go_back(self, instance=None):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'