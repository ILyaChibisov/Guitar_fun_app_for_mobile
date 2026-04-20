# config/carousel_config.py
"""
Конфигурация карусели главного экрана
"""
from kivy.metrics import dp


class CarouselConfig:
    """Настройки карусели"""

    # ========== НАСТРОЙКИ КАРУСЕЛИ ==========
    CAROUSEL_HEIGHT = 260
    CAROUSEL_WIDTH = 200

    # ========== НАСТРОЙКИ ИКОНОК ==========
    ICON_SIZE = 0.65
    ICON_CONTAINER_HEIGHT = 0.75

    # ========== НАСТРОЙКИ ТЕКСТА ==========
    FONT_SIZE = 14
    TEXT_COLOR = [1, 1, 1, 1]  # Белый текст на тёмном фоне

    # ========== ЭЛЕМЕНТЫ КАРУСЕЛИ ==========
    CAROUSEL_ITEMS = [
        {'icon_asset': 'songs_png', 'title': 'Песни', 'screen': 'songs'},
        {'icon_asset': 'chords_png', 'title': 'Аккорды', 'screen': 'chords'},
        {'icon_asset': 'tuner_png', 'title': 'Тюнер', 'screen': 'tuner'},
        {'icon_asset': 'dictionary_png', 'title': 'Словарь', 'screen': 'dictionary'},
        {'icon_asset': 'favorites_png', 'title': 'Избранное', 'screen': 'favorites'}
    ]

    # ========== ПРЕСЕТЫ ==========
    SCREEN_PRESETS = {
        'small': {'CAROUSEL_HEIGHT': 200, 'CAROUSEL_WIDTH': 160, 'ICON_SIZE': 0.60, 'FONT_SIZE': 11},
        'normal': {'CAROUSEL_HEIGHT': 240, 'CAROUSEL_WIDTH': 190, 'ICON_SIZE': 0.62, 'FONT_SIZE': 13},
        'large': {'CAROUSEL_HEIGHT': 280, 'CAROUSEL_WIDTH': 220, 'ICON_SIZE': 0.65, 'FONT_SIZE': 15},
        'tablet': {'CAROUSEL_HEIGHT': 320, 'CAROUSEL_WIDTH': 260, 'ICON_SIZE': 0.68, 'FONT_SIZE': 17}
    }

    @classmethod
    def apply_preset(cls, preset_name='normal'):
        preset = cls.SCREEN_PRESETS.get(preset_name, cls.SCREEN_PRESETS['normal'])
        cls.CAROUSEL_HEIGHT = preset.get('CAROUSEL_HEIGHT', cls.CAROUSEL_HEIGHT)
        cls.CAROUSEL_WIDTH = preset.get('CAROUSEL_WIDTH', cls.CAROUSEL_WIDTH)
        cls.ICON_SIZE = preset.get('ICON_SIZE', cls.ICON_SIZE)
        cls.FONT_SIZE = preset.get('FONT_SIZE', cls.FONT_SIZE)
        return cls


carousel_config = CarouselConfig()