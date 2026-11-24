# state/base_term_detail_state.py
"""
Состояние экрана «Детали термина».
Кэширует название, описание, размер шрифта и позицию скролла по term_id (LRU до 20 терминов).
"""
from kivy.logger import Logger
from state.base import BaseStateManager

logger = Logger.getChild('State:TermDetail')


class TermDetailStateManager(BaseStateManager):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__(name='TermDetail', default_ttl=600)
        self._initialized = True
        self._current_term_id = None
        self._max_cached_terms = 20
        self._lru_order = []

    def _touch_lru(self, key: str):
        if key in self._lru_order:
            self._lru_order.remove(key)
        self._lru_order.append(key)
        while len(self._lru_order) > self._max_cached_terms:
            oldest = self._lru_order.pop(0)
            self.invalidate(oldest)

    def save_term_state(self, term_id: int, state_data: dict):
        if not term_id:
            return
        key = str(term_id)
        self._current_term_id = term_id
        self.save(key, state_data, ttl=600)
        self._touch_lru(key)

    def get_term_state(self, term_id: int) -> dict | None:
        if not term_id:
            return None
        key = str(term_id)
        data = self.get(key, allow_stale=False)
        if data is not None:
            self._touch_lru(key)
        return data


term_detail_state = TermDetailStateManager()
