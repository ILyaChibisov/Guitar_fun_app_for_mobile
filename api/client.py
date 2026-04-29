# api/client.py
"""
HTTP клиент для работы с сервером с поддержкой пагинации
"""
import json
import threading
import http.server
import socketserver
import urllib.parse
import webbrowser
import requests
import warnings
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from config.app_config import config
from api.ssl_config import get_requests_session
import time

# Отключаем предупреждения SSL
warnings.filterwarnings("ignore", category=Warning)

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============ Локальный сервер для OAuth callback ============

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик callback от Google OAuth"""
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
    """Локальный сервер для приёма Google OAuth callback"""
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
        self.is_loading_complete = False
        self.loading_progress = 0

        # Кэш для страниц
        self.cache = {
            'alphabet': None,
            'artists': {},      # {letter: {page: artists_data, total: total, page_size: 50}}
            'songs': {},        # {artist: {page: songs_data, total: total, page_size: 50}}
            'popular': None,
            'favorites': None
        }

        # Создаем сессию
        self.session = get_requests_session()
        self.session.headers.update({
            'User-Agent': 'GuitarFuns/1.0',
            'Accept': 'application/json'
        })

        self._load_tokens()

    # ============ МЕТОДЫ КЭШИРОВАНИЯ ============

    def _cache_artists_page(self, letter, page, data, total):
        """Кэширует страницу исполнителей"""
        if letter not in self.cache['artists']:
            self.cache['artists'][letter] = {}
        self.cache['artists'][letter][page] = {
            'data': data,
            'total': total,
            'timestamp': time.time()
        }

    def _get_cached_artists_page(self, letter, page):
        """Получает страницу исполнителей из кэша"""
        if letter in self.cache['artists'] and page in self.cache['artists'][letter]:
            return self.cache['artists'][letter][page]
        return None

    def _cache_songs_page(self, artist, page, data, total):
        """Кэширует страницу песен"""
        if artist not in self.cache['songs']:
            self.cache['songs'][artist] = {}
        self.cache['songs'][artist][page] = {
            'data': data,
            'total': total,
            'timestamp': time.time()
        }

    def _get_cached_songs_page(self, artist, page):
        """Получает страницу песен из кэша"""
        if artist in self.cache['songs'] and page in self.cache['songs'][artist]:
            return self.cache['songs'][artist][page]
        return None

    def clear_cache(self):
        """Очищает кэш"""
        self.cache = {
            'alphabet': None,
            'artists': {},
            'songs': {},
            'popular': None,
            'favorites': None
        }
        Logger.info("🗑️ Кэш очищен")

    # ============ AUTH METHODS ============

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

    def _request_sync(self, url, method='GET', data=None, include_auth=True):
        """Синхронный запрос"""
        headers = self._get_headers(include_auth)

        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=config.CONNECTION_TIMEOUT)
            elif method == 'POST':
                if data and isinstance(data, dict):
                    response = self.session.post(url, json=data, headers=headers, timeout=config.CONNECTION_TIMEOUT)
                else:
                    response = self.session.post(url, data=data, headers=headers, timeout=config.CONNECTION_TIMEOUT)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers, timeout=config.CONNECTION_TIMEOUT)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=config.CONNECTION_TIMEOUT)
            else:
                response = self.session.request(method, url, json=data, headers=headers,
                                                timeout=config.CONNECTION_TIMEOUT)

            response.raise_for_status()
            return response.json() if response.content else None

        except requests.exceptions.SSLError as e:
            Logger.error(f'API: SSL ошибка - {e}')
            raise Exception(f"SSL error: {e}")
        except requests.exceptions.ConnectionError as e:
            Logger.error(f'API: Ошибка соединения - {e}')
            raise Exception(f"Connection error: {e}")
        except requests.exceptions.Timeout as e:
            Logger.error(f'API: Таймаут - {e}')
            raise Exception(f"Timeout: {e}")
        except requests.exceptions.HTTPError as e:
            Logger.error(f'API: HTTP ошибка {e.response.status_code}')
            raise Exception(f"HTTP {e.response.status_code}")
        except Exception as e:
            Logger.error(f'API: Ошибка запроса - {e}')
            raise

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

    # ============ API МЕТОДЫ ============

    def get_alphabet(self, on_success=None, on_failure=None, force_refresh=False):
        """Получить алфавит"""

        if not force_refresh and self.cache['alphabet'] is not None:
            if on_success:
                Clock.schedule_once(lambda dt: on_success(self.cache['alphabet']), 0)
            return

        def _on_success(result):
            self.cache['alphabet'] = result
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/alphabet",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_artists_by_letter(self, letter: str, limit: int = 50, offset: int = 0,
                              on_success=None, on_failure=None, force_refresh=False):
        """Получить исполнителей по букве с пагинацией"""

        page = offset // limit if limit > 0 else 0

        # Проверяем кэш
        if not force_refresh:
            cached = self._get_cached_artists_page(letter, page)
            if cached:
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached['data']), 0)
                return

        import urllib.parse
        encoded_letter = urllib.parse.quote(letter, safe='')
        url = f"{self.config.API_BASE_URL}/songs/artists/{encoded_letter}?limit={limit}&offset={offset}"

        def _on_success(result):
            # Сохраняем в кэш
            artists = result.get('artists', [])
            total = result.get('total', 0)
            self._cache_artists_page(letter, page, result, total)
            if on_success:
                on_success(result)

        return self._request(
            url=url,
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_artists_by_digits(self, limit: int = 50, offset: int = 0,
                              on_success=None, on_failure=None, force_refresh=False):
        """Получить исполнителей для цифр (0-9) с пагинацией"""

        page = offset // limit if limit > 0 else 0
        cache_key = "digits"

        if not force_refresh:
            cached = self._get_cached_artists_page(cache_key, page)
            if cached:
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached['data']), 0)
                return

        url = f"{self.config.API_BASE_URL}/songs/artists/digits?limit={limit}&offset={offset}"

        def _on_success(result):
            self._cache_artists_page(cache_key, page, result, result.get('total', 0))
            if on_success:
                on_success(result)

        return self._request(
            url=url,
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_songs_by_artist(self, artist: str, limit: int = 50, offset: int = 0,
                            on_success=None, on_failure=None, force_refresh=False):
        """Получить песни исполнителя с пагинацией"""

        page = offset // limit if limit > 0 else 0

        if not force_refresh:
            cached = self._get_cached_songs_page(artist, page)
            if cached:
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached['data']), 0)
                return

        import urllib.parse
        encoded_artist = urllib.parse.quote(artist, safe='')
        url = f"{self.config.API_BASE_URL}/songs/{encoded_artist}?limit={limit}&offset={offset}"
        Logger.info(f"🔍 Запрос песен для: {artist}")
        Logger.info(f"🔍 URL: {url}")

        def _on_success(result):
            self._cache_songs_page(artist, page, result, result.get('total', 0))
            if on_success:
                on_success(result)

        return self._request(
            url=url,
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_tab(self, song_id: int, on_success=None, on_failure=None):
        """Получить текст песни"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_popular_songs(self, limit: int = 20, on_success=None, on_failure=None, force_refresh=False):
        """Получить популярные песни"""

        if not force_refresh and self.cache['popular'] is not None:
            if on_success:
                Clock.schedule_once(lambda dt: on_success(self.cache['popular']), 0)
            return

        def _on_success(result):
            self.cache['popular'] = result
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/popular?limit={limit}",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_favorites(self, on_success=None, on_failure=None, force_refresh=False):
        """Получить избранное"""

        if not force_refresh and self.cache['favorites'] is not None:
            if on_success:
                Clock.schedule_once(lambda dt: on_success(self.cache['favorites']), 0)
            return

        def _on_success(result):
            self.cache['favorites'] = result
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/favorites",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def add_to_favorites(self, song_id: int, on_success=None, on_failure=None):
        """Добавить в избранное"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def remove_from_favorites(self, song_id: int, on_success=None, on_failure=None):
        """Удалить из избранного"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='DELETE',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def toggle_like(self, song_id: int, on_success=None, on_failure=None):
        """Переключить лайк"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/like",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    # ============ ПОИСК ============

    def search_songs(self, query: str, limit: int = 30, offset: int = 0,
                     on_success=None, on_failure=None):
        """Поиск песен с пагинацией"""
        import urllib.parse
        encoded_query = urllib.parse.quote(query, safe='')
        url = f"{self.config.API_BASE_URL}/songs/search?q={encoded_query}&limit={limit}&offset={offset}"

        def _on_success(result):
            Logger.info(f"📦 Результат поиска: {result}")
            Logger.info(f"📦 Тип результата: {type(result)}")
            if on_success:
                on_success(result)

        return self._request(
            url=url,
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def search_songs_sync(self, query: str, limit: int = 20, offset: int = 0):
        """Синхронный поиск песен (для экрана поиска)"""
        import urllib.parse
        encoded_query = urllib.parse.quote(query, safe='')
        # Убираем параметр search_type, оставляем только limit и offset
        url = f"{self.config.API_BASE_URL}/songs/search?q={encoded_query}&limit={limit}&offset={offset}"

        try:
            Logger.info(f"🔍 Синхронный поиск: {query}")
            Logger.info(f"🔍 URL: {url}")
            response = self.session.get(url, timeout=config.CONNECTION_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            Logger.info(f"✅ Результаты поиска: {result}")
            return result
        except requests.exceptions.Timeout:
            Logger.error(f"❌ Таймаут синхронного поиска: {query}")
            return {"results": [], "total": 0}
        except Exception as e:
            Logger.error(f"❌ Ошибка синхронного поиска: {e}")
            return {"results": [], "total": 0}

    # ============ AUTH METHODS ============

    def register(self, username, email, password, full_name=None, on_success=None, on_failure=None):
        """Регистрация нового пользователя"""
        data = {'username': username, 'email': email, 'password': password}
        if full_name:
            data['full_name'] = full_name

        def worker():
            try:
                response = self.session.post(
                    config.API_AUTH_REGISTER,
                    json=data,
                    headers=self._get_headers(include_auth=False),
                    timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json() if response.content else None
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)
            except Exception as e:
                error_msg = str(e)
                if on_failure:
                    Clock.schedule_once(lambda dt: on_failure(None, error_msg), 0)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def login(self, username, password, on_success=None, on_failure=None):
        """Вход по username/password"""
        data = urllib.parse.urlencode({
            'username': username,
            'password': password
        })

        def _on_success(result):
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
            self._save_tokens()
            if on_success:
                on_success(result)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        def worker():
            try:
                response = self.session.post(
                    config.API_AUTH_LOGIN,
                    data=data,
                    headers=headers,
                    timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                Clock.schedule_once(lambda dt: _on_success(result), 0)
            except Exception as e:
                error_msg = str(e)
                if on_failure:
                    Clock.schedule_once(lambda dt: on_failure(None, error_msg), 0)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def google_login(self, on_success=None, on_failure=None):
        """Начинает вход через Google с callback на локальный сервер"""
        self.waiting_for_callback = True

        oauth_server.start()

        redirect_uri = f"http://127.0.0.1:{oauth_server.port}/callback"
        auth_url = f"{self.config.API_BASE_URL}/auth/google/login?redirect_uri={urllib.parse.quote(redirect_uri)}"

        webbrowser.open(auth_url)

        self._check_callback_interval = Clock.schedule_interval(
            lambda dt: self._check_callback(on_success, on_failure), 1
        )

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

            self.get_current_user(
                on_success=on_success,
                on_failure=on_failure
            )
            return False
        return True

    def logout(self, on_success=None, on_failure=None):
        """Выход из аккаунта"""

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
        return self._request(
            url=url,
            method='POST',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_current_user(self, on_success=None, on_failure=None):
        """Получение текущего пользователя"""

        def worker():
            try:
                response = self.session.get(
                    config.API_USER_ME,
                    headers=self._get_headers(include_auth=True),
                    timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                self.user_data = result
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(result), 0)
            except Exception as e:
                error_msg = str(e)
                if on_failure:
                    Clock.schedule_once(lambda dt: on_failure(None, error_msg), 0)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

    def is_authenticated(self):
        return self.access_token is not None and self.user_data is not None

    def is_admin(self):
        if not self.user_data:
            return False
        return self.user_data.get('role') == 'admin'


api = APIClient()