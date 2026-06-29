# utils/cache_manager.py
"""
Утилита для управления кэшем приложения
"""
import os
import json
import time
from kivy.logger import Logger
from config.app_config import config


class CacheManager:
    """Менеджер кэша для удобного управления"""

    @staticmethod
    def get_cache_dir():
        """Возвращает путь к папке кэша"""
        return config.CACHE_DIR

    @staticmethod
    def get_cache_size():
        """Возвращает размер кэша в удобном формате"""
        size_bytes = config.get_cache_size()

        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    @staticmethod
    def get_cached_songs_count():
        """Возвращает количество закэшированных песен"""
        try:
            cache_dir = config.CACHE_DIR
            if not os.path.exists(cache_dir):
                return 0
            return len([f for f in os.listdir(cache_dir)
                        if f.startswith('song_') and f.endswith('.json')])
        except:
            return 0

    @staticmethod
    def get_favorites_cache_age():
        """Возвращает возраст кэша избранного в секундах"""
        try:
            cache_dir = config.CACHE_DIR
            files = [f for f in os.listdir(cache_dir)
                     if f.startswith('favorites_') and f.endswith('.json')]
            if not files:
                return None

            # Берем первый файл
            file_path = os.path.join(cache_dir, files[0])
            mtime = os.path.getmtime(file_path)
            return int(time.time() - mtime)
        except:
            return None

    @staticmethod
    def is_cache_valid():
        """Проверяет, валиден ли кэш избранного"""
        age = CacheManager.get_favorites_cache_age()
        if age is None:
            return False
        return age < config.FAVORITES_CACHE_TTL

    @staticmethod
    def clear_all_cache():
        """Очищает весь кэш"""
        return config.clear_cache()

    @staticmethod
    def get_cache_info():
        """Возвращает информацию о кэше"""
        return {
            'cache_dir': config.CACHE_DIR,
            'size': CacheManager.get_cache_size(),
            'songs_cached': CacheManager.get_cached_songs_count(),
            'favorites_age': CacheManager.get_favorites_cache_age(),
            'favorites_valid': CacheManager.is_cache_valid()
        }


# Для удобного импорта
cache_manager = CacheManager()