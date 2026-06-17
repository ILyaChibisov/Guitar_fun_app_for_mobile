# dicts/base_term.py
"""
Базовый класс для термина (упрощённая версия)
"""

class Term:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description
        }