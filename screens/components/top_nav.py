# screens/components/top_nav.py
"""
Верхняя панель навигации в едином студийном стиле с BottomNav:
- 3 тем (green, dark, light)
- Металлическая нижняя планка разделения (как верхняя планка у BottomNav)
- Металлизированные иконки с неоновой подсветкой при нажатии
- Цвета заголовков и значков синхронизированы с BottomNav
"""
import base64
import io
from io import BytesIO

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image as KivyImage
from kivy.utils import platform
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from config.logger_config import screen_logger
from config.navigation_config import ROOT_SCREENS, navigate_back
from config.system_bars import get_status_bar_height
from config.top_nav_config import top_nav_config
from data.top_nav import top_nav_assets
from state.settings_state import settings_state as settings_manager
from top_nav_utils.top_nav_item_widget import StudioTopNavButton
from utils.localization import get_text

logger = screen_logger('TopNav')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


SONG_DETAIL_SCREENS = (
    'favorite_detail',
    'song_detail',
    'search_detail',
    'search_screen_detail',
)


class TopNavColors:
    @staticmethod
    def get_text_color(theme_id):
        """Цвет текста заголовка в тон металлизированным значкам для каждой темы."""
        if theme_id == 'light':
            return [0.18, 0.22, 0.20, 1.0]  # Тёмный полированный титан (в тон значкам светлой темы)
        return [0.86, 0.90, 0.92, 1.0]

    @staticmethod
    def get_favorite_active_color(theme_id):
        if theme_id == 'light':
            return [0.90, 0.68, 0.0, 1.0]
        elif theme_id == 'dark':
            return [1.0, 0.85, 0.0, 1.0]
        return [1.0, 0.88, 0.10, 1.0]


class ClickableLogo(ButtonBehavior, KivyImage):
    pass


