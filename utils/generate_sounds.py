# utils/generate_sounds.py (исправленный)
"""
Генератор реалистичных звуков гитарных струн для ассетов
Создает WAV и OGG файлы с высоким качеством и натуральным звучанием
"""
import os
import sys
import math
import array
import struct
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ============ НАСТРОЙКИ ============
SAMPLE_RATE = 44100
BITS_PER_SAMPLE = 16
MAX_AMPLITUDE = 32767

# Пробуем импортировать PySoundFile для OGG
try:
    import soundfile as sf

    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False
    print("⚠️ soundfile не установлен, OGG сжатие недоступно")
    print("   Установите: pip install soundfile")


# ============ НАХОДИМ КОРЕНЬ ПРОЕКТА ============
def get_project_root() -> Path:
    """Находит корень проекта (где находится main.py)"""
    current = Path(__file__).resolve().parent  # это /путь/к/проекту/utils

    # Проверяем родительскую папку (корень проекта)
    parent = current.parent
    if (parent / "main.py").exists() or (parent / "assets").exists():
        return parent

    # Если нет, поднимаемся выше
    for candidate in [current] + list(current.parents):
        if (candidate / "main.py").exists():
            return candidate
        if (candidate / "assets").exists():
            return candidate

    # Если не нашли, возвращаем текущую директорию
    return Path.cwd()


PROJECT_ROOT = get_project_root()
print(f"📁 Корень проекта: {PROJECT_ROOT}")

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


def clamp_value(value, min_val=-1.0, max_val=1.0):
    """Ограничивает значение в диапазоне"""
    return max(min_val, min(max_val, value))


def generate_realistic_string_sound(
        frequency: float,
        duration: float = 2.5,
        volume: float = 0.7,
        string_type: str = 'mid',
        add_harmonics: bool = True,
        add_modulation: bool = True,
        add_attack_noise: bool = True,
        add_reverb: bool = True
) -> array.array:
    """
    Генерирует РЕАЛИСТИЧНЫЙ звук гитарной струны

    Особенности:
    - Богатый спектр с гармониками
    - Естественная модуляция (вибрато)
    - Реалистичная атака со щипком
    - Плавное затухание
    - Легкая реверберация
    """
    num_samples = int(SAMPLE_RATE * duration)

    # ===== 1. НАСТРОЙКИ ДЛЯ РАЗНЫХ ТИПОВ СТРУН =====
    if string_type == 'bass':
        harmonics = [
            (1, 1.0), (2, 0.85), (3, 0.65), (4, 0.45),
            (5, 0.30), (6, 0.20), (7, 0.12), (8, 0.07),
        ]
        decay_rate = 1.5
        attack_time = 0.020
        modulation_depth = 0.003
        noise_volume = 0.04
        reverb_amount = 0.10

    elif string_type == 'treble':
        harmonics = [
            (1, 1.0), (2, 0.55), (3, 0.35), (4, 0.20),
            (5, 0.10), (6, 0.05),
        ]
        decay_rate = 2.8
        attack_time = 0.008
        modulation_depth = 0.004
        noise_volume = 0.02
        reverb_amount = 0.15

    else:  # mid
        harmonics = [
            (1, 1.0), (2, 0.70), (3, 0.45), (4, 0.30),
            (5, 0.18), (6, 0.10), (7, 0.05),
        ]
        decay_rate = 2.2
        attack_time = 0.012
        modulation_depth = 0.003
        noise_volume = 0.03
        reverb_amount = 0.12

    audio_data = array.array('h')
    reverb_buffer = [0.0] * int(SAMPLE_RATE * 0.05)

    # Генерируем шум для атаки
    attack_noise = []
    if add_attack_noise:
        import random
        for i in range(int(SAMPLE_RATE * attack_time * 3)):
            noise = (random.random() - 0.5) * 2
            if string_type == 'bass':
                if len(attack_noise) > 0:
                    noise = noise * 0.3 + attack_noise[-1] * 0.7
            attack_noise.append(noise)

    for i in range(num_samples):
        t = i / SAMPLE_RATE

        # ===== 2. ОСНОВНОЙ ТОН С ГАРМОНИКАМИ =====
        value = 0.0

        if add_harmonics:
            for harmonic, amp in harmonics:
                freq = frequency * harmonic
                phase = harmonic * 0.3 + t * harmonic * 0.2
                harmonic_value = amp * math.sin(2 * math.pi * freq * t + phase)
                value += harmonic_value
        else:
            value = math.sin(2 * math.pi * frequency * t)

        # ===== 3. МОДУЛЯЦИЯ ЧАСТОТЫ =====
        if add_modulation and frequency > 40:
            mod_freq = 3.5 + 0.5 * math.sin(t * 0.2)
            mod_amount = modulation_depth * frequency * (0.5 + 0.5 * (1 - math.exp(-t * 0.5)))
            mod_wave = math.sin(2 * math.pi * mod_freq * t)

            freq_mod = frequency + mod_amount * mod_wave
            value = math.sin(2 * math.pi * freq_mod * t)

            if add_harmonics:
                value = 0.0
                for harmonic, amp in harmonics:
                    freq_harm = freq_mod * harmonic
                    phase = harmonic * 0.3 + t * harmonic * 0.2
                    harmonic_value = amp * math.sin(2 * math.pi * freq_harm * t + phase)
                    value += harmonic_value

        # ===== 4. ШУМ АТАКИ =====
        if add_attack_noise and i < len(attack_noise):
            noise_env = math.exp(-t * (20 if string_type != 'bass' else 15))
            noise = attack_noise[i] * noise_volume * noise_env
            value += noise

        # ===== 5. ОГИБАЮЩАЯ =====
        if t < attack_time:
            attack = t / attack_time
            attack = 1 - math.exp(-attack * 8)
        else:
            attack = 1.0

        decay_rate_adj = decay_rate * (1.0 + (frequency / 1000) * 0.15)
        envelope = math.exp(-t * decay_rate_adj)

        if t > duration * 0.6:
            breathe = 1.0 + 0.03 * math.sin(t * 5.0 + 1.0)
            envelope *= breathe

        value = value * envelope * attack * volume

        # ===== 6. РЕВЕРБЕРАЦИЯ =====
        if add_reverb and reverb_amount > 0:
            reverb_buffer.append(value * reverb_amount * 0.3)
            if len(reverb_buffer) > len(reverb_buffer):
                reverb_buffer.pop(0)
            reverb_signal = sum(reverb_buffer[-100:]) / 100
            value += reverb_signal * 0.1

        # ===== 7. КЛИППИНГ И НОРМАЛИЗАЦИЯ =====
        value = math.tanh(value * 0.9)
        value = clamp_value(value, -1.0, 1.0)

        int_value = int(MAX_AMPLITUDE * value)
        int_value = max(-32768, min(32767, int_value))
        audio_data.append(int_value)

    return audio_data


