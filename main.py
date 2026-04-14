# main.py
"""
Главный файл приложения GuitarFuns
С верхней панелью и нижней навигацией
"""
import os
import sys
import ssl
import warnings
import traceback


# ============ ОБРАБОТКА НЕПЕРЕХВАЧЕННЫХ ОШИБОК ============
def handle_exception(exc_type, exc_value, exc_traceback):
    """Глобальный перехватчик ошибок для отладки"""
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("=" * 50)
    print("FATAL ERROR:")
    print(error_msg)
    print("=" * 50)

    try:
        import android
        with open('/sdcard/guitarfuns_crash.log', 'w') as f:
            f.write(error_msg)
    except:
        pass

    if hasattr(sys, '__excepthook__'):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_exception
# =========================================================

# ============ ОТКЛЮЧАЕМ SSL ПРОВЕРКУ ДЛЯ ВСЕХ ПЛАТФОРМ ============
warnings.filterwarnings("ignore", category=Warning)

try:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

os.environ['SSL_CERT_FILE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
# ================================================================

from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.utils import platform
from kivy.core.image import Image as CoreImage
from io import BytesIO

# Настройка логирования
from config.logger_config import setup_logging, app_logger

setup_logging(level='debug')

# Импорты KivyMD с использованием наших утилит
from utils.kivy_imports import (
    MDRaisedButton, MDIconButton, MDFlatButton,
    MDLabel, MDBoxLayout, MDScreen, MDDialog, Snackbar
)

from kivymd.app import MDApp

# Наши модули
from config.app_config import config
from config.theme import theme
from screens.manager import setup_screen_manager
from api.client import api
from api.network_handler import network_manager
from utils.notifications import notify

# Импортируем компонент нижней навигации
from screens.components.bottom_nav import BottomNav

# Импортируем ассеты
try:
    from data import Assets, load_asset_as_bytes, load_asset_as_base64

    HAS_ASSETS = True
    print("✅ Модуль ассетов загружен")
except ImportError as e:
    HAS_ASSETS = False
    print(f"⚠️ Модуль ассетов не найден: {e}")

# Настройка окна для разработки
if os.name == 'nt':
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50

logger = app_logger()


class LanguageSelector(MDBoxLayout):
    """Компонент выбора языка (прозрачный)"""

    def __init__(self, current_lang="ru", on_change_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, 1)
        self.width = dp(100)
        self.spacing = dp(4)
        self.current_lang = current_lang
        self.on_change_callback = on_change_callback

        self.lang_icons = {
            "ru": "language-russian", "en": "alphabet-latin", "de": "alphabet-latin",
            "fr": "alphabet-latin", "it": "alphabet-latin", "pt": "alphabet-latin", "zh": "alphabet-chinese"
        }

        self.lang_codes = {
            "ru": "RU", "en": "EN", "de": "DE", "fr": "FR", "it": "IT", "pt": "PT", "zh": "中文"
        }

        self.button_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            radius=[dp(8), dp(8), dp(8), dp(8)],
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        self.current_icon = MDIconButton()
        self.current_icon.icon = self.lang_icons.get(current_lang, "translate")
        self.current_icon.theme_text_color = "Custom"
        self.current_icon.text_color = [1, 1, 1, 1]
        self.current_icon.size_hint = (None, 1)
        self.current_icon.width = dp(28)
        self.current_icon.md_bg_color = [0, 0, 0, 0]

        self.current_code = MDLabel(
            text=self.lang_codes[current_lang],
            font_size=sp(11),
            size_hint=(None, 1),
            width=dp(36),
            halign="center",
            valign="middle",
            bold=True,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )

        self.arrow = MDIconButton()
        self.arrow.icon = "chevron-down"
        self.arrow.theme_text_color = "Custom"
        self.arrow.text_color = [1, 1, 1, 1]
        self.arrow.size_hint = (None, 1)
        self.arrow.width = dp(24)
        self.arrow.md_bg_color = [0, 0, 0, 0]

        self.button_container.add_widget(self.current_icon)
        self.button_container.add_widget(self.current_code)
        self.button_container.add_widget(self.arrow)
        self.add_widget(self.button_container)
        self.button_container.bind(on_touch_down=self.on_click)
        self.create_language_menu()

    def create_language_menu(self):
        from kivymd.uix.menu import MDDropdownMenu
        languages = [
            {"code": "ru", "name": "Русский", "icon": "language-russian"},
            {"code": "en", "name": "English", "icon": "alphabet-latin"},
            {"code": "de", "name": "Deutsch", "icon": "alphabet-latin"},
            {"code": "fr", "name": "Français", "icon": "alphabet-latin"},
            {"code": "it", "name": "Italiano", "icon": "alphabet-latin"},
            {"code": "pt", "name": "Português", "icon": "alphabet-latin"},
            {"code": "zh", "name": "中文", "icon": "alphabet-chinese"}
        ]
        menu_items = []
        for lang in languages:
            is_current = (lang["code"] == self.current_lang)
            menu_items.append({
                "text": lang["name"], "viewclass": "OneLineListItem",
                "on_release": lambda x=lang["code"]: self.change_language(x),
                "theme_text_color": "Primary" if is_current else "Secondary",
                "left_icon": lang["icon"]
            })
        self.language_menu = MDDropdownMenu(
            caller=self.button_container, items=menu_items, width=dp(180),
            max_height=dp(400), position="bottom", radius=[theme.CORNER_RADIUS_SMALL]
        )

    def on_click(self, instance, touch):
        if self.button_container.collide_point(*touch.pos):
            self.open_language_menu()
            return True
        return False

    def open_language_menu(self):
        self.language_menu.open()

    def change_language(self, lang_code):
        self.current_lang = lang_code
        self.current_icon.icon = self.lang_icons.get(lang_code, "translate")
        self.current_code.text = self.lang_codes.get(lang_code, lang_code.upper())
        self.language_menu.dismiss()
        if self.on_change_callback:
            self.on_change_callback(lang_code)


class GuitarFunsApp(MDApp):
    """Главный класс приложения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "GuitarFuns"
        self.current_language = "ru"
        self.profile_dialog = None
        self.auth_dialog = None
        self.settings_dialog = None
        self.support_dialog = None
        self.language_selector = None
        self.screen_manager = None
        self.home_screen = None
        self.bottom_nav = None

        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК GuitarFuns v{config.VERSION}')
        logger.info(f'🎸 Платформа: {platform}')
        logger.info('🎸 ' + '=' * 50)

    def build(self):
        logger.debug('Создание интерфейса...')

        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "300"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.material_style = "M3"

        # Создаём менеджер экранов
        self.screen_manager = setup_screen_manager()
        self.screen_manager.current = 'home'

        # Корневой контейнер
        root = MDBoxLayout(orientation='vertical')

        # Верхняя панель
        top_bar = self.create_top_bar()
        root.add_widget(top_bar)

        # Менеджер экранов
        root.add_widget(self.screen_manager)

        # Нижняя навигация (используем компонент из screens/components)
        self.bottom_nav = BottomNav(self.screen_manager)
        root.add_widget(self.bottom_nav)

        # Запускаем мониторинг сети
        network_manager.start_monitoring()

        logger.info('Интерфейс успешно создан')
        return root

    def create_top_bar(self):
        """Создаёт прозрачную верхнюю панель с белыми иконками"""
        top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            padding=[theme.PADDING, 0, theme.PADDING, 0],
            spacing=theme.PADDING,
            md_bg_color=[0, 0, 0, 0]
        )

        # Логотип (белый)
        logo = MDLabel(
            text="GuitarFuns",
            font_size=dp(20),
            size_hint_x=0.4,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        # Контейнер для иконок
        icons_container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=0.6,
            spacing=dp(8)
        )

        # Иконка профиля
        profile_btn = MDIconButton()
        profile_btn.icon = "account-circle"
        profile_btn.theme_text_color = "Custom"
        profile_btn.text_color = [1, 1, 1, 1]
        profile_btn.md_bg_color = [0, 0, 0, 0]
        profile_btn.on_release = self.open_profile

        # Иконка настроек
        settings_btn = MDIconButton()
        settings_btn.icon = "cog"
        settings_btn.theme_text_color = "Custom"
        settings_btn.text_color = [1, 1, 1, 1]
        settings_btn.md_bg_color = [0, 0, 0, 0]
        settings_btn.on_release = self.open_settings

        # Иконка поддержки
        support_btn = MDIconButton()
        support_btn.icon = "help-circle"
        support_btn.theme_text_color = "Custom"
        support_btn.text_color = [1, 1, 1, 1]
        support_btn.md_bg_color = [0, 0, 0, 0]
        support_btn.on_release = self.open_support

        # LanguageSelector с прозрачным фоном и белыми элементами
        self.language_selector = LanguageSelector(
            current_lang="ru",
            on_change_callback=self.change_language
        )
        self.language_selector.button_container.md_bg_color = [0, 0, 0, 0]
        self.language_selector.current_icon.text_color = [1, 1, 1, 1]
        self.language_selector.current_code.text_color = [1, 1, 1, 1]
        self.language_selector.arrow.text_color = [1, 1, 1, 1]
        self.language_selector.current_icon.md_bg_color = [0, 0, 0, 0]
        self.language_selector.arrow.md_bg_color = [0, 0, 0, 0]

        icons_container.add_widget(profile_btn)
        icons_container.add_widget(settings_btn)
        icons_container.add_widget(support_btn)
        icons_container.add_widget(self.language_selector)

        top_bar.add_widget(logo)
        top_bar.add_widget(icons_container)
        return top_bar

    def open_profile(self, instance):
        logger.info("Нажата иконка личного кабинета")
        if api.is_authenticated():
            self.screen_manager.current = "profile"
        else:
            if self.home_screen and hasattr(self.home_screen, 'open_profile'):
                self.home_screen.open_profile()
            else:
                logger.warning("HomeScreen не найден")

    def open_settings(self, instance):
        logger.info("Открыты настройки")
        if not self.settings_dialog:
            self.settings_dialog = MDDialog(
                title="⚙️ Настройки",
                text="Здесь будут настройки приложения",
                buttons=[MDFlatButton(text="ЗАКРЫТЬ", on_release=lambda x: self.settings_dialog.dismiss())]
            )
        self.settings_dialog.open()

    def open_support(self, instance):
        logger.info("Открыта поддержка")
        if not self.support_dialog:
            self.support_dialog = MDDialog(
                title="🆘 Поддержка",
                text="Свяжитесь с нами:\n\n📧 Email: support@guitarfuns.com\n\n📱 Telegram: @guitarfuns_bot",
                buttons=[MDFlatButton(text="ЗАКРЫТЬ", on_release=lambda x: self.support_dialog.dismiss())]
            )
        self.support_dialog.open()

    def change_language(self, lang_code):
        self.current_language = lang_code
        lang_names = {"ru": "Русский", "en": "English", "de": "Deutsch",
                      "fr": "Français", "it": "Italiano", "pt": "Português", "zh": "中文"}
        lang_name = lang_names.get(lang_code, lang_code)
        logger.info(f"Язык изменён на: {lang_name} ({lang_code})")
        notify.info(f"Язык изменён на {lang_name}")

    def show_auth_modal(self, on_success=None):
        from screens.home_screen import AuthModal
        if self.home_screen and not self.home_screen.auth_modal:
            self.home_screen.auth_modal = AuthModal(
                parent_screen=self.home_screen,
                on_close=lambda: setattr(self.home_screen, 'auth_modal', None),
                on_login_success=on_success
            )
            self.home_screen.add_widget(self.home_screen.auth_modal)

    def switch_screen(self, screen_name):
        if self.screen_manager and self.screen_manager.current != screen_name:
            self.screen_manager.current = screen_name
            logger.info(f"Переключение на экран: {screen_name}")

    def on_start(self):
        logger.info('Приложение GuitarFuns запущено')

        # Проверяем наличие ассетов
        if HAS_ASSETS:
            assets_list = Assets.list_assets()
            logger.info(f'📦 Загружено ассетов: {len(assets_list)}')
            for asset_name in assets_list:
                meta = Assets.get_metadata(asset_name)
                logger.debug(f'   🖼️  {asset_name}: {meta["original"]} ({meta["size"]} bytes)')
        else:
            logger.warning('Модуль assets.py не найден, используем файловую систему')

        if self.screen_manager:
            self.home_screen = self.screen_manager.get_screen('home')
            logger.info("Ссылка на home_screen сохранена")

    def on_pause(self):
        logger.debug('Приложение свернуто')
        return True

    def on_resume(self):
        logger.debug('Приложение восстановлено')

    def on_stop(self):
        logger.info('Приложение закрыто')
        network_manager.stop_monitoring()


if __name__ == '__main__':
    GuitarFunsApp().run()