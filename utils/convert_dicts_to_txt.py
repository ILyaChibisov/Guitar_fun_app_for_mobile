# utils/convert_dicts_to_txt.py
"""
Конвертор Python-словарей терминов (dicts/) в текстовые файлы.

Структура результата:
    data/dicts/rus/<буква>/<Имя термина>.txt
    data/dicts/en/<буква>/<Имя термина>.txt

Формат файла:
    <Имя термина>
    <пустая строка>
    <описание (как в исходнике, с сохранением отступов)>

Запуск (из корня приложения):
    python utils/convert_dicts_to_txt.py --dry-run
    python utils/convert_dicts_to_txt.py
    python utils/convert_dicts_to_txt.py --report report.json

Особенности:
- Парсит __init__.py и модули через ast (без импорта, без зависимостей).
- Буква берётся из маппинга <LANG>_TERMS_BY_LETTER в __init__.py.
- Имя файла = Term.name. Санитизируется; оригинал всегда в 1-й строке файла.
- Идемпотентен: существующие файлы не перезаписываются.
- Пишет отчёт JSON: created / skipped_duplicate / skipped_invalid / warnings.
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

# ============================================================
# КОНСТАНТЫ
# ============================================================

# Соответствие: код языка → имя папки в data/dicts/
LANG_DIRS = {
    "ru": "rus",
    "en": "en",
}

# Запрещённые в именах файлов символы
ILLEGAL_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Максимальная длина имени файла (без .txt)
MAX_FILENAME_LEN = 120


# ============================================================
# ПАРСИНГ ИСХОДНИКОВ
# ============================================================

def parse_init_mapping(init_path: Path) -> dict:
    """
    Читает __init__.py и возвращает {letter: module_name}.

    Логика:
      1. Собирает псевдонимы импортов TERMS:
             from .ru_01_a import TERMS as А_TERMS
         →   {'А_TERMS': 'ru_01_a'}
      2. Находит <LANG>_TERMS_BY_LETTER = { 'а': А_TERMS, ... }
         и подставляет module_name вместо алиаса.

    Важно: алиасы Y_TERMS и Y_TERMS2 в ru/__init__.py
    ведут на разные модули (ru_11_y и ru_29_y) — оба корректно
    различаются, т.к. читаем asname.
    """
    tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))

    alias_to_module = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            for al in node.names:
                if al.name != "TERMS":
                    continue
                local_name = al.asname or al.name
                alias_to_module[local_name] = mod

    letter_to_module = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name)
                    and target.id.endswith("_TERMS_BY_LETTER")):
                continue
            if not isinstance(node.value, ast.Dict):
                continue
            for k, v in zip(node.value.keys, node.value.values):
                if not isinstance(k, ast.Constant) or not isinstance(v, ast.Name):
                    continue
                letter = str(k.value)
                alias = v.id
                module = alias_to_module.get(alias)
                if module is None:
                    continue
                letter_to_module[letter] = module
    return letter_to_module


def extract_terms_from_module(module_path: Path) -> list:
    """
    Парсит файл модуля и возвращает список:
        [{"key": ..., "name": ..., "description": ...}, ...]

    Ожидает структуру:
        TERMS = {
            "КЛЮЧ": Term(name="...", description="<многострочная строка>"),
            ...
        }
    """
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))

    result = []
    for node in tree.body:
        if not (isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "TERMS"
                        for t in node.targets)):
            continue
        if not isinstance(node.value, ast.Dict):
            continue

        for k_node, v_node in zip(node.value.keys, node.value.values):
            if not (isinstance(k_node, ast.Constant)
                    and isinstance(k_node.value, str)):
                continue
            key = k_node.value

            if not (isinstance(v_node, ast.Call)
                    and isinstance(v_node.func, ast.Name)
                    and v_node.func.id == "Term"):
                continue

            name = None
            description = None
            for kw in v_node.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                    name = kw.value.value
                elif kw.arg == "description" and isinstance(kw.value, ast.Constant):
                    description = kw.value.value

            if name is None or description is None:
                continue

            result.append({
                "key": key,
                "name": name,
                "description": description,
            })
    return result


# ============================================================
# САНИТИЗАЦИЯ
# ============================================================

def sanitize_filename(name: str) -> str:
    """Безопасное имя файла (без .txt)."""
    if not name:
        return ""
    s = name.strip()
    s = ILLEGAL_FILENAME.sub("_", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"_{2,}", "_", s)
    s = s.rstrip(". ")
    if len(s) > MAX_FILENAME_LEN:
        s = s[:MAX_FILENAME_LEN].rstrip(". ")
    return s or "term"


def normalize_description(desc: str) -> str:
    """
    Убирает ОДИН ведущий и ОДИН хвостовой \\n.
    Внутренние отступы/пустые строки сохраняются.
    """
    if desc is None:
        return ""
    if desc.startswith("\n"):
        desc = desc[1:]
    if desc.endswith("\n"):
        desc = desc[:-1]
    return desc


# ============================================================
# ОСНОВНАЯ ЛОГИКА
# ============================================================

def convert_language(
    lang_code: str,
    lang_dir_name: str,
    source_dir: Path,
    target_root: Path,
    dry_run: bool,
    report: dict,
):
    init_path = source_dir / "__init__.py"
    if not init_path.exists():
        report["warnings"].append(f"[{lang_code}] Нет __init__.py: {init_path}")
        return

    letter_to_module = parse_init_mapping(init_path)
    if not letter_to_module:
        report["warnings"].append(
            f"[{lang_code}] Не удалось извлечь маппинг из {init_path}"
        )
        return

    target_lang_root = target_root / lang_dir_name

    for letter, module_name in sorted(letter_to_module.items()):
        module_path = source_dir / f"{module_name}.py"
        if not module_path.exists():
            report["warnings"].append(
                f"[{lang_code}] Нет модуля {module_path.name} "
                f"для буквы '{letter}'"
            )
            continue

        try:
            terms = extract_terms_from_module(module_path)
        except SyntaxError as e:
            report["warnings"].append(
                f"[{lang_code}] Синтаксис в {module_path.name}: {e}"
            )
            continue
        except Exception as e:
            report["warnings"].append(
                f"[{lang_code}] Ошибка парсинга {module_path.name}: {e}"
            )
            continue

        if not terms:
            report["warnings"].append(
                f"[{lang_code}] Пусто в {module_path.name} (буква '{letter}')"
            )
            continue

        letter_dir = target_lang_root / letter

        for term in terms:
            name = term["name"]
            key = term["key"]
            desc = normalize_description(term["description"])

            # Диагностика: первая буква имени vs буква модуля
            first = name.lstrip('«»"\'').strip()[:1].lower()
            if first and first != letter:
                report["warnings"].append(
                    f"[{lang_code}] Термин '{name}' (ключ '{key}') "
                    f"лежит в модуле буквы '{letter}', "
                    f"но начинается на '{first}'"
                )

            safe_name = sanitize_filename(name)
            if not safe_name:
                report["skipped_invalid"].append({
                    "lang": lang_code, "letter": letter,
                    "key": key, "name": name,
                    "reason": "empty filename after sanitize",
                })
                continue

            if safe_name != name:
                report["warnings"].append(
                    f"[{lang_code}] Имя '{name}' санитизировано → '{safe_name}'"
                )

            file_path = letter_dir / f"{safe_name}.txt"

            if file_path.exists():
                report["skipped_duplicate"].append({
                    "lang": lang_code, "letter": letter,
                    "key": key, "name": name,
                    "file": str(file_path),
                })
                continue

            content = f"{name}\n\n{desc}"
            if not content.endswith("\n"):
                content += "\n"

            if dry_run:
                report["created"].append({
                    "lang": lang_code, "letter": letter,
                    "key": key, "name": name,
                    "file": str(file_path),
                    "dry_run": True,
                })
            else:
                letter_dir.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")
                report["created"].append({
                    "lang": lang_code, "letter": letter,
                    "key": key, "name": name,
                    "file": str(file_path),
                })


def main():
    parser = argparse.ArgumentParser(
        description="dicts/*.py → data/dicts/<lang>/<letter>/*.txt"
    )
    parser.add_argument(
        "--source", default="dicts",
        help="Папка с исходными Python-модулями (по умолчанию: dicts)",
    )
    parser.add_argument(
        "--target", default="data/dicts",
        help="Куда писать txt (по умолчанию: data/dicts)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Только показать, что было бы создано",
    )
    parser.add_argument(
        "--report", default="convert_report.json",
        help="Файл отчёта JSON (по умолчанию: convert_report.json)",
    )
    args = parser.parse_args()

    source_root = Path(args.source).resolve()
    target_root = Path(args.target).resolve()

    if not source_root.exists():
        print(f"❌ Не найдена папка с исходниками: {source_root}")
        sys.exit(1)

    print(f"📂 Источник:   {source_root}")
    print(f"📂 Назначение: {target_root}")
    print(f"🧪 Dry run:    {args.dry_run}")
    print()

    report = {
        "source": str(source_root),
        "target": str(target_root),
        "dry_run": args.dry_run,
        "created": [],
        "skipped_duplicate": [],
        "skipped_invalid": [],
        "warnings": [],
    }

    for lang_code, lang_dir in LANG_DIRS.items():
        source_dir = source_root / lang_code
        if not source_dir.exists():
            report["warnings"].append(f"Нет папки {source_dir}")
            continue

        print(f"🔄 Обработка языка: {lang_code} → {lang_dir}/")
        convert_language(
            lang_code=lang_code,
            lang_dir_name=lang_dir,
            source_dir=source_dir,
            target_root=target_root,
            dry_run=args.dry_run,
            report=report,
        )

    print()
    print("=" * 60)
    print(f"✅ Создано файлов:      {len(report['created'])}")
    print(f"⏭️  Дубликаты (пропуск): {len(report['skipped_duplicate'])}")
    print(f"❌ Невалидные имена:    {len(report['skipped_invalid'])}")
    print(f"⚠️  Предупреждений:     {len(report['warnings'])}")
    print("=" * 60)

    if report["warnings"]:
        print("\n⚠️  Предупреждения (первые 30):")
        for w in report["warnings"][:30]:
            print(f"   • {w}")
        if len(report["warnings"]) > 30:
            print(f"   ... и ещё {len(report['warnings']) - 30}")

    if report["skipped_invalid"]:
        print("\n❌ Невалидные (первые 20):")
        for it in report["skipped_invalid"][:20]:
            print(f"   • [{it['lang']}/{it['letter']}] "
                  f"'{it['name']}' — {it['reason']}")

    report_path = Path(args.report).resolve()
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n📝 Отчёт: {report_path}")


if __name__ == "__main__":
    main()