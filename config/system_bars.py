# config/system_bars.py
"""
Определение высоты системных панелей Android
"""
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from config.logger_config import get_logger

logger = get_logger('SystemBars')

_status_bar_height_dp = None
_nav_bar_height_dp = None

# Константы для симуляции на Windows
WINDOWS_STATUS_BAR_HEIGHT_DP = 24
WINDOWS_NAV_BAR_HEIGHT_DP = 48
GESTURE_NAV_BAR_HEIGHT_DP = 16


def get_screen_density():
    """Возвращает плотность экрана"""
    try:
        if platform == 'android':
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')
            density = Resources.getSystem().getDisplayMetrics().density
            return density
        else:
            return Window.dpi / 160 if Window.dpi else 1.0
    except Exception:
        return Window.dpi / 160 if Window.dpi else 1.0


def get_status_bar_height():
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
                px = Resources.getSystem().getDimensionPixelSize(resource_id)
                density = get_screen_density()
                _status_bar_height_dp = px / density
                logger.info(f"[SystemBars] Статус-бар: {_status_bar_height_dp:.1f}dp")
                return _status_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка получения высоты статус-бара: {e}")

    _status_bar_height_dp = WINDOWS_STATUS_BAR_HEIGHT_DP
    return _status_bar_height_dp


def get_navigation_bar_height():
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
                px = Resources.getSystem().getDimensionPixelSize(resource_id)
                density = get_screen_density()
                _nav_bar_height_dp = px / density
                logger.info(f"[SystemBars] Нав-бар: {_nav_bar_height_dp:.1f}dp")
                return _nav_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка получения высоты нав-бара: {e}")

        # Проверяем режим жестов
        try:
            from android import mActivity
            from jnius import autoclass
            View = autoclass('android.view.View')
            systemUiVisibility = mActivity.getWindow().getDecorView().getSystemUiVisibility()
            if systemUiVisibility & 0x00000002:
                _nav_bar_height_dp = GESTURE_NAV_BAR_HEIGHT_DP
                logger.info(f"[SystemBars] Режим жестов: {_nav_bar_height_dp}dp")
                return _nav_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка проверки режима нав-бара: {e}")

    _nav_bar_height_dp = WINDOWS_NAV_BAR_HEIGHT_DP
    return _nav_bar_height_dp