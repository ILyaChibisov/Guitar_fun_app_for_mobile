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


bottom_nav_config = BottomNavConfig()