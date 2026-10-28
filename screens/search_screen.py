# screens/search_screen.py
import time
import re
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from io import BytesIO
from threading import Thread

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.app import MDApp

from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from utils.screen_state import screen_state
from utils.settings_manager import settings_manager
from utils.localization import get_text
from state.search_state import search_state
from screens.components.loading_spinner import LoadingSpinner
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout

logger = screen_logger('SearchScreen')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА
# ============================================================

class SearchColors:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        return [0.10, 0.42, 0.25, 1]

    @staticmethod
    def get_term_icon_color(theme_id):
        if theme_id == 'green':
            return [0.2, 0.6, 1.0, 1]
        elif theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        return [1.0, 0.5, 0.0, 1]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light': return [0.1, 0.1, 0.1, 1]
        return [1, 1, 1, 1]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light': return [0.4, 0.4, 0.4, 1]
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
    def get_hint_color(theme_id):
        if theme_id == 'light': return [0.1, 0.1, 0.1, 1]
        return [1, 1, 1, 1]

    @staticmethod
    def get_arrow_color(theme_id):
        if theme_id == 'light': return [0, 0, 0, 1]
        return [1, 1, 1, 1]


# ============ ПОИСКОВАЯ СТРОКА ============

class SearchBar(MDCard):
    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(16)] * 4
        self.elevation = 0
        self.padding = [dp(12), dp(4), dp(6), dp(4)]
        self.spacing = dp(6)
        self.theme_line_color = "Custom"
        self.theme_bg_color = "Custom"
        self.ripple_behavior = False

        self.search_field = TextInput(
            multiline=False, size_hint_x=1, height=dp(40), font_size=sp(16),
            background_color=[1, 1, 1, 0], background_normal="", background_active="",
            padding=[0, dp(10), 0, dp(4)], on_text_validate=self._on_search_pressed)
        self.search_field.bind(text=self._on_text_change)
        self.search_field.bind(focus=self._on_focus)

        self.clear_wrapper = MDCard(
            size_hint=(None, None), size=(dp(30), dp(30)), radius=[dp(15)] * 4,
            md_bg_color=[0, 0, 0, 0], elevation=0, pos_hint={'center_y': 0.5},
            opacity=0, disabled=True, ripple_behavior=False)
        self.clear_btn = MDIconButton(
            icon="close-circle-outline", size_hint=(1, 1), theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0], on_release=self._on_clear_pressed, ripple_scale=0)
        self.clear_wrapper.add_widget(self.clear_btn)

        self.search_btn = MDRaisedButton(
            text="", size_hint=(None, None), size=(dp(64), dp(36)),
            text_color=[1, 1, 1, 1], font_size=sp(13), elevation=0,
            pos_hint={'center_y': 0.5}, ripple_scale=0)
        try:
            self.search_btn._radius = dp(10)
            self.search_btn.elevation = 0
        except Exception:
            pass
        self.search_btn.bind(on_release=self._on_search_pressed)

        self.add_widget(self.search_field)
        self.add_widget(self.clear_wrapper)
        self.add_widget(self.search_btn)
        self.update_language()
        self.update_theme_colors()

    def update_language(self):
        self.search_field.hint_text = get_text('search', 'Поиск')
        self.search_btn.text = get_text('find', 'Найти')

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = SearchColors.get_accent(theme_id)
        text_p = SearchColors.get_text_primary(theme_id)
        text_s = SearchColors.get_text_secondary(theme_id)
        line = SearchColors.get_card_line(theme_id)

        if theme_id == 'light':
            self.md_bg_color = [1, 1, 1, 1]
            self.line_color = line
            self.line_width = 4.0
            self.search_field.foreground_color = text_p
            self.search_field.hint_text_color = text_s
            self.search_field.cursor_color = accent
            self.clear_btn.icon_color = accent
            self.search_btn.md_bg_color = accent
            self.search_btn.text_color = [0, 0, 0, 1]
        elif theme_id == 'dark':
            self.md_bg_color = [0.15, 0.15, 0.15, 1]
            self.line_color = line
            self.line_width = 4.0
            self.search_field.foreground_color = text_p
            self.search_field.hint_text_color = text_s
            self.search_field.cursor_color = accent
            self.clear_btn.icon_color = accent
            self.search_btn.md_bg_color = accent
            self.search_btn.text_color = [1, 1, 1, 1]
        else:
            self.md_bg_color = [1, 1, 1, 1]
            self.line_color = line
            self.line_width = 4.0
            self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]
            self.search_field.hint_text_color = [0.55, 0.55, 0.55, 1]
            self.search_field.cursor_color = [0.1, 0.1, 0.1, 1]
            self.clear_btn.icon_color = [0.4, 0.4, 0.4, 0.8]
            self.search_btn.md_bg_color = accent
            self.search_btn.text_color = [1, 1, 1, 1]

    def _on_text_change(self, instance, text):
        self.current_query = text
        self.clear_wrapper.opacity = 1 if text.strip() else 0
        self.clear_wrapper.disabled = not bool(text.strip())

    def _on_search_pressed(self, *args):
        if self.on_search:
            t = self.search_field.text.strip()
            if t: self.on_search(t)

    def _on_clear_pressed(self, instance):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""
        if self.on_clear: self.on_clear()
        self.search_field.focus = False

    def _on_focus(self, instance, value):
        self.line_width = 5.0 if value else 4.0

    def set_text(self, text):
        self.search_field.text = text or ""
        self._on_text_change(None, self.search_field.text)

    def clear(self):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""


