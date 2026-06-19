# screens/home_screen.py
"""
Главный экран гитарного приложения - с сеткой разделов 3x2 в стиле карусели
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
    """Карточка раздела в сетке 3x2 - точь-в-точь как SectionCard из карусели"""

    # Свойство для анимации масштаба
    scale = NumericProperty(1.0)

    # Цвета из SectionCard
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
        """Обновляет визуальный размер при изменении scale"""
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
        """При наведении - ярче и поднимаем"""
        Animation(elevation=6, duration=0.15).start(self)
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 1.0)
        Animation(scale=1.05, duration=0.15).start(self)

    def _on_leave(self, *args):
        """При убирании курсора"""
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
        self.welcome_label = None
        self.username_label = None
        self.app_name_label = None
        self.auth_modal_shown = False
        self.is_authenticated = False

        self.init_ui()
        Clock.schedule_once(self._check_auth, 0.5)
        logger.info('Главный экран создан')

    def init_ui(self):
        """Инициализирует UI с сеткой 3x2"""

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

        # ============ ЗАГОЛОВОК ============
        header_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(2),
            padding=[dp(8), dp(4), dp(8), dp(4)]
        )

        # Добро пожаловать (показывается сначала)
        self.welcome_label = MDLabel(
            text="",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True,
            opacity=1
        )

        # Название приложения (появляется после)
        self.app_name_label = MDLabel(
            text="GuitarFuns",
            font_size=sp(24),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            bold=True,
            opacity=0
        )

        header_container.add_widget(self.welcome_label)
        header_container.add_widget(self.app_name_label)
        content_wrapper.add_widget(header_container)

        # Небольшой отступ
        content_wrapper.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # ============ СЕТКА 3x2 ============
        grid = GridLayout(
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
            grid.add_widget(card)

        content_wrapper.add_widget(grid)

        # ============ ПОПУЛЯРНЫЕ ПОДБОРЫ (заглушка) ============
        content_wrapper.add_widget(Widget(size_hint_y=None, height=dp(16)))

        popular_label = MDLabel(
            text="Популярные подборы",
            font_size=sp(16),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )
        content_wrapper.add_widget(popular_label)

        # Заглушка для популярных подборов
        placeholder_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(80),
            radius=[dp(12), dp(12), dp(12), dp(12)],
            md_bg_color=[0, 0, 0, 0.08],
            elevation=0,
            padding=[dp(16), dp(16), dp(16), dp(16)],
            line_color=[1, 1, 1, 0.05],
            line_width=1
        )

        placeholder_label = MDLabel(
            text="Скоро здесь появятся популярные подборы",
            halign="center",
            valign="middle",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4],
            size_hint=(1, 1)
        )
        placeholder_card.add_widget(placeholder_label)
        content_wrapper.add_widget(placeholder_card)

        # Растягивающийся виджет внизу
        content_wrapper.add_widget(Widget(size_hint_y=1))

        main_layout.add_widget(content_wrapper)

        # Нижний отступ
        if platform != 'android':
            main_layout.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.add_widget(main_layout)

        logger.info(f"HomeScreen: top_padding = {top_padding}dp")

    def _show_welcome(self, username):
        """Показывает приветствие с именем пользователя"""
        if self.welcome_label:
            self.welcome_label.text = f"Добро пожаловать, {username}!"
            self.welcome_label.opacity = 1
            self.app_name_label.opacity = 0

            # Через 1.5 секунды меняем на название приложения
            Clock.schedule_once(self._show_app_name, 1.5)

    def _show_app_name(self, dt):
        """Показывает название приложения вместо приветствия"""
        if self.welcome_label:
            # Анимируем исчезновение приветствия
            anim1 = Animation(opacity=0, duration=0.4)
            anim1.start(self.welcome_label)

            # Через 0.4 секунды показываем название
            Clock.schedule_once(lambda x: self._show_app_name_after(), 0.4)

    def _show_app_name_after(self):
        """Показывает название приложения"""
        if self.app_name_label:
            self.app_name_label.opacity = 1
            anim = Animation(opacity=1, duration=0.4)
            anim.start(self.app_name_label)
            logger.info("Показано название приложения")

    def _show_auth_modal(self):
        """Показывает окно авторизации"""
        if self.auth_modal_shown:
            return
        self.auth_modal_shown = True

        # Задерживаем показ, чтобы пользователь увидел приветствие
        Clock.schedule_once(self._show_auth_modal_delayed, 1.0)

    def _show_auth_modal_delayed(self, dt):
        """Показывает окно авторизации с задержкой"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'open_profile'):
            # Используем метод приложения для показа авторизации
            app.open_profile()
        self.auth_modal_shown = False

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
            self._show_welcome("гость")
            # Показываем окно авторизации для гостя
            self._show_auth_modal()

    def _on_auth_success(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        logger.info(f'Пользователь авторизован: {username}')
        self._show_welcome(username)

    def _on_auth_failure(self, req, error):
        logger.warning(f'Авторизация не пройдена: {error}')
        self._show_welcome("гость")
        # Показываем окно авторизации при ошибке
        self._show_auth_modal()

    def on_login_success(self):
        """Обработчик успешного входа"""
        if api.access_token:
            api.get_current_user(
                on_success=self._on_user_data_loaded,
                on_failure=lambda req, err: None
            )

    def _on_user_data_loaded(self, user):
        self.user = user
        api.user_data = user
        username = user.get('username', 'Гость')
        self._show_welcome(username)

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в главный экран")
        # Если пользователь уже авторизован, показываем приветствие
        if api.is_authenticated() and api.user_data:
            username = api.user_data.get('username', 'Гость')
            self._show_welcome(username)
        elif not api.is_authenticated():
            # Если не авторизован, но приветствие ещё не показывали
            if not self.auth_check_done:
                self._check_auth(0)

    def on_leave(self):
        """При выходе с экрана"""
        return super().on_leave()