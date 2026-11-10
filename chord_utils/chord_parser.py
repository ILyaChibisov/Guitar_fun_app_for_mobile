# utils/chord_parser.py
"""
Модуль для парсинга и транспонирования аккордов
"""
import re
from typing import List, Tuple, Optional

# Нотные последовательности (только диезная система)
NOTE_SEQUENCE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def normalize_chord_case(chord: str) -> str:
    """Приводит аккорд к стандартному виду: первая буква заглавная, остальные строчные"""
    if not chord:
        return chord

    # Разделяем на основу и суффикс
    match = re.match(r'^([A-Ga-g][#b]?)(.*)$', chord)
    if not match:
        return chord

    root = match.group(1)
    suffix = match.group(2)

    # Приводим основу к стандартному виду
    if len(root) == 1:
        root = root.upper()
    elif len(root) == 2:
        root = root[0].upper() + root[1].lower()

    suffix = suffix.lower()

    return f"{root}{suffix}"


def normalize_sharp(chord: str) -> str:
    """Преобразует бемоли в диезы"""
    chord = normalize_chord_case(chord)

    flat_to_sharp = {
        'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#',
        'db': 'c#', 'eb': 'd#', 'gb': 'f#', 'ab': 'g#', 'bb': 'a#'
    }

    for flat, sharp in flat_to_sharp.items():
        if chord.startswith(flat):
            chord = sharp + chord[len(flat):]
            break

    return chord


def note_to_index(note: str) -> int:
    """Преобразует ноту в индекс"""
    note_map = {
        'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4,
        'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11
    }
    return note_map.get(note.upper(), -1)


def index_to_note(idx: int) -> str:
    """Преобразует индекс в ноту"""
    return NOTE_SEQUENCE[idx % 12]


def transpose_note(note: str, semitones: int) -> str:
    """Транспонирует ноту"""
    if not note or semitones == 0:
        return note

    idx = note_to_index(note)
    if idx == -1:
        return note

    new_idx = (idx + semitones) % 12
    return index_to_note(new_idx)


def parse_chord(chord: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """Парсит аккорд: (нота, суффикс, бас)"""
    if not chord:
        return None

    chord = chord.strip()
    chord = normalize_sharp(chord)

    # Паттерн для парсинга: нота + суффикс + опционально /бас
    pattern = r'^([A-G][#b]?)([A-Za-z0-9#\(\)]*?)(?:/([A-G][#b]?))?$'
    match = re.match(pattern, chord, re.IGNORECASE)

    if not match:
        return None

    root = match.group(1).upper()
    suffix = match.group(2).lower() if match.group(2) else ''
    bass = match.group(3).upper() if match.group(3) else None

    return (root, suffix, bass)


def transpose_chord(chord: str, semitones: int) -> str:
    """Транспонирует аккорд"""
    if not chord or semitones == 0:
        return chord

    parsed = parse_chord(chord)
    if not parsed:
        return chord

    root, suffix, bass = parsed

    new_root = transpose_note(root, semitones)
    if bass:
        new_bass = transpose_note(bass, semitones)
        return f"{new_root}{suffix}/{new_bass}"
    else:
        return f"{new_root}{suffix}"


def extract_chords_from_text(text: str) -> List[str]:
    """Извлекает все аккорды из текста и приводит к стандартному виду"""
    if not text:
        return []

    # Паттерн для поиска аккордов (без \b, чтобы не мешали)
    pattern = re.compile(
        r'[A-G][#b]?(?:[a-z0-9#\(\)]+?)?(?:/[A-G][#b]?)?',
        re.IGNORECASE
    )

    chords = set()
    for match in pattern.finditer(text):
        chord = match.group(0).strip()
        chord = normalize_chord_case(chord)
        chord = normalize_sharp(chord)
        chords.add(chord)

    return sorted(list(chords))