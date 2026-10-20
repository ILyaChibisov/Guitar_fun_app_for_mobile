# utils/localization.py
from utils.settings_manager import settings_manager

TRANSLATIONS = {
    "ru": {
        "home": "Главная",
        "songs": "Песни",
        "chords": "Аккорды",
        "tuner": "Тюнер",
        "metronome": "Метроном",
        "favorites": "Избранное",
        "profile": "Профиль",
        "dictionary": "Словарь",
        "admin": "Админка",
        "search": "Поиск",
        "settings": "Настройки",
        "help": "Помощь",
        "promo": "Промокод",
        "feedback": "Обратная связь",
        # ... другие экраны
    },
    "en": {
        "home": "Home",
        "songs": "Songs",
        "chords": "Chords",
        "tuner": "Tuner",
        "metronome": "Metronome",
        "favorites": "Favorites",
        "profile": "Profile",
        "dictionary": "Dictionary",
        "admin": "Admin",
        "search": "Search",
        "settings": "Settings",
        "help": "Help",
        "promo": "Promo",
        "feedback": "Feedback",
        # ... другие экраны
    }
}

def get_text(key, default=None):
    """Возвращает перевод для ключа на текущем языке"""
    lang = settings_manager.language
    return TRANSLATIONS.get(lang, {}).get(key, default or key)