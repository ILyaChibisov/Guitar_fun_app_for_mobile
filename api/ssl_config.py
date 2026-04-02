# api/ssl_config.py
import os
import certifi
import requests
from kivy.utils import platform
import logging
import urllib3

# Отключаем предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


def get_ca_bundle():
    """
    Возвращает путь к CA bundle
    """
    return None  # Возвращаем None, чтобы отключить проверку


def get_requests_session():
    """
    Возвращает сессию requests с настройками SSL
    """
    session = requests.Session()

    # Отключаем проверку SSL для разработки
    session.verify = False
    logger.warning("⚠️ SSL проверка ОТКЛЮЧЕНА - только для разработки!")

    return session