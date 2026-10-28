# screens/favorites_screen.py
"""
Экран избранного — в стиле songs_screen / artist_songs_screen.
- PageCardsContainer с невидимыми заполнителями.
- Свайп вверх/вниз.
- Пагинация снизу.
- Динамический page_size.
- Лейбл "Избранное: X из Y".
- 3 попытки авто-загрузки, при провале — текст ошибки (без кнопки "Повторить").
- Логирование через perf('favorites.*').
"""
import time
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
from utils.settings_manager import settings_manager
from utils.localization import get_text
from state.favorites_state import favorites_state
from utils.perf import perf, perf_registry

logger = screen_logger('Favorites')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА — аналог SongsColors
# ============================================================

class FavoritesColors:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        return [0.10, 0.42, 0.25, 1]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 1]
        return [1, 1, 1, 1]

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
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 1]
        return [1, 1, 1, 1]

    @staticmethod
    def get_arrow_color(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 1]
        return [1, 1, 1, 1]


# ============================================================
# ГЛОБАЛЬНЫЕ ТЕКСТУРЫ
# ============================================================

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


# ============================================================
# LONG PRESS + СВАЙП
# ============================================================

class LongPressCardMixin:
    TAP_THRESHOLD = dp(15)
    LONG_PRESS_TIME = 0.5
    LONG_PRESS_MOVE_TOLERANCE = dp(10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._touch_down_pos = None
        self._long_press_event = None
        self._long_press_triggered = False

    def on_touch_down(self, touch):
        if getattr(self, 'disabled', False) or self.opacity < 0.1:
            return False
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self._touch_down_pos = touch.pos
        self._long_press_triggered = False
        self._long_press_event = Clock.schedule_once(
            self._trigger_long_press, self.LONG_PRESS_TIME
        )
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        if getattr(self, 'disabled', False) or self.opacity < 0.1:
            return False
        if self._touch_down_pos is None:
            return False
        dx = touch.x - self._touch_down_pos[0]
        dy = touch.y - self._touch_down_pos[1]
        if (abs(dx) > self.LONG_PRESS_MOVE_TOLERANCE
                or abs(dy) > self.LONG_PRESS_MOVE_TOLERANCE):
            self._cancel_long_press()
            touch.ungrab(self)
            return False
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        if getattr(self, 'disabled', False) or self.opacity < 0.1:
            return False
        if self._touch_down_pos is None:
            return False
        self._cancel_long_press()
        dx = touch.x - self._touch_down_pos[0]
        dy = touch.y - self._touch_down_pos[1]
        was_long = self._long_press_triggered
        self._touch_down_pos = None
        self._long_press_triggered = False
        if was_long:
            return True
        if abs(dx) < self.TAP_THRESHOLD and abs(dy) < self.TAP_THRESHOLD:
            self._handle_normal_click()
        return True

    def _trigger_long_press(self, dt):
        self._long_press_event = None
        if self._touch_down_pos is None:
            return
        self._long_press_triggered = True
        self._handle_long_press()

    def _cancel_long_press(self):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None

    def _flash_feedback(self):
        if not hasattr(self, 'md_bg_color'):
            return
        accent = FavoritesColors.get_accent(settings_manager.theme)
        bright = [min(1.0, c * 1.4 + 0.15) for c in accent[:3]] + [0.7]
        original = list(self.md_bg_color)
        anim = (
                Animation(md_bg_color=bright, duration=0.1, t='out_quad') +
                Animation(md_bg_color=original, duration=0.3, t='in_quad')
        )
        anim.start(self)

    def _handle_normal_click(self):
        pass

    def _handle_long_press(self):
        pass


# ============================================================
# КАРТОЧКА ИЗБРАННОЙ ПЕСНИ (крупнее обычной — 58dp)
# ============================================================

class FavoriteSongCard(LongPressCardMixin, MDCard):
    CARD_HEIGHT = dp(58)

    def __init__(self, song_id=0, artist='', title='', on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.song_id = song_id
        self.artist = artist
        self.title = title
        self.on_click_callback = on_click

        self.size_hint_y = None
        self.height = self.CARD_HEIGHT

        self.radius = [dp(12)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self.theme_line_color = "Custom"
        self.theme_bg_color = "Custom"
        self.padding = [0, 0, 0, 0]
        self.spacing = dp(8)

        content = MDBoxLayout(
            orientation='horizontal',
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(10),
            md_bg_color=[0, 0, 0, 0]
        )
        self.icon = Image(
            size_hint=(None, 1), width=dp(28),
            allow_stretch=True, keep_ratio=True
        )
        if _shared_song_texture:
            self.icon.texture = _shared_song_texture
        else:
            self.icon.text = "🎵"

        text_layout = MDBoxLayout(
            orientation='vertical', size_hint_x=1,
            spacing=dp(2), pos_hint={'center_y': 0.5}
        )
        self.artist_label = MDLabel(
            font_size=sp(15), size_hint_y=None, height=dp(22),
            theme_text_color="Custom", bold=True, valign="middle",
            shorten=True, shorten_from="right"
        )
        self.title_label = MDLabel(
            font_size=sp(12), size_hint_y=None, height=dp(18),
            theme_text_color="Custom", valign="middle",
            shorten=True, shorten_from="right"
        )
        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)

        self.arrow = MDLabel(
            text="›", font_size=sp(22), size_hint_x=None, width=dp(24),
            halign="center", valign="middle", theme_text_color="Custom"
        )

        content.add_widget(self.icon)
        content.add_widget(text_layout)
        content.add_widget(self.arrow)
        self.add_widget(content)

        self.artist_label.text = artist
        self.title_label.text = title

        self.update_theme_colors()

    def _handle_normal_click(self):
        if self.on_click_callback:
            self.on_click_callback(self.song_id, self.title, self.artist)

    def _handle_long_press(self):
        self._flash_feedback()
        if self.on_click_callback:
            Clock.schedule_once(
                lambda dt: self.on_click_callback(self.song_id, self.title, self.artist),
                0.15
            )

    def update_data(self, song_id, artist, title, on_click):
        self.song_id = song_id
        self.artist = artist
        self.title = title
        self.on_click_callback = on_click
        self.artist_label.text = artist
        self.title_label.text = title

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = FavoritesColors.get_accent(theme_id)
        self.md_bg_color = FavoritesColors.get_card_bg(theme_id)
        self.line_color = FavoritesColors.get_card_line(theme_id)
        self.line_width = FavoritesColors.get_card_line_width(theme_id)
        self.artist_label.text_color = FavoritesColors.get_text_primary(theme_id)
        self.title_label.text_color = FavoritesColors.get_text_secondary(theme_id)
        self.arrow.text_color = accent


# ============================================================
# КОНТЕЙНЕР КАРТОЧЕК
# ============================================================

class PageCardsContainer(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(6)
        self.md_bg_color = [0, 0, 0, 0]
        self.cards = []
        self.padding = [0, 0, 0, 0]
        self._card_pool = []
        self.size_hint = (None, None)
        self.height = 0
        self.width = 0
        self.max_cards = 6

    def _ensure_pool(self, count):
        if len(self._card_pool) > count:
            while len(self._card_pool) > count:
                card = self._card_pool.pop()
                if card.parent:
                    self.remove_widget(card)
        while len(self._card_pool) < count:
            card = FavoriteSongCard()
            self.add_widget(card)
            self._card_pool.append(card)

    def sync_max_cards(self, max_cards):
        if self.max_cards == max_cards and len(self._card_pool) == max_cards:
            return
        self.max_cards = max_cards
        self._ensure_pool(max_cards)
        self.height = (
                self.max_cards * FavoriteSongCard.CARD_HEIGHT
                + (self.max_cards - 1) * self.spacing
        ) if self.max_cards > 0 else 0

    def _apply_pool(self, items, on_click):
        self.sync_max_cards(self.max_cards)

        for i in range(self.max_cards):
            card = self._card_pool[i]
            if i < len(items):
                s = items[i]
                card.update_data(
                    song_id=s.get('song_id', 0),
                    artist=s.get('artist', ''),
                    title=s.get('title', ''),
                    on_click=on_click,
                )
                card.height = FavoriteSongCard.CARD_HEIGHT
                card.opacity = 1
                card.disabled = False
            else:
                card.height = FavoriteSongCard.CARD_HEIGHT
                card.opacity = 0
                card.disabled = True
            card.update_theme_colors()

        self.cards = self._card_pool[:len(items)]

        self.height = (
                self.max_cards * FavoriteSongCard.CARD_HEIGHT
                + (self.max_cards - 1) * self.spacing
        ) if self.max_cards > 0 else 0

        if self.parent and hasattr(self.parent, '_update_cards_layout'):
            Clock.schedule_once(
                lambda dt: self.parent._update_cards_layout(len(items)), 0
            )

    def set_songs(self, songs, on_click):
        with perf('favorites.cards.set_songs', log_every=False):
            self._apply_pool(songs, on_click)

    def clear(self):
        for card in self._card_pool:
            card.opacity = 0
            card.disabled = True
        self.cards = []
        self.height = (
                self.max_cards * FavoriteSongCard.CARD_HEIGHT
                + (self.max_cards - 1) * self.spacing
        ) if self.max_cards > 0 else 0
        if self.parent and hasattr(self.parent, '_update_cards_layout'):
            Clock.schedule_once(
                lambda dt: self.parent._update_cards_layout(0), 0
            )

    def update_theme_colors(self):
        for c in self._card_pool:
            c.update_theme_colors()


# ============================================================
# СВАЙП-ОБЁРТКА
# ============================================================

class SwipeableCardsWrapper(FloatLayout):
    SWIPE_THRESHOLD = dp(40)
    SWIPE_TIME_LIMIT = 0.5

    def __init__(self, on_swipe_up=None, on_swipe_down=None, **kwargs):
        super().__init__(**kwargs)
        self.on_swipe_up = on_swipe_up
        self.on_swipe_down = on_swipe_down
        self._touch_start = None
        self._touch_start_time = None
        self._swipe_handled = False

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        self._touch_start = touch.pos
        self._touch_start_time = time.perf_counter()
        self._swipe_handled = False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._touch_start is not None and not self._swipe_handled:
            dx = touch.x - self._touch_start[0]
            dy = touch.y - self._touch_start[1]
            if abs(dy) > self.SWIPE_THRESHOLD and abs(dy) > abs(dx) * 1.2:
                self._swipe_handled = True
                if dy > 0:
                    if self.on_swipe_down:
                        self.on_swipe_down()
                else:
                    if self.on_swipe_up:
                        self.on_swipe_up()
                self._touch_start = None
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._touch_start is None:
            return super().on_touch_up(touch)
        self._touch_start = None
        self._swipe_handled = False
        return super().on_touch_up(touch)


# ============================================================
# ПАГИНАЦИЯ
# ============================================================

class PaginationArrow(MDBoxLayout):
    DEFAULT_WIDTH = dp(40)

    def __init__(self, icon_name, on_press=None, icon_color=None, width=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = width if width else self.DEFAULT_WIDTH
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]
        self._on_press = on_press
        self._enabled = True
        self._pressed = False

        container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 1))
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
            icon_name="chevron-double-left", on_press=self._go_back_10, width=dp(36)
        )
        self.add_widget(self.jump_back_arrow)

        self.prev_arrow = PaginationArrow(
            icon_name="chevron-left", on_press=self._go_prev_page, width=dp(36)
        )
        self.add_widget(self.prev_arrow)

        self.page_label = MDLabel(
            text="1", font_size=sp(16), halign="center", valign="middle",
            theme_text_color="Custom", text_color=[1, 1, 1, 1], bold=True,
            size_hint=(None, 1), width=dp(40),
        )
        self.add_widget(self.page_label)

        self.next_arrow = PaginationArrow(
            icon_name="chevron-right", on_press=self._go_next_page, width=dp(36)
        )
        self.add_widget(self.next_arrow)

        self.jump_forward_arrow = PaginationArrow(
            icon_name="chevron-double-right", on_press=self._go_forward_10, width=dp(36)
        )
        self.add_widget(self.jump_forward_arrow)

        self._update_width()
        self.update_theme_colors()

    def on_touch_down(self, touch):
        if self.parent is not None and self.parent.height < dp(10):
            return False
        return super().on_touch_down(touch)

    def _update_width(self):
        self.width = (
                dp(4) + dp(4)
                + self.jump_back_arrow.width + self.spacing
                + self.prev_arrow.width + self.spacing
                + self.page_label.width + self.spacing
                + self.next_arrow.width + self.spacing
                + self.jump_forward_arrow.width
        )

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
        arrow_color = FavoritesColors.get_arrow_color(theme_id)
        self.jump_back_arrow.set_color(arrow_color)
        self.jump_forward_arrow.set_color(arrow_color)
        self.prev_arrow.set_color(arrow_color)
        self.next_arrow.set_color(arrow_color)
        self.page_label.text_color = FavoritesColors.get_text_primary(theme_id)


