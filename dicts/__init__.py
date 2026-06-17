# dicts/__init__.py
"""
Модуль словаря музыкальных терминов
Структура:
    ru/ - русские термины по буквам (ru_01_a.py, ru_02_b.py, ...)
    en/ - английские термины по буквам (en_01_a.py, en_02_b.py, ...)
"""
from .base_term import Term

# Импортируем все модули для удобства
from .ru import *
from .en import *