# ============ КАРТОЧКА РЕЗУЛЬТАТА ============

class ResultCard(MDCard):
    CARD_HEIGHT = dp(56)

    def __init__(self, title='', result_type='song', subtitle='', song_id=None,
                 chord_name=None, term_id=None, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.result_type = result_type
        self.subtitle = subtitle
        self.song_id = song_id
        self.chord_name = chord_name
        self.term_id = term_id
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = self.CARD_HEIGHT
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.clip = True
        self.theme_line_color = "Custom"
        self.theme_bg_color = "Custom"
        self.padding = [0, 0, 0, 0]
        self.spacing = 0

        self.content = MDBoxLayout(orientation='horizontal',
                                   padding=[dp(12), dp(4), dp(12), dp(4)],
                                   spacing=dp(8), md_bg_color=[0, 0, 0, 0])
        self.add_widget(self.content)

        self._icon_widget = None
        self._name_label = None
        self._artist_label = None
        self._title_label = None
        self._arrow = None

        self._build_content()
        self.update_theme_colors()
        self.bind(on_release=self._on_click)

    def _build_content(self):
        self.content.clear_widgets()

        if self.result_type == 'chord':
            icon = Image(size_hint=(None, 1), width=dp(24), allow_stretch=True, keep_ratio=True)
            self._load_asset_icon(icon, 'chords_png')
            label = MDLabel(font_size=sp(15), theme_text_color="Custom", bold=True,
                            shorten=True, shorten_from="right", valign="middle", size_hint_x=1)
            label.text = self.title
            self.content.add_widget(icon)
            self.content.add_widget(label)
            self._icon_widget = icon
            self._name_label = label

        elif self.result_type == 'term':
            icon = MDIcon(icon="book-open-variant", size_hint=(None, 1), width=dp(24),
                          theme_text_color="Custom", font_size=sp(20))
            label = MDLabel(font_size=sp(15), theme_text_color="Custom", bold=True,
                            shorten=True, shorten_from="right", valign="middle", size_hint_x=1)
            label.text = self.title
            self.content.add_widget(icon)
            self.content.add_widget(label)
            self._icon_widget = icon
            self._name_label = label

        else:  # song
            icon = Image(size_hint=(None, 1), width=dp(24), allow_stretch=True, keep_ratio=True)
            self._load_asset_icon(icon, 'song_png')

            text_layout = MDBoxLayout(orientation='vertical', size_hint_x=1,
                                      spacing=dp(1), pos_hint={'center_y': 0.5})
            artist_label = MDLabel(font_size=sp(15), size_hint_y=None, height=dp(20),
                                   theme_text_color="Custom", bold=True, shorten=True)
            title_label = MDLabel(font_size=sp(12), size_hint_y=None, height=dp(16),
                                  theme_text_color="Custom", shorten=True)
            artist_label.text = self.title
            title_label.text = self.subtitle

            text_layout.add_widget(artist_label)
            text_layout.add_widget(title_label)

            self.content.add_widget(icon)
            self.content.add_widget(text_layout)
            self._icon_widget = icon
            self._artist_label = artist_label
            self._title_label = title_label

        arrow = MDLabel(text="›", font_size=sp(20), size_hint_x=None, width=dp(20),
                        halign="center", valign="middle", theme_text_color="Custom")
        self.content.add_widget(arrow)
        self._arrow = arrow

    def _load_asset_icon(self, image_widget, asset_name):
        if HAS_ASSETS:
            try:
                data = load_asset_as_bytes(asset_name)
                if data:
                    img = CoreImage(BytesIO(data), ext="png")
                    image_widget.texture = img.texture
                    return
            except Exception:
                pass
        image_widget.texture = None
        image_widget.text = "🎵"

    def update_data(self, title, result_type='song', subtitle='', song_id=None,
                    chord_name=None, term_id=None, on_click=None):
        self.title = title
        self.subtitle = subtitle
        self.song_id = song_id
        self.chord_name = chord_name
        self.term_id = term_id
        if on_click:
            self.on_click_callback = on_click

        if self.result_type != result_type:
            self.result_type = result_type
            self._build_content()
        else:
            if self._name_label:
                self._name_label.text = title
            if self._artist_label:
                self._artist_label.text = title
                self._title_label.text = subtitle

        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = SearchColors.get_accent(theme_id)
        self.md_bg_color = SearchColors.get_card_bg(theme_id)
        self.line_color = SearchColors.get_card_line(theme_id)
        self.line_width = 2.0

        if self._icon_widget:
            if isinstance(self._icon_widget, MDIcon):
                self._icon_widget.text_color = (
                    SearchColors.get_term_icon_color(theme_id)
                    if self.result_type == 'term' else accent
                )

        if self._name_label:
            self._name_label.text_color = SearchColors.get_text_primary(theme_id)
        if self._artist_label:
            self._artist_label.text_color = SearchColors.get_text_primary(theme_id)
            self._title_label.text_color = SearchColors.get_text_secondary(theme_id)
        if self._arrow:
            self._arrow.text_color = [0, 0, 0, 0.6] if theme_id == 'light' else [1, 1, 1, 0.3]

    def _on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.result_type, self.chord_name, self.song_id, self.term_id)


