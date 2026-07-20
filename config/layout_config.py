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

    # ========== ОТСТУПЫ ==========
    SIDE_PADDING = 16
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
        """
        Возвращает высоту BottomNav в dp (только видимая часть с иконками).
        На всех платформах = 52dp.
        """
        return dp(52)

    @classmethod
    def get_bottom_nav_total_height(cls):
        """
        Возвращает ПОЛНУЮ высоту BottomNav с учётом системной навигации.
        """
        nav_bar_height = get_navigation_bar_height()

        if platform == 'android':
            # На Android системная навигация не входит в BottomNav
            return cls.get_bottom_nav_height()
        else:
            # На Windows эмулируем системную навигацию
            return cls.get_bottom_nav_height() + nav_bar_height

    @classmethod
    def get_top_padding(cls, include_top_nav=True):
        """
        Возвращает отступ сверху для контента в dp.
        TopNav прилегает к статус-бару без лишних отступов.
        """
        status_h = get_status_bar_height()
        total = status_h
        if include_top_nav:
            total += cls.get_top_nav_height()
        # ✅ НЕТ лишних отступов!
        return total

    @classmethod
    def get_bottom_padding(cls):
        """
        Возвращает отступ снизу для контента в dp.
        BottomNav прилегает к системной навигации без лишних отступов.
        """
        if platform == 'android':
            nav_h = get_navigation_bar_height()
            bottom_nav_h = cls.get_bottom_nav_total_height()
            # ✅ НЕТ лишних отступов!
            return nav_h + bottom_nav_h
        else:
            return cls.get_bottom_nav_total_height()

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
        logger.info("=" * 70)
        logger.info("📐 LAYOUT CONFIG")
        logger.info(f"📱 Платформа: {platform}")
        logger.info(f"📱 TOP_NAV_HEIGHT: {cls.TOP_NAV_HEIGHT}dp")
        logger.info(f"📱 BOTTOM_NAV_HEIGHT: {cls.get_bottom_nav_height()}dp")
        logger.info(f"📱 BOTTOM_NAV_TOTAL: {cls.get_bottom_nav_total_height()}dp")
        logger.info(f"📱 get_top_padding(): {cls.get_top_padding()}dp")
        logger.info(f"📱 get_bottom_padding(): {cls.get_bottom_padding()}dp")
        logger.info("=" * 70)


layout_config = LayoutConfig()
layout_config.update_for_platform()