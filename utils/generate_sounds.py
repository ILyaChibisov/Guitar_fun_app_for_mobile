# utils/generate_sounds.py
import os
import sys
import math
import array
import time
import random
import base64  # <--- ДОБАВЛЕНА ЭТА СТРОКА
from pathlib import Path
from typing import Dict, List

# Пробуем импортировать soundfile
try:
    import soundfile as sf
    import numpy as np
    HAS_SOUNDFILE = False
except ImportError:
    HAS_SOUNDFILE = False
    print("⚠️ soundfile не установлен! OGG не будет работать. Установите: pip install soundfile numpy")
    print("   Звуки будут сохранены в WAV (файлы будут большими).")

SAMPLE_RATE = 44100
MAX_AMPLITUDE = 32767



def get_project_root() -> Path:
    current = Path(__file__).resolve().parent
    parent = current.parent
    if (parent / "main.py").exists() or (parent / "assets").exists():
        return parent
    return Path.cwd()


PROJECT_ROOT = get_project_root()

# ============ СТРОИ ============
TUNINGS = {
    'standard': {
        'name': 'Стандартный',
        'notes': [
            {'string': 6, 'note': 'E2', 'freq': 82.41, 'type': 'bass', 'volume': 0.75},
            {'string': 5, 'note': 'A2', 'freq': 110.00, 'type': 'bass', 'volume': 0.70},
            {'string': 4, 'note': 'D3', 'freq': 146.83, 'type': 'mid', 'volume': 0.65},
            {'string': 3, 'note': 'G3', 'freq': 196.00, 'type': 'mid', 'volume': 0.60},
            {'string': 2, 'note': 'B3', 'freq': 246.94, 'type': 'treble', 'volume': 0.55},
            {'string': 1, 'note': 'E4', 'freq': 329.63, 'type': 'treble', 'volume': 0.50},
        ]
    },
    'drop_d': {
        'name': 'Drop D',
        'notes': [
            {'string': 6, 'note': 'D2', 'freq': 73.42, 'type': 'bass', 'volume': 0.75},
            {'string': 5, 'note': 'A2', 'freq': 110.00, 'type': 'bass', 'volume': 0.70},
            {'string': 4, 'note': 'D3', 'freq': 146.83, 'type': 'mid', 'volume': 0.65},
            {'string': 3, 'note': 'G3', 'freq': 196.00, 'type': 'mid', 'volume': 0.60},
            {'string': 2, 'note': 'B3', 'freq': 246.94, 'type': 'treble', 'volume': 0.55},
            {'string': 1, 'note': 'E4', 'freq': 329.63, 'type': 'treble', 'volume': 0.50},
        ]
    },
    'half_step_down': {
        'name': 'Half Step Down',
        'notes': [
            {'string': 6, 'note': 'Eb2', 'freq': 77.78, 'type': 'bass', 'volume': 0.75},
            {'string': 5, 'note': 'Ab2', 'freq': 103.83, 'type': 'bass', 'volume': 0.70},
            {'string': 4, 'note': 'Db3', 'freq': 138.59, 'type': 'mid', 'volume': 0.65},
            {'string': 3, 'note': 'Gb3', 'freq': 185.00, 'type': 'mid', 'volume': 0.60},
            {'string': 2, 'note': 'Bb3', 'freq': 233.08, 'type': 'treble', 'volume': 0.55},
            {'string': 1, 'note': 'Eb4', 'freq': 311.13, 'type': 'treble', 'volume': 0.50},
        ]
    },
    'bass_4': {
        'name': 'Бас 4-струнный',
        'notes': [
            {'string': 4, 'note': 'E1', 'freq': 41.20, 'type': 'bass', 'volume': 0.85},
            {'string': 3, 'note': 'A1', 'freq': 55.00, 'type': 'bass', 'volume': 0.80},
            {'string': 2, 'note': 'D2', 'freq': 73.42, 'type': 'bass', 'volume': 0.75},
            {'string': 1, 'note': 'G2', 'freq': 98.00, 'type': 'bass', 'volume': 0.70},
        ]
    },
    'bass_5': {
        'name': 'Бас 5-струнный',
        'notes': [
            {'string': 5, 'note': 'B0', 'freq': 30.87, 'type': 'bass', 'volume': 0.90},
            {'string': 4, 'note': 'E1', 'freq': 41.20, 'type': 'bass', 'volume': 0.85},
            {'string': 3, 'note': 'A1', 'freq': 55.00, 'type': 'bass', 'volume': 0.80},
            {'string': 2, 'note': 'D2', 'freq': 73.42, 'type': 'bass', 'volume': 0.75},
            {'string': 1, 'note': 'G2', 'freq': 98.00, 'type': 'bass', 'volume': 0.70},
        ]
    },
    'ukulele': {
        'name': 'Укулеле',
        'notes': [
            {'string': 4, 'note': 'G4', 'freq': 392.00, 'type': 'treble', 'volume': 0.55},
            {'string': 3, 'note': 'C4', 'freq': 261.63, 'type': 'treble', 'volume': 0.55},
            {'string': 2, 'note': 'E4', 'freq': 329.63, 'type': 'treble', 'volume': 0.55},
            {'string': 1, 'note': 'A4', 'freq': 440.00, 'type': 'treble', 'volume': 0.50},
        ]
    },
    'open_g': {
        'name': 'Open G',
        'notes': [
            {'string': 6, 'note': 'D2', 'freq': 73.42, 'type': 'bass', 'volume': 0.75},
            {'string': 5, 'note': 'G2', 'freq': 98.00, 'type': 'bass', 'volume': 0.70},
            {'string': 4, 'note': 'D3', 'freq': 146.83, 'type': 'mid', 'volume': 0.65},
            {'string': 3, 'note': 'G3', 'freq': 196.00, 'type': 'mid', 'volume': 0.60},
            {'string': 2, 'note': 'B3', 'freq': 246.94, 'type': 'treble', 'volume': 0.55},
            {'string': 1, 'note': 'D4', 'freq': 293.66, 'type': 'treble', 'volume': 0.50},
        ]
    },
    'open_d': {
        'name': 'Open D',
        'notes': [
            {'string': 6, 'note': 'D2', 'freq': 73.42, 'type': 'bass', 'volume': 0.75},
            {'string': 5, 'note': 'A2', 'freq': 110.00, 'type': 'bass', 'volume': 0.70},
            {'string': 4, 'note': 'D3', 'freq': 146.83, 'type': 'mid', 'volume': 0.65},
            {'string': 3, 'note': 'F#3', 'freq': 185.00, 'type': 'mid', 'volume': 0.60},
            {'string': 2, 'note': 'A3', 'freq': 220.00, 'type': 'treble', 'volume': 0.55},
            {'string': 1, 'note': 'D4', 'freq': 293.66, 'type': 'treble', 'volume': 0.50},
        ]
    },
    'dadgad': {
        'name': 'DADGAD',
        'notes': [
            {'string': 6, 'note': 'D2', 'freq': 73.42, 'type': 'bass', 'volume': 0.75},
            {'string': 5, 'note': 'A2', 'freq': 110.00, 'type': 'bass', 'volume': 0.70},
            {'string': 4, 'note': 'D3', 'freq': 146.83, 'type': 'mid', 'volume': 0.65},
            {'string': 3, 'note': 'G3', 'freq': 196.00, 'type': 'mid', 'volume': 0.60},
            {'string': 2, 'note': 'A3', 'freq': 220.00, 'type': 'treble', 'volume': 0.55},
            {'string': 1, 'note': 'D4', 'freq': 293.66, 'type': 'treble', 'volume': 0.50},
        ]
    }
}


