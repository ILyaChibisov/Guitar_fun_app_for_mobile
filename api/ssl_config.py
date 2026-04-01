# api/ssl_config.py
import os
import certifi
import requests
from kivy.utils import platform
import logging

logger = logging.getLogger(__name__)


def get_ca_bundle():
    """
    Возвращает путь к CA bundle
    """
    # Для Windows, Linux, macOS используем certifi
    try:
        ca_path = certifi.where()
        if os.path.exists(ca_path):
            return ca_path
    except:
        pass

    # Для Android
    if platform == 'android':
        try:
            # Пробуем системный путь на Android
            if os.path.exists('/system/etc/security/cacerts'):
                return '/system/etc/security/cacerts'
        except:
            pass

    # Пробуем кастомный путь
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    custom_bundle = os.path.join(project_dir, 'certs', 'ca_bundle.pem')

    if os.path.exists(custom_bundle):
        return custom_bundle

    return None


def get_requests_session():
    """
    Возвращает сессию requests с настройками SSL
    """
    session = requests.Session()

    ca_bundle = get_ca_bundle()
    if ca_bundle:
        session.verify = ca_bundle
        logger.info(f"🔒 SSL: используем {ca_bundle}")
    else:
        # Для разработки - временно отключаем проверку
        session.verify = False
        logger.warning("⚠️ SSL: проверка отключена (только для разработки)")

    return session