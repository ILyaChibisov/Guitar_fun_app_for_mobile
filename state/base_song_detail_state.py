# state/base_song_detail_state.py
from state.base import BaseStateManager


class BaseSongDetailStateManager(BaseStateManager):
    """Базовый менеджер состояния для экранов просмотра песни (LRU + TTL)."""

    def __init__(self, name: str, default_ttl: int = 600, max_cached_songs: int = 10):
        super().__init__(name=name, default_ttl=default_ttl)
        self._current_song_id = None
        self._max_cached_songs = max_cached_songs
        self._lru_order = []

    def _touch_lru(self, key: str):
        if key in self._lru_order:
            self._lru_order.remove(key)
        self._lru_order.append(key)
        while len(self._lru_order) > self._max_cached_songs:
            oldest = self._lru_order.pop(0)
            self.invalidate(oldest)

    def save_song_state(self, song_id: int, state_data: dict):
        if not song_id:
            return
        key = str(song_id)
        self._current_song_id = song_id
        self.save(key, state_data, ttl=self._ttl)
        self._touch_lru(key)

    def get_song_state(self, song_id: int) -> dict | None:
        if not song_id:
            return None
        key = str(song_id)
        data = self.get(key, allow_stale=False)
        if data is not None:
            self._touch_lru(key)
        return data

    def reset_song(self, song_id: int = None):
        if song_id is None:
            self.clear()
            self._lru_order.clear()
            self._current_song_id = None
        else:
            key = str(song_id)
            self.invalidate(key)
            if key in self._lru_order:
                self._lru_order.remove(key)
