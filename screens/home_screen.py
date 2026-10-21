# screens/home_screen.py
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
from utils.settings_manager import settings_manager
from utils.localization import get_text

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
    Карточка раздела с адаптивными цветами под темы.
    Всегда цветная, но оттенки подстраиваются под фон.
    """

    # Цвета для ЗЕЛЁНОЙ темы (базовые насыщенные)
    GREEN_SECTION_COLORS = {
        'songs': '#E53935',
        'chords': '#43A047',
        'tuner': '#1E88E5',
        'metronome': '#FB8C00',
        'dictionary': '#8E24AA',
        'favorites': '#EC407A',
    }

    # Цвета для СВЕТЛОЙ темы (пастельные, чтобы не сливались с белым)
    LIGHT_SECTION_COLORS = {
        'songs': '#EF9A9A',
        'chords': '#A5D6A7',
        'tuner': '#90CAF9',
        'metronome': '#FFCC80',
        'dictionary': '#CE93D8',
        'favorites': '#F48FB1',
    }

    # Цвета для ТЁМНОЙ темы (более глубокие, но цветные)
    DARK_SECTION_COLORS = {
        'songs': '#B71C1C',  # Тёмно-красный
        'chords': '#1B5E20',  # Тёмно-зелёный
        'tuner': '#0D47A1',  # Тёмно-синий
        'metronome': '#E65100',  # Тёмно-оранжевый
        'dictionary': '#4A148C',  # Тёмно-фиолетовый
        'favorites': '#880E4F',  # Тёмно-розовый
    }

    def __init__(self, section_id, title, icon_asset, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.section_id = section_id
        self.title_text = title
        self.icon_asset = icon_asset
        self.on_click_callback = on_click
        self._current_theme = settings_manager.theme

        # ---------- карточка ----------
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.radius = [dp(24)]
        self.elevation = 4
        self.ripple_scale = 0.9
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

        content.add_widget(Widget(size_hint_y=0.35))

        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(64), dp(64)),
            pos_hint={'center_x': 0.5},
            fit_mode="contain",
            mipmap=True,
        )
        content.add_widget(self.icon_image)

        content.add_widget(Widget(size_hint_y=None, height=dp(10)))

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
            shorten=True,
            shorten_from="right",
        )
        content.add_widget(self.title_label)

        content.add_widget(Widget(size_hint_y=0.6))

        self.add_widget(content)

        # ---------- ЦВЕТА ----------
        self._load_icon()
        self._setup_colors()

        self.bind(on_release=self._on_click)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _setup_colors(self):
        """Устанавливает цвета в зависимости от текущей темы"""
        theme_id = self._current_theme

        if theme_id == 'dark':
            self.base_color_hex = self.DARK_SECTION_COLORS.get(self.section_id, '#424242')
            self.base_color = hex_to_rgba(self.base_color_hex, 1.0)
            self.hover_color = [min(1.0, c + 0.1) for c in self.base_color[:3]] + [1.0]
            self.md_bg_color = self.base_color
            self.title_label.text_color = [1, 1, 1, 1]
            self.icon_color = [1, 1, 1, 1]  # Белая иконка
        elif theme_id == 'light':
            self.base_color_hex = self.LIGHT_SECTION_COLORS.get(self.section_id, '#E0E0E0')
            self.base_color = hex_to_rgba(self.base_color_hex, 1.0)
            self.hover_color = [min(1.0, c + 0.05) for c in self.base_color[:3]] + [1.0]
            self.md_bg_color = self.base_color
            self.title_label.text_color = [0.15, 0.15, 0.15, 1]  # Тёмный текст

            # ИКОНКА: берём насыщенный цвет (как в зелёной теме) для контраста
            # Но чуть приглушаем, чтобы не резало глаз на пастельном фоне
            rich_hex = self.GREEN_SECTION_COLORS.get(self.section_id, '#546E7A')
            rich_rgb = hex_to_rgb(rich_hex)
            # Смешиваем насыщенный цвет с белым в пропорции 70/30 (чтобы был ярким, но не "кислотным")
            self.icon_color = [
                min(1.0, rich_rgb[0] * 0.7 + 0.3),
                min(1.0, rich_rgb[1] * 0.7 + 0.3),
                min(1.0, rich_rgb[2] * 0.7 + 0.3),
                1.0
            ]
        else:  # green
            self.base_color_hex = self.GREEN_SECTION_COLORS.get(self.section_id, '#546E7A')
            self.base_color = hex_to_rgba(self.base_color_hex, 1.0)
            self.hover_color = [min(1.0, c + 0.06) for c in self.base_color[:3]] + [1.0]
            self.md_bg_color = self.base_color
            self.title_label.text_color = [1, 1, 1, 1]
            self.icon_color = [1, 1, 1, 1]

        if hasattr(self, 'icon_image') and self.icon_image:
            self.icon_image.color = self.icon_color

    def update_theme(self, theme_id):
        """Вызывается при смене темы"""
        self._current_theme = theme_id
        self._setup_colors()

    def update_language(self, new_title):
        """Вызывается при смене языка"""
        self.title_text = new_title
        self.title_label.text = new_title
        # Пересчитываем шрифт на случай, если слово стало длиннее
        font_size = sp(14) if len(new_title) > 8 else (sp(15) if len(new_title) > 6 else sp(16))
        self.title_label.font_size = font_size

    def _load_icon(self):
        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    self.icon_image.color = getattr(self, 'icon_color', [1, 1, 1, 1])
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {self.icon_asset}: {e}")
        self.icon_image.opacity = 0

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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        self.user = None
        self.auth_check_done = False
        self.app_name_label = None
        self.auth_modal_shown = False
        self.is_authenticated = False
        self._grid = None
        self._cards = {}
        self._top_nav_reset_done = False

        self.init_ui()

        Clock.schedule_once(self._force_set_home_title, 0.1)
        Clock.schedule_once(self._force_set_home_title, 0.3)
        Clock.schedule_once(self._force_set_home_title, 0.5)
        Clock.schedule_once(self._check_auth, 0.7)
        Clock.schedule_once(self._apply_current_theme, 0.2)

        logger.info('Главный экран создан')

    def _apply_current_theme(self, dt):
        current_theme = settings_manager.theme

        if self.app_name_label:
            if current_theme == 'dark':
                self.app_name_label.text_color = [1.0, 0.5, 0.0, 1]
            elif current_theme == 'light':
                self.app_name_label.text_color = [0.1, 0.55, 0.3, 1]
            else:
                self.app_name_label.text_color = hex_to_rgb(theme.PRIMARY) + [1]

        for card in self._cards.values():
            card.update_theme(current_theme)

    def update_theme_colors(self):
        """Вызывается из app.apply_theme. Делегируем в существующий _apply_current_theme."""
        self._apply_current_theme(0)

    def update_language(self):
        """Обновляет тексты на карточках при смене языка"""
        logger.info("🌐 Обновление языка на HomeScreen")

        # Обновляем карточки
        for section_id, card in self._cards.items():
            new_title = get_text(section_id, section_id.capitalize())
            card.update_language(new_title)

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

        self._grid = GridLayout(
            cols=3,
            spacing=dp(14),
            size_hint=(1, None),
            height=dp(320),
        )

        sections = [
            ('songs', 'songs_png'),
            ('chords', 'chords_png'),
            ('tuner', 'tuner_png'),
            ('metronome', 'metronome_png'),
            ('dictionary', 'dictionary_png'),
            ('favorites', 'favorites_png'),
        ]

        self._cards = {}
        for section_id, icon_asset in sections:
            # Заголовок берем из перевода
            title = get_text(section_id, section_id.capitalize())

            card = GridCard(
                section_id=section_id,
                title=title,
                icon_asset=icon_asset,
                on_click=self._on_section_selected,
            )
            self._cards[section_id] = card
            self._grid.add_widget(card)

        content_wrapper.add_widget(self._grid)

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

    def on_enter(self):
        logger.info("Вход в главный экран")

        self._apply_current_theme(0)
        self.update_language()  # Обновляем язык при входе на всякий случай

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