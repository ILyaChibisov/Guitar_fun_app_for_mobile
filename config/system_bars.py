# config/system_bars.py
"""
Определение высоты системных панелей Android
На Windows используем фиксированные значения для тестирования
"""
from kivy.utils import platform
from kivy.metrics import dp
from config.logger_config import get_logger

logger = get_logger('SystemBars')

_status_bar_height_dp = None
_nav_bar_height_dp = None

# Константы для симуляции на Windows (в dp)
WINDOWS_STATUS_BAR_HEIGHT_DP = 24  # 24dp симуляция статус-бара
WINDOWS_NAV_BAR_HEIGHT_DP = 48  # 48dp симуляция нав-бара


def get_status_bar_height_dp():
    """Возвращает высоту статус-бара в dp"""
    global _status_bar_height_dp

    if _status_bar_height_dp is not None:
        return _status_bar_height_dp

    if platform == 'android':
        try:
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')
            resource_id = Resources.getSystem().getIdentifier(
                'status_bar_height', 'dimen', 'android'
            )
            if resource_id > 0:
                pixels = Resources.getSystem().getDimensionPixelSize(resource_id)
                # Конвертируем пиксели в dp
                _status_bar_height_dp = pixels // (Resources.getSystem().getDisplayMetrics().density)
                logger.info(f"Высота статус-бара (Android): {pixels}px = {_status_bar_height_dp}dp")
                return _status_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка получения высоты статус-бара: {e}")

    # На Windows используем симуляцию для тестирования
    _status_bar_height_dp = WINDOWS_STATUS_BAR_HEIGHT_DP
    logger.info(f"Высота статус-бара (симуляция Windows): {_status_bar_height_dp}dp")
    return _status_bar_height_dp


def get_navigation_bar_height_dp():
    """Возвращает высоту навигационной панели в dp"""
    global _nav_bar_height_dp

    if _nav_bar_height_dp is not None:
        return _nav_bar_height_dp

    if platform == 'android':
        try:
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')
            resource_id = Resources.getSystem().getIdentifier(
                'navigation_bar_height', 'dimen', 'android'
            )
            if resource_id > 0:
                pixels = Resources.getSystem().getDimensionPixelSize(resource_id)
                # Конвертируем пиксели в dp
                _nav_bar_height_dp = pixels // (Resources.getSystem().getDisplayMetrics().density)
                logger.info(f"Высота нав-бара (Android): {pixels}px = {_nav_bar_height_dp}dp")
                return _nav_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка получения высоты нав-бара: {e}")

    # На Windows используем симуляцию для тестирования
    _nav_bar_height_dp = WINDOWS_NAV_BAR_HEIGHT_DP
    logger.info(f"Высота нав-бара (симуляция Windows): {_nav_bar_height_dp}dp")
    return _nav_bar_height_dp


# Для обратной совместимости (возвращают dp)
def get_status_bar_height():
    """Возвращает высоту статус-бара в dp"""
    return get_status_bar_height_dp()


def get_navigation_bar_height():
    """Возвращает высоту навигационной панели в dp"""
    return get_navigation_bar_height_dp()


def set_simulation_heights(status_dp=24, nav_dp=48):
    """Для Windows: установить свои значения симуляции (в dp)"""
    global _status_bar_height_dp, _nav_bar_height_dp, WINDOWS_STATUS_BAR_HEIGHT_DP, WINDOWS_NAV_BAR_HEIGHT_DP
    if platform != 'android':
        WINDOWS_STATUS_BAR_HEIGHT_DP = status_dp
        WINDOWS_NAV_BAR_HEIGHT_DP = nav_dp
        _status_bar_height_dp = status_dp
        _nav_bar_height_dp = nav_dp
        logger.info(f"Симуляция обновлена: статус-бар={status_dp}dp, нав-бар={nav_dp}dp")