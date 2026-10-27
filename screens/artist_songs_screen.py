# screens/artist_songs_screen.py
"""
Экран списка песен исполнителя.
"""
import time
import unicodedata
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from io import BytesIO
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.animation import Animation
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty

from kivymd.app import MDApp
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton

from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from screens.components.loading_spinner import LoadingSpinner
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
from state.artist_songs_state import artist_songs_state
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = screen_logger('ArtistSongs')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class ArtistColors:
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
        return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        return [1, 1, 1, 0.7]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.1]
        return [0, 0, 0, 0.10]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        return [1, 1, 1, 0.25]

    @staticmethod
    def get_card_line_width(theme_id):
        return 2.0

    @staticmethod
    def get_hint_color(theme_id):
        if theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        return [0.46, 0.70, 0.71, 1]

    @staticmethod
    def get_count_color(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        return [1, 1, 1, 1]

    @staticmethod
    def get_arrow_color(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 1]
        return [1, 1, 1, 1]


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
            logger.error(f"Ошибка загрузки иконки песни: {e}")
    return None


class RecycleSongCard(RecycleDataViewBehavior, MDCard):
    title = StringProperty('')
    tabs_count = NumericProperty(0)
    song_id = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.padding = [0, dp(4), 0, dp(4)]
        self.spacing = dp(8)
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self.theme_line_color = "Custom"
        self.theme_bg_color = "Custom"
        self._build_ui()
        self.update_theme_colors()

    def _build_ui(self):
        content = MDBoxLayout(
            orientation='horizontal',
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]
        )
        self.icon = Image(
            size_hint=(None, 1), width=dp(24),
            allow_stretch=True, keep_ratio=True
        )
        if _shared_song_texture:
            self.icon.texture = _shared_song_texture
        else:
            self.icon.text = "🎵"

        self.title_label = MDLabel(
            font_size=sp(15), theme_text_color="Custom", bold=True,
            shorten=True, shorten_from="right", valign="middle", size_hint_x=1
        )
        self.count_label = MDLabel(
            text="", font_size=sp(12), size_hint_x=None, width=dp(40),
            halign="right", valign="middle", theme_text_color="Custom"
        )
        self.arrow = MDLabel(
            text="›", font_size=sp(20), size_hint_x=None, width=dp(20),
            halign="center", valign="middle", theme_text_color="Custom"
        )
        content.add_widget(self.icon)
        content.add_widget(self.title_label)
        content.add_widget(self.count_label)
        content.add_widget(self.arrow)
        self.add_widget(content)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = ArtistColors.get_accent(theme_id)
        self.md_bg_color = ArtistColors.get_card_bg(theme_id)
        self.line_color = ArtistColors.get_card_line(theme_id)
        self.line_width = ArtistColors.get_card_line_width(theme_id)
        self.title_label.text_color = ArtistColors.get_text_primary(theme_id)
        self.count_label.text_color = ArtistColors.get_text_secondary(theme_id)
        self.arrow.text_color = accent

    def refresh_view_attrs(self, rv, index, data):
        self.title = data.get('title', '')
        self.tabs_count = data.get('tabs_count', 0)
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.title_label.text = self.title
        if self.tabs_count and self.tabs_count > 1:
            self.count_label.text = str(self.tabs_count)
        else:
            self.count_label.text = ""
        self.update_theme_colors()
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.song_id, self.title)
            return True
        return super().on_touch_down(touch)


from kivy.factory import Factory

Factory.register('RecycleSongCard', cls=RecycleSongCard)


class SongRecycleView(RecycleView):
    def __init__(self, on_song_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_song_click = on_song_click
        self.animate_scroll = False
        self.size_hint = (1, 1)
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]
        self.clip = True
        self.scroll_type = ['bars', 'content']
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)), default_size_hint=(1, None),
            size_hint_y=None, height=dp(48) * 50,
            orientation='vertical', spacing=dp(4),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.viewclass = 'RecycleSongCard'
        self.add_widget(self.layout_manager)

    def set_songs(self, songs, on_click):
        data = []
        for song in songs:
            data.append({
                'song_id': song.get('song_id', 0),
                'title': song.get('title', ''),
                'tabs_count': song.get('tabs_count', 1),
                'on_click': on_click
            })
        self.data = data
        self.refresh_from_data()

    def clear(self):
        self.data = []
        self.refresh_from_data()


