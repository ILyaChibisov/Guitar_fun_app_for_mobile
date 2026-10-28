# screens/components/top_nav.py
"""
Верхняя панель навигации с поддержкой тем и языков.
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from config.system_bars import get_status_bar_height, get_screen_density
from config.top_nav_config import top_nav_config
from utils.screen_state import screen_state
from utils.settings_manager import settings_manager
from utils.localization import get_text  # <--- ИМПОРТ ПЕРЕВОДОВ

logger = get_logger('TopNav')


class TopNav(MDCard):
    """Верхняя панель навигации с конфигом"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.app = None
        self.current_screen_name = 'home'
        self._is_back_mode = False
        self._previous_screen = None
        self._custom_back_callback = None
        self._old_title_widget = None
        self.custom_title_widget = None

        # Флаги для управления навигацией
        self._just_returned_from_song_detail = False
        self._block_navigation = False
        self._going_back = False
        self._navigating = False

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.pos_hint = {'top': 1}

        # ============ ПРАВИЛЬНЫЙ РАСЧЁТ ВЫСОТЫ ============
        status_h = get_status_bar_height()

        if platform == 'android':
            panel_height = dp(52)
            self.height = status_h + panel_height
            top_padding = status_h
        else:
            panel_height = dp(64)
            self.height = panel_height
            top_padding = status_h + dp(4)

        # ✅ ПРОЗРАЧНЫЙ ФОН
        self.padding = [0, 0, 0, 0]
        self.radius = [0, 0, 0, 0]
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.spacing = 0

        # ============ ЗЕЛЁНАЯ ПОЛОСКА СНИЗУ ============
        with self.canvas.before:
            self.line_color_inst = Color(0.46, 0.70, 0.71, 0.4)
            self.bottom_line = Rectangle(
                pos=(self.x, self.y),
                size=(self.width, dp(1.5))
            )

        self.bind(pos=self._update_bottom_line, size=self._update_bottom_line)

        # ============ КОНТЕЙНЕР ============
        self.container = MDFloatLayout(
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )

        # Левая часть
        self.left_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(48),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'x': 0, 'center_y': 0.5}
        )

        # Кнопка настроек (шестерёнка)
        self.settings_btn = MDIconButton(
            icon="tune",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )
        self.settings_btn.bind(on_release=self._on_settings_press)

        # Кнопка назад (стрелка)
        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )
        self.back_btn.bind(on_release=self._on_back_press)

        self.left_container.add_widget(self.settings_btn)

        # ============ ЗАГОЛОВОК ============
        self.screen_title = MDLabel(
            text=get_text('home'),  # Используем перевод для стартового экрана
            font_size=sp(20),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            size_hint=(None, None),
            width=dp(250),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            shorten=True,
            shorten_from="right"
        )

        # Правая часть
        self.right_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(48),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'right': 1, 'center_y': 0.5}
        )

        self.home_btn = MDIconButton(
            icon="home",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )
        self.home_btn.bind(on_release=self._on_home_press)

        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )
        self.search_btn.bind(on_release=self._on_search_press)

        self.right_container.add_widget(self.search_btn)

        # Добавляем всё во FloatLayout
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

        # ============ ПРИМЕНЯЕМ ЦВЕТА ТЕМЫ ============
        self.update_theme_colors()

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        logger.info(f"🎨 TopNav: обновление цветов для темы {theme_id}")

        if theme_id == 'light':
            # Насыщенный яркий изумрудный для светлой темы
            color = [0.1, 0.55, 0.3, 1]  # #1A8C4C
            self.line_color_inst.rgba = [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            # БЕЛЫЙ для тёмной темы (как в зелёной)
            color = [1, 1, 1, 1]
            # Полоску снизу оставляем оранжевой для акцента
            self.line_color_inst.rgba = [1.0, 0.5, 0.0, 0.5]
        else:  # green
            color = [1, 1, 1, 1]
            self.line_color_inst.rgba = [0.46, 0.70, 0.71, 0.4]

        self.settings_btn.icon_color = color
        self.back_btn.icon_color = color
        self.home_btn.icon_color = color
        self.search_btn.icon_color = color
        self.screen_title.text_color = color

    def _update_bottom_line(self, *args):
        if hasattr(self, 'bottom_line'):
            self.bottom_line.pos = (self.x, self.y)
            self.bottom_line.size = (self.width, dp(1.5))

    def _get_screen_title(self, screen_name: str) -> str:
        """Возвращает заголовок из конфига с переводом"""
        if screen_name not in top_nav_config.SCREENS:
             return get_text(screen_name, screen_name)
        return get_text(screen_name, top_nav_config.get_title(screen_name))

    def update_title(self, screen_name: str):
        title = self._get_screen_title(screen_name)
        self.screen_title.text = title
        self._adjust_title_width()

    def set_custom_title(self, title: str):
        self.screen_title.text = title
        self._adjust_title_width()

        if title == "Избранное" or title == "Favorites":
            if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
                if self.custom_title_widget in self.container.children:
                    self.container.remove_widget(self.custom_title_widget)
                self.custom_title_widget = None

            if self.screen_title not in self.container.children:
                self.container.add_widget(self.screen_title)
                self._adjust_title_width()

    def _adjust_title_width(self):
        text = self.screen_title.text
        if not text:
            return

        window_width = Window.width
        left_width = dp(48)
        right_width = dp(48)
        padding = dp(32)
        max_width = window_width - left_width - right_width - padding

        if max_width < dp(100):
            max_width = dp(100)

        char_width = sp(12)
        text_width = len(text) * char_width + dp(16)

        if text_width > max_width:
            text_width = max_width

        if text_width < dp(80):
            text_width = dp(80)

        self.screen_title.width = text_width

    def set_custom_title_widget(self, widget):
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        if self.screen_title in self.container.children:
            self.container.remove_widget(self.screen_title)

        widget.size_hint = (None, None)

        window_width = Window.width
        left_width = dp(48)
        right_width = dp(48)
        padding = dp(32)
        max_width = window_width - left_width - right_width - padding

        if max_width < dp(100):
            max_width = dp(100)

        widget.width = max_width
        widget.height = dp(48)
        widget.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        if hasattr(widget, 'padding'):
            widget.padding = [dp(8), dp(4), dp(8), dp(4)]

        self.container.add_widget(widget)
        self.custom_title_widget = widget
        logger.info(f"✅ Установлен кастомный виджет заголовка")

    def clear_custom_title_widget(self):
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        if self.screen_title not in self.container.children:
            self.container.add_widget(self.screen_title)
            self._adjust_title_width()

    def set_custom_back_callback(self, callback):
        self._custom_back_callback = callback

    def clear_custom_back_callback(self):
        self._custom_back_callback = None

    def _update_left_button(self, screen_name: str):
        self.left_container.clear_widgets()

        nav_screens_with_hamburger = [
            'songs', 'chords', 'tuner', 'metronome', 'favorites', 'dictionary',
            'profile', 'help', 'promo', 'feedback',
            'admin'
        ]

        if screen_name in nav_screens_with_hamburger:
            self.left_container.add_widget(self.settings_btn)
        else:
            left_type = top_nav_config.get_left_button(screen_name)
            if left_type == top_nav_config.LEFT_BUTTON_BACK:
                self.left_container.add_widget(self.back_btn)
            elif left_type == top_nav_config.LEFT_BUTTON_HAMBURGER:
                self.left_container.add_widget(self.settings_btn)

    def _update_right_buttons(self, screen_name: str):
        self.right_container.clear_widgets()

        nav_screens_with_home = ['songs', 'chords', 'tuner', 'metronome', 'favorites', 'dictionary']

        if screen_name in nav_screens_with_home:
            self.right_container.add_widget(self.home_btn)
        else:
            right_type = top_nav_config.get_right_button(screen_name)
            if right_type == top_nav_config.RIGHT_BUTTON_SEARCH:
                self.right_container.add_widget(self.search_btn)
            elif right_type == top_nav_config.RIGHT_BUTTON_HOME:
                self.right_container.add_widget(self.home_btn)

    def _set_artist_songs_mode(self):
        self.left_container.clear_widgets()
        self.left_container.add_widget(self.back_btn)
        self.back_btn.on_release = self._on_back_press

        self.right_container.clear_widgets()
        self.right_container.add_widget(self.home_btn)

        self.set_custom_title("Песни исполнителя")

    def _on_screen_changed(self, instance, screen_name):
        if self._block_navigation:
            return
        old = self.current_screen_name
        if old == screen_name:
            return

        self.current_screen_name = screen_name

        if old and old != screen_name:
            if screen_name == 'artist_songs' and old == 'song_detail':
                pass
            else:
                screen_state.set_previous_screen(old)

        if old and old != screen_name:
            self._previous_screen = old

        if screen_name == 'artist_songs':
            self._set_artist_songs_mode()
        else:
            self._update_left_button(screen_name)
            self._update_right_buttons(screen_name)

        if screen_name == 'artist_songs':
            pass
        else:
            title_type = top_nav_config.get_custom_title_widget_type(screen_name)
            if title_type == 'vertical' and screen_name not in ['song_detail']:
                pass
            elif top_nav_config.is_title_custom(screen_name):
                if self.custom_title_widget:
                    self.clear_custom_title_widget()
                self.update_title(screen_name)
            else:
                if self.custom_title_widget:
                    self.clear_custom_title_widget()
                self.update_title(screen_name)

        app = MDApp.get_running_app()
        if app and hasattr(app, 'bottom_nav') and app.bottom_nav:
            nav_screens = ['songs', 'chords', 'tuner', 'metronome', 'favorites']
            if screen_name in nav_screens:
                for item, (_, _, screen) in zip(app.bottom_nav.items, app.bottom_nav.nav_items):
                    item.active = (screen == screen_name)
            else:
                app.bottom_nav.clear_active()

    def _on_back_press(self, *args):
        if self._block_navigation:
            return

        if self._custom_back_callback:
            self._custom_back_callback()
            return

        if not self.sm:
            return

        current = self.sm.current
        prev_from_state = screen_state.get_previous_screen()

        nav_screens = ['songs', 'chords', 'tuner', 'metronome', 'favorites', 'dictionary']

        parser_screens = [
            'amdm_parser', 'mytabs_parser', 'accord_pro_parser',
            'akkordus_parser', 'muzland_parser', 'chordie_parser',
            'fivelad_parser', 'akkordbard_parser', 'domhve_parser',
            'rushsound_parser'
        ]

        if current in nav_screens:
            return

        if current in parser_screens:
            if self.sm.has_screen('admin'):
                self._block_navigation = True
                self.sm.current = 'admin'
                Clock.schedule_once(lambda dt: setattr(self, '_block_navigation', False), 0.5)
            else:
                self.sm.current = 'home'
            return

        if current == 'artist_songs':
            if hasattr(self, '_just_returned_from_song_detail') and self._just_returned_from_song_detail:
                self._just_returned_from_song_detail = False
                return

            if self._navigating:
                return
            self._navigating = True

            if self.sm.has_screen('artist_songs'):
                artist_screen = self.sm.get_screen('artist_songs')
                if hasattr(artist_screen, 'go_back'):
                    artist_screen.go_back()
                    Clock.schedule_once(lambda dt: setattr(self, '_navigating', False), 0.5)
                    return

            if self.sm.has_screen('songs'):
                songs_screen = self.sm.get_screen('songs')
                Clock.schedule_once(lambda dt: songs_screen.restore_state(), 0.1)
                self.sm.current = 'songs'
                Clock.schedule_once(lambda dt: setattr(self, '_navigating', False), 0.5)
                return
            else:
                self.sm.current = 'home'
                Clock.schedule_once(lambda dt: setattr(self, '_navigating', False), 0.5)
                return

        if current == 'song_detail':
            self._just_returned_from_song_detail = True

            if self.sm.has_screen('song_detail'):
                song_detail = self.sm.get_screen('song_detail')
                if hasattr(song_detail, 'go_back'):
                    song_detail.go_back()
                    Clock.schedule_once(lambda dt: setattr(self, '_just_returned_from_song_detail', False), 0.5)
                    return

            if prev_from_state and self.sm.has_screen(prev_from_state):
                self.sm.current = prev_from_state
                Clock.schedule_once(lambda dt: setattr(self, '_just_returned_from_song_detail', False), 0.5)
                return

            if self.sm.has_screen('home'):
                self.sm.current = 'home'
                Clock.schedule_once(lambda dt: setattr(self, '_just_returned_from_song_detail', False), 0.5)
                return

        if current == 'chord_detail':
            if self.sm.has_screen('search'):
                screen_state.clear_pending_chord()
                self.sm.current = 'search'
                return
            elif self.sm.has_screen('chords'):
                self.sm.current = 'chords'
                return
            else:
                self.sm.current = 'home'
                return

        if top_nav_config.show_back_button(current):
            if prev_from_state and self.sm.has_screen(prev_from_state):
                self.sm.current = prev_from_state
                return

        if self.sm.has_screen('home'):
            self.sm.current = 'home'

    def _on_settings_press(self, *args):
        app = MDApp.get_running_app()
        if hasattr(app, 'sidebar') and app.sidebar:
            app.sidebar.toggle()

    def _on_home_press(self, *args):
        if self.sm and self.sm.has_screen('home'):
            self.sm.current = 'home'

    def _on_search_press(self, *args):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

        if self.sm and self.sm.has_screen('search'):
            if self.sm.current == 'search':
                search_screen = self.sm.get_screen('search')
                # Если мы уже на экране поиска, просто фокусируем поле ввода
                if hasattr(search_screen, 'search_bar') and search_screen.search_bar:
                    search_screen.search_bar.search_field.focus = True
            else:
                self.sm.current = 'search'

    def set_app(self, app):
        self.app = app

    def reset_to_default(self):
        self.clear_custom_title_widget()
        self._update_left_button('home')
        self._update_right_buttons('home')
        self.update_title('home')

    def on_size(self, *args):
        Clock.schedule_once(lambda dt: self._adjust_title_width(), 0.1)

    def force_update_title(self, title, show_back=False):
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        self.screen_title.text = title
        self._adjust_title_width()

        if self.screen_title not in self.container.children:
            self.container.add_widget(self.screen_title)

        if show_back:
            self.left_container.clear_widgets()
            self.left_container.add_widget(self.back_btn)

        self.container.do_layout()

    def is_transparent(self):
        return True