def generate_realistic_string_sound(
        frequency: float,
        duration: float = 2.5,
        volume: float = 0.7,
        string_type: str = 'mid'
) -> array.array:
    """
    Чистый алгоритм Карплуса — Стронга (классическая модель струны без перегруза).
    """
    num_samples = int(SAMPLE_RATE * duration)
    rng = random.Random(123)

    # Коэффициент затухания (чем ближе к 1.0, тем дольше тянется нота)
    # Высокие частоты затухают быстрее низких естественным образом за счет усреднения 0.5*(a+b)
    if string_type == 'bass':
        decay = 0.9985
        smooth_passes = 3   # Мягкий щипок для толстых струн
    elif string_type == 'treble':
        decay = 0.9965
        smooth_passes = 1   # Звонкий щипок для тонких струн
    else:  # mid
        decay = 0.9978
        smooth_passes = 2

    # Длина буфера равна периоду основной частоты
    period = SAMPLE_RATE / frequency
    buf_len = max(2, int(round(period)))

    # 1. Генерируем начальный импульс (треугольный шум — звучит намного мягче белого)
    ring_buffer = [(rng.random() + rng.random() - 1.0) for _ in range(buf_len)]

    # Мягкое сглаживание начального импульса (имитация подушечки пальца/медиатора)
    for _ in range(smooth_passes):
        new_buf = [0.0] * buf_len
        for i in range(buf_len):
            new_buf[i] = 0.25 * ring_buffer[(i - 1) % buf_len] + 0.5 * ring_buffer[i] + 0.25 * ring_buffer[(i + 1) % buf_len]
        ring_buffer = new_buf

    # Убираем постоянную составляющую (DC offset)
    mean_val = sum(ring_buffer) / buf_len
    ring_buffer = [x - mean_val for x in ring_buffer]

    # Нормализуем строго в диапазон [-1.0, 1.0]
    max_val = max(abs(x) for x in ring_buffer) or 1.0
    ring_buffer = [x / max_val for x in ring_buffer]

    # 2. Основной цикл волновода (строго по классической формуле Карплуса — Стронга)
    audio_data = array.array('h')
    idx = 0
    attack_samples = int(SAMPLE_RATE * 0.008)      # 8 мс плавный вход
    fade_out_samples = int(SAMPLE_RATE * 0.3)      # 300 мс плавное затухание в конце

    for i in range(num_samples):
        curr_s = ring_buffer[idx]
        next_idx = (idx + 1) % buf_len
        next_s = ring_buffer[next_idx]

        # Классический фильтр усреднения (0.5 * (curr + next)) * decay
        # Именно он дает естественный тембр гитарной струны без синтетики
        new_sample = 0.5 * (curr_s + next_s) * decay
        ring_buffer[idx] = new_sample
        idx = next_idx

        out_val = curr_s

        # Плавная атака, чтобы убрать щелчок в самом начале
        if i < attack_samples:
            out_val *= (i / attack_samples)

        # Плавное затухание в конце файла
        if i > num_samples - fade_out_samples:
            out_val *= max(0.0, (num_samples - i) / fade_out_samples)

        # Чистое масштабирование громкости без клиппинга
        int_value = int(MAX_AMPLITUDE * out_val * volume)
        int_value = max(-32768, min(32767, int_value))
        audio_data.append(int_value)

    return audio_data




