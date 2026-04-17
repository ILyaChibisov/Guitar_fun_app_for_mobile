# config/bottom_nav_config.py
"""
Конфигурация нижней панели навигации
Здесь можно менять все параметры панели и иконок
"""
from kivy.metrics import dp, sp


class BottomNavConfig:
    """Настройки нижней панели"""

    # ========== НАСТРОЙКИ ПАНЕЛИ ==========
    PANEL_HEIGHT = 65  # Высота панели (40-70) - БЕЗ dp()
    PANEL_PADDING = [8, 4, 8, 10]  # Отступы [лево, верх, право, низ] - БЕЗ dp()
    PANEL_SPACING = 2  # Расстояние между кнопками (0-8) - БЕЗ dp()
    PANEL_BG_COLOR = [1, 1, 1, 1]  # Цвет фона (белый)

    # ========== НАСТРОЙКИ ИКОНОК ==========
    # Размер иконки (0.4 - 0.9) - чем больше, тем крупнее иконка
    ICON_SIZE = 0.90

    # Высота контейнера иконки (0.4 - 0.8) - сколько места под иконку
    ICON_CONTAINER_HEIGHT = 0.99

    # Размер шрифта (7 - 14)
    FONT_SIZE = 16

    # Расстояние между иконкой и текстом (0 - 6)
    SPACING = 16

    # Верхний отступ внутри кнопки (0 - 10)
    TOP_PADDING = 4

    # ========== ИНДИВИДУАЛЬНЫЕ НАСТРОЙКИ ДЛЯ КАЖДОЙ КНОПКИ ==========
    BUTTONS_CONFIG = {
        'songs': {
            'icon_size': 0.90,
            'icon_height': 0.4,
            'font_size': 9,
            'spacing': 2,
            'top_padding': 4
        },
        'chords': {
            'icon_size': 0.65,
            'icon_height': 0.6,
            'font_size': 9,
            'spacing': 2,
            'top_padding': 4
        },
        'tuner': {
            'icon_size': 0.65,
            'icon_height': 0.6,
            'font_size': 9,
            'spacing': 2,
            'top_padding': 4
        },
        'dictionary': {
            'icon_size': 0.65,
            'icon_height': 0.6,
            'font_size': 9,
            'spacing': 2,
            'top_padding': 4
        },
        'favorites': {
            'icon_size': 0.65,
            'icon_height': 0.6,
            'font_size': 9,
            'spacing': 2,
            'top_padding': 4
        },
    }

    @classmethod
    def get_button_config(cls, screen_name):
        """Возвращает настройки для конкретной кнопки"""
        return cls.BUTTONS_CONFIG.get(screen_name, {
            'icon_size': cls.ICON_SIZE,
            'icon_height': cls.ICON_CONTAINER_HEIGHT,
            'font_size': cls.FONT_SIZE,
            'spacing': cls.SPACING,
            'top_padding': cls.TOP_PADDING
        })