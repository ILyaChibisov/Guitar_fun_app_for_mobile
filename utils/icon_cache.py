# utils/icon_cache.py
"""
Глобальный кэш иконок - предзагружает все иконки при старте
"""
from kivy.core.image import Image as CoreImage
from io import BytesIO
from kivy.logger import Logger
from kivy.clock import Clock

_icon_cache = {}
_loading_complete = False


def preload_icons():
    """Предзагружает все иконки в фоне"""
    try:
        from data import load_asset_as_bytes
        HAS_ASSETS = True
    except ImportError:
        HAS_ASSETS = False
        Logger.warning("Модуль data не найден, иконки не будут предзагружены")
        return

    icon_names = ['artist_png', 'song_png', 'chord_png']

    def load_worker():
        for icon_name in icon_names:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    _icon_cache[icon_name] = img.texture
                    Logger.info(f"✅ Иконка предзагружена: {icon_name}")
            except Exception as e:
                Logger.error(f"❌ Ошибка предзагрузки {icon_name}: {e}")

        global _loading_complete
        _loading_complete = True
        Logger.info("🎨 Все иконки предзагружены")

    import threading
    thread = threading.Thread(target=load_worker, daemon=True)
    thread.start()


def get_icon_texture(icon_name):
    """Мгновенно возвращает текстуру иконки из кэша (синхронно)"""
    return _icon_cache.get(icon_name)


def is_icons_ready():
    return _loading_complete