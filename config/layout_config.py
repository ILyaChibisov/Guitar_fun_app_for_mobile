# config/layout_config.py
"""
Централизованная конфигурация отступов для всех экранов
"""
from kivy.metrics import dp
from kivy.utils import platform
from config.system_bars import get_status_bar_height, get_navigation_bar_height
from config.logger_config import get_logger

logger = get_logger('LayoutConfig')


class LayoutConfig:
    """Централизованная конфигурация отступов"""

    # ========== ОСНОВНЫЕ НАСТРОЙКИ ==========

    # Высота верхней навигации (TopNav)
    TOP_NAV_HEIGHT = dp(56)

    # Высота нижней навигации (BottomNav) - иконки без системной навигации
    BOTTOM_NAV_ICONS_HEIGHT = dp(76)

    # Отступы по бокам для карточек
    SIDE_PADDING = dp(12)

    # Зазор между контентом и панелями навигации
    GAP_BETWEEN_CONTENT_AND_NAV = dp(8)

    # Внутренние отступы для контента
    CONTENT_TOP_PADDING = dp(8)
    CONTENT_BOTTOM_PADDING = dp(8)

    # ========== ПЛАТФОРМО-ЗАВИСИМЫЕ НАСТРОЙКИ ==========

    @classmethod
    def _get_platform_adjustments(cls):
        """Возвращает корректировки для конкретной платформы"""
        if platform == 'android':
            return {
                'extra_top': dp(2),
                'extra_bottom': dp(6),
                'gap': dp(8)
            }
        elif platform == 'win':
            return {
                'extra_top': dp(4),
                'extra_bottom': dp(12),
                'gap': dp(8)
            }
        else:
            return {
                'extra_top': dp(4),
                'extra_bottom': dp(8),
                'gap': dp(8)
            }

    # ========== МЕТОДЫ ДЛЯ ПОЛУЧЕНИЯ ОТСТУПОВ ==========

    @classmethod
    def get_top_padding(cls, include_top_nav=True):
        """
        Возвращает общий отступ сверху для контента.

        Args:
            include_top_nav: Включать ли высоту TopNav (обычно True)

        Returns:
            Отступ в dp
        """
        status_h = get_status_bar_height()

        total = status_h
        if include_top_nav:
            total += cls.TOP_NAV_HEIGHT

        return total

    @classmethod
    def get_bottom_padding(cls):
        """
        Возвращает отступ снизу для контента (над BottomNav).
        Включает зазор между контентом и иконками BottomNav.
        """
        return cls.GAP_BETWEEN_CONTENT_AND_NAV

    @classmethod
    def get_total_bottom_with_navigation(cls):
        """
        Возвращает общую высоту снизу (иконки + системная навигация + зазоры)
        Используется для BottomNav при расчёте своей высоты
        """
        nav_h = get_navigation_bar_height()
        adjustments = cls._get_platform_adjustments()

        # Общая высота = иконки + системная навигация + маленький зазор
        total = cls.BOTTOM_NAV_ICONS_HEIGHT + nav_h + adjustments['extra_bottom']

        return total

    @classmethod
    def get_content_padding(cls):
        """
        Возвращает готовый padding для контейнера контента
        [left, top, right, bottom]
        """
        return [
            cls.SIDE_PADDING,
            cls.CONTENT_TOP_PADDING,
            cls.SIDE_PADDING,
            cls.CONTENT_BOTTOM_PADDING
        ]

    @classmethod
    def get_scrollview_padding(cls):
        """
        Возвращает padding для ScrollView, чтобы контент не обрезался
        [left, top, right, bottom]
        """
        return [
            cls.SIDE_PADDING,
            cls.CONTENT_TOP_PADDING,
            cls.SIDE_PADDING,
            cls.get_bottom_padding() + cls.CONTENT_BOTTOM_PADDING
        ]

    @classmethod
    def update_for_platform(cls):
        """Обновляет настройки в зависимости от платформы"""
        adjustments = cls._get_platform_adjustments()
        cls.GAP_BETWEEN_CONTENT_AND_NAV = adjustments['gap']

        logger.info(f"LayoutConfig обновлён для платформы: {platform}")
        logger.info(f"  - GAP: {cls.GAP_BETWEEN_CONTENT_AND_NAV}dp")
        logger.info(f"  - TOP_NAV_HEIGHT: {cls.TOP_NAV_HEIGHT}dp")
        logger.info(f"  - BOTTOM_NAV_ICONS_HEIGHT: {cls.BOTTOM_NAV_ICONS_HEIGHT}dp")
        logger.info(f"  - SIDE_PADDING: {cls.SIDE_PADDING}dp")


# Создаём экземпляр для удобства
layout_config = LayoutConfig()
layout_config.update_for_platform()