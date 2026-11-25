# screens/dictionary/base_term_detail_screen.py
"""
Базовый эталонный экран определения термина.
Используется для наследования в:
  - TermDetailScreen (screens/term_detail_screen.py)
  - SearchTermDetailScreen (screens/search_term_detail_screen.py)
"""
import math
from io import BytesIO
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.utils import platform
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image as KivyImage

from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard, MDSeparator
from songs_utils.fader_widget import SongsPanelFader
from kivymd.uix.scrollview import MDScrollView
from kivymd.app import MDApp

from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.navigation_config import navigate_back
from screens.base_screen import BaseScreen
from state.settings_state import settings_state as settings_manager
from state.base_term_detail_state import term_detail_state
from utils.localization import get_text
from api.client import api
from utils.notifications import notify
from screens.components.loading_spinner import LoadingSpinner

logger = screen_logger('BaseTermDetail')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None

ASSET_OK_PNG = "ok_png"
_OK_TEXTURE = None


def _get_ok_texture():
    global _OK_TEXTURE
    if _OK_TEXTURE is not None:
        return _OK_TEXTURE
    if HAS_ASSETS:
        try:
            img_bytes = load_asset_as_bytes(ASSET_OK_PNG)
            if img_bytes:
                _OK_TEXTURE = CoreImage(BytesIO(img_bytes), ext="png").texture
        except Exception as e:
            logger.error(f"Ошибка загрузки {ASSET_OK_PNG}: {e}")
    return _OK_TEXTURE


class TermDetailColors:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        return [0.46, 0.70, 0.71, 1]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 0.95]
        return [1, 1, 1, 0.95]

    @staticmethod
    def get_panel_bg(theme_id):
        if theme_id == 'light':
            return [0.95, 0.95, 0.95, 1]
        elif theme_id == 'dark':
            return [0.13, 0.13, 0.13, 1]
        return [0.05, 0.17, 0.11, 1]

    @staticmethod
    def get_panel_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        return [0.46, 0.70, 0.71, 0.4]

    @staticmethod
    def get_divider(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.6]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.6]
        return [0.46, 0.70, 0.71, 0.55]


class FastPanelIcon(AnchorLayout):
    def __init__(self, icon, on_click=None, asset_name=None, **kwargs):
        kwargs.setdefault('size_hint', (1, 1))
        super().__init__(**kwargs)
        self.anchor_x = 'center'
        self.anchor_y = 'center'
        self.on_click_callback = on_click
        self.is_image = False
        self._touch_down_pos = None

        tex = _get_ok_texture() if asset_name == ASSET_OK_PNG else None
        if tex is not None:
            self.is_image = True
            self.icon_widget = KivyImage(
                texture=tex,
                size_hint=(None, None),
                size=(dp(28), dp(28)),
                color=[1, 1, 1, 1],
                allow_stretch=True,
                keep_ratio=True
            )
        else:
            self.icon_widget = MDIcon(
                icon=icon,
                size_hint=(None, None),
                size=(dp(26), dp(26)),
                font_size=sp(26),
                theme_text_color="Custom",
                text_color=[0.25, 0.78, 0.55, 1]
            )
        self.add_widget(self.icon_widget)

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return False
        self._touch_down_pos = touch.pos
        touch.grab(self)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        start_pos = self._touch_down_pos
        self._touch_down_pos = None
        if start_pos and self.collide_point(*touch.pos):
            if abs(touch.x - start_pos[0]) < dp(12) and abs(touch.y - start_pos[1]) < dp(12):
                if self.on_click_callback:
                    self.on_click_callback()
        return True


