# utils/localization.py
import json
import os
from config.logger_config import get_logger
from utils.settings_manager import settings_manager

logger = get_logger('Localization')

TRANSLATIONS = {
    "ru": {
        "home": "Главная", "songs": "Песни", "chords": "Аккорды", "tuner": "Тюнер",
        "metronome": "Метроном", "favorites": "Избранное", "dictionary": "Словарь",
        "profile": "Профиль", "settings": "Настройки", "help": "Помощь",
        "promo": "Промокод", "feedback": "Обратная связь", "admin": "Админка",
        "search": "Поиск", "find": "Найти", "theme": "Тема", "language": "Язык",
        "theme_green": "Зелёная", "theme_light": "Светлая", "theme_dark": "Тёмная",
        "search_chord": "Поиск аккорда", "search_found": "Мы нашли ваш аккорд",
        "search_not_found": "По вашему запросу ничего не нашлось",
        "no_variants": "Нет других вариантов", "variant": "Вариант",
        "no_chords": "Нет доступных аккордов", "choose_chord": "Выберите аккорд",
        "choose_tonality": "Выберите тональность", "choose_type": "Выберите тип аккорда",
        "mode_notes": "Выбран режим показа нот", "mode_fingers": "Выбран режим постановки пальцев"
    },
    "en": {
        "home": "Home", "songs": "Songs", "chords": "Chords", "tuner": "Tuner",
        "metronome": "Metronome", "favorites": "Favorites", "dictionary": "Dictionary",
        "profile": "Profile", "settings": "Settings", "help": "Help",
        "promo": "Promo", "feedback": "Feedback", "admin": "Admin",
        "search": "Search", "find": "Find", "theme": "Theme", "language": "Language",
        "theme_green": "Green", "theme_light": "Light", "theme_dark": "Dark",
        "search_chord": "Search chord", "search_found": "Chord found",
        "search_not_found": "Nothing found", "no_variants": "No other variants",
        "variant": "Variant", "no_chords": "No chords available",
        "choose_chord": "Choose a chord", "choose_tonality": "Choose tonality",
        "choose_type": "Choose chord type", "mode_notes": "Notes mode selected",
        "mode_fingers": "Fingerings mode selected"
    },
    "fr": {
        "home": "Accueil", "songs": "Chansons", "chords": "Accords", "tuner": "Accordeur",
        "metronome": "Métronome", "favorites": "Favoris", "dictionary": "Dictionnaire",
        "profile": "Profil", "settings": "Paramètres", "help": "Aide",
        "promo": "Promo", "feedback": "Retour", "admin": "Admin",
        "search": "Recherche", "find": "Chercher", "theme": "Thème", "language": "Langue",
        "theme_green": "Vert", "theme_light": "Clair", "theme_dark": "Sombre",
        "search_chord": "Chercher un accord", "search_found": "Accord trouvé",
        "search_not_found": "Rien trouvé", "no_variants": "Pas d'autres variantes",
        "variant": "Variante", "no_chords": "Pas d'accords",
        "choose_chord": "Choisir un accord", "choose_tonality": "Choisir la tonalité",
        "choose_type": "Choisir le type d'accord", "mode_notes": "Mode notes sélectionné",
        "mode_fingers": "Mode doigté sélectionné"
    },
    "it": {
        "home": "Home", "songs": "Canzoni", "chords": "Accordi", "tuner": "Accordatore",
        "metronome": "Metronomo", "favorites": "Preferiti", "dictionary": "Dizionario",
        "profile": "Profilo", "settings": "Impostazioni", "help": "Aiuto",
        "promo": "Promo", "feedback": "Feedback", "admin": "Admin",
        "search": "Cerca", "find": "Trova", "theme": "Tema", "language": "Lingua",
        "theme_green": "Verde", "theme_light": "Chiaro", "theme_dark": "Scuro",
        "search_chord": "Cerca accordo", "search_found": "Accordo trovato",
        "search_not_found": "Niente trovato", "no_variants": "Nessun'altra variante",
        "variant": "Variante", "no_chords": "Nessun accordo",
        "choose_chord": "Scegli accordo", "choose_tonality": "Scegli tonalità",
        "choose_type": "Scegli tipo di accordo", "mode_notes": "Modalità note",
        "mode_fingers": "Modalità diteggiatura"
    },
    "es": {
        "home": "Inicio", "songs": "Canciones", "chords": "Acordes", "tuner": "Afinador",
        "metronome": "Metrónomo", "favorites": "Favoritos", "dictionary": "Diccionario",
        "profile": "Perfil", "settings": "Ajustes", "help": "Ayuda",
        "promo": "Promoción", "feedback": "Comentarios", "admin": "Admin",
        "search": "Buscar", "find": "Buscar", "theme": "Tema", "language": "Idioma",
        "theme_green": "Verde", "theme_light": "Claro", "theme_dark": "Oscuro",
        "search_chord": "Buscar acorde", "search_found": "Acorde encontrado",
        "search_not_found": "Nada encontrado", "no_variants": "Sin otras variantes",
        "variant": "Variante", "no_chords": "Sin acordes",
        "choose_chord": "Elegir acorde", "choose_tonality": "Elegir tonalidad",
        "choose_type": "Elegir tipo de acorde", "mode_notes": "Modo notas",
        "mode_fingers": "Modo digitación"
    },
    "pt": {
        "home": "Início", "songs": "Canções", "chords": "Acordes", "tuner": "Afinador",
        "metronome": "Metrônomo", "favorites": "Favoritos", "dictionary": "Dicionário",
        "profile": "Perfil", "settings": "Configurações", "help": "Ajuda",
        "promo": "Promoção", "feedback": "Feedback", "admin": "Admin",
        "search": "Pesquisar", "find": "Procurar", "theme": "Tema", "language": "Idioma",
        "theme_green": "Verde", "theme_light": "Claro", "theme_dark": "Escuro",
        "search_chord": "Procurar acorde", "search_found": "Acorde encontrado",
        "search_not_found": "Nada encontrado", "no_variants": "Sem outras variantes",
        "variant": "Variante", "no_chords": "Sem acordes",
        "choose_chord": "Escolher acorde", "choose_tonality": "Escolher tonalidade",
        "choose_type": "Escolher tipo de acorde", "mode_notes": "Modo notas",
        "mode_fingers": "Modo dedilhado"
    }
}

def get_text(key, default=None):
    lang = settings_manager.language
    if lang not in TRANSLATIONS:
        lang = 'ru'
    text = TRANSLATIONS[lang].get(key)
    if text is None:
        text = TRANSLATIONS['ru'].get(key, default if default else key)
    return text