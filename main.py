# main.py
"""
Главный файл приложения GuitarApp
С верхней и нижней навигацией
"""
import os

# Настройка логирования
from config.logger_config import setup_logging, app_logger

setup_logging(level='debug')

# Импорты Kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger

# Настройки окна для разработки
if os.name == 'nt':  # Windows
    Window.size = (400, 750)
    Window.top = 50
    Window.left = 50

# Наши модули
from config.app_config import config
from config.theme import theme
from screens.manager import setup_screen_manager
from screens.components.bottom_nav import BottomNav
from screens.components.top_nav import TopNav  # Добавляем верхнюю навигацию

# Создаём логгер приложения
logger = app_logger()


class GuitarApp(App):
    """Главный класс приложения"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = config.APP_NAME
        GuitarApp._instance = self

        logger.info('🎸 ' + '=' * 50)
        logger.info(f'🎸 ЗАПУСК {config.APP_NAME} v{config.VERSION}')
        logger.info('🎸 ' + '=' * 50)

    def build(self):
        """Создаёт интерфейс приложения"""
        logger.debug('Создание интерфейса...')

        # Главный контейнер
        root = BoxLayout(orientation='vertical')

        # Создаём менеджер экранов
        self.screen_manager = setup_screen_manager()

        # Создаём верхнюю навигацию
        self.top_nav = TopNav(self.screen_manager)
        root.add_widget(self.top_nav)

        # Добавляем менеджер экранов
        root.add_widget(self.screen_manager)

        # Создаём нижнюю навигацию
        self.bottom_nav = BottomNav(self.screen_manager)
        root.add_widget(self.bottom_nav)

        logger.info('Интерфейс успешно создан')
        return root

    def on_start(self):
        """Вызывается после запуска"""
        # Определяем платформу
        platform_name = 'Windows' if os.name == 'nt' else 'Другая'
        if hasattr(self, 'platform'):
            platform_name = self.platform

        logger.info(f'🎸 Платформа: {platform_name}')
        logger.info('Приложение запущено и готово к работе')

    def on_pause(self):
        logger.debug('Приложение свернуто')
        return True

    def on_resume(self):
        logger.debug('Приложение восстановлено')

    def on_stop(self):
        logger.info('Приложение закрыто')
        logger.info('🎸 ' + '=' * 50)


if __name__ == '__main__':
    GuitarApp().run()