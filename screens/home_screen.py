# screens/home_screen.py
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.metrics import dp, sp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.utils import platform
from kivy.graphics import Color, RoundedRectangle

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from home_utils.card_widget import StudioHomeGridCard as GridCard
from home_utils.logo_widget import StudioFuturisticLogo
from screens.base_screen import BaseScreen
from api.client import api
from state.settings_state import settings_state as settings_manager
from utils.localization import get_text

logger = screen_logger('Home')


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


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
        self.sub_label = None
        self._sub_hide_event = None

        self.init_ui()

        Clock.schedule_once(self._force_set_home_title, 0.1)
        Clock.schedule_once(self._force_set_home_title, 0.3)
        Clock.schedule_once(self._force_set_home_title, 0.5)
        Clock.schedule_once(self._check_auth, 0.7)
        Clock.schedule_once(self._apply_current_theme, 0.2)

        logger.info('Главный экран создан (StudioHomeGridCard + StudioFuturisticLogo)')

    def _apply_current_theme(self, dt):
        current_theme = settings_manager.theme

        if self.app_name_label:
            self.app_name_label.update_theme_colors()

        for card in self._cards.values():
            card.update_theme(current_theme)

    def update_theme_colors(self):
        self._apply_current_theme(0)

    def update_language(self):
        logger.info("🌐 Обновление языка на HomeScreen")
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
        from config.system_bars import get_navigation_bar_height

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

        self.app_name_label = StudioFuturisticLogo()
        content_wrapper.add_widget(self.app_name_label)
        content_wrapper.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self._grid = GridLayout(
            cols=3,
            spacing=dp(10),
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

        # ============ ПЛАШКА СТАТУСА ПОДПИСКИ ============
        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(52)
        padding_bottom = bottom_nav_height + nav_bar_height + dp(8)

        self.sub_label_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(40),
            padding=[dp(16), 0, dp(16), padding_bottom],
            md_bg_color=[0, 0, 0, 0]
        )

        self.sub_label = MDLabel(
            text="",
            font_size=sp(12),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            opacity=0,
            bold=True
        )

        with self.sub_label.canvas.before:
            self.sub_bg_color = Color(0, 0, 0, 0)
            self.sub_bg_rect = RoundedRectangle(
                pos=self.sub_label.pos,
                size=self.sub_label.size,
                radius=[dp(8)]
            )

        self.sub_label.bind(
            pos=lambda inst, val: setattr(self.sub_bg_rect, 'pos', val),
            size=lambda inst, val: setattr(self.sub_bg_rect, 'size', val)
        )

        self.sub_label_container.add_widget(self.sub_label)
        main_layout.add_widget(self.sub_label_container)

        if platform != 'android':
            main_layout.add_widget(Widget(size_hint_y=None, height=dp(10)))

        self.add_widget(main_layout)
        logger.info(f"HomeScreen: top_padding = {top_padding}dp")

    def show_subscription_status(self, status_data):
        """
        Плашка статуса подписки на 4 секунды.
        Поддерживает: active / exhausted / unlimited + is_admin.
        """
        if not self.sub_label:
            return

        status = status_data.get("status")
        is_admin = bool(status_data.get("is_admin", False))

        if is_admin or status == "unlimited":
            self.sub_label.text = "Безлимитный доступ (Админ)"
            self.sub_bg_color.rgba = [0.2, 0.2, 0.2, 0.95]
            self.sub_label.text_color = [0.9, 0.7, 0.2, 1]
            Animation(opacity=1, duration=0.3).start(self.sub_label)
            if self._sub_hide_event:
                self._sub_hide_event.cancel()
            self._sub_hide_event = Clock.schedule_once(
                lambda dt: Animation(opacity=0, duration=0.5).start(self.sub_label), 4.0
            )
            return

        if status == "exhausted":
            self.sub_label.text = "Подписка закончилась. Оформите или введите промокод."
            self.sub_bg_color.rgba = [0.7, 0.1, 0.1, 0.95]
            self.sub_label.text_color = [1, 1, 1, 1]

        elif status == "active":
            days_left = int(status_data.get("days_left", 0) or 0)
            if days_left <= 3:
                self.sub_label.text = f"[!] Подписка заканчивается. Осталось {days_left} дн."
                self.sub_bg_color.rgba = [0.8, 0.4, 0.1, 0.95]
                self.sub_label.text_color = [1, 1, 1, 1]
            else:
                self.sub_label.text = f"Подписка активна. Осталось {days_left} дн."
                self.sub_bg_color.rgba = [0.1, 0.4, 0.3, 0.95]
                self.sub_label.text_color = [1, 1, 1, 1]
        else:
            return

        Animation(opacity=1, duration=0.3).start(self.sub_label)

        def hide_label(dt):
            Animation(opacity=0, duration=0.5).start(self.sub_label)

        if self._sub_hide_event:
            self._sub_hide_event.cancel()

        self._sub_hide_event = Clock.schedule_once(hide_label, 4.0)

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
        super().on_enter()
        logger.info("Вход в главный экран")

        self._apply_current_theme(0)
        self.update_language()

        if self.app_name_label:
            Clock.schedule_once(lambda dt: self.app_name_label.start_periodic_animation(), 0.05)

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
        if self.app_name_label:
            self.app_name_label.stop_periodic_animation()
        return super().on_leave()