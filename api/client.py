# api/client.py
"""
HTTP клиент для работы с сервером
"""
import json
from kivy.network.urlrequest import UrlRequest
from kivy.logger import Logger
from kivy.clock import Clock
from config.app_config import config
from config.theme import theme
from kivymd.uix.snackbar import Snackbar


class APIClient:
    """Клиент для взаимодействия с API сервером"""

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

        # Загружаем токены из хранилища
        self._load_tokens()

    def _load_tokens(self):
        """Загружает токены из локального хранилища"""
        try:
            from kivy.storage.jsonstore import JsonStore
            store = JsonStore('auth.json')
            if store.exists('tokens'):
                self.access_token = store.get('tokens')['access_token']
                self.refresh_token = store.get('tokens')['refresh_token']
                Logger.info('API: Токены загружены')
        except Exception as e:
            Logger.debug(f'API: Нет сохранённых токенов - {e}')

    def _save_tokens(self):
        """Сохраняет токены в локальное хранилище"""
        try:
            from kivy.storage.jsonstore import JsonStore
            store = JsonStore('auth.json')
            store.put('tokens', access_token=self.access_token, refresh_token=self.refresh_token)
            Logger.info('API: Токены сохранены')
        except Exception as e:
            Logger.error(f'API: Ошибка сохранения токенов - {e}')

    def _clear_tokens(self):
        """Очищает токены"""
        try:
            from kivy.storage.jsonstore import JsonStore
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
        """Возвращает заголовки для запроса"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if include_auth and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        return headers

    def _request(self, url, method='GET', data=None, on_success=None, on_failure=None, include_auth=True):
        """Выполняет HTTP запрос"""
        headers = self._get_headers(include_auth)

        req = UrlRequest(
            url=url,
            method=method,
            req_body=json.dumps(data) if data else None,
            req_headers=headers,
            on_success=on_success,
            on_failure=on_failure or self._on_request_failure,
            on_error=self._on_request_error,
            timeout=config.CONNECTION_TIMEOUT
        )
        return req

    def _on_request_failure(self, req, error):
        """Обработчик ошибки запроса"""
        Logger.error(f'API: Ошибка запроса - {error}')

    def _on_request_error(self, req, error):
        """Обработчик критической ошибки"""
        Logger.error(f'API: Критическая ошибка - {error}')

    # ============ AUTH METHODS ============

    def google_login(self, id_token, on_success=None, on_failure=None):
        """Вход через Google"""
        data = {'id_token': id_token}

        def _on_success(req, result):
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
            self._save_tokens()
            Logger.info('API: Вход через Google выполнен')
            if on_success:
                on_success(result)

        return self._request(
            url=config.API_AUTH_GOOGLE,
            method='POST',
            data=data,
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def vk_login(self, code, on_success=None, on_failure=None):
        """Вход через ВКонтакте"""
        data = {'code': code}

        def _on_success(req, result):
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
            self._save_tokens()
            Logger.info('API: Вход через VK выполнен')
            if on_success:
                on_success(result)

        return self._request(
            url=config.API_AUTH_VK,
            method='POST',
            data=data,
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def logout(self, on_success=None, on_failure=None):
        """Выход из системы"""

        def _on_success(req, result):
            self._clear_tokens()
            Logger.info('API: Выход выполнен')
            if on_success:
                on_success(result)

        return self._request(
            url=config.API_AUTH_LOGOUT,
            method='POST',
            data={'refresh_token': self.refresh_token},
            on_success=_on_success,
            on_failure=on_failure
        )

    def refresh_access_token(self, on_success=None, on_failure=None):
        """Обновление access токена"""

        def _on_success(req, result):
            self.access_token = result.get('access_token')
            self._save_tokens()
            Logger.info('API: Access токен обновлён')
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

    def get_current_user(self, on_success=None, on_failure=None):
        """Получение информации о текущем пользователе"""

        def _on_success(req, result):
            self.user_data = result
            Logger.info(f'API: Получен пользователь {result.get("username")}')
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            # Если токен истёк, пробуем обновить
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

    def check_health(self, on_success=None, on_failure=None):
        """Проверка доступности сервера"""

        def _on_success(req, result):
            Logger.info(f'API: Сервер доступен - {result}')
            if on_success:
                on_success(result)

        return self._request(
            url=config.API_HEALTH,
            method='GET',
            on_success=_on_success,
            on_failure=on_failure,
            include_auth=False
        )


# Создаём глобальный экземпляр клиента
api = APIClient()