# chord_utils/assets.py
"""
Глобальный кеш текстур.
Позволяет не декодировать PNG-файлы заново при каждом свайпе или смене аккорда.
"""
from io import BytesIO
from kivy.core.image import Image as CoreImage
from kivy.logger import Logger

_griff_texture_cache = None


def get_griff_texture():
    """
    Возвращает текстуру фона грифа (griff_png).
    Загружает её один раз и кеширует в памяти.
    """
    global _griff_texture_cache
    if _griff_texture_cache is not None:
        return _griff_texture_cache

    try:
        from data import load_asset_as_bytes
        bg_data = load_asset_as_bytes("griff_png")
        if bg_data:
            img = CoreImage(BytesIO(bg_data), ext="png")
            if img and img.texture:
                _griff_texture_cache = img.texture
                Logger.info("Assets: текстура грифа загружена и закеширована")
                return _griff_texture_cache
    except ImportError:
        Logger.warning("Assets: модуль data не найден, фон грифа не загружен")
    except Exception as e:
        Logger.error(f"Assets: ошибка загрузки griff_png: {e}")

    return None


def clear_asset_cache():
    """Сбрасывает кеш текстур (например, при смене темы или hot-reload)."""
    global _griff_texture_cache
    _griff_texture_cache = None
    Logger.info("Assets: кеш текстур сброшен")