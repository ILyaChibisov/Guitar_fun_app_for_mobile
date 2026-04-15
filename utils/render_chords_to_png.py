# utils/render_chords_to_png.py
"""
Скрипт для рендеринга аккордов в PNG изображения
Использует оригинальные drawing_elements.py из PyQt5
"""
import os
import sys
import base64
from pathlib import Path

# Добавляем пути к оригинальным модулям PyQt5
sys.path.insert(0, str(Path(__file__).parent.parent))

# Используем оригинальные модули из PyQt5
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QSize
from grafic_tools.drawing_elements import DrawingElements
from data.griff import get_pixmap, BACKGROUND_NAMES

import importlib.util


def render_chord_to_pixmap(module, mode="finger", width=1280, height=860):
    """
    Рендерит аккорд в QPixmap с пустым фоном
    """
    # Создаём пустой pixmap с прозрачным фоном
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)

    # Получаем данные из модуля
    frets = getattr(module, 'FRETS', {})
    notes = getattr(module, 'NOTES', {})
    open_notes = getattr(module, 'OPEN_NOTES', {})
    barres = getattr(module, 'BARRES', {})

    if mode == "finger":
        selected = getattr(module, 'SELECTED_FINGER', [])
    else:
        selected = getattr(module, 'SELECTED_NOTE', [])

    # Рисуем элементы (без фона!)
    for fret_id, fret_data in frets.items():
        DrawingElements.draw_fret(painter, fret_data)

    for key in selected:
        if 'BAR' in key and key in barres:
            DrawingElements.draw_barre(painter, barres[key])

    for key in selected:
        if 'BAR' in key:
            continue
        elif key in notes:
            DrawingElements.draw_note(painter, notes[key])
        elif key in open_notes:
            DrawingElements.draw_open_note(painter, open_notes[key])

    painter.end()
    return pixmap


def render_all_chords():
    """
    Рендерит все аккорды в PNG и сохраняет в папку rendered_chords
    """
    chords_dir = Path("chords")
    output_dir = Path("rendered_chords")
    output_dir.mkdir(exist_ok=True)

    app = QApplication(sys.argv)

    for root, dirs, files in os.walk(chords_dir):
        for f in files:
            if f.endswith('.py') and not f.startswith('__'):
                full_path = os.path.join(root, f)
                try:
                    module_name = os.path.splitext(f)[0]
                    spec = importlib.util.spec_from_file_location(module_name, full_path)
                    if spec is None:
                        continue
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    metadata = getattr(module, 'METADATA', {})
                    chord_name = metadata.get('name', module_name)
                    variant = metadata.get('variant', 1)

                    # Рендерим для обоих режимов
                    for mode in ["finger", "note"]:
                        pixmap = render_chord_to_pixmap(module, mode)

                        # Сохраняем PNG
                        safe_name = chord_name.replace('/', '_').replace('|', '_').replace(' ', '_')
                        filename = f"{safe_name}_v{variant}_{mode}.png"
                        filepath = output_dir / filename
                        pixmap.save(str(filepath), "PNG")
                        print(f"✅ Сохранён: {filename}")

                except Exception as e:
                    print(f"❌ Ошибка {f}: {e}")

    app.quit()


def convert_rendered_to_assets():
    """
    Конвертирует сгенерированные PNG в base64 для data/assets.py
    """
    output_dir = Path("rendered_chords")
    assets = {}

    for png_file in output_dir.glob("*.png"):
        with open(png_file, 'rb') as f:
            data = f.read()
            b64 = base64.b64encode(data).decode('ascii')
            var_name = png_file.stem.replace('-', '_').replace(' ', '_')
            assets[var_name] = b64
            print(f"📸 {var_name}: {len(data)} bytes")

    # Сохраняем в файл
    with open("chord_images.py", 'w', encoding='utf-8') as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write("\"\"\"Автоматически сгенерированные изображения аккордов\"\"\"\n\n")
        f.write("import base64\n\n")

        for name, b64 in assets.items():
            f.write(f"_{name}_BASE64 = \"\"\"{b64}\"\"\"\n\n")

        f.write("\nCHORD_IMAGES = {\n")
        for name in assets.keys():
            f.write(f'    "{name}": _{name}_BASE64,\n')
        f.write("}\n")

    print(f"\n✅ Сохранено {len(assets)} изображений в chord_images.py")


if __name__ == "__main__":
    print("=" * 50)
    print("🎸 РЕНДЕРИНГ АККОРДОВ В PNG")
    print("=" * 50)

    # Шаг 1: Рендерим все аккорды
    render_all_chords()

    # Шаг 2: Конвертируем в base64
    convert_rendered_to_assets()