# utils/perf.py
"""
Лёгкий профайлер для экранов.
- context-менеджер perf(label) — замеряет блок.
- PerfRegistry — накапливает min/avg/max/count по метке.
- Декоратор @timed("label") — для методов.
- Без внешних зависимостей, работает на Android (time.perf_counter).
"""
import time
import threading
from collections import defaultdict
from kivy.logger import Logger

logger = Logger.getChild('Perf')


class PerfRegistry:
    """Накапливает статистику по меткам."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._lock = threading.Lock()
        self._stats = defaultdict(lambda: {'count': 0, 'total': 0.0,
                                           'min': float('inf'),
                                           'max': 0.0})

    def add(self, label, dt_ms):
        with self._lock:
            s = self._stats[label]
            s['count'] += 1
            s['total'] += dt_ms
            if dt_ms < s['min']:
                s['min'] = dt_ms
            if dt_ms > s['max']:
                s['max'] = dt_ms

    def dump(self, prefix=''):
        with self._lock:
            items = sorted(self._stats.items())
            stats = [(k, dict(v)) for k, v in items]
            self._stats.clear()

        if not stats:
            return

        logger.info(f"{prefix} ===== PERF SUMMARY =====")
        for label, s in stats:
            avg = s['total'] / s['count'] if s['count'] else 0.0
            logger.info(
                f"{prefix} {label:<40} n={s['count']:<3} "
                f"min={s['min']:7.2f}ms  avg={avg:7.2f}ms  max={s['max']:7.2f}ms"
            )
        logger.info(f"{prefix} ===== END PERF =====")

    def reset(self):
        with self._lock:
            self._stats.clear()


perf_registry = PerfRegistry()


class _Timer:
    __slots__ = ('label', 't0', 'log_every')

    def __init__(self, label, log_every=True):
        self.label = label
        self.t0 = time.perf_counter()
        self.log_every = log_every

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        dt_ms = (time.perf_counter() - self.t0) * 1000.0
        perf_registry.add(self.label, dt_ms)
        if self.log_every:
            status = 'OK' if exc is None else f'ERR({exc_type.__name__})'
            logger.info(f"⏱ [{self.label}] {dt_ms:7.2f} ms  {status}")
        return False


def perf(label, log_every=True):
    """Контекст-менеджер: with perf('label'): ..."""
    return _Timer(label, log_every=log_every)


def timed(label, log_every=True):
    """Декоратор: @timed('label') над методом."""
    def deco(func):
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                dt_ms = (time.perf_counter() - t0) * 1000.0
                perf_registry.add(label, dt_ms)
                if log_every:
                    logger.info(f"⏱ [{label}] {dt_ms:7.2f} ms")
        return wrapper
    return deco