# config/bottom_nav_config.py
"""
Конфигурация нижней панели навигации
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window


class BottomNavConfig:
    """Настройки нижней панели"""

    # ========== БАЗОВЫЕ РАЗМЕРЫ ==========
    PANEL_HEIGHT = 76  # высота панели с иконками
    PANEL_PADDING = [4, 0, 4, 0]  # [лево, верх, право, низ] - верхний отступ 0
    PANEL_SPACING = 0

    # ========== НАСТРОЙКИ ПО УМОЛЧАНИЮ ==========
    DEFAULT_ICON_SIZE = 0.75
    DEFAULT_ICON_CONTAINER_HEIGHT = 0.75
    DEFAULT_FONT_SIZE = 12
    DEFAULT_SPACING = 0
    DEFAULT_TOP_PADDING = 0  # убираем отступ сверху для кнопок

    # ========== НАСТРОЙКИ ДЛЯ РАЗНЫХ ЭКРАНОВ (ПРЕСЕТЫ) ==========
    SCREEN_PRESETS = {
        'small': {
            'PANEL_HEIGHT': 64,
            'PANEL_PADDING': [2, 0, 2, 0],
            'PANEL_SPACING': 0,
            'DEFAULT_ICON_SIZE': 0.70,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.70,
            'DEFAULT_FONT_SIZE': 10,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        },
        'normal': {
            'PANEL_HEIGHT': 70,
            'PANEL_PADDING': [4, 0, 4, 0],
            'PANEL_SPACING': 0,
            'DEFAULT_ICON_SIZE': 0.72,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.72,
            'DEFAULT_FONT_SIZE': 11,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        },
        'large': {
            'PANEL_HEIGHT': 76,
            'PANEL_PADDING': [6, 0, 6, 0],
            'PANEL_SPACING': 0,
            'DEFAULT_ICON_SIZE': 0.75,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.75,
            'DEFAULT_FONT_SIZE': 12,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        },
        'tablet': {
            'PANEL_HEIGHT': 84,
            'PANEL_PADDING': [8, 0, 8, 0],
            'PANEL_SPACING': 2,
            'DEFAULT_ICON_SIZE': 0.78,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.78,
            'DEFAULT_FONT_SIZE': 14,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        }
    }

    # ========== ИНДИВИДУАЛЬНЫЕ НАСТРОЙКИ ДЛЯ КАЖДОЙ КНОПКИ ==========
    BUTTONS_CONFIG = {
        'home': {
            'icon_size': 0.68,
            'icon_height': 0.72,
            'font_size': 11,
            'spacing': 1,
            'top_padding': 0
        },
        'songs': {
            'icon_size': 0.68,
            'icon_height': 0.72,
            'font_size': 11,
            'spacing': 1,
            'top_padding': 0
        },
        'chords': {
            'icon_size': 0.68,
            'icon_height': 0.70,
            'font_size': 11,
            'spacing': 1,
            'top_padding': 0
        },
        'tuner': {
            'icon_size': 0.68,
            'icon_height': 0.70,
            'font_size': 11,
            'spacing': 1,
            'top_padding': 0
        },
        'favorites': {
            'icon_size': 0.68,
            'icon_height': 0.70,
            'font_size': 10,
            'spacing': 1,
            'top_padding': 0
        },
    }

    @classmethod
    def get_preset_for_screen(cls, width, height):
        """Определяет пресет по размеру экрана"""
        if platform == 'win':
            return 'large'

        min_dimension = min(width, height)

        if min_dimension < 480:
            return 'small'
        elif min_dimension < 720:
            return 'normal'
        elif min_dimension < 1000:
            return 'large'
        else:
            return 'tablet'

    @classmethod
    def apply_preset(cls, preset_name='large'):
        """Применяет предустановленные настройки"""
        preset = cls.SCREEN_PRESETS.get(preset_name, cls.SCREEN_PRESETS['large'])

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