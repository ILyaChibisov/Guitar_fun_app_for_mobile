# main.py
"""
Главный файл приложения GuitarApp
Современное приложение для гитаристов
"""
import os

# Настройка логирования (должна быть первой)
from config.logger_config import setup_logging, app_logger

setup_logging(level='debug')  # При разработке - debug, при релизе - info

# Импорты Kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.logger import Logger

# Настройки окна для разработки
if os.name == 'nt':  # Windows
    Window.size = (400, 750)  # Размер современного телефона
    Window.top = 50
    Window.left = 50

# Наши модули
from config.app_config import config
from config.theme import theme
from screens.manager import setup_screen_manager
from screens.components.bottom_nav import BottomNav

# Создаём логгер приложения
logger = app_logger()


class GuitarApp(App):
    """Главный класс приложения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Сначала вызываем родительский конструктор!
        self.title = config.APP_NAME

        # Сохраняем ссылку на экземпляр
        GuitarApp._instance = self

        # Логируем запуск ПОСЛЕ super().__init__
        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК {config.APP_NAME} v{config.VERSION}')
        logger.info('🎸 ' + '=' * 50)

    def build(self):
        """Создаёт интерфейс приложения"""
        logger.debug('Создание интерфейса...')

        from kivy.uix.boxlayout import BoxLayout

        # Главный контейнер
        root = BoxLayout(orientation='vertical')

        # Создаём менеджер экранов
        self.screen_manager = setup_screen_manager()
        root.add_widget(self.screen_manager)

        # Создаём нижнюю навигацию
        self.bottom_nav = BottomNav(self.screen_manager)
        root.add_widget(self.bottom_nav)

        logger.info('Интерфейс успешно создан')
        return root

    def on_start(self):
        """Вызывается после запуска - здесь уже должен быть доступен platform"""
        # Проверяем, существует ли атрибут platform
        if hasattr(self, 'platform'):
            logger.info(f'🎸 Платформа: {self.platform}')
        else:
            logger.info('🎸 Платформа: Windows (определено по ОС)')
        logger.info('Приложение запущено и готово к работе')

    def on_pause(self):
        """При сворачивании"""
        logger.debug('Приложение свернуто')
        return True

    def on_resume(self):
        """При возвращении"""
        logger.debug('Приложение восстановлено')

    def on_stop(self):
        """При закрытии"""
        logger.info('Приложение закрыто')
        logger.info('🎸 ' + '=' * 50)


if __name__ == '__main__':
    GuitarApp().run()