# config/system_bars.py
"""
Определение высоты системных панелей Android с полной диагностикой
"""
from kivy.utils import platform
from kivy.metrics import dp
from kivy.core.window import Window
from config.logger_config import get_logger

logger = get_logger('SystemBars')

_status_bar_height_dp = None
_nav_bar_height_dp = None

# ============ КОНСТАНТЫ ДЛЯ WINDOWS ============
WINDOWS_STATUS_BAR_HEIGHT_DP = 0  # ← НЕТ СТАТУС-БАРА!
WINDOWS_NAV_BAR_HEIGHT_DP = 48    # ← ЕСТЬ СИСТЕМНАЯ ПАНЕЛЬ СНИЗУ
GESTURE_NAV_BAR_HEIGHT_DP = 16


def get_screen_density():
    """Возвращает плотность экрана (scale factor)"""
    try:
        if platform == 'android':
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')
            density = Resources.getSystem().getDisplayMetrics().density

            metrics = Resources.getSystem().getDisplayMetrics()
            logger.info(f"[SystemBars] 📱 DisplayMetrics: widthPixels={metrics.widthPixels}, heightPixels={metrics.heightPixels}, densityDpi={metrics.densityDpi}")
            logger.info(f"[SystemBars] 📱 Плотность экрана (Android): {density:.3f}")
            return density
        else:
            density = Window.dpi / 160 if Window.dpi else 1.0
            logger.info(f"[SystemBars] 💻 Плотность экрана (Windows): {density:.3f} (dpi={Window.dpi})")
            return density
    except Exception as e:
        logger.error(f"Ошибка получения плотности экрана: {e}")
        return Window.dpi / 160 if Window.dpi else 1.0


def get_status_bar_height():
    """
    Возвращает высоту статус-бара в dp
    На Windows: 0 (нет статус-бара)
    """
    global _status_bar_height_dp

    if _status_bar_height_dp is not None:
        return _status_bar_height_dp

    logger.info("[SystemBars] 🔍 НАЧАЛО ОПРЕДЕЛЕНИЯ ВЫСОТЫ СТАТУС-БАРА")

    if platform == 'android':
        try:
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')

            resource_id = Resources.getSystem().getIdentifier(
                'status_bar_height', 'dimen', 'android'
            )
            logger.info(f"[SystemBars] 🔍 Resource ID статус-бара: {resource_id}")

            if resource_id > 0:
                px = Resources.getSystem().getDimensionPixelSize(resource_id)
                density = get_screen_density()
                _status_bar_height_dp = px / density
                logger.info(f"[SystemBars] ✅ Статус-бар (ресурсы): {px}px = {_status_bar_height_dp:.1f}dp")
                return _status_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка получения высоты статус-бара: {e}")

        # Альтернативные способы для Android...
        try:
            from android import mActivity
            from jnius import autoclass
            View = autoclass('android.view.View')
            decorView = mActivity.getWindow().getDecorView()

            if hasattr(decorView, 'getRootWindowInsets'):
                insets = decorView.getRootWindowInsets()
                if insets:
                    status_height = insets.getStatusBarHeight()
                    if status_height > 0:
                        density = get_screen_density()
                        _status_bar_height_dp = status_height / density
                        logger.info(f"[SystemBars] ✅ Статус-бар (Insets): {status_height}px = {_status_bar_height_dp:.1f}dp")
                        return _status_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка альтернативного определения статус-бара: {e}")

        # Значение по умолчанию для Android
        _status_bar_height_dp = 24
        logger.warning(f"[SystemBars] ⚠️ Android: используем значение по умолчанию: {_status_bar_height_dp}dp")
    else:
        # ============ WINDOWS: НЕТ СТАТУС-БАРА ============
        _status_bar_height_dp = WINDOWS_STATUS_BAR_HEIGHT_DP  # 0
        logger.info(f"[SystemBars] 💻 Статус-бар (Windows): {_status_bar_height_dp}dp (отсутствует)")

    return _status_bar_height_dp


