# api/client.py
"""
HTTP клиент для работы с сервером.
- Без файлового кэша.
- Автоматическое обновление access_token через refresh_token.
- Stale-while-revalidate для избранного.
- Ретрай при обрыве keep-alive соединения.
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

import requests
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from config.app_config import config
from api.ssl_config import get_requests_session, reset_requests_session

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

        # ============ КЭШ ИЗБРАННОГО ТОЛЬКО В ПАМЯТИ ============
        self._favorites_cache = None
        self._favorites_cache_timestamp = 0
        self._favorites_stale = True
        self._favorites_listeners = []
        self._favorites_load_in_progress = False

        # Создаём сессию (заголовки User-Agent/Accept/Connection
        # уже выставлены в ssl_config.py)
        self.session = get_requests_session()

        self._load_tokens()

    # ============ СБРОС СЕССИИ (для on_resume) ============

    def reset_session(self):
        """
        Сбрасывает пул соединений сессии.
        Вызывать при возврате приложения из фона (on_resume),
        чтобы избежать использования "мёртвых" keep-alive сокетов.
        """
        try:
            reset_requests_session(self.session)
            Logger.info("API: сессия сброшена (on_resume)")
        except Exception as e:
            Logger.error(f"API: ошибка сброса сессии — {e}")

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
            self._clear_favorites_cache()
            self._notify_favorites_changed()
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

    # ============ ОБНОВЛЕНИЕ ТОКЕНА ============

    def _refresh_access_token(self) -> bool:
        """
        Обновляет access_token через refresh_token с ретраями на таймаут.
        """
        if not self.refresh_token:
            Logger.warning("API: Нет refresh_token, обновление невозможно")
            return False

        for attempt in range(config.MAX_RETRIES + 1):
            try:
                Logger.info(f"🔄 Обновление access_token (попытка {attempt + 1})...")
                response = self.session.post(
                    f"{self.config.API_BASE_URL}/auth/refresh",
                    json={"refresh_token": self.refresh_token},
                    timeout=config.CONNECTION_TIMEOUT
                )

                if response.status_code == 200:
                    result = response.json()
                    new_access = result.get('access_token')
                    if new_access:
                        self.access_token = new_access
                        self._save_tokens()
                        Logger.info("✅ access_token успешно обновлён")
                        return True

                Logger.warning(f"⚠️ Не удалось обновить токен, статус: {response.status_code}")
                return False

            except requests.exceptions.Timeout as e:
                if attempt < config.MAX_RETRIES:
                    delay = config.RETRY_BACKOFF * (attempt + 1)
                    Logger.warning(
                        f"⏱ Таймаут refresh (попытка {attempt + 1}), "
                        f"ретрай через {delay:.1f}с"
                    )
                    time.sleep(delay)
                    continue
                Logger.error(f"❌ Таймаут refresh после ретраев: {e}")
                return False

            except Exception as e:
                Logger.error(f"❌ Ошибка обновления токена: {e}")
                return False

        return False

    # ============ ЗАПРОСЫ ============

    def _do_request(self, method, url, headers, data, verify=True):
        """Выполняет один HTTP-запрос."""
        kwargs = {
            'headers': headers,
            'timeout': config.CONNECTION_TIMEOUT,
        }
        if not verify:
            kwargs['verify'] = False

        if method == 'GET':
            return self.session.get(url, **kwargs)
        elif method == 'POST':
            return self.session.post(url, json=data, **kwargs)
        elif method == 'PUT':
            return self.session.put(url, json=data, **kwargs)
        elif method == 'DELETE':
            return self.session.delete(url, **kwargs)
        elif method == 'PATCH':
            return self.session.patch(url, json=data, **kwargs)
        else:
            return self.session.request(method, url, json=data, **kwargs)

    def _request_sync(self, url, method='GET', data=None,
                      include_auth=True, _retry=True, _attempt=0):
        """
        Синхронный запрос:
        - автообновление токена при 401;
        - fallback без SSL при SSLError;
        - ретрай с новой сессией при «мёртвом» keep-alive;
        - ретраи с паузой при ReadTimeout.
        """
        headers = self._get_headers(include_auth)
        try:
            response = self._do_request(method, url, headers, data)

            if response.status_code == 401 and include_auth and _retry:
                Logger.warning("⚠️ Получен 401, пробуем обновить токен...")
                if self._refresh_access_token():
                    Logger.info("🔄 Повторяем исходный запрос с новым токеном...")
                    return self._request_sync(url, method, data, include_auth, _retry=False)
                else:
                    Logger.warning("❌ Не удалось обновить токен, очищаем данные авторизации")
                    self._clear_tokens()
                    return {"error": "unauthorized"}

            response.raise_for_status()

            if not response.content or response.content.strip() == b'':
                Logger.warning(f"API: Пустой ответ от {url}")
                return {"artists": [], "total": 0}

            return response.json() if response.content else {"artists": [], "total": 0}

        except requests.exceptions.SSLError as e:
            Logger.error(f"❌ SSL Error: {e}")
            Logger.warning("⚠️ Пробуем запрос без проверки SSL (fallback)...")
            try:
                response = self._do_request(method, url, headers, data, verify=False)
                response.raise_for_status()
                Logger.warning("⚠️ Запрос выполнен без проверки SSL")
                return response.json() if response.content else {"artists": [], "total": 0}
            except Exception as e2:
                Logger.error(f'❌ Ошибка запроса (без SSL): {e2}')
                return {"artists": [], "total": 0}

        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError) as e:
            err_text = str(e)
            is_dead_socket = any(s in err_text for s in (
                "RemoteDisconnected", "Connection aborted",
                "Connection reset", "Read timed out",
                "Connection broken",
            ))
            if is_dead_socket and _retry:
                Logger.warning(f"🔌 Обрыв соединения ({err_text[:80]}), ретрай с новой сессией...")
                try:
                    self.reset_session()
                except Exception:
                    pass
                return self._request_sync(url, method, data, include_auth, _retry=False)

            Logger.error(f"🔌 Ошибка соединения: {e}")
            return {"error": "connection", "artists": [], "songs": [],
                    "favorites": [], "results": [], "total": 0}

        except requests.exceptions.Timeout as e:
            if _attempt < config.MAX_RETRIES and _retry:
                delay = config.RETRY_BACKOFF * (_attempt + 1)
                Logger.warning(
                    f"⏱ Таймаут (попытка {_attempt + 1}/{config.MAX_RETRIES + 1}), "
                    f"ретрай через {delay:.1f}с — {e}"
                )
                time.sleep(delay)
                return self._request_sync(
                    url, method, data, include_auth,
                    _retry=_retry, _attempt=_attempt + 1
                )
            Logger.error(f"⏱ Таймаут после ретраев: {e}")
            return {"error": "timeout", "artists": [], "songs": [],
                    "favorites": [], "results": [], "total": 0}

        except Exception as e:
            Logger.error(f'❌ Ошибка запроса: {e}')
            return {"error": "unknown", "artists": [], "songs": [],
                    "favorites": [], "results": [], "total": 0}

    def _request_async(self, url, method='GET', data=None,
                       on_success=None, on_failure=None, include_auth=True):
        """
        Асинхронный запрос.
        ВАЖНО: значения (result / error_msg) фиксируются в аргументах
        лямбды через default-параметры, чтобы не было NameError
        на удалённой переменной 'e' в замыкании.
        """

        def worker():
            try:
                result = self._request_sync(url, method, data, include_auth)

                if isinstance(result, dict) and result.get('error') == 'unauthorized':
                    if on_failure:
                        Clock.schedule_once(
                            lambda dt, msg="unauthorized": on_failure(None, msg), 0
                        )
                    else:
                        Logger.error("API: Требуется повторная авторизация")
                    return

                if on_success:
                    Clock.schedule_once(
                        lambda dt, res=result: on_success(res), 0
                    )

            except Exception as e:
                error_msg = str(e)
                Logger.error(f"API: Ошибка запроса в потоке — {error_msg}")

                if on_failure:
                    Clock.schedule_once(
                        lambda dt, msg=error_msg: on_failure(None, msg), 0
                    )
                else:
                    Logger.error(f'API: Ошибка - {error_msg}')

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def _request(self, url, method='GET', data=None, on_success=None, on_failure=None, include_auth=True):
        return self._request_async(url, method, data, on_success, on_failure, include_auth)

    # ============ КЭШ ИЗБРАННОГО (ТОЛЬКО В ПАМЯТИ) ============

    def _load_favorites_cache(self, allow_stale=False):
        if self._favorites_cache is None:
            return None
        if allow_stale:
            return self._favorites_cache
        if time.time() - self._favorites_cache_timestamp < config.FAVORITES_CACHE_TTL:
            return self._favorites_cache
        return None

    def _save_favorites_cache(self, favorites, stale=False):
        self._favorites_cache = favorites
        self._favorites_cache_timestamp = time.time()
        self._favorites_stale = stale
        Logger.info(f"💾 Кэш избранного сохранён: {len(favorites)} песен, stale={stale}")

    def _mark_favorites_stale(self):
        if self._favorites_cache is not None:
            self._favorites_stale = True
            Logger.info("⚠️ Кэш избранного помечен как устаревший (данные сохранены)")

    def _clear_favorites_cache(self):
        self._favorites_cache = None
        self._favorites_cache_timestamp = 0
        self._favorites_stale = True
        Logger.info("🗑️ Кэш избранного очищен")

    # ============ ЛОКАЛЬНЫЕ ИЗМЕНЕНИЯ КЭША ============

    def _add_to_favorites_cache_local(self, song: dict):
        if self._favorites_cache is None:
            self._favorites_cache = []

        song_id = song.get('id') or song.get('song_id')
        if not song_id:
            return

        for s in self._favorites_cache:
            if s.get('id') == song_id or s.get('song_id') == song_id:
                return

        entry = {
            'id': song_id,
            'song_id': song_id,
            'artist': song.get('artist', ''),
            'title': song.get('title', ''),
            'tabs_count': song.get('tabs_count', 1),
        }
        self._favorites_cache.insert(0, entry)
        self._favorites_cache_timestamp = time.time()
        self._favorites_stale = False
        Logger.info(f"➕ Локально добавлено в избранное: {entry['artist']} - {entry['title']}")

    def _remove_from_favorites_cache_local(self, song_id):
        if self._favorites_cache is None:
            return

        before = len(self._favorites_cache)
        self._favorites_cache = [
            s for s in self._favorites_cache
            if s.get('id') != song_id and s.get('song_id') != song_id
        ]
        self._favorites_cache_timestamp = time.time()
        self._favorites_stale = False
        removed = before - len(self._favorites_cache)
        if removed:
            Logger.info(f"➖ Локально удалено из избранного: song_id={song_id}")

    # ============ ПОДПИСКА НА ИЗМЕНЕНИЯ ============

    def add_favorites_listener(self, callback):
        if callback not in self._favorites_listeners:
            self._favorites_listeners.append(callback)
            Logger.debug(f"👂 Добавлен слушатель избранного: {callback}")

    def remove_favorites_listener(self, callback):
        if callback in self._favorites_listeners:
            self._favorites_listeners.remove(callback)
            Logger.debug(f"👂 Удалён слушатель избранного: {callback}")

    def _notify_favorites_changed(self):
        favorites = self._favorites_cache or []
        Logger.info(f"📢 Уведомляем {len(self._favorites_listeners)} слушателей об изменении избранного")
        for cb in self._favorites_listeners:
            try:
                Clock.schedule_once(lambda dt, c=cb: c(favorites), 0)
            except Exception as e:
                Logger.error(f"Ошибка в слушателе избранного: {e}")

    # ============ API МЕТОДЫ ============

    def get_favorites(self, on_success=None, on_failure=None,
                      force_refresh=False, silent_refresh=False):
        if not force_refresh:
            cached_stale = self._load_favorites_cache(allow_stale=True)
            if cached_stale is not None:
                Logger.info(f"⚡ Избранное из кэша (stale={self._favorites_stale}): {len(cached_stale)} песен")
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached_stale), 0)
                if not self._favorites_stale:
                    return
                Logger.info("🔄 Кэш устарел — фоновое обновление...")
                self._fetch_favorites_from_server(
                    on_success=on_success, on_failure=on_failure, silent=True
                )
                return

        Logger.info("🔄 Загрузка избранного с сервера (кэш пуст)...")
        self._fetch_favorites_from_server(
            on_success=on_success, on_failure=on_failure, silent=silent_refresh
        )

    def _fetch_favorites_from_server(self, on_success=None, on_failure=None, silent=False):
        if self._favorites_load_in_progress:
            Logger.info("⏳ Загрузка избранного уже идёт — пропускаем")
            return

        self._favorites_load_in_progress = True

        def _on_success(result):
            self._favorites_load_in_progress = False

            if isinstance(result, dict):
                favorites = result.get('favorites', result.get('songs', []))
            elif isinstance(result, list):
                favorites = result
            else:
                favorites = []

            formatted = self._format_favorites(favorites)
            self._save_favorites_cache(formatted, stale=False)
            self._notify_favorites_changed()

            Logger.info(f"✅ Избранное получено с сервера: {len(formatted)} песен")
            if on_success:
                on_success(formatted)

        def _on_failure(req, error):
            self._favorites_load_in_progress = False
            Logger.warning(f"⚠️ Ошибка загрузки избранного: {error}")

            if self._favorites_cache is not None:
                Logger.info("ℹ️ Используем старый кэш после ошибки")
                if silent:
                    return
                if on_failure:
                    on_failure(req, error)
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

    def _format_favorites(self, favorites):
        formatted = []
        for item in favorites:
            if isinstance(item, str):
                parts = item.split(' - ', 1)
                if len(parts) == 2:
                    formatted.append({
                        'artist': parts[0], 'title': parts[1],
                        'tabs_count': 1, 'id': 0, 'song_id': 0,
                    })
                else:
                    formatted.append({
                        'artist': '', 'title': item,
                        'tabs_count': 1, 'id': 0, 'song_id': 0,
                    })
            else:
                if 'id' in item and 'song_id' not in item:
                    item['song_id'] = item['id']
                elif 'song_id' in item and 'id' not in item:
                    item['id'] = item['song_id']
                formatted.append(item)
        return formatted

    def add_to_favorites(self, song_id: int, song_data: dict = None,
                         on_success=None, on_failure=None):
        if song_data:
            song_data = dict(song_data)
            song_data['id'] = song_id
            song_data['song_id'] = song_id
        else:
            song_data = {'id': song_id, 'song_id': song_id, 'artist': '', 'title': ''}

        self._add_to_favorites_cache_local(song_data)
        self._notify_favorites_changed()

        def _on_success(result):
            Logger.info(f"⭐ Песня {song_id} добавлена на сервере")
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            Logger.error(f"❌ Ошибка добавления в избранное: {error}")
            self._remove_from_favorites_cache_local(song_id)
            self._notify_favorites_changed()
            if on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='POST',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=True
        )

    def remove_from_favorites(self, song_id: int,
                              on_success=None, on_failure=None):
        removed_song = None
        if self._favorites_cache:
            for s in self._favorites_cache:
                if s.get('id') == song_id or s.get('song_id') == song_id:
                    removed_song = dict(s)
                    break

        self._remove_from_favorites_cache_local(song_id)
        self._notify_favorites_changed()

        def _on_success(result):
            Logger.info(f"⭐ Песня {song_id} удалена на сервере")
            if on_success:
                on_success(result)

        def _on_failure(req, error):
            Logger.error(f"❌ Ошибка удаления из избранного: {error}")
            if removed_song:
                self._add_to_favorites_cache_local(removed_song)
                self._notify_favorites_changed()
            if on_failure:
                on_failure(req, error)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='DELETE',
            on_success=_on_success,
            on_failure=_on_failure,
            include_auth=True
        )

    def is_song_favorited(self, song_id: int) -> bool:
        cached = self._load_favorites_cache(allow_stale=True)
        if cached is None:
            return False

        for song in cached:
            if song.get('id') == song_id or song.get('song_id') == song_id:
                return True
            if str(song.get('id', '')) == str(song_id) or str(song.get('song_id', '')) == str(song_id):
                return True
        return False

    def get_tab(self, song_id: int, on_success=None, on_failure=None, force_refresh=False):
        Logger.info(f"🔄 Загрузка песни {song_id} с сервера...")
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
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

    # ============ API СЛОВАРЯ ============

    def get_dictionary_alphabet(self, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/dictionary/alphabet",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=False
        )

    def get_terms_by_letter(self, letter: str, lang: str = 'ru', limit: int = 200, offset: int = 0,
                            on_success=None, on_failure=None):
        encoded_letter = urllib.parse.quote(letter, safe='')
        url = f"{self.config.API_BASE_URL}/dictionary/terms/{encoded_letter}?lang={lang}&limit={limit}&offset={offset}"
        return self._request(
            url=url, method='GET',
            on_success=on_success, on_failure=on_failure,
            include_auth=False
        )

    def search_terms(self, query: str, lang: str = None, limit: int = 100, offset: int = 0,
                     on_success=None, on_failure=None):
        encoded_query = urllib.parse.quote(query, safe='')
        url = f"{self.config.API_BASE_URL}/dictionary/search?q={encoded_query}&limit={limit}&offset={offset}"
        if lang:
            url += f"&lang={lang}"
        return self._request(
            url=url, method='GET',
            on_success=on_success, on_failure=on_failure,
            include_auth=False
        )

    def search_terms_sync(self, query: str, lang: str = 'ru', limit: int = 20) -> dict:
        try:
            q_enc = urllib.parse.quote(query, safe='')
            url = f"{self.config.API_BASE_URL}/dictionary/search?q={q_enc}&lang={lang}&limit={limit}"
            response = self.session.get(url, timeout=self.config.CONNECTION_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"❌ Ошибка синхронного поиска терминов: {e}")
            return {"results": [], "total": 0}

    def get_term(self, term_id: int, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/dictionary/term/{term_id}",
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=False
        )

    # ============ МЕТОДЫ ДЛЯ РАБОТЫ С ЗАДАЧАМИ ============

    def get_tasks(self, on_success=None, on_failure=None, force_refresh=False, status=None):
        Logger.info("🔄 Загрузка задач с сервера...")
        url = f"{self.config.API_BASE_URL}/tasks/"
        if status:
            url += f"?status={status}"
        return self._request(
            url=url, method='GET',
            on_success=on_success, on_failure=on_failure,
            include_auth=True
        )

    def get_task(self, task_id, on_success=None, on_failure=None, force_refresh=False):
        Logger.info(f"🔄 Загрузка задачи {task_id} с сервера...")
        url = f"{self.config.API_BASE_URL}/tasks/{task_id}"
        return self._request(
            url=url, method='GET',
            on_success=on_success, on_failure=on_failure,
            include_auth=True
        )

    def create_task(self, task_data, on_success=None, on_failure=None):
        Logger.info(f"📝 Создание задачи: {task_data.get('title')}")
        url = f"{self.config.API_BASE_URL}/tasks/"
        return self._request(
            url=url, method='POST', data=task_data,
            on_success=on_success, on_failure=on_failure,
            include_auth=True
        )

    def update_task(self, task_id, task_data, on_success=None, on_failure=None):
        Logger.info(f"📝 Обновление задачи {task_id}")
        url = f"{self.config.API_BASE_URL}/tasks/{task_id}"
        return self._request(
            url=url, method='PUT', data=task_data,
            on_success=on_success, on_failure=on_failure,
            include_auth=True
        )

    def delete_task(self, task_id, hard=False, on_success=None, on_failure=None):
        Logger.info(f"🗑️ Удаление задачи {task_id}")
        url = f"{self.config.API_BASE_URL}/tasks/{task_id}?hard={str(hard).lower()}"
        return self._request(
            url=url, method='DELETE',
            on_success=on_success, on_failure=on_failure,
            include_auth=True
        )

    def add_task_comment(self, task_id, comment, on_success=None, on_failure=None):
        Logger.info(f"💬 Добавление комментария к задаче {task_id}")
        url = f"{self.config.API_BASE_URL}/tasks/{task_id}/comment"
        return self._request(
            url=url, method='POST', data={'comment': comment},
            on_success=on_success, on_failure=on_failure,
            include_auth=True
        )

    def change_task_status(self, task_id, status, completed_at=None, on_success=None, on_failure=None):
        """Изменить статус задачи"""
        Logger.info(f"🔄 Изменение статуса задачи {task_id} на {status}")

        url = f"{self.config.API_BASE_URL}/tasks/{task_id}/status"
        data = {'status': status}
        if completed_at:
            data['completed_at'] = completed_at
            Logger.info(f"   с completed_at={completed_at}")

        return self._request(
            url=url,
            method='PATCH',
            data=data,
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

    def get_task_statuses(self, on_success=None, on_failure=None):
        """Получить список статусов задач - ВСЕГДА С СЕРВЕРА"""
        url = f"{self.config.API_BASE_URL}/tasks/statuses/list"

        return self._request(
            url=url,
            method='GET',
            on_success=on_success,
            on_failure=on_failure,
            include_auth=True
        )

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

    def register(self, username, email, password, full_name=None,
                 on_success=None, on_failure=None):
        data = {'username': username, 'email': email, 'password': password}
        if full_name:
            data['full_name'] = full_name

        def worker():
            try:
                response = self.session.post(
                    config.API_AUTH_REGISTER, json=data,
                    headers=self._get_headers(include_auth=False),
                    timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json() if response.content else None
                if on_success:
                    Clock.schedule_once(lambda dt, res=result: on_success(res), 0)
            except Exception as e:
                msg = str(e)
                Logger.error(f"API register: {msg}")
                if on_failure:
                    Clock.schedule_once(
                        lambda dt, m=msg: on_failure(None, m), 0
                    )

        threading.Thread(target=worker, daemon=True).start()

    def login(self, username, password, on_success=None, on_failure=None):
        data = urllib.parse.urlencode({'username': username, 'password': password})

        def _on_success(result):
            self.access_token = result.get('access_token')
            self.refresh_token = result.get('refresh_token')
            self._save_tokens()
            self._clear_favorites_cache()
            if on_success:
                on_success(result)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        def worker():
            try:
                response = self.session.post(
                    config.API_AUTH_LOGIN, data=data, headers=headers,
                    timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                Clock.schedule_once(
                    lambda dt, res=result: _on_success(res), 0
                )
            except Exception as e:
                msg = str(e)
                Logger.error(f"API login: {msg}")
                if on_failure:
                    Clock.schedule_once(
                        lambda dt, m=msg: on_failure(None, m), 0
                    )

        threading.Thread(target=worker, daemon=True).start()

    def google_login(self, on_success=None, on_failure=None):
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
            self._clear_favorites_cache()
            self.get_current_user(on_success=on_success, on_failure=on_failure)
            return False
        return True

    def logout(self, on_success=None, on_failure=None):
        def _on_success(result):
            self._clear_tokens()
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
                response = self.session.get(
                    config.API_USER_ME,
                    headers=self._get_headers(include_auth=True),
                    timeout=config.CONNECTION_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                self.user_data = result
                if on_success:
                    Clock.schedule_once(lambda dt, res=result: on_success(res), 0)
            except Exception as e:
                msg = str(e)
                Logger.error(f"API get_current_user: {msg}")
                if on_failure:
                    Clock.schedule_once(
                        lambda dt, m=msg: on_failure(None, m), 0
                    )

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
            response = self.session.get(url, timeout=config.CONNECTION_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения букв: {e}")
            return None

    def force_refresh_favorites(self, on_success=None):
        """Принудительно обновляет кэш избранного с сервера (для pull-to-refresh)"""
        Logger.info("🔄 Принудительное обновление избранного")

        def _done(favorites):
            if on_success:
                on_success(favorites)

        self.get_favorites(
            on_success=_done,
            on_failure=lambda req, err: Logger.warning(f"⚠️ Ошибка refresh: {err}"),
            force_refresh=True
        )


api = APIClient()