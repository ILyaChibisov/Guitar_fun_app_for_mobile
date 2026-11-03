# state/subscription_state.py
"""
Единое состояние подписки.
Хранит последний известный статус, уведомляет слушателей.

Ключевые изменения (Этап 4 + фикс):
- subscription_end_date теперь берётся из status_data (если есть),
  а не только из user_data. Это устраняет «залипшие» дни,
  когда api.user_data закэширован со старым значением.
"""
import threading
import time
from datetime import datetime
from kivy.logger import Logger

logger = Logger.getChild('State:Subscription')


class SubscriptionState:
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

        # Последний известный статус
        self._status = None            # 'active' | 'limited' | 'unlimited' | None
        self._days_left = 0
        self._seconds_left = 0
        self._is_admin = False
        self._subscription_end_date = None   # datetime | None
        self._last_check_ts = 0

        # Слушатели
        self._listeners = []

    # ---------- Геттеры ----------

    @property
    def status(self):
        return self._status

    @property
    def days_left(self):
        return self._days_left

    @property
    def seconds_left(self):
        return self._seconds_left

    @property
    def is_admin(self):
        return self._is_admin

    @property
    def subscription_end_date(self):
        return self._subscription_end_date

    @property
    def last_check_age(self):
        """Сколько секунд назад обновляли статус."""
        return time.time() - self._last_check_ts

    def is_active(self):
        """Активна ли подписка (или админ)."""
        return self._status in ("active", "unlimited")

    def is_limited(self):
        return self._status == "limited"

    def is_exhausted(self):
        """Подписка закончилась — нужна жёсткая блокировка."""
        return self._status == "exhausted"

    def has_any_access(self):
        """Есть ли доступ прямо сейчас (активна или админ)."""
        return self._status in ("active", "unlimited")

    # ---------- Обновление ----------

    def update_from_response(self, status_data: dict, user_data: dict | None = None):
        """
        Принимает ответ /users/me/subscription (и опционально /users/me).
        status: 'active' | 'exhausted' | 'unlimited'
        """
        if not isinstance(status_data, dict):
            return

        with self._lock:
            old_status = self._status
            old_days = self._days_left
            old_seconds = self._seconds_left
            old_end = self._subscription_end_date

            self._status = status_data.get("status")
            self._is_admin = bool(status_data.get("is_admin", False))

            if self._status == "active":
                self._days_left = int(status_data.get("days_left", 0) or 0)
                self._seconds_left = 0
            elif self._status == "exhausted":
                self._days_left = 0
                self._seconds_left = 0
            elif self._status == "unlimited":
                self._is_admin = True
                self._days_left = 0
                self._seconds_left = 0
            else:
                self._days_left = 0
                self._seconds_left = 0

            # ---- subscription_end_date: сначала status_data, потом user_data ----
            end_str = status_data.get("subscription_end_date")
            if not end_str and user_data and isinstance(user_data, dict):
                end_str = user_data.get("subscription_end_date")

            if end_str:
                try:
                    self._subscription_end_date = datetime.fromisoformat(
                        str(end_str).replace("Z", "+00:00")
                    )
                except Exception:
                    self._subscription_end_date = None
            else:
                self._subscription_end_date = None

            self._last_check_ts = time.time()

            changed = (
                    old_status != self._status
                    or old_days != self._days_left
                    or old_seconds != self._seconds_left
                    or old_end != self._subscription_end_date
            )

        if changed:
            logger.info(
                f"📊 Subscription: status={self._status}, "
                f"days_left={self._days_left}, "
                f"admin={self._is_admin}, "
                f"end={self._subscription_end_date}"
            )
            self._notify()

    # ---------- Слушатели ----------

    def add_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify(self):
        snapshot = {
            "status": self._status,
            "days_left": self._days_left,
            "seconds_left": self._seconds_left,
            "is_admin": self._is_admin,
            "subscription_end_date": self._subscription_end_date,
        }
        for cb in list(self._listeners):
            try:
                cb(snapshot)
            except Exception as e:
                logger.error(f"Ошибка в subscription-listener: {e}")

    def reset(self):
        """Сброс при logout."""
        with self._lock:
            self._status = None
            self._days_left = 0
            self._seconds_left = 0
            self._is_admin = False
            self._subscription_end_date = None
            self._last_check_ts = 0
        self._notify()


subscription_state = SubscriptionState()