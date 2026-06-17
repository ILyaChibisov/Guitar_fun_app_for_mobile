# utils/add_term.py
"""
Интерактивный скрипт для добавления терминов в словарь

Запуск через PyCharm: просто нажмите Run (зелёная стрелка)
Или через терминал: python -m utils.add_term

Как работает:
    1. Вы вводите название термина
    2. Затем вводите описание (можно многострочное, для завершения введите пустую строку)
    3. Скрипт автоматически определяет первую букву и язык (RU/EN)
    4. Добавляет термин в соответствующий модуль
    5. Если модуль не существует - создаёт его

Пример:
    Название: аккорд
    Описание: Одновременное звучание трёх и более звуков...
    (пустая строка для завершения)

    Термин "аккорд" добавлен в dicts/ru/ru_01_a.py
"""

import os
import re
from pathlib import Path
from datetime import datetime

# ============ НАСТРОЙКИ ============

# Русские буквы с индексами (для определения модуля)
RU_LETTERS = {
    'а': '01', 'б': '02', 'в': '03', 'г': '04', 'д': '05',
    'е': '06', 'ё': '07', 'ж': '08', 'з': '09', 'и': '10',
    'й': '11', 'к': '12', 'л': '13', 'м': '14', 'н': '15',
    'о': '16', 'п': '17', 'р': '18', 'с': '19', 'т': '20',
    'у': '21', 'ф': '22', 'х': '23', 'ц': '24', 'ч': '25',
    'ш': '26', 'щ': '27', 'ъ': '28', 'ы': '29', 'ь': '30',
    'э': '31', 'ю': '32', 'я': '33'
}

# Английские буквы с индексами
EN_LETTERS = {
    'a': '01', 'b': '02', 'c': '03', 'd': '04', 'e': '05',
    'f': '06', 'g': '07', 'h': '08', 'i': '09', 'j': '10',
    'k': '11', 'l': '12', 'm': '13', 'n': '14', 'o': '15',
    'p': '16', 'q': '17', 'r': '18', 's': '19', 't': '20',
    'u': '21', 'v': '22', 'w': '23', 'x': '24', 'y': '25', 'z': '26'
}

# Имена файлов для букв (для генерации имени модуля)
RU_FILE_NAMES = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i',
    'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'щ': 'shch', 'ъ': 'hard', 'ы': 'y', 'ь': 'soft',
    'э': 'e', 'ю': 'yu', 'я': 'ya'
}

EN_FILE_NAMES = {
    'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e',
    'f': 'f', 'g': 'g', 'h': 'h', 'i': 'i', 'j': 'j',
    'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'o': 'o',
    'p': 'p', 'q': 'q', 'r': 'r', 's': 's', 't': 't',
    'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x', 'y': 'y', 'z': 'z'
}


def get_project_root():
    """Находит корневую папку проекта"""
    current = Path(__file__).resolve()
    return current.parent.parent


def detect_language_and_letter(term_name):
    """
    Определяет язык и первую букву термина
    Возвращает: (language, letter, index, file_name)
    """
    if not term_name:
        return None, None, None, None

    # Очищаем от лишних символов в начале
    clean_name = term_name.lstrip('«»"\'')
    if not clean_name:
        return None, None, None, None

    first_char = clean_name[0].lower()

    # Проверяем русскую букву
    if first_char in RU_LETTERS:
        return 'ru', first_char, RU_LETTERS[first_char], RU_FILE_NAMES[first_char]

    # Проверяем английскую букву
    if first_char in EN_LETTERS:
        return 'en', first_char, EN_LETTERS[first_char], EN_FILE_NAMES[first_char]

    return None, None, None, None


def get_module_path(language, letter, index, file_name):
    """Возвращает путь к модулю для буквы"""
    root = get_project_root()

    if language == 'ru':
        return root / 'dicts' / 'ru' / f'ru_{index}_{file_name}.py'
    else:
        return root / 'dicts' / 'en' / f'en_{index}_{file_name}.py'


def read_term_from_user():
    """Читает термин от пользователя"""
    print("\n" + "=" * 60)
    print("📝 ДОБАВЛЕНИЕ НОВОГО ТЕРМИНА")
    print("=" * 60)

    # Ввод названия
    print("\nВведите название термина (или 'q' для выхода):")
    name = input("> ").strip()

    if name.lower() == 'q':
        return None, None

    if not name:
        print("⚠️ Название не может быть пустым!")
        return None, None

    # Ввод описания
    print(f"\nВведите описание для '{name}' (введите пустую строку для завершения):")
    print("   (Поддерживаются переносы строк и пустые строки)")

    lines = []
    while True:
        line = input()
        if line == '' and len(lines) > 0:
            break
        lines.append(line)

    description = '\n'.join(lines).strip()

    if not description:
        print("⚠️ Описание не может быть пустым!")
        return None, None

    return name, description


