# state/search_state.py
import time
import threading
from kivy.logger import Logger

logger = Logger.getChild('State:Search')

class SearchStateManager:
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
        logger.debug(f"💾 Search: query='{data.get('query', '')[:20]}', results={len(data.get('results', []))}")

    def get(self, allow_stale: bool = False):
        with self._lock:
            if not self._data:
                return None
            age = time.time() - self._timestamp
            if age > self._ttl and not allow_stale:
                return None
            return dict(self._data)

    def invalidate(self):
        with self._lock:
            self._data = {}
            self._timestamp = 0
        logger.debug("🗑️ Search инвалидирован")

search_state = SearchStateManager()