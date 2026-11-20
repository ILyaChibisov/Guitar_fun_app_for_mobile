# utils/chord_parser.py
"""
Модуль парсинга, нормализации и транспонирования аккордов.

Ключевые принципы:
  - Единый строгий CHORD_PATTERN — импортируется другими модулями.
  - НЕ трогаем регистр в тексте (никакой normalize_chord_case при подсветке).
  - Поддержка H-нотации (Си) наряду с B.
  - Поддержка кириллических нот (А, В, С, Е, Н).
  - Отсечение табулатуры, обозначений строя и обычных слов.
  - Умная обработка служебных слов (Кода:, Припев:) и счётчиков повторов (x4, 2 раза).
  - Отсечение римских цифр в скобках: Am(V) -> Am.
"""
import re
from typing import List, Tuple, Optional

# ============ НОТЫ ============

# Диезная система (стандартная: B = Си, H при парсинге приводится к B)
NOTE_SEQUENCE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Карта нота → полутон. B и H = Си (11). Bb = 10 (Си-бемоль).
NOTE_MAP = {
    'C': 0,
    'C#': 1, 'DB': 1,
    'D': 2,
    'D#': 3, 'EB': 3,
    'E': 4, 'FB': 4,
    'F': 5, 'E#': 5,
    'F#': 6, 'GB': 6,
    'G': 7,
    'G#': 8, 'AB': 8,
    'A': 9,
    'A#': 10, 'BB': 10,
    'B': 11, 'H': 11, 'CB': 11,
}

# Карта кириллических нот -> латинские
CYRILLIC_TO_LATIN = {
    'А': 'A', 'В': 'B', 'С': 'C', 'Е': 'E', 'Н': 'H',
    'а': 'a', 'в': 'b', 'с': 'c', 'е': 'e', 'н': 'h',
}

# Кириллические ноты: А (A), В (B), С (C), Е (E), Н (H)
# ВАЖНО: именно перечисление, а не диапазон А-Н (буква С вне диапазона!)
CYR_NOTES = 'АВСЕН'

# ============ ПАТТЕРН АККОРДА ============

# Единый строгий паттерн для поиска/подсветки/транспонирования.
# БЕЗ re.IGNORECASE — иначе ловит «am», «be», «add» и прочие слова.
#
# Разбор:
#   (?<![A-Za-zА-Яа-я0-9_]) — не внутри слова слева
#   (?P<root>[A-HАВСЕН][#b]?) — корень A..H (лат) или А,В,С,Е,Н (кир) + альтерация
#   (?P<quality>...)        — суффикс (m, maj7, sus4, add9, dim7, #9, (add9), ...)
#   (?:/(?P<bass>[A-HАВСЕН][#b]?))? — слэш-бас
#   (?=\s|$|[.,!?;:\)\]\-\|]) — граница слова справа
#
# Защита от римских цифр:
#   (?!(?:[IVXLCDM]+)\)) — негативный lookahead: отменяет совпадение, если внутри скобок
#                          только римские цифры (V, VII, IV и т.д.). Это нужно, чтобы
#                          Am(V) распознавался как Am, а не Am(V).
CHORD_PATTERN = re.compile(
    r'(?<![A-Za-zА-Яа-я0-9_])'
    r'(?P<root>[A-H' + CYR_NOTES + r'][#b]?)'
                                   r'(?P<quality>'
                                   r'(?:m|min|maj|M|dim|aug|sus|add|°|ø|\+)?'
                                   r'(?:2|3|4|5|6|7|9|10|11|12|13)?'
                                   r'(?:(?:maj|min|M|dim|aug|sus|add|[#b+\-°ø])'
                                   r'(?:2|3|4|5|6|7|9|10|11|12|13|[#b+\-°ø]))*'
    # Скобки разрешены, НО внутри не должно быть только римских цифр/заглавных букв
                                   r'(?!(?:[IVXLCDM]+)\))(?:\([a-zA-Z0-9#b+\-]+\))?'
                                   r')'
                                   r'(?:/(?P<bass>[A-H' + CYR_NOTES + r'][#b]?))?'
                                                                      r'(?=\s|$|[.,!?;:\)\]\-\|])'
)

# ============ СТРОЙ ГИТАРЫ ============

# Обозначение строя: Drop C, Open G, Standard E, E standard, Half-step down
TUNING_LINE = re.compile(
    r'^\s*(?:'
    r'drop\s+[A-H](?:#|b)?'
    r'|open\s+[A-H](?:#|b)?'
    r'|(?:standard|std)\s*[A-H]?(?:#|b)?'
    r'|[A-H](?:#|b)?\s*standard'
    r'|(?:half|full)[\s\-]?step(?:\s+(?:down|up))?'
    r'|строй\s+[A-H](?:#|b)?'
    r'|настройка'
    r')\b',
    re.IGNORECASE
)

