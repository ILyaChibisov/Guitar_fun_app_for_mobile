# state/favorites_state.py
"""
Состояние экрана «Избранное».

Хранит ТОЛЬКО метаданные (страница, total, скролл).
Список песен живёт на самом экране в self._favorites.

Аналогично songs_state / artist_songs_state.
"""
import time
import threading
from kivy.logger import Logger

logger = Logger.getChild('State:Favorites')


class FavoritesStateManager:
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
        self._ttl = 300  # 5 минут

    def save(self, data: dict):
        """
        data = {
            'page': int,
            'total': int,
            'scroll_position': float,
        }
        """
        with self._lock:
            self._data = dict(data)
            self._timestamp = time.time()
        logger.debug(
            f"💾 Favorites: page={data.get('page')}, "
            f"total={data.get('total')}, "
            f"scroll={data.get('scroll_position', 1.0):.2f}"
        )

    def get(self, allow_stale: bool = False):
        with self._lock:
            if not self._data:
                return None
            age = time.time() - self._timestamp
            if age > self._ttl and not allow_stale:
                logger.debug(f"⏳ Favorites устарел ({age:.0f}с)")
                return None
            return dict(self._data)

    def invalidate(self):
        with self._lock:
            self._data = {}
            self._timestamp = 0
        logger.debug("🗑️ Favorites инвалидирован")


favorites_state = FavoritesStateManager()