class TermFontPanel(MDCard):
    """Выезжающая справа панель со шкалой масштаба текста и галочкой подтверждения."""
    PANEL_WIDTH = dp(55)
    FIXED_HEIGHT = dp(280)

    def __init__(self, parent_screen=None, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen
        theme_id = settings_manager.theme

        self.size_hint = (None, None)
        self.width = self.PANEL_WIDTH
        self.height = self.FIXED_HEIGHT
        self.md_bg_color = [0, 0, 0, 0]
        self.radius = [0, 0, 0, 0]
        self.elevation = 0
        self.padding = [0, 0, 0, 0]

        with self.canvas.before:
            self.bg_color_inst = Color(*TermDetailColors.get_panel_bg(theme_id))
            self.bg_rect = RoundedRectangle(
                pos=(self.x, self.y),
                size=(self.PANEL_WIDTH, self.height),
                radius=[dp(16), 0, 0, dp(16)]
            )
        with self.canvas.after:
            self.line_color_inst = Color(*TermDetailColors.get_panel_line(theme_id))
            self.outline_line = Line(points=[], width=1.5, cap='round', joint='round')

        self.bind(pos=self._update_bg, size=self._update_bg)

        self._visible_x = None
        self._hidden_x = None
        self.is_open = False
        self._anim = None

        self._build_ui()
        Clock.schedule_once(lambda dt: self._init_position(), 0.2)

    def _build_open_border_points(self):
        x, y = self.x, self.y
        w, h = self.PANEL_WIDTH, self.height
        r = min(dp(16), w / 2, h / 2)
        segments = 12
        pts = [x + w, y + h, x + r, y + h]
        for i in range(1, segments + 1):
            a = math.pi / 2 + (math.pi / 2) * (i / segments)
            pts.extend([x + r + r * math.cos(a), y + h - r + r * math.sin(a)])
        pts.extend([x, y + r])
        for i in range(1, segments + 1):
            a = math.pi + (math.pi / 2) * (i / segments)
            pts.extend([x + r + r * math.cos(a), y + r + r * math.sin(a)])
        pts.extend([x + w, y])
        return pts

    def _update_bg(self, *args):
        self.bg_rect.pos = (self.x, self.y)
        self.bg_rect.size = (self.PANEL_WIDTH, self.height)
        self.outline_line.points = self._build_open_border_points()

    def _init_position(self):
        self._hidden_x = Window.width + dp(4)
        self._visible_x = Window.width - self.PANEL_WIDTH
        self.x = self._hidden_x
        top_offset = layout_config.get_top_padding(include_top_nav=True)
        nav_bottom = layout_config.get_bottom_nav_total_height()
        work_h = Window.height - top_offset - nav_bottom
        self.y = nav_bottom + (work_h - self.height) / 2
        self.is_open = False

    def toggle(self):
        if self.is_open:
            self.hide()
        else:
            self.show()

    def show(self):
        if self._hidden_x is None:
            self._init_position()
        self._sync_value()
        if self.is_open:
            return
        self.is_open = True
        if self._anim:
            self._anim.cancel(self)
        self._anim = Animation(x=self._visible_x, duration=0.22, t='out_quad')
        self._anim.start(self)

    def hide(self):
        if not self.is_open:
            return
        self.is_open = False
        if self._anim:
            self._anim.cancel(self)
        self._anim = Animation(x=self._hidden_x, duration=0.22, t='in_quad')
        self._anim.start(self)

    def _build_ui(self):
        parent = self.parent_screen
        theme_id = settings_manager.theme
        accent = TermDetailColors.get_accent(theme_id)

        content = MDBoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            width=self.PANEL_WIDTH,
            height=self.FIXED_HEIGHT,
            pos_hint={'right': 1, 'center_y': 0.5},
            spacing=0,
            padding=[0, dp(8), 0, dp(8)]
        )

        header_box = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(26),
            padding=[0, dp(2), 0, 0]
        )
        self.val_label = MDLabel(
            text="1x",
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=accent,
            bold=True,
            size_hint=(1, 1),
            font_size=sp(15)
        )
        header_box.add_widget(self.val_label)
        content.add_widget(header_box)

        slider_wrap = AnchorLayout(
            anchor_x='center',
            anchor_y='center',
            size_hint=(1, 1),
            padding=[0, dp(4), 0, dp(4)]
        )

        std_size = getattr(parent, 'STANDARD_FONT_SIZE', 42 if platform == 'android' else 20)
        self._font_multipliers = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6]
        self._font_sizes = [int(round(std_size * m)) for m in self._font_multipliers]
        total_steps = len(self._font_sizes) - 1

        self.font_slider = SongsPanelFader(
            min_value=0, max_value=total_steps, value=3, step=1,
            size_hint=(None, 1), width=dp(46),
        )
        self._style_slider(self.font_slider, accent)

        def on_font_change(instance, value):
            int_val = max(0, min(total_steps, int(round(value))))
            if self.font_slider.value != int_val:
                self.font_slider.value = int_val
            new_size = self._font_sizes[int_val]
            mult = self._font_multipliers[int_val]
            self.val_label.text = f"{int(mult)}x" if mult == int(mult) else f"{mult:.1f}x"
            if parent and getattr(parent, 'current_font_size', 0) != new_size:
                parent.apply_font_size(new_size)

        self.font_slider.bind(value=on_font_change)
        slider_wrap.add_widget(self.font_slider)
        content.add_widget(slider_wrap)

        div = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(1.2),
            padding=[dp(8), 0, dp(8), 0]
        )
        self.divider = MDSeparator(color=TermDetailColors.get_divider(theme_id))
        div.add_widget(self.divider)
        content.add_widget(div)

        menu_slot_height = (self.FIXED_HEIGHT - dp(16) - dp(1.2) * 4) / 5
        back_btn = FastPanelIcon(
            icon="check",
            on_click=self.hide,
            asset_name=ASSET_OK_PNG,
            size_hint=(1, None),
            height=menu_slot_height
        )
        content.add_widget(back_btn)

        self.add_widget(content)

    def _style_slider(self, slider, accent):
        slider.accent_color = accent

    def _sync_value(self):
        if not self.parent_screen:
            return
        curr_size = getattr(self.parent_screen, 'current_font_size', self._font_sizes[3])
        idx = min(range(len(self._font_sizes)), key=lambda i: abs(self._font_sizes[i] - curr_size))
        self.font_slider.value = idx
        mult = self._font_multipliers[idx]
        self.val_label.text = f"{int(mult)}x" if mult == int(mult) else f"{mult:.1f}x"


    def update_theme_colors(self):
        theme_id = settings_manager.theme
        accent = TermDetailColors.get_accent(theme_id)
        self.bg_color_inst.rgba = TermDetailColors.get_panel_bg(theme_id)
        self.line_color_inst.rgba = TermDetailColors.get_panel_line(theme_id)
        self.divider.color = TermDetailColors.get_divider(theme_id)
        self.val_label.text_color = accent
        self._style_slider(self.font_slider, accent)


