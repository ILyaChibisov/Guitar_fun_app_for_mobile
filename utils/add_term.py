# utils/add_term_gui.py
"""
GUI-приложение для добавления терминов в словарь
Запуск: python -m utils.add_term_gui

Никаких дополнительных библиотек не требуется (используется встроенный tkinter)
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import re
from pathlib import Path

# ============ НАСТРОЙКИ (скопированы из add_term.py) ============

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
    """Очищает название от эмодзи и лишних символов"""
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
    """Форматирует описание для вставки в модуль"""
    if '\n' in description:
        desc_lines = description.split('\n')
        while desc_lines and not desc_lines[0].strip():
            desc_lines.pop(0)
        while desc_lines and not desc_lines[-1].strip():
            desc_lines.pop()

        if len(desc_lines) > 1:
            return '"""\n' + '\n'.join(desc_lines) + '\n"""'
        else:
            return f'"{desc_lines[0].strip()}"'
    else:
        return f'"{description}"'


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
        return False, "Термин уже существует!"

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
            return True, "Термин успешно добавлен!"

    return False, "Не удалось найти словарь TERMS!"


class TermAdderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Добавление терминов в словарь 🎸")
        self.root.geometry("950x750")
        self.root.resizable(True, True)

        # Настройка стиля
        style = ttk.Style()
        style.theme_use('clam')

        # Главный контейнер с отступами
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="🎼 ДОБАВЛЕНИЕ ТЕРМИНА В СЛОВАРЬ",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # Информационная панель
        info_frame = ttk.LabelFrame(main_frame, text="📋 Информация", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))

        self.info_label = ttk.Label(
            info_frame,
            text="Вставьте название и описание термина, затем нажмите 'Добавить'",
            font=('Arial', 10)
        )
        self.info_label.pack(anchor=tk.W)

        # Поле для названия
        name_frame = ttk.LabelFrame(main_frame, text="📝 Название термина", padding="10")
        name_frame.pack(fill=tk.X, pady=(0, 15))

        # Верхняя панель с полем и кнопкой вставки
        name_top_frame = ttk.Frame(name_frame)
        name_top_frame.pack(fill=tk.X)

        self.name_text = tk.Text(name_top_frame, height=2, font=('Arial', 11), wrap=tk.WORD)
        self.name_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопка вставки для названия
        name_paste_btn = ttk.Button(
            name_top_frame,
            text="📋 Вставить",
            command=lambda: self.paste_to_widget(self.name_text),
            width=10
        )
        name_paste_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Подсказка для названия
        name_hint = ttk.Label(
            name_frame,
            text="💡 Вставьте название (можно с эмодзи) или введите вручную. Используйте кнопку 'Вставить' или Ctrl+V",
            font=('Arial', 9),
            foreground='gray'
        )
        name_hint.pack(anchor=tk.W, pady=(5, 0))

        # Поле для описания
        desc_frame = ttk.LabelFrame(main_frame, text="📄 Описание термина", padding="10")
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Верхняя панель с полем и кнопкой вставки
        desc_top_frame = ttk.Frame(desc_frame)
        desc_top_frame.pack(fill=tk.BOTH, expand=True)

        self.desc_text = scrolledtext.ScrolledText(
            desc_top_frame,
            height=12,
            font=('Arial', 10),
            wrap=tk.WORD
        )
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Кнопка вставки для описания
        desc_paste_btn = ttk.Button(
            desc_top_frame,
            text="📋 Вставить",
            command=lambda: self.paste_to_widget(self.desc_text),
            width=10
        )
        desc_paste_btn.pack(side=tk.RIGHT, padx=(10, 0), fill=tk.Y)

        # Подсказка для описания
        desc_hint = ttk.Label(
            desc_frame,
            text="💡 Вставьте описание (можно многострочное). Используйте кнопку 'Вставить' или Ctrl+V",
            font=('Arial', 9),
            foreground='gray'
        )
        desc_hint.pack(anchor=tk.W, pady=(5, 0))

        # Панель кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Кнопка "Очистить"
        clear_btn = ttk.Button(
            button_frame,
            text="🗑️ Очистить",
            command=self.clear_fields,
            width=15
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Кнопка "Добавить"
        add_btn = ttk.Button(
            button_frame,
            text="✅ Добавить термин (Ctrl+Enter)",
            command=self.add_term,
            width=25
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Кнопка "Выход"
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

        # Быстрые кнопки для вставки примеров
        quick_frame = ttk.LabelFrame(main_frame, text="⚡ Быстрая вставка", padding="5")
        quick_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            quick_frame,
            text="Вставить название (А БАТТУТА)",
            command=self.insert_example_name,
            width=25
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            quick_frame,
            text="Вставить описание (А БАТТУТА)",
            command=self.insert_example_desc,
            width=25
        ).pack(side=tk.LEFT)

        # Привязываем горячие клавиши
        self.name_text.bind('<Control-v>', self.paste_to_widget_event)
        self.name_text.bind('<Control-V>', self.paste_to_widget_event)
        self.desc_text.bind('<Control-v>', self.paste_to_widget_event)
        self.desc_text.bind('<Control-V>', self.paste_to_widget_event)
        self.root.bind('<Control-Return>', lambda e: self.add_term())

    def paste_to_widget(self, widget):
        """Вставляет текст из буфера обмена в указанный виджет"""
        try:
            # Получаем текст из системного буфера обмена
            text = self.root.clipboard_get()
            if text:
                # Вставляем в позицию курсора
                widget.insert(tk.INSERT, text)
                # Обновляем статус для поля названия
                if widget == self.name_text:
                    self.root.after(100, self.update_status_after_paste)
        except tk.TclError:
            # Буфер обмена пуст или недоступен
            messagebox.showinfo("Информация", "Буфер обмена пуст!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось вставить текст: {e}")

    def paste_to_widget_event(self, event):
        """Обработчик события вставки"""
        widget = event.widget
        self.paste_to_widget(widget)
        return "break"  # Отменяем стандартную обработку

    def update_status_after_paste(self):
        """Обновление статуса после вставки"""
        name = self.name_text.get("1.0", "end-1c").strip()
        if name:
            clean = clean_term_name(name)
            lang, letter, index, file_name = detect_language_and_letter(clean)
            if lang:
                lang_text = "Русский" if lang == 'ru' else "English"
                self.status_label.config(
                    text=f"✅ Определено: {lang_text}, буква '{letter.upper()}'",
                    foreground='green'
                )
            else:
                self.status_label.config(
                    text="⚠️ Не удалось определить язык (первая буква должна быть русской или английской)",
                    foreground='orange'
                )

    def clear_fields(self):
        """Очищает все поля"""
        self.name_text.delete("1.0", tk.END)
        self.desc_text.delete("1.0", tk.END)
        self.status_label.config(text="Поля очищены", foreground='gray')

    def insert_example_name(self):
        """Вставляет пример названия"""
        self.name_text.delete("1.0", tk.END)
        self.name_text.insert("1.0", "🎼 А БАТТУТА (итал. «по ударению», «по такту»)")
        self.update_status_after_paste()

    def insert_example_desc(self):
        """Вставляет пример описания"""
        example_desc = """Команда вернуться к строгому метрическому пульсу и ясной тактовой доле после периода ритмической свободы. Это не просто «сыграть в темп», а именно подчиниться жесткой сетке размера, часто с акцентированием сильных долей.

