# screens/home_screen.py
"""
Главный экран гитарного приложения - сетка разделов 3x2.
Стиль: Clean Solid Cards (минимализм как в Spotify / Apple Music).
"""
from io import BytesIO

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp, sp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.behaviors import CircularRippleBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api

logger = screen_logger('Home')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def hex_to_rgba(hex_color, alpha=1.0):
    return hex_to_rgb(hex_color) + [alpha]


# ============================================================
# КАРТОЧКА РАЗДЕЛА
# ============================================================

class GridCard(CircularRippleBehavior, MDCard):
    """
    Чистая минималистичная карточка:
    - однотонный насыщенный фон
    - PNG-иконка по центру
    - крупное белое название под иконкой
    - мягкая тень, hover, ripple
    """

    SECTION_COLORS = {
        'songs':      '#E53935',   # красный
        'chords':     '#43A047',   # зелёный
        'tuner':      '#1E88E5',   # синий
        'metronome':  '#FB8C00',   # оранжевый
        'dictionary': '#8E24AA',   # фиолетовый
        'favorites':  '#EC407A',   # розовый
    }

    def __init__(self, section_id, title, icon_asset, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.section_id = section_id
        self.title_text = title
        self.icon_asset = icon_asset
        self.on_click_callback = on_click

        self.base_color_hex = self.SECTION_COLORS.get(section_id, '#546E7A')
        self.base_color = hex_to_rgba(self.base_color_hex, 1.0)
        # hover — на 6% светлее
        self.hover_color = [min(1.0, c + 0.06) for c in self.base_color[:3]] + [1.0]

        # ---------- карточка ----------
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.radius = [dp(24)]
        self.elevation = 4
        self.ripple_scale = 0.9
        self.md_bg_color = self.base_color
        self.padding = [dp(10), dp(14), dp(10), dp(14)]
        self.spacing = 0

        # ---------- контент ----------
        content = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0],
            padding=0,
            spacing=0,
        )

        # верхняя распорка — оттесняет иконку чуть выше центра
        content.add_widget(Widget(size_hint_y=0.35))

        # иконка
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(64), dp(64)),
            pos_hint={'center_x': 0.5},
            fit_mode="contain",
            mipmap=True,
        )
        self._load_icon()
        content.add_widget(self.icon_image)

        # отступ между иконкой и названием
        content.add_widget(Widget(size_hint_y=None, height=dp(10)))

        # название
        font_size = sp(14) if len(title) > 8 else (sp(15) if len(title) > 6 else sp(16))

        self.title_label = MDLabel(
            text=title,
            font_size=font_size,
            halign="center",
            valign="middle",
            bold=True,
            size_hint=(1, None),
            height=dp(26),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1.0],
            shorten=True,
            shorten_from="right",
        )
        content.add_widget(self.title_label)

        # нижняя распорка
        content.add_widget(Widget(size_hint_y=0.6))

        self.add_widget(content)

        # ---------- события ----------
        self.bind(on_release=self._on_click)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    # ---------- иконка ----------
    def _load_icon(self):
        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {self.icon_asset}: {e}")
        self.icon_image.opacity = 0

    # ---------- hover / click ----------
    def _on_enter(self, *args):
        Animation(elevation=12, duration=0.15).start(self)
        Animation(md_bg_color=self.hover_color, duration=0.15).start(self)

    def _on_leave(self, *args):
        Animation(elevation=4, duration=0.15).start(self)
        Animation(md_bg_color=self.base_color, duration=0.15).start(self)

    def _on_click(self, instance):
        if self.on_click_callback:
            Animation(elevation=0, duration=0.08).start(self)
            Clock.schedule_once(self._restore_and_navigate, 0.09)

    def _restore_and_navigate(self, dt):
        Animation(elevation=4, duration=0.18).start(self)
        if self.on_click_callback:
            self.on_click_callback(self.section_id)


# ============================================================
# ГЛАВНЫЙ ЭКРАН
# ============================================================