# ============ КОНТЕЙНЕР КАРТОЧЕК ============

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

    def _ensure_pool(self, count, on_click):
        while len(self._card_pool) < count:
            card = ResultCard(on_click=on_click)
            self.add_widget(card)
            self._card_pool.append(card)

    def _apply_pool(self, items, on_click):
        self._ensure_pool(self.max_cards, on_click)
        for i in range(self.max_cards):
            card = self._card_pool[i]
            if i < len(items):
                item = items[i]
                card.update_data(
                    title=item.get('title', ''),
                    result_type=item.get('result_type', 'song'),
                    subtitle=item.get('subtitle', ''),
                    song_id=item.get('song_id'),
                    chord_name=item.get('chord_name'),
                    term_id=item.get('term_id'),
                    on_click=on_click
                )
                card.height = ResultCard.CARD_HEIGHT
                card.opacity = 1
                card.disabled = False
            else:
                card.height = ResultCard.CARD_HEIGHT
                card.opacity = 0
                card.disabled = True

        self.cards = self._card_pool[:len(items)]
        self.height = (self.max_cards * ResultCard.CARD_HEIGHT + (
                    self.max_cards - 1) * self.spacing) if self.max_cards > 0 else 0

        if self.parent and hasattr(self.parent, '_update_cards_layout'):
            Clock.schedule_once(lambda dt: self.parent._update_cards_layout(len(items)), 0)

    def set_cards(self, items, on_click):
        self._apply_pool(items, on_click)

    def clear(self):
        for card in self._card_pool:
            card.opacity = 0
            card.disabled = True
        self.cards = []
        self.height = (self.max_cards * ResultCard.CARD_HEIGHT + (
                    self.max_cards - 1) * self.spacing) if self.max_cards > 0 else 0
        if self.parent and hasattr(self.parent, '_update_cards_layout'):
            Clock.schedule_once(lambda dt: self.parent._update_cards_layout(0), 0)

    def update_theme_colors(self):
        for c in self._card_pool:
            c.update_theme_colors()


# ============ ОБЁРТКА СО СВАЙПОМ ============

