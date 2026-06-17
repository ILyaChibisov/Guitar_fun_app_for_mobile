# dicts/b.py
"""
Термины на букву Б
"""
from dicts.base_term import Term

TERMS = {
    "баррэ": Term(
        name="Баррэ",
        description="Приём игры на гитаре, при котором указательный палец прижимает все или несколько струн на одном ладу.",
        synonyms=["барре"],
        examples=["Большое баррэ", "Малое баррэ"]
    ),
    "бенд": Term(
        name="Бенд",
        description="Приём изменения высоты звука путём натяжения струны вверх или вниз.",
        synonyms=["подтяжка"],
        examples=["Бенд на 1 тон"]
    ),
}

def get_all_terms():
    return TERMS