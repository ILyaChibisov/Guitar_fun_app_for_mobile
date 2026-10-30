# api/ssl_config.py
"""
Настройка requests.Session для Android и Windows.

Ключевые моменты:
- Настраиваем HTTPAdapter с контролем пула соединений.
- Android: используем системные сертификаты (verify=True).
- Windows: используем certifi.
- НЕ отключаем SSL глобально.
"""
import requests
from requests.adapters import HTTPAdapter
from kivy.utils import platform
from kivy.logger import Logger

import urllib3

# Отключаем только предупреждения (не проверку!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_requests_session() -> requests.Session:
    """
    Возвращает сессию requests с настройками SSL и пула соединений.
    Универсальная версия для Android и Windows.
    """
    session = requests.Session()

    # ============ ПУЛ СОЕДИНЕНИЙ ============
    # Контролируем размер пула явно, чтобы избежать ситуаций,
    # когда keep-alive соединения закрываются сервером,
    # а клиент пытается их переиспользовать.
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=10,
        max_retries=0,  # Ретраи делаем на уровне приложения
        pool_block=False,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # ============ ЗАГОЛОВКИ ПО УМОЛЧАНИЮ ============
    session.headers.update({
        "User-Agent": "GuitarFuns/1.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        # ВАЖНО: keep-alive оставляем включённым.
        # Проблему "мёртвых" сокетов решаем через api.reset_session()
        # при возврате из фона (on_resume) и ретрай в client.py.
        "Connection": "keep-alive",
    })

    # ============ SSL НАСТРОЙКИ ============
    if platform == "android":
        # Android: доверяем системным сертификатам.
        # Если сервер использует валидный публичный сертификат
        # (Let's Encrypt, DigiCert и т.п.) — этого достаточно.
        session.verify = True
        Logger.info("SSL: Android — системные сертификаты (verify=True)")
    else:
        # Windows / Linux / macOS: используем certifi.
        try:
            import certifi
            session.verify = certifi.where()
            Logger.info(f"SSL: {platform} — certifi ({certifi.where()})")
        except ImportError:
            Logger.warning("SSL: certifi не найден, используем системные сертификаты")
            session.verify = True

    return session


def reset_requests_session(session: requests.Session) -> requests.Session:
    """
    Сбрасывает все соединения в пуле сессии.
    Полезно вызывать при возврате приложения из фона (on_resume),
    чтобы избежать использования "мёртвых" keep-alive сокетов.

    Возвращает ту же сессию (для удобства).
    """
    try:
        session.close()  # закрывает все соединения в пуле
        # Пересоздаём адаптеры (сессия остаётся той же, но пул пустой)
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0,
            pool_block=False,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        Logger.info("SSL: пул соединений сброшен")
    except Exception as e:
        Logger.error(f"SSL: ошибка сброса пула — {e}")
    return session