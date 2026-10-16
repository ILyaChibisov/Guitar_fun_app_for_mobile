# screens/favorites_screen.py
"""
Экран избранного - список любимых песен пользователя

АРХИТЕКТУРА:
- Данные из api._favorites_cache (в памяти)
- Мгновенный рендер через RecycleView (виртуализация)
- Подписка на изменения через api.add_favorites_listener
- Никаких force_refresh при on_enter
- Спиннер только если кэша нет
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.factory import Factory
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.components.loading_spinner import LoadingSpinner
from api.client import api
from utils.notifications import notify

logger = screen_logger('Favorites')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None

# ============ ГЛОБАЛЬНАЯ ТЕКСТУРА ============
_shared_song_texture = None


def init_shared_song_icon():
    global _shared_song_texture
    if _shared_song_texture is not None:
        return _shared_song_texture

    if HAS_ASSETS:
        try:
            icon_data = load_asset_as_bytes('song_png')
            if icon_data:
                img = CoreImage(BytesIO(icon_data), ext="png")
                _shared_song_texture = img.texture
                logger.info("✅ Общая иконка песни загружена")
                return _shared_song_texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки: {e}")
    return None


# ============ КАРТОЧКА ИЗБРАННОЙ ПЕСНИ (RecycleView) ============
class FavoriteSongCard(RecycleDataViewBehavior, MDCard):
    """
    Карточка избранной песни для RecycleView.
    Переиспользуется через refresh_view_attrs.
    """

    artist = StringProperty('')
    title = StringProperty('')
    song_id = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.spacing = dp(10)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self.clip = True

        self._build_ui()

    def _build_ui(self):
        # Иконка
        self.icon_image = Image(
            size_hint=(None, 1),
            width=dp(28),
            allow_stretch=True,
            keep_ratio=True
        )

        if _shared_song_texture:
            self.icon_image.texture = _shared_song_texture
        else:
            self.icon_image.text = "🎵"

        # Текст: исполнитель + название
        text_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_x=1,
            spacing=dp(2),
            pos_hint={'center_y': 0.5}
        )

        self.artist_label = MDLabel(
            font_size=sp(15),
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        self.title_label = MDLabel(
            font_size=sp(11),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)

        # Стрелка
        arrow = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(28),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon_image)
        self.add_widget(text_layout)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        """Вызывается RecycleView при переиспользовании карточки"""
        self.artist = data.get('artist', '')
        self.title = data.get('title', '')
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')

        self.artist_label.text = self.artist
        self.title_label.text = self.title

        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


# ✅ РЕГИСТРИРУЕМ в Factory ДО создания RecycleView
Factory.register('FavoriteSongCard', cls=FavoriteSongCard)


# ============ RECYCLEVIEW ДЛЯ ИЗБРАННОГО ============
class FavoritesRecycleView(RecycleView):
    """
    Виртуализированный список избранного.

    ВАЖНО: viewclass передаётся как КЛАСС (не строка).
    Kivy RecycleView хранит viewclass в ObjectProperty,
    поэтому строка не работает как ожидается.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.clip = True
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]

        # ✅ viewclass — КЛАСС, а не строка!
        self.viewclass = FavoriteSongCard

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(60)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(60),
            orientation='vertical',
            spacing=dp(6),
            padding=[0, 0, 0, dp(12)]
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.add_widget(self.layout_manager)

    def set_favorites(self, favorites, on_click):
        """Устанавливает список избранного. Быстро — просто заменяет data."""
        data = []
        for fav in favorites:
            data.append({
                'song_id': fav.get('id') or fav.get('song_id', 0),
                'artist': fav.get('artist', ''),
                'title': fav.get('title', ''),
                'on_click': on_click,
            })

        logger.info(f"🔍 set_favorites: data={len(data)} элементов")
        if data:
            logger.info(f"🔍 Первый элемент: {data[0]}")

        # ✅ Явно переустанавливаем viewclass перед data (на случай перезаписи)
        self.viewclass = FavoriteSongCard

        self.data = data
        self.refresh_from_data()

        # Сбрасываем скролл на верх
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 1.0), 0.05)

    def clear(self):
        self.data = []
        self.refresh_from_data()


