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
from kivy.network.urlrequest import UrlRequest
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from config.app_config import config


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

    def _request(self, url, method='GET', data=None, on_success=None, on_failure=None, include_auth=True):
        headers = self._get_headers(include_auth)
        req = UrlRequest(
            url=url,
            method=method,
            req_body=json.dumps(data) if data else None,
            req_headers=headers,
            on_success=on_success,
            on_failure=on_failure or self._on_failure,
            on_error=self._on_error,
            timeout=config.CONNECTION_TIMEOUT
        )
        return req

    def _on_failure(self, req, error):
        Logger.error(f'API: Ошибка запроса - {error}')

    def _on_error(self, req, error):
        Logger.error(f'API: Критическая ошибка - {error}')

    # ============ AUTH METHODS ============

    def check_health(self, on_success=None, on_failure=None):
        def _on_success(req, result):
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

        def _on_success(req, result):
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

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

        def _on_success(req, result):
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
            self._save_tokens()
            Logger.info(f'✅ Вход выполнен: {username}')
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            Logger.error(f'❌ Ошибка входа: {error}')
            if on_failure:
                on_failure(req, error)

        req = UrlRequest(
            url=config.API_AUTH_LOGIN,
            method='POST',
            req_body=data,
            req_headers=headers,
            on_success=_on_success,
            on_failure=_on_failure,
            on_error=self._on_error,
            timeout=config.CONNECTION_TIMEOUT
        )
        return req

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

        def _on_success(req, result):
            self._clear_tokens()
            Logger.info('✅ Выход выполнен')
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            Logger.error(f'❌ Ошибка выхода: {error}')
            if on_failure:
                on_failure(req, error)

        # Если нет refresh_token, просто очищаем локально
        if not self.refresh_token:
            self._clear_tokens()
            if on_success:
                on_success({})
            return

        # Отправляем refresh_token как query параметр
        url = f"{config.API_AUTH_LOGOUT}?refresh_token={self.refresh_token}"

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        req = UrlRequest(
            url=url,
            method='POST',
            req_body=None,
            req_headers=headers,
            on_success=_on_success,
            on_failure=_on_failure,
            on_error=self._on_error,
            timeout=config.CONNECTION_TIMEOUT
        )
        return req

    def get_current_user(self, on_success=None, on_failure=None):
        def _on_success(req, result):
            self.user_data = result
            Logger.info(f'✅ Получен пользователь: {result.get("username")}')
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            if error == 401 and self.refresh_token:
                self.refresh_access_token(
                    on_success=lambda x: self.get_current_user(on_success, on_failure),
                    on_failure=on_failure
                )
            elif on_failure:
                on_failure(req, error)

        return self._request(
            url=config.API_USER_ME,
            method='GET',
            on_success=_on_success,
            on_failure=_on_failure
        )

    def refresh_access_token(self, on_success=None, on_failure=None):
        def _on_success(req, result):
            self.access_token = result.get('access_token')
            self._save_tokens()
            Logger.info('✅ Токен обновлён')
            if on_success:
                on_success(result)

        return self._request(
            url=config.API_AUTH_REFRESH,
            method='POST',
            data={'refresh_token': self.refresh_token},
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def is_authenticated(self):
        return self.access_token is not None and self.user_data is not None


api = APIClient()