# state/__init__.py
"""
Пакет состояний экранов и настроек.
"""
from state.songs_state import songs_state, SongsStateManager
from state.artist_songs_state import artist_songs_state, ArtistSongsStateManager
from state.dictionary_state import dictionary_state, DictionaryStateManager
from state.settings_state import settings_state, SettingsState
from state.favorites_state import favorites_state, FavoritesStateManager
from state.search_state import search_state, SearchStateManager

__all__ = [
    'songs_state', 'SongsStateManager',
    'artist_songs_state', 'ArtistSongsStateManager',
    'dictionary_state', 'DictionaryStateManager',
    'settings_state', 'SettingsState',
    'favorites_state', 'FavoritesStateManager',
    'SearchStateManager',
]