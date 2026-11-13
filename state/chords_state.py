# state/chords_state.py
"""
Состояние экрана «Аккорды».

Хранит:
  - текущий выбор (тональность, тип, аккорд, вариант, режим);
  - кэш просканированных ЛОКАЛЬНЫХ модулей (в пакете chords/);
  - кэш UI-слайдов (чтобы не пересобирать при возврате на экран).

Локально в пакете chords/ оставлен ТОЛЬКО A Major (все варианты).
Всё остальное (другие тональности, другие типы) грузится с сервера
и в этом менеджере НЕ кэшируется — им управляет сам экран.
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

        # --- Кэш просканированных ЛОКАЛЬНЫХ модулей ---
        self._all_chords = []
        self._scan_done = False

        # --- Кэш UI ---
        self._slides_built = False
        self._slides_theme = None
        self._slides_chord = None
        self._slides_variants = None

    # ============================================================
    # Состояние выбора
    # ============================================================

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
        """Сбрасывает текущий выбор и кэш слайдов (но НЕ кэш сканирования)."""
        with self._lock:
            self._data = {}
            self._timestamp = 0
            self._reset_slides_locked()
        logger.debug("🗑️ Chords: выбор и слайды инвалидированы")

    # ============================================================
    # Кэш сканирования (локальные модули)
    # ============================================================

    def get_all_chords(self):
        with self._lock:
            return list(self._all_chords)

    def set_all_chords(self, chords_list):
        with self._lock:
            self._all_chords = list(chords_list)
            self._scan_done = True
            self._reset_slides_locked()
        logger.info(f"📦 Chords: закэшировано {len(self._all_chords)} локальных модулей")

    def is_scan_done(self):
        with self._lock:
            return self._scan_done

    def invalidate_scan(self):
        """Сбрасывает кэш сканирования (после удаления части модулей)."""
        with self._lock:
            self._all_chords = []
            self._scan_done = False
            self._reset_slides_locked()
        logger.debug("🗑️ Chords: кэш сканирования сброшен")

    # ============================================================
    # Кэш UI (слайды)
    # ============================================================

    def mark_slides_built(self, theme_id, chord_name, variants):
        with self._lock:
            self._slides_built = True
            self._slides_theme = theme_id
            self._slides_chord = chord_name
            self._slides_variants = variants

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
            self._reset_slides_locked()
        logger.debug("🗑️ Chords: кэш слайдов сброшен")

    # ============================================================
    # Полный сброс (logout / смена пользователя / отладка)
    # ============================================================

    def clear_all(self):
        """Полный сброс: выбор + сканирование + слайды."""
        with self._lock:
            self._data = {
                'current_tonality': 'A',
                'current_type': 'Major',
                'current_chord_name': 'A',
                'current_variant_index': 0,
                'current_mode': 'finger',
            }
            self._timestamp = 0
            self._all_chords = []
            self._scan_done = False
            self._reset_slides_locked()
        logger.info("🗑️ Chords: полный сброс состояния")

    # ============================================================
    # Внутренние хелперы
    # ============================================================

    def _reset_slides_locked(self):
        """Сброс кэша слайдов. Вызывать только под self._lock."""
        self._slides_built = False
        self._slides_theme = None
        self._slides_chord = None
        self._slides_variants = None


chords_state = ChordsStateManager()