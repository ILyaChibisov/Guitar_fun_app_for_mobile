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
from kivy.clock import Clock
from io import BytesIO

import kivy

kivy.require('2.3.0')

# ============ ПРИНУДИТЕЛЬНОЕ ИСПОЛЬЗОВАНИЕ SDL2 ДЛЯ ЗВУКА ============
os.environ['KIVY_AUDIO'] = 'sdl2'


# ============ ФУНКЦИЯ ДЛЯ ПУТЕЙ К ЗВУКАМ (ANDROID/ПК) ============
def get_sound_path(filename):
    """
    Возвращает абсолютный путь к звуковому файлу на Android и ПК

    Args:
        filename: Имя файла (например, 'click.wav')

    Returns:
        str: Абсолютный путь к файлу
    """
    # Получаем путь к папке с main.py
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # На Android пробуем разные варианты
    if platform == 'android':
        possible_paths = [
            os.path.join(base_dir, 'sounds', filename),
            os.path.join(base_dir, 'assets', 'sounds', filename),
            os.path.join(base_dir, filename),
            os.path.join('/sdcard', 'sounds', filename),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        # Если не нашли - возвращаем путь в папке приложения
        return os.path.join(base_dir, filename)
    else:
        # На ПК сначала проверяем папку sounds
        pc_path = os.path.join(base_dir, 'sounds', filename)
        if os.path.exists(pc_path):
            return pc_path
        return os.path.join(base_dir, filename)


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

# ============ НАСТРОЙКА ОКНА ============
if platform == 'android':
    try:
        from android import mActivity
        from jnius import autoclass
        from android.permissions import request_permissions, Permission

        request_permissions([
            Permission.INTERNET,
            Permission.ACCESS_NETWORK_STATE,
            Permission.ACCESS_WIFI_STATE,
            Permission.MODIFY_AUDIO_SETTINGS,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.RECORD_AUDIO
        ])
        print("✅ Разрешения запрошены")

        Window.clearcolor = (0, 0, 0, 0)
        View = autoclass('android.view.View')
        window = mActivity.getWindow()
        decorView = window.getDecorView()
        decorView.setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
        )
        window.setStatusBarColor(0xFF000000)
        window.setNavigationBarColor(0xFF000000)
        current_flags = decorView.getSystemUiVisibility()
        if current_flags & View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR:
            new_flags = current_flags & ~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
            decorView.setSystemUiVisibility(new_flags)
        print("✅ Системные панели настроены")
    except Exception as e:
        print(f"Ошибка настройки: {e}")
        Window.clearcolor = (0, 0, 0, 0)
else:
    Window.borderless = False
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50
    Window.clearcolor = (0, 0, 0, 0)

from config.logger_config import setup_logging, app_logger

setup_logging(level='debug')

from kivymd.app import MDApp
from kivymd.uix.floatlayout import MDFloatLayout

from config.app_config import config
from screens.manager import setup_screen_manager
from api.client import api
from api.network_handler import network_manager
from screens.components.bottom_nav import BottomNav
from screens.components.top_nav import TopNav
from screens.components.blocking_layer import BlockingLayer
from config.system_bars import get_navigation_bar_height, get_status_bar_height, get_screen_density, get_all_system_info

# ============ ОТКЛЮЧЕНИЕ RIPPLE ЭФФЕКТА ============
from kivymd.uix.button import MDIconButton

MDIconButton.ripple_scale = 0
MDIconButton.ripple_alpha = 0

# Импортируем ассеты
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
    print("✅ Модуль ассетов загружен")
except ImportError as e:
    HAS_ASSETS = False
    print(f"⚠️ Модуль ассетов не найден: {e}")

logger = app_logger()


def check_audio_support():
    """Проверяет поддержку звука на устройстве"""
    try:
        from kivy.core.audio import SoundLoader
        logger.info("✅ SoundLoader доступен")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Звук может не работать: {e}")
    return False