def save_wav(audio_data: array.array, filename: str) -> bool:
    """Сохраняет WAV файл"""
    try:
        with open(filename, 'wb') as f:
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + len(audio_data) * 2))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<H', 1))
            f.write(struct.pack('<H', 1))
            f.write(struct.pack('<I', SAMPLE_RATE))
            f.write(struct.pack('<I', SAMPLE_RATE * 2))
            f.write(struct.pack('<H', 2))
            f.write(struct.pack('<H', BITS_PER_SAMPLE))
            f.write(b'data')
            f.write(struct.pack('<I', len(audio_data) * 2))
            audio_data.tofile(f)
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения {filename}: {e}")
        return False


# utils/generate_sounds.py (альтернативная функция save_ogg)

def save_ogg(audio_data: array.array, filename: str) -> bool:
    """Сохраняет OGG файл (сжатый) через soundfile с правильным форматом"""
    if not HAS_SOUNDFILE:
        return False

    try:
        import numpy as np
        # Конвертируем в float64 для лучшей точности
        audio_np = np.array(audio_data, dtype=np.float64) / MAX_AMPLITUDE

        # Пробуем разные варианты сохранения
        try:
            # Вариант 1: без указания subtype
            sf.write(filename, audio_np, SAMPLE_RATE, format='ogg')
        except:
            try:
                # Вариант 2: с явным subtype
                sf.write(filename, audio_np, SAMPLE_RATE, format='ogg', subtype='PCM_16')
            except:
                # Вариант 3: конвертируем в int16 и сохраняем
                audio_int16 = (audio_np * MAX_AMPLITUDE).astype(np.int16)
                sf.write(filename, audio_int16, SAMPLE_RATE, format='ogg', subtype='PCM_16')
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения OGG {filename}: {e}")
        return False


def generate_all_sounds(output_dir: str = "assets/sounds", format: str = 'ogg'):
    """Генерирует все звуки для всех строев в папку assets/sounds/"""
    # Используем абсолютный путь от корня проекта
    base_dir = PROJECT_ROOT / output_dir
    base_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🎸 ГЕНЕРАЦИЯ РЕАЛИСТИЧНЫХ ЗВУКОВ")
    print("=" * 60)
    print(f"📁 Корень проекта: {PROJECT_ROOT}")
    print(f"📁 Формат: {format.upper()}")
    print(f"📁 Папка сохранения: {base_dir}")
    print("=" * 60)

    total_files = 0
    total_size = 0

    for tuning_name, tuning_data in TUNINGS.items():
        tuning_dir = base_dir / tuning_name
        tuning_dir.mkdir(exist_ok=True)

        print(f"\n📁 {tuning_data['name']} ({tuning_name})")
        print("-" * 40)

        for note_data in tuning_data['notes']:
            note = note_data['note']
            freq = note_data['freq']
            string_type = note_data['type']
            volume = note_data.get('volume', 0.7)

            filename = tuning_dir / f"{note}.{format}"

            audio_data = generate_realistic_string_sound(
                frequency=freq,
                duration=2.5,
                volume=volume,
                string_type=string_type,
                add_harmonics=True,
                add_modulation=True,
                add_attack_noise=True,
                add_reverb=True
            )

            # Сохраняем в нужном формате
            if format == 'ogg':
                if HAS_SOUNDFILE:
                    success = save_ogg(audio_data, str(filename))
                else:
                    # Если нет soundfile, сохраняем WAV
                    filename = tuning_dir / f"{note}.wav"
                    success = save_wav(audio_data, str(filename))
                    format = 'wav'
            else:
                success = save_wav(audio_data, str(filename))

            if success:
                size = os.path.getsize(str(filename))
                size_kb = size / 1024
                total_size += size
                total_files += 1
                print(f"   ✅ {note} ({freq:.2f} Hz) - {size_kb:.1f} KB")
            else:
                print(f"   ❌ {note} - Ошибка сохранения")

    print("\n" + "=" * 60)
    print(f"✅ Сгенерировано {total_files} файлов")
    print(f"📦 Общий размер: {total_size / 1024:.1f} KB")
    print(f"📁 Папка: {base_dir.absolute()}")
    print("=" * 60)

    return total_files > 0