def format_description_for_module(description):
    """
    Форматирует описание для вставки в модуль
    Сохраняет все переносы строк
    """
    # Если описание содержит переносы строк - используем тройные кавычки
    if '\n' in description:
        # Убираем лишние пробелы в начале и конце
        desc_lines = description.split('\n')
        # Убираем пустые строки в начале и конце
        while desc_lines and not desc_lines[0].strip():
            desc_lines.pop(0)
        while desc_lines and not desc_lines[-1].strip():
            desc_lines.pop()

        # Если осталось больше одной строки - используем тройные кавычки
        if len(desc_lines) > 1:
            return '"""\n' + '\n'.join(desc_lines) + '\n"""'
        else:
            return f'"{desc_lines[0].strip()}"'
    else:
        return f'"{description}"'


def add_term_to_module(module_path, term_name, description):
    """
    Добавляет термин в модуль
    Если модуль не существует - создаёт его
    """
    # Проверяем существование модуля
    if not module_path.exists():
        print(f"📁 Модуль не найден, создаю: {module_path.name}")
        create_module(module_path)

    # Читаем содержимое модуля
    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Проверяем, существует ли уже такой термин
    if f'"{term_name}":' in content or f"'{term_name}':" in content:
        print(f"⚠️ Термин '{term_name}' уже существует в этом модуле!")
        return False

    # Формируем запись для термина
    formatted_desc = format_description_for_module(description)
    term_entry = f'\n    "{term_name}": Term(\n        name="{term_name.capitalize()}",\n        description={formatted_desc}\n    ),'

    # Находим место для вставки
    # Ищем конец словаря TERMS
    if 'TERMS = {' in content:
        # Находим позицию после открывающей скобки
        start_pos = content.find('TERMS = {') + len('TERMS = {')
        # Ищем закрывающую скобку с конца
        end_pos = content.rfind('}')

        if start_pos > 0 and end_pos > start_pos:
            # Вставляем перед закрывающей скобкой
            new_content = (
                    content[:end_pos] +
                    term_entry +
                    '\n' +
                    content[end_pos:]
            )

            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            return True

    print("⚠️ Не удалось найти словарь TERMS в модуле!")
    return False


def create_module(module_path):
    """Создаёт новый модуль для буквы"""
    module_name = module_path.stem

    # Определяем язык из имени файла
    if module_name.startswith('ru_'):
        language = 'ru'
        letter_upper = module_name.split('_')[2].upper()
        if letter_upper == 'YO':
            letter_upper = 'Ё'
        elif letter_upper == 'HARD':
            letter_upper = 'Ъ'
        elif letter_upper == 'SOFT':
            letter_upper = 'Ь'
        else:
            # Пытаемся найти букву по имени файла
            for letter, file_name in RU_FILE_NAMES.items():
                if file_name == module_name.split('_')[2]:
                    letter_upper = letter.upper()
                    break
    else:
        language = 'en'
        letter_upper = module_name.split('_')[2].upper()

    # Создаём содержимое модуля
    content = f'''# {module_path.relative_to(get_project_root())}
"""
Термины на букву {letter_upper}
"""
from dicts.base_term import Term

TERMS = {{
    # ============ ДОБАВЬТЕ ТЕРМИНЫ НА БУКВУ {letter_upper} ============
}}
'''

    with open(module_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True


def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("🔧 ИНТЕРАКТИВНОЕ ДОБАВЛЕНИЕ ТЕРМИНОВ")
    print("=" * 60)
    print("\nИнструкция:")
    print("  1. Введите название термина")
    print("  2. Введите описание (можно многострочное)")
    print("  3. Для завершения ввода описания введите пустую строку")
    print("  4. Скрипт автоматически определит букву и язык")
    print("  5. Термин будет добавлен в нужный модуль")
    print("\nДля выхода введите 'q' в поле названия")
    print("=" * 60)

    added_count = 0

    while True:
        # Читаем термин от пользователя
        name, description = read_term_from_user()

        if name is None and description is None:
            break

        if not name or not description:
            continue

        # Определяем язык и букву
        lang, letter, index, file_name = detect_language_and_letter(name)

        if not lang:
            print(f"⚠️ Не удалось определить язык для '{name}'")
            print("   Первая буква должна быть русской или английской")
            continue

        # Получаем путь к модулю
        module_path = get_module_path(lang, letter, index, file_name)

        print(f"\n📊 Определено:")
        print(f"   Язык: {'Русский' if lang == 'ru' else 'English'}")
        print(f"   Буква: {letter.upper()}")
        print(f"   Модуль: {module_path.name}")

        # Подтверждение
        print(f"\n📝 Термин: {name}")
        print(f"📄 Описание: {description[:100]}..." if len(description) > 100 else f"📄 Описание: {description}")

        confirm = input("\nДобавить термин? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Отменено")
            continue

        # Добавляем термин
        if add_term_to_module(module_path, name, description):
            print(f"✅ Термин '{name}' добавлен в {module_path.relative_to(get_project_root())}")
            added_count += 1
        else:
            print(f"❌ Ошибка при добавлении '{name}'")

        print("-" * 40)

    print("\n" + "=" * 60)
    print(f"✅ Готово! Добавлено терминов: {added_count}")
    print("=" * 60)


if __name__ == '__main__':
    main()