# screens/home_screen.py
"""
Главный экран гитарного приложения - с сеткой разделов 3x2 и информацией о пользователе
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
from io import BytesIO
from kivy.utils import platform
from kivy.properties import NumericProperty

from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.behaviors import CircularRippleBehavior
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('Home')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


def hex_to_rgb(hex_color):
    """Конвертирует HEX цвет в RGB список"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


class GridCard(CircularRippleBehavior, MDCard):
    """Карточка раздела в сетке 3x2"""

    # Свойство для анимации масштаба
    scale = NumericProperty(1.0)

    # Цвета разделов
    SECTION_COLORS = {
        'songs': ('#E53935', '#C62828'),
        'chords': ('#43A047', '#2E7D32'),
        'tuner': ('#1E88E5', '#1565C0'),
        'metronome': ('#FF6F00', '#E65100'),
        'dictionary': ('#8E24AA', '#6A1B9A'),
        'favorites': ('#E91E63', '#AD1457'),
    }

    def __init__(self, section_id, title, icon_asset, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.section_id = section_id
        self.title = title
        self.icon_asset = icon_asset
        self.on_click_callback = on_click

        colors = self.SECTION_COLORS.get(section_id, ('#757575', '#616161'))
        self.bg_color = colors[0]

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.radius = [dp(16)]
        self.elevation = 2
        self.ripple_scale = 0.95

        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.85)

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(6),
            padding=[dp(10), dp(12), dp(10), dp(12)],
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )

        # Иконка
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        # Название
        if len(title) > 8:
            font_size = sp(10)
        elif len(title) > 6:
            font_size = sp(11)
        else:
            font_size = sp(12)

        self.title_label = MDLabel(
            text=title,
            font_size=font_size,
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            shorten=True,
            shorten_from="right"
        )

        content.add_widget(self.icon_image)
        content.add_widget(self.title_label)

        self.add_widget(content)
        self.bind(on_release=self._on_click)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)
        self.bind(scale=self._update_scale)

    def _update_scale(self, instance, value):
        pass

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
        self.icon_image.text = "🎸"
        self.icon_image.color = [1, 1, 1, 0.8]

    def _hex_to_rgba(self, hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [alpha]

    def _on_enter(self, *args):
        Animation(elevation=6, duration=0.15).start(self)
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 1.0)
        Animation(scale=1.05, duration=0.15).start(self)

    def _on_leave(self, *args):
        Animation(elevation=2, duration=0.15).start(self)
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.85)
        Animation(scale=1.0, duration=0.15).start(self)

    def _on_click(self, instance):
        if self.on_click_callback:
            Animation(opacity=0.8, duration=0.05).start(self)
            Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.1).start(self), 0.05)
            self.on_click_callback(self.section_id)


