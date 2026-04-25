# config/top_nav_config.py
"""
Конфигурация верхней панели навигации
"""
from kivy.metrics import dp


class TopNavConfig:
    """Настройки верхней панели"""

    # Тип панели: small, medium, large
    BAR_TYPE = "small"

    # Прозрачность фона (0 - полностью прозрачный, 1 - непрозрачный)
    BG_COLOR = [0, 0, 0, 0]  # Полностью прозрачный

    # Высота тени (0 - без тени)
    ELEVATION = 0

    # Выравнивание заголовка: "left", "center"
    TITLE_ALIGNMENT = "center"

    # Размер шрифта заголовка
    TITLE_FONT_SIZE = 18  # sp

    # Доступные языки
    LANGUAGES = [
        {'code': 'ru', 'flag': 'rus_png', 'name': 'RU'},
        {'code': 'en', 'flag': 'eng_png', 'name': 'EN'}
    ]

    # Размер иконок в верхней панели
    ICON_SIZE = (dp(40), dp(40))

    # Пресеты для разных размеров экрана
    SCREEN_PRESETS = {
        'small': {
            'BAR_TYPE': 'small',
            'TITLE_FONT_SIZE': 14,
            'ICON_SIZE': (dp(32), dp(32))
        },
        'normal': {
            'BAR_TYPE': 'small',
            'TITLE_FONT_SIZE': 16,
            'ICON_SIZE': (dp(36), dp(36))
        },
        'large': {
            'BAR_TYPE': 'medium',
            'TITLE_FONT_SIZE': 18,
            'ICON_SIZE': (dp(40), dp(40))
        },
        'tablet': {
            'BAR_TYPE': 'large',
            'TITLE_FONT_SIZE': 20,
            'ICON_SIZE': (dp(44), dp(44))
        }
    }

    @classmethod
    def apply_preset(cls, preset_name='normal'):
        """Применяет предустановленные настройки для размера экрана"""
        preset = cls.SCREEN_PRESETS.get(preset_name, cls.SCREEN_PRESETS['normal'])
        cls.BAR_TYPE = preset.get('BAR_TYPE', cls.BAR_TYPE)
        cls.TITLE_FONT_SIZE = preset.get('TITLE_FONT_SIZE', cls.TITLE_FONT_SIZE)
        cls.ICON_SIZE = preset.get('ICON_SIZE', cls.ICON_SIZE)
        return cls


top_nav_config = TopNavConfig()