# ============ КАРТОЧКА АВТОРИЗАЦИИ ============
class AuthMessageCard(MDCard):
    """Карточка сообщения для неавторизованных пользователей"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(140)
        self.padding = [dp(20), dp(20), dp(20), dp(20)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.5
        self.clip = True

        self.icon_label = MDLabel(
            text="🔒",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(56),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        self.title_label = MDLabel(
            text="Требуется авторизация",
            font_size=sp(16),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        self.message_label = MDLabel(
            text="Чтобы увидеть ваши избранные треки,\nнеобходимо войти в аккаунт",
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            line_height=1.4
        )

        self.add_widget(self.icon_label)
        self.add_widget(self.title_label)
        self.add_widget(self.message_label)


# ============ ОСНОВНОЙ ЭКРАН ============
class FavoritesScreen(BaseScreen):
    """
    Экран избранного - НА RecycleView

    - Мгновенный рендер из кэша api
    - RecycleView переиспользует карточки
    - Подписка на изменения через api.add_favorites_listener
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'
        self.favorites = []
        self.bg_image = None
        self._main_layout = None
        self.recycle_view = None
        self.loading_spinner = None
        self._top_spacer = None
        self.count_label = None
        self._auth_card = None
        self._empty_card = None
        self._listener_registered = False

        self.init_ui()
        self.load_background()

        Clock.schedule_once(lambda dt: init_shared_song_icon(), 0.05)

        # Подписываемся на изменения избранного
        Clock.schedule_once(lambda dt: self._register_listener(), 0.1)

        logger.info('Экран избранного создан (RecycleView)')

    def _register_listener(self):
        if not self._listener_registered:
            api.add_favorites_listener(self._on_favorites_changed)
            self._listener_registered = True
            logger.info("👂 FavoritesScreen подписан на изменения избранного")

    def load_background(self):
        try:
            if HAS_ASSETS:
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        break

                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")
                    with self.canvas.before:
                        Color(1, 1, 1, 1)
                        self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                    self.bind(pos=self._update_bg, size=self._update_bg)
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        self._main_layout = main_layout

        top_padding = layout_config.get_top_padding()
        top_padding = top_padding - dp(8)
        if top_padding < dp(20):
            top_padding = dp(20)

        self._top_spacer = Widget(size_hint_y=None, height=top_padding)
        main_layout.add_widget(self._top_spacer)

        # ============ КОЛИЧЕСТВО ПЕСЕН ============
        self.count_label = MDLabel(
            text="",
            font_size=sp(13),
            halign="center",
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            opacity=0,
            bold=True
        )
        main_layout.add_widget(self.count_label)

        # ============ RECYCLEVIEW ============
        bottom_padding = layout_config.get_bottom_padding()

        wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), bottom_padding]
        )
        wrapper.clip = True

        self.recycle_view = FavoritesRecycleView()
        wrapper.add_widget(self.recycle_view)

        main_layout.add_widget(wrapper)

        self.add_widget(main_layout)
        logger.info(f"UI избранного построен (RecycleView), bottom_padding={bottom_padding}dp")

    # ============ ОБНОВЛЕНИЕ TopNav ============

    def _update_top_nav(self):
        """Обновляет TopNav на 'Избранное' ТОЛЬКО если этот экран сейчас активен."""
        if not self.manager:
            return
        # Проверяем, что текущий экран — именно favorites
        if self.manager.current != 'favorites':
            return

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.force_update_title("Избранное", show_back=False)

    def _update_count_label(self, total):
        if self.count_label:
            if total == 0:
                self.count_label.text = "Нет песен"
            elif total == 1:
                self.count_label.text = "1 песня"
            elif 2 <= total <= 4:
                self.count_label.text = f"{total} песни"
            else:
                self.count_label.text = f"{total} песен"
            self.count_label.opacity = 1

    # ============ РЕНДЕР СПИСКА ============

    def _clear_extra_widgets(self):
        """Убирает auth/empty карточки, если они есть"""
        if self._auth_card and self._auth_card.parent:
            self._auth_card.parent.remove_widget(self._auth_card)
        self._auth_card = None

        if self._empty_card and self._empty_card.parent:
            self._empty_card.parent.remove_widget(self._empty_card)
        self._empty_card = None

    def _render_favorites(self, favorites):
        """
        Рендерит список избранного через RecycleView.
        Вызывается:
        - при on_enter (из кэша api)
        - при _on_favorites_changed (из api listener)
        - при on_favorites_loaded (после сети)
        """
        # Скрываем спиннер
        self._hide_loading()

        # Проверяем авторизацию
        if not api.is_authenticated():
            self._show_auth_message()
            return

        # Нормализуем
        formatted = self._format_favorites(favorites)
        self.favorites = formatted

        self._update_top_nav()
        self._update_count_label(len(formatted))

        if not formatted:
            self._show_empty()
            return

        # Показываем список
        self._clear_extra_widgets()
        self.recycle_view.set_favorites(formatted, self.on_song_selected)

        # Диагностика
        Clock.schedule_once(lambda dt: self._debug_recycle_view(), 0.2)

        logger.info(f"📄 Отображено {len(formatted)} избранных песен")

    def _debug_recycle_view(self):
        """Диагностика RecycleView - что реально происходит с layout"""
        rv = self.recycle_view
        logger.info("=" * 70)
        logger.info(f"🔍 RECYCLEVIEW ДИАГНОСТИКА:")
        logger.info(f"   rv.size = {rv.size}")
        logger.info(f"   rv.pos = {rv.pos}")
        logger.info(f"   rv.height = {rv.height}")
        logger.info(f"   rv.width = {rv.width}")
        logger.info(f"   rv.data count = {len(rv.data)}")
        logger.info(f"   rv.viewclass = {rv.viewclass}")
        logger.info(f"   rv.viewclass type = {type(rv.viewclass)}")
        logger.info(f"   rv.scroll_y = {rv.scroll_y}")

        # Проверка Factory
        try:
            test_card = Factory.FavoriteSongCard()
            logger.info(f"   ✅ Factory.FavoriteSongCard создаётся: {test_card}")
            logger.info(f"      test_card.size_hint = {test_card.size_hint}")
            logger.info(f"      test_card.height = {test_card.height}")
        except Exception as e:
            logger.error(f"   ❌ Ошибка Factory.FavoriteSongCard: {e}")

        # Проверка layout_manager
        lm = rv.layout_manager
        if lm:
            logger.info(f"   layout_manager = {lm}")
            logger.info(f"   lm.size = {lm.size}")
            logger.info(f"   lm.height = {lm.height}")
            logger.info(f"   lm.minimum_height = {lm.minimum_height}")
            logger.info(f"   lm.default_size = {lm.default_size}")
            logger.info(f"   lm.default_size_hint = {lm.default_size_hint}")
            logger.info(f"   lm.spacing = {lm.spacing}")
            logger.info(f"   lm.padding = {lm.padding}")
            logger.info(f"   lm.children count = {len(lm.children)}")

            # Показать первые 3 дочерних виджета
            for i, child in enumerate(lm.children[:3]):
                logger.info(f"      child[{i}] = {child} size={child.size} pos={child.pos}")
        else:
            logger.error(f"   ❌ layout_manager отсутствует!")

        # Проверка: создан ли хоть один виджет карточки
        logger.info(f"   rv.children count = {len(rv.children)}")
        for i, child in enumerate(rv.children[:3]):
            logger.info(f"      rv.child[{i}] = {child}")

        logger.info("=" * 70)

    def _show_empty(self):
        """Показывает пустое состояние"""
        self._clear_extra_widgets()
        self.recycle_view.clear()

        self._empty_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(120),
            padding=[dp(20), dp(20), dp(20), dp(20)],
            radius=[theme.CORNER_RADIUS_SMALL] * 4,
            md_bg_color=[0, 0, 0, 0.06],
            elevation=0,
            line_color=[1, 1, 1, 0.15],
            line_width=0.5
        )

        icon_label = MDLabel(
            text="❤️",
            font_size=sp(48),
            halign="center",
            size_hint_y=None,
            height=dp(56),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        text_label = MDLabel(
            text="Нет избранных песен",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            bold=True
        )

        self._empty_card.add_widget(icon_label)
        self._empty_card.add_widget(text_label)

        # Вставляем после count_label
        try:
            index = self._main_layout.children.index(self.count_label)
            self._main_layout.add_widget(self._empty_card, index)
        except ValueError:
            self._main_layout.add_widget(self._empty_card)

    def _show_auth_message(self):
        """Показывает сообщение о необходимости авторизации"""
        self._clear_extra_widgets()
        self.recycle_view.clear()
        self._update_top_nav()
        self._update_count_label(0)

        self._auth_card = AuthMessageCard()

        try:
            index = self._main_layout.children.index(self.count_label)
            self._main_layout.add_widget(self._auth_card, index)
        except ValueError:
            self._main_layout.add_widget(self._auth_card)

    def _format_favorites(self, favorites):
        """Форматирует избранное в единый формат"""
        formatted = []
        for item in favorites:
            if isinstance(item, dict):
                if 'id' in item and 'song_id' not in item:
                    item['song_id'] = item['id']
                elif 'song_id' in item and 'id' not in item:
                    item['id'] = item['song_id']
                formatted.append(item)
            elif isinstance(item, str):
                parts = item.split(' - ', 1)
                if len(parts) == 2:
                    formatted.append({
                        'artist': parts[0], 'title': parts[1],
                        'id': 0, 'song_id': 0,
                    })
                else:
                    formatted.append({
                        'artist': '', 'title': item,
                        'id': 0, 'song_id': 0,
                    })
        return formatted

    # ============ ЗАГРУЗКА / СПИННЕР ============

    def _show_loading(self):
        if self.loading_spinner:
            return

        self.loading_spinner = LoadingSpinner(text="Загрузка избранного...")
        self.loading_spinner.start_animation()

        if self._main_layout:
            if self.loading_spinner.parent:
                self.loading_spinner.parent.remove_widget(self.loading_spinner)
            try:
                index = self._main_layout.children.index(self._top_spacer) + 1
                self._main_layout.add_widget(self.loading_spinner, index)
            except ValueError:
                self._main_layout.add_widget(self.loading_spinner)

        self.count_label.opacity = 0

    def _hide_loading(self):
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            if self.loading_spinner.parent:
                self.loading_spinner.parent.remove_widget(self.loading_spinner)
            self.loading_spinner = None

    # ============ ЛОГИКА ЗАГРУЗКИ ============

    def load_favorites(self, force_refresh=False):
        """
        Загружает избранное.
        force_refresh=False — мгновенно из кэша + фоновое обновление.
        force_refresh=True — принудительно с сервера.
        """
        if not api.is_authenticated():
            self._show_auth_message()
            return

        cached = api._load_favorites_cache(allow_stale=True)

        if cached is not None and not force_refresh:
            # МГНОВЕННЫЙ рендер из кэша
            logger.info(f"⚡ Мгновенный рендер из кэша: {len(cached)} песен")
            self._render_favorites(cached)

            if not api._favorites_stale:
                return

            # Фоновое обновление
            logger.info("🔄 Фоновое обновление избранного...")
            api.get_favorites(
                on_success=self._on_background_update,
                on_failure=lambda req, err: logger.warning(f"⚠️ Фоновое обновление: {err}"),
                force_refresh=False
            )
            return

        # Кэша нет или force_refresh
        if cached is None:
            self._show_loading()

        logger.info("🔄 Загрузка избранного с сервера...")
        api.get_favorites(
            on_success=self._on_network_loaded,
            on_failure=self._on_load_failed,
            force_refresh=force_refresh
        )

    def _on_network_loaded(self, favorites):
        logger.info(f"✅ Избранное загружено с сервера: {len(favorites)}")
        self._hide_loading()
        self._render_favorites(favorites)

    def _on_background_update(self, favorites):
        logger.info(f"✅ Фоновое обновление завершено: {len(favorites)}")
        self._render_favorites(favorites)

    def _on_load_failed(self, req, error):
        self._hide_loading()

        error_str = str(error)
        if "401" in error_str or "Unauthorized" in error_str:
            self._show_auth_message()
            return

        logger.error(f"❌ Ошибка загрузки избранного: {error}")

        self._clear_extra_widgets()
        self.recycle_view.clear()

        error_label = MDLabel(
            text="Ошибка загрузки\nПроверьте интернет",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None,
            height=dp(60)
        )

        try:
            index = self._main_layout.children.index(self.count_label)
            self._main_layout.add_widget(error_label, index)
        except ValueError:
            self._main_layout.add_widget(error_label)

        notify.error("Ошибка загрузки избранного")

    # ============ LISTENER ============

    def _on_favorites_changed(self, favorites):
        """Вызывается из api._notify_favorites_changed"""
        logger.info(f"📢 FavoritesScreen получил обновление: {len(favorites)} песен")
        self._render_favorites(favorites)

    # ============ ОБРАБОТЧИКИ ============

    def on_song_selected(self, song_id, song_title):
        if not song_id:
            notify.error("Ошибка: не удалось загрузить песню")
            return

        artist = ""
        for song in self.favorites:
            if song.get('song_id') == song_id or song.get('id') == song_id:
                artist = song.get('artist', '')
                break

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('favorite_detail'):
                favorite_detail_screen = self.manager.get_screen('favorite_detail')
                favorite_detail_screen.set_song(song_id, artist, song_title)
                self.manager.current = 'favorite_detail'
                logger.info(f"✅ Переход на FavoriteDetailScreen: {song_title}")
            elif self.manager.has_screen('song_detail'):
                song_detail_screen = self.manager.get_screen('song_detail')
                song_detail_screen.set_previous_screen('favorites')
                song_detail_screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def refresh_favorites(self):
        """Принудительное обновление (pull-to-refresh)"""
        logger.info("🔄 Принудительное обновление избранного")
        self.load_favorites(force_refresh=True)

    def go_back(self, instance=None):
        logger.info("🔙 go_back: возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_login_success(self):
        """Обработчик успешного входа"""
        logger.info("✅ Успешная авторизация — загружаем избранное")
        self.load_favorites(force_refresh=True)

    # ============ on_enter, on_leave ============

    def on_pre_enter(self):
        self._update_top_nav()

    def on_enter(self):
        """При входе — мгновенный рендер из кэша"""
        logger.info("🚪 Вход в экран избранного")
        self._register_listener()
        self.load_favorites(force_refresh=False)

    def on_leave(self):
        pass

    @staticmethod
    def pre_update_top_nav():
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.force_update_title("Избранное", show_back=False)