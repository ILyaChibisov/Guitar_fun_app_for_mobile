# state/dictionary_state.py
"""
Состояние экрана «Словарь».
Хранит только метаданные (буква, страница, скролл, запрос, режим поиска).
Списки терминов живут в all_terms / terms_by_letter на экране.
"""
import time
import threading
from kivy.logger import Logger

logger = Logger.getChild('State:Dictionary')


class DictionaryStateManager:
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
        self._data = {}
        self._timestamp = 0
        self._ttl = 300

    def save(self, data: dict):
        with self._lock:
            self._data = dict(data)
            self._timestamp = time.time()
        logger.debug(
            f"💾 Dictionary: letter={data.get('current_letter')}, "
            f"search={data.get('is_search_mode')}, "
            f"page={data.get('page')}, "
            f"query='{data.get('query', '')[:20]}'"
        )

    def get(self, allow_stale: bool = False):
        with self._lock:
            if not self._data:
                return None
            age = time.time() - self._timestamp
            if age > self._ttl and not allow_stale:
                logger.debug(f"⏳ Dictionary устарел ({age:.0f}с)")
                return None
            return dict(self._data)

    def invalidate(self):
        with self._lock:
            self._data = {}
            self._timestamp = 0
        logger.debug("🗑️ Dictionary инвалидирован")

    # ============ Совместимость с старым screen_state API ============
    def save_screen_state(self, screen_name, state_dict):
        self.save(state_dict)

    def get_screen_state(self, screen_name, max_age=60):
        return self.get(allow_stale=False)

    def clear_screen_state(self, screen_name):
        self.invalidate()


dictionary_state = DictionaryStateManager()