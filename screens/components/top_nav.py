# screens/components/top_nav.py
"""
Верхняя панель навигации - MDTopAppBar прозрачный с LanguageSelector
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window
from kivy.clock import Clock

from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from config.system_bars import get_status_bar_height, get_screen_density
from screens.components.language_selector import LanguageSelector

logger = get_logger('TopNav')


class TopNav(MDTopAppBar):
    """Верхняя панель навигации - MDTopAppBar прозрачный"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.app = None
        self.language_selector = None
        self.current_screen_name = 'home'
        self._is_back_mode = False

        # Настройки прозрачности
        self.md_bg_color = [0, 0, 0, 0]  # ПОЛНОСТЬЮ ПРОЗРАЧНЫЙ
        self.elevation = 0
        self.radius = [0, 0, 0, 0]

        # Позиция - прижата к верху
        self.pos_hint = {'top': 1}

        # Отступ сверху под статус-бар
        status_h = get_status_bar_height()
        self.padding = [0, status_h, 0, 0]

        # Левая кнопка (меню)
        self.left_action_items = [["menu", lambda x: self._on_menu_press(x)]]

        # Заголовок
        self.title = self._get_screen_title('home')

        # Правая часть: поиск и профиль через action_items
        self.right_action_items = [
            ["magnify", lambda x: self._on_search_press(x)],
            ["account-circle", lambda x: self._on_profile_press(x)]
        ]

        # Добавляем LanguageSelector отдельно
        Clock.schedule_once(self._add_language_selector, 0.1)

        # Подписываемся на смену экранов
        if hasattr(self.sm, 'add_observer'):
            self.sm.add_observer(self._on_screen_changed)
        elif hasattr(self.sm, 'bind'):
            self.sm.bind(current=self._on_screen_changed)

        if self.sm:
            self._on_screen_changed(self.sm, self.sm.current)

        # Отладка
        screen_density = get_screen_density()
        logger.info("=" * 70)
        logger.info(f"📱 TOP NAV (MDTopAppBar прозрачный)")
        logger.info(f"📱 Статус-бар: {status_h}dp ({status_h * screen_density:.0f}px)")
        logger.info("=" * 70)

    def _add_language_selector(self, dt):
        """Добавляет LanguageSelector в правую часть панели"""
        try:
            # Создаём LanguageSelector
            self.language_selector = LanguageSelector(
                on_language_change=self._on_language_changed,
                size_hint=(None, None),
                size=(dp(50), dp(32))
            )

            # Пытаемся найти trailing container и добавить туда
            # В KivyMD 1.2.0 MDTopAppBar имеет内部结构, нужно найти контейнер
            for child in self.children:
                if hasattr(child, 'ids'):
                    if hasattr(child.ids, 'trailing_container'):
                        child.ids.trailing_container.add_widget(self.language_selector)
                        logger.info("LanguageSelector добавлен в trailing_container")
                        return
                # Проверяем детей рекурсивно
                self._add_to_trailing_container(child)

        except Exception as e:
            logger.error(f"Ошибка добавления LanguageSelector: {e}")
            # Альтернативный способ: добавляем в right_action_items как кастомный виджет
            self.right_action_items.append([self._create_language_widget(), None])

    def _add_to_trailing_container(self, widget):
        """Рекурсивно ищет trailing_container и добавляет LanguageSelector"""
        if hasattr(widget, 'ids'):
            if hasattr(widget.ids, 'trailing_container'):
                widget.ids.trailing_container.add_widget(self.language_selector)
                logger.info("LanguageSelector добавлен в trailing_container (рекурсивно)")
                return True
        if hasattr(widget, 'children'):
            for child in widget.children:
                if self._add_to_trailing_container(child):
                    return True
        return False

    def _create_language_widget(self):
        """Создаёт виджет для отображения в right_action_items"""
        # Возвращаем MDIconButton как заглушку
        btn = MDIconButton(
            icon="translate",
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            size_hint=(None, None),
            size=(dp(40), dp(40))
        )
        btn.bind(on_release=lambda x: self._on_language_btn_press())
        return btn

    def _on_language_btn_press(self):
        """Обработчик нажатия на кнопку языка (если LanguageSelector не добавлен)"""
        if self.language_selector and hasattr(self.language_selector, '_open_popup'):
            self.language_selector._open_popup(None)

    def _get_screen_title(self, screen_name: str) -> str:
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
            'admin': 'Админ панель',
            'search': 'Поиск'
        }
        return titles.get(screen_name, screen_name.capitalize())

    def _on_screen_changed(self, instance, screen_name):
        self.current_screen_name = screen_name
        if screen_name != 'artists_by_letter':
            self._hide_back_button()
            self.title = self._get_screen_title(screen_name)
        else:
            self._show_back_button()

    def _on_menu_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return
        if self.app and hasattr(self.app, 'open_drawer'):
            self.app.open_drawer(btn)
        else:
            logger.info("Меню нажато")

    def _on_back_press(self, btn):
        if self.sm:
            self.sm.current = 'songs'
            logger.info("Возврат на экран песен")

    def _on_profile_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return
        if self.app and hasattr(self.app, 'open_profile'):
            self.app.open_profile(btn)
        else:
            if hasattr(self, 'sm') and self.sm and self.sm.has_screen('profile'):
                self.sm.current = 'profile'

    def _on_language_changed(self, lang_code):
        logger.info(f"Язык изменён на: {lang_code}")
        if self.app and hasattr(self.app, 'change_language'):
            self.app.change_language(lang_code)

    def _on_search_press(self, btn):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return
        if self.sm and self.sm.has_screen('chords') and self.sm.has_screen('search'):
            chords_screen = self.sm.get_screen('chords')
            search_screen = self.sm.get_screen('search')
            search_screen.set_chords_screen(chords_screen)
            self.sm.current = 'search'

    def set_app(self, app):
        self.app = app

    def get_current_language(self):
        if self.language_selector:
            return self.language_selector.get_current_lang()
        return 'ru'

    def set_current_language(self, lang_code):
        if self.language_selector:
            self.language_selector.set_current_lang(lang_code)

    def update_title(self, screen_name: str):
        self.title = self._get_screen_title(screen_name)

    def update_for_artists_screen(self, letter: str, show_back_button: bool = True):
        if show_back_button:
            self._show_back_button()
        else:
            self._hide_back_button()
        display = "0-9" if letter in ("digits", "0-9") else letter.upper()
        self.title = f"Буква {display}"
        logger.info(f"TopNav обновлён для экрана исполнителей: {self.title}")

    def reset_to_default(self):
        self._hide_back_button()
        if self.sm:
            self.title = self._get_screen_title(self.sm.current)
        logger.info("TopNav сброшен к стандартному виду")

    def _show_back_button(self):
        self._is_back_mode = True
        self.left_action_items = [["arrow-left", lambda x: self._on_back_press(x)]]

    def _hide_back_button(self):
        self._is_back_mode = False
        self.left_action_items = [["menu", lambda x: self._on_menu_press(x)]]

    def hide_search_button(self, hide: bool = True):
        if hide:
            self.right_action_items = [item for item in self.right_action_items if item[0] != "magnify"]
        else:
            if not any(item[0] == "magnify" for item in self.right_action_items):
                self.right_action_items.insert(0, ["magnify", lambda x: self._on_search_press(x)])

    def hide_profile_button(self, hide: bool = True):
        if hide:
            self.right_action_items = [item for item in self.right_action_items if item[0] != "account-circle"]
        else:
            if not any(item[0] == "account-circle" for item in self.right_action_items):
                self.right_action_items.append(["account-circle", lambda x: self._on_profile_press(x)])

    def reload_config(self):
        """Обновляет конфигурацию при повороте экрана"""
        status_h = get_status_bar_height()
        self.padding = [0, status_h, 0, 0]

        screen_density = get_screen_density()
        logger.info(f"🔄 TopNav | Статус-бар: {status_h}dp ({status_h * screen_density:.0f}px)")