class RootWidget(MDFloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_image = None
        self.size_hint = (1, 1)
        self.padding = [0, 0, 0, 0]
        self.load_background()
        logger.info("RootWidget создан")

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
        with self.canvas.before:
            Color(0.46, 0.70, 0.71, 1)
            self.bg_image = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size


class GuitarFunsApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "GuitarFuns"
        self.screen_manager = None
        self.bottom_nav = None
        self.top_nav = None
        self.blocking_layer = None
        self.current_auth_modal = None
        self.is_auth_blocking = False
        self._bottom_nav_visible = False
        self._favorites_preloaded = False  # ← флаг предзагрузки
        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК GuitarFuns v{config.VERSION}')
        logger.info(f'🎸 Платформа: {platform}')
        logger.info('🎸 ' + '=' * 50)

    def set_blocking(self, blocked):
        logger.info(f"set_blocking вызван: blocked={blocked}")
        self.is_auth_blocking = blocked
        if self.blocking_layer:
            self.blocking_layer.set_active(blocked)

    def open_profile(self, instance=None):
        if self.screen_manager:
            current_screen = self.screen_manager.current_screen
            if api.is_authenticated():
                if 'profile' in self.screen_manager.screen_names:
                    self.screen_manager.current = 'profile'
            else:
                self._show_auth_modal_on_screen(current_screen)

    def _show_auth_modal_on_screen(self, screen):
        from screens.components.auth_modal import AuthModal
        self.set_blocking(True)
        self.current_auth_modal = AuthModal(
            parent_screen=screen,
            on_close=self._on_auth_modal_close,
            on_login_success=self._on_auth_success
        )
        if self.blocking_layer:
            self.blocking_layer.set_modal_widget(self.current_auth_modal)
        screen.add_widget(self.current_auth_modal)

    def _on_auth_modal_close(self):
        logger.info("Модальное окно закрыто")
        if self.blocking_layer:
            self.blocking_layer.clear_modal_widget()
        self.current_auth_modal = None
        self.set_blocking(False)

    def _on_auth_success(self, provider=None):
        """Обработчик успешной авторизации"""
        logger.info(f"Авторизация успешна: {provider}")

        # Закрываем модальное окно
        if self.blocking_layer:
            self.blocking_layer.clear_modal_widget()
        self.current_auth_modal = None
        self.set_blocking(False)

        # Загружаем данные пользователя
        if api.access_token:
            api.get_current_user(
                on_success=self._on_user_data_loaded,
                on_failure=lambda req, err: None
            )

        # Обновляем текущий экран после авторизации
        Clock.schedule_once(self._refresh_current_screen, 0.3)

    def _on_user_data_loaded(self, user):
        """Загружены данные пользователя"""
        api.user_data = user
        username = user.get('username', 'Гость')
        logger.info(f"Данные пользователя загружены: {username}")

        # После загрузки данных пользователя — предзагружаем избранное
        Clock.schedule_once(lambda dt: self._preload_favorites(), 0.5)

    def _refresh_current_screen(self, dt):
        """Обновляет текущий экран после авторизации"""
        if self.screen_manager:
            current_screen = self.screen_manager.current_screen
            if current_screen:
                screen_name = current_screen.name
                logger.info(f"Обновление экрана после авторизации: {screen_name}")

                if hasattr(current_screen, 'on_login_success'):
                    current_screen.on_login_success()
                elif screen_name == 'favorites' and hasattr(current_screen, 'refresh_favorites'):
                    current_screen.refresh_favorites()

                if self.screen_manager.has_screen('home'):
                    home_screen = self.screen_manager.get_screen('home')
                    if hasattr(home_screen, 'on_login_success'):
                        home_screen.on_login_success()

    # ============ ПРЕДЗАГРУЗКА ИЗБРАННОГО ============

    def _preload_favorites(self):
        """Предзагружает избранное в фоне при запуске приложения"""
        if self._favorites_preloaded:
            logger.debug("ℹ️ Избранное уже предзагружено")
            return

        if not api.is_authenticated():
            logger.info("ℹ️ Пользователь не авторизован, предзагрузка избранного пропущена")
            return

        logger.info("🔄 Фоновая предзагрузка избранного...")

        def preload():
            try:
                from api.client import api
                api.get_favorites(
                    on_success=self._on_favorites_preloaded,
                    on_failure=lambda req, err: logger.warning(f"⚠️ Предзагрузка избранного не удалась: {err}"),
                    force_refresh=False
                )
            except Exception as e:
                logger.warning(f"⚠️ Ошибка предзагрузки избранного: {e}")

        # Запускаем в фоновом потоке
        import threading
        threading.Thread(target=preload, daemon=True).start()

    def _on_favorites_preloaded(self, favorites):
        """Обработчик успешной предзагрузки избранного"""
        try:
            from utils.screen_state import screen_state
            screen_state.cache_screen_data('favorites', favorites)
            self._favorites_preloaded = True
            logger.info(f"✅ Избранное предзагружено: {len(favorites)} песен")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка сохранения предзагруженного избранного: {e}")

    def build(self):
        logger.debug('Создание интерфейса...')

        if platform == 'android':
            try:
                from android import mActivity
                from jnius import autoclass
                View = autoclass('android.view.View')
                window = mActivity.getWindow()
                window.setSoftInputMode(0x00000020)
                logger.info("⌨️ Android: клавиатура настроена в режиме PAN")
            except Exception as e:
                logger.error(f"Ошибка настройки клавиатуры: {e}")

        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "300"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.material_style = "M3"

        root = RootWidget()
        self.screen_manager = setup_screen_manager()
        self.screen_manager.current = 'home'
        self.screen_manager.md_bg_color = [0, 0, 0, 0]

        try:
            from utils.icon_cache import preload_icons
            preload_icons()
            logger.info("🚀 Запущена предзагрузка иконок")
        except ImportError:
            logger.warning("⚠️ Модуль icon_cache не найден")

        logger.info("📡 Режим работы: все данные загружаются с сервера по запросу")

        self.top_nav = TopNav(self.screen_manager)
        self.top_nav.set_app(self)
        self.top_nav.size_hint = (1, None)
        self.top_nav.pos_hint = {'top': 1}

        # Обновляем заголовок для home
        self.top_nav.update_title('home')
        # Левую кнопку обновляем через встроенный метод TopNav
        self.top_nav._update_left_button('home')
        self.top_nav._update_right_buttons('home')
        logger.info("✅ TopNav установлен на 'Главная'")

        self.bottom_nav = BottomNav(self.screen_manager)
        self.bottom_nav.pos_hint = {'y': 0}

        self.blocking_layer = BlockingLayer()
        self.blocking_layer.opacity = 0
        self.blocking_layer.disabled = True

        root.add_widget(self.screen_manager)
        root.add_widget(self.bottom_nav)
        root.add_widget(self.top_nav)
        root.add_widget(self.blocking_layer)

        network_manager.start_monitoring()
        Window.bind(on_resize=self.on_window_resize)

        logger.info('Интерфейс успешно создан')
        return root

    def on_window_resize(self, window, width, height):
        from config.layout_config import layout_config
        from kivy.clock import Clock
        logger.info(f"🔄 Поворот экрана: {width}x{height}")
        layout_config.force_update()
        Clock.schedule_once(lambda dt: self._reload_nav_bars(), 0.1)
        Clock.schedule_once(lambda dt: self._reload_content_screens(), 0.2)

    def _reload_nav_bars(self):
        if hasattr(self, 'bottom_nav') and self.bottom_nav:
            self.bottom_nav.reload_config()
        if hasattr(self, 'top_nav') and self.top_nav:
            if hasattr(self.top_nav, 'reload_config'):
                self.top_nav.reload_config()
        logger.info("✅ Панели навигации обновлены после поворота")

    def _reload_content_screens(self):
        if hasattr(self, 'screen_manager') and self.screen_manager:
            current_screen = self.screen_manager.current_screen
            if hasattr(current_screen, 'on_orientation_changed'):
                current_screen.on_orientation_changed()

    def open_support(self, instance=None):
        from utils.notifications import notify
        notify.info("Поддержка будет доступна в следующей версии")

    def change_language(self, lang_code):
        logger.info(f"Смена языка на: {lang_code}")

    def on_start(self):
        logger.info('Приложение GuitarFuns запущено')
        check_audio_support()

        # ============ ПРЕДЗАГРУЗКА ИЗБРАННОГО ============
        # Запускаем с задержкой, чтобы дать приложению полностью загрузиться
        Clock.schedule_once(lambda dt: self._preload_favorites(), 1.0)

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

    def hide_bottom_nav(self):
        if hasattr(self, 'bottom_nav') and self.bottom_nav and self.bottom_nav.parent:
            self._bottom_nav_visible = True
            self.bottom_nav.parent.remove_widget(self.bottom_nav)
            logger.info("🔻 BottomNav скрыт")

    def show_bottom_nav(self):
        if hasattr(self, 'bottom_nav') and self.bottom_nav:
            if hasattr(self, '_bottom_nav_visible') and self._bottom_nav_visible:
                root = self.root
                if root and self.bottom_nav.parent is None:
                    root.add_widget(self.bottom_nav)
                    if hasattr(self, 'top_nav') and self.top_nav and self.top_nav.parent:
                        self.top_nav.parent.remove_widget(self.top_nav)
                        root.add_widget(self.top_nav)
                    logger.info("🔺 BottomNav восстановлен")
                self._bottom_nav_visible = False

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        return False


if __name__ == '__main__':
    GuitarFunsApp().run()