# utils/localization.py
import json
import os
from config.logger_config import get_logger
from utils.settings_manager import settings_manager

logger = get_logger('Localization')

# Базовые переводы для всех поддерживаемых языков
TRANSLATIONS = {
    "ru": {
        "home": "Главная", "songs": "Песни", "chords": "Аккорды", "tuner": "Тюнер",
        "metronome": "Метроном", "favorites": "Избранное", "dictionary": "Словарь",
        "profile": "Профиль", "settings": "Настройки", "help": "Помощь",
        "promo": "Промокод", "feedback": "Обратная связь", "admin": "Админка",
        "search": "Поиск", "theme": "Тема", "language": "Язык",
        "theme_green": "Зелёная", "theme_light": "Светлая", "theme_dark": "Тёмная"
    },
    "en": {
        "home": "Home", "songs": "Songs", "chords": "Chords", "tuner": "Tuner",
        "metronome": "Metronome", "favorites": "Favorites", "dictionary": "Dictionary",
        "profile": "Profile", "settings": "Settings", "help": "Help",
        "promo": "Promo", "feedback": "Feedback", "admin": "Admin",
        "search": "Search", "theme": "Theme", "language": "Language",
        "theme_green": "Green", "theme_light": "Light", "theme_dark": "Dark"
    },
    "fr": {
        "home": "Accueil", "songs": "Chansons", "chords": "Accords", "tuner": "Accordeur",
        "metronome": "Métronome", "favorites": "Favoris", "dictionary": "Dictionnaire",
        "profile": "Profil", "settings": "Paramètres", "help": "Aide",
        "promo": "Promo", "feedback": "Retour", "admin": "Admin",
        "search": "Recherche", "theme": "Thème", "language": "Langue",
        "theme_green": "Vert", "theme_light": "Clair", "theme_dark": "Sombre"
    },
    "it": {
        "home": "Home", "songs": "Canzoni", "chords": "Accordi", "tuner": "Accordatore",
        "metronome": "Metronomo", "favorites": "Preferiti", "dictionary": "Dizionario",
        "profile": "Profilo", "settings": "Impostazioni", "help": "Aiuto",
        "promo": "Promo", "feedback": "Feedback", "admin": "Admin",
        "search": "Cerca", "theme": "Tema", "language": "Lingua",
        "theme_green": "Verde", "theme_light": "Chiaro", "theme_dark": "Scuro"
    },
    "es": {
        "home": "Inicio", "songs": "Canciones", "chords": "Acordes", "tuner": "Afinador",
        "metronome": "Metrónomo", "favorites": "Favoritos", "dictionary": "Diccionario",
        "profile": "Perfil", "settings": "Ajustes", "help": "Ayuda",
        "promo": "Promoción", "feedback": "Comentarios", "admin": "Admin",
        "search": "Buscar", "theme": "Tema", "language": "Idioma",
        "theme_green": "Verde", "theme_light": "Claro", "theme_dark": "Oscuro"
    },
    "pt": {
        "home": "Início", "songs": "Canções", "chords": "Acordes", "tuner": "Afinador",
        "metronome": "Metrônomo", "favorites": "Favoritos", "dictionary": "Dicionário",
        "profile": "Perfil", "settings": "Configurações", "help": "Ajuda",
        "promo": "Promoção", "feedback": "Feedback", "admin": "Admin",
        "search": "Pesquisar", "theme": "Tema", "language": "Idioma",
        "theme_green": "Verde", "theme_light": "Claro", "theme_dark": "Escuro"
    }
}


def get_text(key, default=None):
    """Возвращает перевод для текущего языка."""
    lang = settings_manager.language
    if lang not in TRANSLATIONS:
        lang = 'ru'

    text = TRANSLATIONS[lang].get(key)
    if text is None:
        text = TRANSLATIONS['ru'].get(key, default if default else key)

    return text