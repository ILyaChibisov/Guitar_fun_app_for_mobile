# state/base.py
"""
Базовый класс для всех менеджеров состояний.
Общий кэш + TTL + потокобезопасность.
"""
import time
import threading
from kivy.logger import Logger

logger = Logger.getChild('State')


class BaseStateManager:
    """Базовый менеджер состояния с TTL-кэшем."""

    def __init__(self, name: str, default_ttl: int = 60):
        self._name = name
        self._ttl = default_ttl
        self._cache = {}
        self._last_update = {}
        self._lock = threading.RLock()
        self._logger = Logger.getChild(f'State:{name}')

    # -------- Основные операции --------

    def save(self, key: str, data: dict, ttl: int = None):
        """
        Сохраняет данные по ключу.
        data копируется, чтобы избежать мутаций снаружи.
        """
        ttl = ttl if ttl is not None else self._ttl
        with self._lock:
            self._cache[key] = {
                'data': dict(data) if isinstance(data, dict) else data,
                'timestamp': time.time(),
                'ttl': ttl,
            }
            self._last_update[key] = time.time()
        self._logger.debug(f"💾 {self._name}.save({key}) → {len(data) if hasattr(data, '__len__') else 'obj'}")

    def get(self, key: str, max_age: int = None, allow_stale: bool = False) -> dict | None:
        """
        Возвращает данные, если они не устарели.
        allow_stale=True — вернуть даже устаревшие (для мгновенного показа).
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._logger.debug(f"❌ {self._name}.get({key}) — нет в кэше")
                return None

            age = time.time() - entry['timestamp']
            ttl = max_age if max_age is not None else entry['ttl']

            if age >= ttl and not allow_stale:
                self._logger.debug(f"⏳ {self._name}.get({key}) — устарело ({age:.1f}с > {ttl}с)")
                return None

            data = entry['data']
            if isinstance(data, dict):
                data = dict(data)  # защита от мутаций
            return data

    def is_valid(self, key: str, max_age: int = None) -> bool:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            age = time.time() - entry['timestamp']
            ttl = max_age if max_age is not None else entry['ttl']
            return age < ttl

    def age(self, key: str) -> float | None:
        """Возвращает возраст данных в секундах или None, если нет в кэше."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            return time.time() - entry['timestamp']

    def invalidate(self, key: str = None):
        """Удаляет конкретный ключ или всё."""
        with self._lock:
            if key is None:
                self._cache.clear()
                self._last_update.clear()
                self._logger.debug(f"🗑️ {self._name}: кэш полностью очищен")
            else:
                self._cache.pop(key, None)
                self._last_update.pop(key, None)
                self._logger.debug(f"🗑️ {self._name}: удалён ключ {key}")

    def clear(self):
        self.invalidate(None)