class HomeScreen(BaseScreen):
    """Главный экран приложения с сеткой разделов 3x2"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        self.user = None
        self.auth_check_done = False
        self.app_name_label = None
        self.user_info_label = None
        self.auth_modal_shown = False
        self.is_authenticated = False
        self._grid = None
        self._user_info_container = None
        self._top_nav_reset_done = False

        self.init_ui()

        # Принудительно устанавливаем заголовок при создании
        Clock.schedule_once(self._force_set_home_title, 0.1)
        Clock.schedule_once(self._force_set_home_title, 0.3)
        Clock.schedule_once(self._force_set_home_title, 0.5)

        Clock.schedule_once(self._check_auth, 0.7)

        logger.info('Главный экран создан')

    def _force_set_home_title(self, dt):
        """Принудительно устанавливает 'Главная' в TopNav"""
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav') and app.top_nav:
                app.top_nav.clear_custom_title_widget()
                app.top_nav.update_title('home')
                app.top_nav._update_left_button('home')
                app.top_nav._update_right_buttons('home')
                logger.debug("✅ TopNav принудительно установлен на 'Главная'")
                self._top_nav_reset_done = True
        except Exception as e:
            logger.debug(f"TopNav ещё не готов: {e}")

    def init_ui(self):
        """Инициализирует UI с сеткой 3x2 и информацией о пользователе"""

        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Верхний отступ (под статус-бар и TopNav)
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Дополнительный отступ сверху
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # Контейнер с боковыми отступами
        content_padding = layout_config.get_content_padding()
        content_wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[content_padding[0], 0, content_padding[2], 0]
        )

        # ============ НАЗВАНИЕ ПРИЛОЖЕНИЯ ============
        self.app_name_label = MDLabel(
            text="GuitarFuns",
            font_size=sp(32),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            bold=True
        )
        content_wrapper.add_widget(self.app_name_label)

        # Небольшой отступ
        content_wrapper.add_widget(Widget(size_hint_y=None, height=dp(8)))

        # ============ СЕТКА 3x2 ============
        self._grid = GridLayout(
            cols=3,
            spacing=dp(12),
            size_hint=(1, None),
            height=dp(260)
        )

        sections = [
            ('songs', 'Песни', 'songs_png'),
            ('chords', 'Аккорды', 'chords_png'),
            ('tuner', 'Тюнер', 'tuner_png'),
            ('metronome', 'Метроном', 'metronome_png'),
            ('dictionary', 'Словарь', 'dictionary_png'),
            ('favorites', 'Избранное', 'favorites_png'),
        ]

        for section_id, title, icon_asset in sections:
            card = GridCard(
                section_id=section_id,
                title=title,
                icon_asset=icon_asset,
                on_click=self._on_section_selected
            )
            self._grid.add_widget(card)

        content_wrapper.add_widget(self._grid)

        # ============ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ ============
        content_wrapper.add_widget(Widget(size_hint_y=None, height=dp(24)))

        self._user_info_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(50),
            spacing=dp(4),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        # Разделительная линия
        divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(1),
            md_bg_color=[1, 1, 1, 0.1],
            padding=[dp(20), 0, dp(20), 0]
        )
        self._user_info_container.add_widget(divider)

        # Информация о пользователе
        self.user_info_label = MDLabel(
            text="👤 Пользователь: гость",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(32),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            bold=False
        )
        self._user_info_container.add_widget(self.user_info_label)

        content_wrapper.add_widget(self._user_info_container)

        # Растягивающийся виджет внизу
        content_wrapper.add_widget(Widget(size_hint_y=1))

        main_layout.add_widget(content_wrapper)

        # Нижний отступ
        if platform != 'android':
            main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.add_widget(main_layout)

        logger.info(f"HomeScreen: top_padding = {top_padding}dp")

    def _update_user_info(self, username=None):
        """Обновляет информацию о пользователе"""
        if self.user_info_label:
            if username:
                self.user_info_label.text = f"👤 Пользователь: {username}"
            else:
                self.user_info_label.text = "👤 Пользователь: гость"

    def _reset_top_nav_to_home(self):
        """Сбрасывает TopNav в состояние для главного экрана"""
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav') and app.top_nav:
                app.top_nav.clear_custom_title_widget()
                app.top_nav.update_title('home')
                app.top_nav._update_left_button('home')
                app.top_nav._update_right_buttons('home')
                logger.debug("TopNav сброшен для главного экрана")
                self._top_nav_reset_done = True
        except Exception as e:
            logger.debug(f"TopNav ещё не готов: {e}")

    def _on_section_selected(self, section_id):
        """Обработчик выбора раздела"""
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
        """Проверяет авторизацию"""
        if self.auth_check_done:
            return
        self.auth_check_done = True

        if api.access_token:
            api.get_current_user(
                on_success=self._on_auth_success,
                on_failure=self._on_auth_failure
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

        # Сбрасываем TopNav на главный экран
        self._reset_top_nav_to_home()

        # Обновляем избранное, если экран избранного активен
        self._refresh_favorites_if_needed()

    def _on_auth_failure(self, req, error):
        logger.warning(f'Авторизация не пройдена: {error}')
        self._update_user_info()
        self._show_auth_modal()

    def _show_auth_modal(self):
        """Показывает окно авторизации"""
        if self.auth_modal_shown:
            return
        self.auth_modal_shown = True

        Clock.schedule_once(self._show_auth_modal_delayed, 0.5)

    def _show_auth_modal_delayed(self, dt):
        """Показывает окно авторизации с задержкой"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'open_profile'):
            app.open_profile()
        self.auth_modal_shown = False

    def _refresh_favorites_if_needed(self):
        """Обновляет экран избранного, если он открыт"""
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('favorites'):
                favorites_screen = self.manager.get_screen('favorites')
                if hasattr(favorites_screen, 'refresh_favorites'):
                    Clock.schedule_once(lambda dt: favorites_screen.refresh_favorites(), 0.5)

    def on_login_success(self):
        """Обработчик успешного входа - вызывается из main.py"""
        logger.info("✅ Успешная авторизация на главном экране")
        # Сбрасываем TopNav на главный экран
        self._reset_top_nav_to_home()

        # Обновляем информацию о пользователе
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
        """При входе на экран"""
        logger.info("Вход в главный экран")

        # ============ ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ ЗАГОЛОВОК "ГЛАВНАЯ" ============
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav') and app.top_nav:
                app.top_nav.clear_custom_title_widget()
                app.top_nav.update_title('home')
                app.top_nav._update_left_button('home')
                app.top_nav._update_right_buttons('home')
                logger.debug("✅ TopNav принудительно установлен на 'Главная' при входе")
                self._top_nav_reset_done = True
        except Exception as e:
            logger.debug(f"TopNav ещё не готов: {e}")

        # Если пользователь уже авторизован - показываем его имя
        if api.is_authenticated() and api.user_data:
            username = api.user_data.get('username', 'Гость')
            self._update_user_info(username)
        elif api.is_authenticated() and api.access_token:
            # Есть токен, но нет данных - загружаем
            api.get_current_user(
                on_success=self._on_user_data_loaded,
                on_failure=lambda req, err: self._update_user_info()
            )
        elif not api.is_authenticated():
            if not self.auth_check_done:
                self._check_auth(0)
            else:
                self._update_user_info()

    def on_leave(self):
        """При выходе с экрана"""
        return super().on_leave()