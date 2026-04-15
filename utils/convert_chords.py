# utils/coord_converter.py
"""
Конвертер координат для файлов аккордов
Преобразует абсолютные координаты (пиксели) в относительные (0-1)
"""
import os
import re
import sys
from pathlib import Path

# Базовые размеры исходного грифа (из файла griff.png)
BASE_WIDTH = 1280
BASE_HEIGHT = 860


def convert_chord_file(filepath):
    """
    Конвертирует координаты в одном файле аккорда
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = False

        # Функция для замены x координат
        def replace_x(match):
            nonlocal changes_made
            val = int(match.group(1))
            new_val = val / BASE_WIDTH
            changes_made = True
            return f'"x": {new_val:.6f}'

        # Функция для замены y координат
        def replace_y(match):
            nonlocal changes_made
            val = int(match.group(1))
            new_val = val / BASE_HEIGHT
            changes_made = True
            return f'"y": {new_val:.6f}'

        # Функция для замены радиуса
        def replace_radius(match):
            nonlocal changes_made
            val = int(match.group(1))
            new_val = val / BASE_WIDTH
            changes_made = True
            return f'"radius": {new_val:.6f}'

        # Функция для замены ширины
        def replace_width(match):
            nonlocal changes_made
            val = int(match.group(1))
            new_val = val / BASE_WIDTH
            changes_made = True
            return f'"width": {new_val:.6f}'

        # Функция для замены высоты
        def replace_height(match):
            nonlocal changes_made
            val = int(match.group(1))
            new_val = val / BASE_HEIGHT
            changes_made = True
            return f'"height": {new_val:.6f}'

        # Применяем замены
        content = re.sub(r'"x":\s*(\d+)', replace_x, content)
        content = re.sub(r'"y":\s*(\d+)', replace_y, content)
        content = re.sub(r'"radius":\s*(\d+)', replace_radius, content)
        content = re.sub(r'"width":\s*(\d+)', replace_width, content)
        content = re.sub(r'"height":\s*(\d+)', replace_height, content)

        # Сохраняем изменения только если они были
        if changes_made:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Конвертирован: {os.path.basename(filepath)}")
            return True
        else:
            print(f"  ⏭️  Пропущен (нет координат): {os.path.basename(filepath)}")
            return False

    except Exception as e:
        print(f"  ❌ Ошибка в {filepath}: {e}")
        return False


def scan_and_convert(chords_dir="chords"):
    """
    Рекурсивно сканирует папку chords и конвертирует все файлы .py
    """
    current_dir = Path(__file__).parent.parent
    chords_path = current_dir / chords_dir

    if not chords_path.exists():
        print(f"❌ Папка '{chords_dir}' не найдена по пути: {chords_path}")
        return 0, 0

    print(f"\n📁 Сканирование папки: {chords_path}")
    print("=" * 50)

    converted_count = 0
    total_count = 0

    for root, dirs, files in os.walk(chords_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                total_count += 1
                filepath = os.path.join(root, file)
                if convert_chord_file(filepath):
                    converted_count += 1

    print("=" * 50)
    print(f"\n📊 Результат:")
    print(f"   Всего файлов: {total_count}")
    print(f"   Конвертировано: {converted_count}")

    return converted_count, total_count


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔄 КОНВЕРТЕР КООРДИНАТ АККОРДОВ")
    print("=" * 50)
    print(f"📐 Базовые размеры грифа: {BASE_WIDTH} x {BASE_HEIGHT}\n")

    scan_and_convert()