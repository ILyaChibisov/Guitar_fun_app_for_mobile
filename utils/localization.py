# utils/localization.py
"""
Локализация приложения. 6 языков: ru, en, fr, it, es, pt.
Ключи сгруппированы по экранам/модулям.
"""
from config.logger_config import get_logger
from utils.settings_manager import settings_manager

logger = get_logger('Localization')

TRANSLATIONS = {
    # ============================================================
    # РУССКИЙ
    # ============================================================
    "ru": {
        # ============ НАВИГАЦИЯ ============
        "home": "Главная", "songs": "Песни", "chords": "Аккорды", "tuner": "Тюнер",
        "metronome": "Метроном", "favorites": "Избранное", "dictionary": "Словарь",
        "profile": "Профиль", "settings": "Настройки", "help": "Помощь",
        "promo": "Промокод", "feedback": "Обратная связь", "admin": "Админка",

        # ============ ОБЩИЕ ============
        "search": "Поиск", "find": "Найти", "theme": "Тема", "language": "Язык",
        "theme_green": "Зелёная", "theme_light": "Светлая", "theme_dark": "Тёмная",
        "loading": "Загрузка", "min_chars": "Введите минимум 2 символа",
        "selected_lang": "Выбран", "lang_ru": "Русский", "lang_en": "English",
        "lang_digits": "0-9", "load_error": "Ошибка: не удалось загрузить песню",
        "close": "Закрыть", "cancel": "Отмена", "ok": "ОК", "apply": "Применить",
        "yes": "Да", "no": "Нет",

        # ============ АККОРДЫ ============
        "search_chord": "Поиск аккорда", "search_found": "Мы нашли ваш аккорд",
        "search_not_found": "По вашему запросу ничего не нашлось",
        "no_variants": "Нет других вариантов", "variant": "Вариант",
        "no_chords": "Нет доступных аккордов", "choose_chord": "Выберите аккорд",
        "choose_tonality": "Выберите тональность", "choose_type": "Выберите тип аккорда",
        "mode_notes": "Выбран режим показа нот", "mode_fingers": "Выбран режим постановки пальцев",

        # ============ ПЕСНИ ============
        "search_artists": "Поиск исполнителей по алфавиту",
        "search_results": "Результаты поиска",
        "artist_songs": "Песни исполнителя",
        "no_artists": "Нет исполнителей",
        "artists": "Исполнители",
        "songs_found": "Найдено песен",
        "nothing_found": "Ничего не найдено",
        "search_error": "Ошибка поиска\nПроверьте интернет",
        "loading_error": "Ошибка загрузки\nПроверьте интернет",
        "loading_songs": "Загрузка песен...",
        "no_artist_songs": "Нет песен у этого исполнителя",

        # ============ ТЮНЕР ============
        "in_tune": "В СТРОЕ!", "cents": "цент",
        "guitar": "🎸 Гитара", "bass": "🎸 Бас", "ukulele": "🎵 Укулеле",
        "choose_tuning": "Выберите строй", "tuning": "Строй",
        "audio_not_init": "Аудио не инициализировано",
        "tuning_standard_6": "Стандартный", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "На полтона ниже",
        "tuning_bass_4": "Бас 4-струнный", "tuning_bass_5": "Бас 5-струнный",
        "tuning_ukulele": "Укулеле",

        # ============ ИЗБРАННОЕ ============
        "auth_required_title": "Требуется авторизация",
        "auth_required_message": "Чтобы увидеть ваши избранные треки,\nнеобходимо войти в аккаунт",
        "no_songs": "Нет песен", "song_one": "песня", "songs_many": "песен",
        "no_favorites": "Нет избранных песен",
        "loading_favorites": "Загрузка избранного...",
        "remove_from_favorites": "Удалить из избранного?",
        "favorite_added": "Добавлено в избранное",
        "favorite_removed": "Удалено из избранного",
        "favorite_error": "Ошибка избранного",

        # ============ МЕТРОНОМ ============
        "reset": "Сброс", "accent": "Акцент", "on": "ВКЛ", "off": "ВЫКЛ",
        "started": "Запущен", "stopped": "Остановлен", "audio_error": "Ошибка звука",
        "sub_none": "Нет", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Механический", "tone_electronic": "Электронный",
        "tone_wood": "Деревянный", "tone_click": "Щелчок", "tone_beep": "Пищалка",

        # ============ СЛОВАРЬ ============
        "search_terms": "Поиск терминов",
        "search_by_alphabet": "Поиск по алфавиту",
        "terms_by_letter": "Термины на букву",
        "no_terms_for_letter": "Нет терминов на букву",
        "found_terms": "Найденные термины",
        "term_not_found": "Термин не найден",

        # ============ ПОИСК ============
        "what_to_search": "Что будем искать?",
        "search_placeholder": "Поиск аккордов или песен...",
        "searching": "Поиск...",
        "found_chords": "Найденные аккорды",
        "found_songs": "Найденные песни",
        "tonality": "Тональность",
        "unknown_artist": "Неизвестный",
        "untitled": "Без названия",
        "navigation_error": "Ошибка навигации",
        "chords_not_found": "Экран аккордов не найден",
        "song_not_found": "Экран песни не найден",

        # ============ CHORD DETAIL ============
        "chord_not_found": "Аккорд не найден",
    },

    # ============================================================
    # ENGLISH
    # ============================================================
    "en": {
        "home": "Home", "songs": "Songs", "chords": "Chords", "tuner": "Tuner",
        "metronome": "Metronome", "favorites": "Favorites", "dictionary": "Dictionary",
        "profile": "Profile", "settings": "Settings", "help": "Help",
        "promo": "Promo", "feedback": "Feedback", "admin": "Admin",

        "search": "Search", "find": "Find", "theme": "Theme", "language": "Language",
        "theme_green": "Green", "theme_light": "Light", "theme_dark": "Dark",
        "loading": "Loading", "min_chars": "Enter at least 2 characters",
        "selected_lang": "Selected", "lang_ru": "Russian", "lang_en": "English",
        "lang_digits": "0-9", "load_error": "Error: failed to load song",
        "close": "Close", "cancel": "Cancel", "ok": "OK", "apply": "Apply",
        "yes": "Yes", "no": "No",

        "search_chord": "Search chord", "search_found": "Chord found",
        "search_not_found": "Nothing found", "no_variants": "No other variants",
        "variant": "Variant", "no_chords": "No chords available",
        "choose_chord": "Choose a chord", "choose_tonality": "Choose tonality",
        "choose_type": "Choose chord type", "mode_notes": "Notes mode selected",
        "mode_fingers": "Fingerings mode selected",

        "search_artists": "Search artists alphabetically",
        "search_results": "Search results", "artist_songs": "Artist songs",
        "no_artists": "No artists", "artists": "Artists",
        "songs_found": "Songs found", "nothing_found": "Nothing found",
        "search_error": "Search error\nCheck connection",
        "loading_error": "Loading error\nCheck connection",
        "loading_songs": "Loading songs...",
        "no_artist_songs": "No songs by this artist",

        "in_tune": "IN TUNE!", "cents": "cents",
        "guitar": "🎸 Guitar", "bass": "🎸 Bass", "ukulele": "🎵 Ukulele",
        "choose_tuning": "Choose tuning", "tuning": "Tuning",
        "audio_not_init": "Audio not initialized",
        "tuning_standard_6": "Standard", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Half-step down",
        "tuning_bass_4": "Bass 4-string", "tuning_bass_5": "Bass 5-string",
        "tuning_ukulele": "Ukulele",

        "auth_required_title": "Authorization required",
        "auth_required_message": "To see your favorite tracks,\nyou need to log in",
        "no_songs": "No songs", "song_one": "song", "songs_many": "songs",
        "no_favorites": "No favorite songs",
        "loading_favorites": "Loading favorites...",
        "remove_from_favorites": "Remove from favorites?",
        "favorite_added": "Added to favorites",
        "favorite_removed": "Removed from favorites",
        "favorite_error": "Favorites error",

        "reset": "Reset", "accent": "Accent", "on": "ON", "off": "OFF",
        "started": "Started", "stopped": "Stopped", "audio_error": "Sound error",
        "sub_none": "None", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mechanical", "tone_electronic": "Electronic",
        "tone_wood": "Wood", "tone_click": "Click", "tone_beep": "Beep",

        "search_terms": "Search terms",
        "search_by_alphabet": "Search alphabetically",
        "terms_by_letter": "Terms for letter",
        "no_terms_for_letter": "No terms for letter",
        "found_terms": "Terms found", "term_not_found": "Term not found",

        "what_to_search": "What to search?",
        "search_placeholder": "Search chords or songs...",
        "searching": "Searching...",
        "found_chords": "Found chords", "found_songs": "Found songs",
        "tonality": "Tonality", "unknown_artist": "Unknown", "untitled": "Untitled",
        "navigation_error": "Navigation error",
        "chords_not_found": "Chords screen not found",
        "song_not_found": "Song screen not found",

        "chord_not_found": "Chord not found",
    },

    # ============================================================
    # FRANÇAIS
    # ============================================================
    "fr": {
        "home": "Accueil", "songs": "Chansons", "chords": "Accords", "tuner": "Accordeur",
        "metronome": "Métronome", "favorites": "Favoris", "dictionary": "Dictionnaire",
        "profile": "Profil", "settings": "Paramètres", "help": "Aide",
        "promo": "Promo", "feedback": "Retour", "admin": "Admin",

        "search": "Recherche", "find": "Chercher", "theme": "Thème", "language": "Langue",
        "theme_green": "Vert", "theme_light": "Clair", "theme_dark": "Sombre",
        "loading": "Chargement", "min_chars": "Entrez au moins 2 caractères",
        "selected_lang": "Sélectionné", "lang_ru": "Russe", "lang_en": "Anglais",
        "lang_digits": "0-9", "load_error": "Erreur: impossible de charger la chanson",
        "close": "Fermer", "cancel": "Annuler", "ok": "OK", "apply": "Appliquer",
        "yes": "Oui", "no": "Non",

        "search_chord": "Chercher un accord", "search_found": "Accord trouvé",
        "search_not_found": "Rien trouvé", "no_variants": "Pas d'autres variantes",
        "variant": "Variante", "no_chords": "Pas d'accords",
        "choose_chord": "Choisir un accord", "choose_tonality": "Choisir la tonalité",
        "choose_type": "Choisir le type d'accord", "mode_notes": "Mode notes sélectionné",
        "mode_fingers": "Mode doigté sélectionné",

        "search_artists": "Rechercher des artistes par ordre alphabétique",
        "search_results": "Résultats de recherche", "artist_songs": "Chansons de l'artiste",
        "no_artists": "Aucun artiste", "artists": "Artistes",
        "songs_found": "Chansons trouvées", "nothing_found": "Rien trouvé",
        "search_error": "Erreur de recherche\nVérifiez la connexion",
        "loading_error": "Erreur de chargement\nVérifiez la connexion",
        "loading_songs": "Chargement des chansons...",
        "no_artist_songs": "Aucune chanson de cet artiste",

        "in_tune": "ACCORDÉ !", "cents": "cents",
        "guitar": "🎸 Guitare", "bass": "🎸 Basse", "ukulele": "🎵 Ukulélé",
        "choose_tuning": "Choisir l'accordage", "tuning": "Accordage",
        "audio_not_init": "Audio non initialisé",
        "tuning_standard_6": "Standard", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Un demi-ton plus bas",
        "tuning_bass_4": "Basse 4 cordes", "tuning_bass_5": "Basse 5 cordes",
        "tuning_ukulele": "Ukulélé",

        "auth_required_title": "Autorisation requise",
        "auth_required_message": "Pour voir vos titres favoris,\nvous devez vous connecter",
        "no_songs": "Aucune chanson", "song_one": "chanson", "songs_many": "chansons",
        "no_favorites": "Aucune chanson favorite",
        "loading_favorites": "Chargement des favoris...",
        "remove_from_favorites": "Retirer des favoris ?",
        "favorite_added": "Ajouté aux favoris",
        "favorite_removed": "Retiré des favoris",
        "favorite_error": "Erreur des favoris",

        "reset": "Réinitialiser", "accent": "Accent", "on": "ON", "off": "OFF",
        "started": "Démarré", "stopped": "Arrêté", "audio_error": "Erreur audio",
        "sub_none": "Aucune", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mécanique", "tone_electronic": "Électronique",
        "tone_wood": "Bois", "tone_click": "Clic", "tone_beep": "Bip",

        "search_terms": "Rechercher des termes",
        "search_by_alphabet": "Recherche alphabétique",
        "terms_by_letter": "Termes pour la lettre",
        "no_terms_for_letter": "Aucun terme pour la lettre",
        "found_terms": "Termes trouvés", "term_not_found": "Terme non trouvé",

        "what_to_search": "Que chercher ?",
        "search_placeholder": "Rechercher accords ou chansons...",
        "searching": "Recherche...",
        "found_chords": "Accords trouvés", "found_songs": "Chansons trouvées",
        "tonality": "Tonalité", "unknown_artist": "Inconnu", "untitled": "Sans titre",
        "navigation_error": "Erreur de navigation",
        "chords_not_found": "Écran des accords introuvable",
        "song_not_found": "Écran de la chanson introuvable",

        "chord_not_found": "Accord non trouvé",
    },

    # ============================================================
    # ITALIANO
    # ============================================================
    "it": {
        "home": "Home", "songs": "Canzoni", "chords": "Accordi", "tuner": "Accordatore",
        "metronome": "Metronomo", "favorites": "Preferiti", "dictionary": "Dizionario",
        "profile": "Profilo", "settings": "Impostazioni", "help": "Aiuto",
        "promo": "Promo", "feedback": "Feedback", "admin": "Admin",

        "search": "Cerca", "find": "Trova", "theme": "Tema", "language": "Lingua",
        "theme_green": "Verde", "theme_light": "Chiaro", "theme_dark": "Scuro",
        "loading": "Caricamento", "min_chars": "Inserisci almeno 2 caratteri",
        "selected_lang": "Selezionato", "lang_ru": "Russo", "lang_en": "Inglese",
        "lang_digits": "0-9", "load_error": "Errore: impossibile caricare la canzone",
        "close": "Chiudi", "cancel": "Annulla", "ok": "OK", "apply": "Applica",
        "yes": "Sì", "no": "No",

        "search_chord": "Cerca accordo", "search_found": "Accordo trovato",
        "search_not_found": "Niente trovato", "no_variants": "Nessun'altra variante",
        "variant": "Variante", "no_chords": "Nessun accordo",
        "choose_chord": "Scegli accordo", "choose_tonality": "Scegli tonalità",
        "choose_type": "Scegli tipo di accordo", "mode_notes": "Modalità note",
        "mode_fingers": "Modalità diteggiatura",

        "search_artists": "Cerca artisti in ordine alfabetico",
        "search_results": "Risultati della ricerca", "artist_songs": "Canzoni dell'artista",
        "no_artists": "Nessun artista", "artists": "Artisti",
        "songs_found": "Canzoni trovate", "nothing_found": "Niente trovato",
        "search_error": "Errore di ricerca\nControlla la connessione",
        "loading_error": "Errore di caricamento\nControlla la connessione",
        "loading_songs": "Caricamento canzoni...",
        "no_artist_songs": "Nessuna canzone di questo artista",

        "in_tune": "ACCORDATO!", "cents": "cents",
        "guitar": "🎸 Chitarra", "bass": "🎸 Basso", "ukulele": "🎵 Ukulele",
        "choose_tuning": "Scegli accordatura", "tuning": "Accordatura",
        "audio_not_init": "Audio non inizializzato",
        "tuning_standard_6": "Standard", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Mezzo tono sotto",
        "tuning_bass_4": "Basso 4 corde", "tuning_bass_5": "Basso 5 corde",
        "tuning_ukulele": "Ukulele",

        "auth_required_title": "Autenticazione richiesta",
        "auth_required_message": "Per vedere i tuoi brani preferiti,\ndevi accedere",
        "no_songs": "Nessuna canzone", "song_one": "canzone", "songs_many": "canzoni",
        "no_favorites": "Nessuna canzone preferita",
        "loading_favorites": "Caricamento preferiti...",
        "remove_from_favorites": "Rimuovere dai preferiti?",
        "favorite_added": "Aggiunto ai preferiti",
        "favorite_removed": "Rimosso dai preferiti",
        "favorite_error": "Errore preferiti",

        "reset": "Ripristina", "accent": "Accento", "on": "ON", "off": "OFF",
        "started": "Avviato", "stopped": "Fermato", "audio_error": "Errore audio",
        "sub_none": "Nessuna", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Meccanico", "tone_electronic": "Elettronico",
        "tone_wood": "Legno", "tone_click": "Clic", "tone_beep": "Bip",

        "search_terms": "Cerca termini",
        "search_by_alphabet": "Ricerca alfabetica",
        "terms_by_letter": "Termini per la lettera",
        "no_terms_for_letter": "Nessun termine per la lettera",
        "found_terms": "Termini trovati", "term_not_found": "Termine non trovato",

        "what_to_search": "Cosa cercare?",
        "search_placeholder": "Cerca accordi o canzoni...",
        "searching": "Ricerca...",
        "found_chords": "Accordi trovati", "found_songs": "Canzoni trovate",
        "tonality": "Tonalità", "unknown_artist": "Sconosciuto", "untitled": "Senza titolo",
        "navigation_error": "Errore di navigazione",
        "chords_not_found": "Schermata accordi non trovata",
        "song_not_found": "Schermata canzone non trovata",

        "chord_not_found": "Accordo non trovato",
    },

    # ============================================================
    # ESPAÑOL
    # ============================================================
    "es": {
        "home": "Inicio", "songs": "Canciones", "chords": "Acordes", "tuner": "Afinador",
        "metronome": "Metrónomo", "favorites": "Favoritos", "dictionary": "Diccionario",
        "profile": "Perfil", "settings": "Ajustes", "help": "Ayuda",
        "promo": "Promoción", "feedback": "Comentarios", "admin": "Admin",

        "search": "Buscar", "find": "Buscar", "theme": "Tema", "language": "Idioma",
        "theme_green": "Verde", "theme_light": "Claro", "theme_dark": "Oscuro",
        "loading": "Cargando", "min_chars": "Introduce al menos 2 caracteres",
        "selected_lang": "Seleccionado", "lang_ru": "Ruso", "lang_en": "Inglés",
        "lang_digits": "0-9", "load_error": "Error: no se pudo cargar la canción",
        "close": "Cerrar", "cancel": "Cancelar", "ok": "OK", "apply": "Aplicar",
        "yes": "Sí", "no": "No",

        "search_chord": "Buscar acorde", "search_found": "Acorde encontrado",
        "search_not_found": "Nada encontrado", "no_variants": "Sin otras variantes",
        "variant": "Variante", "no_chords": "Sin acordes",
        "choose_chord": "Elegir acorde", "choose_tonality": "Elegir tonalidad",
        "choose_type": "Elegir tipo de acorde", "mode_notes": "Modo notas",
        "mode_fingers": "Modo digitación",

        "search_artists": "Buscar artistas por orden alfabético",
        "search_results": "Resultados de búsqueda", "artist_songs": "Canciones del artista",
        "no_artists": "Sin artistas", "artists": "Artistas",
        "songs_found": "Canciones encontradas", "nothing_found": "Nada encontrado",
        "search_error": "Error de búsqueda\nVerifica la conexión",
        "loading_error": "Error de carga\nVerifica la conexión",
        "loading_songs": "Cargando canciones...",
        "no_artist_songs": "Sin canciones de este artista",

        "in_tune": "¡AFINADO!", "cents": "cents",
        "guitar": "🎸 Guitarra", "bass": "🎸 Bajo", "ukulele": "🎵 Ukelele",
        "choose_tuning": "Elegir afinación", "tuning": "Afinación",
        "audio_not_init": "Audio no inicializado",
        "tuning_standard_6": "Estándar", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Medio tono abajo",
        "tuning_bass_4": "Bajo 4 cuerdas", "tuning_bass_5": "Bajo 5 cuerdas",
        "tuning_ukulele": "Ukelele",

        "auth_required_title": "Autorización requerida",
        "auth_required_message": "Para ver tus pistas favoritas,\ndebes iniciar sesión",
        "no_songs": "Sin canciones", "song_one": "canción", "songs_many": "canciones",
        "no_favorites": "Sin canciones favoritas",
        "loading_favorites": "Cargando favoritos...",
        "remove_from_favorites": "¿Quitar de favoritos?",
        "favorite_added": "Añadido a favoritos",
        "favorite_removed": "Eliminado de favoritos",
        "favorite_error": "Error de favoritos",

        "reset": "Restablecer", "accent": "Acento", "on": "ON", "off": "OFF",
        "started": "Iniciado", "stopped": "Detenido", "audio_error": "Error de audio",
        "sub_none": "Ninguna", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mecánico", "tone_electronic": "Electrónico",
        "tone_wood": "Madera", "tone_click": "Clic", "tone_beep": "Pitido",

        "search_terms": "Buscar términos",
        "search_by_alphabet": "Búsqueda alfabética",
        "terms_by_letter": "Términos para la letra",
        "no_terms_for_letter": "Sin términos para la letra",
        "found_terms": "Términos encontrados", "term_not_found": "Término no encontrado",

        "what_to_search": "¿Qué buscar?",
        "search_placeholder": "Buscar acordes o canciones...",
        "searching": "Buscando...",
        "found_chords": "Acordes encontrados", "found_songs": "Canciones encontradas",
        "tonality": "Tonalidad", "unknown_artist": "Desconocido", "untitled": "Sin título",
        "navigation_error": "Error de navegación",
        "chords_not_found": "Pantalla de acordes no encontrada",
        "song_not_found": "Pantalla de canción no encontrada",

        "chord_not_found": "Acorde no encontrado",
    },

    # ============================================================
    # PORTUGUÊS
    # ============================================================
    "pt": {
        "home": "Início", "songs": "Canções", "chords": "Acordes", "tuner": "Afinador",
        "metronome": "Metrônomo", "favorites": "Favoritos", "dictionary": "Dicionário",
        "profile": "Perfil", "settings": "Configurações", "help": "Ajuda",
        "promo": "Promoção", "feedback": "Feedback", "admin": "Admin",

        "search": "Pesquisar", "find": "Procurar", "theme": "Tema", "language": "Idioma",
        "theme_green": "Verde", "theme_light": "Claro", "theme_dark": "Escuro",
        "loading": "Carregando", "min_chars": "Digite pelo menos 2 caracteres",
        "selected_lang": "Selecionado", "lang_ru": "Russo", "lang_en": "Inglês",
        "lang_digits": "0-9", "load_error": "Erro: não foi possível carregar a música",
        "close": "Fechar", "cancel": "Cancelar", "ok": "OK", "apply": "Aplicar",
        "yes": "Sim", "no": "Não",

        "search_chord": "Procurar acorde", "search_found": "Acorde encontrado",
        "search_not_found": "Nada encontrado", "no_variants": "Sem outras variantes",
        "variant": "Variante", "no_chords": "Sem acordes",
        "choose_chord": "Escolher acorde", "choose_tonality": "Escolher tonalidade",
        "choose_type": "Escolher tipo de acorde", "mode_notes": "Modo notas",
        "mode_fingers": "Modo dedilhado",

        "search_artists": "Pesquisar artistas em ordem alfabética",
        "search_results": "Resultados da pesquisa", "artist_songs": "Canções do artista",
        "no_artists": "Sem artistas", "artists": "Artistas",
        "songs_found": "Canções encontradas", "nothing_found": "Nada encontrado",
        "search_error": "Erro de pesquisa\nVerifique a conexão",
        "loading_error": "Erro de carregamento\nVerifique a conexão",
        "loading_songs": "Carregando canções...",
        "no_artist_songs": "Sem canções deste artista",

        "in_tune": "AFINADO!", "cents": "cents",
        "guitar": "🎸 Guitarra", "bass": "🎸 Baixo", "ukulele": "🎵 Ukulele",
        "choose_tuning": "Escolher afinação", "tuning": "Afinação",
        "audio_not_init": "Áudio não inicializado",
        "tuning_standard_6": "Padrão", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Meio tom abaixo",
        "tuning_bass_4": "Baixo 4 cordas", "tuning_bass_5": "Baixo 5 cordas",
        "tuning_ukulele": "Ukulele",

        "auth_required_title": "Autorização necessária",
        "auth_required_message": "Para ver suas faixas favoritas,\nvocê precisa fazer login",
        "no_songs": "Sem canções", "song_one": "canção", "songs_many": "canções",
        "no_favorites": "Sem canções favoritas",
        "loading_favorites": "Carregando favoritos...",
        "remove_from_favorites": "Remover dos favoritos?",
        "favorite_added": "Adicionado aos favoritos",
        "favorite_removed": "Removido dos favoritos",
        "favorite_error": "Erro de favoritos",

        "reset": "Redefinir", "accent": "Acento", "on": "ON", "off": "OFF",
        "started": "Iniciado", "stopped": "Parado", "audio_error": "Erro de áudio",
        "sub_none": "Nenhuma", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mecânico", "tone_electronic": "Eletrônico",
        "tone_wood": "Madeira", "tone_click": "Clique", "tone_beep": "Bip",

        "search_terms": "Pesquisar termos",
        "search_by_alphabet": "Pesquisa alfabética",
        "terms_by_letter": "Termos para a letra",
        "no_terms_for_letter": "Sem termos para a letra",
        "found_terms": "Termos encontrados", "term_not_found": "Termo não encontrado",

        "what_to_search": "O que procurar?",
        "search_placeholder": "Procurar acordes ou canções...",
        "searching": "Procurando...",
        "found_chords": "Acordes encontrados", "found_songs": "Canções encontradas",
        "tonality": "Tonalidade", "unknown_artist": "Desconhecido", "untitled": "Sem título",
        "navigation_error": "Erro de navegação",
        "chords_not_found": "Tela de acordes não encontrada",
        "song_not_found": "Tela de canção não encontrada",

        "chord_not_found": "Acorde não encontrado",
    },
}


def get_text(key, default=None):
    """Возвращает перевод по ключу для текущего языка с фолбэком на ru."""
    lang = settings_manager.language
    if lang not in TRANSLATIONS:
        lang = 'ru'
    text = TRANSLATIONS[lang].get(key)
    if text is None:
        text = TRANSLATIONS['ru'].get(key, default if default else key)
    return text


def get_available_languages():
    """Список доступных языков для UI выбора."""
    return list(TRANSLATIONS.keys())