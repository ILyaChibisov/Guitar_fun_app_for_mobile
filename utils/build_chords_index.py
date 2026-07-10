# utils/build_chords_index.py
"""
Модуль для построения индекса всех аккордов из папки chords.
Запускается как отдельный скрипт для создания/обновления файла chords/all_chords.py

Запуск: python utils/build_chords_index.py
Или через PyCharm: нажать кнопку Run
"""

import os
import sys
import re
import json
import importlib
from typing import Dict, List, Optional
from datetime import datetime

# Определяем корневую директорию проекта (где находятся chords и utils)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHORDS_ROOT = os.path.join(PROJECT_ROOT, 'chords')

# Добавляем корень проекта в путь для импорта
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def create_empty_init_files(base_path: str, verbose: bool = True):
    """
    Создает пустые __init__.py во всех подпапках

    Args:
        base_path: Корневая папка, начиная с которой нужно создать __init__.py
        verbose: Выводить ли информацию о созданных файлах

    Returns:
        List[str]: Список созданных файлов
    """
    created_files = []

    if not os.path.exists(base_path):
        print(f"❌ Path does not exist: {base_path}")
        return created_files

    # Проходим по всем папкам рекурсивно
    for root, dirs, files in os.walk(base_path):
        # Проверяем, есть ли уже __init__.py в папке
        init_file = os.path.join(root, '__init__.py')
        if not os.path.exists(init_file):
            # Создаем пустой __init__.py
            try:
                with open(init_file, 'w', encoding='utf-8') as f:
                    pass  # Создаем пустой файл

                created_files.append(init_file)
                if verbose:
                    print(f"   ✅ Created: {init_file}")

            except Exception as e:
                print(f"   ❌ Error creating {init_file}: {str(e)}")

    return created_files


def import_module_from_file(file_path: str):
    """
    Импортирует модуль из файла различными способами

    Args:
        file_path: Путь к файлу

    Returns:
        Импортированный модуль или None
    """
    try:
        # Способ 1: через importlib (Python 3.4+)
        if hasattr(importlib, 'util'):
            try:
                spec = importlib.util.spec_from_file_location("temp_module", file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return module
            except:
                pass

        # Способ 2: через __import__ с добавлением в sys.path
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path).replace('.py', '')

        # Добавляем директорию в путь
        if dir_path not in sys.path:
            sys.path.insert(0, dir_path)

        try:
            module = __import__(file_name)
            return module
        except:
            pass

        # Способ 3: через exec (самый простой, но менее безопасный)
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        # Создаем пустой модуль
        module = type('module', (), {})()
        exec(code, module.__dict__)
        return module

    except Exception:
        return None


