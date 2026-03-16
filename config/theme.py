# config/theme.py
"""
Современная цветовая тема приложения
"""
from kivy.utils import rgba
from kivy.metrics import dp, sp


class Theme:
    # Основные цвета (Material Design 3 + музыкальная тематика)
    PRIMARY = '#6200EE'  # Глубокий фиолетовый
    PRIMARY_VARIANT = '#3700B3'
    SECONDARY = '#03DAC6'  # Бирюзовый (как звуковая волна)
    SECONDARY_VARIANT = '#018786'
    BACKGROUND = '#F6F5F8'  # Светлый фон
    SURFACE = '#FFFFFF'  # Поверхности (карточки)
    ERROR = '#B00020'
    SUCCESS = '#4CAF50'
    WARNING = '#FF9800'

    # Текст
    TEXT_PRIMARY = '#1A1A1A'  # Основной текст
    TEXT_SECONDARY = '#666666'  # Вторичный текст
    TEXT_HINT = '#999999'  # Подсказки
    TEXT_ON_PRIMARY = '#FFFFFF'  # Текст на цветном фоне

    # Градиенты (для современного вида)
    GRADIENT_PRIMARY = [PRIMARY, PRIMARY_VARIANT]
    GRADIENT_ACCENT = [SECONDARY, SECONDARY_VARIANT]

    # Размеры
    CORNER_RADIUS = 12  # Скругление углов
    CORNER_RADIUS_SMALL = 8
    PADDING = 16  # Стандартный отступ
    PADDING_SMALL = 8

    # Тени (параметры для эффекта глубины)
    SHADOW = {
        'small': (1, 2, 0.1),
        'medium': (2, 4, 0.15),
        'large': (4, 8, 0.2)
    }

    # Анимации
    ANIMATION_DURATION = 0.3
    ANIMATION_TRANSITION = 'out_quad'

    # Шрифты
    FONT_SIZE_H1 = sp(32)
    FONT_SIZE_H2 = sp(24)
    FONT_SIZE_H3 = sp(20)
    FONT_SIZE_BODY = sp(16)
    FONT_SIZE_CAPTION = sp(14)
    FONT_SIZE_SMALL = sp(12)


# Глобальный экземпляр темы
theme = Theme()