# Строй как последовательность нот: DADGAD, EADGBE, BEADGBE (5–7 заглавных нот)
TUNING_NOTES = re.compile(r'^\s*[A-H' + CYR_NOTES + r']{5,7}\s*$')

# ============ СЛУЖЕБНЫЕ СЛОВА И ПОВТОРЫ ============

# Служебные слова секций (Кода:, Припев:, Вступление:)
SECTION_WORDS = re.compile(
    r'\b(?:куплет|припев|вступление|проигрыш|бридж|кода|окончание|соло|интро|аутро|переход|аккорды)\b[:\s]*',
    re.IGNORECASE
)

# Счётчики повторов: x4, х2 (русская х), 2 раза, (2 раза)
REPEAT_MARKERS = re.compile(
    r'(?:[xх]\s*\d+|\d+\s*раз(?:а)?)',
    re.IGNORECASE
)


# ============ ОПРЕДЕЛЕНИЕ АККОРДОВОЙ СТРОКИ ============

def _is_single_cyrillic_note_token(tokens: List[str]) -> bool:
    """Проверяет, состоит ли строка ровно из одной заглавной кириллической ноты (А, В, С, Е, Н)."""
    return len(tokens) == 1 and bool(re.fullmatch(r'[' + CYR_NOTES + r'][#b]?', tokens[0]))


def is_chord_line(line: str, next_line: Optional[str] = None) -> bool:
    """
    Является ли строка аккордовой (а не текстом, табулатурой или строем).
    next_line используется для распознавания одиночной кириллической ноты (например, 'С') над строкой текста.
    """
    stripped = line.strip()
    if not stripped:
        return False

    # Табулатура: E|--8--- или E |--0--- (после | идут цифры/дефисы).
    if re.match(r'^[A-H' + CYR_NOTES + r'][#b]?\s*\|\s*[-0-9]', stripped):
        return False

    # Строй гитары: Drop C, Open G, Standard E, E standard, Half-step down
    if TUNING_LINE.match(stripped):
        return False

    # Строй как набор нот: DADGAD, EADGBE, BEADGBE
    if TUNING_NOTES.match(stripped):
        return False

    # Очищаем от служебных слов секций (Кода:, Припев:)
    cleaned = SECTION_WORDS.sub(' ', stripped)

    # Убираем счётчики повторов (x4, 2 раза)
    cleaned = REPEAT_MARKERS.sub(' ', cleaned)

    # Убираем спецсимволы разметки (|, }, -, скобки и т.д.)
    cleaned = re.sub(r'[\|\-\(\)\[\]\{\}.,:;!?/\\]+', ' ', cleaned)

    tokens = cleaned.split()
    if not tokens:
        return False

    # Игнорируем токены, которые являются только римскими цифрами (II, III, IV, V, VI, VII, VIII, IX, X и т.д.),
    # НЕ трогая одиночные аккорды C и D!
    tokens = [
        t for t in tokens
        if t.upper() in ('C', 'D') or not re.fullmatch(r'[IVXLCDM]+', t, re.IGNORECASE)
    ]
    if not tokens:
        return False

    # Одиночная кириллическая нота ('С', 'А', 'Е', 'В', 'Н'):
    # считаем аккордом только если сразу под ней идёт непустая текстовая строка песни
    if _is_single_cyrillic_note_token(tokens):
        if next_line and next_line.strip() and not is_chord_line(next_line):
            return True
        return False

    # Защита от смешанных строк с текстом: если есть длинные русские слова
    # (3+ буквы) и слов больше 3 — это текст, а не аккорды.
    has_russian_text = any(re.search(r'[А-Яа-яЁё]{3,}', t) for t in tokens)
    if has_russian_text and len(tokens) > 3:
        return False

    chord_tokens = sum(1 for t in tokens if CHORD_PATTERN.fullmatch(t))
    return (chord_tokens / len(tokens)) >= 0.5



# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

def _latinize_note(note: str) -> str:
    """Заменяет кириллические буквы нот на латинские."""
    if not note:
        return note
    return note.translate(str.maketrans(CYRILLIC_TO_LATIN))


def clean_chord_name(chord: str) -> str:
    """
    Жесткая очистка названия аккорда от римских цифр в скобках (Am(V) -> Am).
    Используется как страховка, если регулярка всё же пропустила скобки.
    """
    if not chord:
        return chord
    # Удаляем (V), (VII), (IV) и т.д. в конце строки
    cleaned = re.sub(r'\s*\((?:I|V|X|L|C|D|M)+\)\s*$', '', chord, flags=re.IGNORECASE)
    return cleaned.strip()


