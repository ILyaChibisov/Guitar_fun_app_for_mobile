# screens/artist_songs_screen.py
"""
Экран списка песен исполнителя - с именем в TopNav,
количеством песен («50 из 70 песен») и пагинацией (батч 200, страница 50).
Пагинация: ≤ 6 кнопок → по центру (AnchorLayout), ≥ 7 → скролл.
Адаптирован под 3 темы и 6 языков.
"""
from kivymd.app import MDApp
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from screens.components.loading_spinner import LoadingSpinner
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
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


# ============================================================
# ЦВЕТА ДЛЯ ЭКРАНА
# ============================================================

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
        else:
            return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        else:
            return [1, 1, 1, 0.4]

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
            logger.error(f"Ошибка загрузки иконки песни: {e}")
    return None


# ============ КАРТОЧКА ПЕСНИ ============

class RecycleSongCard(RecycleDataViewBehavior, MDCard):
    title = StringProperty('')
    tabs_count = NumericProperty(0)
    song_id = NumericProperty(0)
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.padding = [dp(10), dp(4), dp(10), dp(4)]
        self.spacing = dp(8)
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self._build_ui()
        self.update_theme_colors()

    def _build_ui(self):
        self.icon = Image(size_hint=(None, 1), width=dp(28),
                          allow_stretch=True, keep_ratio=True)
        if _shared_song_texture:
            self.icon.texture = _shared_song_texture
        else:
            self.icon.text = "🎵"

        self.title_label = MDLabel(
            font_size=sp(15), theme_text_color="Custom", bold=True,
            shorten=True, shorten_from="right", valign="middle", size_hint_x=1)

        self.count_label = MDLabel(
            text="", font_size=sp(11), size_hint_x=None, width=dp(40),
            halign="right", valign="middle", theme_text_color="Custom")

        self.arrow = MDLabel(
            text="›", font_size=sp(22), size_hint_x=None, width=dp(24),
            halign="center", valign="middle", theme_text_color="Custom")

        self.add_widget(self.icon)
        self.add_widget(self.title_label)
        self.add_widget(self.count_label)
        self.add_widget(self.arrow)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = ArtistColors.get_accent(theme_id)
        self.md_bg_color = ArtistColors.get_card_bg(theme_id)
        self.line_color = ArtistColors.get_card_line(theme_id)
        self.line_width = 1.0 if theme_id in ('dark', 'light') else 0.5
        self.title_label.text_color = ArtistColors.get_text_primary(theme_id)
        self.count_label.text_color = ArtistColors.get_text_secondary(theme_id)
        self.arrow.text_color = accent

    def refresh_view_attrs(self, rv, index, data):
        self.title = data.get('title', '')
        self.tabs_count = data.get('tabs_count', 0)
        self.song_id = data.get('song_id', 0)
        self.on_click = data.get('on_click')
        self.title_label.text = self.title
        self.count_label.text = str(self.tabs_count) if self.tabs_count > 0 else ""
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


# ============ RECYCLEVIEW ============

class SongRecycleView(RecycleView):
    def __init__(self, on_song_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_song_click = on_song_click
        self.animate_scroll = False
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]
        self.clip = True

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)), default_size_hint=(1, None),
            size_hint_y=None, height=dp(48) * 50,
            orientation='vertical', spacing=dp(2))
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

