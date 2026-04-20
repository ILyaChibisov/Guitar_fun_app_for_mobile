# main.py
"""
Главный файл приложения GuitarFuns
"""
import os
import sys
import ssl
import warnings
import traceback
from kivy.core.window import Window
from kivy.utils import platform
from screens.components.top_nav import TopNav
from config.top_nav_config import TopNavConfig

# ============ ОБРАБОТКА НЕПЕРЕХВАЧЕННЫХ ОШИБОК ============
def handle_exception(exc_type, exc_value, exc_traceback):
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

# ============ ОТКЛЮЧАЕМ SSL ПРОВЕРКУ ============
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
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.utils import platform
from kivy.core.image import Image as CoreImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle  # ← ДОБАВЛЕН ИМПОРТ
from io import BytesIO

# Настройка окна
if platform == 'win':
    Window.borderless = False
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50
    Window.clearcolor = (0, 0, 0, 0)  # Прозрачный фон окна
else:
    Window.clearcolor = (0, 0, 0, 0)  # Прозрачный фон окна
    try:
        from android import mActivity
        from jnius import autoclass

        View = autoclass('android.view.View')
        decorView = mActivity.getWindow().getDecorView()
        decorView.setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        )
    except:
        pass

from config.logger_config import setup_logging, app_logger

setup_logging(level='debug')

from utils.kivy_imports import (
    MDRaisedButton, MDIconButton, MDFlatButton,
    MDLabel, MDBoxLayout, MDDialog
)
from kivymd.app import MDApp

from config.app_config import config
from config.theme import theme
from screens.manager import setup_screen_manager
from api.client import api
from api.network_handler import network_manager
from utils.notifications import notify
from screens.components.bottom_nav import BottomNav

# Импортируем ассеты
try:
    from data import Assets, load_asset_as_bytes

    HAS_ASSETS = True
    print("✅ Модуль ассетов загружен")
except ImportError as e:
    HAS_ASSETS = False
    print(f"⚠️ Модуль ассетов не найден: {e}")

logger = app_logger()


class AnimatedImageButton(ButtonBehavior, Image):
    """Анимированная кнопка-иконка из ассета"""

    def __init__(self, normal_icon_data, pressed_scale=0.9, **kwargs):
        super().__init__(**kwargs)
        self.normal_icon_data = normal_icon_data
        self.pressed_scale = pressed_scale
        self.original_size = self.size
        self._update_texture()

    def _update_texture(self):
        if self.normal_icon_data:
            core_img = CoreImage(BytesIO(self.normal_icon_data), ext="png")
            self.texture = core_img.texture
            self.texture_size = self.texture.size

    def on_press(self):
        if self.original_size[0] > 0:
            anim = Animation(size_hint=(None, None),
                             size=(self.original_size[0] * self.pressed_scale,
                                   self.original_size[1] * self.pressed_scale),
                             duration=0.05)
            anim += Animation(size=self.original_size, duration=0.1)
            anim.start(self)

    def on_release(self):
        pass


