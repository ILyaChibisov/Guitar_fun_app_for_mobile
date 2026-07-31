# screens/components/top_nav.py
"""
Верхняя панель навигации - с конфигом из top_nav_config.py
"""
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.core.window import Window
from kivy.clock import Clock

from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from config.system_bars import get_status_bar_height, get_screen_density
from config.top_nav_config import top_nav_config
from utils.screen_state import screen_state

logger = get_logger('TopNav')


class TopNav(MDCard):
    """Верхняя панель навигации с конфигом"""

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

        # Флаги для управления навигацией
        self._just_returned_from_song_detail = False
        self._block_navigation = False  # ← ДОБАВЛЕНО
        self._going_back = False
        self._navigating = False

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.pos_hint = {'top': 1}

        # ============ ПРАВИЛЬНЫЙ РАСЧЁТ ВЫСОТЫ И ОТСТУПОВ ============
        status_h = get_status_bar_height()

        if platform == 'android':
            self.height = dp(88) + status_h
            top_padding = status_h + dp(24)
        else:
            self.height = dp(80)
            top_padding = status_h + dp(8)

        self.padding = [0, top_padding, 0, 0]
        self.radius = [0, 0, 0, 0]
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.spacing = 0

        logger.info("=" * 70)
        logger.info(f"📱 TOP NAV - {platform.upper()}")
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

        # Кнопка настроек (шестерёнка) - открывает Sidebar
        self.settings_btn = MDIconButton(
            icon="tune",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )
        self.settings_btn.bind(on_release=self._on_settings_press)

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
        """Возвращает заголовок из конфига"""
        return top_nav_config.get_title(screen_name)

    def update_title(self, screen_name: str):
        """Обновляет заголовок из конфига"""
        title = self._get_screen_title(screen_name)
        self.screen_title.text = title
        self._adjust_title_width()

    def set_custom_title(self, title: str):
        """Устанавливает кастомный заголовок"""
        self.screen_title.text = title
        self._adjust_title_width()

        if title == "Избранное":
            if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
                if self.custom_title_widget in self.container.children:
                    self.container.remove_widget(self.custom_title_widget)
                self.custom_title_widget = None

            if self.screen_title not in self.container.children:
                self.container.add_widget(self.screen_title)
                self._adjust_title_width()

    def _adjust_title_width(self):
        """Подстраивает ширину заголовка"""
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
        """Устанавливает кастомный виджет заголовка"""
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
        """Удаляет кастомный виджет заголовка"""
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
        """Устанавливает кастомный callback для кнопки назад"""
        self._custom_back_callback = callback

    def clear_custom_back_callback(self):
        """Удаляет кастомный callback"""
        self._custom_back_callback = None

    def _update_left_button(self, screen_name: str):
        self.left_container.clear_widgets()

        # СПИСОК ЭКРАНОВ, ГДЕ ВСЕГДА БУРГЕР
        nav_screens_with_hamburger = [
            'songs', 'chords', 'tuner', 'metronome', 'favorites', 'dictionary',
            'profile', 'settings', 'help', 'promo', 'feedback',
            'admin'
        ]

        if screen_name in nav_screens_with_hamburger:
            self.left_container.add_widget(self.settings_btn)
            logger.info(f"🔧 Для {screen_name} установлена кнопка HAMBURGER")
        else:
            left_type = top_nav_config.get_left_button(screen_name)
            logger.info(f"🔧 _update_left_button для экрана: {screen_name} → {left_type}")

            if left_type == top_nav_config.LEFT_BUTTON_BACK:
                self.left_container.add_widget(self.back_btn)
            elif left_type == top_nav_config.LEFT_BUTTON_HAMBURGER:
                self.left_container.add_widget(self.settings_btn)
            else:
                pass

    def _update_right_buttons(self, screen_name: str):
        """Обновляет правую кнопку согласно конфигу"""
        self.right_container.clear_widgets()

        # СПИСОК ЭКРАНОВ, ГДЕ ВСЕГДА ДОМИК
        nav_screens_with_home = ['songs', 'chords', 'tuner', 'metronome', 'favorites', 'dictionary']

        if screen_name in nav_screens_with_home:
            # Для этих экранов всегда показываем домик
            self.right_container.add_widget(self.home_btn)
            logger.info(f"🔧 Для {screen_name} установлена кнопка HOME")
        else:
            right_type = top_nav_config.get_right_button(screen_name)
            logger.info(f"🔧 _update_right_buttons для экрана: {screen_name} → {right_type}")

            if right_type == top_nav_config.RIGHT_BUTTON_SEARCH:
                self.right_container.add_widget(self.search_btn)
            elif right_type == top_nav_config.RIGHT_BUTTON_HOME:
                self.right_container.add_widget(self.home_btn)
            else:
                pass

    def _set_artist_songs_mode(self):
        """Принудительно устанавливает режим для artist_songs"""
        logger.info("🔧 _set_artist_songs_mode: устанавливаем стрелку назад и заголовок")

        self.left_container.clear_widgets()
        self.left_container.add_widget(self.back_btn)
        self.back_btn.on_release = self._on_back_press

        self.right_container.clear_widgets()
        self.right_container.add_widget(self.home_btn)

        self.set_custom_title("Песни исполнителя")

        logger.info("✅ artist_songs режим установлен")

    def _on_screen_changed(self, instance, screen_name):
        """Обработчик смены экрана"""
        # ============ БЛОКИРОВКА НАВИГАЦИИ ============
        if self._block_navigation:
            logger.info("⏭️ Навигация заблокирована, пропускаем смену экрана")
            return

        old = self.current_screen_name

        # ============ ДИАГНОСТИКА ============
        import traceback
        logger.info(f"🔍 _on_screen_changed: {old} → {screen_name}")
        logger.info(f"   Стек вызовов:")
        stack = traceback.format_stack()[-6:-1]
        for line in stack:
            line = line.strip()
            if len(line) > 150:
                line = line[:150] + "..."
            logger.info(f"     {line}")
        # =====================================

        if old == screen_name:
            logger.debug(f"⏭️ Экран не изменился: {screen_name}, пропускаем")
            return

        # ✅ Сначала обновляем текущий экран
        self.current_screen_name = screen_name
        logger.info(f"🔄 _on_screen_changed: {old} → {screen_name}")

        # ============ СОХРАНЯЕМ ПРЕДЫДУЩИЙ ЭКРАН ============
        if old and old != screen_name:
            if screen_name == 'artist_songs' and old == 'song_detail':
                logger.info(f"   ⏭️ Возврат в artist_songs, не меняем previous_screen")
            else:
                screen_state.set_previous_screen(old)
                logger.info(f"   ✅ Сохранён предыдущий экран: {old}")

        if old and old != screen_name:
            self._previous_screen = old

        # ============ ОБНОВЛЯЕМ КНОПКИ ============
        if screen_name == 'artist_songs':
            self._set_artist_songs_mode()
        else:
            self._update_left_button(screen_name)
            self._update_right_buttons(screen_name)

        # ============ ОБНОВЛЯЕМ ЗАГОЛОВОК ============
        if screen_name == 'artist_songs':
            # Заголовок уже установлен в _set_artist_songs_mode
            pass
        else:
            title_type = top_nav_config.get_custom_title_widget_type(screen_name)
            if title_type == 'vertical' and screen_name not in ['song_detail']:
                pass
            elif top_nav_config.is_title_custom(screen_name):
                if self.custom_title_widget:
                    self.clear_custom_title_widget()
                self.update_title(screen_name)
            else:
                if self.custom_title_widget:
                    self.clear_custom_title_widget()
                self.update_title(screen_name)

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

    def _on_back_press(self, *args):
        """Обработчик нажатия кнопки назад"""
        # ============ БЛОКИРОВКА НАВИГАЦИИ ============
        if self._block_navigation:
            logger.info("⏭️ Навигация заблокирована, пропускаем")
            return

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

        # СПИСОК ЭКРАНОВ, ГДЕ КНОПКА НАЗАД НЕ РАБОТАЕТ (нижняя навигация)
        nav_screens = ['songs', 'chords', 'tuner', 'metronome', 'favorites', 'dictionary']

        # СПИСОК ПАРСЕРОВ — они должны возвращать на admin
        parser_screens = [
            'amdm_parser', 'mytabs_parser', 'accord_pro_parser',
            'akkordus_parser', 'muzland_parser', 'chordie_parser',
            'fivelad_parser', 'akkordbard_parser', 'domhve_parser',
            'rushsound_parser'
        ]

        # ============ Если экран из нижней навигации — игнорируем ============
        if current in nav_screens:
            logger.info(f"   ⏭️ Экран '{current}' не поддерживает кнопку назад, игнорируем")
            return

        # ============ Если экран парсера — возвращаем на admin ============
        if current in parser_screens:
            logger.info(f"   → Парсер '{current}' возвращает на admin")
            if self.sm.has_screen('admin'):
                self._block_navigation = True  # Блокируем последующие переходы
                self.sm.current = 'admin'
                Clock.schedule_once(lambda dt: setattr(self, '_block_navigation', False), 0.5)
            else:
                self.sm.current = 'home'
            return

        # ============ artist_songs → всегда на songs ============
        if current == 'artist_songs':
            # Проверяем, не только ли мы вернулись из song_detail
            if hasattr(self, '_just_returned_from_song_detail') and self._just_returned_from_song_detail:
                logger.info("   ⏭️ Только что вернулись из song_detail, пропускаем повторный возврат")
                self._just_returned_from_song_detail = False
                return

            if self._navigating:
                logger.info("⏭️ Уже выполняется навигация, пропускаем")
                return
            self._navigating = True

            if self.sm.has_screen('artist_songs'):
                artist_screen = self.sm.get_screen('artist_songs')
                if hasattr(artist_screen, 'go_back'):
                    artist_screen.go_back()
                    logger.info("   → artist_songs возврат на songs через go_back")
                    Clock.schedule_once(lambda dt: setattr(self, '_navigating', False), 0.5)
                    return

            if self.sm.has_screen('songs'):
                songs_screen = self.sm.get_screen('songs')
                Clock.schedule_once(lambda dt: songs_screen.restore_state(), 0.1)
                self.sm.current = 'songs'
                logger.info("   → artist_songs возврат на songs (fallback)")
                Clock.schedule_once(lambda dt: setattr(self, '_navigating', False), 0.5)
                return
            else:
                self.sm.current = 'home'
                logger.info("   → artist_songs возврат на home (songs не найден)")
                Clock.schedule_once(lambda dt: setattr(self, '_navigating', False), 0.5)
                return

        # ============ song_detail → на предыдущий экран ============
        if current == 'song_detail':
            # Устанавливаем флаг, что мы только что вернулись из song_detail
            self._just_returned_from_song_detail = True

            if self.sm.has_screen('song_detail'):
                song_detail = self.sm.get_screen('song_detail')
                if hasattr(song_detail, 'go_back'):
                    song_detail.go_back()
                    logger.info("   → song_detail возврат через go_back")
                    Clock.schedule_once(lambda dt: setattr(self, '_just_returned_from_song_detail', False), 0.5)
                    return

            if prev_from_state and self.sm.has_screen(prev_from_state):
                logger.info(f"   → song_detail возврат на {prev_from_state}")
                self.sm.current = prev_from_state
                Clock.schedule_once(lambda dt: setattr(self, '_just_returned_from_song_detail', False), 0.5)
                return

            if self.sm.has_screen('home'):
                logger.info("   → song_detail возврат на home (по умолчанию)")
                self.sm.current = 'home'
                Clock.schedule_once(lambda dt: setattr(self, '_just_returned_from_song_detail', False), 0.5)
                return

        # ============ chord_detail → на search или chords ============
        if current == 'chord_detail':
            if self.sm.has_screen('search'):
                screen_state.clear_pending_chord()
                self.sm.current = 'search'
                logger.info("   → chord_detail возврат на search")
                return
            elif self.sm.has_screen('chords'):
                self.sm.current = 'chords'
                logger.info("   → chord_detail возврат на chords")
                return
            else:
                self.sm.current = 'home'
                logger.info("   → chord_detail возврат на home")
                return

        # ============ ОБЫЧНАЯ ЛОГИКА ============
        if top_nav_config.show_back_button(current):
            if prev_from_state and self.sm.has_screen(prev_from_state):
                logger.info(f"   → Возврат на {prev_from_state}")
                self.sm.current = prev_from_state
                return

        if self.sm.has_screen('home'):
            logger.info("   → Переход на home (по умолчанию)")
            self.sm.current = 'home'

    def _on_settings_press(self, *args):
        """Обработчик нажатия на иконку настроек"""
        logger.info("⚙️ Нажата иконка настроек → открываем Sidebar")
        app = MDApp.get_running_app()
        if hasattr(app, 'sidebar') and app.sidebar:
            app.sidebar.toggle()

    def _on_home_press(self, *args):
        """Обработчик нажатия кнопки домой"""
        logger.info("🏠 Нажата иконка домой")
        if self.sm and self.sm.has_screen('home'):
            self.sm.current = 'home'

    def _on_search_press(self, *args):
        """Обработчик нажатия кнопки поиска"""
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
        """Сбрасывает TopNav к состоянию по умолчанию (home)"""
        self.clear_custom_title_widget()
        self._update_left_button('home')
        self._update_right_buttons('home')
        self.update_title('home')

    def on_size(self, *args):
        Clock.schedule_once(lambda dt: self._adjust_title_width(), 0.1)

    def force_update_title(self, title, show_back=False):
        """Мгновенно обновляет заголовок"""
        if hasattr(self, 'custom_title_widget') and self.custom_title_widget:
            if self.custom_title_widget in self.container.children:
                self.container.remove_widget(self.custom_title_widget)
            self.custom_title_widget = None

        self.screen_title.text = title
        self._adjust_title_width()

        if self.screen_title not in self.container.children:
            self.container.add_widget(self.screen_title)

        if show_back:
            self.left_container.clear_widgets()
            self.left_container.add_widget(self.back_btn)

        self.container.do_layout()
        logger.info(f"⚡ Мгновенное обновление заголовка: {title}")