# screens/components/top_nav.py
"""
Верхняя панель навигации - заголовок по левому краю
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

        # Левая часть (бутерброд и кнопка назад)
        self.left_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(96),
            spacing=dp(4),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        self.menu_btn = MDIconButton(
            icon="menu",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_menu_press,
            pos_hint={'center_y': 0.5}
        )

        self.back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_back_press,
            pos_hint={'center_y': 0.5},
            opacity=0,
            disabled=True
        )

        self.left_container.add_widget(self.menu_btn)
        self.left_container.add_widget(self.back_btn)

        # Заголовок (растягивается)
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

        # Правая часть
        self.right_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(100),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        # Иконка "Дом"
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

        # Иконка "Лупа" (для поиска, только на home)
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

        # Иконка "Профиль"
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

        # Начинаем с home экрана: лупа + профиль
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
            'artists_by_letter': 'Исполнители',
            'artist_songs': 'Песни',
            'song_detail': 'Текст песни',
            'search_results': 'Результаты поиска',
            'dictionary': 'Словарь',
            'admin': 'Админ панель',
            'search': 'Быстрый поиск',
            'terms_by_letter': '',  # пусто, т.к. используется кастомный виджет
            'term_detail': '',  # пусто, т.к. используется кастомный виджет
        }
        return titles.get(screen_name, screen_name.capitalize())

    def update_title(self, screen_name: str):
        self.screen_title.text = self._get_screen_title(screen_name)

    def set_custom_title(self, title: str):
        self.screen_title.text = title

    def set_custom_title_widget(self, widget):
        """Устанавливает кастомный виджет в качестве заголовка"""
        # Сохраняем старый виджет если его нет
        if not hasattr(self, '_old_title_widget') or self._old_title_widget is None:
            self._old_title_widget = self.screen_title

        # Удаляем старый кастомный виджет если есть
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        # Удаляем стандартный заголовок из контейнера
        if self.screen_title in self.container.children:
            self.container.remove_widget(self.screen_title)

        # Добавляем новый кастомный виджет
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

        # Восстанавливаем стандартный заголовок
        if hasattr(self, '_old_title_widget') and self._old_title_widget:
            if self._old_title_widget not in self.container.children:
                self.container.add_widget(self._old_title_widget, index=1)
                logger.info("✅ Стандартный заголовок восстановлен")

    def set_custom_back_callback(self, callback):
        self._custom_back_callback = callback

    def clear_custom_back_callback(self):
        self._custom_back_callback = None

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
        if old and old != screen_name:
            self._previous_screen = old

        # Сбрасываем кастомный заголовок для экранов, где он не нужен
        # Экран terms_by_letter использует кастомный виджет (буква + количество)
        # Экран term_detail использует кастомный заголовок (название термина)
        # Song_detail использует кастомный виджет (название песни + артист)
        screens_with_custom_title = ['song_detail', 'terms_by_letter', 'term_detail']

        # Если текущий экран НЕ использует кастомный заголовок - очищаем
        if screen_name not in screens_with_custom_title:
            if self.custom_title_widget:
                self.clear_custom_title_widget()
                self.update_title(screen_name)

        # Обработка кнопки назад
        if screen_name not in ['artists_by_letter', 'artist_songs', 'song_detail', 'search_results', 'chords',
                               'terms_by_letter', 'term_detail']:
            self._hide_back_button()
            if not hasattr(self, 'custom_title_widget') or not self.custom_title_widget:
                self.update_title(screen_name)
        else:
            self._show_back_button()
            if screen_name == 'chords':
                self.screen_title.text = "Аккорды"
            elif screen_name == 'song_detail':
                pass  # заголовок устанавливается в set_custom_title_widget
            elif screen_name == 'terms_by_letter':
                pass  # заголовок устанавливается в set_custom_title_widget
            elif screen_name == 'term_detail':
                pass  # заголовок устанавливается в set_custom_title_widget
            else:
                if not hasattr(self, 'custom_title_widget') or not self.custom_title_widget:
                    self.update_title(screen_name)

        # Специальный случай: при выходе с terms_by_letter или term_detail очищаем кастомный виджет
        if old == 'terms_by_letter' and screen_name != 'terms_by_letter':
            self.clear_custom_title_widget()
            self.update_title(screen_name)

        if old == 'term_detail' and screen_name != 'term_detail':
            self.clear_custom_title_widget()
            self.update_title(screen_name)

        if old == 'song_detail' and screen_name != 'song_detail':
            self.clear_custom_title_widget()
            self.update_title(screen_name)

        if screen_name != 'chords':
            self.clear_custom_back_callback()

        self._update_right_buttons(screen_name)

    def _on_menu_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return
        if self.app and hasattr(self.app, 'open_drawer'):
            self.app.open_drawer(btn)

    def _on_back_press(self, btn):
        if self._custom_back_callback:
            self._custom_back_callback()
            return

        if not self.sm:
            return

        current = self.sm.current

        if current == 'chords':
            previous_screen = screen_state.get_previous_screen()
            if previous_screen and self.sm.has_screen(previous_screen):
                self.sm.current = previous_screen
                return

        if hasattr(self, '_previous_screen') and self._previous_screen:
            target = self._previous_screen
            self.sm.current = target
            self._previous_screen = None
        else:
            back_map = {
                'artists_by_letter': 'songs',
                'artist_songs': 'artists_by_letter',
                'song_detail': 'artist_songs',
                'search_results': 'songs',
                'profile': 'home',
                'admin': 'profile',
                'terms_by_letter': 'dictionary',
                'term_detail': 'terms_by_letter',
            }
            target = back_map.get(current, 'songs')
            self.sm.current = target

    def _on_home_press(self, btn):
        """Переход на главную страницу"""
        if self.sm and self.sm.has_screen('home'):
            self.sm.current = 'home'

    def _on_search_press(self, btn):
        """Поиск (только на главном экране)"""
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

    def _on_profile_press(self, btn):
        """Переход на страницу профиля через единую логику приложения"""
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

    def update_for_artists_screen(self, letter: str, show_back_button: bool = True):
        if show_back_button:
            self._show_back_button()
        else:
            self._hide_back_button()
        display = "0-9" if letter in ("digits", "0-9") else letter.upper()
        self.screen_title.text = f"Буква {display}"

    def reset_to_default(self):
        """Сбрасывает заголовок на стандартный"""
        self.clear_custom_title_widget()
        self._hide_back_button()
        self.clear_custom_back_callback()
        if self.sm:
            self.update_title(self.sm.current)
            self._update_right_buttons(self.sm.current)

    def _show_back_button(self):
        self.back_btn.opacity = 1
        self.back_btn.disabled = False

    def _hide_back_button(self):
        self.back_btn.opacity = 0
        self.back_btn.disabled = True