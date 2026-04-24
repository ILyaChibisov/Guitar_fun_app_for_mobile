# config/app_config.py
import os


class AppConfig:
    VERSION = '1.0.0'
    APP_NAME = 'GuitarFuns'

    # API URL (используем домен)
    API_BASE_URL = "https://guitarfans.ru/api"

    # API endpoints
    API_AUTH_LOGIN = f"{API_BASE_URL}/auth/login"
    API_AUTH_REGISTER = f"{API_BASE_URL}/auth/register"
    API_AUTH_GOOGLE = f"{API_BASE_URL}/auth/google/login"
    API_AUTH_VK = f"{API_BASE_URL}/auth/vk/login"
    API_AUTH_REFRESH = f"{API_BASE_URL}/auth/refresh"
    API_AUTH_LOGOUT = f"{API_BASE_URL}/auth/logout"
    API_USER_ME = f"{API_BASE_URL}/users/me"
    API_HEALTH = f"{API_BASE_URL}/health"

    # Таймауты
    CONNECTION_TIMEOUT = 10
    READ_TIMEOUT = 30


config = AppConfig()