def save_wav(audio_data, filename):
    try:
        with open(filename, 'wb') as f:
            f.write(b'RIFF')
            f.write((36 + len(audio_data) * 2).to_bytes(4, 'little'))
            f.write(b'WAVEfmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))
            f.write((1).to_bytes(2, 'little'))
            f.write(SAMPLE_RATE.to_bytes(4, 'little'))
            f.write((SAMPLE_RATE * 2).to_bytes(4, 'little'))
            f.write((2).to_bytes(2, 'little'))
            f.write((16).to_bytes(2, 'little'))
            f.write(b'data')
            f.write((len(audio_data) * 2).to_bytes(4, 'little'))
            audio_data.tofile(f)
        return True
    except Exception as e:
        print(f"❌ Ошибка WAV: {e}")
        return False


# 3. Замена функции generate_python_module (исправлено имя класса и безопасное удаление файла)
def generate_python_module(tuning_id, tuning_name, notes_data, output_path):
    """Генерирует Python-модуль с base64 данными звуков."""
    lines = [
        "# -*- coding: utf-8 -*-",
        '"""',
        f"Звуковые ассеты для строя: {tuning_name}",
        f"Количество нот: {len(notes_data)}",
        '"""',
        "",
        "import base64",
        "from typing import Optional",
        "import tempfile",
        "import os",
        "",
        "try:",
        "    from kivy.core.audio import SoundLoader",
        "    from kivy.clock import Clock",
        "    KIVY_AVAILABLE = True",
        "except ImportError:",
        "    KIVY_AVAILABLE = False",
        "",
    ]

    metadata_lines = []
    note_map = {}

    for note_info in notes_data:
        note_name = note_info['note']
        safe_name = note_name.replace('#', '_SHARP_').replace(' ', '_')
        note_map[note_name] = safe_name

        filename = f"{safe_name}.wav"
        filepath = output_path / filename

        audio = generate_realistic_string_sound(
            frequency=note_info['freq'],
            duration=2.5,
            volume=note_info['volume'],
            string_type=note_info['type']
        )

        save_wav(audio, str(filepath))
        file_size = os.path.getsize(filepath)

        with open(filepath, 'rb') as f:
            b64_data = base64.b64encode(f.read()).decode('utf-8')

        os.remove(filepath)

        lines.append(f"# {note_name} -> {filename}")
        lines.append(f'_{safe_name}_BASE64 = """{b64_data}"""')
        lines.append("")

        metadata_lines.append(f'    "{note_name}": {{')
        metadata_lines.append(f'        "filename": "{filename}",')
        metadata_lines.append(f'        "size": {file_size},')
        metadata_lines.append(f'        "duration": 2.500,')
        metadata_lines.append(f'        "sample_rate": 44100,')
        metadata_lines.append(f'        "channels": 1,')
        metadata_lines.append(f'        "compressed": False,')
        metadata_lines.append(f'    }},')
        metadata_lines.append("")

        print(f"   ✅ {note_name} ({note_info['freq']} Hz) - {file_size / 1024:.1f} KB")

    lines.append("NOTES_METADATA = {")
    lines.extend(metadata_lines)
    lines.append("}")
    lines.append("")

    # Формируем строго английское имя класса из tuning_id (например, bass_4 -> Bass4Sounds)
    class_name = tuning_id.title().replace('_', '') + 'Sounds'

    lines.extend([
        f"class {class_name}:",
        f'    """Звуки для строя: {tuning_name}"""',
        "",
        "    _NOTE_NAME_MAP = {",
    ])
    for orig, safe in note_map.items():
        lines.append(f'        "{orig}": "{safe}",')
    lines.extend([
        "    }",
        "",
        "    @staticmethod",
        "    def get_sound_data(note_name: str) -> Optional[bytes]:",
        f"        safe_name = {class_name}._NOTE_NAME_MAP.get(note_name)",
        "        if safe_name:",
        '            var_name = f"_{safe_name}_BASE64"',
        "            if var_name in globals():",
        "                return base64.b64decode(globals()[var_name])",
        "        return None",
        "",
        "    @staticmethod",
        "    def get_sound(note_name: str):",
        "        if not KIVY_AVAILABLE:",
        "            return None",
        f"        data = {class_name}.get_sound_data(note_name)",
        "        if data:",
        "            try:",
        '                fd, path = tempfile.mkstemp(suffix=".wav")',
        "                os.close(fd)",
        '                with open(path, "wb") as f:',
        "                    f.write(data)",
        "                sound = SoundLoader.load(path)",
        "                # Отложенное удаление, чтобы Windows и Android успели прочитать файл",
        "                def _cleanup(dt):",
        "                    try:",
        "                        if os.path.exists(path):",
        "                            os.unlink(path)",
        "                    except Exception:",
        "                        pass",
        "                Clock.schedule_once(_cleanup, 5.0)",
        "                return sound",
        "            except Exception:",
        "                return None",
        "        return None",
        "",
        "    @staticmethod",
        "    def get_all_notes() -> list:",
        "        return list(NOTES_METADATA.keys())",
        "",
        f'TUNING_NAME = "{tuning_name}"',
        f'TUNING_ID = "{tuning_id}"',
        f'__all__ = ["{class_name}", "NOTES_METADATA"]',
    ])

    with open(output_path / f"{tuning_id}.py", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))



