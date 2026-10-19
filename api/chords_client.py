# api/chords_client.py
"""
Клиент для загрузки аккордов с сервера.

- Без дискового кеша. Только RAM на время сессии.
- Все варианты одного аккорда грузятся ОДНИМ запросом → свайп мгновенный.
- Индекс (список доступных аккордов для тональности/типа) грузится один раз при первом запросе.
- Использует api.client.api для JWT/SSL/refresh.
"""
import threading
import urllib.parse
from typing import Dict, List, Optional

from kivy.logger import Logger
from kivy.clock import Clock

from api.client import api
from config.app_config import config


class ChordsClient:
    """Загружает аккорды с сервера + кеш в RAM (на время сессии)."""

    _instance = None

    def __init__(self):
        # (main_name, chord_type) -> list[variant_dict]
        self._cache: Dict[tuple, List[dict]] = {}
        # {tonality: {chord_type: [main_name, ...]}}
        self._index: Optional[Dict[str, Dict[str, List[str]]]] = None
        self._index_loading = False
        self._lock = threading.Lock()

    @classmethod
    def get(cls) -> "ChordsClient":
        if cls._instance is None:
            cls._instance = ChordsClient()
        return cls._instance

    # ============ АККОРД (все варианты) ============

    def get_chord(
        self,
        main_name: str,
        chord_type: str,
        on_success=None,
        on_error=None,
    ):
        """
        Возвращает список вариантов аккорда.
        - В RAM → on_success сразу (синхронно).
        - Иначе → HTTP в фоне → on_success через Clock.
        """
        key = (main_name, chord_type)

        with self._lock:
            cached = self._cache.get(key)
        if cached is not None:
            Logger.info(f"ChordsClient: {main_name}/{chord_type} из RAM")
            if on_success:
                on_success(cached)
            return

        def _worker():
            try:
                variants = self._fetch_chord(main_name, chord_type)
                if variants is None:
                    if on_error:
                        Clock.schedule_once(lambda dt: on_error("Не найдено"), 0)
                    return
                with self._lock:
                    self._cache[key] = variants
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(variants), 0)
            except Exception as e:
                Logger.error(f"ChordsClient.get_chord: {e}")
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(str(e)), 0)

        threading.Thread(target=_worker, daemon=True).start()

    def _fetch_chord(self, main_name: str, chord_type: str) -> Optional[List[dict]]:
        import urllib.parse
        main_enc = urllib.parse.quote(main_name, safe="")
        type_enc = urllib.parse.quote(chord_type, safe="")
        url = f"{config.API_BASE_URL}/chords/{main_enc}/{type_enc}"

        Logger.info(f"ChordsClient: GET {url}")
        result = api._request_sync(url, method="GET", include_auth=False)

        if not result or not isinstance(result, dict):
            return None
        variants = result.get("variants")
        if not variants:
            return None
        Logger.info(f"ChordsClient: получено {len(variants)} вариантов")
        return variants

    # ============ ИНДЕКС (список аккордов для селектора) ============

    def get_available_chords(
        self,
        tonality: str,
        chord_type: str,
        on_success=None,
        on_error=None,
    ):
        """
        Список main_name для (тональность, тип).
        Первый вызов грузит весь индекс с сервера (~50 КБ), дальше — из RAM.
        """
        if self._index is not None:
            result = (self._index.get(tonality, {}) or {}).get(chord_type, [])
            if on_success:
                on_success(result)
            return

        def _worker():
            try:
                index = self._fetch_index()
                with self._lock:
                    self._index = index
                result = (index.get(tonality, {}) or {}).get(chord_type, [])
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)
            except Exception as e:
                Logger.error(f"ChordsClient.get_available_chords: {e}")
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(str(e)), 0)

        threading.Thread(target=_worker, daemon=True).start()

    def _fetch_index(self) -> Dict[str, Dict[str, List[str]]]:
        with self._lock:
            if self._index is not None:
                return self._index

        url = f"{config.API_BASE_URL}/chords/index"
        Logger.info(f"ChordsClient: GET {url}")
        result = api._request_sync(url, method="GET", include_auth=False)

        if not result or not isinstance(result, dict):
            return {}

        index = result.get("index") or {}
        with self._lock:
            self._index = index

        Logger.info(f"ChordsClient: индекс загружен "
                    f"({sum(len(v) for v in index.values())} тональностей)")
        return index

    # ============ ПОИСК ПО СИНОНИМАМ ============

    def search_by_synonym(self, query: str, on_success=None, on_error=None):
        """
        Поиск по main_name и synonyms через GET /api/chords/search?query=...
        Возвращает список [{main_name, synonyms, tonality, chord_type, ...}].
        """
        def _worker():
            try:
                import urllib.parse
                q_enc = urllib.parse.quote(query, safe="")
                url = f"{config.API_BASE_URL}/chords/search?query={q_enc}"

                Logger.info(f"ChordsClient: GET {url}")
                result = api._request_sync(url, method="GET", include_auth=False)

                if not result or not isinstance(result, dict):
                    if on_success:
                        Clock.schedule_once(lambda dt: on_success([]), 0)
                    return

                items = result.get("results") or []
                Logger.info(f"ChordsClient.search_by_synonym('{query}'): {len(items)} результатов")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(items), 0)
            except Exception as e:
                Logger.error(f"ChordsClient.search_by_synonym: {e}")
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(str(e)), 0)

        threading.Thread(target=_worker, daemon=True).start()

    # ============ ИНВАЛИДАЦИЯ ============

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._index = None
        Logger.info("ChordsClient: кеш очищен")


def get_chords_client() -> ChordsClient:
    return ChordsClient.get()