class SwipeableCardsWrapper(FloatLayout):
    def __init__(self, on_swipe_up=None, on_swipe_down=None, **kwargs):
        super().__init__(**kwargs)
        self.on_swipe_up = on_swipe_up
        self.on_swipe_down = on_swipe_down
        self._touch_start = None
        self._swipe_handled = False

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos): return super().on_touch_down(touch)
        self._touch_start = touch.pos
        self._swipe_handled = False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._touch_start is not None and not self._swipe_handled:
            dx = touch.x - self._touch_start[0]
            dy = touch.y - self._touch_start[1]
            if abs(dy) > dp(40) and abs(dy) > abs(dx) * 1.2:
                self._swipe_handled = True
                if dy > 0 and self.on_swipe_down:
                    self.on_swipe_down()
                elif dy < 0 and self.on_swipe_up:
                    self.on_swipe_up()
                self._touch_start = None
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._touch_start is None: return super().on_touch_up(touch)
        self._touch_start = None
        self._swipe_handled = False
        return super().on_touch_up(touch)


# ============ ПАГИНАЦИЯ ============

class PaginationArrow(MDBoxLayout):
    def __init__(self, icon_name, on_press=None, icon_color=None, width=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, 1)
        self.width = width if width else dp(40)
        self.padding = [dp(2)] * 4
        self.md_bg_color = [0, 0, 0, 0]
        self._on_press = on_press
        self._enabled = True
        self._pressed = False

        container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 1))
        self.icon_widget = MDIcon(icon=icon_name, font_size=sp(22), theme_text_color="Custom",
                                  text_color=icon_color if icon_color else [1, 1, 1, 1],
                                  size_hint=(None, None), size=(dp(24), dp(24)))
        container.add_widget(self.icon_widget)
        self.add_widget(container)

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.opacity = 1.0 if enabled else 0.3

    def set_color(self, color):
        self.icon_widget.text_color = color

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos): return super().on_touch_down(touch)
        if not self._enabled: return True
        self._pressed = True
        touch.grab(self)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self: return super().on_touch_up(touch)
        touch.ungrab(self)
        if self._pressed:
            self._pressed = False
            if self._enabled and self.collide_point(*touch.pos) and self._on_press: self._on_press()
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

        self.jump_back_arrow = PaginationArrow("chevron-double-left", on_press=self._go_back_10, width=dp(36))
        self.prev_arrow = PaginationArrow("chevron-left", on_press=self._go_prev_page, width=dp(36))
        self.page_label = MDLabel(text="1", font_size=sp(16), halign="center", valign="middle",
                                  theme_text_color="Custom", text_color=[1, 1, 1, 1], bold=True,
                                  size_hint=(None, 1), width=dp(40))
        self.next_arrow = PaginationArrow("chevron-right", on_press=self._go_next_page, width=dp(36))
        self.jump_forward_arrow = PaginationArrow("chevron-double-right", on_press=self._go_forward_10, width=dp(36))

        self.add_widget(self.jump_back_arrow)
        self.add_widget(self.prev_arrow)
        self.add_widget(self.page_label)
        self.add_widget(self.next_arrow)
        self.add_widget(self.jump_forward_arrow)

        self._update_width()
        self.update_theme_colors()

    def on_touch_down(self, touch):
        if self.parent is not None and self.parent.height < dp(10): return False
        return super().on_touch_down(touch)

    def _update_width(self):
        self.width = (dp(4) + dp(4) + self.jump_back_arrow.width + self.spacing +
                      self.prev_arrow.width + self.spacing + self.page_label.width +
                      self.spacing + self.next_arrow.width + self.spacing + self.jump_forward_arrow.width)

    def set_total(self, total_items, per_page, current_page=0, on_click=None):
        if on_click: self.on_page_select = on_click
        new_total_pages = max(1, (total_items + per_page - 1) // per_page)
        if self._last_total == total_items and self._last_per_page == per_page and self.total_pages == new_total_pages:
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
        if self.current_page_index > 0:
            self.current_page_index = max(0, self.current_page_index - 10)
            self._apply_page()
            if self.on_page_select: self.on_page_select(self.current_page_index)

    def _go_prev_page(self):
        if self.current_page_index > 0:
            self.current_page_index -= 1
            self._apply_page()
            if self.on_page_select: self.on_page_select(self.current_page_index)

    def _go_next_page(self):
        if self.current_page_index < self.total_pages - 1:
            self.current_page_index += 1
            self._apply_page()
            if self.on_page_select: self.on_page_select(self.current_page_index)

    def _go_forward_10(self):
        if self.current_page_index < self.total_pages - 1:
            self.current_page_index = min(self.total_pages - 1, self.current_page_index + 10)
            self._apply_page()
            if self.on_page_select: self.on_page_select(self.current_page_index)

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        arrow_color = SearchColors.get_arrow_color(theme_id)
        self.jump_back_arrow.set_color(arrow_color)
        self.jump_forward_arrow.set_color(arrow_color)
        self.prev_arrow.set_color(arrow_color)
        self.next_arrow.set_color(arrow_color)
        self.page_label.text_color = SearchColors.get_text_primary(theme_id)


# ============ ОСНОВНОЙ ЭКРАН ============

class SearchScreen(BaseScreen):
    MIN_PAGE_SIZE = 3
    MAX_PAGE_SIZE = 12
    PAGINATION_HEIGHT = dp(48) + dp(1) + dp(2)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'search'
        self.bg_image = None
        self.bg_color_inst = None
        self.bg_rect = None
        self._search_thread = None
        self._is_searching = False
        self.current_query = ""
        self._state_restored = False
        self._block_transition = False

        self._all_chords = []
        self._all_songs = []
        self._all_terms = []
        self._active_tab = 'songs'

        self._page = 0
        self._page_size = 6
        self._page_size_locked = False

        self._loading_overlay = None
        self._loading_spinner_widget = None

        self._cards_wrapper = None
        self.cards_container = None
        self._cards_top_offset = dp(6)
        self._cards_left_pad = dp(0)
        self._cards_right_pad = dp(0)
        self._pagination_container = None
        self._pagination_bar = None
        self._result_label = None

        self.load_background()
        self.init_ui()
        logger.info('Экран поиска создан')

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
            logger.error(f'Ошибка фона: {e}')
        self.update_screen_background()

    def _update_rect(self, *args):
        if hasattr(self, 'bg_rect') and self.bg_rect:
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def update_screen_background(self):
        if not hasattr(self, 'bg_color_inst') or not hasattr(self, 'bg_rect'): return
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
        if hasattr(self, 'search_bar'): self.search_bar.update_theme_colors()
        if hasattr(self, 'title_label'):
            self.title_label.text_color = SearchColors.get_hint_color(theme_id)
        if hasattr(self, 'tabs_container'):
            self._update_tabs_buttons()
        if self._result_label:
            self._result_label.text_color = SearchColors.get_hint_color(theme_id)
        if self.cards_container:
            self.cards_container.update_theme_colors()
        if self._pagination_bar:
            self._pagination_bar.update_theme_colors()

    def update_language(self):
        if self.search_bar: self.search_bar.update_language()
        if hasattr(self, 'title_label'):
            self.title_label.text = get_text('what_to_search', 'Что будем искать?')
        if self._all_songs or self._all_terms or self._all_chords:
            self._update_tabs_buttons()

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        main_layout.add_widget(Widget(size_hint_y=None, height=layout_config.get_top_padding()))
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(16)))

        self.title_label = MDLabel(
            text=get_text('what_to_search', 'Что будем искать?'),
            font_size=sp(16), halign="center",
            size_hint_y=None, height=dp(36),
            theme_text_color="Custom", bold=True)
        main_layout.add_widget(self.title_label)
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        search_container = MDBoxLayout(orientation='vertical', size_hint=(1, None),
                                       height=dp(52), padding=[dp(16), 0, dp(16), 0])
        self.search_bar = SearchBar(on_search=self.perform_search, on_clear=self.clear_search)
        search_container.add_widget(self.search_bar)
        main_layout.add_widget(search_container)
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Вкладки
        self.tabs_container = MDBoxLayout(
            orientation='horizontal', size_hint=(1, None), height=dp(40),
            padding=[dp(16), 0, dp(16), dp(8)], spacing=dp(6), md_bg_color=[0, 0, 0, 0]
        )
        main_layout.add_widget(self.tabs_container)

        self.tab_btn_songs = MDRaisedButton(text="Песни", on_release=lambda x: self._switch_tab('songs'),
                                            ripple_scale=0)
        self.tab_btn_chords = MDRaisedButton(text="Аккорды", on_release=lambda x: self._switch_tab('chords'),
                                             ripple_scale=0)
        self.tab_btn_terms = MDRaisedButton(text="Термины", on_release=lambda x: self._switch_tab('terms'),
                                            ripple_scale=0)

        self.tabs_container.add_widget(self.tab_btn_songs)
        self.tabs_container.add_widget(self.tab_btn_chords)
        self.tabs_container.add_widget(self.tab_btn_terms)

        # Лейбл
        self._result_label = MDLabel(
            text="", font_size=sp(12), halign="center", valign="middle",
            size_hint_y=None, height=dp(24), theme_text_color="Custom",
            text_color=SearchColors.get_hint_color(settings_manager.theme),
            opacity=0, bold=True)
        main_layout.add_widget(self._result_label)

        # Контейнер карточек (Wrapper)
        padding = layout_config.get_content_padding()
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
        self.cards_container.max_cards = self._page_size
        self._cards_wrapper.add_widget(self.cards_container)

        self._cards_wrapper.bind(
            size=lambda *a: self._update_cards_layout(len(self.cards_container.cards)),
            pos=lambda *a: self._update_cards_layout(len(self.cards_container.cards)),
        )

        main_layout.add_widget(self._cards_wrapper)

        # Пагинация
        bottom_padding = layout_config.get_pagination_bottom_padding()
        self._pagination_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, None), height=0,
            md_bg_color=[0, 0, 0, 0], padding=[padding[0], dp(0), padding[2], dp(0)])
        self._pagination_anchor = FloatLayout(size_hint=(1, 1))
        self._pagination_bar = PaginationBar(on_page_select=self._on_page_selected)
        self._pagination_bar.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self._pagination_anchor.add_widget(self._pagination_bar)
        self._pagination_container.add_widget(self._pagination_anchor)
        main_layout.add_widget(self._pagination_container)

        main_layout.add_widget(Widget(size_hint_y=None, height=bottom_padding))
        self.add_widget(main_layout)
        self.update_theme_colors()

        self._update_tabs_buttons()
        self._switch_tab('songs')

    def _update_cards_layout(self, count):
        if not self.cards_container or not self._cards_wrapper: return
        if self._cards_wrapper.height <= 1: return

        self.cards_container.max_cards = self._page_size
        h_card = ResultCard.CARD_HEIGHT

        self.cards_container.x = self._cards_wrapper.x + self._cards_left_pad
        self.cards_container.width = max(dp(50),
                                         self._cards_wrapper.width - self._cards_left_pad - self._cards_right_pad)
        n_total = self.cards_container.max_cards
        self.cards_container.spacing = dp(6)
        self.cards_container.height = (n_total * h_card + (n_total - 1) * self.cards_container.spacing)

        try:
            label_bottom = self._result_label.to_window(self._result_label.x, self._result_label.y, initial=False)[1]
            wrapper_top = self._cards_wrapper.to_window(self._cards_wrapper.x, self._cards_wrapper.y, initial=False)[
                              1] + self._cards_wrapper.height
            desired_top = label_bottom - self._cards_top_offset
            max_top = wrapper_top - self._cards_top_offset
            self.cards_container.top = min(desired_top, max_top)
        except Exception:
            self.cards_container.top = self._cards_wrapper.top - self._cards_top_offset

    def _show_loading_spinner(self):
        if self._loading_overlay: return
        overlay = FloatLayout(size_hint=(1, 1))
        spinner = LoadingSpinner(text=get_text('loading', 'Поиск...'))
        spinner.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        with overlay.canvas.before:
            Color(0, 0, 0, 0.4)
            rect = Rectangle(pos=overlay.pos, size=overlay.size)
        overlay.bind(pos=lambda inst, val: setattr(rect, 'pos', val),
                     size=lambda inst, val: setattr(rect, 'size', val))

        overlay.add_widget(spinner)
        spinner.start_animation()
        self._loading_overlay = overlay
        self._loading_spinner_widget = spinner
        self.add_widget(overlay)

    def _hide_loading_spinner(self):
        if self._loading_spinner_widget:
            self._loading_spinner_widget.stop_animation()
            self._loading_spinner_widget = None
        if self._loading_overlay:
            if self._loading_overlay.parent:
                self._loading_overlay.parent.remove_widget(self._loading_overlay)
            self._loading_overlay = None

    def _switch_tab(self, tab):
        self._active_tab = tab
        self._page = 0
        self._update_tabs_buttons()
        self._display_results()

    def _update_tabs_buttons(self):
        theme_id = settings_manager.theme
        accent = SearchColors.get_accent(theme_id)
        text_p = SearchColors.get_text_primary(theme_id)
        bg_inactive = [0.9, 0.9, 0.9, 1] if theme_id == 'light' else [0.2, 0.2, 0.2, 1]

        buttons = {
            'songs': (self.tab_btn_songs, len(self._all_songs)),
            'chords': (self.tab_btn_chords, len(self._all_chords)),
            'terms': (self.tab_btn_terms, len(self._all_terms))
        }

        for tab, (btn, count) in buttons.items():
            label = {
                'songs': get_text('songs', 'Песни'),
                'chords': get_text('chords', 'Аккорды'),
                'terms': get_text('terms', 'Термины')
            }[tab]

            btn.text = f"{label} ({count})"
            if self._active_tab == tab:
                btn.md_bg_color = accent
                btn.text_color = [1, 1, 1, 1]
            else:
                btn.md_bg_color = bg_inactive
                btn.text_color = text_p
            btn.size_hint = (1, 1)
            btn.font_size = sp(11)

    def _on_page_selected(self, page_index):
        if page_index == self._page: return
        self._page = page_index
        self._display_results()

    def _display_results(self):
        self.cards_container.clear()
        self._is_searching = False

        # Жёсткая проверка: если поиска не было, ничего не показываем и скрываем всё
        if not self.current_query:
            self._pagination_container.height = 0
            self._result_label.opacity = 0
            return

        if self._active_tab == 'songs':
            items = self._all_songs
        elif self._active_tab == 'chords':
            items = self._all_chords
        else:
            items = self._all_terms

        if not items:
            self._pagination_container.height = 0
            self._result_label.opacity = 0
            return

        total = len(items)
        start = self._page * self._page_size
        end = min(start + self._page_size, total)
        page_slice = items[start:end]

        cards_data = []
        for item in page_slice:
            if self._active_tab == 'songs':
                cards_data.append({
                    'title': item.get('artist', ''),
                    'result_type': 'song',
                    'subtitle': item.get('title', ''),
                    'song_id': item.get('song_id'),
                })
            elif self._active_tab == 'chords':
                chord_title = item.get('main_name', '')
                cards_data.append({
                    'title': chord_title,
                    'result_type': 'chord',
                    'chord_name': chord_title,
                })
            else:
                cards_data.append({
                    'title': item.get('name', ''),
                    'result_type': 'term',
                    'term_id': item.get('id'),
                })

        self.cards_container.set_cards(cards_data, self.on_result_selected)

        label = {
            'songs': get_text('found_songs', 'Найденные песни'),
            'chords': get_text('found_chords', 'Найденные аккорды'),
            'terms': get_text('found_terms', 'Найденные термины')
        }[self._active_tab]

        if total > self._page_size:
            current = end - start
            self._result_label.text = f"{label}: {current} {get_text('of', 'из')} {total}"
        else:
            self._result_label.text = f"{label}: {total}"
        self._result_label.opacity = 1

        self._pagination_container.height = self.PAGINATION_HEIGHT
        self._pagination_bar.set_total(total, self._page_size, self._page)

        Clock.schedule_once(lambda dt: self._update_cards_layout(len(page_slice)), 0)

    def _on_swipe_up(self):
        if self._total_items() > 0:
            max_page = (self._total_items() - 1) // self._page_size
            if self._page < max_page:
                self._on_page_selected(self._page + 1)

    def _on_swipe_down(self):
        if self._total_items() > 0:
            if self._page > 0:
                self._on_page_selected(self._page - 1)

    def _total_items(self):
        if self._active_tab == 'songs':
            return len(self._all_songs)
        elif self._active_tab == 'chords':
            return len(self._all_chords)
        return len(self._all_terms)

    def save_current_state(self):
        if self._block_transition: return
        search_state.save({
            'query': self.current_query,
            'songs': self._all_songs,
            'chords': self._all_chords,
            'terms': self._all_terms,
            'active_tab': self._active_tab,
            'page': self._page,
        })

    def restore_state(self):
        if self._block_transition or self._state_restored:
            return self._state_restored
        state = search_state.get(allow_stale=True)
        if not state: return False
        try:
            self._all_songs = state.get('songs', [])
            self._all_chords = state.get('chords', [])
            self._all_terms = state.get('terms', [])
            self._active_tab = state.get('active_tab', 'songs')
            self._page = state.get('page', 0)

            if state.get('query'):
                self.current_query = state['query']
                self.search_bar.set_text(self.current_query)

            if self._all_songs or self._all_chords or self._all_terms:
                self._update_tabs_buttons()
                self._display_results()
            else:
                self.cards_container.clear()
                self._pagination_container.height = 0
                self._result_label.opacity = 0

            self._state_restored = True
            return True
        except Exception as e:
            logger.error(f"Ошибка восстановления: {e}")
            return False

    def clear_search(self):
        self._is_searching = False
        self._hide_loading_spinner()
        self.cards_container.clear()
        self.current_query = ""
        self._all_songs = []
        self._all_chords = []
        self._all_terms = []
        self._state_restored = False
        self.search_bar.clear()
        search_state.invalidate()
        self._update_tabs_buttons()

        # Принудительно скрываем пагинацию и лейбл
        self._pagination_container.height = 0
        self._pagination_container.opacity = 0
        self._pagination_container.disabled = True
        self._result_label.opacity = 0
        self._pagination_bar.set_total(0, self._page_size, 0)

    def perform_search(self, query):
        query = query.strip()
        self.current_query = query
        self._state_restored = False
        if not query:
            self.clear_search()
            return
        if self._is_searching: return

        self._is_searching = True
        self.cards_container.clear()
        self._pagination_container.height = 0
        self._result_label.opacity = 0
        self._show_loading_spinner()

        if self._search_thread and self._search_thread.is_alive():
            self._search_thread = None
        self._search_thread = Thread(target=self._search_worker, args=(query,), daemon=True)
        self._search_thread.start()

    def _search_worker(self, query):
        try:
            chords = self._search_chords(query)
            songs = self._search_songs(query)
            terms = self._search_terms(query)
            Clock.schedule_once(lambda dt: self._on_search_complete(songs, chords, terms), 0)
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            Clock.schedule_once(lambda dt: self.clear_search(), 0)

    def _search_chords(self, query):
        try:
            import urllib.parse
            from api.client import api
            from config.app_config import config
            q_enc = urllib.parse.quote(query, safe="")
            url = f"{config.API_BASE_URL}/chords/search?query={q_enc}"
            res = api._request_sync(url, method="GET", include_auth=False)
            if isinstance(res, dict):
                return res.get('results', [])
        except Exception:
            pass
        return []

    def _search_songs(self, query):
        if len(query) < 2: return []
        try:
            res = api.search_songs_sync(query, limit=50)
            if isinstance(res, dict): return res.get('results', [])
        except Exception:
            pass
        return []

    def _search_terms(self, query):
        if len(query) < 2: return []
        try:
            user_lang = settings_manager.language
            lang = 'ru' if user_lang == 'ru' else 'en'
            res = api.search_terms_sync(query, lang=lang, limit=50)
            if isinstance(res, dict): return res.get('results', [])
        except Exception:
            pass
        return []

    def _on_search_complete(self, songs, chords, terms):
        self._is_searching = False
        self._hide_loading_spinner()
        self._all_songs = songs
        self._all_chords = chords
        self._all_terms = terms

        if self._all_songs:
            self._active_tab = 'songs'
        elif self._all_chords:
            self._active_tab = 'chords'
        elif self._all_terms:
            self._active_tab = 'terms'

        self._page = 0
        self._update_tabs_buttons()
        self._display_results()
        self.save_current_state()

    def on_result_selected(self, result_type, chord_name, song_id, term_id):
        if result_type == "chord" and chord_name:
            self.select_chord(chord_name)
        elif result_type == "song" and song_id:
            self.select_song(song_id)
        elif result_type == "term" and term_id:
            self.select_term(term_id)

    def select_chord(self, chord_name):
        self.save_current_state()
        screen_state.set_previous_screen('search')
        screen_state.set_pending_chord(chord_name)
        if self.manager and self.manager.has_screen('chord_detail'):
            self.manager.current = 'chord_detail'

    def select_song(self, song_id):
        self.save_current_state()
        artist, title = "", ""
        for child in self.cards_container.cards:
            if hasattr(child, 'song_id') and child.song_id == song_id:
                artist = getattr(child, 'title', '')
                title = getattr(child, 'subtitle', '')
                break
        screen_state.set_previous_screen('search')
        if self.manager and self.manager.has_screen('search_screen_detail'):
            scr = self.manager.get_screen('search_screen_detail')
            scr.set_song(song_id, artist, title)
            self.manager.current = 'search_screen_detail'

    def select_term(self, term_id):
        self.save_current_state()
        screen_state.set_previous_screen('search')
        if self.manager and self.manager.has_screen('search_term_detail'):
            scr = self.manager.get_screen('search_term_detail')
            scr.set_term(term_id, previous_screen='search')
            self.manager.current = 'search_term_detail'

    def go_back(self, instance=None):
        self.save_current_state()
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'