def generate_all_sounds():
    base_dir = PROJECT_ROOT / "data" / "sounds"
    base_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎸 ГЕНЕРАЦИЯ РЕАЛИСТИЧНЫХ ЗВУКОВ")
    print(f"📁 Папка: {base_dir}")
    if HAS_SOUNDFILE:
        print("✅ OGG (сжатие включено)")
    else:
        print("⚠️ WAV (сжатие ВЫКЛЮЧЕНО)")
    print("=" * 60)

    # Генерируем __init__.py
    init_lines = ['"""Пакет звуковых ассетов"""', ""]
    init_lines.append("from .standard import StandardSounds")
    init_lines.append("from .drop_d import DropDSounds")
    init_lines.append("from .half_step_down import HalfStepDownSounds")
    init_lines.append("from .bass_4 import Bass4Sounds")
    init_lines.append("from .bass_5 import Bass5Sounds")
    init_lines.append("from .ukulele import UkuleleSounds")
    init_lines.append("from .open_g import OpenGSounds")
    init_lines.append("from .open_d import OpenDSounds")
    init_lines.append("from .dadgad import DadgadSounds")
    with open(base_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write("\n".join(init_lines))

    for tuning_id, tuning_data in TUNINGS.items():
        print(f"\n📁 {tuning_data['name']} ({tuning_id})")
        print("-" * 40)
        generate_python_module(tuning_id, tuning_data['name'], tuning_data['notes'], base_dir)

    print("\n" + "=" * 60)
    print("✅ ВСЁ ГОТОВО! Перезапустите приложение.")
    print("=" * 60)


if __name__ == '__main__':
    generate_all_sounds()