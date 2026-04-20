# config/top_nav_config.py
"""
Конфигурация верхней панели навигации
"""
from kivy.metrics import dp


class TopNavConfig:
    """Настройки верхней панели"""

    # Отступ от верха экрана
    TOP_OFFSET = 0.99

    # Размер иконок
    ICON_SIZE = (40, 40)

    # Доступные языки
    LANGUAGES = [
        {'code': 'ru', 'flag': 'rus_png', 'name': 'RU'},
        {'code': 'en', 'flag': 'eng_png', 'name': 'EN'}
    ]

    # Позиция языкового селектора
    LANGUAGE_SELECTOR_POS = {'right': 0.96, 'top': TOP_OFFSET}

    # Пресеты для разных экранов
    SCREEN_PRESETS = {
        'small': {'TOP_OFFSET': 0.92, 'ICON_SIZE': (36, 36)},
        'normal': {'TOP_OFFSET': 0.94, 'ICON_SIZE': (40, 40)},
        'large': {'TOP_OFFSET': 0.95, 'ICON_SIZE': (44, 44)},
        'tablet': {'TOP_OFFSET': 0.96, 'ICON_SIZE': (48, 48)}
    }

    @classmethod
    def apply_preset(cls, preset_name='normal'):
        preset = cls.SCREEN_PRESETS.get(preset_name, cls.SCREEN_PRESETS['normal'])
        cls.TOP_OFFSET = preset.get('TOP_OFFSET', cls.TOP_OFFSET)
        cls.ICON_SIZE = preset.get('ICON_SIZE', cls.ICON_SIZE)
        cls.LANGUAGE_SELECTOR_POS['top'] = cls.TOP_OFFSET
        return cls


top_nav_config = TopNavConfig()