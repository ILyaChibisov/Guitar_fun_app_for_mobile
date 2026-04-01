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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)

    custom_bundle = os.path.join(project_dir, 'certs', 'ca_bundle.pem')

    if os.path.exists(custom_bundle):
        return custom_bundle

    return certifi.where()


def get_requests_session():
    """
    Возвращает сессию requests с настройками SSL
    """
    session = requests.Session()

    # ВРЕМЕННО: отключаем проверку SSL для разработки
    # ВНИМАНИЕ: Не используйте в продакшене!
    session.verify = False
    logger.warning("⚠️ SSL проверка ОТКЛЮЧЕНА - только для разработки!")

    return session