# utils/upload_chords.py
"""
Загрузка всех аккордов из /chords/ на сервер (PostgreSQL через API).

Запуск из PyCharm: правый клик → Run 'upload_chords'

Настройки берутся из:
  - config.app_config.API_BASE_URL (URL API)
  - auth.json в корне проекта (JWT-токены)

Токены загружаются напрямую из auth.json в корне проекта,
чтобы не зависеть от os.getcwd() и JsonStore.
"""
import importlib.util
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============ ПУТИ ============

# Скрипт лежит в utils/, корень проекта — на уровень выше
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CHORDS_DIR = PROJECT_ROOT / "chords"
AUTH_JSON = PROJECT_ROOT / "auth.json"


# ============ ДИАГНОСТИКА ============

print("=" * 70)
print("🔍 Диагностика окружения")
print(f"   cwd:              {os.getcwd()}")
print(f"   PROJECT_ROOT:     {PROJECT_ROOT}")
print(f"   CHORDS_DIR:       {CHORDS_DIR}")
print(f"   CHORDS_DIR exists: {CHORDS_DIR.exists()}")
print(f"   AUTH_JSON:        {AUTH_JSON}")
print(f"   AUTH_JSON exists: {AUTH_JSON.exists()}")
print("=" * 70)


# ============ ИМПОРТ API-КЛИЕНТА ============

try:
    from api.client import api
    from config.app_config import config
    API_IMPORT_OK = True
except Exception as e:
    print(f"❌ Не удалось импортировать api.client: {e}")
    print("   Убедись, что скрипт запускается из корня проекта.")
    sys.exit(1)


# ============ ЗАГРУЗКА ТОКЕНОВ ИЗ КОРНЯ ПРОЕКТА ============