class ChordIndexBuilder:
    """Сборщик индекса аккордов из файлов конфигураций"""

    def __init__(self, chords_root: str = None):
        if chords_root is None:
            chords_root = CHORDS_ROOT
        self.chords_root = chords_root
        self.index: Dict[str, Dict] = {}
        self.errors: List[str] = []
        self.total_files = 0
        self.processed_files = 0

    def build_index(self) -> Dict[str, Dict]:
        """
        Обходит все папки с аккордами и строит индекс

        Returns:
            Dict[str, Dict]: {
                "A": {
                    "type": "Major",
                    "description": "Ля мажор",
                    "variants": ["A_1", "A_2", "A_3"],
                    "configs": {
                        "A_1": {"variant": 1, "file": "-5/A_1.py"},
                        "A_2": {"variant": 2, "file": "-5/A_2.py"},
                    }
                }
            }
        """
        print(f"🔍 Building chord index...")
        print(f"📁 Chords folder: {self.chords_root}")

        if not os.path.exists(self.chords_root):
            print(f"❌ Error: Chords folder not found at: {self.chords_root}")
            return {}

        # Создаем пустые __init__.py файлы
        print(f"\n📦 Creating empty __init__.py files...")
        created = create_empty_init_files(self.chords_root)
        print(f"   Created {len(created)} __init__.py files")

        print(f"\n📂 Scanning chord files...")

        # Проходим по всем подпапкам в chords
        for root, dirs, files in os.walk(self.chords_root):
            # Пропускаем корневую папку chords
            if root == self.chords_root:
                continue

            chord_type = os.path.basename(root)
            print(f"   Processing: {chord_type} ({len(files)} files)")

            # Ищем файлы с метаданными
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    self.total_files += 1
                    file_path = os.path.join(root, file)
                    self._process_chord_file(file_path, root, file)

        print(f"\n📊 Processed {self.processed_files}/{self.total_files} files")
        print(f"✅ Index built: {len(self.index)} unique chords, {self._count_total_configs()} configs")

        if self.errors:
            print(f"⚠️  Errors: {len(self.errors)}")
            for error in self.errors[:5]:
                print(f"   - {error}")
            if len(self.errors) > 5:
                print(f"   ... and {len(self.errors) - 5} more errors")

        return self.index

    def _get_relative_path(self, file_path: str) -> str:
        """
        Возвращает относительный путь от папки chords

        Args:
            file_path: Полный путь к файлу

        Returns:
            Относительный путь вида: "-5/A-5_1.py"
        """
        rel_path = os.path.relpath(file_path, self.chords_root)
        rel_path = rel_path.replace('\\', '/')
        return rel_path

    def _process_chord_file(self, file_path: str, root: str, filename: str):
        """Обрабатывает один файл конфигурации аккорда"""
        try:
            # Импортируем модуль из файла
            module = import_module_from_file(file_path)

            if module is None:
                self.errors.append(f"Cannot import {filename}")
                return

            # Получаем METADATA
            if hasattr(module, 'METADATA'):
                metadata = module.METADATA
                self.processed_files += 1

                # Парсим названия и описания
                names = self._split_by_delimiter(metadata.get('name', ''))
                descriptions = self._split_by_delimiter(metadata.get('description', ''))
                chord_type = metadata.get('type', 'Unknown')
                variant = metadata.get('variant', 0)

                # Получаем относительный путь
                rel_path = self._get_relative_path(file_path)
                config_name = filename.replace('.py', '')

                # Добавляем каждое имя в индекс
                for i, name in enumerate(names):
                    clean_name = self._clean_chord_name(name)
                    if not clean_name:
                        continue

                    # Берем описание для этого имени
                    description = descriptions[i] if i < len(descriptions) else descriptions[0] if descriptions else ''

                    # Создаем запись в индексе
                    if clean_name not in self.index:
                        self.index[clean_name] = {
                            'type': chord_type,
                            'description': description,
                            'variants': [],
                            'configs': {}
                        }

                    # Добавляем конфигурацию
                    if config_name not in self.index[clean_name]['configs']:
                        self.index[clean_name]['variants'].append(config_name)
                        self.index[clean_name]['configs'][config_name] = {
                            'variant': variant,
                            'file': rel_path,
                            'chord_type': chord_type
                        }

            else:
                self.errors.append(f"No METADATA in {filename}")

        except Exception as e:
            self.errors.append(f"Error processing {filename}: {str(e)}")

    def _split_by_delimiter(self, text: str) -> List[str]:
        """Разделяет строку по символу ! и убирает пустые значения"""
        if not text:
            return []
        parts = text.split('!')
        return [p.strip() for p in parts if p.strip()]

    def _clean_chord_name(self, name: str) -> str:
        """Очищает имя аккорда от лишних символов"""
        clean = name.strip()
        # Убираем суффиксы типа maj, min, aug, dim и т.д.
        clean = re.sub(r'\s+maj$', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+min$', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+aug$', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+dim$', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+sus\d*$', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\s+[0-9]+$', '', clean)
        clean = re.sub(r'\s+', ' ', clean)
        return clean

    def _count_total_configs(self) -> int:
        """Подсчитывает общее количество конфигураций в индексе"""
        total = 0
        for chord_data in self.index.values():
            total += len(chord_data['variants'])
        return total

    def save_index(self, output_file: str = None):
        """
        Сохраняет индекс в Python файл как словарь ALL_CHORDS

        Args:
            output_file: Имя выходного файла (по умолчанию chords/all_chords.py)
        """
        if output_file is None:
            output_file = os.path.join(CHORDS_ROOT, 'all_chords.py')

        # Создаем папку если её нет
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('"""\n')
                f.write('Автоматически сгенерированный индекс всех аккордов\n')
                f.write(f'Создан: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
                f.write(f'Всего аккордов: {len(self.index)}\n')
                f.write(f'Всего конфигураций: {self._count_total_configs()}\n')
                f.write('"""\n\n')

                f.write('# ALL_CHORDS - словарь всех аккордов\n')
                f.write('# {\n')
                f.write('#   "A": {\n')
                f.write('#       "type": "Major",\n')
                f.write('#       "description": "Ля мажор",\n')
                f.write('#       "variants": ["A_1", "A_2", "A_3"],\n')
                f.write('#       "configs": {\n')
                f.write('#           "A_1": {"variant": 1, "file": "-5/A_1.py", "chord_type": "Major"}\n')
                f.write('#       }\n')
                f.write('#   }\n')
                f.write('# }\n\n')

                f.write('ALL_CHORDS = ')
                f.write(self._format_dict_for_file(self.index))
                f.write('\n')

            print(f"✅ Index saved to: {output_file}")

        except Exception as e:
            print(f"❌ Error saving index: {str(e)}")

    def _format_dict_for_file(self, data: dict, indent: int = 2) -> str:
        """Форматирует словарь для записи в Python файл"""
        json_str = json.dumps(data, ensure_ascii=False, indent=indent)
        json_str = json_str.replace('true', 'True')
        json_str = json_str.replace('false', 'False')
        json_str = json_str.replace('null', 'None')
        return json_str

    def get_statistics(self) -> Dict:
        """Возвращает статистику по индексу аккордов"""
        type_counts = {}
        for chord_data in self.index.values():
            chord_type = chord_data['type']
            type_counts[chord_type] = type_counts.get(chord_type, 0) + 1

        return {
            'total_chords': len(self.index),
            'total_configs': self._count_total_configs(),
            'type_counts': type_counts,
            'chord_names': sorted(self.index.keys()),
            'errors': self.errors,
            'total_files': self.total_files,
            'processed_files': self.processed_files
        }


def build_chords_index():
    """
    Основная функция для построения индекса аккордов
    """
    print("=" * 60)
    print("🎸 CHORD INDEX BUILDER")
    print("=" * 60)
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"📁 Chords path: {CHORDS_ROOT}")
    print()

    # Проверяем наличие папки chords
    if not os.path.exists(CHORDS_ROOT):
        print(f"❌ Chords folder not found!")
        print(f"   Expected: {CHORDS_ROOT}")
        return False

    # Создаем билдер
    builder = ChordIndexBuilder()

    # Строим индекс (автоматически создает пустые __init__.py)
    index = builder.build_index()

    if not index:
        print("❌ No chords found! Check the 'chords' folder structure.")
        return False

    # Сохраняем в файл
    builder.save_index()

    # Показываем статистику
    stats = builder.get_statistics()
    print("\n" + "=" * 60)
    print("📊 STATISTICS")
    print("=" * 60)
    print(f"Total files processed: {stats['processed_files']}/{stats['total_files']}")
    print(f"Total unique chords: {stats['total_chords']}")
    print(f"Total configurations: {stats['total_configs']}")

    if stats['type_counts']:
        print("\nChords by type:")
        for chord_type, count in sorted(stats['type_counts'].items()):
            print(f"  - {chord_type}: {count}")

    if stats['errors']:
        print(f"\n⚠️  Errors: {len(stats['errors'])}")
        for error in stats['errors'][:5]:
            print(f"  - {error}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more errors")

    print("=" * 60)
    print("✅ Done!")

    return True


# Функция для загрузки индекса из файла
def load_chords_index() -> Optional[Dict]:
    """
    Загружает сохраненный индекс аккордов

    Returns:
        Dict с индексом или None
    """
    try:
        index_file = os.path.join(CHORDS_ROOT, 'all_chords.py')
        if not os.path.exists(index_file):
            print(f"❌ Index file not found: {index_file}")
            print("   Run build_chords_index.py first")
            return None

        module = import_module_from_file(index_file)

        if module and hasattr(module, 'ALL_CHORDS'):
            return module.ALL_CHORDS
        else:
            print(f"❌ ALL_CHORDS not found in {index_file}")
            return None

    except Exception as e:
        print(f"❌ Error loading index: {str(e)}")
        return None


# Функция для поиска аккорда в индексе
def find_chord(chord_name: str, index: Dict = None) -> Optional[Dict]:
    """
    Находит аккорд в индексе

    Args:
        chord_name: Имя аккорда (например, "A" или "A#")
        index: Индекс аккордов (если None, загружается из файла)

    Returns:
        Dict с информацией об аккорде или None
    """
    if index is None:
        index = load_chords_index()
        if index is None:
            return None

    return index.get(chord_name)


# Функция для получения всех вариантов аккорда
def get_chord_variants(chord_name: str, index: Dict = None) -> List[str]:
    """
    Возвращает список всех вариантов для аккорда
    """
    chord_info = find_chord(chord_name, index)
    if chord_info:
        return chord_info.get('variants', [])
    return []


# Основная функция при запуске как скрипт
if __name__ == "__main__":
    build_chords_index()