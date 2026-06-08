# utils/chord_highlighter.py
"""
Модуль для подсветки аккордов в тексте
"""
import re
from kivymd.uix.label import MDLabel

# Глобальный паттерн для поиска аккордов
CHORD_PATTERN = None


def init_chord_patterns(chords_screen):
    """Инициализирует паттерны аккордов из базы данных"""
    global CHORD_PATTERN

    if not chords_screen or not hasattr(chords_screen, 'all_chords'):
        # Базовый паттерн для аккордов
        CHORD_PATTERN = re.compile(r'\b[A-G](?:#|b)?(?:maj|min|m|sus|aug|dim|add|M)?\d*(?:/[A-G](?:#|b)?)?\b',
                                   re.IGNORECASE)
        return

    # Собираем все известные аккорды из базы
    chord_names = set()
    for chord in chords_screen.all_chords:
        short_name = chord.get('short_name', '')
        if short_name:
            chord_names.add(short_name)
        name = chord.get('name', '')
        if name:
            for variant in name.split('|'):
                variant_clean = variant.strip().replace('$', '/')
                if variant_clean:
                    chord_names.add(variant_clean)

    if chord_names:
        # Сортируем по длине (от длинных к коротким) для корректного поиска
        sorted_chords = sorted(chord_names, key=len, reverse=True)
        # Экранируем специальные символы в названиях аккордов
        escaped_chords = [re.escape(chord) for chord in sorted_chords]
        pattern = r'\b(' + '|'.join(escaped_chords) + r')\b'
        CHORD_PATTERN = re.compile(pattern, re.IGNORECASE)
    else:
        CHORD_PATTERN = re.compile(r'\b[A-G](?:#|b)?(?:maj|min|m|sus|aug|dim|add|M)?\d*(?:/[A-G](?:#|b)?)?\b',
                                   re.IGNORECASE)


def highlight_chords_in_text(text):
    """Подсвечивает аккорды в тексте жирным шрифтом (без цвета)"""
    if not text:
        return text

    if CHORD_PATTERN is None:
        return text

    def replace_chord(match):
        chord = match.group(1) if match.groups() else match.group(0)
        chord = chord.strip()
        # Просто жирный шрифт, без цвета
        return f'[b]{chord}[/b]'

    try:
        highlighted = CHORD_PATTERN.sub(replace_chord, text)
        return highlighted
    except Exception as e:
        print(f"Ошибка подсветки аккордов: {e}")
        return text


def extract_chords_from_text(text):
    """Извлекает все аккорды из текста"""
    if not text:
        return []

    chords = set()

    if CHORD_PATTERN:
        matches = CHORD_PATTERN.finditer(text)
        for match in matches:
            chord = match.group(1) if match.groups() else match.group(0)
            chord = chord.strip()
            chords.add(chord)

    return list(chords)


class ChordTextLabel(MDLabel):
    """Простая метка для текста с подсветкой аккордов (без кликабельности)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.markup = True