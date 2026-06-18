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


# ============ КЭШ ЗВУКОВ ============
_click_sound = None
_accent_sound = None
_subdivision_sound = None


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


def clear_sound_cache():
    """Очищает кэш звуков (полезно при смене громкости)"""
    global _click_sound, _accent_sound, _subdivision_sound
    _click_sound = None
    _accent_sound = None
    _subdivision_sound = None
    logger.info("Кэш звуков очищен")