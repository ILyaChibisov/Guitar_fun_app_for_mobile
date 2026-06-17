# utils/metronome_sound.py
"""
Генератор звука для метронома
"""
import math
import array
from kivy.core.audio import SoundLoader
from kivy.logger import Logger
import io


def generate_click_sound(frequency=1200, duration=0.05, sample_rate=44100):
    """
    Генерирует короткий щелчок для метронома

    Args:
        frequency: частота звука (Гц)
        duration: длительность (сек)
        sample_rate: частота дискретизации
    """
    num_samples = int(sample_rate * duration)

    # Создаём массив для аудиоданных
    data = array.array('h', [0]) * num_samples

    # Затухающая синусоида для естественного щелчка
    for i in range(num_samples):
        t = i / sample_rate
        # Синусоида с экспоненциальным затуханием
        value = int(32767 * math.sin(2 * math.pi * frequency * t) * math.exp(-t * 30))
        data[i] = value

    # Создаём WAV в памяти
    import struct
    wav_header = struct.pack(
        '<4s4s4s4sIHHIIHH4s',
        b'RIFF', 36 + len(data) * 2, b'WAVE', b'fmt ',
        16, 1, 1, sample_rate, sample_rate * 2, 2, 16, b'data',
                 len(data) * 2
    )

    wav_data = wav_header + data.tobytes()

    # Загружаем звук из памяти
    sound = SoundLoader.load(io.BytesIO(wav_data))
    return sound


def generate_accent_sound(frequency=1800, duration=0.08, sample_rate=44100):
    """
    Генерирует акцентный звук (для сильной доли)

    Args:
        frequency: частота звука (Гц) - выше для акцента
        duration: длительность (сек) - чуть длиннее
        sample_rate: частота дискретизации
    """
    num_samples = int(sample_rate * duration)
    data = array.array('h', [0]) * num_samples

    for i in range(num_samples):
        t = i / sample_rate
        # Более яркий звук для акцента
        value = int(32767 * math.sin(2 * math.pi * frequency * t) * math.exp(-t * 25))
        data[i] = value

    import struct
    wav_header = struct.pack(
        '<4s4s4s4sIHHIIHH4s',
        b'RIFF', 36 + len(data) * 2, b'WAVE', b'fmt ',
        16, 1, 1, sample_rate, sample_rate * 2, 2, 16, b'data',
                 len(data) * 2
    )

    wav_data = wav_header + data.tobytes()
    sound = SoundLoader.load(io.BytesIO(wav_data))
    return sound


# Предзагруженные звуки (кэш)
_click_sound = None
_accent_sound = None


def get_click_sound():
    """Возвращает предзагруженный звук щелчка"""
    global _click_sound
    if _click_sound is None:
        _click_sound = generate_click_sound()
    return _click_sound


def get_accent_sound():
    """Возвращает предзагруженный акцентный звук"""
    global _accent_sound
    if _accent_sound is None:
        _accent_sound = generate_accent_sound()
    return _accent_sound