# ============ НОРМАЛИЗАЦИЯ НОТЫ ============

def normalize_note(note: str, use_h: bool = False, preserve_original: bool = False) -> str:
    """
    Приводит ноту к каноническому виду.
    Если preserve_original=True, сохраняет бемоли (Eb, Bb...) и ноту H как в тексте песни.
    """
    if not note:
        return note

    note = _latinize_note(note)
    clean = note[0].upper() + (note[1:].lower() if len(note) > 1 else '')
    idx = NOTE_MAP.get(clean.upper(), -1)
    if idx == -1:
        return clean

    if preserve_original:
        if clean.startswith('H'):
            return clean
        if len(clean) == 2 and clean[1] == 'b':
            if clean == 'Cb':
                return 'H' if use_h else 'B'
            if clean == 'Fb':
                return 'E'
            return clean

    res = NOTE_SEQUENCE[idx]
    if use_h and res == 'B':
        return 'H'
    return res


# ============ НОРМАЛИЗАЦИЯ АККОРДА ============

def normalize_chord_case(chord: str) -> str:
    """
    Приводит аккорд к аккуратному виду, сохраняя бемоли (Eb), ноту H (H7)
    и суффикс (A5min7) для точного отображения над грифом.
    """
    if not chord:
        return chord

    match = CHORD_PATTERN.fullmatch(chord.strip())
    if not match:
        return chord

    root = normalize_note(match.group('root'), preserve_original=True)
    quality = match.group('quality') or ''
    bass = normalize_note(match.group('bass'), preserve_original=True) if match.group('bass') else None

    return f"{root}{quality}/{bass}" if bass else f"{root}{quality}"


# ============ ТРАНСПОНИРОВАНИЕ ============

def transpose_note(note: str, semitones: int, use_h: bool = False) -> str:
    """Транспонирует одиночную ноту на заданное число полутонов."""
    if not note or semitones == 0:
        return note

    # Переводим кириллицу в латиницу
    note_latin = _latinize_note(note)
    clean = note_latin[0].upper() + (note_latin[1:].lower() if len(note_latin) > 1 else '')

    idx = NOTE_MAP.get(clean.upper(), -1)
    if idx == -1:
        return note  # возвращаем как было

    new_note = NOTE_SEQUENCE[(idx + semitones) % 12]

    # Сохраняем регистр первой буквы исходной ноты
    if note_latin[0].islower():
        new_note = new_note[0].lower() + new_note[1:]

    if use_h and new_note.upper() == 'B':
        new_note = 'H' if note_latin[0].isupper() else 'h'

    return new_note


def parse_chord(chord: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """Парсит аккорд в кортеж: (тоника, суффикс, бас). Регистр корня/баса сохраняется."""
    if not chord:
        return None

    match = CHORD_PATTERN.fullmatch(chord.strip())
    if not match:
        return None

    root = match.group('root')
    root = _latinize_note(root)  # Переводим в латиницу
    root = root[0].upper() + (root[1:].lower() if len(root) > 1 else '')

    quality = match.group('quality') or ''

    bass = match.group('bass')
    if bass:
        bass = _latinize_note(bass)  # Переводим в латиницу
        bass = bass[0].upper() + (bass[1:].lower() if len(bass) > 1 else '')

    return (root, quality, bass)


def transpose_chord(chord: str, semitones: int, use_h: bool = False) -> str:
    """Транспонирует аккорд целиком, сохраняя суффикс и слэш-бас."""
    if not chord:
        return chord

    parsed = parse_chord(chord)
    if not parsed:
        return chord

    root, quality, bass = parsed
    new_root = transpose_note(root, semitones, use_h=use_h)

    if bass:
        new_bass = transpose_note(bass, semitones, use_h=use_h)
        return f"{new_root}{quality}/{new_bass}"
    return f"{new_root}{quality}"


# ============ ИЗВЛЕЧЕНИЕ АККОРДОВ ИЗ ТЕКСТА ============

def extract_chords_from_text(text: str) -> List[str]:
    """Извлекает уникальные аккорды только из аккордовых строк текста."""
    if not text:
        return []

    chords = set()
    lines = text.splitlines()
    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else None
        if not is_chord_line(line, next_line=next_line):
            continue
        for match in CHORD_PATTERN.finditer(line):
            chord = normalize_chord_case(match.group(0))
            chord = clean_chord_name(chord)
            chords.add(chord)

    return sorted(list(chords))
