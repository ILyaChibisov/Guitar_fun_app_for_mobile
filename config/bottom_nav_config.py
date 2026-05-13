# config/bottom_nav_config.py
"""
Конфигурация нижней панели навигации - использует layout_config
"""
from kivy.metrics import dp, sp
from config.layout_config import layout_config


class BottomNavConfig:
    """Настройки нижней панели - берёт размеры из layout_config"""

    # Размеры берутся из layout_config
    PANEL_HEIGHT = layout_config.get_bottom_nav_height()

    # Отступы
    PANEL_PADDING = [8, 4, 8, 4]
    PANEL_SPACING = 4

    # Пропорции внутри кнопки (относительные)
    ICON_CONTAINER_RATIO = 0.68  # 68% высоты кнопки под иконку
    TEXT_CONTAINER_RATIO = 0.32  # 32% высоты кнопки под текст
    ICON_SIZE_RATIO = 0.75  # 75% от контейнера иконки

    # Шрифт (sp - адаптируется под настройки пользователя)
    FONT_SIZE = sp(11)

    # Индивидуальные настройки для каждой кнопки
    BUTTONS_CONFIG = {
        'home': {'icon_ratio': 0.72, 'text': 'Главная'},
        'songs': {'icon_ratio': 0.72, 'text': 'Песни'},
        'chords': {'icon_ratio': 0.70, 'text': 'Аккорды'},
        'tuner': {'icon_ratio': 0.70, 'text': 'Тюнер'},
        'favorites': {'icon_ratio': 0.70, 'text': 'Избранное'},
    }

    @classmethod
    def get_button_config(cls, screen_name):
        config = cls.BUTTONS_CONFIG.get(screen_name, {})
        return {
            'icon_height': config.get('icon_ratio', cls.ICON_CONTAINER_RATIO),
            'font_size': cls.FONT_SIZE,
            'text': config.get('text', screen_name),
        }


bottom_nav_config = BottomNavConfig()