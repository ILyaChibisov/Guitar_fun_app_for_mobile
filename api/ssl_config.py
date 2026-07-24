# api/ssl_config.py
import os
import requests
from kivy.utils import platform
import logging
import urllib3

# Отключаем только предупреждения, НЕ проверку SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def get_requests_session():
    """
    Возвращает сессию requests с настройками SSL
    Универсальная версия для Android и Windows
    """
    session = requests.Session()

    # На Android используем системные сертификаты
    if platform == 'android':
        try:
            # Android доверяет системным сертификатам
            session.verify = True
            logger.info("✅ Android: SSL проверка включена (системные сертификаты)")
            return session
        except Exception as e:
            logger.warning(f"⚠️ Android SSL ошибка: {e}")

    # На Windows используем certifi
    try:
        import certifi
        session.verify = certifi.where()
        logger.info(f"✅ Windows: SSL проверка включена (certifi)")
        return session
    except ImportError:
        logger.warning("⚠️ certifi не найден, пробуем системные сертификаты")

    # Fallback: системные сертификаты
    try:
        session.verify = True
        logger.info("✅ SSL проверка включена (системные)")
        return session
    except:
        # Последний вариант — отключаем проверку (НЕ РЕКОМЕНДУЕТСЯ)
        session.verify = False
        logger.warning("⚠️ SSL проверка ОТКЛЮЧЕНА (только для отладки)")
        return session