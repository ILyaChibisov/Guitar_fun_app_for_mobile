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

    # Попытка записать ошибку в файл (на Android)
    try:
        import android
        with open('/sdcard/guitarfuns_crash.log', 'w') as f:
            f.write(error_msg)
    except:
        pass

    # Вызываем стандартный обработчик
    if hasattr(sys, '__excepthook__'):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = handle_exception
# =========================================================

# ============ ОТКЛЮЧАЕМ SSL ПРОВЕРКУ ДЛЯ ВСЕХ ПЛАТФОРМ ============
# Отключаем предупреждения SSL
warnings.filterwarnings("ignore", category=Warning)

# Для urllib3
try:
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

# Для requests
try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass

# Отключаем проверку SSL глобально
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

# Для Kivy UrlRequest
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

# Настройка логирования
from config.logger_config import setup_logging, app_logger

setup_logging(level='debug')

# Импорты KivyMD с использованием наших утилит
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog

# Наши модули
from config.app_config import config
from config.theme import theme
from screens.manager import setup_screen_manager
from api.client import api
from api.network_handler import network_manager
from utils.notifications import notify

# Настройка окна для разработки
if os.name == 'nt':
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50

logger = app_logger()


class BottomNavItem(BoxLayout):
    """Элемент нижней навигации с иконкой и текстом"""

    def __init__(self, icon, text, screen_name, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.spacing = dp(2)
        self.screen_name = screen_name

        # Иконка
        self.icon_btn = MDIconButton(
            size_hint=(1, 0.6)
        )
        self.icon_btn.icon = icon
        self.icon_btn.icon_color = theme.TEXT_SECONDARY
        self.icon_btn.theme_icon_color = "Custom"

        # Универсальный маленький шрифт
        self.text_label = MDLabel(
            text=text,
            font_size=sp(8),
            size_hint=(1, 0.4),
            halign="center",
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            bold=False
        )

        self.add_widget(self.icon_btn)
        self.add_widget(self.text_label)

    def set_active(self, active):
        if active:
            self.icon_btn.icon_color = theme.PRIMARY
            self.text_label.text_color = theme.PRIMARY
            self.text_label.bold = True
        else:
            self.icon_btn.icon_color = theme.TEXT_SECONDARY
            self.text_label.text_color = theme.TEXT_SECONDARY
            self.text_label.bold = False


class LanguageSelector(MDBoxLayout):
    """Компонент выбора языка"""

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
            orientation='horizontal', size_hint=(1, 1), spacing=dp(4),
            md_bg_color=theme.PRIMARY_LIGHT, radius=[dp(8), dp(8), dp(8), dp(8)],
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        self.current_icon = MDIconButton(
            size_hint=(None, 1), width=dp(28)
        )
        self.current_icon.icon = self.lang_icons.get(current_lang, "translate")
        self.current_icon.icon_color = [1, 1, 1, 1]
        self.current_icon.theme_icon_color = "Custom"

        self.current_code = MDLabel(
            text=self.lang_codes[current_lang], font_size=sp(11),
            size_hint=(None, 1), width=dp(36), halign="center", valign="middle",
            bold=True, theme_text_color="Custom", text_color=[1, 1, 1, 1]
        )

        self.arrow = MDIconButton(
            size_hint=(None, 1), width=dp(24)
        )
        self.arrow.icon = "chevron-down"
        self.arrow.icon_color = [1, 1, 1, 1]
        self.arrow.theme_icon_color = "Custom"

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
        self.nav_items = []

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
        self.screen_manager.bind(current=self.on_screen_change)

        # Устанавливаем начальный экран
        self.screen_manager.current = 'home'

        # Корневой контейнер
        root = MDBoxLayout(orientation='vertical')

        # Верхняя панель
        top_bar = self.create_top_bar()
        root.add_widget(top_bar)

        # Менеджер экранов
        root.add_widget(self.screen_manager)

        # Нижняя навигация
        bottom_nav = self.create_bottom_navigation()
        root.add_widget(bottom_nav)

        # Запускаем мониторинг сети
        network_manager.start_monitoring()

        logger.info('Интерфейс успешно создан')
        return root

    def create_top_bar(self):
        top_bar = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(60),
            padding=[theme.PADDING, 0, theme.PADDING, 0], spacing=theme.PADDING,
            md_bg_color=theme.PRIMARY
        )

        # Исправлено: убран font_style="H6", добавлен font_size
        logo = MDLabel(
            text="GuitarFuns", font_size=sp(18), size_hint_x=0.4,
            theme_text_color="Custom", text_color=[1, 1, 1, 1], bold=True
        )

        icons_container = MDBoxLayout(orientation='horizontal', size_hint_x=0.6, spacing=dp(8))

        profile_btn = MDIconButton(
            on_release=self.open_profile
        )
        profile_btn.icon = "account-circle"
        profile_btn.icon_color = [1, 1, 1, 1]
        profile_btn.theme_icon_color = "Custom"

        settings_btn = MDIconButton(
            on_release=self.open_settings
        )
        settings_btn.icon = "cog"
        settings_btn.icon_color = [1, 1, 1, 1]
        settings_btn.theme_icon_color = "Custom"

        support_btn = MDIconButton(
            on_release=self.open_support
        )
        support_btn.icon = "help-circle"
        support_btn.icon_color = [1, 1, 1, 1]
        support_btn.theme_icon_color = "Custom"

        self.language_selector = LanguageSelector(
            current_lang="ru", on_change_callback=self.change_language
        )

        icons_container.add_widget(profile_btn)
        icons_container.add_widget(settings_btn)
        icons_container.add_widget(support_btn)
        icons_container.add_widget(self.language_selector)

        top_bar.add_widget(logo)
        top_bar.add_widget(icons_container)
        return top_bar

    def create_bottom_navigation(self):
        """Создаёт нижнюю навигацию с иконками"""

        bottom_nav = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(60),
            padding=[theme.PADDING, dp(4), theme.PADDING, dp(4)],
            spacing=dp(4),
            md_bg_color=theme.SURFACE
        )

        # Добавляем тень сверху
        from kivy.graphics import Color, Rectangle
        with bottom_nav.canvas.before:
            Color(0, 0, 0, 0.05)
            bottom_nav.shadow = Rectangle(pos=(bottom_nav.x, bottom_nav.y + bottom_nav.height - dp(1)),
                                          size=(bottom_nav.width, dp(1)))

        def update_shadow(instance, value):
            if hasattr(bottom_nav, 'shadow'):
                bottom_nav.shadow.pos = (bottom_nav.x, bottom_nav.y + bottom_nav.height - dp(1))
                bottom_nav.shadow.size = (bottom_nav.width, dp(1))

        bottom_nav.bind(pos=update_shadow, size=update_shadow)

        # Элементы навигации
        nav_items = [
            {"icon": "home", "text": "Главная", "screen": "home"},
            {"icon": "music-note", "text": "Песни", "screen": "songs"},
            {"icon": "guitar-acoustic", "text": "Аккорды", "screen": "chords"},
            {"icon": "book", "text": "Словарь", "screen": "dictionary"},
            {"icon": "tune", "text": "Тюнер", "screen": "tuner"},
            {"icon": "heart", "text": "Избранное", "screen": "favorites"}
        ]

        for item in nav_items:
            nav_item = BottomNavItem(
                icon=item["icon"],
                text=item["text"],
                screen_name=item["screen"]
            )
            nav_item.icon_btn.bind(on_release=lambda x, s=item["screen"]: self.on_nav_press(s))
            bottom_nav.add_widget(nav_item)
            self.nav_items.append(nav_item)

        # Устанавливаем активный элемент по умолчанию
        if self.nav_items:
            self.nav_items[0].set_active(True)

        return bottom_nav

    def on_nav_press(self, screen_name):
        """Обработчик нажатия на элемент навигации"""
        if self.screen_manager and self.screen_manager.current != screen_name:
            self.screen_manager.current = screen_name

    def on_screen_change(self, instance, value):
        """Обновляет активные элементы при смене экрана"""
        for item in self.nav_items:
            item.set_active(item.screen_name == value)

    def open_profile(self, instance):
        """Открывает профиль пользователя"""
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
            close_btn = MDButton(
                text="ЗАКРЫТЬ",
                theme_text_color="Custom",
                text_color=theme.TEXT_SECONDARY,
                on_release=lambda x: self.settings_dialog.dismiss(),
                style="text"
            )
            self.settings_dialog = MDDialog(
                title="⚙️ Настройки",
                text="Здесь будут настройки приложения",
                buttons=[close_btn]
            )
        self.settings_dialog.open()

    def open_support(self, instance):
        logger.info("Открыта поддержка")
        if not self.support_dialog:
            close_btn = MDButton(
                text="ЗАКРЫТЬ",
                theme_text_color="Custom",
                text_color=theme.TEXT_SECONDARY,
                on_release=lambda x: self.support_dialog.dismiss(),
                style="text"
            )
            self.support_dialog = MDDialog(
                title="🆘 Поддержка",
                text="Свяжитесь с нами:\n\n📧 Email: support@guitarfuns.com\n\n📱 Telegram: @guitarfuns_bot",
                buttons=[close_btn]
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
        """Показывает модальное окно авторизации"""
        from screens.home_screen import AuthModal

        if self.home_screen and not self.home_screen.auth_modal:
            self.home_screen.auth_modal = AuthModal(
                parent_screen=self.home_screen,
                on_close=lambda: setattr(self.home_screen, 'auth_modal', None),
                on_login_success=on_success
            )
            self.home_screen.add_widget(self.home_screen.auth_modal)

    def switch_screen(self, screen_name):
        """Переключает экран (для вызова из других модулей)"""
        if self.screen_manager and self.screen_manager.current != screen_name:
            self.screen_manager.current = screen_name
            logger.info(f"Переключение на экран: {screen_name}")

    def on_start(self):
        logger.info('Приложение GuitarFuns запущено')
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