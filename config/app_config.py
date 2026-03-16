# config/app_config.py
"""
Общие настройки приложения
"""


class AppConfig:
    # Версия приложения
    VERSION = '1.0.0'

    # Название
    APP_NAME = 'GuitarApp'

    # Настройки сервера
    SERVER_URL = 'https://api.guitarapp.com'  # Заменишь на свой
    API_TIMEOUT = 10  # секунд

    # Настройки тюнера
    TUNER_SAMPLE_RATE = 44100
    TUNER_CHUNK_SIZE = 1024

    # Настройки путей
    CHORD_IMAGES_DIR = 'chords_cache'

    # Цвета приложения (для будущего использования)
    COLORS = {
        'primary': '#2196F3',
        'secondary': '#FF9800',
        'success': '#4CAF50',
        'error': '#F44336',
        'background': '#F5F5F5'
    }


# Создаем глобальный экземпляр конфига
config = AppConfig()