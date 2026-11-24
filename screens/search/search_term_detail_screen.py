# screens/search_term_detail_screen.py
"""
Экран определения термина из поиска.
Наследует всё оформление, шкалу шрифта, кэш term_detail_state и навигацию от BaseTermDetailScreen.
"""
from screens.dictionary.base_term_detail_screen import BaseTermDetailScreen


class SearchTermDetailScreen(BaseTermDetailScreen):
    SCREEN_NAME = 'search_term_detail'
    DEFAULT_PREVIOUS_SCREEN = 'search'