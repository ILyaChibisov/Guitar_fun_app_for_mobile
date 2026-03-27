# screens/manager.py
from kivy.uix.screenmanager import ScreenManager
from config.logger_config import get_logger

logger = get_logger('ScreenManager')

def setup_screen_manager():
    sm = ScreenManager()
    logger.info('ScreenManager создан')
    return sm