class TopNav(MDCard):
    _bot_bar_dark_tex = None
    _bot_bar_light_tex = None

    def __init__(self, screen_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.sm = screen_manager
        self.current_screen_name = None

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.pos_hint = {'top': 1}
        self.elevation = 0
        self.radius = [0, 0, 0, 0]
        self.padding = [0, 0, 0, 0]
        self.spacing = 0
        self.md_bg_color = [0, 0, 0, 0]

        if TopNav._bot_bar_dark_tex is None:
            TopNav._bot_bar_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(top_nav_assets.BOT_BAR_DARK_B64)), ext="png"
            ).texture
            TopNav._bot_bar_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(top_nav_assets.BOT_BAR_LIGHT_B64)), ext="png"
            ).texture

        status_h = get_status_bar_height()
        if platform == 'android':
            self.height = status_h + dp(52)
        else:
            self.height = dp(64)

        self.bar_height = dp(5)

        with self.canvas.before:
            # 1. Фон панели (1-в-1 как в BottomNav)
            self.bg_color_inst = Color(0.0, 0.05, 0.03, 0.26)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        with self.canvas.after:
            # 2. Металлическая нижняя планка разделения (зеркально верхней планке BottomNav)
            self.bot_bar_color = Color(1, 1, 1, 1)
            self.bot_bar_rect = Rectangle(
                texture=self._bot_bar_dark_tex,
                pos=(self.x, self.y),
                size=(self.width, self.bar_height),
            )

        self.bind(pos=self._update_bottom_line, size=self._update_bottom_line)

        self.logo_texture = None
        self.load_logo_texture()

        self.current_song_id = None
        self.is_favorite = False
        self.custom_title_widget = None
        self._custom_back_callback = None

        self.build_ui()
        self.update_theme_colors()

        if self.sm:
            if hasattr(self.sm, 'add_observer'):
                self.sm.add_observer(self._on_screen_changed)
            elif hasattr(self.sm, 'bind'):
                self.sm.bind(current=self._on_screen_changed)
            self.set_screen(self.sm.current or 'home')
        else:
            self.set_screen('home')

        Window.bind(on_resize=self._on_window_resize)
        logger.info("✅ TopNav создан (в едином студийном стиле с BottomNav)")

    def _update_bottom_line(self, *args):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size
        if hasattr(self, 'bot_bar_rect'):
            self.bot_bar_rect.pos = (self.x, self.y)
            self.bot_bar_rect.size = (self.width, self.bar_height)

    def set_app(self, app):
        self.app = app

    def update_title(self, screen_name: str):
        self.set_screen(screen_name)

    def set_back_button(self, callback):
        self._custom_back_callback = callback
        if self.back_btn:
            self.back_btn.on_release = callback

    def clear_back_button(self):
        self._custom_back_callback = None
        if self.back_btn:
            self.back_btn.on_release = self._on_back_click

    def set_custom_back_callback(self, callback):
        self.set_back_button(callback)

    def clear_custom_back_callback(self):
        self.clear_back_button()

    def _on_window_resize(self, instance, width, height):
        if self.screen_title and self.screen_title in self.container.children:
            self._adjust_title_width()

    def force_update_title(self, title_text: str, show_back: bool = False):
        if self.logo_widget in self.container.children:
            self.container.remove_widget(self.logo_widget)
        self.restore_default_title()
        self.screen_title.text = title_text
        self._adjust_title_width()

        if self.back_btn in self.container.children:
            self.container.remove_widget(self.back_btn)
        if self.settings_btn in self.container.children:
            self.container.remove_widget(self.settings_btn)

        if show_back:
            self.container.add_widget(self.back_btn)
        else:
            self.container.add_widget(self.settings_btn)

    def load_logo_texture(self):
        if not HAS_ASSETS:
            logger.warning("⚠️ Модуль data недоступен, логотип будет текстовым")
            return
        try:
            logo_bytes = load_asset_as_bytes("logo_png")
            if logo_bytes:
                self.logo_texture = CoreImage(BytesIO(logo_bytes), ext="png").texture
                logger.info("✅ Текстура logo_png загружена")
            else:
                logger.warning("⚠️ Ассет logo_png не найден")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки logo_png: {e}")

    def build_ui(self):
        self.container = FloatLayout(size_hint=(1, 1))
        self.container.bind(pos=self._reposition_container_children, size=self._reposition_container_children)

        self.settings_btn = StudioTopNavButton(
            icon="tune",
            pos_hint={'x': 0.015, 'center_y': 0.52},
            on_release=self._on_settings_click,
        )

        self.back_btn = StudioTopNavButton(
            icon="arrow-left",
            pos_hint={'x': 0.015, 'center_y': 0.52},
            on_release=self._on_back_click,
        )

        if self.logo_texture:
            self.logo_widget = ClickableLogo(
                texture=self.logo_texture,
                size_hint=(None, None),
                size=(dp(260), dp(50)),
                allow_stretch=True,
                keep_ratio=True,
                pos_hint={'center_x': 0.5, 'center_y': 0.52},
                on_release=self._on_logo_click,
            )
        else:
            fallback_title = get_text('home')
            if fallback_title == 'home':
                fallback_title = "GuitarFuns"
            self.logo_widget = MDLabel(
                text=fallback_title,
                font_size=sp(20),
                bold=True,
                halign="center",
                valign="middle",
                size_hint=(None, None),
                size=(dp(240), dp(48)),
                pos_hint={'center_x': 0.5, 'center_y': 0.52},
                theme_text_color="Custom",
            )

        self.screen_title = MDLabel(
            text="",
            font_size=sp(20),
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(None, None),
            height=dp(48),
            pos_hint={'center_x': 0.5, 'center_y': 0.52},
            theme_text_color="Custom",
            shorten=True,
            shorten_from='right',
            max_lines=1,
        )
        self.screen_title.bind(size=self._update_title_text_size)

        self.right_container = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            height=dp(46),
            spacing=dp(4),
            pos_hint={'right': 0.985, 'center_y': 0.52},
        )
        self.right_container.bind(minimum_width=self.right_container.setter('width'))

        self.search_btn = StudioTopNavButton(
            icon="magnify",
            on_release=self._on_search_click,
        )

        self.home_btn = StudioTopNavButton(
            icon="home",
            on_release=self._on_home_click,
        )

        self.favorite_btn = StudioTopNavButton(
            icon="star-outline",
            on_release=self._on_favorite_click,
        )

        self.actions_btn = StudioTopNavButton(
            icon="cog",
            on_release=self._on_actions_click,
        )

        self.container.add_widget(self.right_container)
        self.container.bind(
            pos=self._reposition_container_children,
            size=self._reposition_container_children,
        )
        self.add_widget(self.container)

    def _reposition_container_children(self, *args):
        if not hasattr(self, 'container'):
            return
        cy = self.container.y + self.container.height * 0.52
        lx = self.container.x + self.container.width * 0.015
        for btn in (self.settings_btn, self.back_btn):
            if btn:
                btn.x = lx
                btn.center_y = cy
        if self.right_container:
            self.right_container.right = self.container.x + self.container.width * 0.985
            self.right_container.center_y = cy
        for title_w in (self.logo_widget, self.screen_title, self.custom_title_widget):
            if title_w and title_w in self.container.children:
                title_w.center_x = self.container.center_x
                title_w.center_y = cy


    def _update_title_text_size(self, instance, value):
        instance.text_size = (instance.width, None)

    def _get_screen_title(self, screen_name: str) -> str:
        if screen_name in ('term_detail', 'search_term_detail'):
            return get_text('dictionary', 'Словарь')
        if screen_name not in top_nav_config.SCREENS:
            return get_text(screen_name, screen_name)
        return get_text(screen_name, top_nav_config.get_title(screen_name))

    def _adjust_title_width(self):
        text = self.screen_title.text
        if not text:
            return

        window_width = Window.width
        left_width = dp(48)
        right_width = dp(48)
        padding = dp(32)

        current = self.sm.current if self.sm else 'home'
        if current in SONG_DETAIL_SCREENS or current in ('term_detail', 'search_term_detail'):
            right_width = dp(96)

        max_width = window_width - left_width - right_width - padding
        if max_width < dp(100):
            max_width = dp(100)

        char_width = sp(12)
        text_width = len(text) * char_width + dp(16)
        text_width = max(dp(80), min(text_width, max_width))
        self.screen_title.width = text_width

    def set_custom_title_widget(self, widget):
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        if self.screen_title in self.container.children:
            self.container.remove_widget(self.screen_title)

        if self.logo_widget in self.container.children:
            self.container.remove_widget(self.logo_widget)

        widget.size_hint = (None, None)

        window_width = Window.width
        left_width = dp(48)
        right_width = dp(48)
        padding = dp(32)

        current = self.sm.current if self.sm else 'home'
        if current in SONG_DETAIL_SCREENS or current in ('term_detail', 'search_term_detail'):
            right_width = dp(96)

        max_width = max(dp(100), window_width - left_width - right_width - padding)
        widget.width = max_width
        widget.height = dp(48)
        widget.pos_hint = {'center_x': 0.5, 'center_y': 0.52}

        if hasattr(widget, 'padding'):
            widget.padding = [dp(8), dp(4), dp(8), dp(4)]

        self.container.add_widget(widget)
        self.custom_title_widget = widget

    def restore_default_title(self):
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        if self.screen_title not in self.container.children:
            self.container.add_widget(self.screen_title)
        self._adjust_title_width()

    def clear_custom_title_widget(self):
        self.restore_default_title()

    def _on_screen_changed(self, instance, screen_name):
        self.current_screen_name = screen_name
        self.set_screen(screen_name)

    def _update_left_button(self, screen_name: str):
        if self.back_btn in self.container.children:
            self.container.remove_widget(self.back_btn)
        if self.settings_btn in self.container.children:
            self.container.remove_widget(self.settings_btn)

        self._custom_back_callback = None

        if screen_name in ROOT_SCREENS:
            self.container.add_widget(self.settings_btn)
        else:
            self.container.add_widget(self.back_btn)
        self._reposition_container_children()

    def set_screen(self, screen_name: str):
        logger.debug(f"🔄 TopNav переключён на экран: {screen_name}")

        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        if screen_name == 'home':
            if self.screen_title in self.container.children:
                self.container.remove_widget(self.screen_title)
            if self.logo_widget not in self.container.children:
                self.container.add_widget(self.logo_widget)
        else:
            if self.logo_widget in self.container.children:
                self.container.remove_widget(self.logo_widget)
            if self.screen_title not in self.container.children:
                self.container.add_widget(self.screen_title)
            self.screen_title.text = self._get_screen_title(screen_name)
            self._adjust_title_width()

        Clock.schedule_once(lambda dt, s=screen_name: self._apply_nav_buttons(s), 0)
        self.update_theme_colors()

    def _apply_nav_buttons(self, screen_name: str):
        self._update_left_button(screen_name)
        self._update_right_buttons(screen_name)

    def _update_right_buttons(self, screen_name: str):
        self.right_container.clear_widgets()

        if screen_name in SONG_DETAIL_SCREENS:
            self._update_favorite_icon()
            self.right_container.add_widget(self.favorite_btn)
            self.right_container.add_widget(self.actions_btn)
            return

        if screen_name in ('term_detail', 'search_term_detail'):
            self.right_container.add_widget(self.home_btn)
            self.right_container.add_widget(self.actions_btn)
            return

        nav_screens_with_home = ['songs', 'chords', 'tuner', 'metronome', 'favorites', 'dictionary']
        if screen_name in nav_screens_with_home:
            self.right_container.add_widget(self.home_btn)
        else:
            right_type = top_nav_config.get_right_button(screen_name)
            if right_type == top_nav_config.RIGHT_BUTTON_SEARCH:
                self.right_container.add_widget(self.search_btn)
            elif right_type == top_nav_config.RIGHT_BUTTON_HOME:
                self.right_container.add_widget(self.home_btn)

    def _update_favorite_icon(self):
        theme_id = settings_manager.theme
        if self.is_favorite:
            self.favorite_btn.icon = "star"
            self.favorite_btn.custom_tint = TopNavColors.get_favorite_active_color(theme_id)
        else:
            self.favorite_btn.icon = "star-outline"
            self.favorite_btn.custom_tint = []

    def update_favorite_icon(self, is_favorite: bool = None):
        """Публичный метод для обновления иконки избранного из экранов-наследников."""
        if is_favorite is not None:
            self.is_favorite = is_favorite
        self._update_favorite_icon()

    def set_song_favorite_state(self, song_id: int, is_favorite: bool):
        self.current_song_id = song_id
        self.is_favorite = is_favorite
        if self.sm and self.sm.current in SONG_DETAIL_SCREENS:
            self._update_favorite_icon()

    def set_custom_title(self, title_text: str):
        if self.logo_widget in self.container.children:
            self.container.remove_widget(self.logo_widget)
        self.restore_default_title()
        self.screen_title.text = title_text
        self._adjust_title_width()

    def _on_logo_click(self, instance):
        if self.sm and self.sm.current != 'home':
            self.sm.current = 'home'

    def _on_settings_click(self, instance):
        app = MDApp.get_running_app()
        if hasattr(app, 'sidebar') and app.sidebar:
            app.sidebar.toggle()

    def _on_back_click(self, instance=None):
        import time
        now = time.monotonic()
        if now - getattr(self, '_last_back_click_time', 0.0) < 0.35:
            return
        self._last_back_click_time = now
        if not self.sm:
            return
        current = self.sm.current
        if current in ROOT_SCREENS:
            return

        current_screen = self.sm.current_screen
        if current_screen and hasattr(current_screen, 'go_back') and callable(current_screen.go_back):
            current_screen.go_back()
            return
        navigate_back(self.sm, current)

    def _on_search_click(self, instance):
        if self.sm and self.sm.has_screen('search'):
            self.sm.current = 'search'

    def _on_home_click(self, instance):
        if self.sm:
            self.sm.current = 'home'

    def _on_favorite_click(self, instance):
        if not self.sm:
            return
        current = self.sm.current
        if current in SONG_DETAIL_SCREENS and self.sm.has_screen(current):
            screen = self.sm.get_screen(current)
            if hasattr(screen, 'toggle_favorite') and callable(screen.toggle_favorite):
                screen.toggle_favorite()
                return

        if self.current_song_id:
            if self.is_favorite:
                api.remove_favorite(
                    self.current_song_id,
                    on_success=lambda r: self._on_fav_toggled(False),
                    on_failure=lambda req, err: logger.error(f"Ошибка удаления из избранного: {err}"),
                )
            else:
                api.add_favorite(
                    self.current_song_id,
                    on_success=lambda r: self._on_fav_toggled(True),
                    on_failure=lambda req, err: logger.error(f"Ошибка добавления в избранное: {err}"),
                )

    def _on_fav_toggled(self, new_state: bool):
        self.is_favorite = new_state
        self._update_favorite_icon()

        if self.sm and self.sm.has_screen('favorites'):
            fav_screen = self.sm.get_screen('favorites')
            if hasattr(fav_screen, 'load_favorites'):
                fav_screen.load_favorites()

    def _on_actions_click(self, instance):
        if not self.sm:
            return
        current = self.sm.current
        if self.sm.has_screen(current):
            screen = self.sm.get_screen(current)
            if hasattr(screen, 'toggle_settings_panel') and callable(screen.toggle_settings_panel):
                screen.toggle_settings_panel()
            elif hasattr(screen, 'toggle_actions_panel') and callable(screen.toggle_actions_panel):
                screen.toggle_actions_panel()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        is_light = theme_id == 'light'
        self.md_bg_color = (0, 0, 0, 0)

        # Фон 1-в-1 как в BottomNav
        if is_light:
            self.bg_color_inst.rgba = (0.97, 0.99, 0.98, 0.96)
        elif theme_id == 'dark':
            self.bg_color_inst.rgba = (0.09, 0.09, 0.11, 0.96)
        else:  # green
            self.bg_color_inst.rgba = (0.0, 0.05, 0.03, 0.26)

        if hasattr(self, 'bot_bar_rect'):
            self.bot_bar_rect.texture = (
                self._bot_bar_light_tex if is_light else self._bot_bar_dark_tex
            )

        text_color = TopNavColors.get_text_color(theme_id)
        if self.screen_title:
            self.screen_title.text_color = text_color
        if not self.logo_texture and hasattr(self, 'logo_widget'):
            self.logo_widget.text_color = text_color

        for btn in (
            self.settings_btn,
            self.back_btn,
            self.search_btn,
            self.home_btn,
            self.favorite_btn,
            self.actions_btn,
        ):
            if btn:
                btn.update_theme_colors()

        if self.sm and self.sm.current in SONG_DETAIL_SCREENS:
            self._update_favorite_icon()
        elif self.favorite_btn:
            self.favorite_btn.custom_tint = []

    def update_language(self):
        if self.sm:
            current = self.sm.current
            if current != 'home':
                self.screen_title.text = self._get_screen_title(current)
                self._adjust_title_width()
            elif not self.logo_texture and hasattr(self, 'logo_widget'):
                fallback = get_text('home')
                self.logo_widget.text = "GuitarFuns" if fallback == 'home' else fallback

    def is_transparent(self):
        return False