def interactive_generation():
    """Интерактивный режим генерации"""
    print("\n" + "=" * 60)
    print("🎸 ГЕНЕРАТОР РЕАЛИСТИЧНЫХ ЗВУКОВ")
    print("   С поддержкой OGG сжатия")
    print("=" * 60)
    print(f"📁 Звуки будут сохранены в: {PROJECT_ROOT / 'assets/sounds/'}")
    print("=" * 60)

    while True:
        print("\nВыберите действие:")
        print("1. Сгенерировать все звуки (OGG - рекомендуется)")
        print("2. Сгенерировать все звуки (WAV - максимальное качество)")
        print("3. Сгенерировать один строй")
        print("4. Тест одной ноты")
        print("5. Выход")

        choice = input("\nВаш выбор (1-5): ").strip()

        if choice == '1':
            generate_all_sounds("assets/sounds", format='ogg')

        elif choice == '2':
            generate_all_sounds("assets/sounds", format='wav')

        elif choice == '3':
            print("\nДоступные строи:")
            for i, (name, data) in enumerate(TUNINGS.items(), 1):
                print(f"   {i}. {data['name']} ({name})")

            try:
                choice_num = int(input("Выберите строй (номер): ").strip())
                tuning_names = list(TUNINGS.keys())
                if 1 <= choice_num <= len(tuning_names):
                    tuning_name = tuning_names[choice_num - 1]

                    format_choice = input("Формат (ogg/wav, по умолчанию ogg): ").strip().lower()
                    if format_choice not in ['ogg', 'wav']:
                        format_choice = 'ogg'

                    base_dir = PROJECT_ROOT / "assets/sounds" / tuning_name
                    base_dir.mkdir(parents=True, exist_ok=True)

                    print(f"\n📁 {TUNINGS[tuning_name]['name']}")
                    for note_data in TUNINGS[tuning_name]['notes']:
                        note = note_data['note']
                        freq = note_data['freq']
                        filename = base_dir / f"{note}.{format_choice}"

                        audio_data = generate_realistic_string_sound(
                            frequency=freq,
                            duration=2.5,
                            volume=note_data.get('volume', 0.7),
                            string_type=note_data['type']
                        )

                        if format_choice == 'ogg' and HAS_SOUNDFILE:
                            success = save_ogg(audio_data, str(filename))
                        else:
                            success = save_wav(audio_data, str(filename))

                        if success:
                            size = os.path.getsize(str(filename)) / 1024
                            print(f"   ✅ {note} ({freq:.2f} Hz) - {size:.1f} KB")
                else:
                    print("❌ Неверный номер")
            except ValueError:
                print("❌ Введите число")

        elif choice == '4':
            try:
                freq = float(input("Введите частоту (Гц): ").strip())
                note = input("Введите название ноты (например, E2): ").strip()

                base_dir = PROJECT_ROOT / "assets/sounds/test"
                base_dir.mkdir(parents=True, exist_ok=True)
                filename = base_dir / f"{note}_{freq:.0f}Hz.wav"

                audio_data = generate_realistic_string_sound(
                    frequency=freq,
                    duration=3.0,
                    volume=0.7,
                    string_type='mid'
                )

                if save_wav(audio_data, str(filename)):
                    size_kb = len(audio_data) * 2 / 1024
                    print(f"✅ Сохранено: {filename} ({size_kb:.1f} KB)")
            except ValueError:
                print("❌ Введите корректное число")

        elif choice == '5':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")


def quick_generate():
    """Быстрая генерация для разработки"""
    print("\n⚡ БЫСТРАЯ ГЕНЕРАЦИЯ (OGG)")
    generate_all_sounds("assets/sounds", format='ogg')


if __name__ == '__main__':
    try:
        interactive_generation()
    except KeyboardInterrupt:
        print("\n👋 Прервано")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)