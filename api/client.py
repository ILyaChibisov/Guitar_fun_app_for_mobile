# api/client.py
"""
HTTP клиент для работы с сервером - с кэшированием избранного и текстов песен
ОПТИМИЗИРОВАННАЯ ВЕРСИЯ
"""
import json
import os
import threading
import http.server
import socketserver
import urllib.parse
import webbrowser
import warnings
import time
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from config.app_config import config
from api.ssl_config import get_requests_session

# Отключаем предупреждения SSL
warnings.filterwarnings("ignore", category=Warning)
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============ Локальный сервер для OAuth callback ============

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    tokens = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        access_token = query.get('access_token', [None])[0]
        refresh_token = query.get('refresh_token', [None])[0]

        if access_token:
            OAuthCallbackHandler.tokens = {
                'access_token': access_token,
                'refresh_token': refresh_token
            }
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <html>
            <body style="text-align:center; padding:50px; font-family:sans-serif;">
            <h2>✅ Авторизация успешна!</h2>
            <p>Можете закрыть это окно и вернуться в приложение.</p>
            <script>setTimeout(window.close, 2000);</script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <html>
            <body style="text-align:center; padding:50px;font-family:sans-serif;">
            <h2>🔄 Авторизация...</h2>
            <p>Подождите, идёт обработка...</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        pass


