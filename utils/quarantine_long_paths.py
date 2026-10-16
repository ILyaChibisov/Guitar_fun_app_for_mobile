"""
Утилита, которая находит файлы с слишком длинными путями и добавляет их
в .gitignore, чтобы они не попадали в коммит и, соответственно, в сборку.

Файлы НЕ перемещаются и НЕ удаляются — просто игнорируются гитом.

Проблема: python-for-android при упаковке использует tarfile формат USTAR,
который ограничен 100 байтами на поле 'name'. Если полный путь к файлу
превышает лимит — сборка падает с ValueError: name is too long.

Использование:
    python utils/quarantine_long_paths.py              # обновить .gitignore
    python utils/quarantine_long_paths.py --dry-run    # только показать
    python utils/quarantine_long_paths.py --limit 80   # другой лимит
    python utils/quarantine_long_paths.py --top 30     # диагностика
    python utils/quarantine_long_paths.py --clean      # убрать из .gitignore
    python utils/quarantine_long_paths.py --all        # сканировать весь проект

Работает из PyCharm, командной строки и GitHub Actions.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# ============ НАСТРОЙКИ ============

# Корневые папки для сканирования (относительно корня проекта).
SCAN_DIRS = ["chords", "dicts"]

# Что НИКОГДА не сканировать
EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__",
    ".buildozer", "bin", "chords_quarantine",
    ".idea", ".vscode", "build", "dist",
    "node_modules", ".mypy_cache", ".pytest_cache",
}

# Маркеры начала/конца блока в .gitignore
BLOCK_START = "# >>> auto-ignored long paths (utils/quarantine_long_paths.py) >>>"
BLOCK_END = "# <<< auto-ignored long paths <<<"

# Максимальная длина пути в байтах
MAX_PATH_BYTES = 90

# Префикс, который добавляется внутри архива p4a
ARCHIVE_PREFIX = "app/"

# Маркеры корня проекта
PROJECT_MARKERS = ["buildozer.spec", "main.py", ".git", "requirements.txt"]


# ============ КОРЕНЬ ПРОЕКТА ============

def project_root() -> Path:
    env_root = os.environ.get("PROJECT_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if p.exists():
            return p

    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        for marker in PROJECT_MARKERS:
            if (candidate / marker).exists():
                return candidate

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        for marker in PROJECT_MARKERS:
            if (candidate / marker).exists():
                return candidate

    return here.parent


# ============ СКАНИРОВАНИЕ ============

def iter_files(root: Path, scan_dirs):
    """Рекурсивно обходит файлы, пропуская EXCLUDE_DIRS."""
    if scan_dirs:
        bases = [root / d for d in scan_dirs]
    else:
        bases = [root]

    for base in bases:
        if not base.exists():
            print(f"[!] Папка не найдена: {base}")
            continue

        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [
                d for d in dirnames
                if d not in EXCLUDE_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if filename.endswith((".pyc", ".pyo")):
                    continue

                full_path = Path(dirpath) / filename
                try:
                    rel_path = full_path.relative_to(root)
                except ValueError:
                    continue

                archive_path = ARCHIVE_PREFIX + str(rel_path).replace(os.sep, "/")
                path_bytes = len(archive_path.encode("utf-8"))
                yield rel_path, path_bytes, archive_path


# ============ GITIGNORE ============

def read_gitignore(gitignore: Path):
    """Возвращает список строк .gitignore (или пустой список)."""
    if not gitignore.exists():
        return []
    return gitignore.read_text(encoding="utf-8").splitlines()


def write_gitignore(gitignore: Path, lines):
    """Пишет строки в .gitignore, добавляя финальный перевод строки."""
    gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")


def strip_old_block(lines):
    """Удаляет наш старый блок из списка строк .gitignore."""
    result = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if stripped == BLOCK_START:
            inside = True
            continue
        if stripped == BLOCK_END:
            inside = False
            continue
        if not inside:
            result.append(line)
    # Убираем лишние пустые строки в конце
    while result and not result[-1].strip():
        result.pop()
    return result


def update_gitignore(root: Path, ignored_paths, dry_run=False, clean=False):
    """
    Обновляет .gitignore:
      - удаляет наш старый блок (если был),
      - добавляет новый со списком путей,
      - сохраняет остальное содержимое файла нетронутым.
    """
    gitignore = root / ".gitignore"

    if clean:
        lines = read_gitignore(gitignore)
        new_lines = strip_old_block(lines)
        if not dry_run:
            write_gitignore(gitignore, new_lines)
        print(f"[+] Блок удалён из .gitignore ({len(lines) - len(new_lines)} строк)")
        return

    if not ignored_paths:
        print("[i] Нет файлов для игнорирования — .gitignore не меняется.")
        return

    lines = read_gitignore(gitignore)
    lines = strip_old_block(lines)

    # Преобразуем пути в gitignore-формат (прямые слэши, без ведущего ./)
    entries = sorted(
        str(p).replace(os.sep, "/")
        for p in ignored_paths
    )

    block = [BLOCK_START]
    block.append(f"# Всего: {len(entries)} файлов с длиной пути > {MAX_PATH_BYTES} байт")
    block.append(f"# Найдено: {MAX_PATH_BYTES}-байтовый лимит tarfile USTAR")
    block.extend(entries)
    block.append(BLOCK_END)

    new_lines = lines + [""] + block

    if dry_run:
        print(f"[dry-run] В .gitignore будет добавлено {len(entries)} строк:")
        for e in entries[:20]:
            print(f"  {e}")
        if len(entries) > 20:
            print(f"  ... и ещё {len(entries) - 20}")
        return

    write_gitignore(gitignore, new_lines)
    print(f"[+] .gitignore обновлён: добавлено {len(entries)} путей")


# ============ GIT ============

def git_rm_cached(root: Path, paths):
    """Убирает файлы из индекса git (если они уже закоммичены)."""
    git_dir = root / ".git"
    if not git_dir.exists():
        return

    original_paths = [str(p).replace(os.sep, "/") for p in paths]
    BATCH = 500
    removed = 0

    for i in range(0, len(original_paths), BATCH):
        batch = original_paths[i:i + BATCH]
        try:
            result = subprocess.run(
                ["git", "rm", "--cached", "--ignore-unmatch", "-r", *batch],
                cwd=root, capture_output=True, text=True,
            )
            if result.returncode == 0:
                removed += sum(1 for line in result.stdout.splitlines()
                               if line.startswith("rm "))
            else:
                if result.stderr:
                    print(f"[!] git rm: {result.stderr.strip()}")
        except FileNotFoundError:
            print("[!] git не найден в PATH")
            return
        except Exception as e:
            print(f"[!] Ошибка git rm: {e}")
            return

    if removed:
        print(f"[+] Убрано из git-индекса: {removed} файлов")
    else:
        print("[i] В git-индексе этих файлов не было")


# ============ MAIN ============

def main():
    parser = argparse.ArgumentParser(description="Добавляет длинные пути в .gitignore.")
    parser.add_argument("--limit", type=int, default=MAX_PATH_BYTES)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clean", action="store_true",
                        help="Удалить наш блок из .gitignore")
    parser.add_argument("--root", type=str, default=None)
    parser.add_argument("--top", type=int, default=0)
    parser.add_argument("--no-git", action="store_true",
                        help="Не трогать git-индекс")
    parser.add_argument("--all", action="store_true",
                        help="Сканировать весь проект, а не только SCAN_DIRS")

    args, unknown = parser.parse_known_args()
    if unknown:
        print(f"[i] Игнорирую неизвестные аргументы: {unknown}")

    root = Path(args.root).resolve() if args.root else project_root()

    print(f"[i] Корень проекта: {root}")
    print(f"[i] Рабочая директория: {Path.cwd()}")

    if args.clean:
        update_gitignore(root, [], dry_run=args.dry_run, clean=True)
        return

    scan_dirs = None if args.all else SCAN_DIRS
    print(f"[i] Сканируются: {scan_dirs if scan_dirs else 'весь проект'}")
    print(f"[i] Лимит: {args.limit} байт (включая префикс '{ARCHIVE_PREFIX}')")
    print()

    all_files = list(iter_files(root, scan_dirs))
    print(f"[i] Всего файлов просканировано: {len(all_files)}")

    if args.top > 0 and all_files:
        print(f"\n[i] Топ-{args.top} самых длинных путей:")
        for rel, n, ap in sorted(all_files, key=lambda x: -x[1])[:args.top]:
            marker = "  <-- превышает" if n > args.limit else ""
            print(f"  {n:>4}  {ap}{marker}")
        print()

    long_files = [(rel, n, ap) for rel, n, ap in all_files if n > args.limit]

    if not long_files:
        print("[+] Проблемных файлов не найдено.")
        return

    print(f"[!] Найдено файлов с длинным путём: {len(long_files)}")

    paths_to_ignore = [rel for rel, _, _ in long_files]
    update_gitignore(root, paths_to_ignore, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n[dry-run] Ничего не изменено.")
        return

    if not args.no_git:
        git_rm_cached(root, paths_to_ignore)

    print()
    print(f"[i] Отмена: python {Path(__file__).name} --clean")


if __name__ == "__main__":
    main()