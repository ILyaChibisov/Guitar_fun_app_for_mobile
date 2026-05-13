# config/system_bars.py
"""
Определение высоты системных панелей Android
На Windows используем значения, имитирующие реальное Android устройство
"""
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from config.logger_config import get_logger

logger = get_logger('SystemBars')

_status_bar_height_px = None
_nav_bar_height_px = None

# Константы для симуляции на Windows (в dp)
WINDOWS_STATUS_BAR_HEIGHT_DP = 24  # 24dp - стандартная высота статус-бара на Android
WINDOWS_NAV_BAR_HEIGHT_DP = 48  # 48dp - стандартная высота нав-бара с кнопками
GESTURE_NAV_BAR_HEIGHT_DP = 16  # 16dp - высота нав-бара при жестах


def get_screen_density():
    """Возвращает плотность экрана для корректного пересчёта dp в px"""
    try:
        if platform == 'android':
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')
            return Resources.getSystem().getDisplayMetrics().density
        else:
            return Window.dpi / 160 if Window.dpi else 1.0
    except Exception:
        return Window.dpi / 160 if Window.dpi else 1.0


def get_status_bar_height_px():
    """Возвращает высоту статус-бара в пикселях"""
    global _status_bar_height_px

    if _status_bar_height_px is not None:
        return _status_bar_height_px

    if platform == 'android':
        try:
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')
            resource_id = Resources.getSystem().getIdentifier(
                'status_bar_height', 'dimen', 'android'
            )
            if resource_id > 0:
                _status_bar_height_px = Resources.getSystem().getDimensionPixelSize(resource_id)
                density = get_screen_density()
                logger.info(f"Высота статус-бара (Android): {_status_bar_height_px}px, "
                            f"плотность={density:.2f}, "
                            f"в dp={_status_bar_height_px / density:.0f}dp")
                return _status_bar_height_px
        except Exception as e:
            logger.error(f"Ошибка получения высоты статус-бара: {e}")

    # Для Windows - имитируем реальное Android устройство
    density = get_screen_density()
    _status_bar_height_px = int(WINDOWS_STATUS_BAR_HEIGHT_DP * density)
    logger.info(f"Высота статус-бара (симуляция Windows): {_status_bar_height_px}px "
                f"(={WINDOWS_STATUS_BAR_HEIGHT_DP}dp, плотность={density:.2f})")
    return _status_bar_height_px


def get_navigation_bar_height_px():
    """Возвращает высоту навигационной панели в пикселях"""
    global _nav_bar_height_px

    if _nav_bar_height_px is not None:
        return _nav_bar_height_px

    if platform == 'android':
        try:
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')

            resource_id = Resources.getSystem().getIdentifier(
                'navigation_bar_height', 'dimen', 'android'
            )
            if resource_id > 0:
                _nav_bar_height_px = Resources.getSystem().getDimensionPixelSize(resource_id)
                density = get_screen_density()
                logger.info(
                    f"[SystemBars] Android нав-бар: {_nav_bar_height_px}px, плотность={density:.2f}, в dp={_nav_bar_height_px / density:.0f}dp")
                return _nav_bar_height_px
        except Exception as e:
            logger.error(f"Ошибка получения высоты нав-бара: {e}")

    # Для Windows
    density = get_screen_density()
    _nav_bar_height_px = int(48 * density)
    logger.info(f"[SystemBars] Симуляция нав-бара: {_nav_bar_height_px}px, в dp=48dp")
    return _nav_bar_height_px


def get_status_bar_height():
    """Возвращает высоту статус-бара в dp"""
    return dp(get_status_bar_height_px())


def get_navigation_bar_height():
    """Возвращает высоту навигационной панели в dp"""
    return dp(get_navigation_bar_height_px())


def set_simulation_heights(status_dp=24, nav_dp=48):
    """
    Для Windows: установить свои значения симуляции (в dp)
    Стандартные значения Android:
    - Статус-бар: 24dp
    - Нав-бар с кнопками: 48dp
    - Нав-бар с жестами: 16dp
    """
    global WINDOWS_STATUS_BAR_HEIGHT_DP, WINDOWS_NAV_BAR_HEIGHT_DP
    global _status_bar_height_px, _nav_bar_height_px

    if platform != 'android':
        WINDOWS_STATUS_BAR_HEIGHT_DP = status_dp
        WINDOWS_NAV_BAR_HEIGHT_DP = nav_dp
        # Сбрасываем кэш, чтобы пересчитать px
        _status_bar_height_px = None
        _nav_bar_height_px = None
        logger.info(f"Симуляция обновлена: статус-бар={status_dp}dp, нав-бар={nav_dp}dp")


def set_gesture_mode(enabled=True):
    """
    Устанавливает режим жестов (для симуляции на Windows)
    """
    if platform != 'android':
        if enabled:
            set_simulation_heights(status_dp=24, nav_dp=GESTURE_NAV_BAR_HEIGHT_DP)
            logger.info(f"Режим жестов включён: нав-бар={GESTURE_NAV_BAR_HEIGHT_DP}dp")
        else:
            set_simulation_heights(status_dp=24, nav_dp=WINDOWS_NAV_BAR_HEIGHT_DP)
            logger.info(f"Режим кнопок включён: нав-бар={WINDOWS_NAV_BAR_HEIGHT_DP}dp")