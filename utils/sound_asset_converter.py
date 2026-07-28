# utils/sound_asset_converter.py (ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ)

"""
Конвертер звуковых ассетов в Python-модули с base64
Поддерживает WAV и OGG
Читает из: assets/sounds/
Сохраняет в: data/sounds/
"""
import os
import base64
import wave
import struct
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime
import sys
import re


# ============ НАХОДИМ КОРЕНЬ ПРОЕКТА ============
def get_project_root() -> Path:
    current = Path(__file__).resolve().parent
    parent = current.parent
    if (parent / "main.py").exists() or (parent / "assets").exists():
        return parent
    for candidate in [current] + list(current.parents):
        if (candidate / "main.py").exists():
            return candidate
        if (candidate / "assets").exists():
            return candidate
    return Path.cwd()


PROJECT_ROOT = get_project_root()
print(f"📁 Корень проекта: {PROJECT_ROOT}")

# Пробуем импортировать soundfile для чтения OGG
try:
    import soundfile as sf

    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False
    print("⚠️ soundfile не установлен, OGG чтение недоступно")
    print("   Установите: pip install soundfile")


def safe_var_name(name: str) -> str:
    """Преобразует имя ноты в безопасное имя переменной Python"""
    replacements = {
        '#': '_SHARP_',
        'b': '_FLAT_',
        '♯': '_SHARP_',
        '♭': '_FLAT_',
        '+': '_PLUS_',
        '-': '_MINUS_',
        '/': '_SLASH_',
        '\\': '_BACKSLASH_',
    }
    result = name
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    result = re.sub(r'_+', '_', result)
    result = result.strip('_')
    if result and result[0].isdigit():
        result = f"NOTE_{result}"
    return result