class BaseTermDetailScreen(BaseScreen):
    SCREEN_NAME = 'base_term_detail'
    DEFAULT_PREVIOUS_SCREEN = 'dictionary'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self.SCREEN_NAME
        self._manage_padding_manually = True
        self.bg_color_inst = None
        self.bg_rect = None
        self.texture = None
        self.term_id = None
        self.term_name = None
        self.previous_screen = self.DEFAULT_PREVIOUS_SCREEN
        self.is_loading = False
        self.loading_spinner = None
        self.STANDARD_FONT_SIZE = 42 if platform == 'android' else 20
        self.current_font_size = self.STANDARD_FONT_SIZE
        self._floating_panel = None
        self.load_background()
        self.init_ui()
        logger.info(f'Экран {self.__class__.__name__} создан')

    def load_background(self):
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        try:
            if HAS_ASSETS:
                for name in ["background_jpg", "background", "bg", "BACKGROUND_JPG"]:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        self.texture = CoreImage(BytesIO(bg_data), ext="jpg").texture
                        break
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
        text_p = TermDetailColors.get_text_primary(theme_id)
        div_color = TermDetailColors.get_divider(theme_id)
        if hasattr(self, 'content_label'):
            self.content_label.text_color = text_p
        if hasattr(self, 'term_title_label'):
            self.term_title_label.text_color = text_p
        for div in (getattr(self, 'top_divider', None), getattr(self, 'bottom_divider', None)):
            if div:
                div.md_bg_color = div_color
        if self._floating_panel:
            self._floating_panel.update_theme_colors()

    def update_language(self):
        self._update_top_nav()

    def init_ui(self):
        main_container = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
        top_padding_for_nav = layout_config.get_top_nav_height()
        bottom_padding_for_card = layout_config.get_bottom_nav_total_height()

        card_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, top_padding_for_nav, 0, 0]
        )

        self.term_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[0, 0, 0, bottom_padding_for_card],
            spacing=0,
            radius=[0, 0, 0, 0],
            md_bg_color=[0, 0, 0, 0],
            elevation=0
        )

        self.top_divider = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(2))
        self.term_card.add_widget(self.top_divider)

        self.content_scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=3,
            bar_color=[0.5, 0.5, 0.5, 0.3],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.1]
        )

        self._text_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(6),
            padding=[dp(16), dp(12), dp(16), dp(8)],
            adaptive_height=True,
            md_bg_color=[0, 0, 0, 0]
        )

        self.term_title_label = MDLabel(
            text="",
            font_size=self.current_font_size + dp(6),
            size_hint_y=None,
            height=dp(46),
            theme_text_color="Custom",
            bold=True,
            valign="middle",
            halign="center",
            shorten=False
        )
        self.term_title_label.bind(
            width=lambda inst, w: setattr(inst, 'text_size', (w, None))
        )
        self._text_container.add_widget(self.term_title_label)

        self.content_label = MDLabel(
            text="",
            font_size=self.current_font_size,
            size_hint_y=None,
            theme_text_color="Custom",
            valign="top",
            halign="left",
            line_height=1.6
        )
        self.content_label.bind(
            width=lambda inst, w: setattr(inst, 'text_size', (w, None)),
            texture_size=self._update_content_height
        )
        self._text_container.add_widget(self.content_label)

        self.content_scroll.add_widget(self._text_container)
        self.term_card.add_widget(self.content_scroll)

        self.bottom_divider = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(2))
        self.term_card.add_widget(self.bottom_divider)

        card_container.add_widget(self.term_card)
        main_container.add_widget(card_container)
        self.add_widget(main_container)

        self._floating_panel = TermFontPanel(parent_screen=self)
        self.add_widget(self._floating_panel)
        Clock.schedule_once(lambda dt: self.update_theme_colors(), 0.1)

    def toggle_settings_panel(self):
        if self._floating_panel:
            self._floating_panel.toggle()

    def toggle_actions_panel(self):
        self.toggle_settings_panel()

    def _update_content_height(self, *args):
        if not self.content_label.texture:
            Clock.schedule_once(lambda dt: self._update_content_height(), 0.05)
            return
        text_height = self.content_label.texture_size[1]
        title_height = self.term_title_label.texture_size[1] if self.term_title_label.text else dp(20)
        self.content_label.height = max(dp(50), text_height + dp(8))
        self.term_title_label.height = max(dp(40), title_height + dp(8))
        total_height = self.term_title_label.height + self.content_label.height + dp(20)
        if self._text_container:
            self._text_container.height = total_height
            self._text_container.minimum_height = total_height

    def prepare_clean_screen(self, term_id, term_name="", previous_screen=None):
        """Мгновенно очищает старый термин до начала анимации перехода на экран."""
        self.term_id = term_id
        self.term_name = term_name
        self.previous_screen = previous_screen or self.DEFAULT_PREVIOUS_SCREEN
        self.current_font_size = self.STANDARD_FONT_SIZE
        if hasattr(self, 'term_title_label'):
            self.term_title_label.text = ""
            self.term_title_label.font_size = self.current_font_size + dp(6)
        if hasattr(self, 'content_label'):
            self.content_label.text = ""
            self.content_label.font_size = self.current_font_size
            self.content_label.height = dp(50)
        if hasattr(self, 'content_scroll'):
            self.content_scroll.scroll_y = 1.0
        if self._floating_panel:
            self._floating_panel.hide()
        self._update_top_nav()
        self.show_loading()

    def set_term(self, term_id, previous_screen=None):
        self.term_id = term_id
        self.previous_screen = previous_screen or self.DEFAULT_PREVIOUS_SCREEN
        self.load_term_data()

    def load_term_data(self):
        saved = term_detail_state.get_term_state(self.term_id)
        if saved and saved.get('description') is not None:
            self.term_name = saved.get('name', get_text('term_not_found'))
            description = saved.get('description', '')
            saved_font = saved.get('font_size', self.STANDARD_FONT_SIZE)
            self.apply_font_size(saved_font)
            self.term_title_label.text = self.term_name.capitalize() if self.term_name else get_text('dictionary')
            self.content_label.text = description
            self._update_content_height()
            self._update_top_nav()
            self.hide_loading()
            saved_scroll = saved.get('scroll_y', 1.0)
            Clock.schedule_once(lambda dt: setattr(self.content_scroll, 'scroll_y', saved_scroll), 0.05)
            return
        self.show_loading()
        api.get_term(
            term_id=self.term_id,
            on_success=self.on_term_loaded,
            on_failure=self.on_load_failed
        )

    def apply_font_size(self, new_size):
        """Изменяет размер шрифта заголовка и описания термина с пересчётом высоты."""
        self.current_font_size = new_size
        if hasattr(self, 'term_title_label') and self.term_title_label:
            self.term_title_label.font_size = new_size + dp(6)
        if hasattr(self, 'content_label') and self.content_label:
            self.content_label.font_size = new_size
        self._update_content_height()

    def show_loading(self):
        if self.is_loading:
            return
        self.is_loading = True
        spinner = LoadingSpinner(text=get_text('loading', 'Загрузка'))
        spinner.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.loading_spinner = spinner
        self.add_widget(spinner)
        spinner.start_animation()

    def hide_loading(self):
        self.is_loading = False
        if self.loading_spinner:
            if hasattr(self.loading_spinner, 'stop_animation'):
                self.loading_spinner.stop_animation()
            if self.loading_spinner.parent:
                self.remove_widget(self.loading_spinner)
            self.loading_spinner = None

    def on_term_loaded(self, data):
        self.term_name = data.get('name', get_text('term_not_found'))
        description = data.get('description', '')
        self.term_title_label.text = self.term_name.capitalize() if self.term_name else get_text('dictionary')
        self.content_label.text = description
        self._update_content_height()
        self._update_top_nav()
        self.hide_loading()
        Clock.schedule_once(self._scroll_to_top, 0.1)
        Clock.schedule_once(self._scroll_to_top, 0.3)

    def on_load_failed(self, req, error):
        self.hide_loading()
        self.content_label.text = get_text('loading_error')
        notify.error(get_text('loading_error'))

    def _scroll_to_top(self, dt):
        if hasattr(self, 'content_scroll'):
            self.content_scroll.scroll_y = 1.0

    def _update_top_nav(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            title = self.term_name.capitalize() if self.term_name else get_text('dictionary', 'Словарь')
            app.top_nav.set_custom_title(title)

    def _save_current_term_state(self):
        if not self.term_id or not self.content_label.text:
            return
        term_detail_state.save_term_state(self.term_id, {
            'name': self.term_name,
            'description': self.content_label.text,
            'font_size': self.current_font_size,
            'scroll_y': self.content_scroll.scroll_y if self.content_scroll else 1.0,
        })

    def go_back(self, instance=None):
        navigate_back(self.manager, self.SCREEN_NAME)

    def on_enter(self):
        super().on_enter()
        self._update_top_nav()
        self.update_theme_colors()
        if self._floating_panel:
            def _init_p(dt):
                self._floating_panel._init_position()
                self._floating_panel.hide()
            Clock.schedule_once(_init_p, 0.1)

    def on_leave(self):
        self.hide_loading()
        self._save_current_term_state()
        if self._floating_panel:
            self._floating_panel.hide()