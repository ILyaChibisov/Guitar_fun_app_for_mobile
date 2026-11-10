# state/chords_state.py
"""
Состояние экрана «Аккорды».
Хранит текущий выбор, кэш просканированных модулей и флаг готовности UI.
"""
import time
import threading
from kivy.logger import Logger

logger = Logger.getChild('State:Chords')


class ChordsStateManager:
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
        self._lock = threading.RLock()

        # --- Текущий выбор ---
        self._data = {
            'current_tonality': 'A',
            'current_type': 'Major',
            'current_chord_name': 'A',
            'current_variant_index': 0,
            'current_mode': 'finger',
        }
        self._timestamp = 0
        self._ttl = 3600  # 1 час

        # --- Кэш просканированных модулей ---
        # Список словарей (module, name, short_name, variant, type, description, path)
        self._all_chords = []
        self._scan_done = False

        # --- Кэш UI ---
        self._slides_built = False       # слайды уже созданы
        self._slides_theme = None        # для какой темы созданы
        self._slides_chord = None        # для какого аккорда созданы
        self._slides_variants = None     # список вариантов

    # ---------- Состояние выбора ----------

    def save(self, data: dict):
        with self._lock:
            self._data = dict(data)
            self._timestamp = time.time()
        logger.debug(
            f"💾 Chords: ton={data.get('current_tonality')}, "
            f"type={data.get('current_type')}, "
            f"chord={data.get('current_chord_name')}, "
            f"mode={data.get('current_mode')}"
        )

    def get(self, allow_stale: bool = False):
        with self._lock:
            if not self._data:
                return None
            age = time.time() - self._timestamp
            if age > self._ttl and not allow_stale:
                return None
            return dict(self._data)

    def invalidate(self):
        with self._lock:
            self._data = {}
            self._timestamp = 0
            self._slides_built = False
        logger.debug("🗑️ Chords инвалидирован")

    # ---------- Кэш сканирования ----------

    def get_all_chords(self):
        with self._lock:
            return list(self._all_chords)

    def set_all_chords(self, chords_list):
        with self._lock:
            self._all_chords = list(chords_list)
            self._scan_done = True
        logger.info(f"📦 Chords: закэшировано {len(self._all_chords)} модулей")

    def is_scan_done(self):
        with self._lock:
            return self._scan_done

    # ---------- Кэш UI (слайды) ----------

    def mark_slides_built(self, theme_id, chord_name, variants):
        with self._lock:
            self._slides_built = True
            self._slides_theme = theme_id
            self._slides_chord = chord_name
            self._slides_variants = variants  # список dict (с module/server_data)

    def can_reuse_slides(self, theme_id, chord_name, variants):
        """Можно ли переиспользовать уже построенные слайды?"""
        with self._lock:
            if not self._slides_built:
                return False
            if self._slides_theme != theme_id:
                return False
            if self._slides_chord != chord_name:
                return False
            if len(self._slides_variants or []) != len(variants or []):
                return False
            return True

    def get_slides_variants(self):
        with self._lock:
            return list(self._slides_variants) if self._slides_variants else []

    def invalidate_slides(self):
        with self._lock:
            self._slides_built = False
            self._slides_theme = None
            self._slides_chord = None
            self._slides_variants = None


chords_state = ChordsStateManager()