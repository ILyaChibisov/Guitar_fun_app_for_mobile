# config/bottom_nav_config.py
"""
Конфигурация нижней панели навигации
Разные настройки для Windows и Android
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window


class BottomNavConfig:
    """Настройки нижней панели - разные для разных платформ"""

    # ========== НАСТРОЙКИ ДЛЯ WINDOWS (разработка/отладка) ==========
    WINDOWS_CONFIG = {
        'PANEL_HEIGHT': 76,
        'PANEL_PADDING': [8, 4, 8, 4],
        'PANEL_SPACING': 4,
        'DEFAULT_ICON_SIZE': 0.75,
        'DEFAULT_ICON_CONTAINER_HEIGHT': 0.72,
        'DEFAULT_FONT_SIZE': 12,
        'DEFAULT_SPACING': 2,
        'DEFAULT_TOP_PADDING': 4
    }

    # ========== НАСТРОЙКИ ДЛЯ ANDROID (реальное устройство) ==========
    ANDROID_CONFIG = {
        'PANEL_HEIGHT': 56,  # меньше, так как плотность экрана выше
        'PANEL_PADDING': [6, 3, 6, 3],
        'PANEL_SPACING': 3,
        'DEFAULT_ICON_SIZE': 0.68,
        'DEFAULT_ICON_CONTAINER_HEIGHT': 0.65,
        'DEFAULT_FONT_SIZE': 10,  # sp - адаптируется под плотность
        'DEFAULT_SPACING': 2,
        'DEFAULT_TOP_PADDING': 3
    }

    # ========== ТЕКУЩАЯ КОНФИГУРАЦИЯ (заполняется при инициализации) ==========
    PANEL_HEIGHT = 76
    PANEL_PADDING = [8, 4, 8, 4]
    PANEL_SPACING = 4
    DEFAULT_ICON_SIZE = 0.75
    DEFAULT_ICON_CONTAINER_HEIGHT = 0.72
    DEFAULT_FONT_SIZE = 12
    DEFAULT_SPACING = 2
    DEFAULT_TOP_PADDING = 4

    # ========== НАСТРОЙКИ ДЛЯ РАЗНЫХ ЭКРАНОВ (ПРЕСЕТЫ) ==========
    SCREEN_PRESETS = {
        'small': {
            'PANEL_HEIGHT': 48,
            'PANEL_PADDING': [4, 2, 4, 2],
            'PANEL_SPACING': 2,
            'DEFAULT_ICON_SIZE': 0.62,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.60,
            'DEFAULT_FONT_SIZE': 9,
            'DEFAULT_SPACING': 1,
            'DEFAULT_TOP_PADDING': 2
        },
        'normal': {
            'PANEL_HEIGHT': 52,
            'PANEL_PADDING': [6, 3, 6, 3],
            'PANEL_SPACING': 3,
            'DEFAULT_ICON_SIZE': 0.65,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.62,
            'DEFAULT_FONT_SIZE': 10,
            'DEFAULT_SPACING': 2,
            'DEFAULT_TOP_PADDING': 3
        },
        'large': {
            'PANEL_HEIGHT': 56,
            'PANEL_PADDING': [8, 4, 8, 4],
            'PANEL_SPACING': 4,
            'DEFAULT_ICON_SIZE': 0.68,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.65,
            'DEFAULT_FONT_SIZE': 11,
            'DEFAULT_SPACING': 2,
            'DEFAULT_TOP_PADDING': 4
        },
        'tablet': {
            'PANEL_HEIGHT': 64,
            'PANEL_PADDING': [12, 6, 12, 6],
            'PANEL_SPACING': 6,
            'DEFAULT_ICON_SIZE': 0.70,
            'DEFAULT_ICON_CONTAINER_HEIGHT': 0.68,
            'DEFAULT_FONT_SIZE': 12,
            'DEFAULT_SPACING': 3,
            'DEFAULT_TOP_PADDING': 5
        }
    }

    # ========== ИНДИВИДУАЛЬНЫЕ НАСТРОЙКИ ДЛЯ КАЖДОЙ КНОПКИ ==========
    BUTTONS_CONFIG = {
        'home': {
            'icon_size': 0.60,
            'icon_height': 0.68,
            'font_size': 10,
            'spacing': 2,
            'top_padding': 4
        },
        'songs': {
            'icon_size': 0.60,
            'icon_height': 0.68,
            'font_size': 10,
            'spacing': 2,
            'top_padding': 4
        },
        'chords': {
            'icon_size': 0.60,
            'icon_height': 0.66,
            'font_size': 10,
            'spacing': 2,
            'top_padding': 4
        },
        'tuner': {
            'icon_size': 0.60,
            'icon_height': 0.66,
            'font_size': 10,
            'spacing': 2,
            'top_padding': 4
        },
        'favorites': {
            'icon_size': 0.60,
            'icon_height': 0.66,
            'font_size': 9,
            'spacing': 2,
            'top_padding': 4
        },
    }

    @classmethod
    def init_for_platform(cls):
        """Инициализирует настройки в зависимости от платформы"""
        if platform == 'android':
            config = cls.ANDROID_CONFIG
            logger.info("BottomNavConfig: загружены настройки для Android")
        else:
            config = cls.WINDOWS_CONFIG
            logger.info("BottomNavConfig: загружены настройки для Windows")

        cls.PANEL_HEIGHT = config.get('PANEL_HEIGHT', cls.PANEL_HEIGHT)
        cls.PANEL_PADDING = config.get('PANEL_PADDING', cls.PANEL_PADDING)
        cls.PANEL_SPACING = config.get('PANEL_SPACING', cls.PANEL_SPACING)
        cls.DEFAULT_ICON_SIZE = config.get('DEFAULT_ICON_SIZE', cls.DEFAULT_ICON_SIZE)
        cls.DEFAULT_ICON_CONTAINER_HEIGHT = config.get('DEFAULT_ICON_CONTAINER_HEIGHT',
                                                       cls.DEFAULT_ICON_CONTAINER_HEIGHT)
        cls.DEFAULT_FONT_SIZE = config.get('DEFAULT_FONT_SIZE', cls.DEFAULT_FONT_SIZE)
        cls.DEFAULT_SPACING = config.get('DEFAULT_SPACING', cls.DEFAULT_SPACING)
        cls.DEFAULT_TOP_PADDING = config.get('DEFAULT_TOP_PADDING', cls.DEFAULT_TOP_PADDING)

        return cls

    @classmethod
    def get_preset_for_screen(cls, width, height):
        """
        Определяет пресет по размеру экрана
        """
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
    def apply_preset(cls, preset_name='normal'):
        """Применяет предустановленные настройки поверх платформенных"""
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


# Импортируем logger после определения класса (чтобы избежать циклического импорта)
from config.logger_config import get_logger

logger = get_logger('BottomNavConfig')

# Инициализируем настройки в зависимости от платформы
BottomNavConfig.init_for_platform()

# Создаём экземпляр для удобства
bottom_nav_config = BottomNavConfig()