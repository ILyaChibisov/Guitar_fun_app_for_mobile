# utils/generate_guitar_notes.py
"""
Генератор ЧИСТЫХ эталонных звуков гитарных струн
Без шумов, с плавным затуханием — идеально для проверки тюнера
"""
import os
import sys
import math
import array
import struct
import time
import tempfile

# ============ НАСТРОЙКИ ============
SAMPLE_RATE = 44100

# ============ СТРОЙ ГИТАРЫ ============
TUNINGS = {
    'standard': [
        {'string': 6, 'note': 'E2', 'freq': 82.41},
        {'string': 5, 'note': 'A2', 'freq': 110.00},
        {'string': 4, 'note': 'D3', 'freq': 146.83},
        {'string': 3, 'note': 'G3', 'freq': 196.00},
        {'string': 2, 'note': 'B3', 'freq': 246.94},
        {'string': 1, 'note': 'E4', 'freq': 329.63},
    ],
    'drop_d': [
        {'string': 6, 'note': 'D2', 'freq': 73.42},
        {'string': 5, 'note': 'A2', 'freq': 110.00},
        {'string': 4, 'note': 'D3', 'freq': 146.83},
        {'string': 3, 'note': 'G3', 'freq': 196.00},
        {'string': 2, 'note': 'B3', 'freq': 246.94},
        {'string': 1, 'note': 'E4', 'freq': 329.63},
    ],
    'bass_4': [
        {'string': 4, 'note': 'E1', 'freq': 41.20},
        {'string': 3, 'note': 'A1', 'freq': 55.00},
        {'string': 2, 'note': 'D2', 'freq': 73.42},
        {'string': 1, 'note': 'G2', 'freq': 98.00},
    ],
    'ukulele': [
        {'string': 4, 'note': 'G4', 'freq': 392.00},
        {'string': 3, 'note': 'C4', 'freq': 261.63},
        {'string': 2, 'note': 'E4', 'freq': 329.63},
        {'string': 1, 'note': 'A4', 'freq': 440.00},
    ],
}


def clamp_value(value, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, value))


def generate_clean_note(frequency, duration=2.5, volume=0.6):
    """
    Генерирует ЧИСТЫЙ эталонный звук ноты
    - Основная частота + гармоники
    - Плавное затухание
    - БЕЗ ШУМОВ
    - БЕЗ ЭФФЕКТОВ
    """
    num_samples = int(SAMPLE_RATE * duration)

    # Гармоники (обертоны) — чистые, без шума
    harmonics = [
        (1, 1.0),  # Основная
        (2, 0.60),  # 2-я гармоника
        (3, 0.35),  # 3-я
        (4, 0.20),  # 4-я
        (5, 0.10),  # 5-я
        (6, 0.05),  # 6-я
    ]

    audio_data = array.array('h')

    for i in range(num_samples):
        t = i / SAMPLE_RATE

        # Суммируем гармоники
        value = 0.0
        for harmonic, amp in harmonics:
            freq = frequency * harmonic
            phase = harmonic * 0.2
            harmonic_value = amp * math.sin(2 * math.pi * freq * t + phase)
            value += harmonic_value

        # Плавное затухание (одинаковое для всех нот)
        decay_rate = 2.0
        envelope = math.exp(-t * decay_rate)

        # Атака (плавный вход)
        attack_time = 0.01
        if t < attack_time:
            attack = t / attack_time
        else:
            attack = 1.0

        value = value * envelope * attack * volume
        value = clamp_value(value, -1.0, 1.0)

        int_value = int(32767 * value)
        int_value = max(-32768, min(32767, int_value))
        audio_data.append(int_value)

    return audio_data


