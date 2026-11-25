# utils/localization.py
"""
Локализация приложения GuitarFans.
12 языков: ru, en, es, pt, de, fr, it, pl, hu, uk, kk, tr.
Ключи сгруппированы по экранам и модулям.
"""
from config.logger_config import get_logger
from state.settings_state import settings_state as settings_manager

logger = get_logger('Localization')

TRANSLATIONS = {
    # ============================================================
    # РУССКИЙ (ru)
    # ============================================================
    "ru": {
        "home": "Главная", "songs": "Песни", "chords": "Аккорды", "tuner": "Тюнер",
        "metronome": "Метроном", "favorites": "Избранное", "dictionary": "Словарь",
        "profile": "Профиль", "settings": "Настройки", "help": "Помощь",
        "promo": "Промокод", "feedback": "Обратная связь", "admin": "Админка",

        "search": "Поиск", "find": "Найти", "theme": "Тема", "language": "Язык",
        "avatar": "Аватар", "apply_changes": "Принять изменения", "changes_saved": "Настройки сохранены",
        "theme_green": "Зелёная", "theme_light": "Светлая", "theme_dark": "Тёмная",
        "loading": "Загрузка...", "min_chars": "Введите минимум 2 символа",
        "selected_lang": "Выбран", "lang_ru": "Русский", "lang_en": "English",
        "lang_digits": "0-9", "load_error": "Ошибка: не удалось загрузить песню",
        "close": "Закрыть", "cancel": "Отмена", "ok": "ОК", "apply": "Применить",
        "yes": "Да", "no": "Нет", "retry": "Повторить",
        "page_of": "Страница {current} из {total}",

        "search_chord": "Поиск аккорда", "search_found": "Мы нашли ваш аккорд",
        "search_not_found": "По вашему запросу ничего не нашлось",
        "no_variants": "Нет других вариантов", "variant": "Вариант",
        "no_chords": "Нет доступных аккордов", "choose_chord": "Выберите аккорд",
        "choose_tonality": "Выберите тональность", "choose_type": "Выберите тип аккорда",
        "mode_notes": "Выбран режим показа нот", "mode_fingers": "Выбран режим постановки пальцев",

        "search_artists": "Поиск исполнителей по алфавиту",
        "search_results": "Результаты поиска", "artist_songs": "Песни исполнителя",
        "no_artists": "Нет исполнителей", "artists": "Исполнители", "of": "из",
        "songs_found": "Найдено песен", "nothing_found": "Ничего не найдено",
        "search_error": "Ошибка поиска\nПроверьте интернет",
        "loading_error": "Ошибка загрузки\nПроверьте интернет",
        "loading_songs": "Загрузка песен...",
        "no_artist_songs": "Нет песен у этого исполнителя",
        "tap_letter_to_retry": "Нажмите букву ещё раз, чтобы повторить",

        "in_tune": "В СТРОЕ!", "in_tune_label": "В СТРОЕ",
        "cents": "цент", "listening": "Слушаю...", "low": "НИЗКО", "high": "ВЫСОКО",
        "guitar": "🎸 Гитара", "bass": "🎸 Бас", "ukulele": "🎵 Укулеле",
        "choose_tuning": "Выберите строй", "tuning": "Строй",
        "audio_not_init": "Аудио не инициализировано",
        "tuning_standard_6": "Стандартный", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "На полтона ниже",
        "tuning_bass_4": "Бас 4-струнный", "tuning_bass_5": "Бас 5-струнный",
        "tuning_ukulele": "Укулеле",

        "auth_required_title": "Требуется авторизация",
        "auth_required_message": "Чтобы увидеть ваши избранные треки,\nнеобходимо войти в аккаунт",
        "no_songs": "Нет песен", "song_one": "песня", "songs_many": "песен",
        "no_favorites": "Нет избранных песен", "loading_favorites": "Загрузка избранного...",
        "remove_from_favorites": "Удалить из избранного?",
        "favorite_added": "Добавлено в избранное",
        "favorite_removed": "Удалено из избранного", "favorite_error": "Ошибка избранного",

        "reset": "Сброс", "accent": "Акцент", "on": "ВКЛ", "off": "ВЫКЛ",
        "started": "Запущен", "stopped": "Остановлен", "audio_error": "Ошибка звука",
        "sub_none": "Нет", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Механический", "tone_electronic": "Электронный",
        "tone_wood": "Деревянный", "tone_click": "Щелчок", "tone_beep": "Пищалка",

        "search_terms": "Поиск терминов", "search_by_alphabet": "Поиск по алфавиту",
        "terms_by_letter": "Термины на букву", "no_terms_for_letter": "Нет терминов на букву",
        "found_terms": "Найденные термины", "term_not_found": "Термин не найден",

        "what_to_search": "Что будем искать?", "search_placeholder": "Поиск аккордов или песен...",
        "searching": "Поиск...", "found_chords": "Найденные аккорды",
        "found_songs": "Найденные песни", "tonality": "Тональность",
        "unknown_artist": "Неизвестный", "untitled": "Без названия",
        "navigation_error": "Ошибка навигации",
        "chords_not_found": "Экран аккордов не найден", "song_not_found": "Экран песни не найден",
        "chord_not_found": "Аккорд не найден",
    },

    # ============================================================
    # ENGLISH (en)
    # ============================================================
    "en": {
        "home": "Home", "songs": "Songs", "chords": "Chords", "tuner": "Tuner",
        "metronome": "Metronome", "favorites": "Favorites", "dictionary": "Dictionary",
        "profile": "Profile", "settings": "Settings", "help": "Help",
        "promo": "Promo", "feedback": "Feedback", "admin": "Admin",

        "search": "Search", "find": "Find", "theme": "Theme", "language": "Language",
        "avatar": "Avatar", "apply_changes": "Apply changes", "changes_saved": "Settings saved",
        "theme_green": "Green", "theme_light": "Light", "theme_dark": "Dark",
        "loading": "Loading...", "min_chars": "Enter at least 2 characters",
        "selected_lang": "Selected", "lang_ru": "Russian", "lang_en": "English",
        "lang_digits": "0-9", "load_error": "Error: failed to load song",
        "close": "Close", "cancel": "Cancel", "ok": "OK", "apply": "Apply",
        "yes": "Yes", "no": "No", "retry": "Retry",
        "page_of": "Page {current} of {total}",

        "search_chord": "Search chord", "search_found": "Chord found",
        "search_not_found": "Nothing found", "no_variants": "No other variants",
        "variant": "Variant", "no_chords": "No chords available",
        "choose_chord": "Choose a chord", "choose_tonality": "Choose tonality",
        "choose_type": "Choose chord type", "mode_notes": "Notes mode selected",
        "mode_fingers": "Fingerings mode selected",

        "search_artists": "Search artists alphabetically",
        "search_results": "Search results", "artist_songs": "Artist songs",
        "no_artists": "No artists", "artists": "Artists", "of": "of",
        "songs_found": "Songs found", "nothing_found": "Nothing found",
        "search_error": "Search error\nCheck connection",
        "loading_error": "Loading error\nCheck connection",
        "loading_songs": "Loading songs...",
        "no_artist_songs": "No songs by this artist",
        "tap_letter_to_retry": "Tap the letter again to retry",

        "in_tune": "IN TUNE!", "in_tune_label": "IN TUNE",
        "cents": "cents", "listening": "Listening...", "low": "LOW", "high": "HIGH",
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
        "no_favorites": "No favorite songs", "loading_favorites": "Loading favorites...",
        "remove_from_favorites": "Remove from favorites?",
        "favorite_added": "Added to favorites",
        "favorite_removed": "Removed from favorites", "favorite_error": "Favorites error",

        "reset": "Reset", "accent": "Accent", "on": "ON", "off": "OFF",
        "started": "Started", "stopped": "Stopped", "audio_error": "Sound error",
        "sub_none": "None", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mechanical", "tone_electronic": "Electronic",
        "tone_wood": "Wood", "tone_click": "Click", "tone_beep": "Beep",

        "search_terms": "Search terms", "search_by_alphabet": "Search alphabetically",
        "terms_by_letter": "Terms for letter", "no_terms_for_letter": "No terms for letter",
        "found_terms": "Terms found", "term_not_found": "Term not found",

        "what_to_search": "What to search?", "search_placeholder": "Search chords or songs...",
        "searching": "Searching...", "found_chords": "Found chords",
        "found_songs": "Found songs", "tonality": "Tonality",
        "unknown_artist": "Unknown", "untitled": "Untitled",
        "navigation_error": "Navigation error",
        "chords_not_found": "Chords screen not found", "song_not_found": "Song screen not found",
        "chord_not_found": "Chord not found",
    },

    # ============================================================
    # ESPAÑOL (es)
    # ============================================================
    "es": {
        "home": "Inicio", "songs": "Canciones", "chords": "Acordes", "tuner": "Afinador",
        "metronome": "Metrónomo", "favorites": "Favoritos", "dictionary": "Diccionario",
        "profile": "Perfil", "settings": "Ajustes", "help": "Ayuda",
        "promo": "Promoción", "feedback": "Comentarios", "admin": "Admin",

        "search": "Buscar", "find": "Buscar", "theme": "Tema", "language": "Idioma",
        "avatar": "Avatar", "apply_changes": "Aplicar cambios", "changes_saved": "Ajustes guardados",
        "theme_green": "Verde", "theme_light": "Claro", "theme_dark": "Oscuro",
        "loading": "Cargando...", "min_chars": "Introduce al menos 2 caracteres",
        "selected_lang": "Seleccionado", "lang_ru": "Ruso", "lang_en": "Inglés",
        "lang_digits": "0-9", "load_error": "Error: no se pudo cargar la canción",
        "close": "Cerrar", "cancel": "Cancelar", "ok": "OK", "apply": "Aplicar",
        "yes": "Sí", "no": "No", "retry": "Reintentar",
        "page_of": "Página {current} de {total}",

        "search_chord": "Buscar acorde", "search_found": "Acorde encontrado",
        "search_not_found": "Nada encontrado", "no_variants": "Sin otras variantes",
        "variant": "Variante", "no_chords": "Sin acordes",
        "choose_chord": "Elegir acorde", "choose_tonality": "Elegir tonalidad",
        "choose_type": "Elegir tipo de acorde", "mode_notes": "Modo notas",
        "mode_fingers": "Modo digitación",

        "search_artists": "Buscar artistas por orden alfabético",
        "search_results": "Resultados de búsqueda", "artist_songs": "Canciones del artista",
        "no_artists": "Sin artistas", "artists": "Artistas", "of": "de",
        "songs_found": "Canciones encontradas", "nothing_found": "Nada encontrado",
        "search_error": "Error de búsqueda\nVerifica la conexión",
        "loading_error": "Error de carga\nVerifica la conexión",
        "loading_songs": "Cargando canciones...",
        "no_artist_songs": "Sin canciones de este artista",
        "tap_letter_to_retry": "Toca la letra de nuevo para reintentar",

        "in_tune": "¡AFINADO!", "in_tune_label": "AFINADO",
        "cents": "cents", "listening": "Escuchando...", "low": "BAJO", "high": "ALTO",
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
        "no_favorites": "Sin canciones favoritas", "loading_favorites": "Cargando favoritos...",
        "remove_from_favorites": "¿Quitar de favoritos?",
        "favorite_added": "Añadido a favoritos",
        "favorite_removed": "Eliminado de favoritos", "favorite_error": "Error de favoritos",

        "reset": "Restablecer", "accent": "Acento", "on": "ON", "off": "OFF",
        "started": "Iniciado", "stopped": "Detenido", "audio_error": "Error de audio",
        "sub_none": "Ninguna", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mecánico", "tone_electronic": "Electrónico",
        "tone_wood": "Madera", "tone_click": "Clic", "tone_beep": "Pitido",

        "search_terms": "Buscar términos", "search_by_alphabet": "Búsqueda alfabética",
        "terms_by_letter": "Términos para la letra", "no_terms_for_letter": "Sin términos para la letra",
        "found_terms": "Términos encontrados", "term_not_found": "Término no encontrado",

        "what_to_search": "¿Qué buscar?", "search_placeholder": "Buscar acordes o canciones...",
        "searching": "Buscando...", "found_chords": "Acordes encontrados",
        "found_songs": "Canciones encontradas", "tonality": "Tonalidad",
        "unknown_artist": "Desconocido", "untitled": "Sin título",
        "navigation_error": "Error de navegación",
        "chords_not_found": "Pantalla de acordes no encontrada", "song_not_found": "Pantalla de canción no encontrada",
        "chord_not_found": "Acorde no encontrado",
    },

    # ============================================================
    # PORTUGUÊS (pt)
    # ============================================================
    "pt": {
        "home": "Início", "songs": "Canções", "chords": "Acordes", "tuner": "Afinador",
        "metronome": "Metrônomo", "favorites": "Favoritos", "dictionary": "Dicionário",
        "profile": "Perfil", "settings": "Configurações", "help": "Ajuda",
        "promo": "Promoção", "feedback": "Feedback", "admin": "Admin",

        "search": "Pesquisar", "find": "Procurar", "theme": "Tema", "language": "Idioma",
        "avatar": "Avatar", "apply_changes": "Aplicar alterações", "changes_saved": "Configurações salvas",
        "theme_green": "Verde", "theme_light": "Claro", "theme_dark": "Escuro",
        "loading": "Carregando...", "min_chars": "Digite pelo menos 2 caracteres",
        "selected_lang": "Selecionado", "lang_ru": "Russo", "lang_en": "Inglês",
        "lang_digits": "0-9", "load_error": "Erro: não foi possível carregar a música",
        "close": "Fechar", "cancel": "Cancelar", "ok": "OK", "apply": "Aplicar",
        "yes": "Sim", "no": "Não", "retry": "Tentar novamente",
        "page_of": "Página {current} de {total}",

        "search_chord": "Procurar acorde", "search_found": "Acorde encontrado",
        "search_not_found": "Nada encontrado", "no_variants": "Sem outras variantes",
        "variant": "Variante", "no_chords": "Sem acordes",
        "choose_chord": "Escolher acorde", "choose_tonality": "Escolher tonalidade",
        "choose_type": "Escolher tipo de acorde", "mode_notes": "Modo notas",
        "mode_fingers": "Modo dedilhado",

        "search_artists": "Pesquisar artistas em ordem alfabética",
        "search_results": "Resultados da pesquisa", "artist_songs": "Canções do artista",
        "no_artists": "Sem artistas", "artists": "Artistas", "of": "de",
        "songs_found": "Canções encontradas", "nothing_found": "Nada encontrado",
        "search_error": "Erro de pesquisa\nVerifique a conexão",
        "loading_error": "Erro de carregamento\nVerifique a conexão",
        "loading_songs": "Carregando canções...",
        "no_artist_songs": "Sem canções deste artista",
        "tap_letter_to_retry": "Toque na letra novamente para tentar de novo",

        "in_tune": "AFINADO!", "in_tune_label": "AFINADO",
        "cents": "cents", "listening": "Ouvindo...", "low": "BAIXO", "high": "ALTO",
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
        "no_favorites": "Sem canções favoritas", "loading_favorites": "Carregando favoritos...",
        "remove_from_favorites": "Remover dos favoritos?",
        "favorite_added": "Adicionado aos favoritos",
        "favorite_removed": "Removido dos favoritos", "favorite_error": "Erro de favoritos",

        "reset": "Redefinir", "accent": "Acento", "on": "ON", "off": "OFF",
        "started": "Iniciado", "stopped": "Parado", "audio_error": "Erro de áudio",
        "sub_none": "Nenhuma", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mecânico", "tone_electronic": "Eletrônico",
        "tone_wood": "Madeira", "tone_click": "Clique", "tone_beep": "Bip",

        "search_terms": "Pesquisar termos", "search_by_alphabet": "Pesquisa alfabética",
        "terms_by_letter": "Termos para a letra", "no_terms_for_letter": "Sem termos para a letra",
        "found_terms": "Termos encontrados", "term_not_found": "Termo não encontrado",

        "what_to_search": "O que procurar?", "search_placeholder": "Procurar acordes ou canções...",
        "searching": "Procurando...", "found_chords": "Acordes encontrados",
        "found_songs": "Canções encontradas", "tonality": "Tonalidade",
        "unknown_artist": "Desconhecido", "untitled": "Sem título",
        "navigation_error": "Erro de navegação",
        "chords_not_found": "Tela de acordes não encontrada", "song_not_found": "Tela de canção não encontrada",
        "chord_not_found": "Acorde não encontrado",
    },

    # ============================================================
    # DEUTSCH (de)
    # ============================================================
    "de": {
        "home": "Startseite", "songs": "Lieder", "chords": "Akkorde", "tuner": "Stimmgerät",
        "metronome": "Metronom", "favorites": "Favoriten", "dictionary": "Wörterbuch",
        "profile": "Profil", "settings": "Einstellungen", "help": "Hilfe",
        "promo": "Aktionscode", "feedback": "Feedback", "admin": "Admin",

        "search": "Suche", "find": "Finden", "theme": "Design", "language": "Sprache",
        "avatar": "Avatar", "apply_changes": "Änderungen übernehmen", "changes_saved": "Gespeichert",
        "theme_green": "Grün", "theme_light": "Hell", "theme_dark": "Dunkel",
        "loading": "Laden...", "min_chars": "Mindestens 2 Zeichen eingeben",
        "selected_lang": "Ausgewählt", "lang_ru": "Russisch", "lang_en": "Englisch",
        "lang_digits": "0-9", "load_error": "Fehler beim Laden des Liedes",
        "close": "Schließen", "cancel": "Abbrechen", "ok": "OK", "apply": "Anwenden",
        "yes": "Ja", "no": "Nein", "retry": "Wiederholen",
        "page_of": "Seite {current} von {total}",

        "search_chord": "Akkord suchen", "search_found": "Akkord gefunden",
        "search_not_found": "Nichts gefunden", "no_variants": "Keine weiteren Varianten",
        "variant": "Variante", "no_chords": "Keine Akkorde verfügbar",
        "choose_chord": "Akkord wählen", "choose_tonality": "Tonart wählen",
        "choose_type": "Akkordtyp wählen", "mode_notes": "Notenmodus gewählt",
        "mode_fingers": "Fingersatzmodus gewählt",

        "search_artists": "Künstler alphabetisch suchen",
        "search_results": "Suchergebnisse", "artist_songs": "Lieder des Künstlers",
        "no_artists": "Keine Künstler", "artists": "Künstler", "of": "von",
        "songs_found": "Lieder gefunden", "nothing_found": "Nichts gefunden",
        "search_error": "Suchfehler\nVerbindung prüfen",
        "loading_error": "Ladefehler\nVerbindung prüfen",
        "loading_songs": "Lieder werden geladen...",
        "no_artist_songs": "Keine Lieder dieses Künstlers",
        "tap_letter_to_retry": "Tippen Sie erneut auf den Buchstaben",

        "in_tune": "GESTIMMT!", "in_tune_label": "GESTIMMT",
        "cents": "Cent", "listening": "Höre zu...", "low": "TIEF", "high": "HOCH",
        "guitar": "🎸 Gitarre", "bass": "🎸 Bass", "ukulele": "🎵 Ukulele",
        "choose_tuning": "Stimmung wählen", "tuning": "Stimmung",
        "audio_not_init": "Audio nicht initialisiert",
        "tuning_standard_6": "Standard", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Halbton tiefer",
        "tuning_bass_4": "Bass 4-saitig", "tuning_bass_5": "Bass 5-saitig",
        "tuning_ukulele": "Ukulele",

        "auth_required_title": "Anmeldung erforderlich",
        "auth_required_message": "Melden Sie sich an, um Ihre\nFavoriten zu sehen",
        "no_songs": "Keine Lieder", "song_one": "Lied", "songs_many": "Lieder",
        "no_favorites": "Keine Favoriten", "loading_favorites": "Favoriten werden geladen...",
        "remove_from_favorites": "Aus Favoriten entfernen?",
        "favorite_added": "Zu Favoriten hinzugefügt",
        "favorite_removed": "Aus Favoriten entfernt", "favorite_error": "Favoritenfehler",

        "reset": "Zurücksetzen", "accent": "Akzent", "on": "EIN", "off": "AUS",
        "started": "Gestartet", "stopped": "Gestoppt", "audio_error": "Tonfehler",
        "sub_none": "Keine", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mechanisch", "tone_electronic": "Elektronisch",
        "tone_wood": "Holz", "tone_click": "Klick", "tone_beep": "Piepton",

        "search_terms": "Begriffe suchen", "search_by_alphabet": "Alphabetische Suche",
        "terms_by_letter": "Begriffe mit Buchstabe", "no_terms_for_letter": "Keine Begriffe",
        "found_terms": "Gefundene Begriffe", "term_not_found": "Begriff nicht gefunden",

        "what_to_search": "Wonach suchen?", "search_placeholder": "Akkorde oder Lieder suchen...",
        "searching": "Suche...", "found_chords": "Gefundene Akkorde",
        "found_songs": "Gefundene Lieder", "tonality": "Tonart",
        "unknown_artist": "Unbekannt", "untitled": "Ohne Titel",
        "navigation_error": "Navigationsfehler",
        "chords_not_found": "Akkordbildschirm nicht gefunden", "song_not_found": "Liedbildschirm nicht gefunden",
        "chord_not_found": "Akkord nicht gefunden",
    },

    # ============================================================
    # FRANÇAIS (fr)
    # ============================================================
    "fr": {
        "home": "Accueil", "songs": "Chansons", "chords": "Accords", "tuner": "Accordeur",
        "metronome": "Métronome", "favorites": "Favoris", "dictionary": "Dictionnaire",
        "profile": "Profil", "settings": "Paramètres", "help": "Aide",
        "promo": "Promo", "feedback": "Retour", "admin": "Admin",

        "search": "Recherche", "find": "Chercher", "theme": "Thème", "language": "Langue",
        "avatar": "Avatar", "apply_changes": "Appliquer", "changes_saved": "Paramètres enregistrés",
        "theme_green": "Vert", "theme_light": "Clair", "theme_dark": "Sombre",
        "loading": "Chargement...", "min_chars": "Entrez au moins 2 caractères",
        "selected_lang": "Sélectionné", "lang_ru": "Russe", "lang_en": "Anglais",
        "lang_digits": "0-9", "load_error": "Erreur: impossible de charger la chanson",
        "close": "Fermer", "cancel": "Annuler", "ok": "OK", "apply": "Appliquer",
        "yes": "Oui", "no": "Non", "retry": "Réessayer",
        "page_of": "Page {current} sur {total}",

        "search_chord": "Chercher un accord", "search_found": "Accord trouvé",
        "search_not_found": "Rien trouvé", "no_variants": "Pas d'autres variantes",
        "variant": "Variante", "no_chords": "Pas d'accords",
        "choose_chord": "Choisir un accord", "choose_tonality": "Choisir la tonalité",
        "choose_type": "Choisir le type d'accord", "mode_notes": "Mode notes sélectionné",
        "mode_fingers": "Mode doigté sélectionné",

        "search_artists": "Rechercher des artistes par ordre alphabétique",
        "search_results": "Résultats de recherche", "artist_songs": "Chansons de l'artiste",
        "no_artists": "Aucun artiste", "artists": "Artistes", "of": "sur",
        "songs_found": "Chansons trouvées", "nothing_found": "Rien trouvé",
        "search_error": "Erreur de recherche\nVérifiez la connexion",
        "loading_error": "Erreur de chargement\nVérifiez la connexion",
        "loading_songs": "Chargement des chansons...",
        "no_artist_songs": "Aucune chanson de cet artiste",
        "tap_letter_to_retry": "Appuyez à nouveau sur la lettre pour réessayer",

        "in_tune": "ACCORDÉ !", "in_tune_label": "ACCORDÉ",
        "cents": "cents", "listening": "Écoute...", "low": "BAS", "high": "HAUT",
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
        "no_favorites": "Aucune chanson favorite", "loading_favorites": "Chargement des favoris...",
        "remove_from_favorites": "Retirer des favoris ?",
        "favorite_added": "Ajouté aux favoris",
        "favorite_removed": "Retiré des favoris", "favorite_error": "Erreur des favoris",

        "reset": "Réinitialiser", "accent": "Accent", "on": "ON", "off": "OFF",
        "started": "Démarré", "stopped": "Arrêté", "audio_error": "Erreur audio",
        "sub_none": "Aucune", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mécanique", "tone_electronic": "Électronique",
        "tone_wood": "Bois", "tone_click": "Clic", "tone_beep": "Bip",

        "search_terms": "Rechercher des termes", "search_by_alphabet": "Recherche alphabétique",
        "terms_by_letter": "Termes pour la lettre", "no_terms_for_letter": "Aucun terme pour la lettre",
        "found_terms": "Termes trouvés", "term_not_found": "Terme non trouvé",

        "what_to_search": "Que chercher ?", "search_placeholder": "Rechercher accords ou chansons...",
        "searching": "Recherche...", "found_chords": "Accords trouvés",
        "found_songs": "Chansons trouvées", "tonality": "Tonalité",
        "unknown_artist": "Inconnu", "untitled": "Sans titre",
        "navigation_error": "Erreur de navigation",
        "chords_not_found": "Écran des accords introuvable", "song_not_found": "Écran de la chanson introuvable",
        "chord_not_found": "Accord non trouvé",
    },

    # ============================================================
    # ITALIANO (it)
    # ============================================================
    "it": {
        "home": "Home", "songs": "Canzoni", "chords": "Accordi", "tuner": "Accordatore",
        "metronome": "Metronomo", "favorites": "Preferiti", "dictionary": "Dizionario",
        "profile": "Profilo", "settings": "Impostazioni", "help": "Aiuto",
        "promo": "Promo", "feedback": "Feedback", "admin": "Admin",

        "search": "Cerca", "find": "Trova", "theme": "Tema", "language": "Lingua",
        "avatar": "Avatar", "apply_changes": "Applica modifiche", "changes_saved": "Impostazioni salvate",
        "theme_green": "Verde", "theme_light": "Chiaro", "theme_dark": "Scuro",
        "loading": "Caricamento...", "min_chars": "Inserisci almeno 2 caratteri",
        "selected_lang": "Selezionato", "lang_ru": "Russo", "lang_en": "Inglese",
        "lang_digits": "0-9", "load_error": "Errore: impossibile caricare la canzone",
        "close": "Chiudi", "cancel": "Annulla", "ok": "OK", "apply": "Applica",
        "yes": "Sì", "no": "No", "retry": "Riprova",
        "page_of": "Pagina {current} di {total}",

        "search_chord": "Cerca accordo", "search_found": "Accordo trovato",
        "search_not_found": "Niente trovato", "no_variants": "Nessun'altra variante",
        "variant": "Variante", "no_chords": "Nessun accordo",
        "choose_chord": "Scegli accordo", "choose_tonality": "Scegli tonalità",
        "choose_type": "Scegli tipo di accordo", "mode_notes": "Modalità note",
        "mode_fingers": "Modalità diteggiatura",

        "search_artists": "Cerca artisti in ordine alfabetico",
        "search_results": "Risultati della ricerca", "artist_songs": "Canzoni dell'artista",
        "no_artists": "Nessun artista", "artists": "Artisti", "of": "di",
        "songs_found": "Canzoni trovate", "nothing_found": "Niente trovato",
        "search_error": "Errore di ricerca\nControlla la connessione",
        "loading_error": "Errore di caricamento\nControlla la connessione",
        "loading_songs": "Caricamento canzoni...",
        "no_artist_songs": "Nessuna canzone di questo artista",
        "tap_letter_to_retry": "Tocca di nuovo la lettera per riprovare",

        "in_tune": "ACCORDATO!", "in_tune_label": "ACCORDATO",
        "cents": "cents", "listening": "In ascolto...", "low": "BASSO", "high": "ALTO",
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
        "no_favorites": "Nessuna canzone preferita", "loading_favorites": "Caricamento preferiti...",
        "remove_from_favorites": "Rimuovere dai preferiti?",
        "favorite_added": "Aggiunto ai preferiti",
        "favorite_removed": "Rimosso dai preferiti", "favorite_error": "Errore preferiti",

        "reset": "Ripristina", "accent": "Accento", "on": "ON", "off": "OFF",
        "started": "Avviato", "stopped": "Fermato", "audio_error": "Errore audio",
        "sub_none": "Nessuna", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Meccanico", "tone_electronic": "Elettronico",
        "tone_wood": "Legno", "tone_click": "Clic", "tone_beep": "Bip",

        "search_terms": "Cerca termini", "search_by_alphabet": "Ricerca alfabetica",
        "terms_by_letter": "Termini per la lettera", "no_terms_for_letter": "Nessun termine per la lettera",
        "found_terms": "Termini trovati", "term_not_found": "Termine non trovato",

        "what_to_search": "Cosa cercare?", "search_placeholder": "Cerca accordi o canzoni...",
        "searching": "Ricerca...", "found_chords": "Accordi trovati",
        "found_songs": "Canzoni trovate", "tonality": "Tonalità",
        "unknown_artist": "Sconosciuto", "untitled": "Senza titolo",
        "navigation_error": "Errore di navigazione",
        "chords_not_found": "Schermata accordi non trovata", "song_not_found": "Schermata canzone non trovata",
        "chord_not_found": "Accordo non trovato",
    },

    # ============================================================
    # POLSKI (pl)
    # ============================================================
    "pl": {
        "home": "Główna", "songs": "Piosenki", "chords": "Akordy", "tuner": "Stroik",
        "metronome": "Metronom", "favorites": "Ulubione", "dictionary": "Słownik",
        "profile": "Profil", "settings": "Ustawienia", "help": "Pomoc",
        "promo": "Kod promo", "feedback": "Opinia", "admin": "Admin",

        "search": "Szukaj", "find": "Znajdź", "theme": "Motyw", "language": "Język",
        "avatar": "Awatar", "apply_changes": "Zastosuj zmiany", "changes_saved": "Zapisano ustawienia",
        "theme_green": "Zielony", "theme_light": "Jasny", "theme_dark": "Ciemny",
        "loading": "Ładowanie...", "min_chars": "Wpisz co najmniej 2 znaki",
        "selected_lang": "Wybrano", "lang_ru": "Rosyjski", "lang_en": "Angielski",
        "lang_digits": "0-9", "load_error": "Błąd wczytywania piosenki",
        "close": "Zamknij", "cancel": "Anuluj", "ok": "OK", "apply": "Zastosuj",
        "yes": "Tak", "no": "Nie", "retry": "Ponów",
        "page_of": "Strona {current} z {total}",

        "search_chord": "Szukaj akordu", "search_found": "Znaleziono akord",
        "search_not_found": "Nic nie znaleziono", "no_variants": "Brak innych wariantów",
        "variant": "Wariant", "no_chords": "Brak dostępnych akordów",
        "choose_chord": "Wybierz akord", "choose_tonality": "Wybierz tonację",
        "choose_type": "Wybierz typ akordu", "mode_notes": "Tryb nut",
        "mode_fingers": "Tryb palcowania",

        "search_artists": "Szukaj wykonawców alfabetycznie",
        "search_results": "Wyniki wyszukiwania", "artist_songs": "Piosenki wykonawcy",
        "no_artists": "Brak wykonawców", "artists": "Wykonawcy", "of": "z",
        "songs_found": "Znalezione piosenki", "nothing_found": "Nic nie znaleziono",
        "search_error": "Błąd wyszukiwania\nSprawdź połączenie",
        "loading_error": "Błąd ładowania\nSprawdź połączenie",
        "loading_songs": "Ładowanie piosenek...",
        "no_artist_songs": "Brak piosenek tego wykonawcy",
        "tap_letter_to_retry": "Dotknij literę ponownie",

        "in_tune": "NASTROJONE!", "in_tune_label": "NASTROJONE",
        "cents": "centy", "listening": "Słucham...", "low": "NISKO", "high": "WYSOKO",
        "guitar": "🎸 Gitara", "bass": "🎸 Bas", "ukulele": "🎵 Ukulele",
        "choose_tuning": "Wybierz strój", "tuning": "Strój",
        "audio_not_init": "Audio niezainicjowane",
        "tuning_standard_6": "Standardowy", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Pół tonu niżej",
        "tuning_bass_4": "Bas 4-strunowy", "tuning_bass_5": "Bas 5-strunowy",
        "tuning_ukulele": "Ukulele",

        "auth_required_title": "Wymagane logowanie",
        "auth_required_message": "Zaloguj się, aby zobaczyć\nulubione utwory",
        "no_songs": "Brak piosenek", "song_one": "piosenka", "songs_many": "piosenek",
        "no_favorites": "Brak ulubionych", "loading_favorites": "Ładowanie ulubionych...",
        "remove_from_favorites": "Usunąć z ulubionych?",
        "favorite_added": "Dodano do ulubionych",
        "favorite_removed": "Usunięto z ulubionych", "favorite_error": "Błąd ulubionych",

        "reset": "Resetuj", "accent": "Akcent", "on": "WŁ", "off": "WYŁ",
        "started": "Uruchomiono", "stopped": "Zatrzymano", "audio_error": "Błąd dźwięku",
        "sub_none": "Brak", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mechaniczny", "tone_electronic": "Elektroniczny",
        "tone_wood": "Drewniany", "tone_click": "Klik", "tone_beep": "Sygnał",

        "search_terms": "Szukaj terminów", "search_by_alphabet": "Szukaj alfabetycznie",
        "terms_by_letter": "Terminy na literę", "no_terms_for_letter": "Brak terminów",
        "found_terms": "Znalezione terminy", "term_not_found": "Nie znaleziono terminu",

        "what_to_search": "Czego szukasz?", "search_placeholder": "Szukaj akordów lub piosenek...",
        "searching": "Szukanie...", "found_chords": "Znalezione akordy",
        "found_songs": "Znalezione piosenki", "tonality": "Tonacja",
        "unknown_artist": "Nieznany", "untitled": "Bez tytułu",
        "navigation_error": "Błąd nawigacji",
        "chords_not_found": "Nie znaleziono ekranu akordów", "song_not_found": "Nie znaleziono ekranu piosenki",
        "chord_not_found": "Nie znaleziono akordu",
    },

    # ============================================================
    # MAGYAR (hu)
    # ============================================================
    "hu": {
        "home": "Főoldal", "songs": "Dalok", "chords": "Akkordok", "tuner": "Hangoló",
        "metronome": "Metronóm", "favorites": "Kedvencek", "dictionary": "Szótár",
        "profile": "Profil", "settings": "Beállítások", "help": "Súgó",
        "promo": "Promóció", "feedback": "Visszajelzés", "admin": "Admin",

        "search": "Keresés", "find": "Keres", "theme": "Téma", "language": "Nyelv",
        "avatar": "Avatár", "apply_changes": "Módosítások mentése", "changes_saved": "Mentve",
        "theme_green": "Zöld", "theme_light": "Világos", "theme_dark": "Sötét",
        "loading": "Betöltés...", "min_chars": "Írj be legalább 2 karaktert",
        "selected_lang": "Kiválasztva", "lang_ru": "Orosz", "lang_en": "Angol",
        "lang_digits": "0-9", "load_error": "Hiba a dal betöltésekor",
        "close": "Bezárás", "cancel": "Mégse", "ok": "OK", "apply": "Alkalmaz",
        "yes": "Igen", "no": "Nem", "retry": "Újra",
        "page_of": "{current} / {total} oldal",

        "search_chord": "Akkord keresése", "search_found": "Akkord megtalálva",
        "search_not_found": "Nincs találat", "no_variants": "Nincs több változat",
        "variant": "Változat", "no_chords": "Nincsenek akkordok",
        "choose_chord": "Válassz akkordot", "choose_tonality": "Válassz hangnemet",
        "choose_type": "Válassz akkordtípust", "mode_notes": "Hangjegy mód",
        "mode_fingers": "Ujjrend mód",

        "search_artists": "Előadók keresése ábécé szerint",
        "search_results": "Keresési eredmények", "artist_songs": "Előadó dalai",
        "no_artists": "Nincsenek előadók", "artists": "Előadók", "of": "/",
        "songs_found": "Talált dalok", "nothing_found": "Nincs találat",
        "search_error": "Keresési hiba\nEllenőrizd a netet",
        "loading_error": "Betöltési hiba\nEllenőrizd a netet",
        "loading_songs": "Dalok betöltése...",
        "no_artist_songs": "Nincsenek dalai az előadónak",
        "tap_letter_to_retry": "Érintsd meg újra a betűt",

        "in_tune": "HANGOLVA!", "in_tune_label": "HANGOLVA",
        "cents": "cent", "listening": "Hallgatás...", "low": "ALACSONY", "high": "MAGAS",
        "guitar": "🎸 Gitár", "bass": "🎸 Basszus", "ukulele": "🎵 Ukulele",
        "choose_tuning": "Hangolás választása", "tuning": "Hangolás",
        "audio_not_init": "Hang nincs inicializálva",
        "tuning_standard_6": "Normál", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Fél hanggal lejjebb",
        "tuning_bass_4": "4 húros basszus", "tuning_bass_5": "5 húros basszus",
        "tuning_ukulele": "Ukulele",

        "auth_required_title": "Bejelentkezés szükséges",
        "auth_required_message": "A kedvencek megtekintéséhez\njelentkezz be",
        "no_songs": "Nincsenek dalok", "song_one": "dal", "songs_many": "dal",
        "no_favorites": "Nincsenek kedvencek", "loading_favorites": "Kedvencek betöltése...",
        "remove_from_favorites": "Törlés a kedvencekből?",
        "favorite_added": "Hozzáadva a kedvencekhez",
        "favorite_removed": "Eltávolítva a kedvencekből", "favorite_error": "Kedvencek hiba",

        "reset": "Alaphelyzet", "accent": "Hangsúly", "on": "BE", "off": "KI",
        "started": "Elindítva", "stopped": "Leállítva", "audio_error": "Hanghiba",
        "sub_none": "Nincs", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mechanikus", "tone_electronic": "Elektronikus",
        "tone_wood": "Fa", "tone_click": "Kattogás", "tone_beep": "Sípolás",

        "search_terms": "Kifejezések keresése", "search_by_alphabet": "Keresés ábécé szerint",
        "terms_by_letter": "Kifejezések betű szerint", "no_terms_for_letter": "Nincs kifejezés",
        "found_terms": "Talált kifejezések", "term_not_found": "Kifejezés nem található",

        "what_to_search": "Mit keressünk?", "search_placeholder": "Akkordok vagy dalok keresése...",
        "searching": "Keresés...", "found_chords": "Talált akkordok",
        "found_songs": "Talált dalok", "tonality": "Hangnem",
        "unknown_artist": "Ismeretlen", "untitled": "Cím nélkül",
        "navigation_error": "Navigációs hiba",
        "chords_not_found": "Akkordok képernyő nem található", "song_not_found": "Dal képernyő nem található",
        "chord_not_found": "Akkord nem található",
    },

    # ============================================================
    # УКРАЇНСЬКА (uk)
    # ============================================================
    "uk": {
        "home": "Головна", "songs": "Пісні", "chords": "Акорди", "tuner": "Тюнер",
        "metronome": "Метроном", "favorites": "Обране", "dictionary": "Словник",
        "profile": "Профіль", "settings": "Налаштування", "help": "Допомога",
        "promo": "Промокод", "feedback": "Зворотний зв'язок", "admin": "Адмінка",

        "search": "Пошук", "find": "Знайти", "theme": "Тема", "language": "Мова",
        "avatar": "Аватар", "apply_changes": "Прийняти зміни", "changes_saved": "Налаштування збережено",
        "theme_green": "Зелена", "theme_light": "Світла", "theme_dark": "Темна",
        "loading": "Завантаження...", "min_chars": "Введіть мінімум 2 символи",
        "selected_lang": "Обрано", "lang_ru": "Російська", "lang_en": "Англійська",
        "lang_digits": "0-9", "load_error": "Помилка завантаження пісні",
        "close": "Закрити", "cancel": "Скасувати", "ok": "ОК", "apply": "Застосувати",
        "yes": "Так", "no": "Ні", "retry": "Повторити",
        "page_of": "Сторінка {current} з {total}",

        "search_chord": "Пошук акорду", "search_found": "Акорд знайдено",
        "search_not_found": "Нічого не знайдено", "no_variants": "Немає інших варіантів",
        "variant": "Варіант", "no_chords": "Немає доступних акордів",
        "choose_chord": "Оберіть акорд", "choose_tonality": "Оберіть тональність",
        "choose_type": "Оберіть тип акорду", "mode_notes": "Режим показу нот",
        "mode_fingers": "Режим постановки пальців",

        "search_artists": "Пошук виконавців за алфавітом",
        "search_results": "Результати пошуку", "artist_songs": "Пісні виконавця",
        "no_artists": "Немає виконавців", "artists": "Виконавці", "of": "з",
        "songs_found": "Знайдено пісень", "nothing_found": "Нічого не знайдено",
        "search_error": "Помилка пошуку\nПеревірте інтернет",
        "loading_error": "Помилка завантаження\nПеревірте інтернет",
        "loading_songs": "Завантаження пісень...",
        "no_artist_songs": "Немає пісень у цього виконавця",
        "tap_letter_to_retry": "Натисніть літеру ще раз",

        "in_tune": "В СТРОЇ!", "in_tune_label": "В СТРОЇ",
        "cents": "цент", "listening": "Слухаю...", "low": "НИЗЬКО", "high": "ВИСОКО",
        "guitar": "🎸 Гітара", "bass": "🎸 Бас", "ukulele": "🎵 Укулеле",
        "choose_tuning": "Оберіть стрій", "tuning": "Стрій",
        "audio_not_init": "Аудіо не ініціалізовано",
        "tuning_standard_6": "Стандартний", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "На півтону нижче",
        "tuning_bass_4": "Бас 4-струнний", "tuning_bass_5": "Бас 5-струнний",
        "tuning_ukulele": "Укулеле",

        "auth_required_title": "Потрібна авторизація",
        "auth_required_message": "Щоб бачити обрані треки,\nнеобхідно увійти в акаунт",
        "no_songs": "Немає пісень", "song_one": "пісня", "songs_many": "пісень",
        "no_favorites": "Немає обраних пісень", "loading_favorites": "Завантаження обраного...",
        "remove_from_favorites": "Видалити з обраного?",
        "favorite_added": "Додано до обраного",
        "favorite_removed": "Видалено з обраного", "favorite_error": "Помилка обраного",

        "reset": "Скинути", "accent": "Акцент", "on": "УВІМК", "off": "ВИМК",
        "started": "Запущено", "stopped": "Зупинено", "audio_error": "Помилка звуку",
        "sub_none": "Немає", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Механічний", "tone_electronic": "Електронний",
        "tone_wood": "Дерев'яний", "tone_click": "Клацання", "tone_beep": "Сигнал",

        "search_terms": "Пошук термінів", "search_by_alphabet": "Пошук за алфавітом",
        "terms_by_letter": "Терміни на літеру", "no_terms_for_letter": "Немає термінів",
        "found_terms": "Знайдені терміни", "term_not_found": "Термін не знайдено",

        "what_to_search": "Що шукати?", "search_placeholder": "Пошук акордів або пісень...",
        "searching": "Пошук...", "found_chords": "Знайдені акорди",
        "found_songs": "Знайдені пісні", "tonality": "Тональність",
        "unknown_artist": "Невідомий", "untitled": "Без назви",
        "navigation_error": "Помилка навігації",
        "chords_not_found": "Екран акордів не знайдено", "song_not_found": "Екран пісні не знайдено",
        "chord_not_found": "Акорд не знайдено",
    },

    # ============================================================
    # ҚАЗАҚША (kk)
    # ============================================================
    "kk": {
        "home": "Басты бет", "songs": "Әндер", "chords": "Аккордтар", "tuner": "Тюнер",
        "metronome": "Метроном", "favorites": "Таңдаулылар", "dictionary": "Сөздік",
        "profile": "Профиль", "settings": "Баптаулар", "help": "Көмек",
        "promo": "Промокод", "feedback": "Кері байланыс", "admin": "Админ",

        "search": "Іздеу", "find": "Табу", "theme": "Тақырып", "language": "Тіл",
        "avatar": "Аватар", "apply_changes": "Өзгерістерді сақтау", "changes_saved": "Баптаулар сақталды",
        "theme_green": "Жасыл", "theme_light": "Ашық", "theme_dark": "Қараңғы",
        "loading": "Жүктелуде...", "min_chars": "Кемінде 2 таңба енгізіңіз",
        "selected_lang": "Таңдалды", "lang_ru": "Орысша", "lang_en": "Ағылшынша",
        "lang_digits": "0-9", "load_error": "Әнді жүктеу қатесі",
        "close": "Жабу", "cancel": "Бас тарту", "ok": "ОК", "apply": "Қолдану",
        "yes": "Иә", "no": "Жоқ", "retry": "Қайталау",
        "page_of": "{current} / {total} бет",

        "search_chord": "Аккорд іздеу", "search_found": "Аккорд табылды",
        "search_not_found": "Ештеңе табылмады", "no_variants": "Басқа нұсқалар жоқ",
        "variant": "Нұсқа", "no_chords": "Қолжетімді аккордтар жоқ",
        "choose_chord": "Аккордты таңдаңыз", "choose_tonality": "Тональдікті таңдаңыз",
        "choose_type": "Аккорд түрін таңдаңыз", "mode_notes": "Ноталар режимі",
        "mode_fingers": "Саусақ қою режимі",

        "search_artists": "Орындаушыларды әліпби бойынша іздеу",
        "search_results": "Іздеу нәтижелері", "artist_songs": "Орындаушы әндері",
        "no_artists": "Орындаушылар жоқ", "artists": "Орындаушылар", "of": "/",
        "songs_found": "Табылған әндер", "nothing_found": "Ештеңе табылмады",
        "search_error": "Іздеу қатесі\nИнтернетті тексеріңіз",
        "loading_error": "Жүктеу қатесі\nИнтернетті тексеріңіз",
        "loading_songs": "Әндер жүктелуде...",
        "no_artist_songs": "Бұл орындаушының әндері жоқ",
        "tap_letter_to_retry": "Қайталау үшін әріпті басыңыз",

        "in_tune": "БАПТАЛДЫ!", "in_tune_label": "БАПТАЛДЫ",
        "cents": "цент", "listening": "Тыңдалуда...", "low": "ТӨМЕН", "high": "ЖОҒАРЫ",
        "guitar": "🎸 Гитара", "bass": "🎸 Бас", "ukulele": "🎵 Укулеле",
        "choose_tuning": "Бұрауды таңдаңыз", "tuning": "Бұрау",
        "audio_not_init": "Аудио іске қосылмаған",
        "tuning_standard_6": "Стандартты", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Жарты тон төмен",
        "tuning_bass_4": "4 ішекті бас", "tuning_bass_5": "5 ішекті бас",
        "tuning_ukulele": "Укулеле",

        "auth_required_title": "Авторизация қажет",
        "auth_required_message": "Таңдаулы әндерді көру үшін\nаккаунтқа кіріңіз",
        "no_songs": "Әндер жоқ", "song_one": "ән", "songs_many": "ән",
        "no_favorites": "Таңдаулы әндер жоқ", "loading_favorites": "Таңдаулылар жүктелуде...",
        "remove_from_favorites": "Таңдаулылардан өшіру керек пе?",
        "favorite_added": "Таңдаулыларға қосылды",
        "favorite_removed": "Таңдаулылардан өшірілді", "favorite_error": "Таңдаулылар қатесі",

        "reset": "Қалпына келтіру", "accent": "Екпін", "on": "ҚОСУ", "off": "ӨШІРУ",
        "started": "Қосылды", "stopped": "Тоқтатылды", "audio_error": "Дыбыс қатесі",
        "sub_none": "Жоқ", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Механикалық", "tone_electronic": "Электронды",
        "tone_wood": "Ағаш", "tone_click": "Шерту", "tone_beep": "Сигнал",

        "search_terms": "Терминдерді іздеу", "search_by_alphabet": "Әліпби бойынша іздеу",
        "terms_by_letter": "Әріп бойынша терминдер", "no_terms_for_letter": "Терминдер жоқ",
        "found_terms": "Табылған терминдер", "term_not_found": "Термин табылмады",

        "what_to_search": "Не іздейміз?", "search_placeholder": "Аккордтар мен әндерді іздеу...",
        "searching": "Ізделуде...", "found_chords": "Табылған аккордтар",
        "found_songs": "Табылған әндер", "tonality": "Тональдік",
        "unknown_artist": "Белгісіз", "untitled": "Атаусыз",
        "navigation_error": "Навигация қатесі",
        "chords_not_found": "Аккордтар экраны табылмады", "song_not_found": "Ән экраны табылмады",
        "chord_not_found": "Аккорд табылмады",
    },

    # ============================================================
    # TÜRKÇE (tr)
    # ============================================================
    "tr": {
        "home": "Ana Sayfa", "songs": "Şarkılar", "chords": "Akorlar", "tuner": "Akort",
        "metronome": "Metronom", "favorites": "Favoriler", "dictionary": "Sözlük",
        "profile": "Profil", "settings": "Ayarlar", "help": "Yardım",
        "promo": "Promosyon", "feedback": "Geri Bildirim", "admin": "Yönetici",

        "search": "Ara", "find": "Bul", "theme": "Tema", "language": "Dil",
        "avatar": "Avatar", "apply_changes": "Değişiklikleri uygula", "changes_saved": "Ayarlar kaydedildi",
        "theme_green": "Yeşil", "theme_light": "Açık", "theme_dark": "Koyu",
        "loading": "Yükleniyor...", "min_chars": "En az 2 karakter girin",
        "selected_lang": "Seçildi", "lang_ru": "Rusça", "lang_en": "İngilizce",
        "lang_digits": "0-9", "load_error": "Şarkı yüklenemedi",
        "close": "Kapat", "cancel": "İptal", "ok": "Tamam", "apply": "Uygula",
        "yes": "Evet", "no": "Hayır", "retry": "Tekrar dene",
        "page_of": "Sayfa {current} / {total}",

        "search_chord": "Akor ara", "search_found": "Akor bulundu",
        "search_not_found": "Hiçbir şey bulunamadı", "no_variants": "Başka varyant yok",
        "variant": "Varyant", "no_chords": "Mevcut akor yok",
        "choose_chord": "Akor seçin", "choose_tonality": "Ton seçin",
        "choose_type": "Akor türü seçin", "mode_notes": "Nota modu seçildi",
        "mode_fingers": "Parmak modu seçildi",

        "search_artists": "Sanatçıları alfabetik ara",
        "search_results": "Arama sonuçları", "artist_songs": "Sanatçının şarkıları",
        "no_artists": "Sanatçı yok", "artists": "Sanatçılar", "of": "/",
        "songs_found": "Bulunan şarkılar", "nothing_found": "Hiçbir şey bulunamadı",
        "search_error": "Arama hatası\nBağlantıyı kontrol edin",
        "loading_error": "Yükleme hatası\nBağlantıyı kontrol edin",
        "loading_songs": "Şarkılar yükleniyor...",
        "no_artist_songs": "Bu sanatçının şarkısı yok",
        "tap_letter_to_retry": "Tekrar denemek için harfe dokunun",

        "in_tune": "AKORT TAMAM!", "in_tune_label": "TAMAM",
        "cents": "cent", "listening": "Dinleniyor...", "low": "PES", "high": "TİZ",
        "guitar": "🎸 Gitar", "bass": "🎸 Bas", "ukulele": "🎵 Ukulele",
        "choose_tuning": "Akort düzeni seç", "tuning": "Akort",
        "audio_not_init": "Ses başlatılmadı",
        "tuning_standard_6": "Standart", "tuning_drop_d": "Drop D",
        "tuning_open_g": "Open G", "tuning_open_d": "Open D",
        "tuning_dadgad": "DADGAD", "tuning_half_step_down": "Yarım ton pes",
        "tuning_bass_4": "4 telli bas", "tuning_bass_5": "5 telli bas",
        "tuning_ukulele": "Ukulele",

        "auth_required_title": "Giriş gerekli",
        "auth_required_message": "Favori parçalarınızı görmek için\ngiriş yapmalısınız",
        "no_songs": "Şarkı yok", "song_one": "şarkı", "songs_many": "şarkı",
        "no_favorites": "Favori şarkı yok", "loading_favorites": "Favoriler yükleniyor...",
        "remove_from_favorites": "Favorilerden kaldırılsın mı?",
        "favorite_added": "Favorilere eklendi",
        "favorite_removed": "Favorilerden çıkarıldı", "favorite_error": "Favori hatası",

        "reset": "Sıfırla", "accent": "Vurgu", "on": "AÇIK", "off": "KAPALI",
        "started": "Başlatıldı", "stopped": "Durduruldu", "audio_error": "Ses hatası",
        "sub_none": "Yok", "sub_eighth": "1/8", "sub_triplet": "1/8T", "sub_sixteenth": "1/16",
        "tone_mechanical": "Mekanik", "tone_electronic": "Elektronik",
        "tone_wood": "Ahşap", "tone_click": "Tık", "tone_beep": "Bip",

        "search_terms": "Terim ara", "search_by_alphabet": "Alfabetik arama",
        "terms_by_letter": "Harfe göre terimler", "no_terms_for_letter": "Terim bulunamadı",
        "found_terms": "Bulunan terimler", "term_not_found": "Terim bulunamadı",

        "what_to_search": "Ne arayalım?", "search_placeholder": "Akor veya şarkı ara...",
        "searching": "Aranıyor...", "found_chords": "Bulunan akorlar",
        "found_songs": "Bulunan şarkılar", "tonality": "Tonalite",
        "unknown_artist": "Bilinmeyen", "untitled": "İsimsiz",
        "navigation_error": "Gezinme hatası",
        "chords_not_found": "Akor ekranı bulunamadı", "song_not_found": "Şarkı ekranı bulunamadı",
        "chord_not_found": "Akor bulunamadı",
    },
}


def get_text(key, default=None):
    """Возвращает перевод по ключу для текущего языка с фолбэком на en и ru."""
    lang = settings_manager.language
    if lang not in TRANSLATIONS:
        lang = 'ru'

    text = TRANSLATIONS[lang].get(key)
    if text is None:
        text = TRANSLATIONS['en'].get(key)
    if text is None:
        text = TRANSLATIONS['ru'].get(key, default if default else key)
    return text


def format_text(key, default=None, **kwargs):
    """
    Возвращает перевод с подстановкой {placeholder}.
    Пример: format_text('page_of', current=3, total=25)
    """
    text = get_text(key, default)
    try:
        return text.format(**kwargs)
    except Exception:
        return text


def get_available_languages():
    """Список всех 12 поддерживаемых языков."""
    return list(TRANSLATIONS.keys())