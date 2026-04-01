# utils/helpers.py
"""
Вспомогательные функции
"""
import re
from datetime import datetime
from kivy.utils import platform


def is_android():
    """Проверяет, запущено ли приложение на Android"""
    return platform == 'android'


def is_desktop():
    """Проверяет, запущено ли приложение на десктопе"""
    return platform in ('win', 'linux', 'macosx')


def format_date(date_string):
    """
    Форматирует дату из ISO в читаемый формат

    Args:
        date_string: Дата в формате ISO (2024-01-01T12:00:00)

    Returns:
        str: Отформатированная дата (01.01.2024)
    """
    if not date_string:
        return 'неизвестно'

    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y')
    except:
        return 'неизвестно'


def truncate_text(text, max_length=100):
    """
    Обрезает текст до указанной длины

    Args:
        text: Исходный текст
        max_length: Максимальная длина

    Returns:
        str: Обрезанный текст с многоточием
    """
    if not text:
        return ''

    if len(text) <= max_length:
        return text

    return text[:max_length] + '...'


def sanitize_filename(filename):
    """
    Очищает имя файла от недопустимых символов

    Args:
        filename: Исходное имя файла

    Returns:
        str: Очищенное имя файла
    """
    # Удаляем недопустимые символы для имен файлов
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Удаляем лишние пробелы
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename


def get_avatar_emoji(username):
    """
    Возвращает эмодзи для аватара на основе имени пользователя

    Args:
        username: Имя пользователя

    Returns:
        str: Эмодзи для аватара
    """
    if not username:
        return '👤'

    # Простая хеш-функция для выбора эмодзи
    emojis = ['😀', '😎', '🎸', '🎵', '🎶', '🎤', '🎧', '🎼', '🎹', '🥁']
    hash_value = sum(ord(c) for c in username)
    return emojis[hash_value % len(emojis)]


def get_status_color(is_active):
    """
    Возвращает цвет для статуса пользователя

    Args:
        is_active: Активен ли пользователь

    Returns:
        list: Цвет в формате RGBA
    """
    if is_active:
        return [0.3, 0.7, 0.3, 1]  # Зеленый
    return [0.8, 0.3, 0.3, 1]  # Красный