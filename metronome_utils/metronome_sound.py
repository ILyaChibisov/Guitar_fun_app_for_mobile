# utils/metronome_sound.py
"""
Генератор звука для метронома
Поддержка Android через временные файлы .wav
"""
import math
import array
import struct
import tempfile
import os
import random
from kivy.core.audio import SoundLoader
from kivy.utils import platform
from kivy.logger import Logger

logger = Logger.getChild('MetronomeSound')


# ============ ФУНКЦИИ ДЛЯ РАБОТЫ НА ANDROID ============
def get_temp_path():
    """Возвращает безопасный путь для временных файлов на Android"""
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except:
            pass
    return tempfile.gettempdir()


def generate_click_sound(frequency=1200, duration=0.05, sample_rate=44100, volume=0.8, waveform='sine'):
    """
    Генерирует короткий щелчок для метронома в формате .wav

    Args:
        frequency: частота звука (Гц)
        duration: длительность (сек)
        sample_rate: частота дискретизации
        volume: громкость (0.0 - 1.0)
        waveform: форма волны ('sine', 'square', 'triangle', 'sawtooth')
    """
    num_samples = int(sample_rate * duration)
    audio_data = array.array('h')

    for i in range(num_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 30)

        if waveform == 'sine':
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)
        elif waveform == 'square':
            value = int(32767 * volume * (1 if math.sin(2 * math.pi * frequency * t) > 0 else -1) * envelope)
        elif waveform == 'triangle':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            tri = 2 * abs(phase / math.pi - 1) - 1
            value = int(32767 * volume * tri * envelope)
        elif waveform == 'sawtooth':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            saw = 2 * (phase / (2 * math.pi)) - 1
            value = int(32767 * volume * saw * envelope)
        else:
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)

        audio_data.append(value)

    # Используем временный файл вместо BytesIO для Android
    temp_dir = get_temp_path()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=temp_dir) as tmp_file:
            tmp_path = tmp_file.name
            with open(tmp_path, 'wb') as f:
                f.write(b'RIFF')
                f.write(struct.pack('<I', 36 + len(audio_data) * 2))
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write(struct.pack('<I', 16))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<I', sample_rate))
                f.write(struct.pack('<I', sample_rate * 2))
                f.write(struct.pack('<H', 2))
                f.write(struct.pack('<H', 16))
                f.write(b'data')
                f.write(struct.pack('<I', len(audio_data) * 2))
                audio_data.tofile(f)

        sound = SoundLoader.load(tmp_path)
        try:
            os.unlink(tmp_path)
        except:
            pass
        return sound

    except Exception as e:
        logger.error(f"Ошибка создания звука: {e}")
        return None


def generate_accent_sound(frequency=1800, duration=0.08, sample_rate=44100, volume=1.0, waveform='sine'):
    """
    Генерирует акцентный звук (для сильной доли) в формате .wav

    Args:
        frequency: частота звука (Гц) - выше для акцента
        duration: длительность (сек) - чуть длиннее
        sample_rate: частота дискретизации
        volume: громкость (0.0 - 1.0)
        waveform: форма волны
    """
    num_samples = int(sample_rate * duration)
    audio_data = array.array('h')

    for i in range(num_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 25)

        if waveform == 'sine':
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)
        elif waveform == 'square':
            value = int(32767 * volume * (1 if math.sin(2 * math.pi * frequency * t) > 0 else -1) * envelope)
        elif waveform == 'triangle':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            tri = 2 * abs(phase / math.pi - 1) - 1
            value = int(32767 * volume * tri * envelope)
        elif waveform == 'sawtooth':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            saw = 2 * (phase / (2 * math.pi)) - 1
            value = int(32767 * volume * saw * envelope)
        else:
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)

        audio_data.append(value)

    temp_dir = get_temp_path()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=temp_dir) as tmp_file:
            tmp_path = tmp_file.name
            with open(tmp_path, 'wb') as f:
                f.write(b'RIFF')
                f.write(struct.pack('<I', 36 + len(audio_data) * 2))
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write(struct.pack('<I', 16))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<I', sample_rate))
                f.write(struct.pack('<I', sample_rate * 2))
                f.write(struct.pack('<H', 2))
                f.write(struct.pack('<H', 16))
                f.write(b'data')
                f.write(struct.pack('<I', len(audio_data) * 2))
                audio_data.tofile(f)

        sound = SoundLoader.load(tmp_path)
        try:
            os.unlink(tmp_path)
        except:
            pass
        return sound

    except Exception as e:
        logger.error(f"Ошибка создания акцентного звука: {e}")
        return None


def generate_subdivision_sound(frequency=800, duration=0.03, sample_rate=44100, volume=0.5, waveform='sine'):
    """
    Генерирует звук для деления длительностей в формате .wav
    """
    num_samples = int(sample_rate * duration)
    audio_data = array.array('h')

    for i in range(num_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 40)

        if waveform == 'sine':
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)
        elif waveform == 'square':
            value = int(32767 * volume * (1 if math.sin(2 * math.pi * frequency * t) > 0 else -1) * envelope)
        elif waveform == 'triangle':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            tri = 2 * abs(phase / math.pi - 1) - 1
            value = int(32767 * volume * tri * envelope)
        elif waveform == 'sawtooth':
            phase = (2 * math.pi * frequency * t) % (2 * math.pi)
            saw = 2 * (phase / (2 * math.pi)) - 1
            value = int(32767 * volume * saw * envelope)
        else:
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * t) * envelope)

        audio_data.append(value)

    temp_dir = get_temp_path()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=temp_dir) as tmp_file:
            tmp_path = tmp_file.name
            with open(tmp_path, 'wb') as f:
                f.write(b'RIFF')
                f.write(struct.pack('<I', 36 + len(audio_data) * 2))
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write(struct.pack('<I', 16))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<I', sample_rate))
                f.write(struct.pack('<I', sample_rate * 2))
                f.write(struct.pack('<H', 2))
                f.write(struct.pack('<H', 16))
                f.write(b'data')
                f.write(struct.pack('<I', len(audio_data) * 2))
                audio_data.tofile(f)

        sound = SoundLoader.load(tmp_path)
        try:
            os.unlink(tmp_path)
        except:
            pass
        return sound

    except Exception as e:
        logger.error(f"Ошибка создания звука деления: {e}")
        return None


