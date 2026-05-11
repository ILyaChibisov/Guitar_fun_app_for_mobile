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

    # Высота верхней навигации (TopNav)
    TOP_NAV_HEIGHT = dp(56)

    # Высота нижней навигации (BottomNav)
    BOTTOM_NAV_HEIGHT = dp(56)

    # Дополнительные отступы
    EXTRA_TOP_PADDING = dp(4)  # Дополнительный отступ сверху
    EXTRA_BOTTOM_PADDING = dp(20)  # Дополнительный отступ снизу (для безопасной зоны)

    # Отступы по бокам для карточек
    SIDE_PADDING = dp(12)

    @classmethod
    def get_top_padding(cls):
        """Возвращает общий отступ сверху для контента"""
        status_h = get_status_bar_height()
        total = status_h + cls.TOP_NAV_HEIGHT + cls.EXTRA_TOP_PADDING
        logger.debug(
            f"Top padding: статус-бар={status_h}dp + TopNav={cls.TOP_NAV_HEIGHT}dp + отступ={cls.EXTRA_TOP_PADDING}dp = {total}dp")
        return total

    @classmethod
    def get_bottom_padding(cls):
        """Возвращает общий отступ снизу для контента"""
        nav_h = get_navigation_bar_height()
        total = cls.BOTTOM_NAV_HEIGHT + nav_h + cls.EXTRA_BOTTOM_PADDING
        logger.debug(
            f"Bottom padding: BottomNav={cls.BOTTOM_NAV_HEIGHT}dp + нав-бар={nav_h}dp + отступ={cls.EXTRA_BOTTOM_PADDING}dp = {total}dp")
        return total

    @classmethod
    def get_safe_area_insets(cls):
        """Возвращает безопасные отступы (как в iOS/Android)"""
        return {
            'top': cls.get_top_padding(),
            'bottom': cls.get_bottom_padding(),
            'left': cls.SIDE_PADDING,
            'right': cls.SIDE_PADDING
        }

    @classmethod
    def update_for_platform(cls):
        """Обновляет настройки в зависимости от платформы"""
        if platform == 'android':
            # На Android немного уменьшаем отступы
            cls.EXTRA_TOP_PADDING = dp(2)
            cls.EXTRA_BOTTOM_PADDING = dp(12)
        elif platform == 'win':
            # На Windows оставляем стандартные для тестирования
            cls.EXTRA_TOP_PADDING = dp(4)
            cls.EXTRA_BOTTOM_PADDING = dp(20)
        logger.info(f"LayoutConfig обновлён для платформы: {platform}")


layout_config = LayoutConfig()
layout_config.update_for_platform()