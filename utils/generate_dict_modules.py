# utils/generate_dict_modules.py
"""
Скрипт для генерации модулей словаря терминов

Запуск через PyCharm: просто нажмите Run (зелёная стрелка)
Или через терминал: python -m utils.generate_dict_modules
"""

import os
from pathlib import Path

# ============ НАСТРОЙКИ ============

# Русские буквы: индекс -> (буква, название_файла)
RU_LETTERS = {
    '01': ('а', 'a'),
    '02': ('б', 'b'),
    '03': ('в', 'v'),
    '04': ('г', 'g'),
    '05': ('д', 'd'),
    '06': ('е', 'e'),
    '07': ('ё', 'yo'),
    '08': ('ж', 'zh'),
    '09': ('з', 'z'),
    '10': ('и', 'i'),
    '11': ('й', 'y'),
    '12': ('к', 'k'),
    '13': ('л', 'l'),
    '14': ('м', 'm'),
    '15': ('н', 'n'),
    '16': ('о', 'o'),
    '17': ('п', 'p'),
    '18': ('р', 'r'),
    '19': ('с', 's'),
    '20': ('т', 't'),
    '21': ('у', 'u'),
    '22': ('ф', 'f'),
    '23': ('х', 'kh'),
    '24': ('ц', 'ts'),
    '25': ('ч', 'ch'),
    '26': ('ш', 'sh'),
    '27': ('щ', 'shch'),
    '28': ('ъ', 'hard'),
    '29': ('ы', 'y'),
    '30': ('ь', 'soft'),
    '31': ('э', 'e'),
    '32': ('ю', 'yu'),
    '33': ('я', 'ya'),
}

# Английские буквы: индекс -> (буква, название_файла)
EN_LETTERS = {
    '01': ('a', 'a'),
    '02': ('b', 'b'),
    '03': ('c', 'c'),
    '04': ('d', 'd'),
    '05': ('e', 'e'),
    '06': ('f', 'f'),
    '07': ('g', 'g'),
    '08': ('h', 'h'),
    '09': ('i', 'i'),
    '10': ('j', 'j'),
    '11': ('k', 'k'),
    '12': ('l', 'l'),
    '13': ('m', 'm'),
    '14': ('n', 'n'),
    '15': ('o', 'o'),
    '16': ('p', 'p'),
    '17': ('q', 'q'),
    '18': ('r', 'r'),
    '19': ('s', 's'),
    '20': ('t', 't'),
    '21': ('u', 'u'),
    '22': ('v', 'v'),
    '23': ('w', 'w'),
    '24': ('x', 'x'),
    '25': ('y', 'y'),
    '26': ('z', 'z'),
}


def get_project_root():
    """Находит корневую папку проекта"""
    current = Path(__file__).resolve()
    root = current.parent.parent
    return root


def ensure_dir(path):
    """Создаёт папку если её нет"""
    if not path.exists():
        path.mkdir(parents=True)
        print(f"📁 Создана папка: {path}")
        return True
    print(f"📁 Папка уже существует: {path}")
    return False


def write_file(path, content):
    """Записывает файл, перезаписывая если существует"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Создан/обновлён: {path.name}")
    return True


def generate_base_term():
    """Создаёт base_term.py"""
    root = get_project_root()
    dicts_path = root / 'dicts'
    base_path = dicts_path / 'base_term.py'

    content = '''# dicts/base_term.py
"""
Базовый класс для термина (упрощённая версия)
"""

class Term:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description
        }
'''

    write_file(base_path, content)


def generate_dicts_init():
    """Создаёт dicts/__init__.py"""
    root = get_project_root()
    dicts_path = root / 'dicts'
    init_path = dicts_path / '__init__.py'

    content = '''# dicts/__init__.py
"""
Модуль словаря музыкальных терминов
Структура:
    ru/ - русские термины по буквам (ru_01_a.py, ru_02_b.py, ...)
    en/ - английские термины по буквам (en_01_a.py, en_02_b.py, ...)
