# utils/chord_highlighter.py
"""
Модуль для подсветки аккордов в тексте.
"""
from kivymd.uix.label import MDLabel
# Импортируем единый строгий паттерн и функцию проверки строки
from chord_utils.chord_parser import (
    CHORD_PATTERN,
    is_chord_line,
    extract_chords_from_text
)

# Цвета аккордов по темам
CHORD_COLORS = {
    'dark':  '#FF9933',  # оранжевый
    'green': '#FF9933',  # оранжевый
    'light': '#1A8C4C',  # зелёный
}
DEFAULT_CHORD_COLOR = '#FF9933'


def get_chord_color(theme_id=None):
    if theme_id is None:
        try:
            from state.settings_state import settings_state as _s
            theme_id = _s.theme
        except Exception:
            theme_id = None
    return CHORD_COLORS.get(theme_id, DEFAULT_CHORD_COLOR)


def init_chord_patterns(chords_screen):
    pass


def highlight_chords_in_text(text, theme_id=None):
    """
    Подсвечивает аккорды жирным + цветом.
    Текст НЕ меняется (регистр сохраняется), применяется только к аккордовым строкам.
    """
    if not text:
        return text

    color = get_chord_color(theme_id)

    def replace_chord(match):
        chord = match.group(0)
        return f'[b][color={color}]{chord}[/color][/b]'

    lines = text.splitlines()
    highlighted_lines = [
        CHORD_PATTERN.sub(replace_chord, line) if is_chord_line(line) else line
        for line in lines
    ]
    return '\n'.join(highlighted_lines)


def extract_chords_from_text_wrapper(text):
    return extract_chords_from_text(text)


class ChordTextLabel(MDLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.markup = True