# ============ ПАГИНАЦИЯ ============

class PaginationArrow(MDBoxLayout):
    DEFAULT_WIDTH = dp(40)

    def __init__(self, icon_name, on_press=None,
                 icon_color=None, width=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = width if width else self.DEFAULT_WIDTH
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]

        self._on_press = on_press
        self._enabled = True
        self._pressed = False

        container = AnchorLayout(anchor_x='center', anchor_y='center',
                                 size_hint=(1, 1))
        self.icon_widget = MDIcon(
            icon=icon_name, font_size=sp(22),
            theme_text_color="Custom",
            text_color=icon_color if icon_color else [1, 1, 1, 1],
            size_hint=(None, None), size=(dp(24), dp(24)),
        )
        container.add_widget(self.icon_widget)
        self.add_widget(container)

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.opacity = 1.0 if enabled else 0.3

    def set_color(self, color):
        self.icon_widget.text_color = color

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if not self._enabled:
            return True
        self._pressed = True
        touch.grab(self)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        if self._pressed:
            self._pressed = False
            if self._enabled and self.collide_point(*touch.pos) and self._on_press:
                self._on_press()
        return True


class PaginationBar(MDBoxLayout):
    def __init__(self, on_page_select=None, **kwargs):
        super().__init__(**kwargs)
        self.on_page_select = on_page_select
        self.current_page_index = 0
        self.total_pages = 1
        self._last_total = None
        self._last_per_page = None

        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.height = dp(48)
        self.padding = [dp(4), 0, dp(4), 0]
        self.spacing = dp(4)
        self.md_bg_color = [0, 0, 0, 0]

        self.jump_back_arrow = PaginationArrow(
            icon_name="chevron-double-left",
            on_press=self._go_back_10,
            width=dp(36),
        )
        self.add_widget(self.jump_back_arrow)

        self.prev_arrow = PaginationArrow(
            icon_name="chevron-left",
            on_press=self._go_prev_page,
            width=dp(36),
        )
        self.add_widget(self.prev_arrow)

        self.page_label = MDLabel(
            text="1",
            font_size=sp(16),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            size_hint=(None, 1),
            width=dp(40),
        )
        self.add_widget(self.page_label)

        self.next_arrow = PaginationArrow(
            icon_name="chevron-right",
            on_press=self._go_next_page,
            width=dp(36),
        )
        self.add_widget(self.next_arrow)

        self.jump_forward_arrow = PaginationArrow(
            icon_name="chevron-double-right",
            on_press=self._go_forward_10,
            width=dp(36),
        )
        self.add_widget(self.jump_forward_arrow)

        self._update_width()
        self.update_theme_colors()

    def on_touch_down(self, touch):
        if self.parent is not None and self.parent.height < dp(10):
            return False
        return super().on_touch_down(touch)

    def _update_width(self):
        w = (
                dp(4) + dp(4)
                + self.jump_back_arrow.width + self.spacing
                + self.prev_arrow.width + self.spacing
                + self.page_label.width + self.spacing
                + self.next_arrow.width + self.spacing
                + self.jump_forward_arrow.width
        )
        self.width = w

    def set_total(self, total_items, per_page, current_page=0, on_click=None):
        if on_click:
            self.on_page_select = on_click
        new_total_pages = max(1, (total_items + per_page - 1) // per_page)

        if (self._last_total == total_items
                and self._last_per_page == per_page
                and self.total_pages == new_total_pages):
            self.set_current_page(current_page)
            return

        self._last_total = total_items
        self._last_per_page = per_page
        self.total_pages = new_total_pages
        self.current_page_index = max(0, min(current_page, self.total_pages - 1))
        self._apply_page()
        self.update_theme_colors()

    def set_current_page(self, page):
        self.current_page_index = max(0, min(page, self.total_pages - 1))
        self._apply_page()

    def _apply_page(self):
        self.page_label.text = str(self.current_page_index + 1)
        digits = len(str(self.total_pages))
        self.page_label.width = dp(12) * max(2, digits) + dp(4)

        at_first = self.current_page_index == 0
        at_last = self.current_page_index >= self.total_pages - 1

        self.jump_back_arrow.set_enabled(not at_first)
        self.prev_arrow.set_enabled(not at_first)
        self.next_arrow.set_enabled(not at_last)
        self.jump_forward_arrow.set_enabled(not at_last)

        self._update_width()

    def _go_back_10(self):
        if self.current_page_index <= 0:
            return
        new_index = max(0, self.current_page_index - 10)
        self.current_page_index = new_index
        self._apply_page()
        if self.on_page_select:
            self.on_page_select(new_index)

    def _go_prev_page(self):
        if self.current_page_index <= 0:
            return
        new_index = self.current_page_index - 1
        self.current_page_index = new_index
        self._apply_page()
        if self.on_page_select:
            self.on_page_select(new_index)

    def _go_next_page(self):
        if self.current_page_index >= self.total_pages - 1:
            return
        new_index = self.current_page_index + 1
        self.current_page_index = new_index
        self._apply_page()
        if self.on_page_select:
            self.on_page_select(new_index)

    def _go_forward_10(self):
        if self.current_page_index >= self.total_pages - 1:
            return
        new_index = min(self.total_pages - 1, self.current_page_index + 10)
        self.current_page_index = new_index
        self._apply_page()
        if self.on_page_select:
            self.on_page_select(new_index)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        arrow_color = ArtistColors.get_arrow_color(theme_id)
        self.jump_back_arrow.set_color(arrow_color)
        self.jump_forward_arrow.set_color(arrow_color)
        self.prev_arrow.set_color(arrow_color)
        self.next_arrow.set_color(arrow_color)
        self.page_label.text_color = ArtistColors.get_text_primary(theme_id)


# ============ ОСНОВНОЙ ЭКРАН ============

class ArtistSongsScreen(BaseScreen):
    MIN_PAGE_SIZE = 3
    MAX_PAGE_SIZE = 15
    PAGINATION_HEIGHT = dp(48) + dp(1) + dp(2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artist_songs'
        self.artist_name = ''
        self._pending_artist = None

        self._page = 0
        self._page_size = 10
        self._page_size_locked = False
        self._batch_size = 200
        self._total_songs = 0
        self._songs_cache = {}

        self._batch_loading = False
        self._pending_page = None
        self._is_loading = False

        self._saved_scroll_position = 1.0
        self._is_restoring = False
        self._last_display_key = None

        self.recycle_view = None
        self._main_layout = None
        self.loading_spinner = None
        self.empty_label = None
        self.bg_color_inst = None
        self.bg_rect = None
        self.texture = None
        self.count_label = None
        self._pagination_bar = None
        self._loading_spinner = None
        self._loading_spinner_widget = None

        self._initialized = False
        self._going_back = False
        self._last_window_size = None

        init_shared_song_icon()

        self.load_background()
        self.init_ui()
        logger.info('Экран песен исполнителя создан')

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
        if hasattr(self, 'count_label') and self.count_label:
            self.count_label.text_color = ArtistColors.get_count_color(theme_id)
        if self.empty_label:
            self.empty_label.text_color = ArtistColors.get_hint_color(theme_id)
        if self._pagination_bar:
            self._pagination_bar.update_theme_colors()
        if self.recycle_view:
            for child in self.recycle_view.layout_manager.children:
                if hasattr(child, 'update_theme_colors'):
                    child.update_theme_colors()

    def update_language(self):
        if hasattr(self, 'count_label') and self.count_label.opacity > 0:
            self._update_count_label(self._total_songs)

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        self._main_layout = main_layout

        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        self.count_label = MDLabel(
            text="", font_size=sp(13), halign="center",
            size_hint_y=None, height=dp(28),
            theme_text_color="Custom", opacity=0, bold=True
        )
        main_layout.add_widget(self.count_label)

        # Контейнер для карточек
        self._cards_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), dp(4)],
            md_bg_color=[0, 0, 0, 0]
        )
        self.recycle_view = SongRecycleView(on_song_click=self.on_song_selected)
        self._cards_container.add_widget(self.recycle_view)
        main_layout.add_widget(self._cards_container)

        # Пагинация
        self._pagination_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=0,
            md_bg_color=[0, 0, 0, 0],
        )
        self._pagination_anchor = FloatLayout(size_hint=(1, 1))
        self._pagination_bar = PaginationBar(on_page_select=self._on_page_selected_from_bar)
        self._pagination_bar.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self._pagination_anchor.add_widget(self._pagination_bar)
        self._pagination_container.add_widget(self._pagination_anchor)
        main_layout.add_widget(self._pagination_container)

        # Нижний отступ
        if platform == 'android':
            bottom_padding = layout_config.get_bottom_nav_height() + get_navigation_bar_height()
        else:
            bottom_padding = layout_config.get_bottom_nav_height() + dp(4)
        main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))

        self.add_widget(main_layout)
        self._initialized = True
        self.update_theme_colors()

        Clock.schedule_once(lambda dt: self._recalc_page_size(force=True), 0.3)

    # ============ РАЗМЕР СТРАНИЦЫ ============

    def _calc_page_size(self):
        if platform == 'android':
            bottom_pad = layout_config.get_bottom_nav_height() + get_navigation_bar_height()
        else:
            bottom_pad = layout_config.get_bottom_nav_height() + dp(4)

        fixed_h = (
                layout_config.get_top_padding()
                + dp(28)  # count_label
                + dp(8)  # padding карточек
                + self.PAGINATION_HEIGHT  # пагинация
                + bottom_pad
        )
        available_h = Window.height - fixed_h
        if available_h <= 0:
            return self.MIN_PAGE_SIZE

        card_h = dp(48) + dp(4)
        n = int(available_h / card_h)
        return max(self.MIN_PAGE_SIZE, min(self.MAX_PAGE_SIZE, n))

    def _recalc_page_size(self, force=False):
        if self._page_size_locked and not force:
            return
        new_size = self._calc_page_size()
        if new_size == self._page_size:
            if not self._page_size_locked:
                self._page_size_locked = True
                logger.info(f"📐 PAGE_SIZE зафиксирован: {new_size}")
            return
        self._page_size = new_size
        self._page_size_locked = True
        logger.info(f"📐 PAGE_SIZE определён: {new_size}")
        if self.artist_name:
            self._ensure_valid_page()
            self._display_page(self._build_page_slice(
                self._songs_cache.get(self.artist_name, {'items': {}, 'total': 0}),
                self._page
            ))

    def on_size(self, *args):
        current_size = (Window.width, Window.height)
        if self._last_window_size is not None:
            old_w, old_h = self._last_window_size
            if (abs(old_w - current_size[0]) < dp(50)
                    and abs(old_h - current_size[1]) < dp(50)):
                return
        self._last_window_size = current_size
        if self._page_size_locked:
            Clock.schedule_once(lambda dt: self._recalc_on_rotation(), 0.3)

    def _recalc_on_rotation(self):
        new_size = self._calc_page_size()
        if new_size != self._page_size:
            self._page_size = new_size
            if self.artist_name:
                self._ensure_valid_page()
                cache = self._songs_cache.get(self.artist_name)
                if cache:
                    self._display_page(self._build_page_slice(cache, self._page))

    def _get_page_size(self):
        return self._page_size

    def _ensure_valid_page(self):
        page_size = self._get_page_size()
        if self._total_songs <= 0:
            self._page = 0
            return
        max_page = (self._total_songs - 1) // page_size
        if self._page > max_page:
            self._page = max_page

    # ============ COUNT LABEL ============

    def _update_count_label(self, total):
        if not self.count_label:
            return
        if total == 0:
            self.count_label.text = get_text('no_songs')
            self.count_label.opacity = 1
            return
        page_size = self._get_page_size()
        if total > page_size:
            current_count = min((self._page + 1) * page_size, total)
            self.count_label.text = (
                f"{current_count} {get_text('of')} {total} {get_text('songs_many')}"
            )
        elif total == 1:
            self.count_label.text = f"1 {get_text('song_one')}"
        else:
            self.count_label.text = f"{total} {get_text('songs_many')}"
        self.count_label.opacity = 1

    def _update_top_nav_title(self, artist=None):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            artist_name = artist if artist is not None else self.artist_name
            if artist_name:
                display_name = artist_name if len(artist_name) <= 25 else artist_name[:22] + "..."
                app.top_nav.set_custom_title(display_name)

    # ============ ПАГИНАЦИЯ ============

    def _hide_pagination(self):
        if not self._pagination_container:
            return
        self._pagination_container.height = 0
        self._pagination_container.opacity = 0
        self._pagination_container.disabled = True

    def _show_pagination_bar(self):
        if not self._pagination_container:
            return
        self._pagination_container.height = self.PAGINATION_HEIGHT
        self._pagination_container.opacity = 1
        self._pagination_container.disabled = False
        self._pagination_bar.set_total(self._total_songs, self._get_page_size(), self._page)

    def _on_page_selected_from_bar(self, page_index):
        if page_index == self._page:
            return
        self._load_page(page_index)

    def _is_page_cached(self, cache, page):
        page_size = self._get_page_size()
        start = page * page_size
        total = cache['total']
        end = min(start + page_size, total) if total else start + page_size
        for idx in range(start, end):
            if idx not in cache['items']:
                return False
        return True

    def _build_page_slice(self, cache, page):
        page_size = self._get_page_size()
        start = page * page_size
        end = start + page_size
        total = cache['total']
        if total:
            end = min(end, total)
        result = []
        for idx in range(start, end):
            item = cache['items'].get(idx)
            if item is not None:
                result.append(item)
        return result

    def _load_page(self, page):
        if not self.artist_name:
            return
        cache = self._songs_cache.get(self.artist_name)
        if cache is None:
            return
        self._total_songs = cache['total']
        self._page = page
        if self._is_page_cached(cache, page):
            self._update_count_label(self._total_songs)
            self._display_page(self._build_page_slice(cache, page))
            return
        if self._batch_loading:
            self._pending_page = page
            return
        batch_offset = (page * self._get_page_size()) // self._batch_size * self._batch_size
        self._load_batch(self.artist_name, batch_offset, page)

    def _load_batch(self, artist, batch_offset, target_page):
        cache = self._songs_cache.get(artist)
        if cache is None:
            cache = {'items': {}, 'total': 0, 'batches': set()}
            self._songs_cache[artist] = cache
        if batch_offset in cache['batches']:
            self._batch_loading = False
            self._display_page(self._build_page_slice(cache, target_page))
            return
        self._batch_loading = True
        self._show_loading_spinner()

        def _on_success(data):
            try:
                self._batch_loading = False
                self._is_loading = False
                if data is None or not isinstance(data, dict):
                    data = {"songs": [], "total": 0}

                if data.get('error'):
                    self._hide_loading_spinner()
                    self._show_empty("Нет ответа от сервера. Проверьте интернет.")
                    return

                songs = data.get('songs', [])
                total = data.get('total', 0)
                if not isinstance(songs, list):
                    songs = []
                for i, s in enumerate(songs):
                    sid = s.get('song_id', 0) if isinstance(s, dict) else 0
                    title = s.get('title', '') if isinstance(s, dict) else ''
                    tabs = s.get('tabs_count', 1) if isinstance(s, dict) else 1
                    cache['items'][batch_offset + i] = {
                        'song_id': sid, 'title': title, 'tabs_count': tabs,
                    }
                if total > 0:
                    cache['total'] = total
                if batch_offset not in cache['batches']:
                    cache['batches'].add(batch_offset)
                self._total_songs = cache['total']

                show_page = self._pending_page
                self._pending_page = None
                if show_page is None:
                    show_page = target_page
                self._page = show_page
                self._ensure_valid_page()

                if not self._is_page_cached(cache, self._page):
                    if cache['total'] and self._page * self._get_page_size() >= cache['total']:
                        self._hide_loading_spinner()
                        self._update_count_label(self._total_songs)
                        self._display_page(self._build_page_slice(cache, self._page))
                        return
                    page_size = self._get_page_size()
                    batch_offset2 = (self._page * page_size) // self._batch_size * self._batch_size
                    self._load_batch(artist, batch_offset2, self._page)
                    return
                self._hide_loading_spinner()
                self._update_top_nav_title(artist)
                self._update_count_label(self._total_songs)
                self._display_page(self._build_page_slice(cache, self._page))
            except Exception as e:
                self._batch_loading = False
                self._is_loading = False
                self._pending_page = None
                self._hide_loading_spinner()
                logger.error(f"❌ Ошибка _on_success (artist_songs): {e}")
                self._show_empty(get_text('loading_error'))

        def _on_error(req, err):
            self._batch_loading = False
            self._is_loading = False
            self._pending_page = None
            self._hide_loading_spinner()
            logger.error(f"Ошибка загрузки песен '{artist}': {err}")
            self._update_top_nav_title(artist)
            self._show_empty("Нет ответа от сервера. Проверьте интернет.")

        api.get_songs_by_artist(
            artist=artist,
            limit=self._batch_size,
            offset=batch_offset,
            on_success=_on_success,
            on_failure=_on_error
        )

    def _display_page(self, songs_slice):
        if not songs_slice:
            if self._total_songs == 0:
                self._show_empty()
            if self.recycle_view:
                self.recycle_view.clear()
            self._hide_pagination()
            return
        self._hide_empty()
        first_song = songs_slice[0].get('song_id', 0) if songs_slice else 0
        display_key = (self.artist_name, self._page, len(songs_slice), first_song)
        if self._last_display_key != display_key:
            if self.recycle_view:
                self.recycle_view.set_songs(songs_slice, self.on_song_selected)
            self._last_display_key = display_key
            Clock.schedule_once(lambda dt: setattr(self.recycle_view, 'scroll_y', 1.0), 0.1)

        # ✅ Пагинация показывается ВСЕГДА
        self._show_pagination_bar()

    # ============ ОСНОВНЫЕ МЕТОДЫ ============

    def set_artist(self, artist):
        self.artist_name = artist
        self._total_songs = 0
        self._page = 0
        self._is_loading = False
        self._batch_loading = False
        self._pending_page = None
        self._last_display_key = None
        self._update_top_nav_title(artist)
        self._update_count_label(0)
        if self.manager and self.manager.current == self.name:
            self._load_artist_songs(artist)
        else:
            self._pending_artist = artist

    def _load_artist_songs(self, artist):
        if self._is_loading:
            return
        self._is_loading = True
        self.artist_name = artist
        self._page = 0
        self._batch_loading = False
        self._pending_page = None
        self._last_display_key = None
        if self.recycle_view:
            self.recycle_view.clear()
        self._hide_empty()
        self._hide_pagination()
        self._show_loading_spinner()
        cache = self._songs_cache.get(artist)
        if cache is not None and self._is_page_cached(cache, 0):
            self._is_loading = False
            self._hide_loading_spinner()
            self._total_songs = cache['total']
            self._ensure_valid_page()
            self._update_top_nav_title(artist)
            self._update_count_label(self._total_songs)
            self._display_page(self._build_page_slice(cache, 0))
            return
        self._songs_cache[artist] = {'items': {}, 'total': 0, 'batches': set()}
        self._load_batch(artist, batch_offset=0, target_page=0)

    def _show_loading_spinner(self):
        if self._loading_spinner:
            return
        overlay = FloatLayout(size_hint=(1, 1))
        spinner = LoadingSpinner(text=get_text('loading', 'Загрузка'))
        spinner.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        overlay_color = spinner.get_overlay_color()
        with overlay.canvas.before:
            Color(*overlay_color)
            rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(
            pos=lambda inst, val: setattr(rect, 'pos', val),
            size=lambda inst, val: setattr(rect, 'size', val),
        )
        overlay.add_widget(spinner)
        spinner.start_animation()
        self._loading_spinner = overlay
        self._loading_spinner_widget = spinner
        self.add_widget(overlay)

    def _hide_loading_spinner(self):
        if not self._loading_spinner:
            return
        if self._loading_spinner_widget:
            self._loading_spinner_widget.stop_animation()
            self._loading_spinner_widget = None
        if self._loading_spinner.parent:
            self._loading_spinner.parent.remove_widget(self._loading_spinner)
        self._loading_spinner = None

    def _show_empty(self, text=None):
        if self.empty_label:
            return
        theme_id = settings_manager.theme
        self.empty_label = MDLabel(
            text=text or get_text('no_artist_songs', 'Нет песен у этого исполнителя'),
            halign="center", font_size=sp(14),
            theme_text_color="Custom",
            text_color=ArtistColors.get_hint_color(theme_id),
            size_hint_y=None, height=dp(60)
        )
        if self._cards_container:
            self._cards_container.add_widget(self.empty_label)

    def _hide_empty(self):
        if self.empty_label and self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)
        self.empty_label = None

    def on_song_selected(self, song_id, song_title):
        if not song_id:
            notify.error(get_text('load_error'))
            return
        if self.recycle_view:
            self._saved_scroll_position = self.recycle_view.scroll_y
        self._save_state()
        screen_state.set_previous_screen('artist_songs')
        screen_state.set_artist_songs_data(self.artist_name, self._saved_scroll_position)
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('song_detail'):
                screen = self.manager.get_screen('song_detail')
                screen.set_previous_screen('artist_songs')
                screen.set_song(song_id)
                self.manager.current = 'song_detail'

    def go_back(self, instance=None):
        if self._going_back:
            return
        self._going_back = True
        Clock.schedule_once(lambda dt: setattr(self, '_going_back', False), 0.8)
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('songs'):
                songs_screen = self.manager.get_screen('songs')
                Clock.schedule_once(lambda dt: songs_screen.restore_state(), 0.1)
                self.manager.current = 'songs'
            else:
                self.manager.current = 'home'

    def _save_state(self):
        scroll = self.recycle_view.scroll_y if self.recycle_view else 1.0
        artist_songs_state.save({
            'artist_name': self.artist_name,
            'page': self._page,
            'total_songs': self._total_songs,
            'scroll_position': scroll,
        })

    def _restore_state(self):
        saved = artist_songs_state.get(allow_stale=True)
        if not saved:
            return False
        try:
            self._is_restoring = True
            self.artist_name = saved.get('artist_name', '')
            self._page = saved.get('page', 0)
            self._total_songs = saved.get('total_songs', 0)
            scroll = saved.get('scroll_position', 1.0)
            if not self.artist_name:
                self._is_restoring = False
                return False
            self._update_top_nav_title(self.artist_name)
            cache = self._songs_cache.get(self.artist_name)
            if cache is not None and self._is_page_cached(cache, self._page):
                self._total_songs = cache['total']
                self._ensure_valid_page()
                self._update_count_label(self._total_songs)
                self._display_page(self._build_page_slice(cache, self._page))

                def restore_scroll(dt):
                    if self.recycle_view:
                        self.recycle_view.scroll_y = scroll

                Clock.schedule_once(restore_scroll, 0.1)
                Clock.schedule_once(restore_scroll, 0.2)
            else:
                self._load_artist_songs(self.artist_name)
            self._is_restoring = False
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка восстановления ArtistSongs: {e}")
            self._is_restoring = False
            return False

    def on_enter(self):
        super().on_enter()

        if self._last_display_key is not None and self.artist_name:
            self._update_top_nav_title(self.artist_name)
            self._update_count_label(self._total_songs)
            return
        if self._restore_state():
            return
        if self._pending_artist:
            artist = self._pending_artist
            self._pending_artist = None
            self._load_artist_songs(artist)
            return
        if self.artist_name and not self._songs_cache.get(self.artist_name):
            self._load_artist_songs(self.artist_name)
            return
        cache = self._songs_cache.get(self.artist_name)
        if cache is not None:
            self._total_songs = cache['total']
            self._ensure_valid_page()
            self._update_count_label(self._total_songs)
            self._display_page(self._build_page_slice(cache, self._page))

    def on_pre_leave(self):
        self._save_state()
        return super().on_pre_leave()

    def on_leave(self):
        self._hide_loading_spinner()
        if self.manager and self.manager.current != 'song_detail':
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.clear_custom_title_widget()