class PageButton(ButtonBehavior, MDBoxLayout):
    """Кнопка страницы — цифра, без ripple. bold всегда True — ширина стабильна."""

    def __init__(self, text, index, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = dp(48)
        self.padding = [dp(2)] * 4
        self.spacing = 0
        self.md_bg_color = [0, 0, 0, 0]
        self.is_selected = False
        self.is_hover = False
        self.page_index = index
        self.on_click_callback = on_click

        self.label = MDLabel(
            text=text,
            font_size=sp(14),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            bold=True,
            size_hint=(None, 1),
            width=dp(44),
            pos_hint={'center_x': 0.5},
        )
        self.add_widget(self.label)

        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)
        self.bind(on_release=self._on_release)

    def _on_release(self, *args):
        if self.on_click_callback:
            self.on_click_callback(self.page_index)

    def _on_enter(self, *args):
        self.is_hover = True
        self.update_style()

    def _on_leave(self, *args):
        self.is_hover = False
        self.update_style()

    def set_selected(self, selected):
        self.is_selected = selected
        self.update_style()

    def update_style(self):
        theme_id = settings_manager.theme
        accent = ArtistColors.get_accent(theme_id)
        text_s = ArtistColors.get_text_secondary(theme_id)

        if self.is_selected:
            self.md_bg_color = accent
            self.label.text_color = [1, 1, 1, 1]
            self.radius = [dp(8)]
        elif self.is_hover:
            if theme_id == 'light':
                self.md_bg_color = [0, 0, 0, 0.05]
            else:
                self.md_bg_color = [1, 1, 1, 0.08]
            self.label.text_color = accent
            self.radius = [dp(8)]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = text_s
            self.radius = [0]


