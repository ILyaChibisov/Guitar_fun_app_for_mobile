# utils/settings_manager.py
import os
import json
from config.logger_config import get_logger
from config.app_config import config

logger = get_logger('SettingsManager')


class SettingsManager:
    _instance = None

    DEFAULT_SETTINGS = {
        "theme": "green",
        "language": "ru",
        "is_authenticated": False
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._file_path = os.path.join(config.CACHE_DIR, 'user_settings.json')
            cls._instance._cache = None
            cls._instance._ensure_file_exists()
        return cls._instance

    def _ensure_file_exists(self):
        """Создает файл с дефолтными настройками, если его нет"""
        if not os.path.exists(self._file_path):
            self._save(self.DEFAULT_SETTINGS)
            logger.info(f"✅ Создан файл настроек: {self._file_path}")

    def _read(self):
        """Читает настройки. С диска — один раз, дальше из кэша."""
        if self._cache is not None:
            return self._cache

        try:
            if os.path.exists(self._file_path):
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                result = self.DEFAULT_SETTINGS.copy()
                result.update(data)
                self._cache = result
                return result
        except Exception as e:
            logger.error(f"❌ Ошибка чтения файла настроек: {e}")

        self._cache = self.DEFAULT_SETTINGS.copy()
        return self._cache

    def _save(self, data):
        """Сохраняет настройки в файл и синхронизирует кэш."""
        try:
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self._cache = data.copy()
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения настроек: {e}")

    @property
    def theme(self):
        return self._read().get("theme", "green")

    @property
    def language(self):
        return self._read().get("language", "ru")

    @property
    def is_authenticated(self):
        return self._read().get("is_authenticated", False)

    def set_theme(self, theme_id):
        data = self._read()
        if data.get("theme") != theme_id:
            data = data.copy()
            data["theme"] = theme_id
            self._save(data)          # файл + кэш
            logger.info(f"🎨 Тема изменена на: {theme_id}")

    def set_language(self, lang_code):
        data = self._read()
        if data.get("language") != lang_code:
            data = data.copy()
            data["language"] = lang_code
            self._save(data)          # файл + кэш
            logger.info(f"🌐 Язык изменён на: {lang_code}")

    def set_authenticated(self, is_auth):
        data = self._read()
        if data.get("is_authenticated") != is_auth:
            data = data.copy()
            data["is_authenticated"] = is_auth
            self._save(data)

    def get_all(self):
        return self._read().copy()


settings_manager = SettingsManager()