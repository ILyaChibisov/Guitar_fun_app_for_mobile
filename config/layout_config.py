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

    # Дополнительные отступы
    EXTRA_TOP_PADDING = dp(4)
    EXTRA_BOTTOM_PADDING = dp(8)  # Минимальный отступ от BottomNav

    # Отступы по бокам для карточек
    SIDE_PADDING = dp(12)

    @classmethod
    def get_top_padding(cls):
        """Возвращает общий отступ сверху для контента"""
        status_h = get_status_bar_height()
        total = status_h + cls.TOP_NAV_HEIGHT + cls.EXTRA_TOP_PADDING
        return total

    @classmethod
    def get_bottom_padding(cls):
        """
        Возвращает общий отступ снизу для контента.
        Контент должен заканчиваться до BottomNav, чтобы не перекрываться.
        BottomNav сам имеет отступ под системную навигацию.
        """
        # Возвращаем только небольшой отступ, чтобы контент не прилипал к BottomNav
        return cls.EXTRA_BOTTOM_PADDING

    @classmethod
    def get_safe_area_insets(cls):
        """Возвращает безопасные отступы"""
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
            cls.EXTRA_TOP_PADDING = dp(2)
            cls.EXTRA_BOTTOM_PADDING = dp(8)
        elif platform == 'win':
            cls.EXTRA_TOP_PADDING = dp(4)
            cls.EXTRA_BOTTOM_PADDING = dp(12)
        logger.info(f"LayoutConfig обновлён для платформы: {platform}")


layout_config = LayoutConfig()
layout_config.update_for_platform()