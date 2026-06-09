# utils/transposer.py
"""
Модуль для транспонирования аккордов
"""
import re
from utils.chord_parser import transpose_chord, normalize_chord_case

# Паттерн для поиска аккордов (без \b)
CHORD_PATTERN = re.compile(
    r'[A-G][#b]?(?:[a-z0-9#\(\)]+?)?(?:/[A-G][#b]?)?',
    re.IGNORECASE
)


def set_transpose_system(chords_list):
    """Устанавливает систему (упрощённо - всегда диезная)"""
    pass


def transpose_text(text: str, step: float, chord_pattern=None) -> str:
    """Транспонирует текст с аккордами"""
    if not text or step == 0:
        return text

    semitones = int(round(step * 2))

    def replace_chord(match):
        chord = match.group(0)
        new_chord = transpose_chord(chord, semitones)
        new_chord = normalize_chord_case(new_chord)
        return f'[b]{new_chord}[/b]'

    try:
        # Убираем старые Kivy теги
        clean_text = re.sub(r'\[/?[a-z]+.*?\]', '', text)
        result = CHORD_PATTERN.sub(replace_chord, clean_text)
        return result
    except Exception as e:
        print(f"Ошибка: {e}")
        return text


def transpose_chord_list(chords: list, step: float) -> list:
    """Транспонирует список аккордов"""
    if not chords or step == 0:
        return chords[:]

    semitones = int(round(step * 2))
    result = []
    for chord in chords:
        new_chord = transpose_chord(chord, semitones)
        new_chord = normalize_chord_case(new_chord)
        result.append(new_chord)

    # Убираем дубликаты
    return sorted(set(result))