def save_wav(audio_data, filename):
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
            f.write(struct.pack('<H', 16))
            f.write(b'data')
            f.write(struct.pack('<I', len(audio_data) * 2))
            audio_data.tofile(f)
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def play_sound(audio_data):
    """Воспроизводит звук через Kivy SoundLoader"""
    try:
        from kivy.core.audio import SoundLoader

        # Создаём временный файл
        fd, path = tempfile.mkstemp(suffix='.wav')
        os.close(fd)

        if not save_wav(audio_data, path):
            return False

        sound = SoundLoader.load(path)
        if not sound:
            try:
                os.unlink(path)
            except:
                pass
            return False

        sound.play()

        # Ждём окончания
        timeout = 5.0
        start = time.time()
        while sound.state == 'play' and (time.time() - start) < timeout:
            time.sleep(0.05)

        try:
            os.unlink(path)
        except:
            pass

        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def play_note(note_data, duration=2.5):
    """Проигрывает одну ноту"""
    freq = note_data['freq']
    note = note_data['note']
    string = note_data['string']

    print(f"🎵 Струна {string} ({note}, {freq:.2f} Hz)...")

    audio_data = generate_clean_note(freq, duration, volume=0.6)
    return play_sound(audio_data)


def play_all_strings(tuning='standard', delay=0.5):
    """Проигрывает все струны"""
    strings = TUNINGS.get(tuning, TUNINGS['standard'])

    print("=" * 50)
    print(f"🎸 ЭТАЛОННЫЕ НОТЫ: {tuning}")
    print("=" * 50)

    success = 0
    for note_data in strings:
        if play_note(note_data, duration=2.5):
            print(f"   ✅ {note_data['note']}")
            success += 1
        else:
            print(f"   ❌ {note_data['note']}")

        if delay > 0:
            time.sleep(delay)

    print("=" * 50)
    print(f"✅ Проиграно {success}/{len(strings)} нот")
    print("=" * 50)
    return success == len(strings)


def generate_files(tuning='standard', output_dir='test_notes'):
    """Создаёт WAV файлы всех нот"""
    os.makedirs(output_dir, exist_ok=True)
    strings = TUNINGS.get(tuning, TUNINGS['standard'])

    print(f"📁 Создание файлов в: {output_dir}")
    print("=" * 50)

    for note_data in strings:
        freq = note_data['freq']
        note = note_data['note']
        string = note_data['string']

        audio_data = generate_clean_note(freq, duration=2.5, volume=0.6)
        filename = os.path.join(output_dir, f"{string}_{note}_{freq:.0f}Hz.wav")

        if save_wav(audio_data, filename):
            print(f"   ✅ {note} -> {filename}")
        else:
            print(f"   ❌ {note}")

    print("=" * 50)
    print(f"✅ Файлы сохранены в {output_dir}")


def interactive_mode():
    print("\n" + "=" * 50)
    print("🎸 ЭТАЛОННЫЕ НОТЫ ГИТАРЫ")
    print("   (чистые, без шумов)")
    print("=" * 50)

    while True:
        print("\nВыберите действие:")
        print("1. Проиграть все струны (стандартный строй)")
        print("2. Проиграть конкретную ноту")
        print("3. Проиграть все струны (Drop D)")
        print("4. Проиграть все струны (Бас 4-струнный)")
        print("5. Проиграть все струны (Укулеле)")
        print("6. Сгенерировать WAV файлы для тестирования")
        print("7. Выход")

        choice = input("\nВаш выбор (1-7): ").strip()

        if choice == '1':
            play_all_strings('standard', delay=0.5)
        elif choice == '2':
            note = input("Введите ноту (E2, A2, D3, G3, B3, E4): ").strip().upper()
            strings = TUNINGS['standard']
            for n in strings:
                if n['note'] == note:
                    play_note(n, duration=3.0)
                    break
            else:
                print(f"❌ Нота {note} не найдена")
        elif choice == '3':
            play_all_strings('drop_d', delay=0.5)
        elif choice == '4':
            play_all_strings('bass_4', delay=0.5)
        elif choice == '5':
            play_all_strings('ukulele', delay=0.5)
        elif choice == '6':
            output_dir = input("Имя папки (по умолчанию: test_notes): ").strip()
            if not output_dir:
                output_dir = 'test_notes'
            generate_files('standard', output_dir)
        elif choice == '7':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор")


def quick_test():
    """Быстрый тест — все струны"""
    print("\n🎸 БЫСТРЫЙ ТЕСТ")
    print("=" * 50)
    play_all_strings('standard', delay=0.8)


if __name__ == '__main__':
    try:
        from kivy.core.audio import SoundLoader

        print("✅ Kivy SoundLoader доступен")
    except ImportError:
        print("⚠️ Kivy не найден!")
        print("   Установите: pip install kivy")
        sys.exit(1)

    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n👋 Прервано")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)