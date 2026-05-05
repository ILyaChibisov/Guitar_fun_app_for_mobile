# test_sprites.py
"""
Тест загрузки спрайтов
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chord_sprites import sprite_loader
from sprite_images import SPRITE_IMAGES

print("=" * 50)
print("ТЕСТ ЗАГРУЗКИ СПРАЙТОВ")
print("=" * 50)

# 1. Список всех доступных спрайтов
available = list(SPRITE_IMAGES.keys())
print(f"\n1. Всего доступно спрайтов: {len(available)}")
print(f"   Первые 20: {available[:20]}")

# 2. Проверяем ключевые спрайты
test_sprites = [
    'finger_1_50',
    'finger_2_50',
    'finger_3_50',
    'finger_4_50',
    'finger_T_50',
    'note_A_50',
    'note_Asharp_50',
    'note_B_50',
    'note_C_50',
    'note_Csharp_50',
    'x_50',
    'fret_1_30',
]

print("\n2. Проверка наличия ключевых спрайтов в словаре:")
for sprite_name in test_sprites:
    exists = sprite_name in SPRITE_IMAGES
    print(f"   {sprite_name}: {'✅ ЕСТЬ' if exists else '❌ НЕТ'}")

# 3. Пытаемся загрузить текстуры
print("\n3. Загрузка текстур:")
for sprite_name in test_sprites[:5]:  # Загружаем только первые 5 для теста
    try:
        texture = sprite_loader.get_texture(sprite_name)
        if texture:
            print(f"   ✅ {sprite_name} - загружен, размер: {texture.width}x{texture.height}")
        else:
            print(f"   ❌ {sprite_name} - не загружен")
    except Exception as e:
        print(f"   ❌ {sprite_name} - ошибка: {e}")

print("\n" + "=" * 50)
print("Тест завершён")