"""
from .base_term import Term

# Импортируем все модули для удобства
from .ru import *
from .en import *
'''

    write_file(init_path, content)


def generate_ru_init():
    """Создаёт dicts/ru/__init__.py"""
    root = get_project_root()
    ru_path = root / 'dicts' / 'ru'
    init_path = ru_path / '__init__.py'

    # Создаём список импортов
    imports = []
    letter_map = {}

    for idx, (letter, name) in RU_LETTERS.items():
        filename = f"ru_{idx}_{name}"

        # Определяем имя переменной для импорта
        if letter == 'ё':
            import_name = 'YO_TERMS'
        elif letter == 'й':
            import_name = 'Y_TERMS'
        elif letter == 'ъ':
            import_name = 'HARD_TERMS'
        elif letter == 'ь':
            import_name = 'SOFT_TERMS'
        elif letter == 'ы':
            import_name = 'Y_TERMS2'
        elif letter == 'э':
            import_name = 'E_TERMS2'
        else:
            import_name = f"{letter.upper()}_TERMS"

        imports.append(f"from .{filename} import TERMS as {import_name}")
        letter_map[letter] = import_name

    # Формируем словарь
    dict_items = []
    for letter, var_name in letter_map.items():
        dict_items.append(f"    '{letter}': {var_name},")

    content = f'''# dicts/ru/__init__.py
"""
Русские термины по буквам
"""
{chr(10).join(imports)}

# Словарь для быстрого доступа по букве
RU_TERMS_BY_LETTER = {{
{chr(10).join(dict_items)}
}}

def get_all_ru_terms():
    """Возвращает все русские термины"""
    all_terms = {{}}
    for letter, terms in RU_TERMS_BY_LETTER.items():
        if terms:
            all_terms.update(terms)
    return all_terms
'''

    write_file(init_path, content)


def generate_en_init():
    """Создаёт dicts/en/__init__.py"""
    root = get_project_root()
    en_path = root / 'dicts' / 'en'
    init_path = en_path / '__init__.py'

    # Создаём список импортов
    imports = []
    letter_map = {}

    for idx, (letter, name) in EN_LETTERS.items():
        filename = f"en_{idx}_{name}"
        import_name = f"{letter.upper()}_TERMS"
        imports.append(f"from .{filename} import TERMS as {import_name}")
        letter_map[letter] = import_name

    # Формируем словарь
    dict_items = []
    for letter, var_name in letter_map.items():
        dict_items.append(f"    '{letter}': {var_name},")

    content = f'''# dicts/en/__init__.py
"""
Английские термины по буквам
"""
{chr(10).join(imports)}

# Словарь для быстрого доступа по букве
EN_TERMS_BY_LETTER = {{
{chr(10).join(dict_items)}
}}

def get_all_en_terms():
    """Возвращает все английские термины"""
    all_terms = {{}}
    for letter, terms in EN_TERMS_BY_LETTER.items():
        if terms:
            all_terms.update(terms)
    return all_terms
'''

    write_file(init_path, content)


def generate_ru_letter_module(idx, letter, name):
    """Создаёт модуль для русской буквы"""
    root = get_project_root()
    ru_path = root / 'dicts' / 'ru'
    filename = f"ru_{idx}_{name}.py"
    filepath = ru_path / filename

    letter_upper = letter.upper() if letter != 'ё' else 'Ё'

    content = f'''# dicts/ru/{filename}
"""
Термины на букву {letter_upper}
"""
from dicts.base_term import Term

TERMS = {{
    # ============ ДОБАВЬТЕ ТЕРМИНЫ НА БУКВУ {letter_upper} ============
    # Формат:
    # "термин": Term(
    #     name="Термин",
    #     description="Развёрнутое описание термина."
    # ),
}}
'''

    write_file(filepath, content)


def generate_en_letter_module(idx, letter, name):
    """Создаёт модуль для английской буквы"""
    root = get_project_root()
    en_path = root / 'dicts' / 'en'
    filename = f"en_{idx}_{name}.py"
    filepath = en_path / filename

    letter_upper = letter.upper()

    content = f'''# dicts/en/{filename}
"""
English terms starting with {letter_upper}
"""
from dicts.base_term import Term

TERMS = {{
    # ============ ADD TERMS STARTING WITH {letter_upper} ============
    # Format:
    # "term": Term(
    #     name="Term",
    #     description="Detailed description of the term."
    # ),
}}
'''

    write_file(filepath, content)


def generate_all_modules():
    """Генерирует все модули словаря"""
    root = get_project_root()
    dicts_path = root / 'dicts'

    print("\n" + "=" * 70)
    print("🔧 ГЕНЕРАЦИЯ МОДУЛЕЙ СЛОВАРЯ")
    print("=" * 70)
    print(f"📂 Корневая папка: {root}")
    print("=" * 70)

    # 1. Создаём папки
    print("\n📁 Создание папок:")
    ensure_dir(dicts_path)
    ru_path = ensure_dir(dicts_path / 'ru')
    en_path = ensure_dir(dicts_path / 'en')

    # 2. Создаём базовые файлы
    print("\n📄 Базовые файлы:")
    generate_base_term()
    generate_dicts_init()

    # 3. Создаём __init__.py для ru и en
    print("\n📄 Файлы инициализации:")
    generate_ru_init()
    generate_en_init()

    # 4. Создаём модули для русских букв
    print(f"\n🇷🇺 Русские модули ({len(RU_LETTERS)} букв):")
    for idx, (letter, name) in RU_LETTERS.items():
        generate_ru_letter_module(idx, letter, name)

    # 5. Создаём модули для английских букв
    print(f"\n🇬🇧 Английские модули ({len(EN_LETTERS)} букв):")
    for idx, (letter, name) in EN_LETTERS.items():
        generate_en_letter_module(idx, letter, name)

    print("\n" + "=" * 70)
    print("✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 70)
    print("\n📖 Проверьте папку dicts/ - все модули созданы!")
    print("=" * 70)


if __name__ == '__main__':
    generate_all_modules()