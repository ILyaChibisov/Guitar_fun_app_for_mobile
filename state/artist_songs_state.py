# state/artist_songs_state.py
"""
Состояние экрана «Песни исполнителя».

Хранит только метаданные (имя исполнителя, страница, total, скролл).
Списки песен живут в _songs_cache на самом экране.

Есть методы-совместимости с предыдущей версией API (set, clear,
get_artist_songs_data, has_artist_songs_data) — чтобы старый compat.py
продолжал работать.
"""
import time
import threading
from kivy.logger import Logger

logger = Logger.getChild('State:ArtistSongs')


class ArtistSongsStateManager:
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

    # ============ Новый API ============

    def save(self, data: dict):
        """
        Сохраняет данные.

        data = {
            'artist_name': str,
            'page': int,
            'total_songs': int,
            'scroll_position': float,
        }
        """
        with self._lock:
            self._data = dict(data)
            self._timestamp = time.time()
        logger.debug(
            f"💾 ArtistSongs: artist={data.get('artist_name')}, "
            f"page={data.get('page')}, "
            f"total={data.get('total_songs')}, "
            f"scroll={data.get('scroll_position', 1.0):.2f}"
        )

    def get(self, allow_stale: bool = False):
        with self._lock:
            if not self._data:
                return None
            age = time.time() - self._timestamp
            if age > self._ttl and not allow_stale:
                logger.debug(f"⏳ ArtistSongs устарел ({age:.0f}с)")
                return None
            return dict(self._data)

    def invalidate(self):
        with self._lock:
            self._data = {}
            self._timestamp = 0
        logger.debug("🗑️ ArtistSongs инвалидирован")

    def age(self):
        """Возвращает возраст данных в секундах или None, если пусто."""
        with self._lock:
            if not self._data:
                return None
            return time.time() - self._timestamp

    # ============ Совместимость со старым API (compat.py) ============

    def set(self, artist_name: str, scroll_position: float = 1.0):
        """Совместимость. Вызывает save()."""
        self.save({
            'artist_name': artist_name,
            'page': 0,
            'total_songs': 0,
            'scroll_position': scroll_position,
        })

    def clear(self):
        """Совместимость. Вызывает invalidate()."""
        self.invalidate()

    def get_artist_songs_data(self):
        """
        Совместимость. Возвращает dict только с artist_name и scroll_position,
        либо пустой dict.
        """
        data = self.get(allow_stale=True)
        if not data:
            return {}
        return {
            'artist_name': data.get('artist_name', ''),
            'scroll_position': data.get('scroll_position', 1.0),
        }

    def has_artist_songs_data(self):
        """Совместимость. True, если есть валидные данные."""
        return bool(self.get(allow_stale=True))


# Глобальный экземпляр
artist_songs_state = ArtistSongsStateManager()