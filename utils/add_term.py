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
    """Форматирует описание для вставки в модуль (сохраняет ВСЕ переносы и пустые строки)"""
    if not description:
        return '""'

    lines = description.split('\n')

    # Убираем пустые строки только в самом начале и самом конце
    while lines and lines[0].strip() == '':
        lines.pop(0)
    while lines and lines[-1].strip() == '':
        lines.pop()

    if not lines:
        return '""'

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
    """
    Добавляет или ПЕРЕЗАПИСЫВАЕТ термин в модуле.
    Если термин существует — он заменяется новым описанием.
    """
    if not module_path.exists():
        create_module(module_path)

    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()

    formatted_desc = format_description_for_module(description)
    new_entry = f'\n    "{term_name}": Term(\n        name="{term_name.capitalize()}",\n        description={formatted_desc}\n    ),'

    # Проверяем, существует ли термин
    term_pattern = f'"{term_name}":'
    if term_pattern in content:
        # Термин существует — ПЕРЕЗАПИСЫВАЕМ его
        start = content.find(term_pattern)
        if start == -1:
            return False, f"Не удалось найти термин '{term_name}'"

        # Ищем конец записи: находим закрывающую скобку ")"
        depth = 0
        end = start
        in_string = False
        i = start

        while i < len(content):
            ch = content[i]

            if ch == '"' and (i == 0 or content[i - 1] != '\\'):
                in_string = not in_string

            if not in_string:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        while end < len(content) and content[end].isspace():
                            end += 1
                        if end < len(content) and content[end] == ',':
                            end += 1
                        break
            i += 1

        if end <= start:
            return False, f"Не удалось определить конец записи для '{term_name}'"

        new_content = content[:start] + new_entry + content[end:]

        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True, f"Термин '{term_name}' перезаписан!"

    else:
        # Термин НЕ существует — добавляем новый
        if 'TERMS = {' in content:
            start_pos = content.find('TERMS = {') + len('TERMS = {')
            end_pos = content.rfind('}')

            if start_pos > 0 and end_pos > start_pos:
                new_content = (
                        content[:end_pos] +
                        new_entry +
                        '\n' +
                        content[end_pos:]
                )

                with open(module_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True, f"Термин '{term_name}' добавлен!"
            else:
                return False, "Не удалось найти словарь TERMS!"
        else:
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
        stripped = line.lstrip()
        lower_stripped = stripped.lower()

        if lower_stripped.startswith('термин:') or lower_stripped.startswith('term:'):
            if current_name and current_desc_lines:
                desc = '\n'.join(current_desc_lines).strip()
                if desc:
                    terms.append((current_name, desc))
                current_desc_lines = []

            colon_pos = stripped.find(':')
            if colon_pos != -1:
                current_name = stripped[colon_pos + 1:].strip()
            else:
                current_name = stripped
        else:
            if current_name is not None:
                current_desc_lines.append(line)

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

Если термин уже существует — он будет ПЕРЕЗАПИСАН новым описанием.
"""

        info_label = ttk.Label(
            info_frame,
            text=mode_text,
            font=('Arial', 9),
            foreground='gray',
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)

        text_frame = ttk.LabelFrame(main_frame, text="📝 Весь текст с терминами", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        self.input_text = scrolledtext.ScrolledText(
            text_frame,
            height=15,
            font=('Arial', 11),
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)

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

        self.status_label = ttk.Label(
            main_frame,
            text="Готов к работе",
            font=('Arial', 10),
            foreground='gray'
        )
        self.status_label.pack(pady=(15, 0), anchor=tk.W)

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
                "Текст описания..."
            )
            return

        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Найдено {len(terms)} терминов.\n"
            f"Существующие термины будут ПЕРЕЗАПИСАНЫ.\n\n"
            f"Добавить их все?"
        )
        if not confirm:
            return

        added = 0
        updated = 0
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
                if "перезаписан" in message:
                    updated += 1
                else:
                    added += 1
            else:
                errors.append(f"❌ {message}")

        result_msg = (
            f"✅ Добавлено новых терминов: {added}\n"
            f"🔄 Перезаписано существующих: {updated}\n"
            f"📊 Всего обработано: {added + updated} из {len(terms)}"
        )
        if errors:
            result_msg += f"\n\nОшибки:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                result_msg += f"\n... и ещё {len(errors) - 5} ошибок"

        self.status_label.config(text=result_msg, foreground='green' if (added + updated) > 0 else 'red')
        messagebox.showinfo("Результат", result_msg)

        if (added + updated) > 0:
            self.clear_fields()


def main():
    root = tk.Tk()
    app = TermAdderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()