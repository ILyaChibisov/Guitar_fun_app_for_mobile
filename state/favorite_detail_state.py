# state/favorite_detail_state.py
"""
Состояние экрана «Детали избранной песни».
Хранит кэш предвычисленных транспонирований, активный вариант (tab_index),
тональность, размер шрифта, скорость прокрутки и позицию скролла по song_id.
"""
import threading
from kivy.logger import Logger
from state.base import BaseStateManager

logger = Logger.getChild('State:FavoriteDetail')


class FavoriteDetailStateManager(BaseStateManager):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__(name='FavoriteDetail', default_ttl=600)
        self._initialized = True
        self._current_song_id = None
        self._max_cached_songs = 10
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
        self.save(key, state_data, ttl=600)
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


favorite_detail_state = FavoriteDetailStateManager()
