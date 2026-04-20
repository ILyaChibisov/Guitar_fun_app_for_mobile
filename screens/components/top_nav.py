# screens/components/top_nav.py
"""
Верхняя панель навигации с плавающими иконками и выбором языка
"""
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.metrics import dp, sp
from kivy.core.image import Image as CoreImage
from io import BytesIO

from config.theme import theme
from config.top_nav_config import TopNavConfig
from config.logger_config import get_logger
from screens.components.language_selector import LanguageSelector
from utils.kivy_imports import MDBoxLayout

logger = get_logger('UI')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


    logger.warning("Модуль data не найден")


class TopIcon(ButtonBehavior, MDBoxLayout):
    """Иконка верхней панели"""

    def __init__(self, icon_asset, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.icon_asset = icon_asset
        self.on_press_callback = on_press_callback

        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = TopNavConfig.ICON_SIZE
        self.spacing = 0
        self.padding = 0

        self.icon_container = MDBoxLayout(size_hint=(1, 1), orientation='vertical')
        self.custom_image = None
        self._load_icon()

        self.add_widget(self.icon_container)
        self.bind(on_release=self._on_press)

    def _load_icon(self):
        """Загружает иконку"""
        self.icon_container.clear_widgets()

        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    core_img = CoreImage(BytesIO(icon_data), ext="png")
                    self.custom_image = Image(
                        texture=core_img.texture,
                        size_hint=(0.75, 0.75),
                        pos_hint={'center_x': 0.5, 'center_y': 0.5},
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    self.icon_container.add_widget(self.custom_image)
                    return
            except Exception as e:
                logger.error(f'Ошибка загрузки иконки: {e}')

        # Заглушка
        self.custom_image = Label(
            text="?",
            font_size=sp(18),
            size_hint=(1, 1),
            color=theme.TEXT_SECONDARY,
            halign='center',
            valign='center'
        )
        self.icon_container.add_widget(self.custom_image)

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(instance)


class TopNav(FloatLayout):
    """Верхняя панель навигации"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.size_hint = (1, 1)

        self.icons = []
        self.app = None
        self.language_selector = None

        self._create_icons()

    def set_app(self, app):
        """Устанавливает ссылку на главное приложение"""
        self.app = app

    # В top_nav.py, в _create_icons():
    def _create_icons(self):
        # Иконка пользователя (слева)
        user_icon = TopIcon(
            icon_asset='profile_png',
            on_press_callback=self._on_user_press
        )
        user_icon.pos_hint = {'x': 0.02, 'top': 0.96}
        self.add_widget(user_icon)

        # Иконка поддержки (справа)
        support_icon = TopIcon(
            icon_asset='support_png',
            on_press_callback=self._on_support_press
        )
        support_icon.pos_hint = {'right': 0.18, 'top': 0.96}
        self.add_widget(support_icon)

        # LanguageSelector
        self.language_selector = LanguageSelector(
            on_language_change=self._on_language_changed
        )
        self.language_selector.pos_hint = {'right': 0.97, 'top': 0.96}
        self.add_widget(self.language_selector)

    def _on_user_press(self, instance):
        """Обработчик нажатия на пользователя"""
        if self.app and hasattr(self.app, 'open_profile'):
            self.app.open_profile(instance)

    def _on_support_press(self, instance):
        """Обработчик нажатия на поддержку"""
        if self.app and hasattr(self.app, 'open_support'):
            self.app.open_support(instance)

    def _on_language_changed(self, lang_code):
        """Обработчик смены языка"""
        if self.app and hasattr(self.app, 'change_language'):
            self.app.change_language(lang_code)

    def get_current_language(self):
        """Возвращает текущий язык"""
        if self.language_selector:
            return self.language_selector.get_current_lang()
        return 'ru'

    def set_current_language(self, lang_code):
        """Устанавливает текущий язык программно"""
        if self.language_selector:
            self.language_selector.set_current_lang(lang_code)

    def update_icon_sizes(self, size):
        """Обновляет размер всех иконок"""
        for icon in self.icons:
            icon.size = size