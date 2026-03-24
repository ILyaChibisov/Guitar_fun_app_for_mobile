# config/app_config.py
import os
import sys


class AppConfig:
    VERSION = '1.0.0'
    APP_NAME = 'GuitarFuns'

    # Определяем окружение
    IS_DEVELOPMENT = os.getenv('ENVIRONMENT', 'development') == 'development'

    # API URL - будем использовать реальный домен
    # Пока DNS не обновился, можно использовать IP для теста
    API_BASE_URL = "https://api.guitarfuns.ru"  # Когда DNS обновится
    # API_BASE_URL = "http://217.179.51.161:8000"  # Временный IP для теста

    # API endpoints
    API_AUTH_LOGIN = f"{API_BASE_URL}/auth/login"
    API_AUTH_REGISTER = f"{API_BASE_URL}/auth/register"
    API_AUTH_GOOGLE = f"{API_BASE_URL}/auth/google"
    API_AUTH_VK = f"{API_BASE_URL}/auth/vk"
    API_AUTH_REFRESH = f"{API_BASE_URL}/auth/refresh"
    API_AUTH_LOGOUT = f"{API_BASE_URL}/auth/logout"
    API_USER_ME = f"{API_BASE_URL}/users/me"
    API_USER_UPDATE = f"{API_BASE_URL}/users/me"
    API_HEALTH = f"{API_BASE_URL}/health"

    # Таймауты
    CONNECTION_TIMEOUT = 10
    READ_TIMEOUT = 30


config = AppConfig()