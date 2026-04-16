# render_tools/generate_sprites.py
"""
Генератор PNG спрайтов из JSON шаблонов
Создаёт отдельные PNG для каждого уникального элемента
"""
import json
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath, QLinearGradient, QRadialGradient
from PyQt5.QtCore import Qt
from drawing_elements import DrawingElements

# Создаём приложение PyQt5
app = QApplication(sys.argv)

# Папки
TEMPLATES_DIR = Path("templates")
SPRITES_DIR = Path("../sprites")
SPRITES_DIR.mkdir(exist_ok=True)

# Основные размеры для спрайтов
NOTE_SIZE = 50
FRET_SIZE = 30

# ПРЯМОЕ СООТВЕТСТВИЕ ЦВЕТОВ НОТАМ (как в PyQt5)
NOTE_STYLES = {
    'C': 'note_C',
    'C#': 'note_C#',
    'D': 'note_D',
    'D#': 'note_D#',
    'E': 'note_E',
    'F': 'note_F',
    'F#': 'note_F#',
    'G': 'note_G',
    'G#': 'note_G#',
    'A': 'note_A',
    'A#': 'note_A#',
    'B': 'note_B',
    'X': 'orange_3d'  # для символа X
}

# СООТВЕТСТВИЕ ЦВЕТОВ ДЛЯ ПАЛЬЦЕВ
FINGER_STYLE = 'orange_3d'


def load_templates():
    """Загружает все JSON шаблоны"""
    templates = {}
    if not TEMPLATES_DIR.exists():
        print(f"❌ Папка {TEMPLATES_DIR} не найдена")
        return templates

    for i in range(1, 13):
        template_path = TEMPLATES_DIR / f"template{i}.json"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                templates[str(i)] = json.load(f)
                print(f"  ✅ Загружен template{i}.json")

    return templates


def extract_unique_elements(templates):
    """Извлекает уникальные элементы из шаблонов"""
    elements = {
        'notes': set(),
        'fingers': set(),
        'barres': set(),
        'frets': set()
    }

    for template in templates.values():
        # Ноты и пальцы из NOTES
        for note_key, note_data in template.get('notes', {}).items():
            if 'note_name' in note_data and note_data['note_name']:
                elements['notes'].add(note_data['note_name'])
            if 'finger' in note_data and note_data['finger']:
                elements['fingers'].add(note_data['finger'])

        # Открытые ноты (X) из OPEN_NOTES
        for open_note in template.get('open_notes', {}).values():
            if open_note.get('symbol') == 'X':
                elements['notes'].add('X')

        # Баре
        for barre_data in template.get('barres', {}).values():
            style = barre_data.get('style', 'wood')
            width = barre_data.get('width', 100)
            height = barre_data.get('height', 20)
            radius = barre_data.get('radius', 10)
            elements['barres'].add((style, width, height, radius))

        # Лады
        for fret_data in template.get('frets', {}).values():
            symbol = fret_data.get('symbol', '')
            if symbol:
                elements['frets'].add(symbol)

    return elements


