# screens/favorites_screen.py
"""
Экран избранного - список любимых песен пользователя.
Адаптирован под 3 темы и 6 языков.
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
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('Favorites')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА ДЛЯ ИЗБРАННОГО
# ============================================================

class FavoritesColors:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        else:
            return [0.46, 0.70, 0.71, 1]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 1]
        else:
            return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        else:
            return [1, 1, 1, 0.5]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.1]
        else:
            return [0, 0, 0, 0.06]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        else:
            return [1, 1, 1, 0.05]

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        else:
            return [0.46, 0.70, 0.71, 1]


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
                return _shared_song_texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки: {e}")
    return None


# ============ КАРТОЧКА ИЗБРАННОЙ ПЕСНИ ============
class FavoriteSongCard(RecycleDataViewBehavior, MDCard):
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
        self.radius = [dp(14)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True

        self._build_ui()
        self.update_theme_colors()

    def _build_ui(self):
        self.icon_image = Image(size_hint=(None, 1), width=dp(28),
                                allow_stretch=True, keep_ratio=True)
        if _shared_song_texture:
            self.icon_image.texture = _shared_song_texture
        else:
            self.icon_image.text = "🎵"

        text_layout = MDBoxLayout(orientation='vertical', size_hint_x=1,
                                  spacing=dp(2), pos_hint={'center_y': 0.5})

        self.artist_label = MDLabel(
            font_size=sp(15), size_hint_y=None, height=dp(24),
            theme_text_color="Custom", bold=True, valign="middle",
            shorten=True, shorten_from="right")
        self.title_label = MDLabel(
            font_size=sp(11), size_hint_y=None, height=dp(18),
            theme_text_color="Custom", valign="middle",
            shorten=True, shorten_from="right")

        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)

        self.arrow = MDLabel(
            text="›", font_size=sp(24), size_hint_x=None, width=dp(28),
            halign="center", theme_text_color="Custom")

        self.add_widget(self.icon_image)
        self.add_widget(text_layout)
        self.add_widget(self.arrow)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = FavoritesColors.get_accent(theme_id)
        self.md_bg_color = FavoritesColors.get_card_bg(theme_id)
        self.line_color = FavoritesColors.get_card_line(theme_id)
        self.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5
        self.artist_label.text_color = FavoritesColors.get_text_primary(theme_id)
        self.title_label.text_color = FavoritesColors.get_text_secondary(theme_id)
        self.arrow.text_color = accent

    def refresh_view_attrs(self, rv, index, data):
        self.artist = data.get('artist', '')
        self.title = data.get('title', '')
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.artist_label.text = self.artist
        self.title_label.text = self.title
        self.update_theme_colors()
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


Factory.register('FavoriteSongCard', cls=FavoriteSongCard)


# ============ RECYCLEVIEW ============
class FavoritesRecycleView(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)
        self.clip = True
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]
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
        data = []
        for fav in favorites:
            data.append({
                'song_id': fav.get('id') or fav.get('song_id', 0),
                'artist': fav.get('artist', ''),
                'title': fav.get('title', ''),
                'on_click': on_click,
            })
        self.viewclass = FavoriteSongCard
        self.data = data
        self.refresh_from_data()
        Clock.schedule_once(lambda dt: setattr(self, 'scroll_y', 1.0), 0.05)

    def clear(self):
        self.data = []
        self.refresh_from_data()


# ============ КАРТОЧКА АВТОРИЗАЦИИ ============
class AuthMessageCard(MDCard):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(140)
        self.padding = [dp(20), dp(20), dp(20), dp(20)]
        self.spacing = dp(12)
        self.radius = [dp(14)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True

        self.icon_label = MDLabel(
            text="🔒", font_size=sp(48), halign="center",
            size_hint_y=None, height=dp(56), theme_text_color="Custom")
        self.title_label = MDLabel(
            text=get_text('auth_required_title'), font_size=sp(16),
            halign="center", size_hint_y=None, height=dp(30),
            theme_text_color="Custom", bold=True)
        self.message_label = MDLabel(
            text=get_text('auth_required_message'), font_size=sp(12),
            halign="center", size_hint_y=None, height=dp(50),
            theme_text_color="Custom", line_height=1.4)

        self.add_widget(self.icon_label)
        self.add_widget(self.title_label)
        self.add_widget(self.message_label)
        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = FavoritesColors.get_accent(theme_id)
        self.md_bg_color = FavoritesColors.get_card_bg(theme_id)
        self.line_color = FavoritesColors.get_card_line(theme_id)
        self.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5
        self.icon_label.text_color = accent
        self.title_label.text_color = FavoritesColors.get_text_primary(theme_id)
        self.message_label.text_color = FavoritesColors.get_text_secondary(theme_id)


# ============ ОСНОВНОЙ ЭКРАН ============
class FavoritesScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'
        self.favorites = []
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self._main_layout = None
        self.recycle_view = None
        self.loading_spinner = None
        self._top_spacer = None
        self.count_label = None
        self._auth_card = None
        self._empty_card = None
        self._error_label = None
        self._listener_registered = False

        self.load_background()
        self.init_ui()

        Clock.schedule_once(lambda dt: init_shared_song_icon(), 0.05)
        Clock.schedule_once(lambda dt: self._register_listener(), 0.1)

        logger.info('Экран избранного создан (RecycleView)')

    def _register_listener(self):
        if not self._listener_registered:
            api.add_favorites_listener(self._on_favorites_changed)
            self._listener_registered = True

    def load_background(self):
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        self.texture = None
        try:
            if HAS_ASSETS:
                bg_data = load_asset_as_bytes("background_jpg")
                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")
                    self.texture = img.texture
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')
        self.update_screen_background()

    def _update_rect(self, *args):
        if hasattr(self, 'bg_rect') and self.bg_rect:
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def update_screen_background(self):
        if not hasattr(self, 'bg_color_inst') or not hasattr(self, 'bg_rect'):
            return
        theme_id = settings_manager.theme
        if theme_id == 'green':
            if self.texture:
                self.bg_rect.texture = self.texture
                self.bg_color_inst.rgba = (1, 1, 1, 1)
            else:
                self.bg_rect.texture = None
                self.bg_color_inst.rgba = (0.1, 0.3, 0.2, 1)
        elif theme_id == 'dark':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.07, 0.07, 0.07, 1)
        elif theme_id == 'light':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.969, 0.976, 0.969, 1)

    def update_theme_colors(self):
        self.update_screen_background()
        theme_id = settings_manager.theme
        if hasattr(self, 'count_label'):
            self.count_label.text_color = FavoritesColors.get_accent(theme_id)
        if self._auth_card:
            self._auth_card.update_theme_colors()
        if self._empty_card:
            for child in self._empty_card.children:
                if hasattr(child, 'text_color'):
                    if child.font_size > sp(40):
                        child.text_color = FavoritesColors.get_accent(theme_id)
                    else:
                        child.text_color = FavoritesColors.get_text_primary(theme_id)
        if self.recycle_view:
            for child in self.recycle_view.layout_manager.children:
                if hasattr(child, 'update_theme_colors'):
                    child.update_theme_colors()

    def update_language(self):
        if self._auth_card:
            self._auth_card.title_label.text = get_text('auth_required_title')
            self._auth_card.message_label.text = get_text('auth_required_message')
        if self.count_label and self.count_label.opacity > 0:
            self._update_count_label(len(self.favorites))

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        self._main_layout = main_layout

        top_padding = max(layout_config.get_top_padding() - dp(8), dp(20))
        self._top_spacer = Widget(size_hint_y=None, height=top_padding)
        main_layout.add_widget(self._top_spacer)

        self.count_label = MDLabel(
            text="", font_size=sp(13), halign="center",
            size_hint_y=None, height=dp(28),
            theme_text_color="Custom", opacity=0, bold=True)
        main_layout.add_widget(self.count_label)

        bottom_padding = layout_config.get_bottom_padding()

        wrapper = MDBoxLayout(orientation='vertical', size_hint=(1, 1),
                              padding=[dp(12), dp(4), dp(12), bottom_padding])
        wrapper.clip = True

        self.recycle_view = FavoritesRecycleView()
        wrapper.add_widget(self.recycle_view)

        main_layout.add_widget(wrapper)
        self.add_widget(main_layout)

        self.update_theme_colors()

    def _update_top_nav(self):
        if not self.manager or self.manager.current != 'favorites':
            return
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.force_update_title(get_text('favorites'), show_back=False)

    def _update_count_label(self, total):
        if not self.count_label:
            return
        if total == 0:
            self.count_label.text = get_text('no_songs')
        elif total == 1:
            self.count_label.text = f"1 {get_text('song_one')}"
        else:
            self.count_label.text = f"{total} {get_text('songs_many')}"
        self.count_label.opacity = 1

    def _clear_extra_widgets(self):
        if self._auth_card and self._auth_card.parent:
            self._auth_card.parent.remove_widget(self._auth_card)
        self._auth_card = None

        if self._empty_card and self._empty_card.parent:
            self._empty_card.parent.remove_widget(self._empty_card)
        self._empty_card = None

        if self._error_label and self._error_label.parent:
            self._error_label.parent.remove_widget(self._error_label)
        self._error_label = None

    def _render_favorites(self, favorites):
        self._hide_loading()
        if not api.is_authenticated():
            self._show_auth_message()
            return

        formatted = self._format_favorites(favorites)
        self.favorites = formatted

        self._update_top_nav()
        self._update_count_label(len(formatted))

        if not formatted:
            self._show_empty()
            return

        self._clear_extra_widgets()
        self.recycle_view.set_favorites(formatted, self.on_song_selected)

    def _show_empty(self):
        self._clear_extra_widgets()
        self.recycle_view.clear()
        theme_id = settings_manager.theme
        accent = FavoritesColors.get_accent(theme_id)

        self._empty_card = MDCard(
            orientation='vertical', size_hint=(1, None), height=dp(120),
            padding=[dp(20)] * 4, radius=[dp(14)] * 4,
            md_bg_color=FavoritesColors.get_card_bg(theme_id),
            elevation=0, line_color=FavoritesColors.get_card_line(theme_id),
            line_width=1.0 if theme_id in ('dark', 'light') else 0.5)

        icon = MDLabel(text="❤️", font_size=sp(48), halign="center",
                       size_hint_y=None, height=dp(56),
                       theme_text_color="Custom", text_color=accent)
        text = MDLabel(text=get_text('no_favorites'), font_size=sp(14),
                       halign="center", size_hint_y=None, height=dp(30),
                       theme_text_color="Custom", bold=True,
                       text_color=FavoritesColors.get_text_primary(theme_id))

        self._empty_card.add_widget(icon)
        self._empty_card.add_widget(text)

        try:
            index = self._main_layout.children.index(self.count_label)
            self._main_layout.add_widget(self._empty_card, index)
        except ValueError:
            self._main_layout.add_widget(self._empty_card)

    def _show_auth_message(self):
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
                    formatted.append({'artist': parts[0], 'title': parts[1],
                                      'id': 0, 'song_id': 0})
                else:
                    formatted.append({'artist': '', 'title': item,
                                      'id': 0, 'song_id': 0})
        return formatted

    def _show_loading(self):
        if self.loading_spinner:
            return
        self.loading_spinner = LoadingSpinner(text=get_text('loading_favorites'))
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

    def load_favorites(self, force_refresh=False):
        if not api.is_authenticated():
            self._show_auth_message()
            return

        cached = api._load_favorites_cache(allow_stale=True)

        if cached is not None and not force_refresh:
            self._render_favorites(cached)
            if not api._favorites_stale:
                return
            api.get_favorites(
                on_success=self._on_background_update,
                on_failure=lambda req, err: logger.warning(f"Фоновое обновление: {err}"),
                force_refresh=False)
            return

        if cached is None:
            self._show_loading()

        api.get_favorites(
            on_success=self._on_network_loaded,
            on_failure=self._on_load_failed,
            force_refresh=force_refresh)

    def _on_network_loaded(self, favorites):
        self._hide_loading()
        self._render_favorites(favorites)

    def _on_background_update(self, favorites):
        self._render_favorites(favorites)

    def _on_load_failed(self, req, error):
        self._hide_loading()
        error_str = str(error)
        if "401" in error_str or "Unauthorized" in error_str:
            self._show_auth_message()
            return
        self._clear_extra_widgets()
        self.recycle_view.clear()

        theme_id = settings_manager.theme
        self._error_label = MDLabel(
            text=get_text('loading_error'), halign="center",
            font_size=sp(14), theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None, height=dp(60))
        try:
            index = self._main_layout.children.index(self.count_label)
            self._main_layout.add_widget(self._error_label, index)
        except ValueError:
            self._main_layout.add_widget(self._error_label)
        notify.error(get_text('loading_error'))

    def _on_favorites_changed(self, favorites):
        self._render_favorites(favorites)

    def on_song_selected(self, song_id, song_title):
        if not song_id:
            notify.error(get_text('load_error'))
            return
        artist = ""
        for song in self.favorites:
            if song.get('song_id') == song_id or song.get('id') == song_id:
                artist = song.get('artist', '')
                break
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('favorite_detail'):
                screen = self.manager.get_screen('favorite_detail')
                screen.set_song(song_id, artist, song_title)
                self.manager.current = 'favorite_detail'
            elif self.manager.has_screen('song_detail'):
                screen = self.manager.get_screen('song_detail')
                screen.set_previous_screen('favorites')
                screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def refresh_favorites(self):
        self.load_favorites(force_refresh=True)

    def go_back(self, instance=None):
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_login_success(self):
        self.load_favorites(force_refresh=True)

    def on_pre_enter(self):
        self._update_top_nav()

    def on_enter(self):
        super().on_enter()

        self._register_listener()
        self.load_favorites(force_refresh=False)

    def on_leave(self):
        pass

    @staticmethod
    def pre_update_top_nav():
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.force_update_title(get_text('favorites'), show_back=False)