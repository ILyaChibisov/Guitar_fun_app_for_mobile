# screens/components/top_nav.py
"""
Верхняя панель навигации - заголовок по левому краю
с правильной навигацией назад через screen_state
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
from utils.screen_state import screen_state

logger = get_logger('TopNav')


class TopNav(MDCard):
    """Верхняя панель навигации"""

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
            self.height = dp(64)
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

        # Основной контейнер
        self.container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 1),
            padding=[dp(12), 0, dp(12), 0],
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0]
        )

        # Левая часть - одна иконка
        self.left_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(48),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        # Кнопка меню (настройки) - только для home
        self.menu_btn = MDIconButton(
            icon="tune",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        # Кнопка назад
        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        # Изначально добавляем только меню (home)
        self.left_container.add_widget(self.menu_btn)

        # Заголовок
        self.screen_title = MDLabel(
            text=self._get_screen_title('home'),
            font_size=sp(20),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            size_hint_x=1,
            shorten=True,
            shorten_from="right"
        )

        # Правая часть - две иконки
        self.right_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(100),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        self.home_btn = MDIconButton(
            icon="home",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_home_press,
            pos_hint={'center_y': 0.5}
        )

        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search_press,
            pos_hint={'center_y': 0.5}
        )

        self.profile_btn = MDIconButton(
            icon="account-circle",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_profile_press,
            pos_hint={'center_y': 0.5}
        )

        # Начинаем с home: лупа + профиль
        self.right_container.add_widget(self.search_btn)
        self.right_container.add_widget(self.profile_btn)

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
            'artists_by_letter': '',  # кастомный виджет
            'artist_songs': '',  # кастомный виджет
            'song_detail': '',  # кастомный виджет
            'search_results': 'Результаты поиска',
            'dictionary': 'Словарь',
            'admin': 'Админ панель',
            'search': 'Быстрый поиск',
            'terms_by_letter': '',  # кастомный виджет
            'term_detail': '',  # кастомный виджет
        }
        return titles.get(screen_name, screen_name.capitalize())

    def update_title(self, screen_name: str):
        self.screen_title.text = self._get_screen_title(screen_name)

    def set_custom_title(self, title: str):
        self.screen_title.text = title

    def set_custom_title_widget(self, widget):
        """Устанавливает кастомный виджет в качестве заголовка"""
        if not hasattr(self, '_old_title_widget') or self._old_title_widget is None:
            self._old_title_widget = self.screen_title

        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        if self.screen_title in self.container.children:
            self.container.remove_widget(self.screen_title)

        self.container.add_widget(widget, index=1)
        self.custom_title_widget = widget

        logger.info(f"✅ Установлен кастомный виджет заголовка")

    def clear_custom_title_widget(self):
        """Очищает кастомный виджет и возвращает стандартный заголовок"""
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None
            logger.info("✅ Кастомный виджет заголовка удалён")

        if hasattr(self, '_old_title_widget') and self._old_title_widget:
            if self._old_title_widget not in self.container.children:
                self.container.add_widget(self._old_title_widget, index=1)
                logger.info("✅ Стандартный заголовок восстановлен")

    def set_custom_back_callback(self, callback):
        self._custom_back_callback = callback

    def clear_custom_back_callback(self):
        self._custom_back_callback = None

    def _update_left_button(self, screen_name):
        """Обновляет левую кнопку в зависимости от экрана"""
        self.left_container.clear_widgets()

        logger.info(f"🔧 _update_left_button для экрана: {screen_name}")

        if screen_name == 'home':
            # Home: настройки (tune)
            self.left_container.add_widget(self.menu_btn)
            self.menu_btn.icon = "tune"
            self.menu_btn.on_release = self._on_menu_press
            logger.info("   → Установлена иконка настроек (tune)")
        else:
            # Все остальные экраны - стрелка назад
            self.left_container.add_widget(self.back_btn)
            self.back_btn.on_release = self._on_back_press
            logger.info(f"   → Установлена стрелка назад")

    def _update_right_buttons(self, screen_name):
        """Обновляет правые кнопки: на home показываем лупу, на остальных - дом"""
        self.right_container.clear_widgets()

        if screen_name == 'home':
            self.right_container.add_widget(self.search_btn)
            self.right_container.add_widget(self.profile_btn)
        else:
            self.right_container.add_widget(self.home_btn)
            self.right_container.add_widget(self.profile_btn)

    def _on_screen_changed(self, instance, screen_name):
        old = self.current_screen_name
        self.current_screen_name = screen_name
        logger.info(f"🔄 _on_screen_changed: {old} → {screen_name}")

        # Сохраняем предыдущий экран в screen_state
        if old and old != screen_name:
            screen_state.set_previous_screen(old)
            logger.info(f"   ✅ Сохранён предыдущий экран: {old}")

        if old and old != screen_name:
            self._previous_screen = old

        screens_with_custom_title = ['song_detail', 'terms_by_letter', 'term_detail', 'artists_by_letter',
                                     'artist_songs', 'favorites']

        if screen_name not in screens_with_custom_title:
            if self.custom_title_widget:
                self.clear_custom_title_widget()
                self.update_title(screen_name)

        self._update_left_button(screen_name)

        if screen_name not in screens_with_custom_title:
            if not hasattr(self, 'custom_title_widget') or not self.custom_title_widget:
                self.update_title(screen_name)

        # Очищаем кастомные заголовки при выходе с экранов
        if old in ['terms_by_letter', 'term_detail', 'artist_songs', 'artists_by_letter',
                   'favorites'] and screen_name != old:
            self.clear_custom_title_widget()
            self.update_title(screen_name)

        if old == 'song_detail' and screen_name != 'song_detail':
            self.clear_custom_title_widget()
            self.update_title(screen_name)

        if screen_name != 'chords':
            self.clear_custom_back_callback()

        self._update_right_buttons(screen_name)

    def _on_back_press(self, *args):
        """
        Обработчик нажатия на стрелку назад.
        Использует screen_state для правильной навигации.
        """
        logger.info(f"🔙 _on_back_press для экрана: {self.current_screen_name}")
        logger.info(f"   📌 screen_state.previous_screen = {screen_state.get_previous_screen()}")

        if self._custom_back_callback:
            logger.info("   → Используем кастомный callback")
            self._custom_back_callback()
            return

        if not self.sm:
            return

        current = self.sm.current

        # ============ ИСПОЛЬЗУЕМ screen_state ДЛЯ НАВИГАЦИИ ============

        # 1. Сначала проверяем screen_state.get_previous_screen()
        prev_from_state = screen_state.get_previous_screen()

        # 2. Для SongDetail - особая логика
        if current == 'song_detail':
            # Пытаемся получить предыдущий экран из screen_state
            if prev_from_state and self.sm.has_screen(prev_from_state):
                logger.info(f"   → SongDetail возврат на {prev_from_state} (из screen_state)")
                self.sm.current = prev_from_state
                return

            # Проверяем favourites
            if self.sm.has_screen('favorites'):
                # Проверяем, был ли favourites активен до этого
                if self._previous_screen == 'favorites':
                    logger.info("   → SongDetail возврат на favorites (из _previous_screen)")
                    self.sm.current = 'favorites'
                    return

            # Проверяем artist_songs
            if self.sm.has_screen('artist_songs'):
                if self._previous_screen == 'artist_songs':
                    logger.info("   → SongDetail возврат на artist_songs (из _previous_screen)")
                    self.sm.current = 'artist_songs'
                    return

            # По умолчанию - artists_by_letter
            if self.sm.has_screen('artists_by_letter'):
                logger.info("   → SongDetail возврат на artists_by_letter (по умолчанию)")
                self.sm.current = 'artists_by_letter'
                return

            # Последняя надежда - home
            if self.sm.has_screen('home'):
                logger.info("   → SongDetail возврат на home")
                self.sm.current = 'home'
                return

        # 3. Для остальных экранов - используем карту переходов
        back_map = {
            'artist_songs': 'artists_by_letter',
            'artists_by_letter': 'songs',
            'songs': 'home',
            'favorites': 'home',
            'profile': 'home',
            'admin': 'profile',
            'dictionary': 'home',
            'terms_by_letter': 'dictionary',
            'term_detail': 'terms_by_letter',
            'search': 'home',
            'tuner': 'home',
            'metronome': 'home',
            'chords': self._get_previous_screen_for_chords,
        }

        if current in back_map:
            target = back_map[current]
            if callable(target):
                target = target()
            if target and self.sm.has_screen(target):
                logger.info(f"   → Переход на {target}")
                self.sm.current = target
                return

        # Если ничего не подошло - идём на home
        if self.sm.has_screen('home'):
            logger.info("   → Переход на home (по умолчанию)")
            self.sm.current = 'home'

    def _get_previous_screen_for_chords(self):
        """Возвращает экран для возврата из Chords"""
        prev = screen_state.get_previous_screen()
        if prev and self.sm.has_screen(prev):
            return prev
        return 'home'

    def _on_menu_press(self, *args):
        """Обработчик нажатия на настройки (home)"""
        logger.info("⚙️ Нажата настройки")
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return
        if self.sm and self.sm.has_screen('profile'):
            self.sm.current = 'profile'
        elif self.app and hasattr(self.app, 'open_profile'):
            self.app.open_profile()

    def _on_home_press(self, *args):
        if self.sm and self.sm.has_screen('home'):
            self.sm.current = 'home'

    def _on_search_press(self, *args):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return
        if self.sm and self.sm.has_screen('chords') and self.sm.has_screen('search'):
            chords_screen = self.sm.get_screen('chords')
            search_screen = self.sm.get_screen('search')
            search_screen.set_chords_screen(chords_screen)

            if self.sm.current == 'search':
                search_screen.refresh_search()
            else:
                self.sm.current = 'search'

    def _on_profile_press(self, *args):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'open_profile'):
            app.open_profile()
        else:
            if self.sm and self.sm.has_screen('profile'):
                self.sm.current = 'profile'
                logger.info("Переход на экран профиля (прямой)")
            else:
                logger.warning("Экран 'profile' не найден")

    def set_app(self, app):
        self.app = app

    def reset_to_default(self):
        self.clear_custom_title_widget()
        if self.sm:
            self.update_title(self.sm.current)
            self._update_right_buttons(self.sm.current)
            self._update_left_button(self.sm.current)

    def _show_back_button(self):
        pass

    def _hide_back_button(self):
        pass