def generate_mechanical_click(is_accent=False, sample_rate=44100, volume=0.8):
    """
    Генерирует реалистичный звук механического метронома (как тиканье часов)
    С имитацией деревянного корпуса и металлического механизма

    Args:
        is_accent: True для сильной доли (более громкий и насыщенный)
        sample_rate: частота дискретизации
        volume: громкость (0.0 - 1.0)
    """
    # Параметры для акцента и обычного тика
    if is_accent:
        duration = 0.06  # чуть длиннее
        vol = volume * 1.0
        base_freq = 1500  # частота для акцента
        decay_factor = 20
        noise_amount = 0.2
        click_strength = 0.4
    else:
        duration = 0.04
        vol = volume * 0.8
        base_freq = 1100  # частота для обычного тика
        decay_factor = 28
        noise_amount = 0.3
        click_strength = 0.3

    num_samples = int(sample_rate * duration)
    audio_data = array.array('h')

    # Генерируем шум для имитации дребезжания механизма
    noise_buffer = [random.uniform(-1, 1) for _ in range(num_samples)]

    for i in range(num_samples):
        t = i / sample_rate

        # Огибающая с быстрым затуханием (имитация удара)
        attack_time = 0.0008
        if t < attack_time:
            envelope = t / attack_time
        else:
            envelope = math.exp(-(t - attack_time) * decay_factor)

        # Затухание для хвоста звука
        if t > 0.025:
            envelope *= 0.7

        # Основной тон с гармониками
        tone = 0
        harmonic_count = 5 if is_accent else 4
        for h in range(1, harmonic_count + 1):
            # Частота с небольшим смещением для натуральности
            freq = base_freq * h * (1 + random.uniform(-0.005, 0.005))
            amp = 1.0 / (h * 1.3)
            tone += math.sin(2 * math.pi * freq * t) * amp
        tone /= harmonic_count

        # Низкочастотный резонанс (имитация корпуса)
        low_freq = base_freq * 0.35
        low_tone = math.sin(2 * math.pi * low_freq * t) * 0.25

        # Шум механизма
        noise_idx = i
        if noise_idx < len(noise_buffer):
            noise = noise_buffer[noise_idx] * noise_amount * envelope * 0.5
        else:
            noise = 0

        # Щелчок (удар)
        click = 0
        if t < 0.002:
            click = click_strength * (1 - t / 0.002) * 0.6

        # Смешиваем все компоненты
        combined = (tone * 0.4 + low_tone * 0.15 + noise + click) * envelope * vol
        combined = max(-1.0, min(1.0, combined))

        # Добавляем небольшую нелинейность для теплоты
        if combined > 0.5:
            combined = 0.5 + (combined - 0.5) * 0.7
        elif combined < -0.5:
            combined = -0.5 + (combined + 0.5) * 0.7

        value = int(32767 * combined)
        audio_data.append(value)

    temp_dir = get_temp_path()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', dir=temp_dir) as tmp_file:
            tmp_path = tmp_file.name
            with open(tmp_path, 'wb') as f:
                f.write(b'RIFF')
                f.write(struct.pack('<I', 36 + len(audio_data) * 2))
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write(struct.pack('<I', 16))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<H', 1))
                f.write(struct.pack('<I', sample_rate))
                f.write(struct.pack('<I', sample_rate * 2))
                f.write(struct.pack('<H', 2))
                f.write(struct.pack('<H', 16))
                f.write(b'data')
                f.write(struct.pack('<I', len(audio_data) * 2))
                audio_data.tofile(f)

        sound = SoundLoader.load(tmp_path)
        try:
            os.unlink(tmp_path)
        except:
            pass
        return sound

    except Exception as e:
        logger.error(f"Ошибка создания механического звука: {e}")
        return None


# ============ КЭШ ЗВУКОВ ============
_click_sound = None
_accent_sound = None
_subdivision_sound = None
_mechanical_click = None
_mechanical_accent = None


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


def get_subdivision_sound():
    """Возвращает предзагруженный звук для деления"""
    global _subdivision_sound
    if _subdivision_sound is None:
        _subdivision_sound = generate_subdivision_sound()
    return _subdivision_sound


def get_mechanical_click(is_accent=False):
    """Возвращает звук механического метронома"""
    if is_accent:
        global _mechanical_accent
        if _mechanical_accent is None:
            _mechanical_accent = generate_mechanical_click(is_accent=True)
        return _mechanical_accent
    else:
        global _mechanical_click
        if _mechanical_click is None:
            _mechanical_click = generate_mechanical_click(is_accent=False)
        return _mechanical_click


def clear_sound_cache():
    """Очищает кэш звуков (полезно при смене громкости)"""
    global _click_sound, _accent_sound, _subdivision_sound, _mechanical_click, _mechanical_accent
    _click_sound = None
    _accent_sound = None
    _subdivision_sound = None
    _mechanical_click = None
    _mechanical_accent = None
    logger.info("Кэш звуков очищен")