# ============================================================
# ОСНОВНОЙ ЭКРАН
# ============================================================

class FavoritesScreen(BaseScreen):
    MIN_PAGE_SIZE = 3
    MAX_PAGE_SIZE = 15
    PAGINATION_HEIGHT = dp(48) + dp(1) + dp(2)
    MAX_RETRIES = 3  # Максимальное количество попыток авто-загрузки

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'

        self._all_favorites = []
        self._page = 0
        self._page_size = 6
        self._page_size_locked = False
        self._total = 0

        self._load_token = 0
        self._last_display_key = None
        self._retry_count = 0  # Счетчик текущих попыток

        self.cards_container = None
        self._cards_wrapper = None
        self._cards_top_offset = dp(6)
        self._cards_left_pad = dp(0)
        self._cards_right_pad = dp(0)

        self._main_layout = None
        self.count_label = None
        self.empty_label = None
        self.bg_color_inst = None
        self.bg_rect = None
        self.texture = None
        self._pagination_bar = None
        self._pagination_container = None
        self._pagination_anchor = None
        self._loading_spinner = None
        self._loading_spinner_widget = None
        self._spinner_pending = False
        self._auth_card = None
        self._listener_registered = False

        self._initialized = False
        self._going_back = False
        self._last_window_size = None

        init_shared_song_icon()
        self.load_background()
        self.init_ui()

        Clock.schedule_once(lambda dt: self._register_listener(), 0.1)
        Clock.schedule_once(lambda dt: self._restore_state(), 0.15)
        Clock.schedule_once(lambda dt: self._recalc_page_size(force=True), 0.3)

        logger.info('Экран избранного создан (PageCardsContainer)')

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
        if self.count_label:
            self.count_label.text_color = FavoritesColors.get_hint_color(theme_id)
        if self.empty_label:
            self.empty_label.text_color = FavoritesColors.get_hint_color(theme_id)
        if self._pagination_bar:
            self._pagination_bar.update_theme_colors()
        if self._auth_card:
            self._auth_card.update_theme_colors()
        if self.cards_container:
            self.cards_container.update_theme_colors()

    def update_language(self):
        if self.count_label and self.count_label.opacity > 0:
            self._update_count_label(self._total)
        if self._auth_card:
            self._auth_card.update_language()

    # ============================================================
    # UI
    # ============================================================

    def init_ui(self):
        with perf('favorites.init_ui', log_every=False):
            main_layout = MDBoxLayout(orientation='vertical', spacing=0)
            self._main_layout = main_layout

            top_padding = layout_config.get_top_padding()
            main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

            padding = layout_config.get_content_padding()

            # === Лейбл "Избранное: X из Y" ===
            self.count_label = MDLabel(
                text="", font_size=sp(12), halign="center", valign="middle",
                size_hint_y=None, height=dp(24),
                theme_text_color="Custom",
                text_color=FavoritesColors.get_hint_color(settings_manager.theme),
                opacity=0, bold=True
            )
            self.count_label.text_size = (Window.width, dp(24))
            self.count_label.bind(
                width=lambda inst, val: setattr(inst, 'text_size', (val, dp(24)))
            )
            main_layout.add_widget(self.count_label)

            # === Карточки ===
            self._cards_wrapper = SwipeableCardsWrapper(
                on_swipe_up=self._on_swipe_up,
                on_swipe_down=self._on_swipe_down,
                size_hint=(1, 1),
            )
            self._cards_wrapper.clip = True

            self._cards_top_offset = dp(6)
            self._cards_left_pad = padding[0]
            self._cards_right_pad = padding[2]

            self.cards_container = PageCardsContainer()
            self.cards_container.sync_max_cards(self._page_size)
            self._cards_wrapper.add_widget(self.cards_container)

            self._cards_wrapper.bind(
                size=lambda *a: self._update_cards_layout(len(self.cards_container.cards)),
                pos=lambda *a: self._update_cards_layout(len(self.cards_container.cards)),
            )

            main_layout.add_widget(self._cards_wrapper)

            # === Пагинация ===
            self._pagination_container = MDBoxLayout(
                orientation='vertical',
                size_hint=(1, None),
                height=0,
                md_bg_color=[0, 0, 0, 0],
                padding=[padding[0], dp(0), padding[2], dp(0)],
            )
            self._pagination_container.clip = True

            self._pagination_anchor = FloatLayout(size_hint=(1, 1))

            self._pagination_bar = PaginationBar(
                on_page_select=self._on_page_selected_from_bar,
            )
            self._pagination_bar.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            self._pagination_anchor.add_widget(self._pagination_bar)
            self._pagination_container.add_widget(self._pagination_anchor)
            main_layout.add_widget(self._pagination_container)

            # === Отступ снизу ===
            bottom_padding = layout_config.get_pagination_bottom_padding()
            main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))

            self.add_widget(main_layout)
            self._initialized = True
            self.update_theme_colors()

    def _update_cards_layout(self, count):
        if not self.cards_container or not self._cards_wrapper:
            return
        if self._cards_wrapper.height <= 1:
            return

        if self.cards_container.max_cards != self._page_size:
            self.cards_container.sync_max_cards(self._page_size)

        h_card = FavoriteSongCard.CARD_HEIGHT

        self.cards_container.x = self._cards_wrapper.x + self._cards_left_pad
        self.cards_container.width = max(
            dp(50),
            self._cards_wrapper.width - self._cards_left_pad - self._cards_right_pad
        )

        n_total = self.cards_container.max_cards
        self.cards_container.spacing = dp(6)
        expected_h = n_total * h_card + (n_total - 1) * self.cards_container.spacing
        if abs(self.cards_container.height - expected_h) > 1:
            self.cards_container.height = expected_h

        try:
            label_bottom = self.count_label.to_window(
                self.count_label.x, self.count_label.y, initial=False
            )[1]
            wrapper_top = self._cards_wrapper.to_window(
                self._cards_wrapper.x, self._cards_wrapper.y, initial=False
            )[1] + self._cards_wrapper.height
            desired_top = label_bottom - self._cards_top_offset
            max_top = wrapper_top - self._cards_top_offset
            self.cards_container.top = min(desired_top, max_top)

            cards_top = self.cards_container.to_window(
                self.cards_container.x, self.cards_container.y, initial=False
            )[1] + self.cards_container.height
            gap = label_bottom - cards_top
            logger.info(
                f"🔍 LAYOUT(favorites): n_real={count}, n_total={n_total}, "
                f"gap={gap:.1f}, spacing={self.cards_container.spacing:.1f}, "
                f"cards_h={self.cards_container.height:.1f}"
            )
        except Exception as e:
            self.cards_container.top = self._cards_wrapper.top - self._cards_top_offset
            logger.debug(f"🔍 LAYOUT(favorites) error: {e}")

    # ============================================================
    # РАЗМЕР СТРАНИЦЫ
    # ============================================================

    def _calc_page_size(self):
        bottom_pad = layout_config.get_pagination_bottom_padding()

        fixed_h = (
                layout_config.get_top_padding()
                + dp(24)
                + self._cards_top_offset
                + self.PAGINATION_HEIGHT
                + bottom_pad
        )
        available_h = Window.height - fixed_h
        if available_h <= 0:
            return self.MIN_PAGE_SIZE

        card_h = FavoriteSongCard.CARD_HEIGHT + dp(6)
        n = int(available_h / card_h)

        return max(self.MIN_PAGE_SIZE, min(self.MAX_PAGE_SIZE, n))

    def _recalc_page_size(self, force=False):
        with perf('favorites._recalc_page_size', log_every=False):
            if self._page_size_locked and not force:
                return
            new_size = self._calc_page_size()
            if new_size == self._page_size:
                if not self._page_size_locked:
                    self._page_size_locked = True
                return
            self._page_size = new_size
            self._page_size_locked = True

            if self.cards_container:
                self.cards_container.sync_max_cards(new_size)

            if self._all_favorites:
                self._ensure_valid_page()
                self._display_page()

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
            if self.cards_container:
                self.cards_container.sync_max_cards(new_size)
            if self._all_favorites:
                self._ensure_valid_page()
                self._display_page()

    def _ensure_valid_page(self):
        if self._total <= 0:
            self._page = 0
            return
        max_page = (self._total - 1) // self._page_size
        if self._page > max_page:
            self._page = max_page

    # ============================================================
    # ЛЕЙБЛ
    # ============================================================

    def _update_count_label(self, total):
        if not self.count_label:
            return
        if total == 0:
            self.count_label.text = get_text('no_favorites')
            self.count_label.opacity = 1
            return
        page_size = self._page_size
        if total > page_size:
            current_count = min((self._page + 1) * page_size, total)
            self.count_label.text = (
                f"{get_text('favorites')}: {current_count} "
                f"{get_text('of')} {total}"
            )
        elif total == 1:
            self.count_label.text = f"{get_text('favorites')}: 1 {get_text('of')} 1"
        else:
            self.count_label.text = f"{get_text('favorites')}: {total} {get_text('of')} {total}"
        self.count_label.opacity = 1

    def _update_top_nav(self):
        if not self.manager or self.manager.current != 'favorites':
            return
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.force_update_title(get_text('favorites'), show_back=False)

    # ============================================================
    # ПАГИНАЦИЯ
    # ============================================================

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
        self._pagination_bar.set_total(self._total, self._page_size, self._page)

    def _on_page_selected_from_bar(self, page_index):
        if page_index == self._page:
            return
        with perf('favorites.action.page_switch'):
            self._page = page_index
            self._display_page()

    # ============================================================
    # СВАЙПЫ
    # ============================================================

    def _on_swipe_up(self):
        with perf('favorites.action.swipe_up', log_every=False):
            if self._total <= 0:
                return
            max_page = (self._total - 1) // self._page_size
            if self._page < max_page:
                self._page += 1
                self._display_page()

    def _on_swipe_down(self):
        with perf('favorites.action.swipe_down', log_every=False):
            if self._total <= 0:
                return
            if self._page > 0:
                self._page -= 1
                self._display_page()

    # ============================================================
    # ДАННЫЕ
    # ============================================================

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

    def _render_favorites(self, favorites):
        with perf('favorites._render_favorites', log_every=False):
            self._hide_loading()
            self._retry_count = 0  # Сбрасываем счетчик при успехе

            if not api.is_authenticated():
                self._show_auth_message()
                return

            formatted = self._format_favorites(favorites)
            self._all_favorites = formatted
            self._total = len(formatted)
            self._update_top_nav()
            self._ensure_valid_page()
            self._update_count_label(self._total)

            if not self._all_favorites:
                self._show_empty()
                return

            self._display_page()

    def _display_page(self):
        with perf('favorites._display_page', log_every=False):
            if not self._all_favorites:
                return
            start = self._page * self._page_size
            end = min(start + self._page_size, self._total)
            page_slice = self._all_favorites[start:end]

            first_id = page_slice[0].get('song_id', 0) if page_slice else 0
            display_key = (self._page, len(page_slice), first_id)
            if self._last_display_key != display_key:
                if self.cards_container:
                    self.cards_container.sync_max_cards(self._page_size)
                    self.cards_container.set_songs(page_slice, self.on_song_selected)
                self._last_display_key = display_key

            self._show_pagination_bar()
            self._update_count_label(self._total)

            Clock.schedule_once(
                lambda dt: self._update_cards_layout(len(page_slice)), 0
            )
            Clock.schedule_once(
                lambda dt: self._update_cards_layout(len(page_slice)), 0.15
            )

    # ============================================================
    # EMPTY / AUTH / ERROR
    # ============================================================

    def _clear_extra_widgets(self):
        if self._auth_card and self._auth_card.parent:
            self._auth_card.parent.remove_widget(self._auth_card)
        self._auth_card = None
        if self.empty_label and self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)
        self.empty_label = None

    def _show_empty(self):
        self._clear_extra_widgets()
        if self.cards_container:
            self.cards_container.clear()
        self._hide_pagination()

        theme_id = settings_manager.theme
        self.empty_label = MDLabel(
            text=get_text('no_favorites'),
            halign="center", font_size=sp(14),
            theme_text_color="Custom",
            text_color=FavoritesColors.get_hint_color(theme_id),
            size_hint_y=None, height=dp(60)
        )
        if self._cards_wrapper:
            self._cards_wrapper.add_widget(self.empty_label)

    def _show_auth_message(self):
        self._clear_extra_widgets()
        if self.cards_container:
            self.cards_container.clear()
        self._hide_pagination()
        self._update_top_nav()
        self._update_count_label(0)

        self._auth_card = AuthMessageCard()
        if self._cards_wrapper:
            self._cards_wrapper.add_widget(self._auth_card)

    def _show_error(self):
        """Показывает текст ошибки, если все попытки загрузки провалились."""
        self._clear_extra_widgets()
        if self.cards_container:
            self.cards_container.clear()
        self._hide_pagination()

        theme_id = settings_manager.theme
        # Сообщение об ошибке согласно требованию
        error_text = "Проверьте соединение интернета.\nДанные не загружены."

        self.empty_label = MDLabel(
            text=error_text,
            halign="center", font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.9],
            size_hint_y=None, height=dp(80)
        )
        if self._cards_wrapper:
            self._cards_wrapper.add_widget(self.empty_label)

    # ============================================================
    # СПИННЕР
    # ============================================================

    def _show_loading(self):
        if self._loading_spinner or self._spinner_pending:
            return
        self._spinner_pending = True

        def _actually_show(dt):
            if not self._spinner_pending:
                return
            self._spinner_pending = False
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

        Clock.schedule_once(_actually_show, 0.25)

    def _hide_loading(self):
        if self._spinner_pending:
            self._spinner_pending = False
        if not self._loading_spinner:
            return
        if self._loading_spinner_widget:
            self._loading_spinner_widget.stop_animation()
            self._loading_spinner_widget = None
        if self._loading_spinner.parent:
            self._loading_spinner.parent.remove_widget(self._loading_spinner)
        self._loading_spinner = None

    # ============================================================
    # ЗАГРУЗКА (с 3 попытками)
    # ============================================================

    def load_favorites(self, force_refresh=False):
        with perf('favorites.load_favorites', log_every=False):
            if not api.is_authenticated():
                self._show_auth_message()
                return

            # Если это не принудительное обновление, сбрасываем счетчик
            if not force_refresh:
                self._retry_count = 0

            cached = api._load_favorites_cache(allow_stale=True)

            if cached is not None and not force_refresh:
                self._render_favorites(cached)
                if not api._favorites_stale:
                    return
                api.get_favorites(
                    on_success=self._on_background_update,
                    on_failure=lambda req, err: logger.warning(f"Фон: {err}"),
                    force_refresh=False)
                return

            if cached is None:
                self._show_loading()

            self._attempt_fetch()

    def _attempt_fetch(self):
        """Запускает попытку загрузки с сервера."""
        api.get_favorites(
            on_success=self._on_network_loaded,
            on_failure=self._on_load_failed,
            force_refresh=True)

    def _on_network_loaded(self, favorites):
        self._hide_loading()
        self._retry_count = 0  # Сброс счетчика при успехе
        self._render_favorites(favorites)

    def _on_background_update(self, favorites):
        self._render_favorites(favorites)

    def _on_load_failed(self, req, error):
        self._retry_count += 1
        error_str = str(error)

        if "401" in error_str or "Unauthorized" in error_str:
            self._hide_loading()
            self._show_auth_message()
            return

        # Если попытки еще есть, пробуем снова
        if self._retry_count < self.MAX_RETRIES:
            logger.info(f"Попытка загрузки {self._retry_count}/{self.MAX_RETRIES} не удалась. Повтор...")
            # Увеличиваем задержку перед следующей попыткой (1с, 2с...)
            delay = self._retry_count * 1.0
            Clock.schedule_once(lambda dt: self._attempt_fetch(), delay)
        else:
            # Все попытки исчерпаны
            logger.error(f"Все {self.MAX_RETRIES} попытки загрузки провалились.")
            self._hide_loading()
            self._show_error()

    def _on_favorites_changed(self, favorites):
        self._render_favorites(favorites)

    # ============================================================
    # СОСТОЯНИЕ
    # ============================================================

    def _save_state(self):
        favorites_state.save({
            'page': self._page,
            'total': self._total,
            'scroll_position': 1.0,
        })

    def _restore_state(self):
        with perf('favorites._restore_state', log_every=False):
            saved = favorites_state.get(allow_stale=True)
            if not saved:
                return False
            try:
                self._page = saved.get('page', 0)
                self._total = saved.get('total', 0)
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка восстановления Favorites: {e}")
                return False

    def _register_listener(self):
        if not self._listener_registered:
            api.add_favorites_listener(self._on_favorites_changed)
            self._listener_registered = True

    # ============================================================
    # ДЕЙСТВИЯ
    # ============================================================

    def on_song_selected(self, song_id, song_title, artist=""):
        with perf('favorites.action.on_song_selected', log_every=False):
            if not song_id:
                notify.error(get_text('load_error'))
                return
            self._save_state()
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

    # ============================================================
    # LIFECYCLE
    # ============================================================

    def on_pre_enter(self):
        self._update_top_nav()

    def on_enter(self):
        with perf('favorites.on_enter.total'):
            super().on_enter()
            self._register_listener()
            self.load_favorites(force_refresh=False)

    def on_pre_leave(self):
        with perf('favorites.on_pre_leave', log_every=False):
            self._save_state()
        return super().on_pre_leave()

    def on_leave(self):
        perf_registry.dump(prefix='[favorites]')

    @staticmethod
    def pre_update_top_nav():
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.force_update_title(get_text('favorites'), show_back=False)


# ============================================================
# AUTH CARD (вспомогательная)
# ============================================================

class AuthMessageCard(MDCard):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(160)
        self.padding = [dp(20)] * 4
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

    def update_language(self):
        self.title_label.text = get_text('auth_required_title')
        self.message_label.text = get_text('auth_required_message')