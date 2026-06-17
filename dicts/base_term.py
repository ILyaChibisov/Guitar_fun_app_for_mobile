# dicts/base_term.py
"""
Базовый класс для термина
"""

class Term:
    def __init__(self, name, description, synonyms=None, examples=None):
        self.name = name
        self.description = description
        self.synonyms = synonyms or []
        self.examples = examples or []

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'synonyms': self.synonyms,
            'examples': self.examples
        }