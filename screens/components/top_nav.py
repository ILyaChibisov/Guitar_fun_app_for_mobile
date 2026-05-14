# screens/components/top_nav.py
"""
Верхняя панель навигации - увеличенный отступ для Android
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window

from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from config.system_bars import get_status_bar_height, get_screen_density
from screens.components.language_selector import LanguageSelector

logger = get_logger('TopNav')


class TopNav(MDCard):
    """Верхняя панель навигации - увеличенная"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.app = None
        self.language_selector = None
        self.current_screen_name = 'home'
        self._is_back_mode = False

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.pos_hint = {'top': 1}

        status_h = get_status_bar_height()

        # УВЕЛИЧИВАЕМ ВСЮ ВЫСОТУ ПАНЕЛИ вместо просто отступа
        if platform == 'android':
            self.height = dp(80)  # было 56, стало 80
            # Отступ сверху = статус-бар + 20dp (значительный запас)
            top_padding = status_h + dp(20)
        else:
            self.height = dp(56)
            top_padding = status_h + dp(4)

        self.padding = [0, top_padding, 0, 0]

        self.radius = [0, 0, 0, 0]
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.spacing = 0

        screen_density = get_screen_density()
        logger.info("=" * 70)
        logger.info(f"📱 TOP NAV - {platform.upper()}")
        logger.info(f"📱 Статус-бар: {status_h:.1f}dp = {status_h * screen_density:.0f}px")
        logger.info(f"📱 Отступ сверху: {top_padding:.1f}dp = {top_padding * screen_density:.0f}px")
        logger.info(f"📱 Высота панели: {self.height}dp = {self.height * screen_density:.0f}px")
        logger.info("=" * 70)

        # Основной контейнер
        self.container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]
        )

        # Левая часть
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
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_menu_press,
            pos_hint={'center_y': 0.5}
        )

        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
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

        # Центр
        self.screen_title = MDLabel(
            text=self._get_screen_title('home'),
            font_size=sp(20),  # увеличен
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            size_hint_x=1,
            size_hint_y=1,
            pos_hint={'center_y': 0.5}
        )

        # Правая часть
        self.right_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            width=dp(150),
            height=dp(44),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search_press,
            pos_hint={'center_y': 0.5}
        )

        self.profile_btn = MDIconButton(
            icon="account-circle",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
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

    def _on_menu_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return
        if self.app and hasattr(self.app, 'open_drawer'):
            self.app.open_drawer(btn)

    def _on_back_press(self, btn):
        if self.sm:
            self.sm.current = 'songs'

    def _on_profile_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
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
            return
        if self.sm and self.sm.has_screen('chords') and self.sm.has_screen('search'):
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

    def reset_to_default(self):
        self._hide_back_button()
        if self.sm:
            self.screen_title.text = self._get_screen_title(self.sm.current)

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

    def reload_config(self):
        status_h = get_status_bar_height()
        if platform == 'android':
            self.height = dp(80)
            self.padding = [0, status_h + dp(20), 0, 0]
        else:
            self.height = dp(56)
            self.padding = [0, status_h + dp(4), 0, 0]