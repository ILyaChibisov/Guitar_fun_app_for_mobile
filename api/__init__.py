# api/__init__.py
"""
Модуль для работы с API
"""
from .client import api
from .ssl_config import get_requests_session, get_ca_bundle
from .network_handler import network_manager