class SoundAssetConverter:
    """Конвертирует WAV/OGG файлы в Python модули"""

    SUPPORTED_EXTENSIONS = {'.wav', '.ogg'}

    def __init__(self, assets_dir: str = "assets/sounds", output_dir: str = "data/sounds"):
        self.assets_dir = PROJECT_ROOT / assets_dir
        self.output_dir = PROJECT_ROOT / output_dir
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.converted_count = 0
        self.errors = []

    def _ensure_output_dir(self):
        """Создаёт папку data/sounds и __init__.py"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        init_file = self.output_dir / "__init__.py"
        if not init_file.exists():
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('"""\nПакет звуковых ассетов\nСодержит сконвертированные звуки для всех строев\n"""\n\n')
                f.write('# Автоматически импортируем все модули строев\n')
                f.write('from .standard import StandardSounds\n')
                f.write('from .drop_d import DropDSounds\n')
                f.write('from .bass_4 import Bass4Sounds\n')
                f.write('from .bass_5 import Bass5Sounds\n')
                f.write('from .ukulele import UkuleleSounds\n')
                f.write('from .open_g import OpenGSounds\n')
                f.write('from .open_d import OpenDSounds\n')
                f.write('from .dadgad import DADGADSounds\n\n')
                f.write('__all__ = [\n')
                f.write('    "StandardSounds", "DropDSounds", "Bass4Sounds",\n')
                f.write('    "Bass5Sounds", "UkuleleSounds", "OpenGSounds",\n')
                f.write('    "OpenDSounds", "DADGADSounds"\n')
                f.write(']\n')
            print(f"📦 Создан файл: {self.output_dir}/__init__.py")

    def read_audio_file(self, file_path: Path) -> Tuple[bytes, Dict]:
        """Читает аудио файл (WAV или OGG)"""
        ext = file_path.suffix.lower()

        if ext == '.ogg':
            with open(file_path, 'rb') as f:
                data = f.read()
            duration = 2.5
            sample_rate = 44100
            channels = 1
            if HAS_SOUNDFILE:
                try:
                    info = sf.info(str(file_path))
                    duration = info.duration
                    sample_rate = info.samplerate
                    channels = info.channels
                except:
                    pass
            return data, {
                'sample_rate': sample_rate,
                'channels': channels,
                'sampwidth': 2,
                'nframes': int(sample_rate * duration),
                'is_compressed': True,
                'compressed_format': 'ogg'
            }

        elif ext == '.wav':
            with wave.open(str(file_path), 'rb') as wav:
                params = wav.getparams()
                frames = wav.readframes(params.nframes)
                return frames, {
                    'sample_rate': params.framerate,
                    'channels': params.nchannels,
                    'sampwidth': params.sampwidth,
                    'nframes': params.nframes,
                    'is_compressed': False,
                    'compressed_format': None
                }

        else:
            raise ValueError(f"Неподдерживаемый формат: {ext}")

    def scan_sounds(self) -> Dict[str, Dict]:
        """Сканирует папку со звуками"""
        sounds = {}

        if not self.assets_dir.exists():
            print(f"❌ Папка {self.assets_dir} не найдена!")
            print(f"📌 Сначала создайте звуки: python utils/generate_sounds.py")
            return sounds

        tuning_dirs = [d for d in self.assets_dir.iterdir() if d.is_dir()]

        if not tuning_dirs:
            print(f"⚠️ В папке {self.assets_dir} нет подпапок со строями")
            return sounds

        print("\n📸 Найденные звуковые файлы:")

        for tuning_dir in sorted(tuning_dirs):
            tuning_name = tuning_dir.name
            sounds[tuning_name] = {}

            audio_files = []
            for ext in ['.wav', '.ogg']:
                audio_files.extend(list(tuning_dir.glob(f"*{ext}")))

            if not audio_files:
                print(f"   ⚠️ {tuning_name}: нет звуковых файлов")
                continue

            for audio_path in sorted(audio_files):
                note_name = audio_path.stem

                try:
                    data, info = self.read_audio_file(audio_path)

                    duration = info.get('duration', 2.5)
                    is_compressed = info.get('is_compressed', False)
                    compressed_format = info.get('compressed_format', None)

                    b64_data = base64.b64encode(data).decode('ascii')
                    ext = audio_path.suffix[1:]
                    safe_note_name = safe_var_name(note_name)

                    sounds[tuning_name][safe_note_name] = {
                        'name': note_name,
                        'safe_name': safe_note_name,
                        'filename': audio_path.name,
                        'size': len(data),
                        'duration': duration,
                        'sample_rate': info['sample_rate'],
                        'channels': info['channels'],
                        'base64': b64_data,
                        'extension': ext,
                        'compressed': is_compressed,
                        'compressed_format': compressed_format,
                    }

                    self.converted_count += 1
                    size_kb = len(data) / 1024
                    comp = "🔊" if is_compressed else "📀"
                    comp_label = f" ({compressed_format.upper()})" if is_compressed else " (WAV)"
                    print(f"   {comp} {tuning_name}/{note_name} ({size_kb:.1f} KB{comp_label}, {duration:.2f}s)")

                except Exception as e:
                    self.errors.append(f"{tuning_name}/{note_name}: {e}")
                    print(f"   ❌ {tuning_name}/{note_name}: {e}")

        return sounds

    def generate_module(self, tuning_name: str, notes: Dict, tuning_display_name: str = None) -> str:
        """Генерирует Python модуль с безопасными именами переменных"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not tuning_display_name:
            tuning_display_name = tuning_name.replace('_', ' ').title()

        class_name = tuning_name.title().replace('_', '') + 'Sounds'

        lines = [
            '# -*- coding: utf-8 -*-',
            '"""',
            f'Звуковые ассеты для строя: {tuning_display_name}',
            f'Создан: {timestamp}',
            f'Количество нот: {len(notes)}',
            '',
            'Использование:',
            f'    from data.sounds.{tuning_name} import {class_name}',
            '    sounds = SoundClass()',
            '    sound_data = sounds.get_sound("E2")',
            '"""',
            '',
            'import base64',
            'from typing import Optional, Dict',
            'from io import BytesIO',
            'import tempfile',
            'import os',
            '',
            'try:',
            '    from kivy.core.audio import SoundLoader',
            '    KIVY_AVAILABLE = True',
            'except ImportError:',
            '    KIVY_AVAILABLE = False',
            '',
            '',
            '# ============ БИНАРНЫЕ ДАННЫЕ ЗВУКОВ ============',
            '',
        ]

        for safe_name, note_data in notes.items():
            original_name = note_data['name']
            size_kb = note_data['size'] / 1024
            ext = note_data['extension'].upper()
            compressed = note_data.get('compressed', False)
            comp_label = " (сжатый OGG)" if compressed else " (WAV)"
            lines.append(f'# {original_name} -> {note_data["filename"]} ({size_kb:.1f} KB{comp_label})')
            lines.append(f'_{safe_name}_BASE64 = """{note_data["base64"]}"""')
            lines.append(f'_{safe_name}_DURATION = {note_data["duration"]:.3f}')
            lines.append(f'_{safe_name}_SAMPLE_RATE = {note_data["sample_rate"]}')
            lines.append(f'_{safe_name}_COMPRESSED = {str(note_data.get("compressed", False))}')
            lines.append('')

        lines.extend([
            '',
            '# ============ МАППИНГ ИМЁН ============',
            '',
            '_NOTE_NAME_MAP = {',
        ])

        for safe_name, note_data in notes.items():
            original_name = note_data['name']
            lines.append(f'    "{original_name}": "{safe_name}",')

        lines.append('}')
        lines.append('')

        lines.extend([
            '',
            '# ============ МЕТАДАННЫЕ ============',
            '',
            'NOTES_METADATA = {',
        ])

        for safe_name, note_data in notes.items():
            original_name = note_data['name']
            lines.append(f'    "{original_name}": {{')
            lines.append(f'        "filename": "{note_data["filename"]}",')
            lines.append(f'        "size": {note_data["size"]},')
            lines.append(f'        "duration": {note_data["duration"]:.3f},')
            lines.append(f'        "sample_rate": {note_data["sample_rate"]},')
            lines.append(f'        "channels": {note_data["channels"]},')
            lines.append(f'        "compressed": {note_data.get("compressed", False)},')
            if note_data.get('compressed_format'):
                lines.append(f'        "compressed_format": "{note_data["compressed_format"]}",')
            lines.append('    },')

        lines.append('}')
        lines.append('')

        # Генерируем класс - ИСПОЛЬЗУЕМ ПРЯМУЮ ПОДСТАНОВКУ class_name
        lines.extend([
            '',
            f'class {class_name}:',
            f'    """Звуки для строя: {tuning_display_name}"""',
            '    ',
            '    @staticmethod',
            '    def _get_safe_name(note_name: str) -> Optional[str]:',
            '        """Преобразует оригинальное имя ноты в безопасное имя переменной"""',
            '        return _NOTE_NAME_MAP.get(note_name)',
            '    ',
            '    @staticmethod',
            '    def get_sound_data(note_name: str) -> Optional[bytes]:',
            '        """Возвращает бинарные данные звука (может быть сжатым OGG)"""',
            f'        safe_name = {class_name}._get_safe_name(note_name)',
            '        if safe_name:',
            '            var_name = f"_{safe_name}_BASE64"',
            '            if var_name in globals():',
            '                return base64.b64decode(globals()[var_name])',
            '        return None',
            '    ',
            '    @staticmethod',
            '    def get_sound(note_name: str):',
            '        """Возвращает Kivy Sound объект для воспроизведения"""',
            '        if not KIVY_AVAILABLE:',
            '            return None',
            f'        data = {class_name}.get_sound_data(note_name)',
            '        if data:',
            '            sound = SoundLoader.load(BytesIO(data))',
            '            if sound:',
            '                return sound',
            '            try:',
            '                fd, path = tempfile.mkstemp(suffix=".ogg")',
            '                os.close(fd)',
            '                with open(path, "wb") as f:',
            '                    f.write(data)',
            '                sound = SoundLoader.load(path)',
            '                try:',
            '                    os.unlink(path)',
            '                except:',
            '                    pass',
            '                return sound',
            '            except:',
            '                return None',
            '        return None',
            '    ',
            '    @staticmethod',
            '    def get_all_notes() -> list:',
            '        """Возвращает список всех доступных нот"""',
            '        return list(NOTES_METADATA.keys())',
            '    ',
            '    @staticmethod',
            '    def get_metadata(note_name: str) -> Optional[dict]:',
            '        """Возвращает метаданные ноты"""',
            '        return NOTES_METADATA.get(note_name)',
            '    ',
            '    @staticmethod',
            '    def get_all_metadata() -> Dict:',
            '        """Возвращает метаданные всех нот"""',
            '        return NOTES_METADATA',
            '',
        ])

        lines.extend([
            '',
            '# ============ КОНСТАНТЫ ДЛЯ УДОБСТВА ============',
            '',
            f'TUNING_NAME = "{tuning_display_name}"',
            f'TUNING_ID = "{tuning_name}"',
            '',
        ])

        lines.append(f'__all__ = ["{class_name}", "NOTES_METADATA", "TUNING_NAME", "TUNING_ID"]')
        lines.append('')

        return '\n'.join(lines)

    def convert(self) -> bool:
        """Выполняет конвертацию"""
        print("=" * 60)
        print("🎵 КОНВЕРТЕР ЗВУКОВЫХ АССЕТОВ")
        print("=" * 60)
        print(f"📁 Читаем из: {self.assets_dir}")
        print(f"📦 Сохраняем в: {self.output_dir}")
        print("=" * 60)

        try:
            self._ensure_output_dir()
            sounds = self.scan_sounds()

            if not sounds:
                print(f"\n⚠️ Не найдено звуков в {self.assets_dir}")
                print(f"\n📌 Решение:")
                print(f"   1. Запусти генератор: python utils/generate_sounds.py")
                print(f"   2. Выбери опцию 1 (OGG)")
                print(f"   3. Затем запусти этот скрипт снова")
                return False

            for tuning_name, notes in sounds.items():
                if not notes:
                    continue

                display_name = tuning_name.replace('_', ' ').title()
                content = self.generate_module(tuning_name, notes, display_name)

                # УДАЛЯЕМ СТАРЫЙ ФАЙЛ если есть
                output_file = self.output_dir / f"{tuning_name}.py"
                if output_file.exists():
                    output_file.unlink()

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"✅ Создан модуль: {output_file}")

            self._update_init(sounds.keys())

            total_size = sum(
                sum(n['size'] for n in notes.values())
                for notes in sounds.values()
            )

            print("\n" + "=" * 60)
            print("✅ КОНВЕРТАЦИЯ ЗАВЕРШЕНА!")
            print(f"   🎵 Ассетов: {self.converted_count}")
            print(f"   📁 Строев: {len(sounds)}")
            print(f"   💾 Общий размер: {total_size / 1024:.2f} KB")

            has_ogg = any(
                n.get('compressed', False)
                for notes in sounds.values()
                for n in notes.values()
            )
            if has_ogg:
                print("   🎯 Используется OGG сжатие (экономия ~90% места!)")
            else:
                print("   📀 Используется WAV формат (без сжатия)")

            print(f"   📁 Выходная папка: {self.output_dir.absolute()}")
            print("=" * 60)

            if self.errors:
                print("\n⚠️ Ошибки:")
                for error in self.errors:
                    print(f"   ❌ {error}")

            return True

        except Exception as e:
            print(f"❌ Ошибка конвертации: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _update_init(self, tuning_names):
        """Обновляет __init__.py"""
        init_file = self.output_dir / "__init__.py"

        imports = []
        all_names = []

        for name in sorted(tuning_names):
            class_name = name.title().replace('_', '') + 'Sounds'
            imports.append(f'from .{name} import {class_name}')
            all_names.append(f'    "{class_name}",')

        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('"""\nПакет звуковых ассетов\nСодержит сконвертированные звуки для всех строев\n"""\n\n')
            for imp in imports:
                f.write(f'{imp}\n')
            f.write('\n')
            f.write('__all__ = [\n')
            for name in all_names:
                f.write(f'    {name}\n')
            f.write(']\n')


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Конвертер звуковых ассетов")
    parser.add_argument("--assets-dir", default="assets/sounds", help="Папка с исходными звуками")
    parser.add_argument("--output-dir", default="data/sounds", help="Выходная папка")

    args = parser.parse_args()

    converter = SoundAssetConverter(
        assets_dir=args.assets_dir,
        output_dir=args.output_dir
    )

    success = converter.convert()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())