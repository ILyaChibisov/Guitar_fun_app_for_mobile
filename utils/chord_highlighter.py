# utils/chord_highlighter.py
"""
Модуль для выделения аккордов в тексте и навигации к ним
"""
import re
from kivy.clock import Clock
from kivymd.uix.label import MDLabel
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp, sp

# Глобальная переменная для хранения списка аккордов
_all_chords_set = None
_chord_regex = None


def init_chord_patterns(chords_screen):
    """Инициализирует паттерны аккордов из реальной базы данных"""
    global _all_chords_set, _chord_regex

    if not chords_screen or not hasattr(chords_screen, 'all_chords'):
        return False

    all_names = set()

    for chord in chords_screen.all_chords:
        # Добавляем short_name
        all_names.add(chord['short_name'])
        # Добавляем варианты из поля name
        name_variants = chord['name'].split('|')
        for variant in name_variants:
            variant_clean = variant.strip().replace('$', '/')
            all_names.add(variant_clean)

    # Сортируем по длине (сначала самые длинные)
    sorted_names = sorted(list(all_names), key=len, reverse=True)

    # Экранируем спецсимволы
    escaped_names = [re.escape(name) for name in sorted_names]

    # Паттерн: границы слова (пробел, начало/конец строки, знаки препинания)
    # Важно: не захватывать части аккордов
    pattern = r'(?<![A-Z0-9#b/])(' + '|'.join(escaped_names) + r')(?![A-Z0-9#b/])'

    _chord_regex = re.compile(pattern, re.IGNORECASE)
    _all_chords_set = all_names

    print(f"🎸 Инициализировано {len(all_names)} названий аккордов")
    return True


def extract_chords_from_text(text):
    """Извлекает все аккорды из текста (без дубликатов)"""
    if not text or not _chord_regex:
        return []

    # Удаляем разметку для поиска
    clean_text = re.sub(r'\[color=[^\]]+\]', '', text)
    clean_text = re.sub(r'\[/color\]', '', clean_text)

    matches = _chord_regex.findall(clean_text)

    # Убираем дубликаты
    seen = set()
    unique_matches = []
    for match in matches:
        match_upper = match.upper()
        if match_upper not in seen:
            seen.add(match_upper)
            unique_matches.append(match_upper)

    return unique_matches


class ChordTextLabel(ButtonBehavior, MDLabel):
    """Текстовая метка с кликабельными аккордами"""

    def __init__(self, on_chord_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_chord_click = on_chord_click
        self._chord_positions = []
        self.bind(size=self._update_positions)
        self.bind(text=self._update_positions)

    def _update_positions(self, *args):
        """Обновляет позиции аккордов"""
        if self.text and _chord_regex:
            Clock.schedule_once(self._calculate_positions, 0.1)

    def _calculate_positions(self, *args):
        """Вычисляет позиции аккордов в тексте"""
        self._chord_positions = []

        if not self.text or not self.texture or not self.texture_size:
            return

        clean_text = re.sub(r'\[color=[^\]]+\]', '', self.text)
        clean_text = re.sub(r'\[/color\]', '', clean_text)

        matches = list(_chord_regex.finditer(clean_text))

        if not matches:
            return

        lines = clean_text.split('\n')
        line_height = self.texture_size[1] / len(lines) if lines else 0

        if line_height <= 0:
            return

        current_char = 0
        for line_idx, line in enumerate(lines):
            line_start = current_char
            line_end = current_char + len(line)

            for match in matches:
                if match.start() >= line_start and match.end() <= line_end:
                    chord = match.group(0)
                    char_in_line = match.start() - line_start

                    char_width = sp(7)
                    x_start = self.x + dp(12) + (char_in_line * char_width)
                    y_start = self.y + self.height - (line_idx + 1) * line_height
                    width = len(chord) * char_width

                    self._chord_positions.append({
                        'x': x_start,
                        'y': y_start,
                        'width': width,
                        'height': line_height,
                        'chord': chord
                    })

            current_char = line_end + 1

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        for pos in self._chord_positions:
            if (pos['x'] <= touch.x <= pos['x'] + pos['width'] and
                    pos['y'] - pos['height'] <= touch.y <= pos['y']):

                if self.on_chord_click:
                    self.on_chord_click(pos['chord'])
                return True

        return super().on_touch_down(touch)


def highlight_chords_in_text(text):
    """Возвращает текст с подсветкой аккордов"""
    if not text or not _chord_regex:
        return text

    def replace_chord(match):
        chord = match.group(0)
        return f'[color=4680c2]{chord}[/color]'

    return _chord_regex.sub(replace_chord, text)


def get_all_chord_names_from_cache():
    return list(_all_chords_set) if _all_chords_set else []