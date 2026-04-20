# config/top_nav_config.py
"""
Конфигурация верхней панели навигации
"""
from kivy.metrics import dp
from kivy.core.window import Window


class TopNavConfig:
    """Настройки верхней панели"""

    # ===== ОБЩИЕ НАСТРОЙКИ =====
    TOP_OFFSET = 0.94  # Отступ от верха экрана
    ICON_SIZE = (40, 40)  # Размер иконок

    # ===== НАСТРОЙКИ ИКОНОК =====
    # Слева: пользователь
    # Справа: поддержка и выбор языка
    ICON_CONFIGS = [
        {
            'name': 'user',
            'icon_asset': 'profile_png',
            'callback': 'open_profile',
            'pos_hint': {'x': 0.02, 'top': TOP_OFFSET},
            'icon_size': 0.75,
            'icon_offset_x': 0,
            'icon_offset_y': 0
        },
        {
            'name': 'support',
            'icon_asset': 'support_png',
            'callback': 'open_support',
            'pos_hint': {'right': 0.18, 'top': TOP_OFFSET},
            'icon_size': 0.75,
            'icon_offset_x': 0,
            'icon_offset_y': 0
        }
    ]

    # ===== НАСТРОЙКИ ВЫБОРА ЯЗЫКА =====
    LANGUAGE_ICON_SIZE = (65, 32)  # Размер иконки языка
    LANGUAGE_ICON_POS = {'right': 0.97, 'top': TOP_OFFSET}  # Позиция
    LANGUAGES = ['ru', 'en']  # Доступные языки
    DEFAULT_LANG = 'ru'  # Язык по умолчанию

    # Флаги для языков (имена ассетов)
    FLAG_ASSETS = {
        'ru': 'rus_png',  # Русский флаг
        'en': 'eng_png'  # Английский флаг
    }

    # Названия языков для отображения
    LANG_NAMES = {
        'ru': 'Русский',
        'en': 'English'
    }

    # ===== НАСТРОЙКИ ДЛЯ РАЗНЫХ ЭКРАНОВ =====
    SCREEN_PRESETS = {
        'small': {
            'TOP_OFFSET': 0.92,
            'ICON_SIZE': (36, 36),
            'LANGUAGE_ICON_SIZE': (58, 28)
        },
        'normal': {
            'TOP_OFFSET': 0.94,
            'ICON_SIZE': (40, 40),
            'LANGUAGE_ICON_SIZE': (65, 32)
        },
        'large': {
            'TOP_OFFSET': 0.95,
            'ICON_SIZE': (44, 44),
            'LANGUAGE_ICON_SIZE': (72, 36)
        }
    }

    @classmethod
    def apply_preset(cls, preset_name):
        """Применяет предустановленные настройки"""
        preset = cls.SCREEN_PRESETS.get(preset_name, cls.SCREEN_PRESETS['normal'])

        cls.TOP_OFFSET = preset.get('TOP_OFFSET', cls.TOP_OFFSET)
        cls.ICON_SIZE = preset.get('ICON_SIZE', cls.ICON_SIZE)
        cls.LANGUAGE_ICON_SIZE = preset.get('LANGUAGE_ICON_SIZE', cls.LANGUAGE_ICON_SIZE)

        # Обновляем позиции иконок
        for config in cls.ICON_CONFIGS:
            config['pos_hint']['top'] = cls.TOP_OFFSET
        cls.LANGUAGE_ICON_POS['top'] = cls.TOP_OFFSET

        return cls


# Создаём экземпляр
top_nav_config = TopNavConfig()