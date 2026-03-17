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

    # Отступы
    PADDING = 16
    PADDING_SMALL = 8

    # Скругления
    CORNER_RADIUS = 18
    CORNER_RADIUS_SMALL = 10

    # Анимация (добавляем этот атрибут)
    ANIMATION_DURATION = 0.25

    # Цвета для KivyMD
    MD_COLORS = {
        "CustomGreen": {
            "50": "#E8F3F4",
            "100": "#C5E1E3",
            "200": "#9EC9CC",
            "300": "#76B3B6",  # Основной твой цвет
            "400": "#5A9CA0",
            "500": "#4D8B8F",
            "600": "#407A7E",
            "700": "#33696C",
            "800": "#26585A",
            "900": "#194748",
            "A100": "#9EC9CC",
            "A200": "#76B3B6",
            "A400": "#5A9CA0",
            "A700": "#33696C",
        }
    }


theme = Theme()