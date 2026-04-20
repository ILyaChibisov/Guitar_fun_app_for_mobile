# config/bottom_nav_config.py
"""
Конфигурация нижней панели навигации
Здесь можно менять все параметры панели и иконок
"""
from kivy.metrics import dp, sp


class BottomNavConfig:
    """Настройки нижней панели"""

    # ========== НАСТРОЙКИ ПАНЕЛИ ==========
    PANEL_HEIGHT = 52  # Высота панели (40-70)
    PANEL_PADDING = [4, 2, 4, 2]  # Отступы [лево, верх, право, низ]
    PANEL_SPACING = 0  # Расстояние между кнопками (0-8)
    PANEL_BG_COLOR = [1, 1, 1, 1]  # Цвет фона (белый)

    # ========== НАСТРОЙКИ ПО УМОЛЧАНИЮ ==========
    DEFAULT_ICON_SIZE = 0.75
    DEFAULT_ICON_CONTAINER_HEIGHT = 0.7
    DEFAULT_FONT_SIZE = 7
    DEFAULT_SPACING = 0
    DEFAULT_TOP_PADDING = 0

    # ========== НАСТРОЙКИ ДЛЯ РАЗНЫХ ЭКРАНОВ (ПРЕСЕТЫ) ==========
    SCREEN_PRESETS = {
        'small': {  # Маленькие телефоны (ширина < 340)
            'PANEL_HEIGHT': 48,
            'PANEL_PADDING': [2, 1, 2, 1],
            'PANEL_SPACING': 0,
            'DEFAULT_ICON_SIZE': 0.70,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.68,
            'DEFAULT_FONT_SIZE': 6,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        },
        'normal': {  # Средние телефоны (ширина 340-400)
            'PANEL_HEIGHT': 52,
            'PANEL_PADDING': [4, 2, 4, 2],
            'PANEL_SPACING': 0,
            'DEFAULT_ICON_SIZE': 0.75,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.70,
            'DEFAULT_FONT_SIZE': 7,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        },
        'large': {  # Большие телефоны (ширина 400-600)
            'PANEL_HEIGHT': 56,
            'PANEL_PADDING': [6, 2, 6, 2],
            'PANEL_SPACING': 2,
            'DEFAULT_ICON_SIZE': 0.78,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.72,
            'DEFAULT_FONT_SIZE': 8,
            'DEFAULT_SPACING': 1,
            'DEFAULT_TOP_PADDING': 1
        },
        'tablet': {  # Планшеты (ширина > 600)
            'PANEL_HEIGHT': 64,
            'PANEL_PADDING': [8, 4, 8, 4],
            'PANEL_SPACING': 4,
            'DEFAULT_ICON_SIZE': 0.85,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.75,
            'DEFAULT_FONT_SIZE': 10,
            'DEFAULT_SPACING': 2,
            'DEFAULT_TOP_PADDING': 2
        }
    }

    # ========== ИНДИВИДУАЛЬНЫЕ НАСТРОЙКИ ДЛЯ КАЖДОЙ КНОПКИ ==========
    BUTTONS_CONFIG = {
        'songs': {
            'icon_size': 0.90,
            'icon_height': 0.75,
            'font_size': 8,
            'spacing': 1,
            'top_padding': 2
        },
        'chords': {
            'icon_size': 0.85,
            'icon_height': 0.72,
            'font_size': 8,
            'spacing': 1,
            'top_padding': 2
        },
        'tuner': {
            'icon_size': 0.85,
            'icon_height': 0.72,
            'font_size': 8,
            'spacing': 1,
            'top_padding': 2
        },
        'dictionary': {
            'icon_size': 0.80,
            'icon_height': 0.70,
            'font_size': 7,
            'spacing': 1,
            'top_padding': 2
        },
        'favorites': {
            'icon_size': 0.85,
            'icon_height': 0.72,
            'font_size': 7,
            'spacing': 1,
            'top_padding': 2
        },
    }

    @classmethod
    def apply_preset(cls, preset_name='normal'):
        """Применяет предустановленные настройки"""
        preset = cls.SCREEN_PRESETS.get(preset_name, cls.SCREEN_PRESETS['normal'])

        cls.PANEL_HEIGHT = preset.get('PANEL_HEIGHT', cls.PANEL_HEIGHT)
        cls.PANEL_PADDING = preset.get('PANEL_PADDING', cls.PANEL_PADDING)
        cls.PANEL_SPACING = preset.get('PANEL_SPACING', cls.PANEL_SPACING)
        cls.DEFAULT_ICON_SIZE = preset.get('DEFAULT_ICON_SIZE', cls.DEFAULT_ICON_SIZE)
        cls.DEFAULT_ICON_CONTAINER_HEIGHT = preset.get('DEFAULT_ICON_CONTAINER_HEIGHT',
                                                       cls.DEFAULT_ICON_CONTAINER_HEIGHT)
        cls.DEFAULT_FONT_SIZE = preset.get('DEFAULT_FONT_SIZE', cls.DEFAULT_FONT_SIZE)
        cls.DEFAULT_SPACING = preset.get('DEFAULT_SPACING', cls.DEFAULT_SPACING)
        cls.DEFAULT_TOP_PADDING = preset.get('DEFAULT_TOP_PADDING', cls.DEFAULT_TOP_PADDING)

        return cls

    @classmethod
    def get_button_config(cls, screen_name):
        """Возвращает настройки для конкретной кнопки"""
        button_config = cls.BUTTONS_CONFIG.get(screen_name, {})
        return {
            'icon_size': button_config.get('icon_size', cls.DEFAULT_ICON_SIZE),
            'icon_height': button_config.get('icon_height', cls.DEFAULT_ICON_CONTAINER_HEIGHT),
            'font_size': button_config.get('font_size', cls.DEFAULT_FONT_SIZE),
            'spacing': button_config.get('spacing', cls.DEFAULT_SPACING),
            'top_padding': button_config.get('top_padding', cls.DEFAULT_TOP_PADDING)
        }

    @classmethod
    def update_button_config(cls, screen_name, **kwargs):
        """Обновляет настройки конкретной кнопки"""
        if screen_name not in cls.BUTTONS_CONFIG:
            cls.BUTTONS_CONFIG[screen_name] = {}

        for key, value in kwargs.items():
            if key in ['icon_size', 'icon_height', 'font_size', 'spacing', 'top_padding']:
                cls.BUTTONS_CONFIG[screen_name][key] = value

        return cls

    @classmethod
    def update_global_config(cls, **kwargs):
        """Обновляет глобальные настройки"""
        for key, value in kwargs.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
        return cls


# Создаём экземпляр для удобства
bottom_nav_config = BottomNavConfig()