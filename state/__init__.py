# state/__init__.py
"""
Пакет состояний экранов.
"""
from state.songs_state import songs_state, SongsStateManager
from state.artist_songs_state import artist_songs_state, ArtistSongsStateManager
from state.dictionary_state import dictionary_state, DictionaryStateManager

__all__ = [
    'songs_state', 'SongsStateManager',
    'artist_songs_state', 'ArtistSongsStateManager',
    'dictionary_state', 'DictionaryStateManager',
]