class OAuthServer:
    _instance = None
    port = 8080

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.server = None
        self.thread = None
        self.callback_received = threading.Event()

    def start(self):
        if self.server:
            return
        handler = OAuthCallbackHandler
        self.server = socketserver.TCPServer(("127.0.0.1", self.port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        Logger.info(f"OAuth сервер запущен на порту {self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server = None
            Logger.info("OAuth сервер остановлен")

    def get_tokens(self):
        tokens = OAuthCallbackHandler.tokens
        OAuthCallbackHandler.tokens = None
        return tokens


oauth_server = OAuthServer()


class APIClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.access_token = None
        self.refresh_token = None
        self.user_data = None
        self.config = config
        self.waiting_for_callback = False

        # Кэш в памяти для быстрого доступа
        self._favorites_cache = None
        self._favorites_cache_timestamp = 0

        # Иконка
        self._icon_texture = None

        # Создаем сессию
        self.session = get_requests_session()
        self.session.headers.update({
            'User-Agent': 'GuitarFuns/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })

        self._load_tokens()

    # ============ AUTH TOKENS ============

    def _load_tokens(self):
        try:
            store = JsonStore('auth.json')
            if store.exists('tokens'):
                self.access_token = store.get('tokens')['access_token']
                self.refresh_token = store.get('tokens')['refresh_token']
                Logger.info('API: Токены загружены')
        except Exception as e:
            Logger.debug(f'API: Нет сохранённых токенов - {e}')

    def _save_tokens(self):
        try:
            store = JsonStore('auth.json')
            store.put('tokens', access_token=self.access_token, refresh_token=self.refresh_token)
            Logger.info('API: Токены сохранены')
        except Exception as e:
            Logger.error(f'API: Ошибка сохранения токенов - {e}')

    def _clear_tokens(self):
        try:
            store = JsonStore('auth.json')
            if store.exists('tokens'):
                store.delete('tokens')
            self.access_token = None
            self.refresh_token = None
            self.user_data = None
            self.clear_cache()
            Logger.info('API: Токены очищены')
        except Exception as e:
            Logger.error(f'API: Ошибка очистки токенов - {e}')

    def _get_headers(self, include_auth=True):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if include_auth and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    # ============ ЗАПРОСЫ ============

    def _request_sync(self, url, method='GET', data=None, include_auth=True):
        """Синхронный запрос"""
        headers = self._get_headers(include_auth)
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=config.CONNECTION_TIMEOUT)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=config.CONNECTION_TIMEOUT)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers, timeout=config.CONNECTION_TIMEOUT)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=config.CONNECTION_TIMEOUT)
            else:
                response = self.session.request(method, url, json=data, headers=headers,
                                                timeout=config.CONNECTION_TIMEOUT)
            response.raise_for_status()

            if not response.content or response.content.strip() == b'':
                Logger.warning(f"API: Пустой ответ от {url}")
                return {"artists": [], "total": 0}

            return response.json() if response.content else {"artists": [], "total": 0}
        except Exception as e:
            Logger.error(f'API: Ошибка запроса - {e}')
            return {"artists": [], "total": 0}

    def _request_async(self, url, method='GET', data=None, on_success=None, on_failure=None, include_auth=True):
        """Асинхронный запрос"""

        def worker():
            try:
                result = self._request_sync(url, method, data, include_auth)
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)
            except Exception as e:
                error_msg = str(e)
                if on_failure:
                    Clock.schedule_once(lambda dt: on_failure(None, error_msg), 0)
                else:
                    Logger.error(f'API: Ошибка - {error_msg}')

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def _request(self, url, method='GET', data=None, on_success=None, on_failure=None, include_auth=True):
        return self._request_async(url, method, data, on_success, on_failure, include_auth)

    # ============ КЭШ ИЗБРАННОГО ============

    def _get_favorites_cache_path(self):
        """Возвращает путь к файлу кэша избранного"""
        cache_dir = config.CACHE_DIR
        user_id = self.user_data.get('id', 'guest') if self.user_data else 'guest'
        return os.path.join(cache_dir, f'favorites_{user_id}.json')

    def _load_favorites_cache(self):
        """Загружает кэш избранного из памяти или файла"""
        # Сначала проверяем память
        if self._favorites_cache is not None:
            if time.time() - self._favorites_cache_timestamp < config.FAVORITES_CACHE_TTL:
                Logger.debug(f"📦 Избранное из памяти: {len(self._favorites_cache)} песен")
                return self._favorites_cache
            else:
                Logger.debug("⏳ Кэш в памяти устарел")

        # Пробуем загрузить из файла
        try:
            cache_path = self._get_favorites_cache_path()
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if time.time() - data.get('timestamp', 0) < config.FAVORITES_CACHE_TTL:
                        favorites = data.get('favorites', [])
                        self._favorites_cache = favorites
                        self._favorites_cache_timestamp = data.get('timestamp', 0)
                        Logger.info(f"📦 Избранное из файла: {len(favorites)} песен")
                        return favorites
        except Exception as e:
            Logger.error(f"❌ Ошибка загрузки кэша: {e}")

        return None

    def _save_favorites_cache(self, favorites):
        """Сохраняет кэш избранного в память и файл"""
        try:
            self._favorites_cache = favorites
            self._favorites_cache_timestamp = time.time()

            cache_path = self._get_favorites_cache_path()
            data = {
                'favorites': favorites,
                'timestamp': time.time()
            }

            cache_dir = os.path.dirname(cache_path)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, mode=0o755)

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            Logger.info(f"💾 Кэш избранного сохранён: {len(favorites)} песен")
        except Exception as e:
            Logger.error(f"❌ Ошибка сохранения кэша избранного: {e}")

    def _clear_favorites_cache(self):
        """Очищает кэш избранного (память + файл)"""
        self._favorites_cache = None
        self._favorites_cache_timestamp = 0
        try:
            cache_path = self._get_favorites_cache_path()
            if os.path.exists(cache_path):
                os.remove(cache_path)
                Logger.info("🗑️ Кэш избранного очищен")
        except Exception as e:
            Logger.error(f"❌ Ошибка очистки кэша избранного: {e}")

    # ============ КЭШ ТЕКСТОВ ПЕСЕН ============

    def _get_song_cache_path(self, song_id):
        """Возвращает путь к файлу кэша текста песни"""
        cache_dir = config.CACHE_DIR
        return os.path.join(cache_dir, f'song_{song_id}.json')

    def _load_song_cache(self, song_id):
        """Загружает текст песни из кэша"""
        try:
            cache_path = self._get_song_cache_path(song_id)
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if time.time() - data.get('timestamp', 0) < config.SONG_CACHE_TTL:
                        Logger.info(f"📦 Текст песни {song_id} загружен из кэша")
                        return data.get('data')
                    else:
                        Logger.info(f"⏳ Кэш песни {song_id} устарел")
                        os.remove(cache_path)
        except Exception as e:
            Logger.error(f"❌ Ошибка загрузки кэша песни {song_id}: {e}")
        return None

    def _save_song_cache(self, song_id, data):
        """Сохраняет текст песни в кэш"""
        try:
            cache_dir = config.CACHE_DIR
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir, mode=0o755)

            song_files = [f for f in os.listdir(cache_dir) if f.startswith('song_') and f.endswith('.json')]

            if len(song_files) >= config.MAX_CACHED_SONGS:
                song_files.sort(key=lambda f: os.path.getmtime(os.path.join(cache_dir, f)))
                to_delete = song_files[:len(song_files) // 2]
                for f in to_delete:
                    try:
                        os.remove(os.path.join(cache_dir, f))
                        Logger.info(f"🗑️ Удален старый кэш: {f}")
                    except:
                        pass

            cache_path = self._get_song_cache_path(song_id)
            cache_data = {
                'data': data,
                'timestamp': time.time(),
                'song_id': song_id
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            Logger.info(f"💾 Текст песни {song_id} сохранён в кэш")
        except Exception as e:
            Logger.error(f"❌ Ошибка сохранения кэша песни {song_id}: {e}")

    def _clear_song_cache(self, song_id=None):
        """Очищает кэш песен (одной или всех)"""
        try:
            cache_dir = config.CACHE_DIR
            if not os.path.exists(cache_dir):
                return

            if song_id:
                cache_path = self._get_song_cache_path(song_id)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    Logger.info(f"🗑️ Кэш песни {song_id} очищен")
            else:
                count = 0
                for f in os.listdir(cache_dir):
                    if f.startswith('song_') and f.endswith('.json'):
                        os.remove(os.path.join(cache_dir, f))
                        count += 1
                Logger.info(f"🗑️ Кэш всех песен очищен: {count} файлов")
        except Exception as e:
            Logger.error(f"❌ Ошибка очистки кэша песен: {e}")

    def clear_cache(self):
        """Очищает весь кэш"""
        self._clear_favorites_cache()
        self._clear_song_cache()
        Logger.info("🗑️ Весь кэш очищен")

    # ============ API МЕТОДЫ ============

    def get_favorites(self, on_success=None, on_failure=None, force_refresh=False):
        """
        Получить избранное с кэшированием

        Args:
            on_success: колбэк при успехе
            on_failure: колбэк при ошибке
            force_refresh: принудительно обновить с сервера
        """
        if not force_refresh:
            cached = self._load_favorites_cache()
            if cached is not None:
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
                return

        Logger.info("🔄 Загрузка избранного с сервера...")

        def _on_success(result):
            if isinstance(result, dict):
                favorites = result.get('favorites', result.get('songs', []))
            elif isinstance(result, list):
                favorites = result
            else:
                favorites = []

            formatted_favorites = []
            for item in favorites:
                if isinstance(item, str):
                    parts = item.split(' - ', 1)
                    if len(parts) == 2:
                        formatted_favorites.append({
                            'artist': parts[0],
                            'title': parts[1],
                            'tabs_count': 1,
                            'id': 0,
                            'song_id': 0
                        })
                    else:
                        formatted_favorites.append({
                            'artist': '',
                            'title': item,
                            'tabs_count': 1,
                            'id': 0,
                            'song_id': 0
                        })
                else:
                    if 'id' in item and 'song_id' not in item:
                        item['song_id'] = item['id']
                    elif 'song_id' in item and 'id' not in item:
                        item['id'] = item['song_id']
                    formatted_favorites.append(item)

            self._save_favorites_cache(formatted_favorites)
            Logger.info(f'✅ Получено избранных: {len(formatted_favorites)}')

            if on_success:
                on_success(formatted_favorites)

        def _on_failure(req, error):
            cached = self._load_favorites_cache()
            if cached is not None:
                Logger.warning(f"⚠️ Ошибка сервера, показываем устаревший кэш ({len(cached)} песен)")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
                return

            if on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/favorites",
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=True
        )

    def add_to_favorites(self, song_id: int, on_success=None, on_failure=None):
        """Добавить в избранное с обновлением кэша"""

        def _on_success(result):
            self._clear_favorites_cache()

            if not self._load_song_cache(song_id):
                def cache_song():
                    self.get_tab(
                        song_id=song_id,
                        on_success=lambda x: Logger.info(f"📦 Песня {song_id} закэширована при добавлении"),
                        on_failure=lambda x, y: Logger.warning(f"⚠️ Не удалось закэшировать песню {song_id}")
                    )

                threading.Thread(target=cache_song, daemon=True).start()

            Logger.info(f"⭐ Песня {song_id} добавлена в избранное, кэш очищен")
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='POST',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def remove_from_favorites(self, song_id: int, on_success=None, on_failure=None):
        """Удалить из избранного с обновлением кэша"""

        def _on_success(result):
            self._clear_favorites_cache()
            Logger.info(f"⭐ Песня {song_id} удалена из избранного, кэш очищен")
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='DELETE',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def is_song_favorited(self, song_id: int) -> bool:
        """
        Проверяет, находится ли песня в избранном (из кэша)
        """
        cached = self._load_favorites_cache()
        if cached is None:
            return False

        for song in cached:
            if song.get('id') == song_id or song.get('song_id') == song_id:
                return True
            if str(song.get('id', '')) == str(song_id) or str(song.get('song_id', '')) == str(song_id):
                return True
        return False

    def get_tab(self, song_id: int, on_success=None, on_failure=None, force_refresh=False):
        """
        Получить текст песни с кэшированием
        """
        if not force_refresh:
            cached = self._load_song_cache(song_id)
            if cached is not None:
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
                return

        Logger.info(f"🔄 Загрузка песни {song_id} с сервера...")

        def _on_success(result):
            self._save_song_cache(song_id, result)
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            cached = self._load_song_cache(song_id)
            if cached is not None:
                Logger.warning(f"⚠️ Ошибка сервера, показываем устаревший кэш песни {song_id}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
                return

            if on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}",
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=False
        )

    # ============ API МЕТОДЫ (без кэша) ============

    def get_alphabet(self, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/alphabet",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_artists_by_letter(self, letter: str, limit: int = 200, offset: int = 0,
                              on_success=None, on_failure=None):
        encoded_letter = self._encode_letter(letter)
        url = f"{self.config.API_BASE_URL}/songs/artists/{encoded_letter}?limit={limit}&offset={offset}"
        Logger.info(f"Запрос артистов для буквы: {letter}")
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=False)

    def get_artists_by_digits(self, limit: int = 200, offset: int = 0,
                              on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/songs/artists/digits?limit={limit}&offset={offset}"
        Logger.info("Запрос артистов для цифр")
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=False)

    def get_songs_by_artist(self, artist: str, limit: int = 200, offset: int = 0,
                            on_success=None, on_failure=None):
        encoded_artist = urllib.parse.quote(artist, safe='')
        url = f"{self.config.API_BASE_URL}/songs/{encoded_artist}?limit={limit}&offset={offset}"
        Logger.info(f"Запрос песен для артиста: {artist}")
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=False)

    def get_popular_songs(self, limit: int = 20, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/popular?limit={limit}",
            method='GET', on_success=on_success, on_failure=on_failure, include_auth=False
        )

    def toggle_like(self, song_id: int, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/like",
            method='POST', on_success=on_success, on_failure=on_failure, include_auth=True
        )

    def search_songs(self, query: str, limit: int = 30, offset: int = 0, on_success=None, on_failure=None):
        encoded_query = urllib.parse.quote(query, safe='')
        url = f"{self.config.API_BASE_URL}/songs/search?q={encoded_query}&limit={limit}&offset={offset}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=False)

    def search_songs_sync(self, query: str, limit: int = 20, offset: int = 0):
        encoded_query = urllib.parse.quote(query, safe='')
        url = f"{self.config.API_BASE_URL}/songs/search?q={encoded_query}&limit={limit}&offset={offset}"
        try:
            Logger.info(f"🔍 Синхронный поиск: {query}")
            response = self.session.get(url, timeout=config.CONNECTION_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"❌ Ошибка синхронного поиска: {e}")
            return {"results": [], "total": 0}

    # ============ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ============

    def _encode_letter(self, letter: str) -> str:
        import urllib.parse
        special_chars = {
            'Ё': '%D0%81',
            'ё': '%D1%91',
            'Ы': '%D0%AB',
            'ы': '%D1%8B',
            'Ь': '%D0%AC',
            'ь': '%D1%8C',
            'Ъ': '%D0%AA',
            'ъ': '%D1%8A',
            '#': '%23',
            ' ': '%20',
        }
        if letter in special_chars:
            return special_chars[letter]
        try:
            return urllib.parse.quote(letter, safe='')
        except Exception as e:
            Logger.error(f"Ошибка кодирования буквы {letter}: {e}")
            return letter

    # ============ AUTH METHODS ============

    def register(self, username, email, password, full_name=None, on_success=None, on_failure=None):
        data = {'username': username, 'email': email, 'password': password}
        if full_name:
            data['full_name'] = full_name

        def worker():
            try:
                response = self.session.post(
                    config.API_AUTH_REGISTER, json=data,
                    headers=self._get_headers(include_auth=False), timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json() if response.content else None
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)
            except Exception as e:
                if on_failure:
                    Clock.schedule_once(lambda dt: on_failure(None, str(e)), 0)

        threading.Thread(target=worker, daemon=True).start()

    def login(self, username, password, on_success=None, on_failure=None):
        data = urllib.parse.urlencode({'username': username, 'password': password})

        def _on_success(result):
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
            self._save_tokens()
            if on_success:
                on_success(result)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        def worker():
            try:
                response = self.session.post(config.API_AUTH_LOGIN, data=data, headers=headers,
                                             timeout=config.CONNECTION_TIMEOUT)
                response.raise_for_status()
                result = response.json()
                Clock.schedule_once(lambda dt: _on_success(result), 0)
            except Exception as e:
                if on_failure:
                    Clock.schedule_once(lambda dt: on_failure(None, str(e)), 0)

        threading.Thread(target=worker, daemon=True).start()

    def google_login(self, on_success=None, on_failure=None):
        self.waiting_for_callback = True
        oauth_server.start()
        redirect_uri = f"http://127.0.0.1:{oauth_server.port}/callback"
        auth_url = f"{self.config.API_BASE_URL}/auth/google/login?redirect_uri={urllib.parse.quote(redirect_uri)}"
        webbrowser.open(auth_url)
        self._check_callback_interval = Clock.schedule_interval(lambda dt: self._check_callback(on_success, on_failure),
                                                                1)

    def _check_callback(self, on_success, on_failure):
        if not self.waiting_for_callback:
            return False
        tokens = oauth_server.get_tokens()
        if tokens and tokens.get('access_token'):
            self.waiting_for_callback = False
            Clock.unschedule(self._check_callback_interval)
            self.access_token = tokens['access_token']
            self.refresh_token = tokens.get('refresh_token')
            self._save_tokens()
            self.get_current_user(on_success=on_success, on_failure=on_failure)
            return False
        return True

    def logout(self, on_success=None, on_failure=None):
        def _on_success(result):
            self._clear_tokens()
            self.clear_cache()
            if on_success:
                on_success(result)

        if not self.refresh_token:
            self._clear_tokens()
            if on_success:
                on_success({})
            return
        url = f"{self.config.API_AUTH_LOGOUT}?refresh_token={self.refresh_token}"
        return self._request(url=url, method='POST', on_success=_on_success, on_failure=on_failure, include_auth=False)

    def get_current_user(self, on_success=None, on_failure=None):
        def worker():
            try:
                response = self.session.get(config.API_USER_ME, headers=self._get_headers(include_auth=True),
                                            timeout=config.CONNECTION_TIMEOUT)
                response.raise_for_status()
                result = response.json()
                self.user_data = result
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)
            except Exception as e:
                if on_failure:
                    Clock.schedule_once(lambda dt: on_failure(None, str(e)), 0)

        threading.Thread(target=worker, daemon=True).start()

    def is_authenticated(self):
        return self.access_token is not None and self.user_data is not None

    def is_admin(self):
        if not self.user_data:
            return False
        return self.user_data.get('role') == 'admin'

    def get_letters_sync(self):
        url = f"{self.config.API_BASE_URL}/songs/alphabet"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка получения букв: {e}")
            return None


api = APIClient()