# screens/settings_screen.py
"""Экран настроек (заглушка)"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from io import BytesIO

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen

logger = screen_logger('Settings')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class SettingsScreen(BaseScreen):
    """Экран настроек"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        self.bg_image = None

        self.init_ui()
        self.load_background()
        logger.info('Экран настроек создан')

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

        # Заголовок
        title = MDLabel(
            text="⚙️ Настройки",
            font_size=sp(24),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )
        content.add_widget(title)

        # Карточка с сообщением
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            radius=[theme.CORNER_RADIUS_SMALL] * 4,
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.15],
            line_width=0.5
        )

        icon_label = MDLabel(
            text="🔧",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(56),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        text_label = MDLabel(
            text="Настройки приложения\nбудут доступны в следующей версии",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            line_height=1.4
        )

        info_card.add_widget(icon_label)
        info_card.add_widget(text_label)
        content.add_widget(info_card)

        # Растяжка
        content.add_widget(Widget(size_hint_y=1))

        self.build_ui(content_widget=content, use_scroll=True)

    def on_enter(self):
        """При входе на экран"""
        logger.info("🚪 Вход в экран настроек")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Настройки")
            app.top_nav.back_btn.on_release = self.go_back

    def go_back(self, instance=None):
        """Возврат на главный экран"""
        logger.info("🔙 Возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'