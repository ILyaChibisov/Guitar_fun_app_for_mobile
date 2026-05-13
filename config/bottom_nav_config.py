# config/bottom_nav_config.py
"""
Конфигурация нижней панели - ТОЛЬКО ОТНОСИТЕЛЬНЫЕ значения
"""
from kivy.metrics import sp
from config.layout_config import layout_config
from config.logger_config import get_logger

logger = get_logger('BottomNavConfig')


class BottomNavConfig:
    """Настройки нижней панели - ТОЛЬКО ОТНОСИТЕЛЬНЫЕ значения"""

    # Относительные пропорции (не в dp, а в долях)
    ICON_CONTAINER_RATIO = 0.68  # 68% высоты кнопки под иконку
    TEXT_CONTAINER_RATIO = 0.32  # 32% высоты кнопки под текст
    ICON_SIZE_RATIO = 0.75  # 75% от контейнера иконки

    # Базовый размер шрифта в sp (адаптивный)
    FONT_SIZE = sp(11)

    # Индивидуальные настройки для кнопок
    BUTTONS_CONFIG = {
        'home': {'icon_ratio': 0.70, 'font_size': sp(11), 'text': 'Главная'},
        'songs': {'icon_ratio': 0.70, 'font_size': sp(11), 'text': 'Песни'},
        'chords': {'icon_ratio': 0.68, 'font_size': sp(11), 'text': 'Аккорды'},
        'tuner': {'icon_ratio': 0.68, 'font_size': sp(11), 'text': 'Тюнер'},
        'favorites': {'icon_ratio': 0.68, 'font_size': sp(10), 'text': 'Избранное'},
    }

    @classmethod
    def get_button_config(cls, screen_name):
        """Возвращает настройки для конкретной кнопки"""
        config = cls.BUTTONS_CONFIG.get(screen_name, {})
        result = {
            'icon_height': config.get('icon_ratio', cls.ICON_CONTAINER_RATIO),
            'font_size': config.get('font_size', cls.FONT_SIZE),
            'text': config.get('text', screen_name.capitalize()),
        }
        logger.info(
            f"[BottomNavConfig] get_button_config({screen_name}): icon_height={result['icon_height']}, font_size={result['font_size']}")
        return result

    @classmethod
    def get_panel_height(cls):
        """Возвращает высоту панели из layout_config"""
        height = layout_config.get_bottom_nav_height()
        logger.info(f"[BottomNavConfig] get_panel_height: {height}dp")
        return height


bottom_nav_config = BottomNavConfig()