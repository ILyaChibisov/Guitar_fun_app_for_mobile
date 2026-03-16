# config/logger_config.py
"""
Настройки логирования для приложения
"""
import os
from kivy.logger import Logger


def setup_logging(level='debug'):
    """
    Настройка уровня логирования

    Args:
        level: 'trace', 'debug', 'info', 'warning', 'error', 'critical'
    """
    os.environ['KIVY_LOG_LEVEL'] = level

    # Логируем сам факт настройки
    Logger.info(f'Config: Логирование настроено на уровень {level}')

    # Можно добавить свои кастомные настройки
    Logger.info('Config: Логгер инициализирован')


def get_logger(component_name):
    """
    Получить логгер для конкретного компонента

    Args:
        component_name: Имя компонента (будет в квадратных скобках)

    Returns:
        Объект Logger с префиксом компонента
    """

    # Создаем класс-обертку для удобного логирования с префиксом
    class ComponentLogger:
        def __init__(self, name):
            self.name = name

        def trace(self, message):
            Logger.trace(f'{self.name}: {message}')

        def debug(self, message):
            Logger.debug(f'{self.name}: {message}')

        def info(self, message):
            Logger.info(f'{self.name}: {message}')

        def warning(self, message):
            Logger.warning(f'{self.name}: {message}')

        def error(self, message):
            Logger.error(f'{self.name}: {message}')

        def critical(self, message):
            Logger.critical(f'{self.name}: {message}')

        def exception(self, message):
            Logger.exception(f'{self.name}: {message}')

    return ComponentLogger(component_name)


# Удобные сокращения для основных компонентов
def app_logger():
    return get_logger('App')


def screen_logger(screen_name):
    return get_logger(f'Screen:{screen_name}')


def tuner_logger():
    return get_logger('Tuner')


def chords_logger():
    return get_logger('Chords')


def network_logger():
    return get_logger('Network')