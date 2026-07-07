# screens/promo_screen.py
"""Экран промокода (заглушка)"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from io import BytesIO

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
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
    """Экран промокода"""

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
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        title = MDLabel(
            text="🎫 Промокод",
            font_size=sp(24),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )
        content.add_widget(title)

        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(200),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            radius=[theme.CORNER_RADIUS_SMALL] * 4,
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.15],
            line_width=0.5,
            spacing=dp(12)
        )

        icon_label = MDLabel(
            text="🏷️",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(56),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )
        info_card.add_widget(icon_label)

        # Поле для ввода промокода
        self.promo_input = MDTextField(
            hint_text="Введите промокод",
            mode="fill",
            size_hint_y=None,
            height=dp(56),
            font_size=sp(14)
        )
        info_card.add_widget(self.promo_input)

        # Кнопка активации
        activate_btn = MDRaisedButton(
            text="Активировать",
            size_hint=(1, None),
            height=dp(44),
            on_release=self._activate_promo
        )
        info_card.add_widget(activate_btn)

        content.add_widget(info_card)

        content.add_widget(Widget(size_hint_y=1))

        self.build_ui(content_widget=content, use_scroll=True)

    def _activate_promo(self, instance):
        """Обработчик активации промокода"""
        code = self.promo_input.text.strip()
        if not code:
            notify.warning("Введите промокод")
            return
        notify.info("Функция активации промокодов будет доступна в следующей версии")

    def on_enter(self):
        logger.info("🚪 Вход в экран промокода")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Промокод")
            app.top_nav.back_btn.on_release = self.go_back

    def go_back(self, instance=None):
        logger.info("🔙 Возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'