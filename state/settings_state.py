# state/settings_state.py
"""
Единое состояние настроек приложения — единственный источник правды.

- Тема, язык, авторизация.
- Версии (theme_version, language_version) — чтобы экраны знали,
  что их отображение устарело, и перекрашивались только при входе.
- Подписчики (listeners) — для «горячих» компонентов
  (TopNav, BottomNav), которые должны обновиться мгновенно.
- Асинхронное сохранение в файл (без fsync в UI-потоке).
"""
import json
import os
import threading
from kivy.clock import Clock
from kivy.logger import Logger

logger = Logger.getChild('State:Settings')


class SettingsState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = threading.RLock()

        # --- Значения ---
        self._theme = 'green'
        self._language = 'ru'
        self._is_authenticated = False

        # --- Версии (растут при каждом изменении) ---
        self._theme_version = 0
        self._language_version = 0

        # --- Подписчики ---
        self._theme_listeners = []
        self._language_listeners = []

        # --- Файл ---
        self._file_path = None
        self._save_event = None
        self._dirty = False

    # ============ ЗАГРУЗКА / СОХРАНЕНИЕ ============

    def load(self, file_path: str):
        """Синхронная загрузка при старте. Вызывается один раз из main."""
        self._file_path = file_path
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._theme = data.get('theme', 'green')
                self._language = data.get('language', 'ru')
                self._is_authenticated = data.get('is_authenticated', False)
                logger.info(
                    f"⚙️ Настройки загружены: theme={self._theme}, "
                    f"lang={self._language}, auth={self._is_authenticated}"
                )
            else:
                logger.info("⚙️ Файл настроек не найден, используем дефолт")
                self._save_now()
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки настроек: {e}")

    def _save_now(self):
        """Синхронная запись (без fsync). Только из фонового таймера или on_stop."""
        if not self._file_path:
            return
        try:
            data = {
                'theme': self._theme,
                'language': self._language,
                'is_authenticated': self._is_authenticated,
            }
            parent = os.path.dirname(self._file_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._dirty = False
            logger.debug(f"💾 Настройки сохранены: {data}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения настроек: {e}")

    def _schedule_save(self):
        """Асинхронная запись через 0.3 с (склеивает частые изменения)."""
        if not self._file_path:
            return
        self._dirty = True
        if self._save_event:
            self._save_event.cancel()
        self._save_event = Clock.schedule_once(lambda dt: self._save_now(), 0.3)

    def flush(self):
        """Принудительная запись. Вызывать в on_stop / on_pause."""
        if self._save_event:
            self._save_event.cancel()
            self._save_event = None
        if self._dirty or self._file_path:
            self._save_now()

    # ============ ТЕМА ============

    @property
    def theme(self):
        return self._theme

    @property
    def theme_version(self):
        return self._theme_version

    def set_theme(self, theme_id: str):
        if theme_id == self._theme:
            return
        with self._lock:
            self._theme = theme_id
            self._theme_version += 1
            self._schedule_save()
        logger.info(f"🎨 Тема → {theme_id} (v{self._theme_version})")
        self._notify_theme(theme_id)

    def add_theme_listener(self, callback):
        if callback not in self._theme_listeners:
            self._theme_listeners.append(callback)

    def remove_theme_listener(self, callback):
        if callback in self._theme_listeners:
            self._theme_listeners.remove(callback)

    def _notify_theme(self, theme_id):
        for cb in list(self._theme_listeners):
            try:
                cb(theme_id)
            except Exception as e:
                logger.error(f"Ошибка в theme-listener: {e}")

    # ============ ЯЗЫК ============

    @property
    def language(self):
        return self._language

    @property
    def language_version(self):
        return self._language_version

    def set_language(self, lang_code: str):
        if lang_code == self._language:
            return
        with self._lock:
            self._language = lang_code
            self._language_version += 1
            self._schedule_save()
        logger.info(f"🌐 Язык → {lang_code} (v{self._language_version})")
        self._notify_language(lang_code)

    def add_language_listener(self, callback):
        if callback not in self._language_listeners:
            self._language_listeners.append(callback)

    def remove_language_listener(self, callback):
        if callback in self._language_listeners:
            self._language_listeners.remove(callback)

    def _notify_language(self, lang_code):
        for cb in list(self._language_listeners):
            try:
                cb(lang_code)
            except Exception as e:
                logger.error(f"Ошибка в language-listener: {e}")

    # ============ АВТОРИЗАЦИЯ ============

    @property
    def is_authenticated(self):
        return self._is_authenticated

    def set_authenticated(self, value: bool):
        if bool(value) == self._is_authenticated:
            return
        with self._lock:
            self._is_authenticated = bool(value)
            self._schedule_save()


settings_state = SettingsState()