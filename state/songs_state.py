# state/songs_state.py
"""
Состояние экрана «Песни».
Хранит ТОЛЬКО метаданные (буква, страница, скролл).
Списки артистов живут в _artists_cache экрана и НЕ дублируются здесь.
"""
import time
import threading
from kivy.logger import Logger

logger = Logger.getChild('State:Songs')


class SongsStateManager:
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

        # ---- Алфавит ----
        self._alphabet = {}
        self._alphabet_ts = 0
        self._alphabet_ttl = 300  # 5 минут

        # ---- Поиск ----
        self._search = {}
        self._search_ts = 0
        self._search_ttl = 120  # 2 минуты

    # ============ АЛФАВИТ ============

    def save_alphabet(self, data: dict):
        """
        data = {
            'current_letter': str,
            'current_language': str,
            'page': int,
            'total_artists': int,
            'has_more': bool,
            'scroll_position': float,
        }
        """
        with self._lock:
            self._alphabet = dict(data)
            self._alphabet_ts = time.time()
        logger.debug(
            f"💾 Alphabet: letter={data.get('current_letter')}, "
            f"page={data.get('page')}, "
            f"scroll={data.get('scroll_position', 1.0):.2f}"
        )

    def get_alphabet(self, allow_stale: bool = False):
        with self._lock:
            if not self._alphabet:
                return None
            age = time.time() - self._alphabet_ts
            if age > self._alphabet_ttl and not allow_stale:
                logger.debug(f"⏳ Alphabet устарел ({age:.0f}с)")
                return None
            return dict(self._alphabet)

    def invalidate_alphabet(self):
        with self._lock:
            self._alphabet = {}
            self._alphabet_ts = 0
        logger.debug("🗑️ Alphabet инвалидирован")

    # ============ ПОИСК ============

    def save_search(self, data: dict):
        """
        data = {
            'query': str,
            'search_page': int,
        }
        Сами результаты поиска живут в self._all_search_results экрана.
        """
        with self._lock:
            self._search = dict(data)
            self._search_ts = time.time()
        logger.debug(
            f"💾 Search: query='{data.get('query')}', "
            f"page={data.get('search_page')}"
        )

    def get_search(self, allow_stale: bool = False):
        with self._lock:
            if not self._search:
                return None
            age = time.time() - self._search_ts
            if age > self._search_ttl and not allow_stale:
                logger.debug(f"⏳ Search устарел ({age:.0f}с)")
                return None
            return dict(self._search)

    def invalidate_search(self):
        with self._lock:
            self._search = {}
            self._search_ts = 0
        logger.debug("🗑️ Search инвалидирован")

    # ============ ОБЩЕЕ ============

    def clear_all(self):
        with self._lock:
            self._alphabet = {}
            self._alphabet_ts = 0
            self._search = {}
            self._search_ts = 0
        logger.debug("🗑️ Все состояния songs очищены")


# Глобальный экземпляр
songs_state = SongsStateManager()