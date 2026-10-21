# main.py
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
from kivy.uix.floatlayout import FloatLayout

import kivy

kivy.require('2.3.0')

# ============ ПРИНУДИТЕЛЬНОЕ ИСПОЛЬЗОВАНИЕ SDL2 ДЛЯ ЗВУКА ============
os.environ['KIVY_AUDIO'] = 'sdl2'


# ============ ФУНКЦИЯ ДЛЯ ПУТЕЙ К ЗВУКАМ (ANDROID/ПК) ============
def get_sound_path(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))

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
        return os.path.join(base_dir, filename)
    else:
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

        Window.clearcolor = (0, 0, 0, 1)

        View = autoclass('android.view.View')
        WindowManager = autoclass('android.view.WindowManager$LayoutParams')
        Build = autoclass('android.os.Build')
        window = mActivity.getWindow()
        decorView = window.getDecorView()

        window.setStatusBarColor(0xFF000000)
        window.setNavigationBarColor(0xFF000000)

        flags = (
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE |
                View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
        )

        if Build.VERSION.SDK_INT >= 23:
            try:
                flags |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                print("✅ API 23+: светлые значки статус-бара")
            except AttributeError:
                pass

        if Build.VERSION.SDK_INT >= 26:
            try:
                flags |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
                print("✅ API 26+: светлые значки навигации")
            except AttributeError:
                pass

        decorView.setSystemUiVisibility(flags)

        try:
            params = window.getAttributes()
            if hasattr(WindowManager, 'FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS'):
                params.flags |= WindowManager.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS
                window.setAttributes(params)
                print("✅ FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS")
        except Exception as e:
            print(f"⚠️ FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS: {e}")

        manufacturer = Build.MANUFACTURER.lower()

        if "xiaomi" in manufacturer:
            try:
                MIUI_NAVIGATION_BAR_DARK = 0x00000010
                decorView.setSystemUiVisibility(
                    decorView.getSystemUiVisibility() | MIUI_NAVIGATION_BAR_DARK
                )
                print("✅ Xiaomi: тёмная навигация")
            except:
                pass

        if "samsung" in manufacturer:
            try:
                if Build.VERSION.SDK_INT >= 26:
                    decorView.setSystemUiVisibility(
                        decorView.getSystemUiVisibility() |
                        View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
                    )
                print("✅ Samsung: светлые значки")
            except:
                pass

        print(f"🔍 Статус-бар: #{window.getStatusBarColor():08X}")
        print(f"🔍 Навигация: #{window.getNavigationBarColor():08X}")
        print("✅ Системные панели: ЧЁРНЫЕ + СВЕТЛЫЕ ЗНАЧКИ")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        Window.clearcolor = (0, 0, 0, 1)
else:
    Window.clearcolor = (0, 0, 0, 1)
    Window.borderless = False
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50

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
from screens.components.sidebar import Sidebar
from screens.components.blocking_layer import BlockingLayer
from config.system_bars import get_navigation_bar_height, get_status_bar_height, get_screen_density, get_all_system_info

