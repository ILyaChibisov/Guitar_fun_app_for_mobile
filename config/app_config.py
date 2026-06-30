# config/app_config.py
import os
from kivy.utils import platform
from kivy.logger import Logger


class AppConfig:
    VERSION = '1.0.0'
    APP_NAME = 'GuitarFuns'

    # API URL (используем домен)
    API_BASE_URL = "https://guitarfans.ru/api"

    # API endpoints
    API_AUTH_LOGIN = f"{API_BASE_URL}/auth/login"
    API_AUTH_REGISTER = f"{API_BASE_URL}/auth/register"
    API_AUTH_GOOGLE = f"{API_BASE_URL}/auth/google/login"
    API_AUTH_VK = f"{API_BASE_URL}/auth/vk/login"
    API_AUTH_REFRESH = f"{API_BASE_URL}/auth/refresh"
    API_AUTH_LOGOUT = f"{API_BASE_URL}/auth/logout"
    API_USER_ME = f"{API_BASE_URL}/users/me"
    API_HEALTH = f"{API_BASE_URL}/health"

    # Таймауты
    CONNECTION_TIMEOUT = 10
    READ_TIMEOUT = 30

    # ============ НАСТРОЙКИ КЭША ============
    # Время жизни кэша избранного (в секундах)
    FAVORITES_CACHE_TTL = 60  # 1 минута

    # Время жизни кэша песен (в секундах) - 24 часа
    SONG_CACHE_TTL = 86400

    # Максимальное количество песен в кэше
    MAX_CACHED_SONGS = 100

    # ============ ДОБАВЛЕННЫЕ НАСТРОЙКИ ДЛЯ НОВОЙ ЛОГИКИ ============
    # Время жизни кэша состояния экрана (в секундах)
    SCREEN_STATE_CACHE_TTL = 60  # 1 минута

    # Задержка перед предзагрузкой избранного при старте (в секундах)
    PRELOAD_FAVORITES_DELAY = 1.0

    # ============ ПУТЬ К ПАПКЕ КЭША ============
    _cache_dir = None

    @property
    def CACHE_DIR(self):
        """
        Возвращает путь к папке кэша.
        Автоматически создает папку, если ее нет.
        Работает на Android и Windows.
        """
        if self._cache_dir is not None:
            return self._cache_dir

        cache_dir = self._get_cache_dir()

        # Создаем папку, если ее нет
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, mode=0o755)
                Logger.info(f"📁 Создана папка кэша: {cache_dir}")
            except Exception as e:
                Logger.error(f"❌ Ошибка создания папки кэша: {e}")
                # fallback: используем временную папку
                import tempfile
                cache_dir = tempfile.gettempdir()
                Logger.warning(f"⚠️ Используем временную папку: {cache_dir}")

        # Проверяем, можно ли записать в папку
        if not self._check_write_permission(cache_dir):
            Logger.error(f"❌ Нет прав на запись в {cache_dir}")
            # fallback: используем временную папку
            import tempfile
            cache_dir = tempfile.gettempdir()
            Logger.warning(f"⚠️ Используем временную папку: {cache_dir}")

        self._cache_dir = cache_dir
        Logger.info(f"✅ Папка кэша: {cache_dir}")
        return cache_dir

    def _get_cache_dir(self):
        """Определяет путь к папке кэша в зависимости от платформы"""

        if platform == 'android':
            # ===== ANDROID =====

            # 1. Пытаемся использовать app_storage_path (лучший вариант)
            try:
                from android.storage import app_storage_path
                cache_dir = os.path.join(app_storage_path(), 'cache')
                Logger.info(f"📱 Android: app_storage_path = {cache_dir}")
                return cache_dir
            except ImportError:
                Logger.warning("⚠️ android.storage недоступен")
            except Exception as e:
                Logger.warning(f"⚠️ Ошибка app_storage_path: {e}")

            # 2. Пытаемся использовать getCacheDir()
            try:
                from android import mActivity
                context = mActivity.getApplicationContext()
                cache_dir = context.getCacheDir().getAbsolutePath()
                Logger.info(f"📱 Android: getCacheDir = {cache_dir}")
                return cache_dir
            except ImportError:
                Logger.warning("⚠️ android модуль недоступен")
            except Exception as e:
                Logger.warning(f"⚠️ Ошибка getCacheDir: {e}")

            # 3. Пытаемся использовать внешнее хранилище
            try:
                from android.storage import primary_external_storage_path
                storage_path = primary_external_storage_path()
                if storage_path:
                    cache_dir = os.path.join(storage_path, 'Android', 'data', 'guitarfuns', 'cache')
                    Logger.info(f"📱 Android: внешнее хранилище = {cache_dir}")
                    return cache_dir
            except:
                pass

            # 4. Последний вариант: папка рядом с приложением
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, 'cache')
            Logger.info(f"📱 Android: fallback = {cache_dir}")
            return cache_dir

        else:
            # ===== WINDOWS / ДРУГИЕ ПЛАТФОРМЫ =====
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, 'cache')
            Logger.info(f"💻 Windows/ПК: cache_dir = {cache_dir}")
            return cache_dir

    def _check_write_permission(self, cache_dir):
        """Проверяет, есть ли права на запись в папку"""
        try:
            test_file = os.path.join(cache_dir, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return True
        except Exception as e:
            Logger.error(f"❌ Нет прав на запись: {e}")
            return False

    def get_cache_size(self):
        """Возвращает размер кэша в байтах"""
        cache_dir = self.CACHE_DIR
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(cache_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
        except Exception as e:
            Logger.error(f"Ошибка подсчета размера кэша: {e}")
        return total_size

    def clear_cache(self):
        """Очищает всю папку кэша"""
        cache_dir = self.CACHE_DIR
        try:
            import shutil
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir, mode=0o755)
                Logger.info(f"🗑️ Кэш очищен: {cache_dir}")
                return True
        except Exception as e:
            Logger.error(f"Ошибка очистки кэша: {e}")
            return False


config = AppConfig()