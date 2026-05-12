# config/bottom_nav_config.py
"""
Конфигурация нижней панели навигации - упрощённая для Android
"""
from kivy.metrics import dp, sp
from kivy.utils import platform


class BottomNavConfig:
    """Настройки нижней панели - упрощённые"""

    # Базовые настройки (будут переопределены для Android)
    PANEL_HEIGHT = 56
    PANEL_PADDING = [4, 0, 4, 0]
    PANEL_SPACING = 2
    
    DEFAULT_ICON_SIZE = 0.70
    DEFAULT_ICON_CONTAINER_HEIGHT = 0.68
    DEFAULT_FONT_SIZE = 10
    DEFAULT_SPACING = 2
    DEFAULT_TOP_PADDING = 2

    # Настройки для разных размеров экрана
    SCREEN_PRESETS = {
        'small': {
            'PANEL_HEIGHT': 52,
            'DEFAULT_ICON_SIZE': 0.65,
            'DEFAULT_FONT_SIZE': 9,
        },
        'normal': {
            'PANEL_HEIGHT': 56,
            'DEFAULT_ICON_SIZE': 0.68,
            'DEFAULT_FONT_SIZE': 10,
        },
        'large': {
            'PANEL_HEIGHT': 60,
            'DEFAULT_ICON_SIZE': 0.70,
            'DEFAULT_FONT_SIZE': 10,
        },
        'tablet': {
            'PANEL_HEIGHT': 68,
            'DEFAULT_ICON_SIZE': 0.72,
            'DEFAULT_FONT_SIZE': 11,
        }
    }

    @classmethod
    def apply_preset(cls, preset_name='normal'):
        preset = cls.SCREEN_PRESETS.get(preset_name, cls.SCREEN_PRESETS['normal'])
        cls.PANEL_HEIGHT = preset.get('PANEL_HEIGHT', cls.PANEL_HEIGHT)
        cls.DEFAULT_ICON_SIZE = preset.get('DEFAULT_ICON_SIZE', cls.DEFAULT_ICON_SIZE)
        cls.DEFAULT_FONT_SIZE = preset.get('DEFAULT_FONT_SIZE', cls.DEFAULT_FONT_SIZE)
        return cls

    @classmethod
    def get_button_config(cls, screen_name):
        return {
            'icon_size': cls.DEFAULT_ICON_SIZE,
            'icon_height': 0.65,
            'font_size': cls.DEFAULT_FONT_SIZE,
            'spacing': 1,
            'top_padding': 2
        }


bottom_nav_config = BottomNavConfig()        'normal': {
            'PANEL_HEIGHT': 74,
            'PANEL_PADDING': [4, 0, 4, 0],
            'PANEL_SPACING': 0,
            'DEFAULT_ICON_SIZE': 0.62,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.62,
            'DEFAULT_FONT_SIZE': 10,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        },
        'large': {
            'PANEL_HEIGHT': 80,
            'PANEL_PADDING': [6, 0, 6, 0],
            'PANEL_SPACING': 0,
            'DEFAULT_ICON_SIZE': 0.65,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.65,
            'DEFAULT_FONT_SIZE': 11,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        },
        'tablet': {
            'PANEL_HEIGHT': 88,
            'PANEL_PADDING': [8, 0, 8, 0],
            'PANEL_SPACING': 2,
            'DEFAULT_ICON_SIZE': 0.68,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.68,
            'DEFAULT_FONT_SIZE': 13,
            'DEFAULT_SPACING': 0,
            'DEFAULT_TOP_PADDING': 0
        }
    }

    # ========== ИНДИВИДУАЛЬНЫЕ НАСТРОЙКИ ДЛЯ КАЖДОЙ КНОПКИ ==========
    BUTTONS_CONFIG = {
        'home': {
            'icon_size': 0.60,
            'icon_height': 0.62,
            'font_size': 10,
            'spacing': 1,
            'top_padding': 0
        },
        'songs': {
            'icon_size': 0.60,
            'icon_height': 0.62,
            'font_size': 10,
            'spacing': 1,
            'top_padding': 0
        },
        'chords': {
            'icon_size': 0.60,
            'icon_height': 0.60,
            'font_size': 10,
            'spacing': 1,
            'top_padding': 0
        },
        'tuner': {
            'icon_size': 0.60,
            'icon_height': 0.60,
            'font_size': 10,
            'spacing': 1,
            'top_padding': 0
        },
        'favorites': {
            'icon_size': 0.60,
            'icon_height': 0.60,
            'font_size': 9,
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


# Создаём экземпляр для удобства
bottom_nav_config = BottomNavConfig()
