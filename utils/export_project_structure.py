# utils/export_project_structure.py
"""
Скрипт для экспорта структуры проекта в текстовый файл.
Запускается как отдельный скрипт для анализа структуры папок и файлов.

Запуск: python utils/export_project_structure.py
Или через PyCharm: нажать кнопку Run
"""

import os
import sys
from datetime import datetime

# Определяем корневую директорию проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def should_exclude_dir(dir_name: str) -> bool:
    """
    Проверяет, нужно ли исключить директорию из сканирования

    Args:
        dir_name: Имя директории

    Returns:
        True если нужно исключить, False если нет
    """
    exclude_dirs = {
        '.venv', 'venv', 'env', '__pycache__',
        '.git', '.idea', '.pytest_cache', '.mypy_cache',
        'node_modules', 'dist', 'build', '.vscode'
    }
    return dir_name in exclude_dirs


def get_project_structure(root_path: str) -> str:
    """
    Получает структуру проекта, показывая только .py и .json файлы
    Исключает .venv и другие ненужные папки

    Args:
        root_path: Путь к корневой папке проекта

    Returns:
        Строка со структурой проекта
    """
    structure = []
    total_files = 0

    for root, dirs, files in os.walk(root_path):
        # Исключаем ненужные папки
        dirs[:] = [d for d in dirs if not should_exclude_dir(d)]

        # Показываем только относительный путь от корневой папки
        rel_path = os.path.relpath(root, root_path)
        if rel_path == '.':
            current_dir = ''
        else:
            current_dir = rel_path

        # Фильтруем файлы: только .py и .json
        py_json_files = [f for f in files if f.endswith(('.py', '.json'))]

        # Если есть подходящие файлы в текущей папке
        if py_json_files:
            total_files += len(py_json_files)

            # Добавляем название папки
            if current_dir:
                structure.append(f'\n📁 {current_dir}/')
            else:
                structure.append('\n📁 .')

            # Добавляем файлы с отступом
            for file in sorted(py_json_files):
                structure.append(f'    📄 {file}')

    if not structure:
        return 'No Python or JSON files found'

    # Добавляем итоговую статистику
    structure.append(
        f'\n\n📊 Total: {total_files} files in {len([s for s in structure if s.startswith("📁")])} directories')

    return '\n'.join(structure)


def export_structure(root_path: str = None, output_file: str = None):
    """
    Экспортирует структуру проекта в файл

    Args:
        root_path: Путь к корневой папке (если None, используется PROJECT_ROOT)
        output_file: Путь к выходному файлу (если None, создается в корне проекта)
    """
    # Определяем корневую папку
    if root_path is None:
        root_path = PROJECT_ROOT

    # Проверяем существование папки
    if not os.path.exists(root_path):
        print(f"❌ Error: Path does not exist: {root_path}")
        return False

    # Определяем выходной файл
    if output_file is None:
        output_file = os.path.join(root_path, 'project_structure.txt')

    print("=" * 60)
    print("📁 PROJECT STRUCTURE EXPORTER")
    print("=" * 60)
    print(f"📂 Root folder: {root_path}")
    print(f"💾 Output file: {output_file}")
    print()

    try:
        # Получаем структуру проекта
        print("⏳ Scanning project structure...")
        structure = get_project_structure(root_path)

        # Формируем полный текст с заголовком
        full_text = f"""Project Structure Export
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Root folder: {root_path}
{'=' * 60}

Note: .venv and other system folders are excluded from this structure
Files shown: .py and .json only
{'=' * 60}

{structure}
"""

        # Сохраняем в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_text)

        print(f"✅ Structure saved to: {output_file}")

        # Показываем небольшой предпросмотр
        lines = structure.split('\n')[:20]  # Первые 20 строк
        if len(lines) < len(structure.split('\n')):
            lines.append('...')
            lines.append(f'\n(Total {len(structure.split("\n"))} lines)')

        print("\n📋 Preview:")
        print("-" * 40)
        print('\n'.join(lines))
        print("-" * 40)

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def export_structure_to_file(root_path: str, output_filename: str = 'project_structure.txt'):
    """
    Упрощенная функция для экспорта структуры

    Args:
        root_path: Путь к папке проекта
        output_filename: Имя выходного файла (по умолчанию project_structure.txt)
    """
    output_file = os.path.join(root_path, output_filename)
    return export_structure(root_path, output_file)


def main():
    """
    Основная функция
    """
    # Просто экспортируем структуру текущего проекта
    success = export_structure()

    if success:
        print("\n✅ Done!")
    else:
        print("\n❌ Export failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()