# ============ НАСТРОЙКИ ============
from utils.settings_manager import settings_manager

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
        self.bg_rect = None
        self.size_hint = (1, 1)
        self.padding = [0, 0, 0, 0]

        self._init_canvas()
        self.load_background()

        # Применяем сохранённую тему (читается из файла)
        self.apply_theme(settings_manager.theme)

        logger.info("RootWidget создан")

    def _init_canvas(self):
        with self.canvas.before:
            self.bg_color = Color(0.05, 0.05, 0.05, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        if self.bg_rect:
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def load_background(self):
        if not HAS_ASSETS:
            return
        # Не дублируем, если уже загружено
        if getattr(self, 'bg_image', None) is not None:
            return
        try:
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
                    self.img_color = Color(1, 1, 1, 1)
                    self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                self._update_rect()
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

    def apply_theme(self, theme_id):
        logger.info(f"🖼️ Применение фона для темы: {theme_id}")

        # Полностью очищаем canvas.before — убираем накопленные инструкции
        self.canvas.before.clear()
        self.bg_image = None
        self.img_color = None

        if theme_id == "dark":
            with self.canvas.before:
                self.bg_color = Color(0.07, 0.07, 0.07, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self._update_rect()
        elif theme_id == "light":
            with self.canvas.before:
                self.bg_color = Color(0.969, 0.976, 0.969, 1)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self._update_rect()
        else:  # green
            with self.canvas.before:
                self.bg_color = Color(0, 0, 0, 0)
                self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self._update_rect()
            self.load_background()


class GuitarFunsApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "GuitarFuns"
        self.screen_manager = None
        self.bottom_nav = None
        self.top_nav = None
        self.sidebar = None
        self.blocking_layer = None
        self.current_auth_modal = None
        self.is_auth_blocking = False
        self._bottom_nav_visible = False
        self._favorites_preloaded = False
        self.splash_screen = None
        self._components_created = False

        # Читаем настройки из файла при старте
        saved_theme = settings_manager.theme
        saved_language = settings_manager.language

        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК GuitarFuns v{config.VERSION}')
        logger.info(f'🎸 Платформа: {platform}')
        logger.info(f'🎸 Язык из файла: {saved_language}')
        logger.info('🎸 ' + '=' * 50)

    # ============ ПРИМЕНЕНИЕ ГЛОБАЛЬНЫХ НАСТРОЕК ============

    def apply_theme(self, theme_id):
        """Глобально применяет тему. KivyMD theme_cls в рантайме НЕ трогаем (это фризит)."""
        logger.info(f"🎨 Глобальное применение темы: {theme_id}")

        # ❌ НЕ меняем self.theme_cls.theme_style / primary_palette —
        # это триггерит KivyMD пересобирать canvas всех виджетов (3-4 сек фриза).
        # Тему применяем вручную через update_theme_colors на каждом экране/компоненте.

        if hasattr(self, 'root') and self.root:
            self.root.apply_theme(theme_id)

        def _refresh_nav():
            if hasattr(self, 'top_nav') and self.top_nav:
                try:
                    self.top_nav.update_theme_colors()
                except Exception as e:
                    logger.debug(f"TopNav theme update failed: {e}")
            if hasattr(self, 'bottom_nav') and self.bottom_nav:
                try:
                    self.bottom_nav.update_theme_colors()
                except Exception as e:
                    logger.debug(f"BottomNav theme update failed: {e}")

        Clock.schedule_once(lambda dt: _refresh_nav(), 0)

        if not hasattr(self, 'screen_manager') or not self.screen_manager:
            return

        sm = self.screen_manager
        current = sm.current_screen if hasattr(sm, 'current_screen') else None

        if current and hasattr(current, 'update_theme_colors'):
            try:
                current.update_theme_colors()
            except Exception as e:
                logger.debug(f"Не удалось обновить тему на экране {getattr(current, 'name', '?')}: {e}")

        current_name = getattr(current, 'name', None)
        others = [n for n in sm.screen_names if n != current_name]

        def _update_next(names, idx=0):
            if idx >= len(names):
                return
            name = names[idx]
            try:
                scr = sm.get_screen(name)
                if hasattr(scr, 'update_theme_colors'):
                    scr.update_theme_colors()
            except Exception as e:
                logger.debug(f"Не удалось обновить тему на экране {name}: {e}")
            Clock.schedule_once(lambda dt: _update_next(names, idx + 1), 0)

        Clock.schedule_once(lambda dt: _update_next(others), 0)

    def apply_language(self, lang_code):
        """Глобально применяет язык"""
        logger.info(f"🌐 Глобальное применение языка: {lang_code}")
        settings_manager.set_language(lang_code)

        if hasattr(self, 'top_nav') and self.top_nav:
            current_screen = self.screen_manager.current if self.screen_manager else 'home'
            self.top_nav.update_title(current_screen)

        if hasattr(self, 'bottom_nav') and self.bottom_nav:
            self.bottom_nav.update_language()

        # Обновляем все экраны
        if hasattr(self, 'screen_manager') and self.screen_manager:
            for screen_name in self.screen_manager.screen_names:
                screen = self.screen_manager.get_screen(screen_name)
                if hasattr(screen, 'update_language'):
                    try:
                        screen.update_language()
                    except Exception as e:
                        logger.debug(f"Не удалось обновить язык на экране {screen_name}: {e}")

    # ============ АВТОРИЗАЦИЯ ============

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
        logger.info(f"Авторизация успешна: {provider}")
        settings_manager.set_authenticated(True)

        if self.blocking_layer:
            self.blocking_layer.clear_modal_widget()
        self.current_auth_modal = None
        self.set_blocking(False)

        if api.access_token:
            api.get_current_user(
                on_success=self._on_user_data_loaded,
                on_failure=lambda req, err: None
            )

        Clock.schedule_once(self._refresh_current_screen, 0.3)
        Clock.schedule_once(lambda dt: self._update_sidebar(), 0.5)

    def _on_user_data_loaded(self, user):
        api.user_data = user
        username = user.get('username', 'Гость')
        logger.info(f"Данные пользователя загружены: {username}")
        Clock.schedule_once(lambda dt: self._preload_favorites(), 0.5)
        Clock.schedule_once(lambda dt: self._update_sidebar(), 0.3)

    def _update_sidebar(self):
        if self.sidebar:
            self.sidebar.update_user_info()

    def _refresh_current_screen(self, dt):
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

    def _preload_favorites(self):
        if self._favorites_preloaded:
            logger.debug("ℹ️ Избранное уже предзагружено")
            return

        if not api.is_authenticated():
            logger.info("ℹ️ Пользователь не авторизован, предзагрузка избранного пропущена")
            return

        logger.info("🔄 Фоновая предзагрузка избранного...")

        api.get_favorites(
            on_success=self._on_favorites_preloaded,
            on_failure=lambda req, err: logger.warning(f"⚠️ Предзагрузка избранного не удалась: {err}"),
            force_refresh=False
        )

    def _on_favorites_preloaded(self, favorites):
        self._favorites_preloaded = True
        logger.info(f"✅ Избранное предзагружено: {len(favorites)} песен")

    # ============ BUILD ============

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

        # ============ ПРИМЕНЕНИЕ СОХРАНЁННЫХ НАСТРОЕК ============
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "300"
        self.theme_cls.material_style = "M3"

        saved_theme = settings_manager.theme
        saved_language = settings_manager.language

        if saved_theme == "dark":
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"

        if saved_theme == "green":
            self.theme_cls.primary_palette = "Teal"
        elif saved_theme == "light":
            self.theme_cls.primary_palette = "Gray"

        logger.info(f"⚙️ Загружены настройки: тема={saved_theme}, язык={saved_language}")

        self.root = RootWidget()

        try:
            from screens.splash_screen import SplashScreen
            self.splash_screen = SplashScreen(
                on_complete=self._on_splash_complete
            )
            self.root.add_widget(self.splash_screen)
            logger.info("✅ SplashScreen создан и добавлен")
        except ImportError as e:
            logger.error(f"❌ Ошибка импорта SplashScreen: {e}")
            self._components_created = True
            self._create_app_components()
            self._show_app_components()

        Clock.schedule_once(self._preload_app, 0.1)

        try:
            from utils.icon_cache import preload_icons
            preload_icons()
            logger.info("🚀 Запущена предзагрузка иконок")
        except ImportError:
            logger.warning("⚠️ Модуль icon_cache не найден")

        logger.info("📡 Режим работы: все данные загружаются с сервера по запросу")

        return self.root

    def _preload_app(self, dt):
        logger.info("🔄 Фоновая предзагрузка приложения...")

        if not self._components_created:
            self._create_app_components()
            self._components_created = True

        Clock.schedule_once(lambda dt: self._preload_favorites(), 0.5)

    def _create_app_components(self):
        logger.info("📦 Создание компонентов приложения...")

        self.screen_manager = setup_screen_manager()
        self.screen_manager.current = 'home'
        self.screen_manager.md_bg_color = [0, 0, 0, 0]

        self.top_nav = TopNav(self.screen_manager)
        self.top_nav.set_app(self)
        self.top_nav.size_hint = (1, None)
        self.top_nav.pos_hint = {'top': 1}
        self.top_nav.update_title('home')
        self.top_nav._update_left_button('home')
        self.top_nav._update_right_buttons('home')

        self.bottom_nav = BottomNav(self.screen_manager)
        self.bottom_nav.pos_hint = {'y': 0}

        self.sidebar = Sidebar(self.screen_manager)
        self.sidebar.close()

        self.blocking_layer = BlockingLayer()
        self.blocking_layer.opacity = 0
        self.blocking_layer.disabled = True

        logger.info("✅ Все компоненты созданы")

    def _show_app_components(self):
        logger.info("🎬 Показываем компоненты приложения")

        self.root.add_widget(self.screen_manager)
        self.root.add_widget(self.bottom_nav)
        self.root.add_widget(self.top_nav)
        self.root.add_widget(self.sidebar)
        self.root.add_widget(self.blocking_layer)

        network_manager.start_monitoring()
        Window.bind(on_resize=self.on_window_resize)

        Clock.schedule_once(lambda dt: self._update_sidebar(), 0.3)

        if self.screen_manager and self.screen_manager.has_screen('home'):
            home_screen = self.screen_manager.get_screen('home')
            Clock.schedule_once(lambda dt: home_screen._check_auth(0), 0.5)

        logger.info("✅ Компоненты приложения показаны")

    def _on_splash_complete(self):
        logger.info("🎬 Сплеш-скрин завершён, показываем приложение")

        if self.splash_screen and self.splash_screen.parent:
            self.root.remove_widget(self.splash_screen)
            self.splash_screen = None

        if not self._components_created:
            self._create_app_components()
            self._components_created = True

        self._show_app_components()

        self.root.opacity = 0
        anim = Animation(opacity=1, duration=0.3, t='out_quad')
        anim.start(self.root)

        logger.info("✅ Приложение полностью загружено")

    # ============ ОБРАБОТЧИКИ ============

    def _on_settings_press(self, *args):
        logger.info("⚙️ Нажата иконка настроек → открываем Sidebar")

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

    # ============ ЖИЗНЕННЫЙ ЦИКЛ ============

    def on_start(self):
        logger.info('Приложение GuitarFuns запущено')
        check_audio_support()

        Clock.schedule_once(lambda dt: self._preload_favorites(), 1.0)
        Clock.schedule_once(lambda dt: self._update_sidebar(), 0.5)

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
        Clock.schedule_once(lambda dt: self._update_sidebar(), 0.3)

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