def get_navigation_bar_height():
    """
    Возвращает высоту навигационной панели в dp
    На Windows: симуляция 48dp (системная панель снизу)
    """
    global _nav_bar_height_dp

    if _nav_bar_height_dp is not None:
        return _nav_bar_height_dp

    logger.info("[SystemBars] 🔍 НАЧАЛО ОПРЕДЕЛЕНИЯ ВЫСОТЫ НАВ-БАРА")

    if platform == 'android':
        try:
            from android import mActivity
            from jnius import autoclass
            Resources = autoclass('android.content.res.Resources')

            resource_id = Resources.getSystem().getIdentifier(
                'navigation_bar_height', 'dimen', 'android'
            )
            logger.info(f"[SystemBars] 🔍 Resource ID нав-бара: {resource_id}")

            if resource_id > 0:
                px = Resources.getSystem().getDimensionPixelSize(resource_id)
                density = get_screen_density()
                _nav_bar_height_dp = px / density
                logger.info(f"[SystemBars] ✅ Нав-бар: {px}px = {_nav_bar_height_dp:.1f}dp")
                return _nav_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка получения высоты нав-бара: {e}")

        # Альтернативные способы для Android...
        try:
            from android import mActivity
            from jnius import autoclass
            View = autoclass('android.view.View')
            decorView = mActivity.getWindow().getDecorView()

            if hasattr(decorView, 'getRootWindowInsets'):
                insets = decorView.getRootWindowInsets()
                if insets:
                    nav_height = insets.getNavigationBarHeight()
                    if nav_height > 0:
                        density = get_screen_density()
                        _nav_bar_height_dp = nav_height / density
                        logger.info(f"[SystemBars] ✅ Нав-бар (Insets): {nav_height}px = {_nav_bar_height_dp:.1f}dp")
                        return _nav_bar_height_dp

            systemUiVisibility = decorView.getSystemUiVisibility()
            if systemUiVisibility & 0x00000002:
                _nav_bar_height_dp = GESTURE_NAV_BAR_HEIGHT_DP
                logger.info(f"[SystemBars] 🖐️ Режим жестов: {_nav_bar_height_dp}dp")
                return _nav_bar_height_dp
        except Exception as e:
            logger.error(f"Ошибка проверки режима нав-бара: {e}")

        # Значение по умолчанию для Android
        _nav_bar_height_dp = 48
        logger.warning(f"[SystemBars] ⚠️ Android: используем значение по умолчанию: {_nav_bar_height_dp}dp")
    else:
        # ============ WINDOWS: ЕСТЬ СИСТЕМНАЯ ПАНЕЛЬ СНИЗУ ============
        _nav_bar_height_dp = WINDOWS_NAV_BAR_HEIGHT_DP  # 48
        logger.info(f"[SystemBars] 💻 Нав-бар (Windows): {_nav_bar_height_dp}dp (симуляция)")

    return _nav_bar_height_dp


def get_all_system_info():
    """Возвращает ВСЮ информацию о системных панелях для диагностики"""
    info = {
        'platform': platform,
        'window_size': (Window.width, Window.height),
        'window_dpi': Window.dpi,
        'screen_density': get_screen_density(),
        'status_bar_height_dp': get_status_bar_height(),
        'navigation_bar_height_dp': get_navigation_bar_height(),
    }

    density = info['screen_density']
    info['status_bar_height_px'] = info['status_bar_height_dp'] * density
    info['navigation_bar_height_px'] = info['navigation_bar_height_dp'] * density

    logger.info("=" * 70)
    logger.info("📱 ПОЛНАЯ ДИАГНОСТИКА СИСТЕМНЫХ ПАНЕЛЕЙ")
    logger.info("=" * 70)
    logger.info(f"📱 Платформа: {info['platform']}")
    logger.info(f"📱 Размер окна: {info['window_size'][0]} x {info['window_size'][1]} px")
    logger.info(f"📱 DPI: {info['window_dpi']}")
    logger.info(f"📱 Плотность: {info['screen_density']:.3f}")
    logger.info("-" * 40)
    logger.info(f"📊 СТАТУС-БАР: {info['status_bar_height_dp']:.1f}dp = {info['status_bar_height_px']:.0f}px")
    logger.info(f"📊 НАВ-БАР: {info['navigation_bar_height_dp']:.1f}dp = {info['navigation_bar_height_px']:.0f}px")
    logger.info("=" * 70)

    return info


def set_simulation_heights(status_dp=0, nav_dp=48):
    """Для Windows: установить свои значения симуляции (в dp)"""
    global WINDOWS_STATUS_BAR_HEIGHT_DP, WINDOWS_NAV_BAR_HEIGHT_DP
    global _status_bar_height_dp, _nav_bar_height_dp

    if platform != 'android':
        WINDOWS_STATUS_BAR_HEIGHT_DP = status_dp
        WINDOWS_NAV_BAR_HEIGHT_DP = nav_dp
        _status_bar_height_dp = None
        _nav_bar_height_dp = None
        logger.info(f"💻 Симуляция обновлена: статус-бар={status_dp}dp, нав-бар={nav_dp}dp")


def set_gesture_mode(enabled=True):
    """Устанавливает режим жестов (для симуляции на Windows)"""
    if platform != 'android':
        if enabled:
            set_simulation_heights(status_dp=0, nav_dp=GESTURE_NAV_BAR_HEIGHT_DP)
            logger.info(f"🖐️ Режим жестов: нав-бар={GESTURE_NAV_BAR_HEIGHT_DP}dp")
        else:
            set_simulation_heights(status_dp=0, nav_dp=WINDOWS_NAV_BAR_HEIGHT_DP)
            logger.info(f"🔘 Режим кнопок: нав-бар={WINDOWS_NAV_BAR_HEIGHT_DP}dp")