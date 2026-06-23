# create_icons.py
import os
from PIL import Image


def create_all_icons():
    # Проверяем наличие исходной иконки
    source_file = '../icon/512.png'
    if not os.path.exists(source_file):
        print(f"❌ Файл {source_file} не найден!")
        return

    # Открываем исходную иконку
    img = Image.open(source_file)
    print(f"✅ Загружена иконка 512x512")

    # Размеры для Android
    sizes = {
        '36.png': 36,
        '48.png': 48,
        '72.png': 72,
        '96.png': 96,
        '144.png': 144,
        '192.png': 192,
        '512.png': 512,  # уже есть, но пересоздадим
    }

    for filename, size in sizes.items():
        path = os.path.join('../icon', filename)
        if os.path.exists(path) and filename == '512.png':
            print(f"⏭️ {filename} уже существует, пропускаем")
            continue

        # Изменяем размер
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(path, 'PNG')
        print(f"✅ Создан {filename} ({size}x{size})")

    print("\n🎉 Все иконки созданы в папке icon/")


if __name__ == '__main__':
    create_all_icons()