# screens/components/top_nav.py
"""
Верхняя панель навигации - с отладочными рамками
"""
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.utils import platform

from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.app import MDApp
from config.theme import theme
from config.logger_config import get_logger
from screens.components.language_selector import LanguageSelector
from config.system_bars import get_status_bar_height_px

logger = get_logger('UI')


class TopNav(MDCard):
    """Верхняя панель навигации - с отладочными рамками"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.app = None
        self.language_selector = None
        self.current_screen_name = 'home'
        self._is_back_mode = False

        self.orientation = 'vertical'
        self.size_hint = (1, None)

        status_bar_height_px = get_status_bar_height_px()
        status_bar_height_dp = dp(status_bar_height_px)

        self.height = dp(56)
        self.padding = [0, status_bar_height_dp, 0, 0]

        self.radius = [0, 0, 0, 0]
        self.md_bg_color = [0, 0, 0, 0]  # ПРОЗРАЧНЫЙ ФОН
        self.theme_bg_color = "Custom"
        self.elevation = 0
        self.spacing = 0

        # БЕЛАЯ РАМКА ВОКРУГ ВСЕЙ ПАНЕЛИ
        self.bind(pos=self._update_panel_outline, size=self._update_panel_outline)

        self.container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]
        )

        # ============ ЛЕВАЯ ЧАСТЬ ============
        self.left_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            width=dp(88),
            height=dp(44),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        self.menu_btn = MDIconButton(
            icon="menu",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_menu_press,
            pos_hint={'center_y': 0.5}
        )

        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_back_press,
            pos_hint={'center_y': 0.5},
            opacity=0,
            disabled=True
        )

        self.left_container.add_widget(self.menu_btn)
        self.left_container.add_widget(self.back_btn)

        # КРАСНАЯ РАМКА ВОКРУГ ЛЕВОГО КОНТЕЙНЕРА
        self.left_container.bind(pos=self._update_left_outline, size=self._update_left_outline)

        # ============ ЦЕНТР ============
        self.screen_title = MDLabel(
            text=self._get_screen_title('home'),
            font_size=sp(18),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            size_hint_x=1,
            pos_hint={'center_y': 0.5}
        )

        # КРАСНАЯ РАМКА ВОКРУГ ЦЕНТРАЛЬНОГО КОНТЕЙНЕРА
        self.screen_title.bind(pos=self._update_title_outline, size=self._update_title_outline)

        # ============ ПРАВАЯ ЧАСТЬ ============
        self.right_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            width=dp(140),
            height=dp(44),
            spacing=dp(6),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search_press,
            pos_hint={'center_y': 0.5}
        )

        self.profile_btn = MDIconButton(
            icon="account-circle",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_profile_press,
            pos_hint={'center_y': 0.5}
        )

        self.language_selector = LanguageSelector(
            on_language_change=self._on_language_changed
        )

        self.right_container.add_widget(self.search_btn)
        self.right_container.add_widget(self.profile_btn)
        self.right_container.add_widget(self.language_selector)

        # КРАСНАЯ РАМКА ВОКРУГ ПРАВОГО КОНТЕЙНЕРА
        self.right_container.bind(pos=self._update_right_outline, size=self._update_right_outline)

        self.container.add_widget(self.left_container)
        self.container.add_widget(self.screen_title)
        self.container.add_widget(self.right_container)

        self.add_widget(self.container)

        if hasattr(self.sm, 'add_observer'):
            self.sm.add_observer(self._on_screen_changed)
        elif hasattr(self.sm, 'bind'):
            self.sm.bind(current=self._on_screen_changed)

        if self.sm:
            self._on_screen_changed(self.sm, self.sm.current)

        logger.info("=" * 60)
        logger.info("Верхняя панель: белая рамка вокруг панели, красные рамки вокруг контейнеров")
        logger.info(f"  - Высота панели: {self.height}dp")
        logger.info(f"  - Отступ сверху (статус-бар): {self.padding[1]}dp")
        logger.info("=" * 60)

    def _update_panel_outline(self, *args):
        """Белая рамка вокруг всей панели"""
        self.canvas.before.remove_group('topnav_panel_outline')
        with self.canvas.before:
            Color(1, 1, 1, 1)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=2, group='topnav_panel_outline')

    def _update_left_outline(self, *args):
        """Красная рамка вокруг левого контейнера"""
        self.canvas.before.remove_group('left_outline')
        with self.canvas.before:
            Color(1, 0, 0, 0.8)
            Line(rectangle=(
                self.left_container.x,
                self.left_container.y,
                self.left_container.width,
                self.left_container.height
            ), width=1, group='left_outline')

    def _update_title_outline(self, *args):
        """Красная рамка вокруг заголовка"""
        self.canvas.before.remove_group('title_outline')
        with self.canvas.before:
            Color(1, 0, 0, 0.8)
            Line(rectangle=(
                self.screen_title.x,
                self.screen_title.y,
                self.screen_title.width,
                self.screen_title.height
            ), width=1, group='title_outline')

    def _update_right_outline(self, *args):
        """Красная рамка вокруг правого контейнера"""
        self.canvas.before.remove_group('right_outline')
        with self.canvas.before:
            Color(1, 0, 0, 0.8)
            Line(rectangle=(
                self.right_container.x,
                self.right_container.y,
                self.right_container.width,
                self.right_container.height
            ), width=1, group='right_outline')

    def _get_screen_title(self, screen_name: str) -> str:
        titles = {
            'home': 'Главная',
            'songs': 'Песни',
            'chords': 'Аккорды',
            'tuner': 'Тюнер',
            'favorites': 'Избранное',
            'profile': 'Профиль',
            'artists_by_letter': 'Исполнители',
            'artist_songs': 'Песни',
            'song_detail': 'Текст песни',
            'search_results': 'Результаты поиска',
            'dictionary': 'Словарь',
            'admin': 'Админ панель',
            'search': 'Поиск'
        }
        return titles.get(screen_name, screen_name.capitalize())

    def _on_screen_changed(self, instance, screen_name):
        self.current_screen_name = screen_name

        if screen_name != 'artists_by_letter':
            self._hide_back_button()
            self.screen_title.text = self._get_screen_title(screen_name)
        else:
            self._show_back_button()

        logger.debug(f"Экран изменён: {screen_name}")

    def _on_menu_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            logger.debug("Навигация заблокирована")
            return

        if self.app and hasattr(self.app, 'open_drawer'):
            self.app.open_drawer(btn)
        else:
            logger.info("Меню нажато")

    def _on_back_press(self, btn):
        logger.info("Кнопка назад нажата")
        if self.sm:
            self.sm.current = 'songs'

    def _on_profile_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            logger.debug("Навигация заблокирована")
            return

        if self.app and hasattr(self.app, 'open_profile'):
            self.app.open_profile(btn)
        else:
            if hasattr(self, 'sm') and self.sm and self.sm.has_screen('profile'):
                self.sm.current = 'profile'

    def _on_language_changed(self, lang_code):
        if self.app and hasattr(self.app, 'change_language'):
            self.app.change_language(lang_code)

    def _on_search_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            logger.debug("Навигация заблокирована")
            return

        if self.sm:
            if self.sm.has_screen('chords') and self.sm.has_screen('search'):
                chords_screen = self.sm.get_screen('chords')
                search_screen = self.sm.get_screen('search')
                search_screen.set_chords_screen(chords_screen)
                self.sm.current = 'search'

    def set_app(self, app):
        self.app = app

    def get_current_language(self):
        if self.language_selector:
            return self.language_selector.get_current_lang()
        return 'ru'

    def set_current_language(self, lang_code):
        if self.language_selector:
            self.language_selector.set_current_lang(lang_code)

    def update_title(self, screen_name: str):
        self.screen_title.text = self._get_screen_title(screen_name)

    def update_for_artists_screen(self, letter: str, show_back_button: bool = True):
        if show_back_button:
            self._show_back_button()
        else:
            self._hide_back_button()

        display = "0-9" if letter in ("digits", "0-9") else letter.upper()
        self.screen_title.text = f"Буква {display}"
        self.screen_title.bold = True
        logger.info(f"TopNav обновлён для экрана исполнителей: {self.screen_title.text}")

    def reset_to_default(self):
        self._hide_back_button()
        self.screen_title.bold = True
        if self.sm:
            self.screen_title.text = self._get_screen_title(self.sm.current)
        logger.info("TopNav сброшен к стандартному виду")

    def _show_back_button(self):
        self._is_back_mode = True
        self.back_btn.opacity = 1
        self.back_btn.disabled = False

    def _hide_back_button(self):
        self._is_back_mode = False
        self.back_btn.opacity = 0
        self.back_btn.disabled = True

    def hide_search_button(self, hide: bool = True):
        self.search_btn.opacity = 0 if hide else 1
        self.search_btn.disabled = hide

    def hide_profile_button(self, hide: bool = True):
        self.profile_btn.opacity = 0 if hide else 1
        self.profile_btn.disabled = hide