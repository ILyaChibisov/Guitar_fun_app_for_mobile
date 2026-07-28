"""
Пакет звуковых ассетов
Содержит сконвертированные звуки для всех строев
"""

from .bass_4 import Bass4Sounds
from .bass_5 import Bass5Sounds
from .dadgad import DadgadSounds
from .drop_d import DropDSounds
from .open_d import OpenDSounds
from .open_g import OpenGSounds
from .standard import StandardSounds
from .ukulele import UkuleleSounds

__all__ = [
        "Bass4Sounds",
        "Bass5Sounds",
        "DadgadSounds",
        "DropDSounds",
        "OpenDSounds",
        "OpenGSounds",
        "StandardSounds",
        "UkuleleSounds",
]
