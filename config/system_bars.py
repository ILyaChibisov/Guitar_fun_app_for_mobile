# config/system_bars.py
"""
Определение высоты системных панелей Android
"""
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from config.logger_config import get_logger

logger = get_logger('SystemBars')

_status_bar_height_px = None
_nav_bar_height_px = None

# Константы для Windows (в пикселях)
WINDOWS_STATUS_BAR_HEIGHT_PX = 30
WINDOWS_NAV_BAR_HEIGHT_PX = 0  # На Windows нет системного нав-бара


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
                logger.info(f"Высота статус-бара (Android): {_status_bar_height_px}px")
                return _status_bar_height_px
        except Exception as e:
            logger.error(f"Ошибка получения высоты статус-бара: {e}")
            # fallback значения для разных плотностей
            density = Window.dpi / 160 if Window.dpi else 2.0
            _status_bar_height_px = int(24 * density)
            logger.info(f"Высота статус-бара (fallback): {_status_bar_height_px}px")
            return _status_bar_height_px

    # Windows
    _status_bar_height_px = WINDOWS_STATUS_BAR_HEIGHT_PX
    logger.info(f"Высота статус-бара (Windows): {_status_bar_height_px}px")
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

            # Пробуем получить высоту нав-бара
            resource_id = Resources.getSystem().getIdentifier(
                'navigation_bar_height', 'dimen', 'android'
            )
            if resource_id > 0:
                _nav_bar_height_px = Resources.getSystem().getDimensionPixelSize(resource_id)
                logger.info(f"Высота нав-бара (Android): {_nav_bar_height_px}px")
                return _nav_bar_height_px
        except Exception as e:
            logger.error(f"Ошибка получения высоты нав-бара: {e}")

        # Проверяем, есть ли вообще нав-бар (для устройств с жестами)
        try:
            from android import mActivity
            from jnius import autoclass
            View = autoclass('android.view.View')
            decorView = mActivity.getWindow().getDecorView()

            # Для жестов нав-бар может быть скрыт
            _nav_bar_height_px = 0
            logger.info("Нав-бар не обнаружен (вероятно, используются жесты)")
            return _nav_bar_height_px
        except:
            pass

        # fallback
        density = Window.dpi / 160 if Window.dpi else 2.0
        _nav_bar_height_px = int(48 * density)
        logger.info(f"Высота нав-бара (fallback): {_nav_bar_height_px}px")
        return _nav_bar_height_px

    # Windows (нет нав-бара)
    _nav_bar_height_px = WINDOWS_NAV_BAR_HEIGHT_PX
    logger.info(f"Высота нав-бара (Windows): {_nav_bar_height_px}px")
    return _nav_bar_height_px


def get_status_bar_height():
    """Возвращает высоту статус-бара в dp"""
    return dp(get_status_bar_height_px())


def get_navigation_bar_height():
    """Возвращает высоту навигационной панели в dp"""
    return dp(get_navigation_bar_height_px())


def get_status_bar_height_px_direct():
    """Возвращает высоту статус-бара в пикселях (без dp)"""
    return get_status_bar_height_px()


def get_navigation_bar_height_px_direct():
    """Возвращает высоту навигационной панели в пикселях (без dp)"""
    return get_navigation_bar_height_px()


def set_simulation_heights(status_px=30, nav_px=0):
    """Для Windows: установить свои значения симуляции (в пикселях)"""
    global _status_bar_height_px, _nav_bar_height_px, WINDOWS_STATUS_BAR_HEIGHT_PX, WINDOWS_NAV_BAR_HEIGHT_PX
    if platform != 'android':
        WINDOWS_STATUS_BAR_HEIGHT_PX = status_px
        WINDOWS_NAV_BAR_HEIGHT_PX = nav_px
        _status_bar_height_px = status_px
        _nav_bar_height_px = nav_px
        logger.info(f"Симуляция обновлена: статус-бар={status_px}px, нав-бар={nav_px}px")