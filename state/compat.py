# state/compat.py
"""
Слой обратной совместимости.
Позволяет существующему коду использовать screen_state как раньше,
но внутри всё уже разложено по модулям.
"""
import time
from kivy.logger import Logger

from state.previous_screen import previous_screen_state
from state.artist_songs_state import artist_songs_state
from state.songs_state import songs_state

logger = Logger.getChild('State:Compat')


class CompatScreenState:
    """Прокси-объект, перенаправляющий вызовы в новые модули."""

    # ---------- Навигация ----------
    def set_previous_screen(self, name):
        previous_screen_state.set_previous(name)

    def get_previous_screen(self):
        return previous_screen_state.get_previous()

    def set_pending_chord(self, chord):
        previous_screen_state.set_pending_chord(chord)

    def get_pending_chord(self):
        return previous_screen_state.get_pending_chord()

    def clear_pending_chord(self):
        previous_screen_state.clear_pending_chord()

    # ---------- Artist Songs ----------
    def set_artist_songs_data(self, artist_name, scroll_position=1.0):
        artist_songs_state.set(artist_name, scroll_position)

    def get_artist_songs_data(self):
        return artist_songs_state.get()

    def clear_artist_songs_data(self):
        artist_songs_state.clear()

    def has_artist_songs_data(self):
        return bool(artist_songs_state.get())

    # ---------- Songs screen ----------
    def save_screen_state(self, screen_name, state_dict):
        """Перенаправляет в соответствующий менеджер по имени экрана."""
        if screen_name == 'songs':
            if state_dict.get('is_search_mode'):
                songs_state.save_search({
                    'query': state_dict.get('query', ''),
                    'results': state_dict.get('all_artists', []),
                    'search_page': state_dict.get('page', 0),
                })
            else:
                # Не перетираем _alphabet пустым/неполным state_dict.
                # Если нет ключа 'current_letter' и 'page' — считаем
                # состояние неполным и не сохраняем (иначе restore_state
                # прочитает page=None и сломает _ensure_valid_page).
                if ('current_letter' not in state_dict
                        and 'page' not in state_dict):
                    logger.debug(
                        "⏭️ save_screen_state('songs'): "
                        "state_dict не содержит current_letter/page — пропуск"
                    )
                    return
                # Дополняем недостающие поля значениями по умолчанию,
                # чтобы save_alphabet всегда писала валидный словарь.
                data = dict(state_dict)
                data.setdefault('current_letter', None)
                data.setdefault('current_language', 'ru')
                data.setdefault('page', 0)
                data.setdefault('total_artists', 0)
                data.setdefault('has_more', True)
                data.setdefault('scroll_position', 1.0)
                songs_state.save_alphabet(data)
        else:
            self._generic_save(screen_name, state_dict)

    def get_screen_state(self, screen_name, max_age=60):
        if screen_name == 'songs':
            data = songs_state.get_search()
            if data:
                return {
                    'is_search_mode': True,
                    'all_artists': data.get('results', []),
                    'page': data.get('search_page', 0),
                    'current_letter': None,
                }
            data = songs_state.get_alphabet()
            if data:
                return data
            return None
        return self._generic_get(screen_name, max_age)

    def clear_screen_state(self, screen_name):
        if screen_name == 'songs':
            songs_state.clear_all()
        else:
            self._generic_clear(screen_name)

    # ---------- Generic fallback ----------
    _generic_cache = {}
    _generic_timestamps = {}

    def _generic_save(self, name, data):
        self._generic_cache[name] = dict(data) if isinstance(data, dict) else data
        self._generic_timestamps[name] = time.time()

    def _generic_get(self, name, max_age=60):
        data = self._generic_cache.get(name)
        if data is None:
            return None
        age = time.time() - self._generic_timestamps.get(name, 0)
        if age > max_age:
            return None
        return data

    def _generic_clear(self, name):
        self._generic_cache.pop(name, None)
        self._generic_timestamps.pop(name, None)


screen_state = CompatScreenState()