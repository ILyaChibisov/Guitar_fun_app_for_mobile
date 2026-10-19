# utils/settings_manager.py
"""
Менеджер глобальных настроек приложения.
Сохраняет и загружает настройки (тема, язык) в JSON-файл.
"""
import os
import json
from kivy.utils import platform
from config.logger_config import get_logger
from config.app_config import config

logger = get_logger('SettingsManager')


class SettingsManager:
    """Синглтон для управления настройками приложения"""

    _instance = None
    _settings = None

    DEFAULT_SETTINGS = {
        "theme": "green",  # green, light, dark
        "language": "ru",  # ru, en
        "is_authenticated": False
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._load()
        return cls._instance

    def _get_file_path(self):
        """Возвращает путь к файлу настроек (в папке кэша)"""
        cache_dir = config.CACHE_DIR
        return os.path.join(cache_dir, 'user_settings.json')

    def _load(self):
        """Загружает настройки из файла или создаёт дефолтные"""
        self._file_path = self._get_file_path()

        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Сливаем с дефолтными, чтобы при добавлении новых ключей не было ошибок
                self._settings = self.DEFAULT_SETTINGS.copy()
                self._settings.update(data)
                logger.info(f"✅ Настройки загружены из файла: {self._settings}")
                return
            except Exception as e:
                logger.error(f"❌ Ошибка чтения файла настроек: {e}")

        # Если файла нет или он битый — используем дефолт
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.save()
        logger.info("⚙️ Созданы настройки по умолчанию")

    def save(self):
        """Сохраняет текущие настройки в файл"""
        try:
            # Убедимся, что папка существует
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)

            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=4)
            logger.debug(f"💾 Настройки сохранены в {self._file_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения настроек: {e}")

    # ---------- ГЕТТЕРЫ ----------
    @property
    def theme(self):
        return self._settings.get("theme", "green")

    @property
    def language(self):
        return self._settings.get("language", "ru")

    @property
    def is_authenticated(self):
        return self._settings.get("is_authenticated", False)

    # ---------- СЕТТЕРЫ ----------
    def set_theme(self, theme_id):
        if self._settings.get("theme") != theme_id:
            self._settings["theme"] = theme_id
            self.save()
            logger.info(f"🎨 Тема изменена на: {theme_id}")

    def set_language(self, lang_code):
        if self._settings.get("language") != lang_code:
            self._settings["language"] = lang_code
            self.save()
            logger.info(f"🌐 Язык изменён на: {lang_code}")

    def set_authenticated(self, is_auth):
        if self._settings.get("is_authenticated") != is_auth:
            self._settings["is_authenticated"] = is_auth
            self.save()

    def reset_to_default(self):
        """Сбрасывает настройки на дефолтные (например, при выходе из аккаунта)"""
        self._settings = self.DEFAULT_SETTINGS.copy()
        self.save()
        logger.info("🔄 Настройки сброшены на дефолтные")

    def get_all(self):
        """Возвращает копию всех настроек"""
        return self._settings.copy()


# Глобальный экземпляр для удобного импорта
settings_manager = SettingsManager()