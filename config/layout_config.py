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
    """Централизованная конфигурация - адаптивная"""

    # ========== РАЗМЕРЫ ПАНЕЛЕЙ (в dp - просто числа, БЕЗ вызова dp()) ==========

    # Стандартные размеры Material Design (чистые числа)
    TOP_NAV_HEIGHT = 56  # стандартная высота TopAppBar
    BOTTOM_NAV_HEIGHT = 56  # стандартная высота BottomNavigationView

    # Альтернативные размеры для планшетов
    TOP_NAV_HEIGHT_TABLET = 64
    BOTTOM_NAV_HEIGHT_TABLET = 64

    # Отступы (чистые числа)
    SIDE_PADDING = 16
    GAP_BETWEEN_CONTENT_AND_NAV = 8
    CONTENT_TOP_PADDING = 8
    CONTENT_BOTTOM_PADDING = 8

    # Флаги для определения типа устройства
    _is_tablet = None

    @classmethod
    def is_tablet(cls):
        """Определяет, является ли устройство планшетом"""
        if cls._is_tablet is None:
            min_width = min(Window.width, Window.height)
            cls._is_tablet = min_width >= dp(600)
            logger.info(f"[LayoutConfig] is_tablet: {cls._is_tablet} (min_width={min_width}dp)")
        return cls._is_tablet

    @classmethod
    def get_top_nav_height(cls):
        """Возвращает адаптивную высоту верхней панели в dp"""
        raw = cls.TOP_NAV_HEIGHT_TABLET if cls.is_tablet() else cls.TOP_NAV_HEIGHT
        result = dp(raw)
        logger.info(f"[LayoutConfig] get_top_nav_height: {result}dp (raw={raw})")
        return result

    @classmethod
    def get_bottom_nav_height(cls):
        """Возвращает адаптивную высоту нижней панели (только иконки) в dp"""
        raw = cls.BOTTOM_NAV_HEIGHT_TABLET if cls.is_tablet() else cls.BOTTOM_NAV_HEIGHT
        result = dp(raw)
        logger.info(f"[LayoutConfig] get_bottom_nav_height: {result}dp (raw={raw})")
        return result

    @classmethod
    def get_top_padding(cls, include_top_nav=True):
        """Возвращает общий отступ сверху для контента в dp"""
        status_h = get_status_bar_height()  # уже в dp
        total = status_h
        if include_top_nav:
            total += cls.get_top_nav_height()
        logger.info(
            f"[LayoutConfig] get_top_padding: {total}dp (status={status_h}dp, top_nav={cls.get_top_nav_height()}dp)")
        return total

    @classmethod
    def get_bottom_padding(cls):
        """Возвращает отступ снизу для контента (над BottomNav) в dp"""
        result = dp(cls.GAP_BETWEEN_CONTENT_AND_NAV)
        logger.info(f"[LayoutConfig] get_bottom_padding: {result}dp")
        return result

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
    def get_total_bottom_height(cls):
        """Общая высота нижней части (BottomNav + системная навигация) в dp"""
        nav_h = get_navigation_bar_height()  # уже в dp
        total = cls.get_bottom_nav_height() + nav_h
        logger.info(
            f"[LayoutConfig] get_total_bottom_height: {total}dp (nav={cls.get_bottom_nav_height()}dp, sys_nav={nav_h}dp)")
        return total

    @classmethod
    def update_for_platform(cls):
        """Обновляет настройки в зависимости от платформы"""
        logger.info("=" * 50)
        logger.info(f"[LayoutConfig] Обновление для платформы: {platform}")
        logger.info(f"[LayoutConfig] TOP_NAV_HEIGHT: {cls.get_top_nav_height()}dp")
        logger.info(f"[LayoutConfig] BOTTOM_NAV_HEIGHT: {cls.get_bottom_nav_height()}dp")
        logger.info(f"[LayoutConfig] SIDE_PADDING: {dp(cls.SIDE_PADDING)}dp")
        logger.info(f"[LayoutConfig] is_tablet: {cls.is_tablet()}")
        logger.info("=" * 50)


# Создаём экземпляр
layout_config = LayoutConfig()
layout_config.update_for_platform()