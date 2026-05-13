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

    # ========== РАЗМЕРЫ ПАНЕЛЕЙ (в dp - адаптируются под плотность экрана) ==========

    # Стандартные размеры Material Design
    TOP_NAV_HEIGHT = dp(56)  # стандартная высота TopAppBar
    BOTTOM_NAV_HEIGHT = dp(56)  # стандартная высота BottomNavigationView (телефоны)

    # Альтернативные размеры для планшетов
    TOP_NAV_HEIGHT_TABLET = dp(64)
    BOTTOM_NAV_HEIGHT_TABLET = dp(64)

    # Отступы
    SIDE_PADDING = dp(16)  # стандартный отступ Material Design
    GAP_BETWEEN_CONTENT_AND_NAV = dp(8)

    # Внутренние отступы для контента
    CONTENT_TOP_PADDING = dp(8)
    CONTENT_BOTTOM_PADDING = dp(8)

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
        """Возвращает адаптивную высоту верхней панели"""
        height = cls.TOP_NAV_HEIGHT_TABLET if cls.is_tablet() else cls.TOP_NAV_HEIGHT
        logger.info(f"[LayoutConfig] get_top_nav_height: {height}dp")
        return height

    @classmethod
    def get_bottom_nav_height(cls):
        """Возвращает адаптивную высоту нижней панели (только иконки)"""
        height = cls.BOTTOM_NAV_HEIGHT_TABLET if cls.is_tablet() else cls.BOTTOM_NAV_HEIGHT
        logger.info(f"[LayoutConfig] get_bottom_nav_height: {height}dp")
        return height

    @classmethod
    def get_top_padding(cls, include_top_nav=True):
        """Возвращает общий отступ сверху для контента"""
        status_h = get_status_bar_height()
        total = status_h
        if include_top_nav:
            total += cls.get_top_nav_height()
        logger.info(
            f"[LayoutConfig] get_top_padding: {total}dp (status={status_h}dp, top_nav={cls.get_top_nav_height()}dp)")
        return total

    @classmethod
    def get_bottom_padding(cls):
        """Возвращает отступ снизу для контента (над BottomNav)"""
        padding = cls.GAP_BETWEEN_CONTENT_AND_NAV
        logger.info(f"[LayoutConfig] get_bottom_padding: {padding}dp")
        return padding

    @classmethod
    def get_content_padding(cls):
        """Возвращает готовый padding для контейнера контента [left, top, right, bottom]"""
        return [
            cls.SIDE_PADDING,
            cls.CONTENT_TOP_PADDING,
            cls.SIDE_PADDING,
            cls.CONTENT_BOTTOM_PADDING
        ]

    @classmethod
    def get_total_bottom_height(cls):
        """Общая высота нижней части (BottomNav + системная навигация)"""
        nav_h = get_navigation_bar_height()
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
        logger.info(f"[LayoutConfig] SIDE_PADDING: {cls.SIDE_PADDING}dp")
        logger.info(f"[LayoutConfig] is_tablet: {cls.is_tablet()}")
        logger.info("=" * 50)


# Создаём экземпляр для удобства
layout_config = LayoutConfig()
layout_config.update_for_platform()