class LanguageSelector(MDBoxLayout):
    """Компонент выбора языка"""

    def __init__(self, current_lang="ru", on_change_callback=None, icon_data=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (dp(80), dp(32))
        self.spacing = dp(2)
        self.current_lang = current_lang
        self.on_change_callback = on_change_callback

        self.lang_codes = {
            "ru": "RU", "en": "EN", "de": "DE", "fr": "FR", "it": "IT", "pt": "PT", "zh": "中文"
        }

        self.button_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            spacing=dp(2),
            md_bg_color=[0, 0, 0, 0.5],
            radius=[dp(8), dp(8), dp(8), dp(8)],
            padding=[dp(6), dp(2), dp(6), dp(2)]
        )

        if icon_data:
            core_img = CoreImage(BytesIO(icon_data), ext="png")
            texture = core_img.texture
            self.current_icon = Image(
                texture=texture,
                size_hint=(None, 1),
                width=dp(20),
                allow_stretch=True,
                keep_ratio=True
            )
        else:
            self.current_icon = MDIconButton()
            self.current_icon.icon = "translate"
            self.current_icon.theme_text_color = "Custom"
            self.current_icon.text_color = [1, 1, 1, 1]
            self.current_icon.size_hint = (None, 1)
            self.current_icon.width = dp(20)
            self.current_icon.md_bg_color = [0, 0, 0, 0]

        self.current_code = MDLabel(
            text=self.lang_codes[current_lang],
            font_size=sp(9),
            size_hint=(None, 1),
            width=dp(30),
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
        self.arrow.width = dp(20)
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
            {"code": "ru", "name": "Русский"},
            {"code": "en", "name": "English"},
            {"code": "de", "name": "Deutsch"},
            {"code": "fr", "name": "Français"},
            {"code": "it", "name": "Italiano"},
            {"code": "pt", "name": "Português"},
            {"code": "zh", "name": "中文"}
        ]
        menu_items = []
        for lang in languages:
            is_current = (lang["code"] == self.current_lang)
            menu_items.append({
                "text": lang["name"], "viewclass": "OneLineListItem",
                "on_release": lambda x=lang["code"]: self.change_language(x),
                "theme_text_color": "Primary" if is_current else "Secondary"
            })
        self.language_menu = MDDropdownMenu(
            caller=self.button_container, items=menu_items, width=dp(120),
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
        self.current_code.text = self.lang_codes.get(lang_code, lang_code.upper())
        self.language_menu.dismiss()
        if self.on_change_callback:
            self.on_change_callback(lang_code)


class RootWidget(FloatLayout):
    """Корневой виджет с фоновым изображением"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_image = None
        self.load_background()

    def load_background(self):
        """Загружает фоновое изображение на весь экран"""
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
                        self.bg_image = Rectangle(
                            texture=img.texture,
                            pos=self.pos,
                            size=self.size
                        )
                    self.bind(pos=self._update_bg, size=self._update_bg)
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

        # Если нет ассета, устанавливаем зелёный цвет
        with self.canvas.before:
            Color(0.46, 0.70, 0.71, 1)
            self.bg_image = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size


class GuitarFunsApp(MDApp):
    """Главный класс приложения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "GuitarFuns"
        self.current_language = "ru"
        self.profile_dialog = None
        self.auth_dialog = None
        self.support_dialog = None
        self.language_selector = None
        self.screen_manager = None
        self.home_screen = None
        self.bottom_nav = None
        self.icon_cache = {}

        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК GuitarFuns v{config.VERSION}')
        logger.info(f'🎸 Платформа: {platform}')
        logger.info('🎸 ' + '=' * 50)

    def load_icon(self, icon_name):
        """Загружает иконку из ассета"""
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]

        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    self.icon_cache[icon_name] = icon_data
                    logger.debug(f"✅ Загружена иконка: {icon_name}")
                    return icon_data
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        self.icon_cache[icon_name] = None
        return None

    def build(self):
        logger.debug('Создание интерфейса...')

        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "300"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.material_style = "M3"

        # Применяем настройки для карусели
        from config.carousel_config import CarouselConfig
        CarouselConfig.apply_preset('normal')  # можно 'small', 'normal', 'large', 'tablet'

        root = RootWidget()

        # Верхняя панель
        from screens.components.top_nav import TopNav
        self.top_nav = TopNav(self.screen_manager)
        self.top_nav.set_app(self)
        root.add_widget(self.top_nav)

        # ScreenManager
        self.screen_manager = setup_screen_manager()
        self.screen_manager.current = 'home'
        self.screen_manager.md_bg_color = [0, 0, 0, 0]
        root.add_widget(self.screen_manager)

        # Нижняя панель
        from screens.components.bottom_nav import BottomNav
        self.bottom_nav = BottomNav(self.screen_manager)
        root.add_widget(self.bottom_nav)

        network_manager.start_monitoring()

        logger.info('Интерфейс успешно создан')
        return root

    def add_top_icons(self, root):
        """Добавляет плавающие иконки в верхней части экрана"""
        # Загружаем иконки
        home_icon_data = self.load_icon("home_png")
        profile_icon_data = self.load_icon("profile_png")
        support_icon_data = self.load_icon("support_png")
        language_icon_data = self.load_icon("language_png")

        # Кнопка Главная (слева)
        if home_icon_data:
            home_btn = AnimatedImageButton(
                normal_icon_data=home_icon_data,
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={'x': 0.02, 'top': 0.94},
                allow_stretch=True,
                keep_ratio=True
            )
            home_btn.bind(on_release=lambda x: self.switch_to_home())
            root.add_widget(home_btn)

        # Кнопка Профиль
        if profile_icon_data:
            profile_btn = AnimatedImageButton(
                normal_icon_data=profile_icon_data,
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={'right': 0.15, 'top': 0.94},
                allow_stretch=True,
                keep_ratio=True
            )
            profile_btn.bind(on_release=self.open_profile)
            root.add_widget(profile_btn)

        # Кнопка Поддержка
        if support_icon_data:
            support_btn = AnimatedImageButton(
                normal_icon_data=support_icon_data,
                size_hint=(None, None),
                size=(dp(32), dp(32)),
                pos_hint={'right': 0.08, 'top': 0.94},
                allow_stretch=True,
                keep_ratio=True
            )
            support_btn.bind(on_release=self.open_support)
            root.add_widget(support_btn)

        # LanguageSelector
        self.language_selector = LanguageSelector(
            current_lang="ru",
            on_change_callback=self.change_language,
            icon_data=language_icon_data
        )
        self.language_selector.pos_hint = {'right': 0.98, 'top': 0.94}
        root.add_widget(self.language_selector)

    def switch_to_home(self):
        if self.screen_manager:
            self.screen_manager.current = 'home'
            if self.bottom_nav:
                for item in self.bottom_nav.items:
                    item.active = False

    def open_profile(self, instance):
        logger.info("Нажата иконка профиля")
        if api.is_authenticated():
            self.screen_manager.current = "profile"
        else:
            if self.home_screen and hasattr(self.home_screen, 'open_profile'):
                self.home_screen.open_profile()

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
        if HAS_ASSETS:
            assets_list = Assets.list_assets()
            logger.info(f'📦 Загружено ассетов: {len(assets_list)}')
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