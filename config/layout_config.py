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
    """Централизованная конфигурация"""

    # ========== БАЗОВЫЕ РАЗМЕРЫ (просто числа, НЕ dp!) ==========
    TOP_NAV_HEIGHT = 64  # высота верхней панели
    BOTTOM_NAV_HEIGHT = 44  # ← ИЗМЕНЕНО: с 56 на 44 (актуальная высота BottomNav)
    TOP_NAV_HEIGHT_TABLET = 72
    BOTTOM_NAV_HEIGHT_TABLET = 52  # ← ИЗМЕНЕНО: с 64 на 52

    # Отступы
    SIDE_PADDING = 16
    GAP_BETWEEN_CONTENT_AND_NAV = 8

    # ДОПОЛНИТЕЛЬНЫЙ ОТСТУП СВЕРХУ (после TopNav)
    EXTRA_TOP_PADDING = 12

    CONTENT_TOP_PADDING = 8
    CONTENT_BOTTOM_PADDING = 8

    _is_tablet = None

    @classmethod
    def is_tablet(cls):
        """Определяет, планшет ли это (ширина >= 600dp)"""
        if cls._is_tablet is None:
            min_width = min(Window.width, Window.height)
            cls._is_tablet = min_width >= dp(600)
        return cls._is_tablet

    @classmethod
    def get_top_nav_height(cls):
        """Возвращает высоту верхней панели в dp"""
        if cls.is_tablet():
            return dp(cls.TOP_NAV_HEIGHT_TABLET)
        return dp(cls.TOP_NAV_HEIGHT)

    @classmethod
    def get_bottom_nav_height(cls):
        """Возвращает высоту нижней панели в dp"""
        if cls.is_tablet():
            return dp(cls.BOTTOM_NAV_HEIGHT_TABLET)
        return dp(cls.BOTTOM_NAV_HEIGHT)

    @classmethod
    def get_top_padding(cls, include_top_nav=True):
        """Возвращает отступ сверху для контента в dp"""
        status_h = get_status_bar_height()
        total = status_h
        if include_top_nav:
            total += cls.get_top_nav_height()
        total += dp(cls.EXTRA_TOP_PADDING)
        return total

    @classmethod
    def get_bottom_padding(cls):
        """Возвращает отступ снизу для контента в dp"""
        # Отступ перед BottomNav с учётом его актуальной высоты
        nav_bar_height = get_navigation_bar_height()
        return cls.get_bottom_nav_height() + nav_bar_height + dp(cls.GAP_BETWEEN_CONTENT_AND_NAV)

    @classmethod
    def get_content_padding(cls):
        """Возвращает padding для контейнера контента [left, top, right, bottom] в dp"""
        return [
            dp(cls.SIDE_PADDING),
            dp(cls.CONTENT_TOP_PADDING),
            dp(cls.SIDE_PADDING),
            dp(cls.CONTENT_BOTTOM_PADDING)
        ]

    @classmethod
    def force_update(cls):
        """Принудительное обновление после поворота экрана"""
        cls._is_tablet = None
        logger.info(f"LayoutConfig: принудительное обновление после поворота")

    @classmethod
    def update_for_platform(cls):
        logger.info(f"LayoutConfig: TOP_NAV_HEIGHT={cls.TOP_NAV_HEIGHT}dp, BOTTOM_NAV_HEIGHT={cls.BOTTOM_NAV_HEIGHT}dp")
        logger.info(f"LayoutConfig: EXTRA_TOP_PADDING={cls.EXTRA_TOP_PADDING}dp")


layout_config = LayoutConfig()
layout_config.update_for_platform()