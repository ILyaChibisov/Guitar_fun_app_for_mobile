# config/theme.py
"""
Настройка цветовой темы для KivyMD
Твой мягкий зелёный RGB(118, 179, 182) - #76B3B6
"""


class Theme:
    # Твой мягкий зелёный
    PRIMARY = "#76B3B6"
    PRIMARY_LIGHT = "#9EC9CC"
    PRIMARY_DARK = "#5A8F92"

    # Бежевый фон
    BACKGROUND = "#FAF5EB"

    # Белый для карточек
    SURFACE = "#FFFFFF"
    SURFACE_LIGHT = "#FCF8F0"

    # Текст
    TEXT_PRIMARY = "#4A4A4A"
    TEXT_SECONDARY = "#7A7A7A"

    # Цвета для уведомлений
    SUCCESS = [0.3, 0.7, 0.3, 1]
    ERROR = [0.8, 0.3, 0.3, 1]
    WARNING = [0.9, 0.7, 0.2, 1]
    INFO = [0.46, 0.70, 0.71, 1]

    # Отступы
    PADDING = 16
    PADDING_SMALL = 8

    # Скругления
    CORNER_RADIUS = 18
    CORNER_RADIUS_SMALL = 10

    # Анимация
    ANIMATION_DURATION = 0.25

    # Список поддерживаемых языков (с кодами)
    LANGUAGES = {
        "ru": "Русский",
        "en": "English",
        "de": "Deutsch",
        "fr": "Français",
        "it": "Italiano",
        "pt": "Português",
        "zh": "中文"
    }

    # Флаги для языков (эмодзи)
    FLAGS = {
        "ru": "🇷🇺", "en": "🇬🇧", "de": "🇩🇪",
        "fr": "🇫🇷", "it": "🇮🇹", "pt": "🇵🇹", "zh": "🇨🇳"
    }

    # Краткие коды для отображения
    SHORT_CODES = {
        "ru": "RU", "en": "EN", "de": "DE",
        "fr": "FR", "it": "IT", "pt": "PT", "zh": "中文"
    }


theme = Theme()