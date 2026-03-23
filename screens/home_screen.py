# screens/home_screen.py
"""
Главный экран: авторизация в карточке, быстрый доступ - кнопками
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import Snackbar
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle
from kivy.utils import rgba
from config.theme import theme
from config.logger_config import screen_logger

logger = screen_logger('Home')


class AuthButton(MDRaisedButton):
    """Кнопка авторизации с иконкой и текстом"""

    def __init__(self, icon, text, bg_color, text_color=[1, 1, 1, 1], **kwargs):
        super().__init__(**kwargs)
        self.icon = icon
        self.text = text
        self.md_bg_color = bg_color
        self.theme_text_color = "Custom"
        self.text_color = text_color
        self.size_hint = (1, None)
        self.height = dp(56)
        self.font_size = dp(16)
        self.ripple_behavior = True
        self.radius = [theme.CORNER_RADIUS_SMALL]

    def on_press(self):
        """Анимация нажатия"""
        anim = Animation(opacity=0.8, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)


class HomeScreen(MDScreen):
    """Главный экран: авторизация в карточке, быстрый доступ - кнопками"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Устанавливаем цвет фона
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_bg, size=self._update_bg)

        # Главный контейнер (скроллируемый)
        scroll = MDScrollView(
            size_hint=(1, 1),
            bar_width=dp(4),
            bar_color=theme.PRIMARY_LIGHT
        )

        # Основной контейнер с отступами
        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20),
            size_hint_y=None,
            adaptive_height=True
        )

        # === Заголовок приложения ===
        title = MDLabel(
            text="GuitarFuns",
            font_style="H3",
            halign="center",
            size_hint_y=None,
            height=dp(100),
            theme_text_color="Primary",
            bold=True
        )

        # === КАРТОЧКА АВТОРИЗАЦИИ ===
        auth_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(220),
            padding=dp(16),
            spacing=dp(12),
            elevation=4,
            radius=[theme.CORNER_RADIUS],
            md_bg_color=theme.SURFACE
        )

        # Заголовок карточки авторизации
        auth_title = MDLabel(
            text="Авторизация",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Primary",
            bold=True
        )

        # Кнопка авторизации через Google
        google_btn = AuthButton(
            icon="google",
            text="Войти через Google",
            bg_color=[0.96, 0.96, 0.96, 1],
            text_color=[0.2, 0.2, 0.2, 1]
        )
        google_btn.bind(on_release=self.login_google)

        # Кнопка авторизации через ВКонтакте
        vk_btn = AuthButton(
            icon="vk",
            text="Войти через ВКонтакте",
            bg_color=[0.27, 0.55, 0.76, 1],
            text_color=[1, 1, 1, 1]
        )
        vk_btn.bind(on_release=self.login_vk)

        # Собираем карточку авторизации
        auth_card.add_widget(auth_title)
        auth_card.add_widget(google_btn)
        auth_card.add_widget(vk_btn)

        # === БЛОК БЫСТРОГО ДОСТУПА (без карточки, просто кнопки) ===
        quick_title = MDLabel(
            text="Быстрый доступ",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Primary",
            bold=True
        )

        # Контейнер для кнопок быстрого доступа
        buttons_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(170)
        )

        # Кнопка тюнера
        tuner_btn = MDRaisedButton(
            text="Открыть тюнер",
            icon="tune",
            size_hint=(0.8, None),
            height=dp(48),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=lambda x: self.navigate_to('tuner')
        )
        tuner_btn.radius = [theme.CORNER_RADIUS_SMALL]

        # Кнопка списка песен
        songs_btn = MDRaisedButton(
            text="Список песен",
            icon="music-note",
            size_hint=(0.8, None),
            height=dp(48),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=lambda x: self.navigate_to('songs')
        )
        songs_btn.radius = [theme.CORNER_RADIUS_SMALL]

        # Кнопка аккордов
        chords_btn = MDRaisedButton(
            text="Аккорды",
            icon="guitar-acoustic",
            size_hint=(0.8, None),
            height=dp(48),
            pos_hint={"center_x": 0.5},
            md_bg_color=theme.PRIMARY,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=lambda x: self.navigate_to('chords')
        )
        chords_btn.radius = [theme.CORNER_RADIUS_SMALL]

        buttons_layout.add_widget(tuner_btn)
        buttons_layout.add_widget(songs_btn)
        buttons_layout.add_widget(chords_btn)

        # === Добавляем все элементы в layout ===
        layout.add_widget(title)
        layout.add_widget(auth_card)
        layout.add_widget(quick_title)
        layout.add_widget(buttons_layout)

        # Добавляем небольшой отступ снизу
        spacer = MDBoxLayout(size_hint_y=None, height=dp(20))
        layout.add_widget(spacer)

        scroll.add_widget(layout)
        self.add_widget(scroll)

        logger.info('Главный экран создан: авторизация в карточке, быстрый доступ - кнопками')

    def _update_bg(self, *args):
        """Обновляет фон при изменении размера"""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def navigate_to(self, screen_name):
        """Переход к другому экрану"""
        if hasattr(self, 'manager') and self.manager:
            logger.info(f'Переход на экран: {screen_name}')
            self.manager.current = screen_name
        else:
            logger.error(f'Невозможно перейти на {screen_name}: менеджер экранов не найден')

    def login_google(self, instance):
        """Обработчик авторизации через Google"""
        logger.info("Попытка входа через Google")
        Snackbar(
            text="🔐 Вход через Google будет доступен в следующей версии",
            duration=2,
            snackbar_x="10dp",
            snackbar_y="10dp",
            radius=[theme.CORNER_RADIUS_SMALL]
        ).open()

    def login_vk(self, instance):
        """Обработчик авторизации через ВКонтакте"""
        logger.info("Попытка входа через ВКонтакте")
        Snackbar(
            text="🔐 Вход через ВКонтакте будет доступен в следующей версии",
            duration=2,
            snackbar_x="10dp",
            snackbar_y="10dp",
            radius=[theme.CORNER_RADIUS_SMALL]
        ).open()