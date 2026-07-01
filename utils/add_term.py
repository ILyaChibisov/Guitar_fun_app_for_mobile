# utils/add_term_gui.py
"""
GUI-приложение для добавления терминов в словарь
Запуск: python -m utils.add_term_gui

Пакетный режим: вставьте весь текст в поле ввода.
Формат: каждая запись начинается с "Термин:" (русский) или "Term:" (английский)
Все пробелы и пустые строки в описании сохраняются.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import re
from pathlib import Path

# ============ НАСТРОЙКИ ============

RU_LETTERS = {
    'а': '01', 'б': '02', 'в': '03', 'г': '04', 'д': '05',
    'е': '06', 'ё': '07', 'ж': '08', 'з': '09', 'и': '10',
    'й': '11', 'к': '12', 'л': '13', 'м': '14', 'н': '15',
    'о': '16', 'п': '17', 'р': '18', 'с': '19', 'т': '20',
    'у': '21', 'ф': '22', 'х': '23', 'ц': '24', 'ч': '25',
    'ш': '26', 'щ': '27', 'ъ': '28', 'ы': '29', 'ь': '30',
    'э': '31', 'ю': '32', 'я': '33'
}

EN_LETTERS = {
    'a': '01', 'b': '02', 'c': '03', 'd': '04', 'e': '05',
    'f': '06', 'g': '07', 'h': '08', 'i': '09', 'j': '10',
    'k': '11', 'l': '12', 'm': '13', 'n': '14', 'o': '15',
    'p': '16', 'q': '17', 'r': '18', 's': '19', 't': '20',
    'u': '21', 'v': '22', 'w': '23', 'x': '24', 'y': '25', 'z': '26'
}

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
    current = Path(__file__).resolve()
    return current.parent.parent


def clean_term_name(raw_name):
    """Очищает название от лишних символов"""
    cleaned = re.sub(r'^[🎼🎸📝🔹📌📊✅❌⚠️📁]+\s*', '', raw_name)
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()


def detect_language_and_letter(term_name):
    """Определяет язык и первую букву термина"""
    if not term_name:
        return None, None, None, None

    first_char = term_name[0].lower()

    if first_char in RU_LETTERS:
        return 'ru', first_char, RU_LETTERS[first_char], RU_FILE_NAMES[first_char]

    if first_char in EN_LETTERS:
        return 'en', first_char, EN_LETTERS[first_char], EN_FILE_NAMES[first_char]

    return None, None, None, None


def get_module_path(language, letter, index, file_name):
    root = get_project_root()
    if language == 'ru':
        return root / 'dicts' / 'ru' / f'ru_{index}_{file_name}.py'
    else:
        return root / 'dicts' / 'en' / f'en_{index}_{file_name}.py'


def format_description_for_module(description):
    """Форматирует описание для вставки в модуль (сохраняет все переносы)"""
    if not description:
        return '""'

    # Разбиваем на строки
    lines = description.split('\n')

    # Убираем пустые строки в начале и конце
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        return '""'

    # Если больше одной строки — используем тройные кавычки
    if len(lines) > 1:
        return '"""\n' + '\n'.join(lines) + '\n"""'
    else:
        return f'"{lines[0].strip()}"'


def create_module(module_path):
    """Создаёт новый модуль для буквы"""
    module_name = module_path.stem

    if module_name.startswith('ru_'):
        letter_upper = module_name.split('_')[2].upper()
        if letter_upper == 'YO':
            letter_upper = 'Ё'
        elif letter_upper == 'HARD':
            letter_upper = 'Ъ'
        elif letter_upper == 'SOFT':
            letter_upper = 'Ь'
        else:
            for letter, file_name in RU_FILE_NAMES.items():
                if file_name == module_name.split('_')[2]:
                    letter_upper = letter.upper()
                    break
    else:
        letter_upper = module_name.split('_')[2].upper()

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


def add_term_to_module(module_path, term_name, description):
    """Добавляет термин в модуль"""
    if not module_path.exists():
        create_module(module_path)

    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if f'"{term_name}":' in content or f"'{term_name}':" in content:
        return False, f"Термин '{term_name}' уже существует!"

    formatted_desc = format_description_for_module(description)
    term_entry = f'\n    "{term_name}": Term(\n        name="{term_name.capitalize()}",\n        description={formatted_desc}\n    ),'

    if 'TERMS = {' in content:
        start_pos = content.find('TERMS = {') + len('TERMS = {')
        end_pos = content.rfind('}')

        if start_pos > 0 and end_pos > start_pos:
            new_content = (
                    content[:end_pos] +
                    term_entry +
                    '\n' +
                    content[end_pos:]
            )

            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, f"Термин '{term_name}' успешно добавлен!"

    return False, "Не удалось найти словарь TERMS!"


def parse_batch_text(text):
    """
    Парсит пакетный текст на термины.
    Поддерживает два маркера:
    - "Термин:" (русский)
    - "Term:" (английский)
    """
    terms = []
    lines = text.split('\n')

    current_name = None
    current_desc_lines = []

    for line in lines:
        stripped = line.strip()

        # Проверяем, начинается ли строка с "Термин:" или "Term:"
        lower_line = stripped.lower()
        if lower_line.startswith('термин:') or lower_line.startswith('term:'):
            # Сохраняем предыдущий термин
            if current_name and current_desc_lines:
                desc = '\n'.join(current_desc_lines).strip()
                if desc:
                    terms.append((current_name, desc))
                current_desc_lines = []

            # Извлекаем название (всё после маркера)
            parts = stripped.split(':', 1)
            if len(parts) == 2:
                current_name = parts[1].strip()
            else:
                current_name = stripped
        else:
            # Это описание (только если есть текущий термин)
            if current_name is not None:
                current_desc_lines.append(line)

    # Добавляем последний термин
    if current_name and current_desc_lines:
        desc = '\n'.join(current_desc_lines).strip()
        if desc:
            terms.append((current_name, desc))

    return terms


class TermAdderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Добавление терминов в словарь 🎸")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)

        style = ttk.Style()
        style.theme_use('clam')

        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="🎼 ДОБАВЛЕНИЕ ТЕРМИНОВ В СЛОВАРЬ",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 10))

        info_frame = ttk.LabelFrame(main_frame, text="📋 Формат ввода", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        mode_text = """Вставьте ВЕСЬ текст в поле ниже.

