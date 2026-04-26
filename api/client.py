# api/client.py
"""
HTTP клиент для работы с сервером
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

# Отключаем предупреждения SSL
warnings.filterwarnings("ignore", category=Warning)

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============ Локальный сервер для OAuth callback ============

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик callback от Google OAuth"""

    tokens = None

    def do_GET(self):
        """Обрабатывает GET запрос с токенами"""
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

        # Создаем сессию с правильной SSL настройкой
        self.session = get_requests_session()

        self.session.headers.update({
            'User-Agent': 'GuitarFuns/1.0',
            'Accept': 'application/json'
        })

        self._load_tokens()

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

    # ============ AUTH METHODS ============

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
        """Выход из системы (refresh_token как query параметр)"""

        def _on_success(result):
            self._clear_tokens()
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

        url = f"{config.API_AUTH_LOGOUT}?refresh_token={self.refresh_token}"

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

    # ============ МЕТОДЫ ДЛЯ РАБОТЫ С ПЕСНЯМИ ============

    def get_alphabet(self, on_success=None, on_failure=None):
        """Получить все буквы, для которых есть песни"""

        def _on_success(result):
            letters = result.get('letters', []) if isinstance(result, dict) else []
            if on_success:
                on_success(letters)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/alphabet",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_artists_by_letter(self, letter: str, on_success=None, on_failure=None):
        """Получить исполнителей по букве"""
        import urllib.parse
        encoded_letter = urllib.parse.quote(letter, safe='')

        def _on_success(result):
            artists = result.get('artists', []) if isinstance(result, dict) else []
            if on_success:
                on_success(artists)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/artists/{encoded_letter}",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_songs_by_artist(self, artist: str, on_success=None, on_failure=None):
        """Получить песни исполнителя"""
        import urllib.parse
        encoded_artist = urllib.parse.quote(artist, safe='')

        url = f"{self.config.API_BASE_URL}/songs/{encoded_artist}"
        Logger.info(f"🔍 Запрос песен для: {artist}")
        Logger.info(f"🔍 URL: {url}")

        def _on_success(result):
            Logger.info(f"✅ Получены песни для {artist}")
            if isinstance(result, dict):
                songs = result.get('songs', [])
            else:
                songs = []
            if on_success:
                on_success(songs)

        def _on_failure(req, error):
            Logger.error(f"❌ Ошибка получения песен для {artist}: {error}")
            if on_failure:
                on_failure(req, error)

        return self._request(
            url=url,
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=False
        )

    def get_tabs_by_song(self, artist: str, title: str, on_success=None, on_failure=None):
        """Получить подборы песни"""
        import urllib.parse
        encoded_artist = urllib.parse.quote(artist, safe='')
        encoded_title = urllib.parse.quote(title, safe='')

        def _on_success(result):
            tabs = result.get('tabs', []) if isinstance(result, dict) else []
            if on_success:
                on_success(tabs)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tabs/{encoded_artist}/{encoded_title}",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_tab(self, song_id: int, on_success=None, on_failure=None):
        """Получить конкретный подбор по ID"""

        def _on_success(result):
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=True
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

    def get_popular_songs(self, limit: int = 20, on_success=None, on_failure=None):
        """Получить популярные песни"""

        def _on_success(result):
            songs = result.get('songs', []) if isinstance(result, dict) else []
            if on_success:
                on_success(songs)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/popular?limit={limit}",
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    # ============ АДМИН МЕТОДЫ ============

    def is_admin(self) -> bool:
        """Проверяет, является ли текущий пользователь администратором"""
        if not self.user_data:
            return False
        return self.user_data.get('role') == 'admin'

    def get_user_role(self) -> str:
        """Возвращает роль текущего пользователя"""
        if not self.user_data:
            return 'guest'
        return self.user_data.get('role', 'user')

    def toggle_like(self, song_id: int, on_success=None, on_failure=None):
        """Поставить/убрать лайк"""

        def _on_success(result):
            Logger.info(f'✅ Лайк переключён для {song_id}')
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/like",
            method='POST',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def add_to_favorites(self, song_id: int, on_success=None, on_failure=None):
        """Добавить в избранное"""

        def _on_success(result):
            Logger.info(f'✅ Добавлено в избранное {song_id}')
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
        """Удалить из избранного"""

        def _on_success(result):
            Logger.info(f'✅ Удалено из избранного {song_id}')
            if on_success:
                on_success(result)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='DELETE',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def get_all_users(self, on_success=None, on_failure=None, limit=100, offset=0):
        """Получить список всех пользователей (только для админов)"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/users?limit={limit}&offset={offset}",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def update_user_role(self, user_id: int, role: str, on_success=None, on_failure=None):
        """Изменить роль пользователя (только для админов)"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/users/{user_id}/role",
            method='PUT',
            data={'role': role},
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def ban_user(self, user_id: int, on_success=None, on_failure=None):
        """Заблокировать пользователя"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/users/{user_id}/ban",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def unban_user(self, user_id: int, on_success=None, on_failure=None):
        """Разблокировать пользователя"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/users/{user_id}/unban",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def get_admin_stats(self, on_success=None, on_failure=None):
        """Получить статистику для админ-панели"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/admin/stats",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def scan_songs(self, on_success=None, on_failure=None):
        """Запустить сканирование песен (только для админов)"""
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/admin/scan",
            method='POST',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )


api = APIClient()