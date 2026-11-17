# api/chords_client.py
"""
Клиент для загрузки аккордов с сервера.

- Кеш в RAM (на время сессии) + дисковый кеш для batch-запросов.
- Batch-запрос: все аккорды песни одним запросом (POST /chords/batch).
- Индекс (список доступных аккордов для тональности/типа) грузится один раз при первом запросе.
- Использует api.client.api для JWT/SSL/refresh.

Потоки: единый ThreadPoolExecutor(max_workers=4).
"""
import json
import os
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from kivy.logger import Logger
from kivy.clock import Clock

from api.client import api
from config.app_config import config


class ChordsClient:
    """Загружает аккорды с сервера + кеш в RAM/на диске."""

    _instance = None
    _MAX_WORKERS = 4

    def __init__(self):
        # (main_name, chord_type) -> list[variant_dict]
        self._cache: Dict[tuple, List[dict]] = {}
        # {tonality: {chord_type: [main_name, ...]}}
        self._index: Optional[Dict[str, Dict[str, List[str]]]] = None
        self._index_loading = False
        self._lock = threading.Lock()

        # Кеш резолва (short_name -> (main_name, chord_type))
        self._resolve_cache: Dict[str, tuple] = {}

        # Пул потоков
        self._executor = ThreadPoolExecutor(
            max_workers=self._MAX_WORKERS,
            thread_name_prefix="chords_",
        )

        # Дисковый кеш для batch-запросов
        self._disk_cache_dir = os.path.join(config.CACHE_DIR, "chords_batch")
        os.makedirs(self._disk_cache_dir, exist_ok=True)

    @classmethod
    def get(cls) -> "ChordsClient":
        if cls._instance is None:
            cls._instance = ChordsClient()
        return cls._instance

    # ============ BATCH (для экрана песни) ============

    def get_chords_batch(
            self,
            chord_pairs: List[Dict[str, str]],
            on_success=None,
            on_error=None,
    ):
        """
        Загружает все варианты для списка аккордов.
        """
        if not chord_pairs:
            if on_success:
                on_success({"chords": {}, "not_found": []})
            return

        # 1. Формируем ключ для дискового кеша
        items_sorted = sorted(chord_pairs, key=lambda x: (x["main_name"], x["chord_type"]))
        cache_key = self._make_cache_key(items_sorted)
        cache_file = os.path.join(self._disk_cache_dir, f"{cache_key}.json")

        # 2. Проверяем дисковый кеш
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                Logger.info(f"ChordsClient: batch из диска ({len(cached_data.get('chords', {}))} групп)")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached_data), 0)
                return
            except Exception as e:
                Logger.warning(f"ChordsClient: ошибка чтения кеша {e}")

        # 3. Идём на сервер
        def _worker():
            try:
                url = f"{config.API_BASE_URL}/chords/batch"
                payload = {"chords": chord_pairs}

                Logger.info(f"ChordsClient: POST {url} ({len(chord_pairs)} аккордов)")
                result = api._request_sync(
                    url, method="POST", data=payload, include_auth=False
                )

                if not result or not isinstance(result, dict):
                    if on_error:
                        Clock.schedule_once(lambda dt: on_error("Ошибка сервера"), 0)
                    return

                # 4. Сохраняем на диск
                try:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, default=str)
                except Exception as e:
                    Logger.warning(f"ChordsClient: не удалось сохранить кеш {e}")

                # 5. Отдаём в UI
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)

            except Exception as e:
                Logger.error(f"ChordsClient.get_chords_batch: {e}")
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(str(e)), 0)

        self._executor.submit(_worker)

    # ============ ИНДЕКС (для резолвинга имён и списка аккордов) ============

    def get_index_sync(self) -> Dict[str, Dict[str, List[str]]]:
        """Синхронно загружает индекс."""
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
        return index

    def get_available_chords(
            self,
            tonality: str,
            chord_type: str,
            on_success=None,
            on_error=None,
    ):
        """Список main_name для (тональность, тип). Используется в ChordsScreen."""
        if self._index is not None:
            result = (self._index.get(tonality, {}) or {}).get(chord_type, [])
            if on_success:
                on_success(result)
            return

        def _worker():
            try:
                index = self.get_index_sync()
                result = (index.get(tonality, {}) or {}).get(chord_type, [])
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)
            except Exception as e:
                Logger.error(f"ChordsClient.get_available_chords: {e}")
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(str(e)), 0)

        self._executor.submit(_worker)

    def resolve_chord(self, short_name: str) -> tuple:
        """
        Находит правильную пару (main_name, chord_type) для сервера.
        """
        short_name = (short_name or "").strip()
        if not short_name:
            return ("", "Major")

        # Ключ для кеша всегда с прямым слешем
        cache_key = short_name.replace('\\', '/')
        with self._lock:
            if cache_key in self._resolve_cache:
                return self._resolve_cache[cache_key]

        index = self.get_index_sync()
        if not index:
            res = self._fallback_resolve(short_name)
            with self._lock:
                self._resolve_cache[cache_key] = res
            return res

        short_norm = cache_key.lower()
        found_res = None

        for tonality, types in index.items():
            for chord_type, names in types.items():
                for name in names:
                    if name.lower().replace('\\', '/') == short_norm:
                        found_res = (name, chord_type)
                        break
                if found_res: break
            if found_res: break

        if not found_res:
            found_res = self._fallback_resolve(short_name)

        with self._lock:
            self._resolve_cache[cache_key] = found_res
        return found_res

    def _fallback_resolve(self, short_name: str) -> tuple:
        # Приводим к формату базы (обратный слеш)
        normalized = short_name.replace('/', '\\')
        if normalized.endswith("m") and not normalized.endswith("maj"):
            return (normalized, "Minor")
        return (normalized, "Major")

    # ============ ПОИСК ПО СИНОНИМАМ ============

    def search_by_synonym(self, query: str, on_success=None, on_error=None):
        """
        Поиск по main_name и synonyms через GET /api/chords/search?query=...
        """

        def _worker():
            try:
                # Принудительно приводим слеш к формату базы (обратный)
                norm_query = query.replace('/', '\\')

                q_enc = urllib.parse.quote(norm_query, safe="")
                url = f"{config.API_BASE_URL}/chords/search?query={q_enc}"

                Logger.info(f"ChordsClient: GET {url}")
                result = api._request_sync(url, method="GET", include_auth=False)

                if not result or not isinstance(result, dict):
                    if on_success:
                        Clock.schedule_once(lambda dt: on_success([]), 0)
                    return

                items = result.get("results") or []
                Logger.info(f"ChordsClient.search_by_synonym('{norm_query}'): {len(items)} результатов")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(items), 0)
            except Exception as e:
                Logger.error(f"ChordsClient.search_by_synonym: {e}")
                if on_error:
                    Clock.schedule_once(lambda dt: on_error(str(e)), 0)

        self._executor.submit(_worker)

    # ============ АККОРД (все варианты) ============

    def get_chord(
            self,
            main_name: str,
            chord_type: str,
            on_success=None,
            on_error=None,
    ):
        """Возвращает список вариантов аккорда (одним запросом)."""
        key = (main_name, chord_type)

        with self._lock:
            cached = self._cache.get(key)
        if cached is not None:
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

        self._executor.submit(_worker)

    def _fetch_chord(self, main_name: str, chord_type: str) -> Optional[List[dict]]:
        # Принудительно приводим слеш к формату базы (обратный)
        main_name = main_name.replace('/', '\\')

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
        return variants

    # ============ УТИЛИТЫ ============

    def _make_cache_key(self, items_sorted: List[Dict[str, str]]) -> str:
        """Хеш от списка аккордов для имени файла кеша."""
        import hashlib
        raw = json.dumps(items_sorted, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._index = None
            self._resolve_cache.clear()
        Logger.info("ChordsClient: кеш очищен")

    def shutdown(self):
        try:
            self._executor.shutdown(wait=False)
            Logger.info("ChordsClient: пул потоков остановлен")
        except Exception as e:
            Logger.error(f"ChordsClient.shutdown: {e}")


def get_chords_client() -> ChordsClient:
    return ChordsClient.get()