Где встречается:
После выразительного Rubato (свободное ведение мелодии).
После длительной Ферматы (задержанная нота) или паузы.
После постепенного замедления (Ritardando / Rallentando).
В конце сольной Каденции (виртуозной вставки).

Специфика для гитариста:
Первое — смена атаки. Гитаристы часто переключаются на апояндо (опертый удар).
Второе — работа правой руки. В испанской или фламенко-музыке это сигнал включить режим метронома.
Третье — баррэ и смена позиций. Гитаристы упрощают аппликатуру.
Четвертое — работа в ансамбле. Ритм-гитарист становится барабанщиком.

Пример из практики:
Вступление к балладе играется свободно. На аккорде перед припевом стоит фермата. После нее A battuta — припев нужно врубить ровно, с мощным downstroke."""
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert("1.0", example_desc)

    def add_term(self):
        """Добавляет термин в словарь"""
        # Получаем данные
        name = self.name_text.get("1.0", "end-1c").strip()
        description = self.desc_text.get("1.0", "end-1c").strip()

        # Проверки
        if not name:
            messagebox.showwarning("Ошибка", "Введите название термина!")
            self.name_text.focus()
            return

        if not description:
            messagebox.showwarning("Ошибка", "Введите описание термина!")
            self.desc_text.focus()
            return

        # Очищаем название
        clean_name = clean_term_name(name)

        if not clean_name:
            messagebox.showwarning("Ошибка", "Название не может быть пустым!")
            return

        # Определяем язык и букву
        lang, letter, index, file_name = detect_language_and_letter(clean_name)

        if not lang:
            messagebox.showwarning(
                "Ошибка",
                f"Не удалось определить язык для '{clean_name}'\n"
                "Первая буква должна быть русской или английской"
            )
            return

        # Получаем путь к модулю
        module_path = get_module_path(lang, letter, index, file_name)

        # Добавляем термин
        success, message = add_term_to_module(module_path, clean_name, description)

        if success:
            lang_text = "Русский" if lang == 'ru' else "English"
            status_msg = (
                f"✅ Термин '{clean_name}' добавлен!\n"
                f"   📁 Модуль: {module_path.relative_to(get_project_root())}\n"
                f"   🌐 Язык: {lang_text}\n"
                f"   🔤 Буква: {letter.upper()}"
            )

            self.status_label.config(text=status_msg, foreground='green')
            messagebox.showinfo("Успешно!", status_msg)

            # Очищаем поля для следующего термина
            self.clear_fields()

        else:
            self.status_label.config(text=f"❌ {message}", foreground='red')
            messagebox.showerror("Ошибка", message)


def main():
    root = tk.Tk()
    app = TermAdderApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()