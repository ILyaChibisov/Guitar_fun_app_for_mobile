# screens/components/top_nav.py
"""
Верхняя панель навигации - заголовок по центру
с правильной навигацией назад через screen_state
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window

from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.app import MDApp
from kivy.clock import Clock

from config.theme import theme
from config.logger_config import get_logger
from config.system_bars import get_status_bar_height, get_screen_density
from utils.screen_state import screen_state

logger = get_logger('TopNav')


class TopNav(MDCard):
    """Верхняя панель навигации"""

    # Список экранов, где всегда показывается стрелка назад
    ALWAYS_BACK_SCREENS = [
        'song_detail',
        'term_detail',
        'admin',
        'task_detail',
        'amdm_parser',
        'mytabs_parser',
        'accord_pro_parser',
        'akkordus_parser',
        'muzland_parser',
        'chordie_parser',
        'fivelad_parser',
        'akkordbard_parser',
        'domhve_parser',
        'rushsound_parser',
        'settings',
        'help',
        'promo',
        'feedback',
    ]

    # Список экранов с кастомным заголовком
    CUSTOM_TITLE_SCREENS = [
        'song_detail',
        'terms_by_letter',
        'term_detail',
        'artists_by_letter',
        'artist_songs',
        'favorites',
    ]

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

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.pos_hint = {'top': 1}

        status_h = get_status_bar_height()

        if platform == 'android':
            self.height = dp(88)
            top_padding = status_h + dp(24)
        else:
            self.height = dp(80)
            top_padding = status_h + dp(8)

        self.padding = [0, top_padding, 0, 0]

        self.radius = [0, 0, 0, 0]
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.spacing = 0

        screen_density = get_screen_density()
        logger.info("=" * 70)
        logger.info(f"📱 TOP NAV - {platform.upper()}")
        logger.info(f"📱 Статус-бар: {status_h:.1f}dp = {status_h * screen_density:.0f}px")
        logger.info(f"📱 Отступ сверху: {top_padding:.1f}dp")
        logger.info(f"📱 Высота панели: {self.height}dp")
        logger.info("=" * 70)

        # ============ ИСПОЛЬЗУЕМ FLOATLAYOUT ДЛЯ ТОЧНОГО ЦЕНТРИРОВАНИЯ ============
        self.container = MDFloatLayout(
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )

        # Левая часть - плавает слева
        self.left_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(48),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'x': 0, 'center_y': 0.5}
        )

        # Кнопка настроек (шестерёнка) - теперь открывает Sidebar
        self.settings_btn = MDIconButton(
            icon="tune",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )
        # ❌ УБИРАЕМ bind - обработчик будет установлен из main.py
        # self.settings_btn.bind(on_release=self._on_settings_press)

        # Кнопка назад (стрелка) - возврат на предыдущий экран
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

        # Изначально добавляем настройки (home)
        self.left_container.add_widget(self.settings_btn)

        # ============ ЗАГОЛОВОК - ПО ЦЕНТРУ ============
        self.screen_title = MDLabel(
            text=self._get_screen_title('home'),
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

        # Правая часть - плавает справа
        self.right_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(48),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'right': 1, 'center_y': 0.5}
        )

        # Кнопка домой - возврат на главный экран
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

        # Кнопка поиска - переход на экран поиска
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

        # Начинаем с home: лупа
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

    def _get_screen_title(self, screen_name: str) -> str:
        titles = {
            'home': 'Главная',
            'songs': 'Песни',
            'chords': 'Аккорды',
            'tuner': 'Тюнер',
            'metronome': 'Метроном',
            'favorites': 'Избранное',
            'profile': 'Профиль',
            'dictionary': 'Словарь',
            'admin': 'Админ панель',
            'search': 'Быстрый поиск',
            'song_detail': '',
            'term_detail': 'Термин',
            'settings': 'Настройки',
            'help': 'Помощь',
            'promo': 'Промокод',
            'feedback': 'Обратная связь',
        }
        return titles.get(screen_name, screen_name.capitalize())

    def update_title(self, screen_name: str):
        self.screen_title.text = self._get_screen_title(screen_name)
        self._adjust_title_width()

    def set_custom_title(self, title: str):
        self.screen_title.text = title
        self._adjust_title_width()

    def _adjust_title_width(self):
        """Адаптирует ширину заголовка под длину текста"""
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
        """Устанавливает кастомный виджет в качестве заголовка"""
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
        """Очищает кастомный виджет и возвращает стандартный заголовок"""
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None
            logger.info("✅ Кастомный виджет заголовка удалён")

        if self.screen_title not in self.container.children:
            self.container.add_widget(self.screen_title)
            self._adjust_title_width()
            logger.info("✅ Стандартный заголовок восстановлен")

    def set_custom_back_callback(self, callback):
        self._custom_back_callback = callback

    def clear_custom_back_callback(self):
        self._custom_back_callback = None

    def _update_left_button(self, screen_name):
        """Обновляет левую кнопку в зависимости от экрана."""
        self.left_container.clear_widgets()

        logger.info(f"🔧 _update_left_button для экрана: {screen_name}")

        # 1. Всегда показываем стрелку на этих экранах
        if screen_name in self.ALWAYS_BACK_SCREENS:
            self.left_container.add_widget(self.back_btn)
            logger.info("   → Установлена стрелка назад (всегда)")
            return

        # 2. Специальная логика для chords
        if screen_name == 'chords':
            previous_screen = screen_state.get_previous_screen()
            if previous_screen == 'search':
                self.left_container.add_widget(self.back_btn)
                logger.info("   → Установлена стрелка назад (пришли из search)")
                return
            else:
                self.left_container.add_widget(self.settings_btn)
                # ❌ НЕ добавляем bind здесь
                logger.info("   → Установлена иконка настроек")
                return

        # 3. Все остальные экраны — показываем настройки
        self.left_container.add_widget(self.settings_btn)
        # ❌ НЕ добавляем bind здесь
        logger.info("   → Установлена иконка настроек")

    def _update_right_buttons(self, screen_name):
        """Обновляет правые кнопки"""
        self.right_container.clear_widgets()

        if screen_name == 'home':
            self.right_container.add_widget(self.search_btn)
            logger.info("   → Установлена лупа (поиск)")
        else:
            self.right_container.add_widget(self.home_btn)
            logger.info("   → Установлена иконка домой")

    def _on_screen_changed(self, instance, screen_name):
        old = self.current_screen_name
        self.current_screen_name = screen_name
        logger.info(f"🔄 _on_screen_changed: {old} → {screen_name}")

        if old and old != screen_name:
            screen_state.set_previous_screen(old)
            logger.info(f"   ✅ Сохранён предыдущий экран: {old}")

        if old and old != screen_name:
            self._previous_screen = old

        # ============ СБРАСЫВАЕМ КАСТОМНЫЙ CALLBACK ============
        if screen_name not in self.ALWAYS_BACK_SCREENS:
            if screen_name == 'chords':
                prev = screen_state.get_previous_screen()
                if prev != 'search':
                    self._custom_back_callback = None
                    logger.info("   → Сброшен custom callback (chords, не из search)")
            else:
                self._custom_back_callback = None
                logger.info(f"   → Сброшен custom callback ({screen_name})")

        # Обновляем левую кнопку
        self._update_left_button(screen_name)

        # Обновляем правые кнопки
        self._update_right_buttons(screen_name)

        # ============ ОБНОВЛЯЕМ BOTTOM NAV ============
        app = MDApp.get_running_app()
        if app and hasattr(app, 'bottom_nav') and app.bottom_nav:
            nav_screens = ['songs', 'chords', 'tuner', 'metronome', 'favorites']
            if screen_name in nav_screens:
                for item, (_, _, screen) in zip(app.bottom_nav.items, app.bottom_nav.nav_items):
                    item.active = (screen == screen_name)
            else:
                app.bottom_nav.clear_active()
                logger.info(f"🔽 BottomNav: экран '{screen_name}' не в меню, все иконки сброшены")

        # Если экран НЕ с кастомным заголовком - обновляем стандартный
        if screen_name not in self.CUSTOM_TITLE_SCREENS:
            if self.custom_title_widget:
                self.clear_custom_title_widget()
            self.update_title(screen_name)
        else:
            if screen_name == 'term_detail':
                if self.custom_title_widget:
                    self.clear_custom_title_widget()
                self.set_custom_title("Термин")
            elif screen_name == 'song_detail':
                pass  # song_detail сам управляет заголовком

        if old in self.CUSTOM_TITLE_SCREENS and screen_name not in self.CUSTOM_TITLE_SCREENS:
            self.clear_custom_title_widget()
            self.update_title(screen_name)

    def _on_back_press(self, *args):
        """Обработчик нажатия на стрелку назад."""
        logger.info(f"🔙 _on_back_press для экрана: {self.current_screen_name}")

        if self._custom_back_callback:
            logger.info("   → Используем кастомный callback")
            self._custom_back_callback()
            return

        if not self.sm:
            return

        current = self.sm.current
        prev_from_state = screen_state.get_previous_screen()
        logger.info(f"   📌 screen_state.previous_screen = {prev_from_state}")

        # ============ ЛОГИКА ДЛЯ song_detail ============
        if current == 'song_detail':
            if prev_from_state and self.sm.has_screen(prev_from_state):
                if prev_from_state in ['songs', 'favorites', 'search', 'chords']:
                    logger.info(f"   → SongDetail возврат на {prev_from_state}")
                    self.sm.current = prev_from_state
                    return

            if self.sm.has_screen('home'):
                logger.info("   → SongDetail возврат на home (по умолчанию)")
                self.sm.current = 'home'
                return

        # ============ ЛОГИКА ДЛЯ term_detail ============
        if current == 'term_detail':
            if prev_from_state and self.sm.has_screen(prev_from_state):
                if prev_from_state in ['dictionary', 'search']:
                    logger.info(f"   → TermDetail возврат на {prev_from_state}")
                    self.sm.current = prev_from_state
                    return

            if self.sm.has_screen('dictionary'):
                logger.info("   → TermDetail возврат на dictionary (по умолчанию)")
                self.sm.current = 'dictionary'
                return
            elif self.sm.has_screen('home'):
                logger.info("   → TermDetail возврат на home")
                self.sm.current = 'home'
                return

        # ============ ЛОГИКА ДЛЯ chords ============
        if current == 'chords':
            if prev_from_state == 'search' and self.sm.has_screen('search'):
                logger.info("   → Chords возврат на search")
                self.sm.current = 'search'
                return

            if self.sm.has_screen('home'):
                logger.info("   → Chords возврат на home")
                self.sm.current = 'home'
                return

        # ============ ЛОГИКА ДЛЯ admin и парсеров ============
        if current == 'admin':
            if self.sm.has_screen('profile'):
                logger.info("   → Admin возврат на profile")
                self.sm.current = 'profile'
                return

        if current in self.ALWAYS_BACK_SCREENS and current not in ['song_detail', 'term_detail', 'admin']:
            if self.sm.has_screen('admin'):
                logger.info(f"   → {current} возврат на admin")
                self.sm.current = 'admin'
                return

        # ============ ЛОГИКА ДЛЯ НОВЫХ ЭКРАНОВ ============
        if current in ['settings', 'help', 'promo', 'feedback']:
            if self.sm.has_screen('home'):
                logger.info(f"   → {current} возврат на home")
                self.sm.current = 'home'
                return

        # ============ ПО УМОЛЧАНИЮ ============
        if self.sm.has_screen('home'):
            logger.info("   → Переход на home (по умолчанию)")
            self.sm.current = 'home'

    def _on_settings_press(self, *args):
        """Обработчик нажатия на иконку настроек (шестерёнка) - открывает Sidebar"""
        logger.info("⚙️ Нажата иконка настроек → открываем Sidebar")
        app = MDApp.get_running_app()
        if hasattr(app, 'sidebar') and app.sidebar:
            app.sidebar.toggle()

    def _on_home_press(self, *args):
        """Обработчик нажатия на иконку домой"""
        logger.info("🏠 Нажата иконка домой")
        if self.sm and self.sm.has_screen('home'):
            self.sm.current = 'home'

    def _on_search_press(self, *args):
        """Обработчик нажатия на иконку поиска"""
        logger.info("🔍 Нажата иконка поиска")
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

        if self.sm and self.sm.has_screen('search'):
            if self.sm.has_screen('chords'):
                chords_screen = self.sm.get_screen('chords')
                search_screen = self.sm.get_screen('search')
                search_screen.set_chords_screen(chords_screen)

            if self.sm.has_screen('dictionary'):
                dictionary_screen = self.sm.get_screen('dictionary')
                search_screen = self.sm.get_screen('search')
                search_screen.set_dictionary_screen(dictionary_screen)

            if self.sm.current == 'search':
                search_screen = self.sm.get_screen('search')
                search_screen.refresh_search()
            else:
                self.sm.current = 'search'

    def set_app(self, app):
        self.app = app

    def reset_to_default(self):
        self.clear_custom_title_widget()
        if self.sm:
            self.update_title(self.sm.current)
            self._update_right_buttons(self.sm.current)
            self._update_left_button(self.sm.current)

    def on_size(self, *args):
        """При изменении размера обновляем ширину заголовка"""
        Clock.schedule_once(lambda dt: self._adjust_title_width(), 0.1)