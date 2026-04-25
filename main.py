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
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from io import BytesIO


# ============ ОБРАБОТКА НЕПЕРЕХВАЧЕННЫХ ОШИБОК ============
def handle_exception(exc_type, exc_value, exc_traceback):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print("=" * 50)
    print("FATAL ERROR:")
    print(error_msg)
    print("=" * 50)
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
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass
os.environ['SSL_CERT_FILE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
# ================================================================

# Настройка окна
if platform == 'win':
    Window.borderless = False
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50
    Window.clearcolor = (0, 0, 0, 0)
else:
    Window.clearcolor = (0, 0, 0, 0)
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

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout

from config.app_config import config
from screens.manager import setup_screen_manager
from api.client import api
from api.network_handler import network_manager
from screens.components.bottom_nav import BottomNav
from screens.components.top_nav import TopNav

# Импортируем ассеты
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
    print("✅ Модуль ассетов загружен")
except ImportError as e:
    HAS_ASSETS = False
    print(f"⚠️ Модуль ассетов не найден: {e}")

logger = app_logger()


class RootWidget(MDFloatLayout):
    """Корневой виджет с фоновым изображением"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_image = None
        self.load_background()
        self.size_hint = (1, 1)

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
                        self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                    self.bind(pos=self._update_bg, size=self._update_bg)
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

        # Если нет ассета, устанавливаем цвет как fallback
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
        self.screen_manager = None
        self.bottom_nav = None
        self.top_nav = None

        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК GuitarFuns v{config.VERSION}')
        logger.info(f'🎸 Платформа: {platform}')
        logger.info('🎸 ' + '=' * 50)

        # main.py - метод build (исправленный)

    def build(self):
        logger.debug('Создание интерфейса...')

        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "300"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.material_style = "M3"

        # Корневой виджет с фоном
        root = RootWidget()

        # Создаём ScreenManager
        self.screen_manager = setup_screen_manager()
        self.screen_manager.current = 'home'
        self.screen_manager.md_bg_color = [0, 0, 0, 0]

        # Создаём верхнюю панель (тёмная полупрозрачная)
        self.top_nav = TopNav(self.screen_manager)
        self.top_nav.set_app(self)
        self.top_nav.size_hint = (1, None)
        self.top_nav.height = dp(56)
        self.top_nav.pos_hint = {'top': 1}
        self.top_nav.md_bg_color = [0, 0, 0, 0.3]  # Тёмный полупрозрачный
        self.top_nav.theme_bg_color = "Custom"

        # Создаём нижнюю панель
        self.bottom_nav = BottomNav(self.screen_manager)

        # Добавляем всё в root
        # ВАЖНО: порядок добавления!
        root.add_widget(self.screen_manager)  # 1. Основной контент (самый нижний слой)
        root.add_widget(self.bottom_nav)  # 2. Нижняя панель
        root.add_widget(self.top_nav)  # 3. Верхняя панель (самый верхний слой)

        # Убираем raise_to_top - он не нужен, порядок добавления уже правильный

        network_manager.start_monitoring()

        logger.info('Интерфейс успешно создан')
        return root

    def open_profile(self, instance=None):
        """Открывает экран профиля"""
        if self.screen_manager and self.screen_manager.has_screen('profile'):
            self.screen_manager.current = 'profile'

    def open_support(self, instance=None):
        """Открывает экран поддержки"""
        from utils.notifications import notify
        notify.info("Поддержка будет доступна в следующей версии")

    def change_language(self, lang_code):
        """Изменяет язык приложения"""
        logger.info(f"Смена языка на: {lang_code}")
        # TODO: Реализовать смену языка

    def on_start(self):
        logger.info('Приложение GuitarFuns запущено')
        if HAS_ASSETS:
            try:
                from data import Assets
                assets_list = Assets.list_assets()
                logger.info(f'📦 Загружено ассетов: {len(assets_list)}')
            except Exception as e:
                logger.error(f'Ошибка получения списка ассетов: {e}')

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