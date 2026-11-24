# config/navigation_config.py
"""
Единый реестр жёстких правил навигации приложения.
Определяет, куда возвращает кнопка «Назад» с каждого экрана.
"""
import time
from kivy.clock import Clock
from kivymd.app import MDApp
from config.logger_config import screen_logger

logger = screen_logger('NavigationConfig')

_last_back_timestamp = 0.0

# Корневые экраны (на них слева кнопка меню, а не стрелка «Назад»)
ROOT_SCREENS = {
    'home',
    'songs',
    'chords',
    'tuner',
    'metronome',
    'favorites',
    'dictionary',
    'profile',
    'search',
    'help',
    'promo',
    'feedback',
    'admin',
}

# Жёсткие привязки: { 'текущий_экран': 'экран_возврата' }
BACK_ROUTES = {
    # Раздел песен и исполнителей
    'artist_songs': 'songs',
    'song_detail': 'artist_songs',
    'search_detail': 'songs',

    # Раздел глобального поиска
    'search_screen_detail': 'search',
    'search_term_detail': 'search',
    'chord_detail': 'search',

    # Раздел избранного
    'favorite_detail': 'favorites',

    # Раздел словаря
    'term_detail': 'dictionary',

    # Раздел администратора и парсеров
    'admin_promo': 'admin',
    'amdm_parser': 'admin',
    'mytabs_parser': 'admin',
    'accord_pro_parser': 'admin',
    'akkordus_parser': 'admin',
    'muzland_parser': 'admin',
    'chordie_parser': 'admin',
    'fivelad_parser': 'admin',
    'akkordbard_parser': 'admin',
    'domhve_parser': 'admin',
    'rushsound_parser': 'admin',
}


def get_back_target(current_screen: str, fallback: str = 'home') -> str:
    """Возвращает целевой экран для кнопки «Назад» по жёсткой таблице."""
    return BACK_ROUTES.get(current_screen, fallback)


def navigate_back(screen_manager, current_screen_name: str = None) -> str:
    global _last_back_timestamp
    if not screen_manager:
        return 'home'

    current = current_screen_name or screen_manager.current

    if current in ROOT_SCREENS:
        logger.debug(f"🛑 Игнорируем navigate_back на корневом экране '{current}'")
        return current

    now = time.monotonic()
    if now - _last_back_timestamp < 0.35:
        logger.debug(f"⏳ Игнорируем повторный вызов navigate_back ({current})")
        return current
    _last_back_timestamp = now

    target = get_back_target(current, fallback='home')

    # Сбрасываем кастомный виджет заголовка в TopNav перед уходом
    app = MDApp.get_running_app()
    if app and hasattr(app, 'top_nav'):
        app.top_nav.clear_custom_title_widget()
        if hasattr(app.top_nav, 'clear_back_button'):
            app.top_nav.clear_back_button()

    if not screen_manager.has_screen(target):
        logger.warning(f"⚠️ Целевой экран '{target}' не найден, переход на 'home'")
        target = 'home'

    logger.info(f"⬅️ Жёсткий маршрут: {current} -> {target}")
    screen_manager.current = target

    # Восстановление состояния целевого экрана после переключения
    target_screen = screen_manager.get_screen(target)
    if target == 'songs' and hasattr(target_screen, 'restore_state'):
        Clock.schedule_once(lambda dt: target_screen.restore_state(), 0.05)
    elif target == 'search' and hasattr(target_screen, 'restore_state'):
        Clock.schedule_once(lambda dt: target_screen.restore_state(), 0.05)

    return target
