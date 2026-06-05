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
        # Добавляем основное название
        all_names.add(chord['short_name'])
        # Добавляем альтернативные названия из METADATA
        name_variants = chord['name'].split('|')
        for variant in name_variants:
            variant_clean = variant.strip().replace('$', '/')
            all_names.add(variant_clean)

    # Сортируем по длине (сначала самые длинные)
    sorted_names = sorted(list(all_names), key=len, reverse=True)

    # Экранируем спецсимволы
    escaped_names = [re.escape(name) for name in sorted_names]

    # Паттерн с границами, учитывающими #, b, / и другие символы
    # Используем lookbehind и lookahead для проверки границ
    # Аккорд не должен быть частью другого слова
    pattern = r'(?<![A-Za-z0-9#b/])(' + '|'.join(escaped_names) + r')(?![A-Za-z0-9#b/])'

    _chord_regex = re.compile(pattern, re.IGNORECASE)
    _all_chords_set = all_names

    print(f"🎸 Инициализировано {len(all_names)} названий аккордов (только из базы)")
    return True2


def extract_chords_from_text(text):
    if not text or not _chord_regex:
        return []

    clean_text = re.sub(r'\[color=[^\]]+\]', '', text)
    clean_text = re.sub(r'\[/color\]', '', clean_text)
    matches = _chord_regex.findall(clean_text)

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
        self._chord_regions = []
        self._update_regions()
        self.bind(size=self._update_regions)
        self.bind(text=self._update_regions)
        self.bind(font_size=self._update_regions)
        self.bind(font_name=self._update_regions)

    def _update_regions(self, *args):
        if self.text and _chord_regex:
            Clock.schedule_once(self._calculate_regions, 0.1)

    def _calculate_regions(self, *args):
        self._chord_regions = []

        if not self.text or not self.texture or not self.texture_size:
            return

        clean_text = re.sub(r'\[color=[^\]]+\]', '', self.text)
        clean_text = re.sub(r'\[/color\]', '', clean_text)

        matches = list(_chord_regex.finditer(clean_text))

        if not matches:
            return

        from kivy.core.text import Label as CoreLabel

        test_label = CoreLabel(
            font_size=self.font_size,
            font_name=self.font_name,
            bold=self.bold,
            italic=self.italic
        )

        lines = clean_text.split('\n')
        line_height = self.texture_size[1] / len(lines) if lines else 0

        current_char = 0
        for line_idx, line in enumerate(lines):
            line_start = current_char
            line_end = current_char + len(line)

            line_y = self.y + self.height - (line_idx + 1) * line_height

            for match in matches:
                if match.start() >= line_start and match.end() <= line_end:
                    chord = match.group(0)
                    char_start = match.start() - line_start

                    prefix_text = line[:char_start]
                    test_label.text = prefix_text
                    test_label.refresh()
                    prefix_width = test_label.texture.width if test_label.texture else 0

                    test_label.text = chord
                    test_label.refresh()
                    chord_width = test_label.texture.width if test_label.texture else len(chord) * sp(7)

                    x_start = self.x + prefix_width

                    self._chord_regions.append({
                        'x': x_start,
                        'y': line_y - line_height,
                        'width': chord_width,
                        'height': line_height,
                        'chord': chord
                    })

            current_char = line_end + 1

        print(f"🎸 Создано {len(self._chord_regions)} областей аккордов")

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        chord = self._find_nearest_chord(touch.x, touch.y)

        if chord:
            print(f"✅ НАЙДЕН БЛИЖАЙШИЙ АККОРД: {chord}")
            if self.on_chord_click:
                self.on_chord_click(chord)
            return True

        return super().on_touch_down(touch)

    def _find_nearest_chord(self, x, y):
        if not self._chord_regions:
            return None

        best_chord = None
        best_distance = float('inf')

        for region in self._chord_regions:
            center_x = region['x'] + region['width'] / 2
            center_y = region['y'] + region['height'] / 2

            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5

            # Точное попадание
            if (region['x'] <= x <= region['x'] + region['width'] and
                    region['y'] <= y <= region['y'] + region['height']):
                print(f"   Точное попадание в {region['chord']}")
                return region['chord']

            # Ближайший в радиусе 50px
            if distance < best_distance and distance < 50:
                best_distance = distance
                best_chord = region['chord']

        if best_chord:
            print(f"   Ближайший к клику: {best_chord} (расстояние: {best_distance:.1f}px)")

        return best_chord


def highlight_chords_in_text(text):
    if not text or not _chord_regex:
        return text

    def replace_chord(match):
        return f'[color=4680c2]{match.group(0)}[/color]'

    return _chord_regex.sub(replace_chord, text)


def get_all_chord_names_from_cache():
    return list(_all_chords_set) if _all_chords_set else []