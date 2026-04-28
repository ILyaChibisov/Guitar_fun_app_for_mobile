# api/client.py
"""
HTTP клиент для работы с сервером с продвинутым кэшированием
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

        # ============ ПРОДВИНУТЫЙ КЭШ ============
        self.cache = {
            'all_data': None,
            'alphabet': None,
            'artists': {},
            'songs': {},
            'popular': None,
            'favorites': None
        }
        self.cache_timestamps = {
            'all_data': 0,
            'alphabet': 0,
            'popular': 0,
            'favorites': 0
        }
        self.cache_duration = 86400  # 24 часа

        # Создаем сессию
        self.session = get_requests_session()
        self.session.headers.update({
            'User-Agent': 'GuitarFuns/1.0',
            'Accept': 'application/json'
        })

        self._load_tokens()

        # Запускаем фоновую загрузку всех данных
        Clock.schedule_once(self._background_load_all_data, 1)

    # ============ МЕТОДЫ ДЛЯ КЭШИРОВАНИЯ ============

    def is_cache_valid(self, cache_key):
        """Проверяет, актуален ли кэш"""
        if cache_key not in self.cache_timestamps:
            return False
        if self.cache_timestamps[cache_key] == 0:
            return False
        return (time.time() - self.cache_timestamps[cache_key]) < self.cache_duration

    def _cache_data(self, key, data):
        """Сохраняет данные в кэш"""
        self.cache[key] = data
        if key in self.cache_timestamps:
            self.cache_timestamps[key] = time.time()

    def _get_cached_artists(self, letter):
        """Получает исполнителей из кэша"""
        if letter in self.cache['artists']:
            return self.cache['artists'][letter]
        return None

    def _cache_artists(self, letter, data):
        """Сохраняет исполнителей в кэш"""
        self.cache['artists'][letter] = data

    def _get_cached_songs(self, artist):
        """Получает песни из кэша"""
        if artist in self.cache['songs']:
            return self.cache['songs'][artist]
        return None

    def _cache_songs(self, artist, data):
        """Сохраняет песни в кэш"""
        self.cache['songs'][artist] = data

    def get_cached_artists_by_letter(self, letter):
        """Быстрый синхронный доступ к кэшу исполнителей"""
        return self._get_cached_artists(letter)

    def get_cached_songs_by_artist(self, artist):
        """Быстрый синхронный доступ к кэшу песен"""
        return self._get_cached_songs(artist)

    def _background_load_all_data(self, dt):
        """Фоновая загрузка всех данных одним запросом"""
        Logger.info("🚀 Начинаем фоновую загрузку всех данных...")

        def on_success(data):
            Logger.info("✅ Все данные успешно загружены!")
            stats = data.get('stats', {})
            Logger.info(f"📊 Статистика: {stats}")

        def on_failure(req, error):
            Logger.warning(f"⚠️ Не удалось загрузить все данные: {error}")

        self.get_all_data(on_success=on_success, on_failure=on_failure)

    # api/client.py - исправленный метод get_all_data и _on_success

    def get_all_data(self, on_success=None, on_failure=None, force_refresh=False):
        """
        Получить все данные одним запросом (алфавит, исполнители, песни)
        """

        # Проверяем кэш
        if not force_refresh and self.is_cache_valid('all_data') and self.cache['all_data'] is not None:
            Logger.info("📦 Используем кэш для всех данных")
            if on_success:
                Clock.schedule_once(lambda dt: on_success(self.cache['all_data']), 0)
            return

        def _on_success(result):
            # Сохраняем в кэш
            self._cache_data('all_data', result)

            # Распаковываем данные для удобства
            if result:
                # Сохраняем алфавит
                if 'letters' in result:
                    self._cache_data('alphabet', result['letters'])

                # Сохраняем исполнителей по буквам
                if 'artists' in result:
                    artists_data = result['artists']
                    # Если artists - словарь {letter: [artists]}
                    if isinstance(artists_data, dict):
                        for letter, artists in artists_data.items():
                            self._cache_artists(letter, artists)
                    # Если artists - список (старый формат)
                    elif isinstance(artists_data, list):
                        for artist_data in artists_data:
                            letter = artist_data.get('letter', '#')
                            self._cache_artists(letter, [artist_data])

                # Сохраняем песни по исполнителям
                if 'songs' in result:
                    songs_data = result['songs']
                    # Если songs - словарь {artist: [songs]}
                    if isinstance(songs_data, dict):
                        for artist, songs in songs_data.items():
                            self._cache_songs(artist, songs)
                    # Если songs - список (старый формат)
                    elif isinstance(songs_data, list):
                        for song_data in songs_data:
                            artist = song_data.get('artist')
                            if artist:
                                existing = self._get_cached_songs(artist) or []
                                existing.append(song_data)
                                self._cache_songs(artist, existing)

                # Сохраняем популярные
                if 'popular' in result:
                    self._cache_data('popular', result['popular'])

                # Сохраняем избранное
                if 'favorites' in result:
                    self._cache_data('favorites', result['favorites'])

            self.is_loading_complete = True
            Logger.info("✅ Все данные успешно загружены и сохранены в кэш")
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            cached = self.cache['all_data']
            if cached is not None:
                Logger.warning(f"Ошибка загрузки, используем кэш: {error}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
            elif on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/all-data",
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=self.is_authenticated()
        )

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
            except Exception as err:
                if on_failure:
                    error_msg = str(err)
                    Clock.schedule_once(lambda dt: on_failure(None, error_msg), 0)
                else:
                    Logger.error(f'API: Ошибка - {err}')

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def _request(self, url, method='GET', data=None, on_success=None, on_failure=None, include_auth=True):
        return self._request_async(url, method, data, on_success, on_failure, include_auth)

    def check_health(self, on_success=None, on_failure=None):
        def _on_success(result):
            Logger.info('✅ Сервер доступен')
            if on_success:
                on_success(result)

        return self._request(
            url=config.API_HEALTH,
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def register(self, username, email, password, full_name=None, on_success=None, on_failure=None):
        data = {'username': username, 'email': email, 'password': password}
        if full_name:
            data['full_name'] = full_name

        def _on_success(result):
            Logger.info(f'✅ Регистрация успешна: {username}')
            if on_success:
                on_success(result)

        return self._request(
            url=config.API_AUTH_REGISTER,
            method='POST',
            data=data,
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def login(self, username, password, on_success=None, on_failure=None):
        """Вход по username/password (form-data)"""
        data = urllib.parse.urlencode({
            'username': username,
            'password': password
        })

        def _on_success(result):
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
            self._save_tokens()
            Logger.info(f'✅ Вход выполнен: {username}')
            if on_success:
                on_success(result)

        def _on_failure(error):
            Logger.error(f'❌ Ошибка входа: {error}')
            if on_failure:
                on_failure(None, error)

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
            except Exception as err:
                error_msg = str(err)
                Clock.schedule_once(lambda dt: _on_failure(error_msg), 0)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def change_password(self, old_password, new_password, on_success=None, on_failure=None):
        """Смена пароля"""
        data = {
            'old_password': old_password,
            'new_password': new_password
        }

        def _on_success(result):
            Logger.info(f'✅ Пароль изменён')
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/auth/change-password",
            method='POST',
            data=data,
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=True
        )

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
        """Выход из системы"""

        def _on_success(result):
            self._clear_tokens()
            self.clear_cache()
            Logger.info('✅ Выход выполнен')
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            Logger.error(f'❌ Ошибка выхода: {error}')
            if on_failure:
                on_failure(req, error)

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
            on_failure=_on_failure,
            include_auth=False
        )

    def get_current_user(self, on_success=None, on_failure=None):
        """Получение текущего пользователя"""

        def _on_success(result):
            self.user_data = result
            Logger.info(f'✅ Получен пользователь: {result.get("username")}')
            if on_success:
                on_success(result)

        def _on_failure(error):
            if "401" in str(error) or "Unauthorized" in str(error):
                if self.refresh_token:
                    def on_refresh_success(x):
                        self.get_current_user(on_success, on_failure)

                    self.refresh_access_token(
                        on_success=on_refresh_success,
                        on_failure=on_failure
                    )
                else:
                    if on_failure:
                        on_failure(None, error)
            else:
                if on_failure:
                    on_failure(None, error)

        def worker():
            try:
                response = self.session.get(
                    config.API_USER_ME,
                    headers=self._get_headers(include_auth=True),
                    timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                Clock.schedule_once(lambda dt: _on_success(result), 0)
            except Exception as err:
                error_msg = str(err)
                Clock.schedule_once(lambda dt: _on_failure(error_msg), 0)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def refresh_access_token(self, on_success=None, on_failure=None):

        def _on_success(result):
            self.access_token = result.get('access_token')
            self._save_tokens()
            Logger.info('✅ Токен обновлён')
            if on_success:
                on_success(result)

        def _on_failure(error):
            if on_failure:
                on_failure(None, error)

        def worker():
            try:
                response = self.session.post(
                    config.API_AUTH_REFRESH,
                    json={'refresh_token': self.refresh_token},
                    headers=self._get_headers(include_auth=False),
                    timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                Clock.schedule_once(lambda dt: _on_success(result), 0)
            except Exception as err:
                error_msg = str(err)
                Clock.schedule_once(lambda dt: _on_failure(error_msg), 0)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def is_authenticated(self):
        return self.access_token is not None and self.user_data is not None

    # ============ МЕТОДЫ ДЛЯ РАБОТЫ С ПЕСНЯМИ (С КЭШЕМ) ============

    def get_alphabet(self, on_success=None, on_failure=None, force_refresh=False):
        """Получить все буквы (с кэшем)"""

        if not force_refresh and self.is_cache_valid('alphabet') and self.cache['alphabet'] is not None:
            Logger.debug("📦 Используем кэш для алфавита")
            if on_success:
                Clock.schedule_once(lambda dt: on_success(self.cache['alphabet']), 0)
            return

        def _on_success(result):
            letters = result.get('letters', []) if isinstance(result, dict) else []
            self._cache_data('alphabet', letters)
            if on_success:
                on_success(letters)

        def _on_failure(req, error):
            if self.cache['alphabet'] is not None:
                Logger.warning(f"Ошибка загрузки алфавита, используем кэш: {error}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(self.cache['alphabet']), 0)
            elif on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/alphabet",
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=False
        )

    def get_artists_by_letter(self, letter: str, on_success=None, on_failure=None, force_refresh=False):
        """Получить исполнителей по букве (с кэшем)"""

        if not force_refresh:
            cached = self._get_cached_artists(letter)
            if cached is not None:
                Logger.debug(f"📦 Используем кэш для исполнителей буквы {letter}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
                return

        import urllib.parse
        encoded_letter = urllib.parse.quote(letter, safe='')

        def _on_success(result):
            artists = result.get('artists', []) if isinstance(result, dict) else []
            self._cache_artists(letter, artists)
            if on_success:
                on_success(artists)

        def _on_failure(req, error):
            cached = self._get_cached_artists(letter)
            if cached is not None:
                Logger.warning(f"Ошибка загрузки исполнителей {letter}, используем кэш: {error}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
            elif on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/artists/{encoded_letter}",
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=False
        )

    def get_songs_by_artist(self, artist: str, on_success=None, on_failure=None, force_refresh=False):
        """Получить песни исполнителя (с кэшем)"""

        if not force_refresh:
            cached = self._get_cached_songs(artist)
            if cached is not None:
                Logger.debug(f"📦 Используем кэш для песен исполнителя {artist}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
                return

        import urllib.parse
        encoded_artist = urllib.parse.quote(artist, safe='')
        url = f"{self.config.API_BASE_URL}/songs/{encoded_artist}"
        Logger.info(f"🔍 Запрос песен для: {artist}")

        def _on_success(result):
            if isinstance(result, dict):
                songs = result.get('songs', [])
            else:
                songs = []
            self._cache_songs(artist, songs)
            Logger.info(f"✅ Получены песни для {artist}")
            if on_success:
                on_success(songs)

        def _on_failure(req, error):
            cached = self._get_cached_songs(artist)
            if cached is not None:
                Logger.warning(f"Ошибка загрузки песен {artist}, используем кэш: {error}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
            elif on_failure:
                on_failure(req, error)

        return self._request(
            url=url,
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=False
        )

    def get_popular_songs(self, limit: int = 20, on_success=None, on_failure=None, force_refresh=False):
        """Получить популярные песни (с кэшем)"""

        if not force_refresh and self.is_cache_valid('popular') and self.cache['popular'] is not None:
            Logger.debug("📦 Используем кэш для популярных песен")
            if on_success:
                Clock.schedule_once(lambda dt: on_success(self.cache['popular']), 0)
            return

        def _on_success(result):
            songs = result.get('songs', []) if isinstance(result, dict) else []
            self._cache_data('popular', songs)
            if on_success:
                on_success(songs)

        def _on_failure(req, error):
            cached = self.cache['popular']
            if cached is not None:
                Logger.warning(f"Ошибка загрузки популярных песен, используем кэш: {error}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
            elif on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/popular?limit={limit}",
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=False
        )

    def get_favorites(self, on_success=None, on_failure=None, force_refresh=False):
        """Получить список избранных песен пользователя (с кэшем)"""

        if not force_refresh and self.is_authenticated() and self.is_cache_valid('favorites') and self.cache[
            'favorites'] is not None:
            Logger.debug("📦 Используем кэш для избранного")
            if on_success:
                Clock.schedule_once(lambda dt: on_success(self.cache['favorites']), 0)
            return

        def _on_success(result):
            if isinstance(result, dict):
                favorites = result.get('favorites', result.get('songs', []))
            else:
                favorites = result if isinstance(result, list) else []
            self._cache_data('favorites', favorites)
            Logger.info(f'✅ Получено избранных: {len(favorites)}')
            if on_success:
                on_success(favorites)

        def _on_failure(req, error):
            cached = self.cache['favorites']
            if cached is not None:
                Logger.warning(f"Ошибка загрузки избранного, используем кэш: {error}")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached), 0)
            elif on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/favorites",
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=True
        )

    def get_tab(self, song_id: int, on_success=None, on_failure=None):
        """Получить конкретный подбор по ID (без кэша - всегда свежий)"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def search_songs(self, query: str, search_type: str = "general", limit: int = 50, on_success=None, on_failure=None):
        """Поиск песен (асинхронный)"""
        import urllib.parse
        encoded_query = urllib.parse.quote(query, safe='')

        def _on_success(result):
            results = result.get('results', []) if isinstance(result, dict) else []
            if on_success:
                on_success(results)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/search?q={encoded_query}&search_type={search_type}&limit={limit}",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def search_songs_sync(self, query: str, search_type: str = "general", limit: int = 50):
        """Синхронный поиск песен (для диалога поиска)"""
        import urllib.parse

        encoded_query = urllib.parse.quote(query, safe='')
        url = f"{self.config.API_BASE_URL}/songs/search?q={encoded_query}&search_type={search_type}&limit={limit}"

        try:
            Logger.info(f"🔍 Синхронный поиск: {query}")
            response = self.session.get(url, timeout=config.CONNECTION_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            return result.get('results', [])
        except requests.exceptions.Timeout:
            Logger.error(f"❌ Таймаут синхронного поиска: {query}")
            return []
        except Exception as e:
            Logger.error(f"❌ Ошибка синхронного поиска: {e}")
            return []

    # ============ ЛАЙКИ ============

    def toggle_like(self, song_id: int, on_success=None, on_failure=None):
        """Поставить/убрать лайк"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/like",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def add_to_favorites(self, song_id: int, on_success=None, on_failure=None):
        """Добавить песню в избранное"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def remove_from_favorites(self, song_id: int, on_success=None, on_failure=None):
        """Удалить песню из избранного"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='DELETE',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    # ============ АДМИН МЕТОДЫ ============

    def is_admin(self) -> bool:
        if not self.user_data:
            return False
        return self.user_data.get('role') == 'admin'

    def get_user_role(self) -> str:
        if not self.user_data:
            return 'guest'
        return self.user_data.get('role', 'user')

    def get_all_users(self, on_success=None, on_failure=None, limit=100, offset=0):
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/users?limit={limit}&offset={offset}",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def update_user_role(self, user_id: int, role: str, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/users/{user_id}/role",
            method='PUT',
            data={'role': role},
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def ban_user(self, user_id: int, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/users/{user_id}/ban",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def unban_user(self, user_id: int, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/users/{user_id}/unban",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def get_admin_stats(self, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/stats",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def scan_songs(self, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/admin/scan",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def clear_cache(self):
        """Очищает весь кэш"""
        self.cache = {
            'all_data': None,
            'alphabet': None,
            'artists': {},
            'songs': {},
            'popular': None,
            'favorites': None
        }
        self.cache_timestamps = {
            'all_data': 0,
            'alphabet': 0,
            'popular': 0,
            'favorites': 0
        }
        self.is_loading_complete = False
        self.loading_progress = 0
        Logger.info("🗑️ Кэш очищен")


api = APIClient()