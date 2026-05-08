# api/client.py
"""
HTTP клиент для работы с сервером - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ
С поддержкой кэширования, предзагрузки и сохранением кэша в файл
"""
import json
import os
import threading
import http.server
import socketserver
import urllib.parse
import webbrowser
import requests
import warnings
import time
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock
from config.app_config import config
from api.ssl_config import get_requests_session

# Файл для сохранения кэша
CACHE_FILE = "cache.json"

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
        self.is_loading_complete = False
        self.loading_progress = 0

        # Кэш для страниц
        self.cache = {
            'alphabet': None,
            'artists': {},
            'songs': {},
            'popular': None,
            'favorites': None
        }

        # Кэш для предзагрузки
        self._prefetched_artists = {}
        self._prefetched_songs = {}
        self._prefetch_complete = False
        self._prefetch_timestamp = 0
        self._prefetch_ttl = 3600  # время жизни кэша в секундах (1 час)

        # Кэш для иконки
        self._icon_texture = None

        # Загружаем кэш из файла
        self._load_cache_from_file()

        # Создаем сессию с оптимизациями
        self.session = get_requests_session()
        self.session.headers.update({
            'User-Agent': 'GuitarFuns/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })

        self._load_tokens()

    # ============ РАБОТА С ФАЙЛОВЫМ КЭШЕМ ============

    def _load_cache_from_file(self):
        """Загружает кэш из файла"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._prefetched_artists = data.get('artists', {})
                    self._prefetched_songs = data.get('songs', {})
                    self._prefetch_timestamp = data.get('timestamp', 0)
                    self._prefetch_complete = bool(self._prefetched_artists)

                    if self.is_cache_fresh():
                        total_artists = sum(len(v['artists']) for v in self._prefetched_artists.values())
                        total_songs = len(self._prefetched_songs)
                        Logger.info(
                            f"✅ Кэш загружен из файла: {len(self._prefetched_artists)} букв, {total_artists} артистов, {total_songs} песен")
                    else:
                        Logger.info("⚠️ Кэш в файле устарел, очищаем")
                        self._prefetched_artists = {}
                        self._prefetched_songs = {}
                        self._prefetch_complete = False
                        self._prefetch_timestamp = 0
            except Exception as e:
                Logger.error(f"Ошибка загрузки кэша: {e}")

    def _save_cache_to_file(self):
        """Сохраняет кэш в файл"""
        try:
            data = {
                'artists': self._prefetched_artists,
                'songs': self._prefetched_songs,
                'timestamp': self._prefetch_timestamp
            }
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            total_artists = sum(len(v['artists']) for v in self._prefetched_artists.values())
            total_songs = len(self._prefetched_songs)
            Logger.info(
                f"💾 Кэш сохранён в файл: {len(self._prefetched_artists)} букв, {total_artists} артистов, {total_songs} песен")
        except Exception as e:
            Logger.error(f"Ошибка сохранения кэша: {e}")

    # ============ МЕТОДЫ КЭШИРОВАНИЯ ============

    def _cache_artists_page(self, letter, page, data, total):
        if letter not in self.cache['artists']:
            self.cache['artists'][letter] = {}
        self.cache['artists'][letter][page] = {
            'data': data,
            'total': total,
            'timestamp': time.time()
        }

    def _get_cached_artists_page(self, letter, page):
        if letter in self.cache['artists'] and page in self.cache['artists'][letter]:
            return self.cache['artists'][letter][page]
        return None

    def _cache_songs_page(self, artist, page, data, total):
        if artist not in self.cache['songs']:
            self.cache['songs'][artist] = {}
        self.cache['songs'][artist][page] = {
            'data': data,
            'total': total,
            'timestamp': time.time()
        }

    def _get_cached_songs_page(self, artist, page):
        if artist in self.cache['songs'] and page in self.cache['songs'][artist]:
            return self.cache['songs'][artist][page]
        return None

    def clear_cache(self):
        self.cache = {
            'alphabet': None,
            'artists': {},
            'songs': {},
            'popular': None,
            'favorites': None
        }
        self._prefetched_artists = {}
        self._prefetched_songs = {}
        self._prefetch_complete = False
        self._prefetch_timestamp = 0
        if os.path.exists(CACHE_FILE):
            try:
                os.remove(CACHE_FILE)
                Logger.info("🗑️ Файл кэша удалён")
            except:
                pass
        Logger.info("🗑️ Кэш очищен")

    # ============ ПРЕДЗАГРУЗКА ДАННЫХ ============

    def is_cache_fresh(self):
        """Проверяет, не устарел ли кэш"""
        if not self._prefetch_complete:
            return False
        return (time.time() - self._prefetch_timestamp) < self._prefetch_ttl

    def _encode_letter(self, letter: str) -> str:
        """Правильно кодирует букву для URL"""
        import urllib.parse

        # Специальная обработка для проблемных букв
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

    def _preload_icon_sync(self):
        """Синхронная предзагрузка иконки (для использования в потоке)"""
        try:
            from data import load_asset_as_bytes
            from kivy.core.image import Image as CoreImage
            from io import BytesIO

            icon_data = load_asset_as_bytes('artist_png')
            if icon_data:
                img = CoreImage(BytesIO(icon_data), ext="png")
                self._icon_texture = img.texture
                Logger.info("🎨 Иконка исполнителя предзагружена в кэш")
        except Exception as e:
            Logger.warning(f"⚠️ Не удалось предзагрузить иконку: {e}")

    def _preload_icon_async(self):
        """Асинхронная предзагрузка иконки"""

        def load():
            self._preload_icon_sync()

        thread = threading.Thread(target=load, daemon=True)
        thread.start()

    def get_shared_icon_texture(self):
        """Возвращает предзагруженную текстуру иконки"""
        return self._icon_texture

    def prefetch_all_artists(self, on_progress=None, on_complete=None, force_refresh=False):
        """Предзагружает всех артистов и их песни в фоновом потоке"""
        if not force_refresh and self.is_cache_fresh():
            total_artists = sum(len(v['artists']) for v in self._prefetched_artists.values())
            total_songs = len(self._prefetched_songs)
            Logger.info(
                f"📦 Кэш ещё свежий, предзагрузка не требуется (артистов: {total_artists}, песен: {total_songs})")

            self._preload_icon_async()

            if on_complete:
                Clock.schedule_once(lambda dt: on_complete(total_artists, total_songs), 0)
            return

        Logger.info("🚀 Начинаем предзагрузку всех данных...")

        def worker():
            try:
                start_time = time.time()

                self._preload_icon_sync()

                alphabet_response = self.session.get(
                    f"{self.config.API_BASE_URL}/songs/alphabet",
                    timeout=30
                )
                alphabet = alphabet_response.json().get('letters', [])
                total_letters = len(alphabet)

                if on_progress:
                    Clock.schedule_once(lambda dt: on_progress(0, total_letters, "Загрузка списка букв..."), 0)

                all_artists = {}
                all_songs_by_artist = {}
                processed = 0

                for letter in alphabet:
                    if letter in ['#', '?', '&', '%']:
                        continue

                    encoded_letter = self._encode_letter(letter)

                    url = f"{self.config.API_BASE_URL}/songs/artists/{encoded_letter}?limit=200&offset=0"
                    try:
                        response = self.session.get(url, timeout=30)
                        data = response.json()

                        artists = data.get('artists', [])
                        total_artists = data.get('total', 0)

                        all_artists[letter] = {
                            'artists': artists,
                            'total': total_artists
                        }

                        for artist_data in artists:
                            artist_name = artist_data.get('artist')
                            if artist_name:
                                songs_url = f"{self.config.API_BASE_URL}/songs/{urllib.parse.quote(artist_name, safe='')}?limit=200&offset=0"
                                try:
                                    songs_response = self.session.get(songs_url, timeout=30)
                                    songs_data = songs_response.json()
                                    all_songs_by_artist[artist_name] = {
                                        'songs': songs_data.get('songs', []),
                                        'total': songs_data.get('total', 0)
                                    }
                                except Exception as e:
                                    Logger.error(f"   Ошибка загрузки песен {artist_name}: {e}")

                        processed += 1
                        if on_progress:
                            Clock.schedule_once(
                                lambda dt, p=processed, t=total_letters: on_progress(p, t, f"Загружено {p}/{t} букв"),
                                0
                            )
                        Logger.info(f"📁 Буква {letter}: {len(artists)} артистов")
                    except Exception as e:
                        Logger.error(f"❌ Ошибка загрузки буквы {letter}: {e}")
                        all_artists[letter] = {'artists': [], 'total': 0}
                        processed += 1

                self._prefetched_artists = all_artists
                self._prefetched_songs = all_songs_by_artist
                self._prefetch_complete = True
                self._prefetch_timestamp = time.time()

                self._save_cache_to_file()

                elapsed = time.time() - start_time
                total_artists_count = sum(len(v['artists']) for v in all_artists.values())
                total_songs_count = len(all_songs_by_artist)

                Logger.info(f"✅ Предзагрузка завершена за {elapsed:.1f} сек!")
                Logger.info(f"   📊 Артистов: {total_artists_count}, Песен: {total_songs_count}")

                if on_complete:
                    Clock.schedule_once(lambda dt: on_complete(total_artists_count, total_songs_count), 0)

            except Exception as e:
                Logger.error(f"❌ Ошибка предзагрузки: {e}")
                import traceback
                traceback.print_exc()
                self._prefetch_complete = False
                if on_complete:
                    Clock.schedule_once(lambda dt: on_complete(0, 0), 0)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread

    def get_artists_by_letter_from_cache(self, letter):
        """Быстрый доступ к артистам из кэша"""
        if letter in self._prefetched_artists:
            return self._prefetched_artists[letter]
        return None

    def get_songs_by_artist_from_cache(self, artist):
        """Быстрый доступ к песням артиста из кэша"""
        if artist in self._prefetched_songs:
            return self._prefetched_songs[artist]
        return None

    def is_prefetch_ready(self):
        return getattr(self, '_prefetch_complete', False)

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
        """Синхронный запрос (для использования в потоках)"""
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

            if not response.content or response.content.strip() == b'':
                Logger.warning(f"API: Пустой ответ от {url}")
                return {"artists": [], "total": 0}

            return response.json() if response.content else {"artists": [], "total": 0}
        except Exception as e:
            Logger.error(f'API: Ошибка запроса - {e}')
            return {"artists": [], "total": 0}

    def _request_async(self, url, method='GET', data=None, on_success=None, on_failure=None, include_auth=True):
        """Асинхронный запрос (не блокирует UI)"""

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

    def get_artists_by_letter(self, letter: str, limit: int = 200, offset: int = 0,
                              on_success=None, on_failure=None, force_refresh=False):
        page = offset // limit if limit > 0 else 0
        if not force_refresh:
            cached = self._get_cached_artists_page(letter, page)
            if cached:
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached['data']), 0)
                return

        encoded_letter = self._encode_letter(letter)
        url = f"{self.config.API_BASE_URL}/songs/artists/{encoded_letter}?limit={limit}&offset={offset}"
        Logger.info(f"Запрос артистов для буквы: {letter} -> {encoded_letter}")

        def _on_success(result):
            if result is None:
                result = {"artists": [], "total": 0}
            artists = result.get('artists', [])
            total = result.get('total', 0)
            self._cache_artists_page(letter, page, result, total)
            if on_success:
                on_success(result)

        return self._request(url=url, method='GET', on_success=_on_success, on_failure=on_failure, include_auth=False)

    def get_artists_by_digits(self, limit: int = 200, offset: int = 0,
                              on_success=None, on_failure=None, force_refresh=False):
        page = offset // limit if limit > 0 else 0
        cache_key = "digits"
        if not force_refresh:
            cached = self._get_cached_artists_page(cache_key, page)
            if cached:
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached['data']), 0)
                return

        url = f"{self.config.API_BASE_URL}/songs/artists/digits?limit={limit}&offset={offset}"
        Logger.info(f"Запрос артистов для цифр")

        def _on_success(result):
            self._cache_artists_page(cache_key, page, result, result.get('total', 0))
            if on_success:
                on_success(result)

        return self._request(url=url, method='GET', on_success=_on_success, on_failure=on_failure, include_auth=False)

    def get_songs_by_artist(self, artist: str, limit: int = 200, offset: int = 0,
                            on_success=None, on_failure=None, force_refresh=False):
        page = offset // limit if limit > 0 else 0
        if not force_refresh:
            cached = self._get_cached_songs_page(artist, page)
            if cached:
                if on_success:
                    Clock.schedule_once(lambda dt: on_success(cached['data']), 0)
                return

        encoded_artist = urllib.parse.quote(artist, safe='')
        url = f"{self.config.API_BASE_URL}/songs/{encoded_artist}?limit={limit}&offset={offset}"

        def _on_success(result):
            self._cache_songs_page(artist, page, result, result.get('total', 0))
            if on_success:
                on_success(result)

        return self._request(url=url, method='GET', on_success=_on_success, on_failure=on_failure, include_auth=False)

    def get_tab(self, song_id: int, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}",
            method='GET', on_success=on_success, on_failure=on_failure, include_auth=False
        )

    def get_popular_songs(self, limit: int = 20, on_success=None, on_failure=None, force_refresh=False):
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
            method='GET', on_success=_on_success, on_failure=on_failure, include_auth=False
        )

    def get_favorites(self, on_success=None, on_failure=None, force_refresh=False):
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
                        formatted_favorites.append({'artist': parts[0], 'title': parts[1], 'tabs_count': 1, 'id': 0})
                    else:
                        formatted_favorites.append({'artist': '', 'title': item, 'tabs_count': 1, 'id': 0})
                else:
                    formatted_favorites.append(item)
            self.cache['favorites'] = formatted_favorites
            Logger.info(f'✅ Получено избранных: {len(formatted_favorites)}')
            if on_success:
                on_success(formatted_favorites)

        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/favorites",
            method='GET', on_success=_on_success, on_failure=on_failure, include_auth=True
        )

    def add_to_favorites(self, song_id: int, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='POST', on_success=on_success, on_failure=on_failure, include_auth=True
        )

    def remove_from_favorites(self, song_id: int, on_success=None, on_failure=None):
        return self._request(
            url=f"{self.config.API_BASE_URL}/songs/tab/{song_id}/favorite",
            method='DELETE', on_success=on_success, on_failure=on_failure, include_auth=True
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

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА AMDM ============

    def start_amdm_parser(self, start_page, end_page, subdomain, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/start"
        data = {"start_page": start_page, "end_page": end_page, "subdomain": subdomain}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_amdm_parser_sync(self, start_page, end_page, subdomain):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/start"
        data = {"start_page": start_page, "end_page": end_page, "subdomain": subdomain}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера AMDM: {e}")
            return None

    def pause_amdm_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/pause"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def pause_amdm_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/pause"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка паузы парсера AMDM: {e}")
            return None

    def resume_amdm_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/resume"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def resume_amdm_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/resume"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка возобновления парсера AMDM: {e}")
            return None

    def stop_amdm_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_amdm_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера AMDM: {e}")
            return None

    def get_amdm_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_amdm_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера AMDM: {e}")
            return None

    def get_amdm_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/amdm/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА MYTABS ============

    def start_mytabs_parser(self, start_page, end_page, subdomain, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/start"
        data = {"start_page": start_page, "end_page": end_page, "subdomain": subdomain}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_mytabs_parser_sync(self, start_page, end_page, subdomain):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/start"
        data = {"start_page": start_page, "end_page": end_page, "subdomain": subdomain}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера MyTabs: {e}")
            return None

    def pause_mytabs_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/pause"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def pause_mytabs_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/pause"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка паузы парсера MyTabs: {e}")
            return None

    def resume_mytabs_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/resume"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def resume_mytabs_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/resume"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка возобновления парсера MyTabs: {e}")
            return None

    def stop_mytabs_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_mytabs_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера MyTabs: {e}")
            return None

    def get_mytabs_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_mytabs_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера MyTabs: {e}")
            return None

    def get_mytabs_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/mytabs/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА ACCORDPRO ============

    def start_accord_pro_parser(self, start_group, end_group, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/accordpro/start"
        data = {"start_group": start_group, "end_group": end_group}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_accord_pro_parser_sync(self, start_group, end_group):
        url = f"{self.config.API_BASE_URL}/parsers/accordpro/start"
        data = {"start_group": start_group, "end_group": end_group}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера AccordPro: {e}")
            return None

    def stop_accord_pro_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/accordpro/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_accord_pro_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/accordpro/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера AccordPro: {e}")
            return None

    def get_accord_pro_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/accordpro/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_accord_pro_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/accordpro/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера AccordPro: {e}")
            return None

    def get_accord_pro_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/accordpro/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА AKKORDUS ============

    def start_akkordus_parser(self, start_group, end_group, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/akkordus/start"
        data = {"start_group": start_group, "end_group": end_group}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_akkordus_parser_sync(self, start_group, end_group):
        url = f"{self.config.API_BASE_URL}/parsers/akkordus/start"
        data = {"start_group": start_group, "end_group": end_group}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера Akkordus: {e}")
            return None

    def stop_akkordus_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/akkordus/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_akkordus_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/akkordus/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера Akkordus: {e}")
            return None

    def get_akkordus_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/akkordus/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_akkordus_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/akkordus/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера Akkordus: {e}")
            return None

    def get_akkordus_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/akkordus/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА MUZLAND ============

    def start_muzland_parser(self, start_group, end_group, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/muzland/start"
        data = {"start_group": start_group, "end_group": end_group}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_muzland_parser_sync(self, start_group, end_group):
        url = f"{self.config.API_BASE_URL}/parsers/muzland/start"
        data = {"start_group": start_group, "end_group": end_group}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера Muzland: {e}")
            return None

    def stop_muzland_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/muzland/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_muzland_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/muzland/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера Muzland: {e}")
            return None

    def get_muzland_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/muzland/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_muzland_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/muzland/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера Muzland: {e}")
            return None

    def get_muzland_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/muzland/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА CHORDIE ============

    def start_chordie_parser(self, start_letter, end_letter, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/chordie/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_chordie_parser_sync(self, start_letter, end_letter):
        url = f"{self.config.API_BASE_URL}/parsers/chordie/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера Chordie: {e}")
            return None

    def stop_chordie_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/chordie/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_chordie_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/chordie/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера Chordie: {e}")
            return None

    def get_chordie_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/chordie/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_chordie_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/chordie/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера Chordie: {e}")
            return None

    def get_chordie_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/chordie/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА 5LAD ============

    def start_fivelad_parser(self, start_group, end_group, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/fivelad/start"
        data = {"start_group": start_group, "end_group": end_group}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_fivelad_parser_sync(self, start_group, end_group):
        url = f"{self.config.API_BASE_URL}/parsers/fivelad/start"
        data = {"start_group": start_group, "end_group": end_group}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера 5Lad: {e}")
            return None

    def stop_fivelad_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/fivelad/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_fivelad_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/fivelad/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера 5Lad: {e}")
            return None

    def get_fivelad_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/fivelad/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_fivelad_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/fivelad/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера 5Lad: {e}")
            return None

    def get_fivelad_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/fivelad/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА AKKORDBARD ============

    def start_akkordbard_parser(self, start_letter, end_letter, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/akkordbard/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_akkordbard_parser_sync(self, start_letter, end_letter):
        url = f"{self.config.API_BASE_URL}/parsers/akkordbard/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера AkkordBard: {e}")
            return None

    def stop_akkordbard_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/akkordbard/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_akkordbard_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/akkordbard/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера AkkordBard: {e}")
            return None

    def get_akkordbard_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/akkordbard/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_akkordbard_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/akkordbard/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера AkkordBard: {e}")
            return None

    def get_akkordbard_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/akkordbard/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА DOMHVE ============

    def start_domhve_parser(self, start_song, end_song, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/domhve/start"
        data = {"start_song": start_song, "end_song": end_song}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_domhve_parser_sync(self, start_song, end_song):
        url = f"{self.config.API_BASE_URL}/parsers/domhve/start"
        data = {"start_song": start_song, "end_song": end_song}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера Domhve: {e}")
            return None

    def stop_domhve_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/domhve/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_domhve_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/domhve/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера Domhve: {e}")
            return None

    def get_domhve_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/domhve/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_domhve_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/domhve/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера Domhve: {e}")
            return None

    def get_domhve_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/domhve/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ МЕТОДЫ ДЛЯ ПАРСЕРА RUSHSOUND ============

    def start_rushsound_parser(self, start_letter, end_letter, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/rushsound/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        return self._request(url=url, method='POST', data=data, on_success=on_success, on_failure=on_failure,
                             include_auth=True)

    def start_rushsound_parser_sync(self, start_letter, end_letter):
        url = f"{self.config.API_BASE_URL}/parsers/rushsound/start"
        data = {"start_letter": start_letter, "end_letter": end_letter}
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(True), timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка запуска парсера RushSound: {e}")
            return None

    def stop_rushsound_parser(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/rushsound/stop"
        return self._request(url=url, method='POST', on_success=on_success, on_failure=on_failure, include_auth=True)

    def stop_rushsound_parser_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/rushsound/stop"
        try:
            response = self.session.post(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка остановки парсера RushSound: {e}")
            return None

    def get_rushsound_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/rushsound/status"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_rushsound_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/rushsound/status"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Logger.error(f"Ошибка получения статуса парсера RushSound: {e}")
            return None

    def get_rushsound_recent_songs(self, limit=10, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/rushsound/recent?limit={limit}"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    # ============ ОБЩИЕ МЕТОДЫ ============

    def get_active_parser_status(self, on_success=None, on_failure=None):
        url = f"{self.config.API_BASE_URL}/parsers/active"
        return self._request(url=url, method='GET', on_success=on_success, on_failure=on_failure, include_auth=True)

    def get_active_parser_status_sync(self):
        url = f"{self.config.API_BASE_URL}/parsers/active"
        try:
            response = self.session.get(url, headers=self._get_headers(True), timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": True, "data": {"has_active_parser": False}}

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