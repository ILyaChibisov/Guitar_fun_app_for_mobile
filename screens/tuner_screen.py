# screens/tuner_screen.py
"""
Экран гитарного тюнера - режим разработки
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from io import BytesIO

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen

logger = screen_logger('Tuner')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class TunerScreen(BaseScreen):
    """Экран гитарного тюнера - режим разработки"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tuner'
        self.bg_image = None

        self.init_ui()
        self.load_background()

        logger.info('Экран тюнера создан (режим разработки)')

    def load_background(self):
        """Загружает фоновое изображение"""
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
        """Инициализирует UI с карточкой под TopNav"""

        # Основной контейнер
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # ============ ВЕРХНИЙ ОТСТУП ============
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # ============ КОНТЕЙНЕР С ОТСТУПАМИ ============
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)

        content_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), total_bottom]
        )

        # ============ КАРТОЧКА ============
        card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(100),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            spacing=dp(8),
            radius=[theme.CORNER_RADIUS_SMALL] * 4,
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.08],
            line_width=0.5,
            pos_hint={'top': 1}
        )

        # Заголовок
        title_label = MDLabel(
            text="Тюнер",
            font_size=sp(20),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95]
        )

        # Сообщение
        message_label = MDLabel(
            text="Модуль находится в разработке",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5]
        )

        card.add_widget(title_label)
        card.add_widget(message_label)

        content_container.add_widget(card)

        # Растягивающийся виджет снизу
        content_container.add_widget(Widget(size_hint_y=1))

        main_layout.add_widget(content_container)

        self.add_widget(main_layout)

        logger.info(f"TunerScreen: top_padding = {top_padding}dp")

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в экран тюнера")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Тюнер")
            app.top_nav._show_back_button()
            app.top_nav.back_btn.on_release = self.go_back

    def go_back(self, instance=None):
        """Возврат на главный экран"""
        logger.info("🔙 go_back: возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из экрана тюнера")
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            app.top_nav.update_title('home')