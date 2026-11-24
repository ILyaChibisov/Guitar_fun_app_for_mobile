# screens/term_detail_screen.py
"""
Экран определения термина из словаря.
Наследует всё оформление, шкалу шрифта, кэш term_detail_state и навигацию от BaseTermDetailScreen.
"""
from screens.dictionary.base_term_detail_screen import BaseTermDetailScreen


class TermDetailScreen(BaseTermDetailScreen):
    SCREEN_NAME = 'term_detail'
    DEFAULT_PREVIOUS_SCREEN = 'dictionary'