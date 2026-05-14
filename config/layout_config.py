# config/layout_config.py
"""
Централизованная конфигурация отступов и размеров панелей
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window
from config.system_bars import get_status_bar_height, get_navigation_bar_height
from config.logger_config import get_logger

logger = get_logger('LayoutConfig')


class LayoutConfig:
    """Централизованная конфигурация - ПРОСТЫЕ ЧИСЛА (не dp!)"""

    # ========== РАЗМЕРЫ ПАНЕЛЕЙ (просто числа, БЕЗ dp) ==========
    TOP_NAV_HEIGHT = 56
    BOTTOM_NAV_HEIGHT = 56
    TOP_NAV_HEIGHT_TABLET = 64
    BOTTOM_NAV_HEIGHT_TABLET = 64

    # Отступы (просто числа)
    SIDE_PADDING = 16
    GAP_BETWEEN_CONTENT_AND_NAV = 8
    CONTENT_TOP_PADDING = 8
    CONTENT_BOTTOM_PADDING = 8

    _is_tablet = None

    @classmethod
    def is_tablet(cls):
        if cls._is_tablet is None:
            min_width = min(Window.width, Window.height)
            cls._is_tablet = min_width >= dp(600)
        return cls._is_tablet

    @classmethod
    def get_top_nav_height(cls):
        """Возвращает высоту верхней панели (просто число)"""
        if cls.is_tablet():
            return cls.TOP_NAV_HEIGHT_TABLET
        return cls.TOP_NAV_HEIGHT

    @classmethod
    def get_bottom_nav_height(cls):
        """Возвращает высоту нижней панели (просто число)"""
        if cls.is_tablet():
            return cls.BOTTOM_NAV_HEIGHT_TABLET
        return cls.BOTTOM_NAV_HEIGHT

    @classmethod
    def get_top_padding(cls, include_top_nav=True):
        """Возвращает отступ сверху для контента в dp"""
        status_h = get_status_bar_height()
        total = status_h
        if include_top_nav:
            total += dp(cls.get_top_nav_height())
        return total

    @classmethod
    def get_bottom_padding(cls):
        """Возвращает отступ снизу для контента в dp"""
        return dp(cls.GAP_BETWEEN_CONTENT_AND_NAV)

    @classmethod
    def get_content_padding(cls):
        """Возвращает готовый padding для контейнера контента [left, top, right, bottom] в dp"""
        return [
            dp(cls.SIDE_PADDING),
            dp(cls.CONTENT_TOP_PADDING),
            dp(cls.SIDE_PADDING),
            dp(cls.CONTENT_BOTTOM_PADDING)
        ]

    @classmethod
    def update_for_platform(cls):
        logger.info(f"LayoutConfig: TOP_NAV_HEIGHT={cls.TOP_NAV_HEIGHT}dp, BOTTOM_NAV_HEIGHT={cls.BOTTOM_NAV_HEIGHT}dp")

    @classmethod
    def force_update(cls):
        """Принудительно обновляет настройки (после поворота экрана)"""
        cls._is_tablet = None
        cls.update_for_platform()
        logger.info(f"LayoutConfig: принудительное обновление после поворота")


# Создаём экземпляр
layout_config = LayoutConfig()
layout_config.update_for_platform()