def load_tokens_from_root() -> bool:
    """
    Читает auth.json из корня проекта и подставляет токены в api.client.
    Не зависит от os.getcwd() и от JsonStore.
    """
    if not AUTH_JSON.exists():
        print(f"❌ auth.json не найден: {AUTH_JSON}")
        return False

    try:
        with open(AUTH_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения auth.json: {e}")
        return False

    tokens = data.get("tokens") or {}
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")

    if not access:
        print("❌ В auth.json нет access_token")
        return False

    # Подставляем в api.client
    api.access_token = access
    api.refresh_token = refresh

    # Проверяем, не протух ли токен
    exp = _jwt_exp(access)
    if exp:
        now = int(time.time())
        if now >= exp:
            print(f"⚠️ access_token ПРОТУХ (exp={exp}, now={now}, "
                  f"просрочен на {(now - exp) // 60} мин)")
            print("   Пробуем обновить через refresh_token...")
            if api._refresh_access_token():
                print("✅ access_token обновлён")
            else:
                print("❌ Не удалось обновить токен")
                return False
        else:
            print(f"✅ access_token действителен ещё {(exp - now) // 60} мин")

    print(f"🔑 access_token:  {access[:30]}...")
    print(f"🔑 refresh_token: {(refresh or '')[:30]}...")

    return True


def _jwt_exp(token: str) -> Optional[int]:
    """Достаёт поле exp из JWT без верификации подписи."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        # Декодируем payload (base64url)
        import base64
        payload_b64 = parts[1]
        # Выравниваем padding
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("exp")
    except Exception:
        return None


# ============ ПАРСЕР ИМЕНИ ============

def parse_chord_name(raw_name: str) -> Dict:
    """
    Разбирает имя аккорда.

    'A!Amaj'              → main='A',        synonyms=['A','Amaj']
    'A9$Gsharp!A9$Ab'     → main='A9\\G#',    synonyms=['A9\\G#','A9\\Ab']
    'Caug!C+'             → main='Caug',      synonyms=['Caug','C+']
    'Asharp!Asharpmaj!Bb!Bbmaj' → main='A#', synonyms=['A#','A#maj','Bb','Bbmaj']
    """
    raw_synonyms = [s.strip() for s in raw_name.split("!") if s.strip()]

    synonyms = []
    for s in raw_synonyms:
        s = s.replace("$", "\\")
        s = re.sub(r"[Ss]harp", "#", s)
        synonyms.append(s)

    if not synonyms:
        return {
            "main": raw_name,
            "synonyms": [raw_name],
            "tonality": raw_name[:1] if raw_name else "",
            "type_suffix": "",
            "slash_note": None,
        }

    main = synonyms[0]

    m = re.match(r"^([A-H][#b]?)(.*)$", main)
    if m:
        tonality = m.group(1)
        rest = m.group(2)
    else:
        tonality = main[:1]
        rest = main[1:]

    if "\\" in rest:
        chord_part, slash_note = rest.split("\\", 1)
    else:
        chord_part, slash_note = rest, None

    return {
        "main": main,
        "synonyms": synonyms,
        "tonality": tonality,
        "type_suffix": chord_part.strip(),
        "slash_note": slash_note.strip() if slash_note else None,
    }


def parse_description(raw_desc: str) -> Tuple[str, List[str]]:
    """Разбивает описание по ! на список."""
    if not raw_desc:
        return "", []
    parts = [p.strip() for p in raw_desc.split("!") if p.strip()]
    unique = []
    for p in parts:
        if p not in unique:
            unique.append(p)
    return raw_desc, unique


# ============ ЗАГРУЗКА МОДУЛЯ ============

def load_chord_module(file_path: Path):
    """Импортирует .py-файл как модуль."""
    module_name = f"chords_upload_{file_path.stem}_{int(time.time() * 1000)}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Не удалось создать spec для {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ============ ИЗВЛЕЧЕНИЕ ДАННЫХ ============

def extract_chord_data(file_path: Path) -> Optional[Dict]:
    """Извлекает все поля из модуля аккорда."""
    try:
        module = load_chord_module(file_path)
    except Exception as e:
        print(f"  ❌ Ошибка импорта {file_path.name}: {e}")
        return None

    metadata = getattr(module, "METADATA", {})
    raw_name = metadata.get("name") or file_path.stem.split("_")[0]

    parsed = parse_chord_name(raw_name)

    variant = metadata.get("variant")
    if variant is None:
        m = re.search(r"_(\d+)$", file_path.stem)
        variant = int(m.group(1)) if m else 1

    chord_type = metadata.get("type", "")
    if "|" in chord_type:
        chord_type = chord_type.split("|")[0].strip()

    raw_desc = metadata.get("description", "")
    desc_full, desc_synonyms = parse_description(raw_desc)

    return {
        "main_name": parsed["main"],
        "synonyms": parsed["synonyms"],
        "tonality": parsed["tonality"],
        "slash_note": parsed["slash_note"],
        "chord_type": chord_type,
        "type_suffix": parsed["type_suffix"],
        "variant": int(variant),
        "description": desc_full,
        "description_synonyms": desc_synonyms,
        "background_name": getattr(module, "BACKGROUND_NAME", "griff"),
        "frets": getattr(module, "FRETS", {}) or {},
        "notes": getattr(module, "NOTES", {}) or {},
        "open_notes": getattr(module, "OPEN_NOTES", {}) or {},
        "barres": getattr(module, "BARRES", {}) or {},
        "selected_finger": getattr(module, "SELECTED_FINGER", []) or [],
        "selected_note": getattr(module, "SELECTED_NOTE", []) or [],
    }


# ============ ОБХОД ФАЙЛОВ ============

def find_all_chord_files(chords_dir: Path) -> List[Path]:
    """Все .py с аккордами, кроме __init__ и all_chords."""
    if not chords_dir.exists():
        raise FileNotFoundError(f"Папка не найдена: {chords_dir}")

    result = []
    for f in chords_dir.rglob("*.py"):
        if f.name in ("__init__.py", "all_chords.py"):
            continue
        result.append(f)
    return result


# ============ ОТПРАВКА НА СЕРВЕР ============

def upload_chord(chord: Dict) -> Tuple[bool, str]:
    """
    Отправляет POST /chords/{main}/{type}/{variant} через api.client.
    Возвращает (success, error_message).
    """
    main = chord["main_name"]
    ctype = chord["chord_type"]
    variant = chord["variant"]

    main_enc = urllib.parse.quote(main, safe="")
    ctype_enc = urllib.parse.quote(ctype, safe="")

    url = f"{config.API_BASE_URL}/chords/{main_enc}/{ctype_enc}/{variant}"

    result = api._request_sync(url, method="POST", data=chord, include_auth=True)

    if isinstance(result, dict) and result.get("error") == "unauthorized":
        return False, "unauthorized"

    if not result or (isinstance(result, dict) and result.get("status") != "ok"):
        return False, f"bad response: {str(result)[:120]}"

    return True, ""


# ============ MAIN ============

def main():
    print("=" * 70)
    print("📤 Загрузка аккордов на сервер GuitarFans")
    print(f"   API: {config.API_BASE_URL}")
    print("=" * 70)

    # 1) Загружаем токены из корня проекта
    if not load_tokens_from_root():
        print("❌ Не удалось загрузить токены. Положи auth.json в корень проекта.")
        return

    # 2) Находим файлы
    files = find_all_chord_files(CHORDS_DIR)
    print(f"\n📦 Найдено файлов: {len(files)}")

    if not files:
        print("❌ Нет файлов для загрузки")
        return

    # 3) Извлекаем данные
    print("\n⏳ Извлечение данных из модулей...")
    all_chords: List[Tuple[Path, Dict]] = []
    errors = 0

    for i, f in enumerate(files, 1):
        data = extract_chord_data(f)
        if data is None:
            errors += 1
            continue
        all_chords.append((f, data))
        if i % 200 == 0:
            print(f"   ... {i}/{len(files)}")

    print(f"✅ Извлечено: {len(all_chords)} аккордов (ошибок: {errors})")

    if not all_chords:
        return

    # 4) Примеры
    print("\n📋 Примеры (первые 3):")
    for f, data in all_chords[:3]:
        print(f"   {f.name}")
        print(f"     → {data['main_name']} | {data['chord_type']} | v{data['variant']}")
        print(f"     synonyms={data['synonyms']}, tonality={data['tonality']}, "
              f"slash={data['slash_note']}, suffix='{data['type_suffix']}'")

    # 5) Загружаем
    print(f"\n🚀 Загрузка...")
    uploaded = 0
    failed = 0
    unauthorized = False
    failed_files = []

    start_time = time.time()

    for i, (f, data) in enumerate(all_chords, 1):
        ok, err = upload_chord(data)

        if ok:
            uploaded += 1
        else:
            failed += 1
            failed_files.append((f.name, err))
            if err == "unauthorized":
                unauthorized = True
                break

        if i % 50 == 0:
            elapsed = time.time() - start_time
            speed = i / elapsed if elapsed > 0 else 0
            eta = (len(all_chords) - i) / speed if speed > 0 else 0
            print(f"   ... {i}/{len(all_chords)}  "
                  f"(✅ {uploaded} ❌ {failed})  "
                  f"[{speed:.1f}/сек, ETA {int(eta)}с]")

    elapsed = time.time() - start_time

    # 6) Итог
    print("\n" + "=" * 70)
    print(f"✅ Загружено: {uploaded}/{len(all_chords)}")
    print(f"❌ Ошибок:   {failed}")
    print(f"⏱️ Время:    {int(elapsed)} сек")

    if unauthorized:
        print("\n🔑 Токен протух и не удалось обновить. Залогинься заново.")
    elif failed_files:
        print("\n⚠️ Первые 10 ошибок:")
        for name, err in failed_files[:10]:
            print(f"   - {name}: {err}")

    print("=" * 70)


if __name__ == "__main__":
    main()