class PaginationBar(MDBoxLayout):
    """
    Лента страниц 50, 100, 150, ...
    ≤ 6 кнопок  → центрируется (AnchorLayout, без ScrollView).
    ≥ 7 кнопок  → ScrollView со скроллом от левого края.
    set_total() пересоздаёт кнопки только при изменении (total, per_page).
    set_current_page() только переключает выделение.
    """

    CENTERED_MAX_BUTTONS = 6

    def __init__(self, on_page_select=None, **kwargs):
        super().__init__(**kwargs)
        self.on_page_select = on_page_select
        self.current_page_index = 0
        self.total_pages = 1
        self._last_total = None
        self._last_per_page = None

        # ВАЖНО: page_buttons создаём ДО height — иначе on_size упадёт
        self.page_buttons = []

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.spacing = dp(2)
        self.md_bg_color = [0, 0, 0, 0]
        self.padding = [dp(4), dp(2), dp(4), dp(2)]

        self.left_arrow = MDIconButton(
            icon="chevron-left", size_hint=(None, 1), width=dp(32),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll_strip(-1)
        )
        self.right_arrow = MDIconButton(
            icon="chevron-right", size_hint=(None, 1), width=dp(32),
            theme_icon_color="Custom", md_bg_color=[0, 0, 0, 0],
            on_release=lambda x: self.scroll_strip(1)
        )

        self.add_widget(self.left_arrow)

        # Центральная зона — либо AnchorLayout с контейнером, либо ScrollView
        self.center_zone = MDBoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )
        self.add_widget(self.center_zone)

        self.add_widget(self.right_arrow)

        # Контейнер с кнопками — общий для обоих режимов
        self.container = MDBoxLayout(
            orientation='horizontal', size_hint=(None, 1),
            spacing=dp(4), padding=[dp(4)] * 4,
            md_bg_color=[0, 0, 0, 0]
        )

        self.scroll_view = None
        self._centered_mode = None

        self.update_theme_colors()

    # ---------- Внутреннее ----------

    def _rebuild_center_zone(self, force_center):
        """Пересобирает center_zone под нужный режим (центр / скролл)."""
        if self._centered_mode == force_center and self.center_zone.children:
            return

        self._centered_mode = force_center

        if self.container.parent:
            self.container.parent.remove_widget(self.container)

        self.center_zone.clear_widgets()
        self.scroll_view = None

        if force_center:
            # Центрированный режим: AnchorLayout — единственный надёжный способ
            anchor = AnchorLayout(
                anchor_x='center',
                anchor_y='center',
                size_hint=(1, 1)
            )
            self.container.size_hint = (None, 1)
            self.container.pos_hint = {}
            anchor.add_widget(self.container)
            self.center_zone.add_widget(anchor)
        else:
            # Режим скролла
            self.container.size_hint = (None, 1)
            self.container.pos_hint = {}
            self.scroll_view = ScrollView(
                size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False,
                bar_width=0, bar_color=[0, 0, 0, 0],
                bar_inactive_color=[0, 0, 0, 0], bar_margin=0
            )
            self.scroll_view.add_widget(self.container)
            self.center_zone.add_widget(self.scroll_view)

    def _apply_layout_mode(self):
        n = len(self.page_buttons)
        if n == 0:
            return
        force_center = (n <= self.CENTERED_MAX_BUTTONS)
        self._rebuild_center_zone(force_center)

    # ---------- Публичный API ----------

    def set_total(self, total_items, per_page, current_page=0):
        if self._last_total == total_items and self._last_per_page == per_page:
            self.set_current_page(current_page)
            return

        self._last_total = total_items
        self._last_per_page = per_page

        self.container.clear_widgets()
        self.page_buttons = []
        self.total_pages = max(1, (total_items + per_page - 1) // per_page)
        self.current_page_index = current_page

        if self.total_pages <= 1:
            self._rebuild_center_zone(True)
            self.container.width = 0
            self.update_theme_colors()
            return

        for i in range(self.total_pages):
            count = (i + 1) * per_page
            if count > total_items:
                count = total_items
            btn = PageButton(
                text=str(count),
                index=i,
                on_click=self._on_page_click
            )
            self.page_buttons.append(btn)
            self.container.add_widget(btn)

        content_w = (
            sum(b.width for b in self.page_buttons)
            + max(0, len(self.page_buttons) - 1) * self.container.spacing
            + self.container.padding[0] + self.container.padding[2]
        )
        self.container.width = content_w

        # Режим — по количеству кнопок
        self._apply_layout_mode()

        self.update_theme_colors()
        Clock.schedule_once(lambda dt: self._scroll_to_current(force=True), 0.1)

    def set_current_page(self, page):
        if not self.page_buttons:
            self.current_page_index = page
            return

        if page == self.current_page_index:
            for i, btn in enumerate(self.page_buttons):
                btn.set_selected(i == page)
            return

        self.current_page_index = page
        for i, btn in enumerate(self.page_buttons):
            btn.set_selected(i == page)

        if self._centered_mode is False and self.scroll_view:
            Clock.schedule_once(lambda dt: self._scroll_to_current(force=False), 0.05)

    def _on_page_click(self, index):
        if index == self.current_page_index:
            return
        self.current_page_index = index
        for i, btn in enumerate(self.page_buttons):
            btn.set_selected(i == index)
        if self.on_page_select:
            self.on_page_select(index)

    def scroll_strip(self, direction):
        if not self.scroll_view:
            return
        scroll_amount = 0.2
        new_scroll = self.scroll_view.scroll_x + (direction * scroll_amount)
        new_scroll = max(0, min(1, new_scroll))
        anim = Animation(scroll_x=new_scroll, duration=0.2, t='out_quad')
        anim.start(self.scroll_view)

    def _scroll_to_current(self, force=False):
        if self._centered_mode is not False:
            return
        if not self.scroll_view or not self.page_buttons:
            return
        idx = self.current_page_index
        if idx >= len(self.page_buttons):
            idx = len(self.page_buttons) - 1
        btn = self.page_buttons[idx]
        if btn.width <= 0:
            return
        total_width = self.container.width - self.scroll_view.width
        if total_width <= 0:
            return

        if not force:
            viewport_w = self.scroll_view.width
            content_w = self.container.width
            if content_w > 0 and viewport_w > 0:
                current_left = self.scroll_view.scroll_x * max(0, content_w - viewport_w)
                current_right = current_left + viewport_w
                btn_left = btn.x
                btn_right = btn.x + btn.width
                if current_left <= btn_left and btn_right <= current_right:
                    return

        x_target = btn.x - dp(4)
        scroll_x = x_target / total_width
        scroll_x = max(0, min(1, scroll_x))
        Animation(scroll_x=scroll_x, duration=0.2, t='out_quad').start(self.scroll_view)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = ArtistColors.get_accent(theme_id)

        self.left_arrow.icon_color = accent
        self.right_arrow.icon_color = accent

        for i, btn in enumerate(self.page_buttons):
            btn.set_selected(i == self.current_page_index)

    def on_size(self, *args):
        # Защита: on_size может вызываться до завершения __init__
        if not getattr(self, 'page_buttons', None):
            return
        if not getattr(self, 'container', None) or not getattr(self, 'center_zone', None):
            return
        Clock.schedule_once(lambda dt: self._apply_layout_mode(), 0.05)


# ============ ОСНОВНОЙ ЭКРАН ============

class ArtistSongsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'artist_songs'
        self.artist_name = ''
        self._pending_artist = None

        # Пагинация
        self._page = 0
        self._limit = 50
        self._batch_size = 200
        self._total_songs = 0

        # Кеш: {artist: {'items': {abs_index: song}, 'total': N, 'batches': set()}}
        self._songs_cache = {}

        # Защита от гонок
        self._batch_loading = False
        self._pending_page = None
        self._is_loading = False

        self._saved_scroll_position = 1.0
        self._is_restoring = False
        self._temp_scroll_position = None

        self.recycle_view = None
        self._hint_timer = None
        self._main_layout = None
        self._top_spacer = None
        self.loading_spinner = None
        self.empty_label = None
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self.count_label = None
        self._pagination_bar = None

        self._initialized = False
        self._going_back = False

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
        if hasattr(self, 'count_label'):
            self.count_label.text_color = ArtistColors.get_accent(theme_id)
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

        top_padding = max(layout_config.get_top_padding() - dp(8), dp(20))
        self._top_spacer = Widget(size_hint_y=None, height=top_padding)
        main_layout.add_widget(self._top_spacer)

        self.count_label = MDLabel(
            text="", font_size=sp(13), halign="center",
            size_hint_y=None, height=dp(28),
            theme_text_color="Custom", opacity=0, bold=True)
        main_layout.add_widget(self.count_label)

        bottom_padding = layout_config.get_bottom_padding()

        cards_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), dp(0)])

        self.recycle_view = SongRecycleView(on_song_click=self.on_song_selected)
        cards_container.add_widget(self.recycle_view)
        main_layout.add_widget(cards_container)

        self._pagination_bar = PaginationBar(
            on_page_select=self._on_page_selected_from_bar,
        )
        self._pagination_bar.height = 0
        self._pagination_bar.opacity = 0
        self._pagination_bar.disabled = True
        main_layout.add_widget(self._pagination_bar)

        main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))

        self.add_widget(main_layout)
        self._initialized = True
        self.update_theme_colors()

    # ============ COUNT LABEL ============

    def _update_count_label(self, total):
        """
        total == 0      → «Нет песен»
        total == 1      → «1 песня»
        total <= limit  → «N песен»
        total >  limit  → «{current_count} из {total} песен»
        """
        if not self.count_label:
            return

        if total == 0:
            self.count_label.text = get_text('no_songs')
            self.count_label.opacity = 1
            return

        if total > self._limit:
            current_count = min((self._page + 1) * self._limit, total)
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
        if not self._pagination_bar:
            return
        self._pagination_bar.height = 0
        self._pagination_bar.opacity = 0
        self._pagination_bar.disabled = True

    def _show_pagination_bar(self):
        if not self._pagination_bar:
            return
        if self._total_songs <= self._limit:
            self._hide_pagination()
            return
        self._pagination_bar.height = dp(48)
        self._pagination_bar.opacity = 1
        self._pagination_bar.disabled = False
        self._pagination_bar.set_total(self._total_songs, self._limit, self._page)

    def _on_page_selected_from_bar(self, page_index):
        if page_index == self._page:
            return
        self._load_page(page_index)

    def _is_page_cached(self, cache, page):
        start = page * self._limit
        total = cache['total']
        if total:
            end = min(start + self._limit, total)
        else:
            end = start + self._limit
        for idx in range(start, end):
            if idx not in cache['items']:
                return False
        return True

    def _build_page_slice(self, cache, page):
        start = page * self._limit
        end = start + self._limit
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
            logger.info(f"⏳ Батч уже грузится — запомнили страницу {page}")
            return

        batch_offset = (page * self._limit) // self._batch_size * self._batch_size
        self._load_batch(self.artist_name, batch_offset, page)

    def _load_batch(self, artist, batch_offset, target_page):
        cache = self._songs_cache.get(artist)
        if cache is None:
            cache = {'items': {}, 'total': 0, 'batches': set()}
            self._songs_cache[artist] = cache

        if batch_offset in cache['batches']:
            logger.info(f"♻️ Батч {batch_offset} уже в кеше для {artist}")
            self._batch_loading = False
            self._display_page(self._build_page_slice(cache, target_page))
            return

        self._batch_loading = True
        self._show_loading()

        def _on_success(data):
            try:
                self._batch_loading = False
                self._is_loading = False

                if data is None:
                    data = {"songs": [], "total": 0}
                if not isinstance(data, dict):
                    data = {"songs": [], "total": 0}

                songs = data.get('songs', [])
                total = data.get('total', 0)
                if not isinstance(songs, list):
                    songs = []

                for i, s in enumerate(songs):
                    sid = s.get('song_id', 0) if isinstance(s, dict) else 0
                    title = s.get('title', '') if isinstance(s, dict) else ''
                    tabs = s.get('tabs_count', 1) if isinstance(s, dict) else 1
                    cache['items'][batch_offset + i] = {
                        'song_id': sid,
                        'title': title,
                        'tabs_count': tabs,
                        'on_click': self.on_song_selected,
                    }

                if total > 0:
                    cache['total'] = total
                if batch_offset not in cache['batches']:
                    cache['batches'].add(batch_offset)

                self._total_songs = cache['total']

                logger.info(
                    f"📦 Батч песен '{artist}' offset={batch_offset}: "
                    f"+{len(songs)} (в кеше {len(cache['items'])}/{cache['total']}, "
                    f"батчей {len(cache['batches'])})"
                )

                show_page = self._pending_page
                self._pending_page = None
                if show_page is None:
                    show_page = target_page

                self._page = show_page

                if not self._is_page_cached(cache, show_page):
                    if cache['total'] and show_page * self._limit >= cache['total']:
                        self._hide_loading()
                        self._update_count_label(self._total_songs)
                        self._display_page(self._build_page_slice(cache, show_page))
                        return

                    batch_offset2 = (show_page * self._limit) // self._batch_size * self._batch_size
                    logger.info(
                        f"📥 Для страницы {show_page} нужен ещё батч offset={batch_offset2}"
                    )
                    self._load_batch(artist, batch_offset2, show_page)
                    return

                self._hide_loading()
                self._update_top_nav_title(artist)
                self._update_count_label(self._total_songs)
                self._display_page(self._build_page_slice(cache, show_page))

            except Exception as e:
                self._batch_loading = False
                self._is_loading = False
                self._pending_page = None
                self._hide_loading()
                logger.error(f"❌ Ошибка в _on_success (artist_songs): {e}")
                import traceback
                traceback.print_exc()
                self._show_empty(get_text('loading_error'))

        def _on_error(req, err):
            self._batch_loading = False
            self._is_loading = False
            self._pending_page = None
            self._hide_loading()
            logger.error(f"Ошибка загрузки песен '{artist}': {err}")
            self._update_top_nav_title(artist)
            self._update_count_label(0)
            self._show_empty(get_text('loading_error'))

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
        if self.recycle_view:
            self.recycle_view.set_songs(songs_slice, self.on_song_selected)
        Clock.schedule_once(lambda dt: setattr(self.recycle_view, 'scroll_y', 1.0), 0.1)

        if self._total_songs > self._limit:
            self._show_pagination_bar()
        else:
            self._hide_pagination()

    # ============ ОСНОВНЫЕ МЕТОДЫ ============

    def set_artist(self, artist):
        self.artist_name = artist
        self._total_songs = 0
        self._page = 0
        self._is_loading = False
        self._batch_loading = False
        self._pending_page = None

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

        if self.recycle_view:
            self.recycle_view.clear()
        self._hide_empty()
        self._hide_pagination()
        self._show_loading()

        cache = self._songs_cache.get(artist)
        if cache is not None and self._is_page_cached(cache, 0):
            self._is_loading = False
            self._hide_loading()
            self._total_songs = cache['total']
            self._update_top_nav_title(artist)
            self._update_count_label(self._total_songs)
            self._display_page(self._build_page_slice(cache, 0))
            return

        self._songs_cache[artist] = {'items': {}, 'total': 0, 'batches': set()}
        self._load_batch(artist, batch_offset=0, target_page=0)

    # ---- Заглушки для совместимости ----

    def _on_first_page_loaded(self, data):
        pass

    def _on_next_page_loaded(self, data):
        pass

    def _load_next_pages(self):
        pass

    def _display_songs(self):
        if not self.artist_name:
            return
        cache = self._songs_cache.get(self.artist_name)
        if cache is None:
            return
        self._update_count_label(self._total_songs)
        self._display_page(self._build_page_slice(cache, self._page))

    # ---- Загрузка / пусто ----

    def _show_loading(self):
        if self.loading_spinner:
            return
        if self.recycle_view:
            self.recycle_view.clear()

        self.loading_spinner = LoadingSpinner(text=get_text('loading_songs', 'Загрузка песен...'))
        self.loading_spinner.start_animation()
        if self._main_layout:
            self._main_layout.add_widget(self.loading_spinner)

    def _hide_loading(self):
        if self.loading_spinner:
            self.loading_spinner.stop_animation()
            if self.loading_spinner.parent:
                self.loading_spinner.parent.remove_widget(self.loading_spinner)
        self.loading_spinner = None

    def _show_empty(self, text=None):
        if self.empty_label:
            return
        theme_id = settings_manager.theme
        self.empty_label = MDLabel(
            text=text or get_text('no_artist_songs', 'Нет песен у этого исполнителя'),
            halign="center", font_size=sp(14),
            theme_text_color="Custom",
            text_color=ArtistColors.get_hint_color(theme_id),
            size_hint_y=None, height=dp(60))
        if self._main_layout:
            self._main_layout.add_widget(self.empty_label)

    def _hide_empty(self):
        if self.empty_label and self.empty_label.parent:
            self.empty_label.parent.remove_widget(self.empty_label)
        self.empty_label = None

    def _on_load_failed(self, req, error):
        self._is_loading = False
        self._batch_loading = False
        self._hide_loading()
        logger.error(f"Ошибка загрузки для {self.artist_name}: {error}")

        if self.recycle_view:
            self.recycle_view.clear()
        self._hide_pagination()
        self._update_top_nav_title(self.artist_name)
        self._update_count_label(0)
        self._show_empty(get_text('loading_error'))

    # ---- Переходы ----

    def on_song_selected(self, song_id, song_title):
        if not song_id:
            notify.error(get_text('load_error'))
            return

        if self.recycle_view:
            self._saved_scroll_position = self.recycle_view.scroll_y

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

    def on_enter(self):
        if self.artist_name:
            self._update_top_nav_title(self.artist_name)
            self._update_count_label(self._total_songs)

        if hasattr(self, '_pending_artist') and self._pending_artist:
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
            self._update_count_label(self._total_songs)
            self._display_page(self._build_page_slice(cache, self._page))

    def on_leave(self):
        self._hide_loading()
        if self.manager and self.manager.current != 'song_detail':
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.clear_custom_title_widget()