class HomeScreen(BaseScreen):
    """Главный экран приложения с сеткой разделов 3x2."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        self.user = None
        self.auth_check_done = False
        self.app_name_label = None
        # user_info_label больше не создаём — оставляем пустое место
        self.user_info_label = None
        self.auth_modal_shown = False
        self.is_authenticated = False
        self._grid = None
        self._user_info_container = None
        self._top_nav_reset_done = False

        self.init_ui()

        Clock.schedule_once(self._force_set_home_title, 0.1)
        Clock.schedule_once(self._force_set_home_title, 0.3)
        Clock.schedule_once(self._force_set_home_title, 0.5)
        Clock.schedule_once(self._check_auth, 0.7)

        logger.info('Главный экран создан')

    def _force_set_home_title(self, dt):
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav') and app.top_nav:
                app.top_nav.clear_custom_title_widget()
                app.top_nav.update_title('home')
                app.top_nav._update_left_button('home')
                app.top_nav._update_right_buttons('home')
                self._top_nav_reset_done = True
        except Exception as e:
            logger.debug(f"TopNav ещё не готов: {e}")

    def init_ui(self):
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        content_padding = layout_config.get_content_padding()
        content_wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[content_padding[0], 0, content_padding[2], 0],
        )

        # ---------- заголовок приложения ----------
        self.app_name_label = MDLabel(
            text="GuitarFuns",
            font_size=sp(32),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            bold=True,
        )
        content_wrapper.add_widget(self.app_name_label)
        content_wrapper.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # ---------- сетка 3x2 ----------
        self._grid = GridLayout(
            cols=3,
            spacing=dp(14),
            size_hint=(1, None),
            height=dp(320),
        )

        sections = [
            ('songs',      'Песни',     'songs_png'),
            ('chords',     'Аккорды',   'chords_png'),
            ('tuner',      'Тюнер',     'tuner_png'),
            ('metronome',  'Метроном',  'metronome_png'),
            ('dictionary', 'Словарь',   'dictionary_png'),
            ('favorites',  'Избранное', 'favorites_png'),
        ]

        for section_id, title, icon_asset in sections:
            card = GridCard(
                section_id=section_id,
                title=title,
                icon_asset=icon_asset,
                on_click=self._on_section_selected,
            )
            self._grid.add_widget(card)

        content_wrapper.add_widget(self._grid)

        # ---------- ПУСТОЕ МЕСТО ПОД КАРТОЧКАМИ ----------
        # Никакой разделительной линии и никакого "Пользователь: гость".
        # Просто резервируем ту же высоту dp(50), чтобы потом сюда
        # можно было положить что угодно (кнопку входа, статистику и т.д.).
        content_wrapper.add_widget(Widget(size_hint_y=None, height=dp(24)))
        self._user_info_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(50),
            md_bg_color=[0, 0, 0, 0],
        )
        content_wrapper.add_widget(self._user_info_container)

        content_wrapper.add_widget(Widget(size_hint_y=1))

        main_layout.add_widget(content_wrapper)

        if platform != 'android':
            main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.add_widget(main_layout)
        logger.info(f"HomeScreen: top_padding = {top_padding}dp")

    # ---------- пользователь ----------
    # Метод оставлен для совместимости — просто ничего не делает,
    # потому что user_info_label больше нет.
    def _update_user_info(self, username=None):
        pass

    def _reset_top_nav_to_home(self):
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav') and app.top_nav:
                app.top_nav.clear_custom_title_widget()
                app.top_nav.update_title('home')
                app.top_nav._update_left_button('home')
                app.top_nav._update_right_buttons('home')
                self._top_nav_reset_done = True
        except Exception as e:
            logger.debug(f"TopNav ещё не готов: {e}")

    # ---------- навигация ----------
    def _on_section_selected(self, section_id):
        screen_map = {
            'songs': 'songs',
            'chords': 'chords',
            'tuner': 'tuner',
            'metronome': 'metronome',
            'dictionary': 'dictionary',
            'favorites': 'favorites',
        }
        screen_name = screen_map.get(section_id)
        if screen_name and hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen(screen_name):
                self.manager.transition.direction = 'left'
                self.manager.current = screen_name
            else:
                logger.warning(f"Экран {screen_name} не найден")

    # ---------- авторизация ----------
    def _check_auth(self, dt):
        if self.auth_check_done:
            return
        self.auth_check_done = True

        if api.access_token:
            api.get_current_user(
                on_success=self._on_auth_success,
                on_failure=self._on_auth_failure,
            )
        else:
            logger.info("Нет токена, показываем гостя")
            self._update_user_info()
            self._show_auth_modal()

    def _on_auth_success(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        logger.info(f'Пользователь авторизован: {username}')
        self._update_user_info(username)
        self._reset_top_nav_to_home()
        self._refresh_favorites_if_needed()

    def _on_auth_failure(self, req, error):
        logger.warning(f'Авторизация не пройдена: {error}')
        self._update_user_info()
        self._show_auth_modal()

    def _show_auth_modal(self):
        if self.auth_modal_shown:
            return
        self.auth_modal_shown = True
        Clock.schedule_once(self._show_auth_modal_delayed, 0.5)

    def _show_auth_modal_delayed(self, dt):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'open_profile'):
            app.open_profile()
        self.auth_modal_shown = False

    def _refresh_favorites_if_needed(self):
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('favorites'):
                favorites_screen = self.manager.get_screen('favorites')
                if hasattr(favorites_screen, 'refresh_favorites'):
                    Clock.schedule_once(lambda dt: favorites_screen.refresh_favorites(), 0.5)

    def on_login_success(self):
        logger.info("✅ Успешная авторизация на главном экране")
        self._reset_top_nav_to_home()
        if api.is_authenticated() and api.user_data:
            username = api.user_data.get('username', 'Гость')
            self._update_user_info(username)
        else:
            self._check_auth(0)

    def _on_user_data_loaded(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        self._update_user_info(username)
        self._refresh_favorites_if_needed()
        logger.info(f'Данные пользователя обновлены: {username}')

    # ---------- lifecycle ----------
    def on_enter(self):
        logger.info("Вход в главный экран")
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav') and app.top_nav:
                app.top_nav.clear_custom_title_widget()
                app.top_nav.update_title('home')
                app.top_nav._update_left_button('home')
                app.top_nav._update_right_buttons('home')
                self._top_nav_reset_done = True
        except Exception as e:
            logger.debug(f"TopNav ещё не готов: {e}")

        if api.is_authenticated() and api.user_data:
            username = api.user_data.get('username', 'Гость')
            self._update_user_info(username)
        elif api.is_authenticated() and api.access_token:
            api.get_current_user(
                on_success=self._on_user_data_loaded,
                on_failure=lambda req, err: self._update_user_info(),
            )
        elif not api.is_authenticated():
            if not self.auth_check_done:
                self._check_auth(0)
            else:
                self._update_user_info()

    def on_leave(self):
        return super().on_leave()