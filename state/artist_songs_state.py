# state/artist_songs_state.py
"""
Состояние экрана «Песни исполнителя».
Хранит имя исполнителя + позицию скролла.
"""
from state.base import BaseStateManager
import time
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
        self._data = {}
        self._timestamp = 0

    def set(self, artist_name: str, scroll_position: float = 1.0):
        self._data = {
            'artist_name': artist_name,
            'scroll_position': scroll_position,
        }
        self._timestamp = time.time()
        logger.info(f"📦 ArtistSongs: {artist_name}, scroll={scroll_position:.2f}")

    def get(self) -> dict:
        if not self._data:
            return {}
        if time.time() - self._timestamp > 300:
            logger.info("⏳ ArtistSongs: устарело")
            return {}
        return dict(self._data)

    def clear(self):
        self._data = {}
        self._timestamp = 0


artist_songs_state = ArtistSongsStateManager()