Формат:
    Термин: НАЗВАНИЕ 1    (для русских терминов)
    Текст описания...

    или

    Term: NAME 1          (для английских терминов)
    Text description...

Важно: каждый термин ДОЛЖЕН начинаться со слова "Термин:" или "Term:"
"""

        info_label = ttk.Label(
            info_frame,
            text=mode_text,
            font=('Arial', 9),
            foreground='gray',
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)

        # Основное поле для ввода всего текста
        text_frame = ttk.LabelFrame(main_frame, text="📝 Весь текст с терминами", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.input_text = scrolledtext.ScrolledText(
            text_frame,
            height=15,
            font=('Arial', 11),
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)

        # Кнопка вставки под полем
        paste_btn_frame = ttk.Frame(text_frame)
        paste_btn_frame.pack(fill=tk.X, pady=(5, 0))

        paste_btn = ttk.Button(
            paste_btn_frame,
            text="📋 Вставить из буфера обмена",
            command=lambda: self.paste_to_widget(self.input_text),
            width=30
        )
        paste_btn.pack(side=tk.LEFT)

        hint_label = ttk.Label(
            paste_btn_frame,
            text="💡 Или используйте Ctrl+V",
            font=('Arial', 9),
            foreground='gray'
        )
        hint_label.pack(side=tk.LEFT, padx=(10, 0))

        # Панель кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Очистить",
            command=self.clear_fields,
            width=15
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        add_btn = ttk.Button(
            button_frame,
            text="✅ Добавить все термины",
            command=self.add_terms_batch,
            width=25
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        exit_btn = ttk.Button(
            button_frame,
            text="🚪 Выход",
            command=self.root.quit,
            width=15
        )
        exit_btn.pack(side=tk.RIGHT)

        # Статусная строка
        self.status_label = ttk.Label(
            main_frame,
            text="Готов к работе",
            font=('Arial', 10),
            foreground='gray'
        )
        self.status_label.pack(pady=(15, 0), anchor=tk.W)

        # Горячие клавиши
        self.input_text.bind('<Control-v>', self.paste_to_widget_event)
        self.input_text.bind('<Control-V>', self.paste_to_widget_event)
        self.root.bind('<Control-Return>', lambda e: self.add_terms_batch())

    def paste_to_widget(self, widget):
        try:
            text = self.root.clipboard_get()
            if text:
                widget.insert(tk.INSERT, text)
        except tk.TclError:
            messagebox.showinfo("Информация", "Буфер обмена пуст!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось вставить текст: {e}")

    def paste_to_widget_event(self, event):
        widget = event.widget
        self.paste_to_widget(widget)
        return "break"

    def clear_fields(self):
        self.input_text.delete("1.0", tk.END)
        self.status_label.config(text="Поля очищены", foreground='gray')

    def add_terms_batch(self):
        text = self.input_text.get("1.0", "end-1c").strip()

        if not text:
            messagebox.showwarning("Ошибка", "Вставьте текст с терминами!")
            return

        terms = parse_batch_text(text)

        if not terms:
            messagebox.showwarning(
                "Ошибка",
                "Не удалось распарсить текст.\n\n"
                "Проверьте формат:\n"
                "Термин: НАЗВАНИЕ 1\n"
                "Текст описания...\n"
                "Термин: НАЗВАНИЕ 2\n"
                "Текст описания...\n\n"
                "или\n\n"
                "Term: NAME 1\n"
                "Text description...\n"
                "Term: NAME 2\n"
                "Text description..."
            )
            return

        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Найдено {len(terms)} терминов.\nДобавить их все?"
        )
        if not confirm:
            return

        added = 0
        errors = []

        for term_name, description in terms:
            clean_name = clean_term_name(term_name)
            if not clean_name:
                errors.append(f"❌ Не удалось очистить название: {term_name}")
                continue

            lang, letter, index, file_name = detect_language_and_letter(clean_name)
            if not lang:
                errors.append(f"❌ Не удалось определить язык для: {clean_name}")
                continue

            module_path = get_module_path(lang, letter, index, file_name)
            success, message = add_term_to_module(module_path, clean_name, description)

            if success:
                added += 1
            else:
                errors.append(f"❌ {message}")

        result_msg = f"✅ Добавлено терминов: {added} из {len(terms)}"
        if errors:
            result_msg += f"\n\nОшибки:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                result_msg += f"\n... и ещё {len(errors) - 5} ошибок"

        self.status_label.config(text=result_msg, foreground='green' if added > 0 else 'red')
        messagebox.showinfo("Результат", result_msg)

        if added > 0:
            self.clear_fields()


def main():
    root = tk.Tk()
    app = TermAdderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()