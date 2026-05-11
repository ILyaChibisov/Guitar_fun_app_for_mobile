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
    EXTRA_TOP_PADDING = dp(4)  # Дополнительный отступ сверху
    EXTRA_BOTTOM_PADDING = dp(12)  # Минимальный отступ снизу для комфортного скролла

    # Отступы по бокам для карточек
    SIDE_PADDING = dp(12)

    @classmethod
    def get_top_padding(cls):
        """
        Возвращает общий отступ сверху для контента.
        = статус-бар + TopNav + дополнительный отступ
        """
        status_h = get_status_bar_height()
        total = status_h + cls.TOP_NAV_HEIGHT + cls.EXTRA_TOP_PADDING
        logger.debug(
            f"Top padding: статус-бар={status_h}dp + TopNav={cls.TOP_NAV_HEIGHT}dp + "
            f"отступ={cls.EXTRA_TOP_PADDING}dp = {total}dp"
        )
        return total

    @classmethod
    def get_bottom_padding(cls):
        """
        Возвращает общий отступ снизу для контента.

        ВНИМАНИЕ: BottomNav позиционируется поверх контента и прилегает
        непосредственно к системной навигации. Контенту нужен только
        небольшой отступ, чтобы не прилипать к иконкам BottomNav.

        Системная навигация НЕ требует отступа от контента, так как
        BottomNav находится между контентом и системной навигацией.
        """
        # Контенту нужен только небольшой отступ, чтобы текст не прилипал к BottomNav
        bottom_padding = cls.EXTRA_BOTTOM_PADDING
        logger.debug(f"Bottom padding: {bottom_padding}dp (только отступ от BottomNav)")
        return bottom_padding

    @classmethod
    def get_bottom_padding_for_scroll(cls):
        """
        Возвращает отступ снизу для ScrollView.
        Немного больше, чем обычный bottom_padding, для лучшего визуального отступа.
        """
        return cls.EXTRA_BOTTOM_PADDING + dp(8)

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
            # На Android уменьшаем отступы, так как экраны обычно меньше
            cls.EXTRA_TOP_PADDING = dp(2)
            cls.EXTRA_BOTTOM_PADDING = dp(8)
            logger.info(f"LayoutConfig обновлён для Android: bottom_padding={cls.EXTRA_BOTTOM_PADDING}dp")
        elif platform == 'win':
            # На Windows оставляем стандартные для тестирования
            cls.EXTRA_TOP_PADDING = dp(4)
            cls.EXTRA_BOTTOM_PADDING = dp(12)
            logger.info(f"LayoutConfig обновлён для Windows: bottom_padding={cls.EXTRA_BOTTOM_PADDING}dp")
        else:
            # iOS или другие платформы
            cls.EXTRA_TOP_PADDING = dp(4)
            cls.EXTRA_BOTTOM_PADDING = dp(10)
            logger.info(f"LayoutConfig обновлён для {platform}: bottom_padding={cls.EXTRA_BOTTOM_PADDING}dp")


# Создаём экземпляр для удобства импорта
layout_config = LayoutConfig()
layout_config.update_for_platform()