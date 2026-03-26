# config/app_config.py
import os


class AppConfig:
    VERSION = '1.0.0'
    APP_NAME = 'GuitarFans'

    # API URL (используем домен)
    # Если настроен Nginx на порт 80:
    API_BASE_URL = "http://guitarfans.ru"

    # Если Nginx ещё не настроен, используй с портом:
    # API_BASE_URL = "http://guitarfans.ru:8000"

    # Для отладки на телефоне в локальной сети:
    # API_BASE_URL = "http://192.168.1.100:8000"  # IP твоего компьютера

    # API endpoints
    API_AUTH_LOGIN = f"{API_BASE_URL}/auth/login"
    API_AUTH_REGISTER = f"{API_BASE_URL}/auth/register"
    API_AUTH_GOOGLE = f"{API_BASE_URL}/auth/google"
    API_AUTH_VK = f"{API_BASE_URL}/auth/vk"
    API_AUTH_REFRESH = f"{API_BASE_URL}/auth/refresh"
    API_AUTH_LOGOUT = f"{API_BASE_URL}/auth/logout"
    API_USER_ME = f"{API_BASE_URL}/users/me"
    API_HEALTH = f"{API_BASE_URL}/health"

    # Таймауты
    CONNECTION_TIMEOUT = 10
    READ_TIMEOUT = 30


config = AppConfig()