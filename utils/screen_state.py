# utils/screen_state.py
"""
Управление состояниями экранов
Позволяет сохранять и восстанавливать состояние экрана при переходах
"""
import time
from kivy.logger import Logger

logger = Logger.getChild('ScreenState')


class ScreenStateManager:
    """Менеджер состояний экранов"""

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
        self._states = {}
        self._previous_screen = None
        self._pending_chord = None

        # ============ КЭШ СОСТОЯНИЙ ЭКРАНОВ ============
        self._screen_cache = {}
        self._last_update = {}

        # ============ ДАННЫЕ ЭКРАНА ПЕСЕН ИСПОЛНИТЕЛЯ ============
        self._artist_songs_data = {}

    def save_state(self, screen_name, state):
        self._states[screen_name] = state
        logger.debug(f"Сохранено состояние для {screen_name}: {state.keys() if state else 'None'}")

    def get_state(self, screen_name):
        return self._states.get(screen_name)

    def clear_state(self, screen_name):
        if screen_name in self._states:
            del self._states[screen_name]
            logger.debug(f"Очищено состояние для {screen_name}")

    def clear_all(self):
        self._states.clear()
        logger.debug("Очищены все состояния")

    def set_previous_screen(self, screen_name):
        old = self._previous_screen
        self._previous_screen = screen_name
        logger.info(f"✅ screen_state: предыдущий экран изменён: {old} → {screen_name}")

    def get_previous_screen(self):
        logger.info(f"📌 screen_state.get_previous_screen() = {self._previous_screen}")
        return self._previous_screen

    def set_pending_chord(self, chord_name):
        self._pending_chord = chord_name
        logger.debug(f"Установлен ожидающий аккорд: {chord_name}")

    def get_pending_chord(self):
        return self._pending_chord

    def clear_pending_chord(self):
        self._pending_chord = None

    # ============ КЭШ СОСТОЯНИЙ ЭКРАНОВ ============

    def cache_screen_data(self, screen_name, data):
        self._screen_cache[screen_name] = data
        self._last_update[screen_name] = time.time()
        logger.debug(f"📦 Закэшированы данные для {screen_name}: {len(data) if data else 0} элементов")

    def get_cached_screen_data(self, screen_name, max_age=60):
        if screen_name in self._screen_cache:
            age = time.time() - self._last_update.get(screen_name, 0)
            if age < max_age:
                logger.debug(f"📦 Данные для {screen_name} из кэша (возраст: {age:.1f}с)")
                return self._screen_cache[screen_name]
            else:
                logger.debug(f"⏳ Кэш для {screen_name} устарел (возраст: {age:.1f}с)")
        return None

    def invalidate_screen_cache(self, screen_name=None):
        if screen_name:
            if screen_name in self._screen_cache:
                del self._screen_cache[screen_name]
                if screen_name in self._last_update:
                    del self._last_update[screen_name]
                logger.debug(f"🗑️ Инвалидирован кэш для {screen_name}")
        else:
            self._screen_cache.clear()
            self._last_update.clear()
            logger.debug("🗑️ Инвалидирован кэш всех экранов")

    def is_cache_valid(self, screen_name, max_age=60):
        if screen_name in self._last_update:
            return (time.time() - self._last_update[screen_name]) < max_age
        return False

    # ============ СОХРАНЕНИЕ СОСТОЯНИЯ ЭКРАНОВ ============

    def save_screen_state(self, screen_name, state_dict):
        """
        Сохраняет полное состояние экрана
        """
        state_dict['_timestamp'] = time.time()
        cache_key = f'{screen_name}_state'
        self._screen_cache[cache_key] = state_dict
        self._last_update[cache_key] = time.time()
        logger.info(f"💾 СОХРАНЕНО состояние для {screen_name}: {list(state_dict.keys())}")
        logger.info(f"   → ключ кэша: {cache_key}")

    def get_screen_state(self, screen_name, max_age=60):
        """
        Возвращает сохранённое состояние экрана
        """
        cache_key = f'{screen_name}_state'
        logger.info(f"🔍 ПОИСК состояния для {screen_name}")
        logger.info(f"   → ключ: {cache_key}")
        logger.info(f"   → есть в кэше: {cache_key in self._screen_cache}")

        if cache_key in self._screen_cache:
            age = time.time() - self._last_update.get(cache_key, 0)
            logger.info(f"   → возраст: {age:.1f}с (макс: {max_age}с)")

            if age < max_age:
                state = self._screen_cache[cache_key]
                if '_timestamp' in state:
                    del state['_timestamp']
                logger.info(f"✅ СОСТОЯНИЕ НАЙДЕНО для {screen_name}")
                return state
            else:
                logger.info(f"⏳ Состояние для {screen_name} устарело")
        else:
            logger.info(f"❌ Состояние для {screen_name} НЕ НАЙДЕНО")

        return None

    def clear_screen_state(self, screen_name):
        cache_key = f'{screen_name}_state'
        if cache_key in self._screen_cache:
            del self._screen_cache[cache_key]
            if cache_key in self._last_update:
                del self._last_update[cache_key]
            logger.debug(f"🗑️ Очищено состояние для {screen_name}")

    # ============ ДАННЫЕ ЭКРАНА ПЕСЕН ИСПОЛНИТЕЛЯ ============

    def set_artist_songs_data(self, artist_name, scroll_position=1.0):
        """
        Сохраняет данные экрана песен исполнителя

        Args:
            artist_name: Имя исполнителя
            scroll_position: Позиция скролла (0-1)
        """
        self._artist_songs_data = {
            'artist_name': artist_name,
            'scroll_position': scroll_position,
            '_timestamp': time.time()
        }
        logger.info(f"📦 Сохранены данные ArtistSongs: {artist_name}, scroll={scroll_position:.2f}")

    def get_artist_songs_data(self):
        """
        Возвращает данные экрана песен исполнителя

        Returns:
            dict: {'artist_name': str, 'scroll_position': float} или пустой dict
        """
        if self._artist_songs_data:
            # Проверяем, не устарели ли данные (максимум 5 минут)
            timestamp = self._artist_songs_data.get('_timestamp', 0)
            if time.time() - timestamp < 300:  # 5 минут
                data = self._artist_songs_data.copy()
                if '_timestamp' in data:
                    del data['_timestamp']
                logger.info(f"📦 Получены данные ArtistSongs: {data.get('artist_name')}, scroll={data.get('scroll_position', 1.0):.2f}")
                return data
            else:
                logger.info("⏳ Данные ArtistSongs устарели")
        else:
            logger.info("❌ Данные ArtistSongs не найдены")
        return {}

    def clear_artist_songs_data(self):
        """
        Очищает данные экрана песен исполнителя
        """
        if self._artist_songs_data:
            self._artist_songs_data = {}
            logger.info("🗑️ Данные ArtistSongs очищены")

    def has_artist_songs_data(self):
        """
        Проверяет, есть ли сохранённые данные экрана песен исполнителя

        Returns:
            bool: True если данные есть и они валидны
        """
        if not self._artist_songs_data:
            return False
        timestamp = self._artist_songs_data.get('_timestamp', 0)
        return time.time() - timestamp < 300  # 5 минут


# Глобальный экземпляр
screen_state = ScreenStateManager()