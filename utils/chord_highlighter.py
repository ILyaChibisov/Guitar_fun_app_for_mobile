# utils/chord_highlighter.py
"""
Модуль для подсветки аккордов в тексте
"""
import re
from kivymd.uix.label import MDLabel
from utils.chord_parser import extract_chords_from_text, normalize_chord_case

# Паттерн для поиска аккордов (без \b)
CHORD_PATTERN = re.compile(
    r'[A-G][#b]?(?:[a-z0-9#\(\)]+?)?(?:/[A-G][#b]?)?',
    re.IGNORECASE
)


def init_chord_patterns(chords_screen):
    pass


def highlight_chords_in_text(text):
    """Подсвечивает аккорды жирным шрифтом"""
    if not text:
        return text

    def replace_chord(match):
        chord = match.group(0)
        chord = normalize_chord_case(chord)
        return f'[b]{chord}[/b]'

    return CHORD_PATTERN.sub(replace_chord, text)


def extract_chords_from_text_wrapper(text):
    return extract_chords_from_text(text)


class ChordTextLabel(MDLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.markup = True