# config/theme.py
"""
Современная цветовая тема приложения
Светло-бежевая с мягким бирюзово-зелёным акцентом
RGB зелёного: (118, 179, 182) - #76B3B6
"""
from kivy.utils import rgba
from kivy.metrics import dp, sp


class Theme:
    # Основные цвета (бежевая гамма с мягким зелёным акцентом)
    # Мягкий зелёный с картинки: RGB(118, 179, 182) -> #76B3B6
    PRIMARY = '#76B3B6'  # Мягкий бирюзово-зелёный (с твоей картинки)
    PRIMARY_LIGHT = '#9EC9CC'  # Светлая версия (для hover/нажатий)
    PRIMARY_DARK = '#5A8F92'  # Тёмная версия (для контраста)

    # Дополнительные акценты
    SECONDARY = '#FFB347'  # Тёплый оранжевый (дополнительный)
    SECONDARY_LIGHT = '#FFC877'

    # Фоновые цвета (бежевая гамма)
    BACKGROUND = '#FAF5EB'  # Очень мягкий бежевый (чуть теплее)
    SURFACE = '#FFFFFF'  # Белый для карточек
    SURFACE_LIGHT = '#F5EFE5'  # Светло-бежевый для альтернативных карточек
    SURFACE_DARK = '#E8E0D2'  # Для границ и разделителей

    # Цвета для карточек
    CARD_BG = '#FFFFFF'  # Белый
    CARD_BG_ALT = '#FCF8F0'  # Тёплый белый с бежевым оттенком

    # Текст (мягкие серые тона)
    TEXT_PRIMARY = '#4A4A4A'  # Мягкий тёмно-серый (не чёрный)
    TEXT_SECONDARY = '#7A7A7A'  # Серый для второстепенного текста
    TEXT_HINT = '#AAAAAA'  # Светло-серый для подсказок
    TEXT_ON_PRIMARY = '#FFFFFF'  # Белый текст на зелёном фоне
    TEXT_ON_SURFACE = '#4A4A4A'  # Текст на светлом фоне

    # Статусы
    SUCCESS = '#76B3B6'  # Тот же мягкий зелёный
    WARNING = '#FFB347'  # Тёплый оранжевый
    ERROR = '#E67A7A'  # Мягкий красный (не яркий)
    INFO = '#7FB4D9'  # Мягкий голубой

    # Размеры
    CORNER_RADIUS = 18  # Более мягкое скругление
    CORNER_RADIUS_SMALL = 10
    PADDING = 16
    PADDING_SMALL = 8

    # Тени (очень мягкие)
    SHADOW = {
        'small': (1, 2, 0.06),  # Ещё мягче
        'medium': (2, 4, 0.1),
        'large': (4, 8, 0.12)
    }

    # Анимации
    ANIMATION_DURATION = 0.25
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