def create_note_sprite(note_name, size=NOTE_SIZE):
    """Создаёт PNG кружочка для ноты с правильным цветом из словаря"""
    canvas_width = size * 4
    canvas_height = size * 4

    pixmap = QPixmap(canvas_width, canvas_height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    center_x = canvas_width // 2
    center_y = canvas_height // 2

    # Используем словарь соответствия
    style_name = NOTE_STYLES.get(note_name, 'orange_3d')

    print(f"  Создаю спрайт для ноты {note_name} -> стиль {style_name}")

    note_data = {
        'x': center_x,
        'y': center_y,
        'radius': size,
        'style': style_name,
        'text_color': [0, 0, 0],
        'font_style': 'bold',
        'display_text': 'note_name',
        'note_name': note_name,
        'outline': 'medium'
    }

    DrawingElements.draw_note(painter, note_data)
    painter.end()

    # Сохраняем во временный файл и обрезаем
    from PIL import Image
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        pixmap.save(tmp.name, "PNG")
        tmp_path = tmp.name

    img = Image.open(tmp_path)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    safe_name = note_name.replace('#', 'sharp')
    filename = SPRITES_DIR / f"note_{safe_name}_{size}.png"
    img.save(filename, "PNG")
    os.unlink(tmp_path)

    print(f"  ✅ note_{safe_name}_{size}.png")
    return filename


def create_finger_sprite(finger_num, size=NOTE_SIZE):
    """Создаёт PNG кружочка для пальца"""
    canvas_width = size * 4
    canvas_height = size * 4

    pixmap = QPixmap(canvas_width, canvas_height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    center_x = canvas_width // 2
    center_y = canvas_height // 2

    finger_data = {
        'x': center_x,
        'y': center_y,
        'radius': size,
        'style': FINGER_STYLE,
        'text_color': [0, 0, 0],
        'font_style': 'bold',
        'display_text': 'finger',
        'finger': str(finger_num),
        'outline': 'medium'
    }

    DrawingElements.draw_note(painter, finger_data)
    painter.end()

    from PIL import Image
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        pixmap.save(tmp.name, "PNG")
        tmp_path = tmp.name

    img = Image.open(tmp_path)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    filename = SPRITES_DIR / f"finger_{finger_num}_{size}.png"
    img.save(filename, "PNG")
    os.unlink(tmp_path)

    print(f"  ✅ finger_{finger_num}_{size}.png")
    return filename


def create_x_sprite(size=NOTE_SIZE):
    """Создаёт PNG для X"""
    canvas_width = size * 4
    canvas_height = size * 4

    pixmap = QPixmap(canvas_width, canvas_height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    center_x = canvas_width // 2
    center_y = canvas_height // 2

    x_data = {
        'x': center_x,
        'y': center_y,
        'radius': size,
        'style': 'orange_3d',
        'text_color': [0, 0, 0],
        'font_style': 'bold',
        'display_text': 'symbol',
        'symbol': 'X',
        'outline': 'medium'
    }

    DrawingElements.draw_open_note(painter, x_data)
    painter.end()

    from PIL import Image
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        pixmap.save(tmp.name, "PNG")
        tmp_path = tmp.name

    img = Image.open(tmp_path)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    filename = SPRITES_DIR / f"x_{size}.png"
    img.save(filename, "PNG")
    os.unlink(tmp_path)

    print(f"  ✅ x_{size}.png")
    return filename


def create_barre_sprite(style, width, height, radius):
    """Создаёт PNG для баре со скруглёнными углами"""
    canvas_width = width + 20
    canvas_height = height + 20

    pixmap = QPixmap(canvas_width, canvas_height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    offset_x = 10
    offset_y = 10

    from PyQt5.QtGui import QPainterPath
    path = QPainterPath()
    corner_radius = radius
    path.addRoundedRect(offset_x, offset_y, width, height, corner_radius, corner_radius)

    # Градиенты для разных стилей
    if style == "wood":
        gradient = QLinearGradient(offset_x, offset_y, offset_x + width, offset_y + height)
        gradient.setColorAt(0, QColor(210, 180, 140))
        gradient.setColorAt(0.5, QColor(160, 120, 80))
        gradient.setColorAt(1, QColor(210, 180, 140))
        painter.fillPath(path, gradient)
    elif style == "metal":
        gradient = QLinearGradient(offset_x, offset_y, offset_x + width, offset_y + height)
        gradient.setColorAt(0, QColor(200, 200, 200))
        gradient.setColorAt(0.5, QColor(100, 100, 100))
        gradient.setColorAt(1, QColor(200, 200, 200))
        painter.fillPath(path, gradient)
    elif style == "orange_metal":
        gradient = QLinearGradient(offset_x, offset_y, offset_x + width, offset_y + height)
        gradient.setColorAt(0, QColor(255, 220, 150))
        gradient.setColorAt(0.3, QColor(255, 180, 80))
        gradient.setColorAt(0.7, QColor(255, 140, 40))
        gradient.setColorAt(1, QColor(255, 120, 20))
        painter.fillPath(path, gradient)
    elif style == "orange_gradient":
        gradient = QLinearGradient(offset_x, offset_y, offset_x + width, offset_y + height)
        gradient.setColorAt(0, QColor(255, 200, 100))
        gradient.setColorAt(0.5, QColor(255, 140, 0))
        gradient.setColorAt(1, QColor(255, 100, 0))
        painter.fillPath(path, gradient)
    elif style == "orange_glow":
        gradient = QRadialGradient(offset_x + width / 2, offset_y + height / 2, max(width, height) * 0.8)
        gradient.setColorAt(0, QColor(255, 230, 180))
        gradient.setColorAt(0.5, QColor(255, 180, 80))
        gradient.setColorAt(1, QColor(255, 140, 0))
        painter.fillPath(path, gradient)
    elif style == "rubber":
        gradient = QRadialGradient(offset_x + width / 2, offset_y + height / 2, max(width, height))
        gradient.setColorAt(0, QColor(80, 80, 80))
        gradient.setColorAt(1, QColor(40, 40, 40))
        painter.fillPath(path, gradient)
    else:
        painter.fillPath(path, QColor(139, 69, 19))

    # Обводка
    painter.setPen(QPen(QColor(0, 0, 0, 80), 1))
    painter.drawPath(path)
    painter.end()

    from PIL import Image
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        pixmap.save(tmp.name, "PNG")
        tmp_path = tmp.name

    img = Image.open(tmp_path)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    filename = SPRITES_DIR / f"barre_{style}_{width}x{height}.png"
    img.save(filename, "PNG")
    os.unlink(tmp_path)

    print(f"  ✅ barre_{style}_{width}x{height}.png")
    return filename


def create_fret_sprite(symbol, size=FRET_SIZE):
    """Создаёт PNG для цифры лада"""
    canvas_width = size * 4
    canvas_height = size * 3

    pixmap = QPixmap(canvas_width, canvas_height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    text_x = canvas_width // 2
    text_y = canvas_height // 2

    fret_data = {
        'x': text_x,
        'y': text_y,
        'size': size,
        'symbol': str(symbol),
        'font_family': 'Arial',
        'style': 'default',
        'color': [0, 0, 0]
    }

    DrawingElements.draw_fret(painter, fret_data)
    painter.end()

    from PIL import Image
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        pixmap.save(tmp.name, "PNG")
        tmp_path = tmp.name

    img = Image.open(tmp_path)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    filename = SPRITES_DIR / f"fret_{symbol}_{size}.png"
    img.save(filename, "PNG")
    os.unlink(tmp_path)

    print(f"  ✅ fret_{symbol}_{size}.png")
    return filename


def generate_all_sprites():
    """Генерирует все спрайты из шаблонов"""
    print("\n" + "=" * 50)
    print("🎨 ГЕНЕРАЦИЯ СПРАЙТОВ ИЗ ШАБЛОНОВ")
    print("=" * 50)

    print("\n📂 Загрузка шаблонов...")
    templates = load_templates()

    if not templates:
        print("❌ Не найдено JSON шаблонов в папке templates/")
        return

    print("\n🔍 Извлечение уникальных элементов...")
    elements = extract_unique_elements(templates)

    print(f"\n📊 Найдено элементов:")
    print(f"   Ноты: {len(elements['notes'])}")
    print(f"   Пальцы: {len(elements['fingers'])}")
    print(f"   Баре: {len(elements['barres'])}")
    print(f"   Лады: {len(elements['frets'])}")

    print("\n📸 Генерация спрайтов нот:")
    for note in sorted(elements['notes']):
        if note != 'X':
            create_note_sprite(note, NOTE_SIZE)

    print("\n🖐 Генерация спрайтов пальцев:")
    for finger in sorted(elements['fingers'], key=lambda x: str(x)):
        create_finger_sprite(finger, NOTE_SIZE)

    print("\n❌ Генерация спрайта X:")
    create_x_sprite(NOTE_SIZE)

    print("\n📏 Генерация спрайтов баре:")
    for style, width, height, radius in sorted(elements['barres']):
        create_barre_sprite(style, width, height, radius)

    print("\n🔢 Генерация спрайтов ладов:")
    for fret in sorted(elements['frets'], key=lambda x: int(x) if str(x).isdigit() else 0):
        create_fret_sprite(fret, FRET_SIZE)

    print("\n" + "=" * 50)
    print(f"✅ Создано спрайтов: {len(list(SPRITES_DIR.glob('*.png')))}")
    print(f"📁 Папка: {SPRITES_DIR.absolute()}")
    print("=" * 50)


if __name__ == "__main__":
    generate_all_sprites()
    app.quit()