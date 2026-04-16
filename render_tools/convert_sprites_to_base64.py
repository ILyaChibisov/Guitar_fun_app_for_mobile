# render_tools/convert_sprites_to_base64.py
"""
Конвертирует PNG спрайты в base64 для использования в Kivy
"""
import base64
import re
from pathlib import Path

SPRITES_DIR = Path("../sprites")
OUTPUT_FILE = Path("../sprite_images.py")


def clean_name(name):
    """Очищает имя для использования в Python"""
    # Заменяем специальные символы
    name = name.replace('#', 'sharp')
    name = name.replace('-', '_')
    name = name.replace('!', '_')
    name = name.replace('@', '_')
    name = name.replace('$', '_')
    name = name.replace('%', '_')
    name = name.replace('&', '_')
    name = name.replace('*', '_')
    name = name.replace('(', '_')
    name = name.replace(')', '_')
    name = name.replace('+', '_')
    name = name.replace('=', '_')
    name = name.replace('[', '_')
    name = name.replace(']', '_')
    name = name.replace('{', '_')
    name = name.replace('}', '_')
    name = name.replace('|', '_')
    name = name.replace('\\', '_')
    name = name.replace(';', '_')
    name = name.replace(':', '_')
    name = name.replace("'", '_')
    name = name.replace('"', '_')
    name = name.replace('<', '_')
    name = name.replace('>', '_')
    name = name.replace(',', '_')
    name = name.replace('.', '_')
    name = name.replace('?', '_')
    name = name.replace('/', '_')
    name = name.replace(' ', '_')

    # Если имя начинается с цифры, добавляем префикс
    if name and name[0].isdigit():
        name = 'sprite_' + name

    return name


def convert_sprites():
    """Конвертирует все PNG спрайты в base64"""
    if not SPRITES_DIR.exists():
        print(f"❌ Папка {SPRITES_DIR} не найдена")
        print("   Сначала запустите generate_sprites.py")
        return

    sprites = {}

    print("\n📸 Конвертация спрайтов в base64...")
    print("=" * 50)

    png_files = list(SPRITES_DIR.glob("*.png"))
    if not png_files:
        print("❌ Нет PNG файлов для конвертации")
        return

    for png_file in sorted(png_files):
        with open(png_file, 'rb') as f:
            data = f.read()
            b64 = base64.b64encode(data).decode('ascii')
            var_name = clean_name(png_file.stem)
            sprites[var_name] = b64
            size_kb = len(data) / 1024
            print(f"  📸 {var_name}: {size_kb:.1f} KB")

    # Сохраняем в файл sprite_images.py
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write('"""\nАвтоматически сгенерированные спрайты элементов аккордов\n')
        f.write(f"Всего спрайтов: {len(sprites)}\n")
        f.write('"""\n\n')
        f.write("import base64\n\n")

        # Сохраняем каждое изображение
        for name, b64 in sprites.items():
            chunks = [b64[i:i + 100] for i in range(0, len(b64), 100)]
            f.write(f"_{name}_BASE64 = (\n")
            for chunk in chunks:
                f.write(f'    "{chunk}"\n')
            f.write(")\n\n")

        # Создаём словарь
        f.write("SPRITE_IMAGES = {\n")
        for name in sprites.keys():
            f.write(f'    "{name}": _{name}_BASE64,\n')
        f.write("}\n\n")

        # Добавляем функции-помощники
        f.write("""
def get_sprite(name, size=None):
    '''Возвращает base64 спрайта по имени'''
    key = name
    if size:
        key = f"{name}_{size}"
    return SPRITE_IMAGES.get(key)


def get_note_sprite(note_name, size=50):
    '''Возвращает спрайт ноты'''
    # Очищаем имя ноты
    clean_note = note_name.replace('#', 'sharp')
    return get_sprite(f"note_{clean_note}_{size}")


def get_finger_sprite(finger_num, size=50):
    '''Возвращает спрайт пальца'''
    return get_sprite(f"finger_{finger_num}_{size}")


def get_x_sprite(size=50):
    '''Возвращает спрайт X'''
    return get_sprite(f"x_{size}")


def get_barre_sprite(style, width, height):
    '''Возвращает спрайт баре'''
    return get_sprite(f"barre_{style}_{width}x{height}")


def get_fret_sprite(symbol, size=30):
    '''Возвращает спрайт цифры лада'''
    return get_sprite(f"fret_{symbol}_{size}")


def list_all_sprites():
    '''Возвращает список всех доступных спрайтов'''
    return list(SPRITE_IMAGES.keys())
""")

    print("=" * 50)
    print(f"\n✅ Сохранено {len(sprites)} спрайтов в {OUTPUT_FILE}")
    print(f"📁 Размер файла: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    print(f"📂 Полный путь: {OUTPUT_FILE.absolute()}")


if __name__ == "__main__":
    convert_sprites()