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

    # ========== БАЗОВЫЕ РАЗМЕРЫ ==========
    TOP_NAV_HEIGHT = 64
    TOP_NAV_HEIGHT_TABLET = 72

    # ========== ДОПОЛНИТЕЛЬНЫЙ ОТСТУП СВЕРХУ ==========
    EXTRA_TOP_PADDING = 4  # Минимальный зазор

    # ========== ОТСТУПЫ ==========
    SIDE_PADDING = 16
    GAP_BETWEEN_CONTENT_AND_NAV = 0

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
        if cls.is_tablet():
            return dp(cls.TOP_NAV_HEIGHT_TABLET)
        return dp(cls.TOP_NAV_HEIGHT)

    @classmethod
    def get_bottom_nav_height(cls):
        return dp(52)

    @classmethod
    def get_bottom_nav_total_height(cls):
        nav_bar_height = get_navigation_bar_height()
        if platform == 'android':
            return cls.get_bottom_nav_height()
        else:
            return cls.get_bottom_nav_height() + nav_bar_height

    @classmethod
    def get_top_padding(cls, include_top_nav=True):
        """
        Возвращает отступ сверху для контента в dp.

        Android: TopNav прозрачный → отступ = panel_height (52dp)
        Windows: TopNav НЕ прозрачный → отступ = status_bar + top_nav_height
        """
        if platform == 'android':
            # Android: TopNav прозрачный
            panel_height = dp(52)
            total = panel_height
        else:
            # Windows: TopNav НЕ прозрачный
            status_h = get_status_bar_height()
            if include_top_nav:
                total = status_h + cls.get_top_nav_height()
            else:
                total = status_h

        total += dp(cls.EXTRA_TOP_PADDING)
        return total

    @classmethod
    def get_bottom_padding(cls):
        return cls.get_bottom_nav_total_height() + dp(cls.GAP_BETWEEN_CONTENT_AND_NAV)

    @classmethod
    def get_content_padding(cls):
        return [
            dp(cls.SIDE_PADDING),
            dp(cls.CONTENT_TOP_PADDING),
            dp(cls.SIDE_PADDING),
            dp(cls.CONTENT_BOTTOM_PADDING)
        ]

    @classmethod
    def force_update(cls):
        cls._is_tablet = None
        logger.info(f"LayoutConfig: принудительное обновление после поворота")

    @classmethod
    def update_for_platform(cls):
        logger.info("=" * 70)
        logger.info("📐 LAYOUT CONFIG")
        logger.info(f"📱 Платформа: {platform}")
        logger.info(f"📱 TOP_NAV_HEIGHT: {cls.TOP_NAV_HEIGHT}dp")
        logger.info(f"📱 BOTTOM_NAV_HEIGHT: {cls.get_bottom_nav_height()}dp")
        logger.info(f"📱 BOTTOM_NAV_TOTAL: {cls.get_bottom_nav_total_height()}dp")
        logger.info(f"📱 EXTRA_TOP_PADDING: {cls.EXTRA_TOP_PADDING}dp")
        logger.info(f"📱 get_top_padding(): {cls.get_top_padding()}dp")
        logger.info(f"📱 get_bottom_padding(): {cls.get_bottom_padding()}dp")
        logger.info("=" * 70)


layout_config = LayoutConfig()
layout_config.update_for_platform()