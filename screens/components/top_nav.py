# screens/components/top_nav.py (исправленный)

"""
Верхняя панель навигации с тёмным полупрозрачным фоном
- Слева: иконка меню 🍔
- По центру: название текущего экрана
- Справа: поиск 🔍, профиль 👤 и выбор языка
- Фон: тёмный полупрозрачный
"""
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from screens.components.search_dialog import SearchDialog
from config.theme import theme
from config.logger_config import get_logger
from screens.components.language_selector import LanguageSelector

logger = get_logger('UI')


class TopNav(MDCard):
    """Верхняя панель навигации с тёмным полупрозрачным фоном"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.app = None
        self.language_selector = None
        self.current_screen_name = 'home'

        # Настройки карточки (панели)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.radius = [0, 0, 0, 0]  # Прямые углы
        self.md_bg_color = [0, 0, 0, 0]  # Прозрачный, фон добавим через canvas
        self.theme_bg_color = "Custom"
        self.elevation = 0
        self.padding = 0
        self.spacing = 0

        # Тёмный полупрозрачный фон через canvas
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0, 0, 0, 0.3)  # Чёрный с прозрачностью 30%
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Основной горизонтальный контейнер для элементов
        self.container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]
        )

        # ============ ЛЕВАЯ ЧАСТЬ: иконка меню ============
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

        # ============ ЦЕНТР: название текущего экрана ============
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

        # ============ ПРАВАЯ ЧАСТЬ: поиск, профиль и выбор языка ============
        # Контейнер для правых элементов (увеличил ширину)
        self.right_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            width=dp(140),
            height=dp(40),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        # Кнопка поиска (лупа)
        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search_press,
            pos_hint={'center_y': 0.5}
        )

        # Кнопка профиля
        self.profile_btn = MDIconButton(
            icon="account-circle",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_profile_press,
            pos_hint={'center_y': 0.5}
        )

        # LanguageSelector
        self.language_selector = LanguageSelector(
            on_language_change=self._on_language_changed
        )

        # Добавляем в правый контейнер (порядок: поиск, профиль, язык)
        self.right_container.add_widget(self.search_btn)
        self.right_container.add_widget(self.profile_btn)
        self.right_container.add_widget(self.language_selector)

        # Добавляем всё в контейнер
        self.container.add_widget(self.menu_btn)
        self.container.add_widget(self.screen_title)
        self.container.add_widget(self.right_container)

        self.add_widget(self.container)

        # Подписываемся на изменение экранов
        if hasattr(self.sm, 'add_observer'):
            self.sm.add_observer(self._on_screen_changed)
        elif hasattr(self.sm, 'bind'):
            self.sm.bind(current=self._on_screen_changed)

        # Обновляем заголовок при старте
        if self.sm:
            self._on_screen_changed(self.sm, self.sm.current)

        logger.info('TopNav с тёмным полупрозрачным фоном создана')

    def _update_bg(self, *args):
        """Обновляет позицию и размер фонового прямоугольника"""
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def _get_screen_title(self, screen_name: str) -> str:
        """Возвращает название для экрана"""
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
            'admin': 'Админ панель'
        }
        return titles.get(screen_name, screen_name.capitalize())

    def _on_screen_changed(self, instance, screen_name):
        """Обновляет заголовок при смене экрана"""
        self.current_screen_name = screen_name
        self.screen_title.text = self._get_screen_title(screen_name)
        logger.debug(f"Экран изменён: {screen_name}, заголовок: {self.screen_title.text}")

    def _on_menu_press(self, instance):
        """Обработчик нажатия на меню - открытие боковой панели"""
        if self.app and hasattr(self.app, 'open_drawer'):
            self.app.open_drawer(instance)
        else:
            logger.info("Меню нажато - боковая панель будет добавлена позже")

    def _on_profile_press(self, instance):
        """Обработчик нажатия на профиль"""
        if self.app and hasattr(self.app, 'open_profile'):
            self.app.open_profile(instance)
        else:
            if hasattr(self, 'sm') and self.sm and self.sm.has_screen('profile'):
                self.sm.current = 'profile'

    def _on_language_changed(self, lang_code):
        """Обработчик смены языка"""
        if self.app and hasattr(self.app, 'change_language'):
            self.app.change_language(lang_code)

    def _on_search_press(self, instance):
        """Обработчик нажатия на поиск - открытие универсального поиска"""
        # Получаем экран аккордов для поиска аккордов
        chords_screen = None
        if self.sm and self.sm.has_screen('chords'):
            chords_screen = self.sm.get_screen('chords')

        SearchDialog.show(self.sm, chords_screen)

    def set_app(self, app):
        """Устанавливает ссылку на главное приложение"""
        self.app = app

    def get_current_language(self):
        """Возвращает текущий язык"""
        if self.language_selector:
            return self.language_selector.get_current_lang()
        return 'ru'

    def set_current_language(self, lang_code):
        """Устанавливает текущий язык программно"""
        if self.language_selector:
            self.language_selector.set_current_lang(lang_code)

    def update_title(self, screen_name: str):
        """Обновляет заголовок вручную"""
        self.screen_title.text = self._get_screen_title(screen_name)