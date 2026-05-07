# config/system_bars.py
"""
Определение высоты системных панелей Android
На Windows используем фиксированные значения для тестирования
"""
from kivy.utils import platform
from kivy.metrics import dp
from config.logger_config import get_logger

logger = get_logger('SystemBars')

_status_bar_height = None
_nav_bar_height = None

# Константы для симуляции на Windows (в пикселях)
WINDOWS_STATUS_BAR_HEIGHT = 30  # 30px симуляция статус-бара
WINDOWS_NAV_BAR_HEIGHT = 50  # 50px симуляция нав-бара


def get_status_bar_height():
    """Возвращает высоту статус-бара в пикселях"""
    global _status_bar_height

    if _status_bar_height is not None:
        return _status_bar_height

    if platform == 'android':
        try:
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')
            resource_id = Resources.getSystem().getIdentifier(
                'status_bar_height', 'dimen', 'android'
            )
            if resource_id > 0:
                _status_bar_height = Resources.getSystem().getDimensionPixelSize(resource_id)
                logger.info(f"Высота статус-бара (Android): {_status_bar_height}px ({dp(_status_bar_height)}dp)")
                return _status_bar_height
        except Exception as e:
            logger.error(f"Ошибка получения высоты статус-бара: {e}")

    # На Windows используем симуляцию для тестирования
    _status_bar_height = WINDOWS_STATUS_BAR_HEIGHT
    logger.info(f"Высота статус-бара (симуляция Windows): {_status_bar_height}px ({dp(_status_bar_height)}dp)")
    return _status_bar_height


def get_navigation_bar_height():
    """Возвращает высоту навигационной панели в пикселях"""
    global _nav_bar_height

    if _nav_bar_height is not None:
        return _nav_bar_height

    if platform == 'android':
        try:
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')
            resource_id = Resources.getSystem().getIdentifier(
                'navigation_bar_height', 'dimen', 'android'
            )
            if resource_id > 0:
                _nav_bar_height = Resources.getSystem().getDimensionPixelSize(resource_id)
                logger.info(f"Высота нав-бара (Android): {_nav_bar_height}px ({dp(_nav_bar_height)}dp)")
                return _nav_bar_height
        except Exception as e:
            logger.error(f"Ошибка получения высоты нав-бара: {e}")

    # На Windows используем симуляцию для тестирования
    _nav_bar_height = WINDOWS_NAV_BAR_HEIGHT
    logger.info(f"Высота нав-бара (симуляция Windows): {_nav_bar_height}px ({dp(_nav_bar_height)}dp)")
    return _nav_bar_height


def get_status_bar_height_dp():
    """Возвращает высоту статус-бара в dp"""
    return dp(get_status_bar_height())


def get_navigation_bar_height_dp():
    """Возвращает высоту навигационной панели в dp"""
    return dp(get_navigation_bar_height())


def set_simulation_heights(status_px=30, nav_px=50):
    """Для Windows: установить свои значения симуляции (в пикселях)"""
    global _status_bar_height, _nav_bar_height, WINDOWS_STATUS_BAR_HEIGHT, WINDOWS_NAV_BAR_HEIGHT
    if platform != 'android':
        WINDOWS_STATUS_BAR_HEIGHT = status_px
        WINDOWS_NAV_BAR_HEIGHT = nav_px
        _status_bar_height = status_px
        _nav_bar_height = nav_px
        logger.info(f"Симуляция обновлена: статус-бар={status_px}px, нав-бар={nav_px}px")