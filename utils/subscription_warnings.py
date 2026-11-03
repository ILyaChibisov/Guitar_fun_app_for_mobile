# utils/subscription_warnings.py
"""
Показывает предупреждения о подписке, но не чаще, чем раз в N.
Хранит последние показанные timestamp в файле кэша.
"""
import json
import os
import time
from kivy.logger import Logger
from kivy.clock import Clock
from config.app_config import config

logger = Logger.getChild('SubWarnings')

WARN_FILE = os.path.join(config.CACHE_DIR, 'subscription_warnings.json')

# анти-спам: не чаще, чем раз в N секунд
COOLDOWN_DAYS_WARN = 24 * 60 * 60       # предупреждение «N дней до конца» — раз в сутки
COOLDOWN_SECONDS_WARN = 5 * 60          # предупреждение «N мин осталось» — раз в 5 минут


class SubscriptionWarnings:
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
        self._data = self._load()

    def _load(self) -> dict:
        try:
            if os.path.exists(WARN_FILE):
                with open(WARN_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Не удалось загрузить warning-state: {e}")
        return {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(WARN_FILE), exist_ok=True)
            with open(WARN_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f)
        except Exception as e:
            logger.warning(f"Не удалось сохранить warning-state: {e}")

    def _can_show(self, key: str, cooldown: int) -> bool:
        last = self._data.get(key, 0)
        if time.time() - last < cooldown:
            return False
        self._data[key] = time.time()
        self._save()
        return True

    # ---------- Публичные проверки ----------

    def maybe_show_days_warning(self, days_left: int):
        """Предупреждение «Осталось N дн.» — раз в сутки."""
        if days_left <= 0 or days_left > 3:
            return
        if not self._can_show("days_warning", COOLDOWN_DAYS_WARN):
            return
        from utils.notifications import notify
        Clock.schedule_once(
            lambda dt: notify.warning(f"⏳ Подписка заканчивается. Осталось {days_left} дн."),
            0,
        )
        logger.info(f"⚠️ Показано предупреждение: осталось {days_left} дн.")

    def maybe_show_seconds_warning(self, seconds_left: int):
        """Предупреждение «Осталось N мин.» — раз в 5 минут."""
        if seconds_left <= 0 or seconds_left > 60:
            return
        if not self._can_show("seconds_warning", COOLDOWN_SECONDS_WARN):
            return
        mins = max(1, seconds_left // 60)
        from utils.notifications import notify
        Clock.schedule_once(
            lambda dt: notify.warning(f"⏳ Осталось {mins} мин. бесплатного доступа"),
            0,
        )
        logger.info(f"⚠️ Показано предупреждение: осталось {seconds_left} сек.")

    def reset_on_new_day(self):
        """Сбрасываем суточные предупреждения при смене дня (для тестов)."""
        self._data.pop("days_warning", None)
        self._data.pop("seconds_warning", None)
        self._save()


subscription_warnings = SubscriptionWarnings()