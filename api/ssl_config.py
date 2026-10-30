# api/ssl_config.py
"""
Настройка requests.Session для Android и Windows.

- HTTPAdapter с контролем пула соединений.
- urllib3 Retry: connect-ошибки и 5xx.
- ReadTimeout ретраится вручную в api/client.py.
- Android: системные сертификаты (verify=True).
- Windows: certifi.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from kivy.utils import platform
from kivy.logger import Logger

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _make_adapter() -> HTTPAdapter:
    retry = Retry(
        total=0,          # общий лимит не нужен
        connect=2,        # 2 ретрая на connect
        read=0,           # read-таймауты ретраим в client.py
        status=0,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST", "PUT", "PATCH", "DELETE"]),
        raise_on_status=False,
    )
    return HTTPAdapter(
        pool_connections=10,
        pool_maxsize=10,
        max_retries=retry,
        pool_block=False,
    )


def get_requests_session() -> requests.Session:
    session = requests.Session()

    adapter = _make_adapter()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    session.headers.update({
        "User-Agent": "GuitarFuns/1.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })

    if platform == "android":
        session.verify = True
        Logger.info("SSL: Android — системные сертификаты (verify=True)")
    else:
        try:
            import certifi
            session.verify = certifi.where()
            Logger.info(f"SSL: {platform} — certifi ({certifi.where()})")
        except ImportError:
            Logger.warning("SSL: certifi не найден, используем системные сертификаты")
            session.verify = True

    return session


def reset_requests_session(session: requests.Session) -> requests.Session:
    try:
        session.close()
        adapter = _make_adapter()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        Logger.info("SSL: пул соединений сброшен")
    except Exception as e:
        Logger.error(f"SSL: ошибка сброса пула — {e}")
    return session