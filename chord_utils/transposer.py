# utils/transposer.py
import re
from chord_utils.chord_parser import (
    CHORD_PATTERN,
    is_chord_line,
    transpose_chord,
    normalize_chord_case,
)
from chord_utils.chord_highlighter import get_chord_color


def set_transpose_system(chords_list):
    pass


def _detect_use_h(text: str) -> bool:
    for line in text.splitlines():
        if not is_chord_line(line):
            continue
        if re.search(r'(?<![A-Za-z])H(?![a-z])', line):
            return True
    return False


def transpose_text(text: str, step: float, theme_id=None) -> str:
    if not text or step == 0:
        return text

    semitones = int(round(step * 2))
    color = get_chord_color(theme_id)
    use_h = _detect_use_h(text)

    def replace_chord(match):
        chord = match.group(0)
        new_chord = transpose_chord(chord, semitones, use_h=use_h)
        return f'[b][color={color}]{new_chord}[/color][/b]'

    try:
        clean_text = re.sub(r'\[/?[a-z]+.*?\]', '', text)
        result_lines = []
        for line in clean_text.splitlines():
            if is_chord_line(line):
                result_lines.append(CHORD_PATTERN.sub(replace_chord, line))
            else:
                result_lines.append(line)
        return '\n'.join(result_lines)
    except Exception as e:
        print(f"Ошибка транспонирования: {e}")
        return text


def transpose_chord_list(chords: list, step: float) -> list:
    if not chords or step == 0:
        return chords[:]
    semitones = int(round(step * 2))
    use_h = any(c.startswith('H') or '/H' in c for c in chords)
    result = []
    for chord in chords:
        new_chord = transpose_chord(chord, semitones, use_h=use_h)
        new_chord = normalize_chord_case(new_chord)
        result.append(new_chord)
    return sorted(set(result))