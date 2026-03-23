# screens/manager.py
"""
Настройка ScreenManager (упрощённая, так как теперь используем MDBottomNavigation)
"""
from kivy.uix.screenmanager import ScreenManager
from config.logger_config import get_logger

logger = get_logger('ScreenManager')

def setup_screen_manager():
    """Создаёт и настраивает менеджер экранов"""
    sm = ScreenManager()
    logger.info('ScreenManager создан')
    return sm