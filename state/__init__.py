# state/__init__.py
"""
Пакет состояний экранов.
"""
from state.songs_state import songs_state, SongsStateManager

__all__ = ['songs_state', 'SongsStateManager']