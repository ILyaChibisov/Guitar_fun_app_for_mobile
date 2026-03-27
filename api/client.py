# api/client.py
import json
from kivy.network.urlrequest import UrlRequest
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from config.app_config import config


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
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if include_auth and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def _request(self, url, method='GET', data=None, on_success=None, on_failure=None, include_auth=True):
        headers = self._get_headers(include_auth)
        req = UrlRequest(
            url=url, method=method, req_body=json.dumps(data) if data else None,
            req_headers=headers, on_success=on_success, on_failure=on_failure or self._on_failure,
            on_error=self._on_error, timeout=config.CONNECTION_TIMEOUT
        )
        return req

    def _on_failure(self, req, error):
        Logger.error(f'API: Ошибка запроса - {error}')

    def _on_error(self, req, error):
        Logger.error(f'API: Критическая ошибка - {error}')

    def check_health(self, on_success=None, on_failure=None):
        def _on_success(req, result):
            Logger.info('✅ Сервер доступен')
            if on_success:
                on_success(result)
        return self._request(url=config.API_HEALTH, method='GET', on_success=_on_success,
                             on_failure=on_failure, include_auth=False)

    def get_current_user(self, on_success=None, on_failure=None):
        def _on_success(req, result):
            self.user_data = result
            Logger.info(f'✅ Получен пользователь: {result.get("username")}')
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            if error == 401 and self.refresh_token:
                self.refresh_access_token(on_success=lambda x: self.get_current_user(on_success, on_failure),
                                          on_failure=on_failure)
            elif on_failure:
                on_failure(req, error)

        return self._request(url=config.API_USER_ME, method='GET', on_success=_on_success, on_failure=_on_failure)

    def refresh_access_token(self, on_success=None, on_failure=None):
        def _on_success(req, result):
            self.access_token = result.get('access_token')
            self._save_tokens()
            Logger.info('✅ Токен обновлён')
            if on_success:
                on_success(result)
        return self._request(url=config.API_AUTH_REFRESH, method='POST',
                             data={'refresh_token': self.refresh_token}, on_success=_on_success,
                             on_failure=on_failure, include_auth=False)

    def login(self, username, password, on_success=None, on_failure=None):
        data = {'username': username, 'password': password}

        def _on_success(req, result):
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
            self._save_tokens()
            Logger.info(f'✅ Вход выполнен: {username}')
            if on_success:
                on_success(result)

        return self._request(url=config.API_AUTH_LOGIN, method='POST', data=data,
                             on_success=_on_success, on_failure=on_failure, include_auth=False)

    def register(self, username, email, password, full_name=None, on_success=None, on_failure=None):
        data = {'username': username, 'email': email, 'password': password}
        if full_name:
            data['full_name'] = full_name

        def _on_success(req, result):
            Logger.info(f'✅ Регистрация успешна: {username}')
            if on_success:
                on_success(result)

        return self._request(url=config.API_AUTH_REGISTER, method='POST', data=data,
                             on_success=_on_success, on_failure=on_failure, include_auth=False)

    def logout(self, on_success=None, on_failure=None):
        def _on_success(req, result):
            self._clear_tokens()
            Logger.info('✅ Выход выполнен')
            if on_success:
                on_success(result)

        return self._request(url=config.API_AUTH_LOGOUT, method='POST',
                             data={'refresh_token': self.refresh_token},
                             on_success=_on_success, on_failure=on_failure)

    def is_authenticated(self):
        """Проверяет, авторизован ли пользователь"""
        return self.access_token is not None and self.user_data is not None


api = APIClient()