# data/__init__.py
"""
Пакет данных приложения
Содержит сконвертированные ассеты и другие данные
"""

from .assets import Assets, load_asset_as_bytes, load_asset_as_base64

__all__ = ["Assets", "load_asset_as_bytes", "load_asset_as_base64"]