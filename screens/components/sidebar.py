# screens/components/sidebar.py
"""
Выдвижная боковая панель (Navigation Drawer)
ПОЛНАЯ ВЫСОТА: от верхней до нижней системной панели
С прозрачными областями для статус-бара и навигации
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from io import BytesIO
from kivy.utils import platform
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty
from kivy.uix.scrollview import ScrollView

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.behaviors import CircularRippleBehavior
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from config.layout_config import layout_config
from config.system_bars import get_status_bar_height, get_navigation_bar_height
from api.client import api

logger = get_logger('Sidebar')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# Константа для логотипа
ASSET_LOGO_NAME_PNG = "logo_name_png"


class SidebarItem(CircularRippleBehavior, MDCard):
    """Пункт меню в боковой панели - кликабельный"""

    def __init__(self, icon_name, title, screen_name, on_click=None, is_admin=False, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.title = title
        self.screen_name = screen_name
        self.on_click_callback = on_click
        self.is_admin = is_admin

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(12)
        self.radius = [dp(8)] * 4
        self.elevation = 0
        self.ripple_scale = 0.95
        self.md_bg_color = [0, 0, 0, 0]

        # Иконка
        self.icon = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.7],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5},
            ripple_scale=0
        )

        # Название
        self.title_label = MDLabel(
            text=title,
            font_size=sp(15),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.85],
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        # Стрелка (для админки)
        if is_admin:
            self.arrow = MDIconButton(
                icon="chevron-right",
                size_hint=(None, None),
                size=(dp(20), dp(20)),
                theme_icon_color="Custom",
                icon_color=[0.46, 0.70, 0.71, 0.5],
                md_bg_color=[0, 0, 0, 0],
                pos_hint={'center_y': 0.5},
                ripple_scale=0
            )
            self.add_widget(self.arrow)

        self.add_widget(self.icon)
        self.add_widget(self.title_label)

        self.bind(on_release=self._on_click)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _on_enter(self, *args):
        self.md_bg_color = [1, 1, 1, 0.05]

    def _on_leave(self, *args):
        self.md_bg_color = [0, 0, 0, 0]

    def _on_click(self, instance):
        if self.on_click_callback:
            logger.info(f"🖱️ Клик по пункту меню: {self.screen_name} ({self.title})")
            self.on_click_callback(self.screen_name)

    def set_active(self, active):
        """Устанавливает активное состояние пункта меню"""
        if active:
            self.icon.icon_color = [0.46, 0.70, 0.71, 1]
            self.title_label.text_color = [0.46, 0.70, 0.71, 1]
            self.title_label.bold = True
        else:
            self.icon.icon_color = [1, 1, 1, 0.7]
            self.title_label.text_color = [1, 1, 1, 0.85]
            self.title_label.bold = False


class SidebarHeader(MDBoxLayout):
    """Шапка боковой панели с логотипом и информацией о пользователе"""

    def __init__(self, on_profile_click=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(180)
        self.padding = [dp(16), dp(24), dp(16), dp(16)]
        self.spacing = dp(8)
        self.md_bg_color = [0, 0, 0, 0.08]

        self.on_profile_click_callback = on_profile_click

        # Контейнер для логотипа (центрирование)
        logo_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(100),
            md_bg_color=[0, 0, 0, 0]
        )

        # Логотип
        self.logo_image = Image(
            size_hint=(None, None),
            size=(dp(120), dp(80)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )

        self._load_logo()

        logo_container.add_widget(self.logo_image)

        # Имя пользователя
        self.username_label = MDLabel(
            text=self._get_username(),
            font_size=sp(16),
            halign="center",
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )

        # Статус
        self.status_label = MDLabel(
            text=self._get_status_text(),
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 0.8],
            bold=False
        )

        self.bind(on_touch_down=self._on_header_click)

        self.add_widget(logo_container)
        self.add_widget(self.username_label)
        self.add_widget(self.status_label)

    def _load_logo(self):
        """Загружает логотип из ассета"""
        if HAS_ASSETS:
            try:
                logo_data = load_asset_as_bytes(ASSET_LOGO_NAME_PNG)
                if logo_data:
                    img = CoreImage(BytesIO(logo_data), ext="png")
                    self.logo_image.texture = img.texture
                    logger.info("✅ Логотип загружен из ассета")
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки логотипа: {e}")

        self.logo_image.text = "🎸"
        self.logo_image.color = [0.46, 0.70, 0.71, 1]
        self.logo_image.font_size = sp(48)

    def _get_username(self):
        if api.is_authenticated() and api.user_data:
            return api.user_data.get('username', 'Гость')
        return 'Гость'

    def _get_status_text(self):
        if api.is_authenticated():
            return '✅ Авторизован'
        return '🔓 Не авторизован'

    def _on_header_click(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self.on_profile_click_callback:
                self.on_profile_click_callback()
            return True
        return False

    def update_user_info(self):
        self.username_label.text = self._get_username()
        self.status_label.text = self._get_status_text()


class SidebarOverlay(Widget):
    """Полупрозрачный оверлей, который перехватывает клики вне панели"""

    def __init__(self, sidebar, **kwargs):
        super().__init__(**kwargs)
        self.sidebar = sidebar
        self.size_hint = (1, 1)
        self.pos = (0, 0)
        self.disabled = True

        with self.canvas.before:
            self.bg_color = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def show(self):
        self.disabled = False
        self.bg_color.rgba = (0, 0, 0, 0.5)

    def hide(self):
        self.disabled = True
        self.bg_color.rgba = (0, 0, 0, 0)

    def on_touch_down(self, touch):
        if self.disabled:
            return False
        if not self.sidebar.panel.collide_point(*touch.pos):
            self.sidebar.close()
            return True
        return False


class Sidebar(FloatLayout):
    """
    Выдвижная боковая панель
    ПОЛНАЯ ВЫСОТА: от верхней до нижней системной панели
    """

    panel_x = NumericProperty(0)

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.is_open = False
        self.anim_duration = 0.25
        self.panel_width = dp(300)

        self._touch_start_x = 0
        self._touch_start_panel_x = 0
        self._is_dragging = False
        self._swipe_threshold = dp(30)

        # ============ НАСТРОЙКИ КОНТЕЙНЕРА ============
        self.size_hint = (1, 1)
        self.pos = (0, 0)
        self.md_bg_color = [0, 0, 0, 0]
        self.disabled = True

        # ============ ОВЕРЛЕЙ ============
        self.overlay = SidebarOverlay(self)
        self.add_widget(self.overlay)

        # ============ ВЫЧИСЛЯЕМ ОТСТУПЫ ============
        status_h = get_status_bar_height()
        nav_h = get_navigation_bar_height()

        self._top_system_offset = status_h
        self._bottom_system_offset = nav_h

        logger.info(f"📐 Системные отступы: сверху={self._top_system_offset}dp, снизу={self._bottom_system_offset}dp")

        # ============ ОСНОВНАЯ ПАНЕЛЬ ============
        self.panel = MDCard(
            orientation='vertical',
            size_hint=(None, 1),
            width=self.panel_width,
            radius=[0, 0, 0, 0],
            elevation=6,
            md_bg_color=[0.08, 0.08, 0.08, 0.98],
            padding=[0, 0, 0, 0]
        )

        self.panel.pos = (-self.panel_width, 0)
        self.panel_x = -self.panel_width

        # ============ ВНУТРЕННИЙ КОНТЕЙНЕР ============
        self.main_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0,
            md_bg_color=[0, 0, 0, 0],
            padding=[0, self._top_system_offset, 0, self._bottom_system_offset]
        )

        # ============ ШАПКА ============
        self.header = SidebarHeader(
            on_profile_click=self._on_profile_click
        )
        self.main_container.add_widget(self.header)

        # ============ СКРОЛЛ С ПУНКТАМИ МЕНЮ ============
        # Используем обычный ScrollView с отключенным скроллбаром
        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            scroll_type=['content'],
            effect_cls='ScrollEffect'
        )

        self.menu_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            adaptive_height=True,
            spacing=dp(2),
            padding=[dp(4), dp(8), dp(4), dp(8)]
        )
        self.menu_container.bind(minimum_height=self.menu_container.setter('height'))

        # ============ ПУНКТЫ МЕНЮ ============
        self.menu_item_refs = {}

        # 1. Профиль
        item = self.add_menu_item('account', 'Профиль', 'profile')
        self.menu_item_refs['profile'] = item

        # 2. Авторизация (специальный пункт)
        self.auth_item = self.add_menu_item('login', 'Войти', 'auth')
        self.menu_item_refs['auth'] = self.auth_item

        # 3. Настройки
        item = self.add_menu_item('cog', 'Настройки', 'settings')
        self.menu_item_refs['settings'] = item

        # 4. Помощь
        item = self.add_menu_item('help-circle', 'Помощь', 'help')
        self.menu_item_refs['help'] = item

        # 5. Промокод
        item = self.add_menu_item('ticket-percent', 'Промокод', 'promo')
        self.menu_item_refs['promo'] = item

        # 6. Обратная связь
        item = self.add_menu_item('chat', 'Обратная связь', 'feedback')
        self.menu_item_refs['feedback'] = item

        # 7. Админка (только для админа)
        self.admin_item = self.add_menu_item('shield-account', 'Админка', 'admin', is_admin=True)
        self.admin_item.opacity = 1 if api.is_admin() else 0
        self.admin_item.disabled = not api.is_admin()
        self.menu_item_refs['admin'] = self.admin_item

        # Разделитель
        self.menu_container.add_widget(
            MDBoxLayout(
                size_hint=(1, None),
                height=dp(1),
                md_bg_color=[1, 1, 1, 0.05],
                padding=[dp(16), 0, dp(16), 0]
            )
        )

        # Версия
        version_label = MDLabel(
            text=f"Версия {api.config.VERSION}",
            font_size=sp(11),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.25]
        )
        self.menu_container.add_widget(version_label)

        self.scroll.add_widget(self.menu_container)
        self.main_container.add_widget(self.scroll)

        self.panel.add_widget(self.main_container)
        self.add_widget(self.panel)

        # ============ ПРИНУДИТЕЛЬНО СКРЫВАЕМ ============
        self.is_open = False
        self.panel.pos = (-self.panel_width, 0)
        self.panel_x = -self.panel_width
        self.overlay.hide()
        self.disabled = True

        Window.bind(on_resize=self._on_window_resize)
        self.bind(panel_x=self._on_panel_x_changed)

        Clock.schedule_once(self._update_menu_state, 0.3)

        # Выводим список доступных экранов для диагностики
        if self.sm:
            logger.info(f"✅ Sidebar создан, ширина={self.panel_width}dp")
            logger.info(f"📋 Доступные экраны в ScreenManager: {self.sm.screen_names}")
        else:
            logger.error("❌ ScreenManager не передан в Sidebar!")

    def _update_menu_state(self, dt=None):
        if not self.sm:
            return

        current_screen = self.sm.current
        logger.info(f"🔄 Обновление состояния меню, текущий экран: {current_screen}")

        for screen_name, item in self.menu_item_refs.items():
            if hasattr(item, 'set_active'):
                is_active = (screen_name == current_screen)
                item.set_active(is_active)

        self._update_auth_state()

    def _update_auth_state(self):
        is_auth = api.is_authenticated()

        if is_auth:
            self.auth_item.title_label.text = "Выйти"
            self.auth_item.icon.icon = "logout"
        else:
            self.auth_item.title_label.text = "Войти"
            self.auth_item.icon.icon = "login"

    def _on_panel_x_changed(self, instance, value):
        self.panel.pos = (value, 0)

        if self.is_open:
            progress = (value + self.panel_width) / self.panel_width
            alpha = 0.5 * progress
            if alpha < 0:
                alpha = 0
            elif alpha > 0.5:
                alpha = 0.5
            self.overlay.bg_color.rgba = (0, 0, 0, alpha)

    def _on_window_resize(self, window, width, height):
        self.height = height

        status_h = get_status_bar_height()
        nav_h = get_navigation_bar_height()

        self._top_system_offset = status_h
        self._bottom_system_offset = nav_h

        self.main_container.padding = [0, self._top_system_offset, 0, self._bottom_system_offset]

        if not self.is_open:
            self.panel.pos = (-self.panel_width, 0)
            self.panel_x = -self.panel_width

    def add_menu_item(self, icon, title, screen_name, is_admin=False):
        item = SidebarItem(
            icon_name=icon,
            title=title,
            screen_name=screen_name,
            on_click=self._on_item_click,
            is_admin=is_admin
        )
        self.menu_container.add_widget(item)
        return item

    def _on_item_click(self, screen_name):
        """Обработчик клика по пункту меню"""
        logger.info(f"📍 ВЫЗВАН _on_item_click для: {screen_name}")

        # Закрываем панель
        self.close()

        # Специальная обработка для авторизации
        if screen_name == 'auth':
            Clock.schedule_once(lambda dt: self._handle_auth(), 0.1)
            return

        # Проверяем, существует ли экран
        if not self.sm:
            logger.error("❌ ScreenManager не найден!")
            return

        # Проверяем, есть ли экран в ScreenManager
        if not self.sm.has_screen(screen_name):
            logger.error(f"❌ Экран '{screen_name}' не найден в ScreenManager!")
            logger.info(f"📋 Доступные экраны: {self.sm.screen_names}")
            return

        # Если уже на этом экране - ничего не делаем
        if self.sm.current == screen_name:
            logger.info(f"ℹ️ Уже на экране {screen_name}")
            return

        # Переход с задержкой, чтобы панель успела закрыться
        def do_navigation(dt):
            try:
                logger.info(f"🚀 Переход на экран: {screen_name}")
                self.sm.current = screen_name
                logger.info(f"✅ Переход выполнен на: {screen_name}")
            except Exception as e:
                logger.error(f"❌ Ошибка перехода: {e}")
                import traceback
                traceback.print_exc()

        Clock.schedule_once(do_navigation, 0.15)

    def _handle_auth(self):
        """Обрабатывает клик по пункту авторизации"""
        if api.is_authenticated():
            def on_logout_success(result):
                logger.info("✅ Выход выполнен")
                self._update_auth_state()
                if hasattr(self, 'header'):
                    self.header.update_user_info()
                self._update_menu_state()

            def on_logout_failure(req, error):
                logger.error(f"❌ Ошибка выхода: {error}")

            api.logout(
                on_success=on_logout_success,
                on_failure=on_logout_failure
            )
        else:
            self._show_auth()

    def _on_profile_click(self):
        logger.info("👤 Клик по шапке -> переход в профиль")
        self.close()
        if self.sm and self.sm.has_screen('profile'):
            def do_navigation(dt):
                try:
                    self.sm.current = 'profile'
                    logger.info("✅ Переход в профиль выполнен")
                except Exception as e:
                    logger.error(f"❌ Ошибка перехода в профиль: {e}")

            Clock.schedule_once(do_navigation, 0.15)
        else:
            logger.error("❌ Экран 'profile' не найден!")

    def _show_auth(self):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'open_profile'):
            app.open_profile()

    def open(self):
        if self.is_open:
            return

        self.is_open = True
        self.disabled = False
        self.overlay.show()
        anim = Animation(panel_x=0, duration=self.anim_duration, t='out_quad')
        anim.start(self)
        logger.info("📂 Sidebar открыта")

    def close(self):
        if not self.is_open:
            return

        self.is_open = False
        self.disabled = True
        self.overlay.hide()
        anim = Animation(panel_x=-self.panel_width, duration=self.anim_duration, t='in_quad')
        anim.start(self)
        logger.info("📂 Sidebar закрыта")

    def toggle(self):
        logger.info(f"🔄 Sidebar toggle: is_open={self.is_open}")
        if self.is_open:
            self.close()
        else:
            self.open()

    def update_user_info(self):
        if hasattr(self, 'header') and self.header:
            self.header.update_user_info()

        self._update_auth_state()

        if hasattr(self, 'admin_item'):
            is_admin = api.is_admin()
            self.admin_item.opacity = 1 if is_admin else 0
            self.admin_item.disabled = not is_admin

        self._update_menu_state()

    # ============ ОБРАБОТКА СВАЙПА ============

    def on_touch_down(self, touch):
        if self.disabled and not self._is_dragging:
            return False

        if not self.is_open:
            if touch.x < dp(30):
                self._touch_start_x = touch.x
                self._touch_start_panel_x = self.panel_x
                self._is_dragging = True
                touch.grab(self)
                return True
            return False

        if self.overlay and not self.overlay.disabled:
            if not self.panel.collide_point(*touch.pos):
                return self.overlay.on_touch_down(touch)

        if self.panel.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        return False

    def on_touch_move(self, touch):
        if not self._is_dragging:
            return False

        if touch.grab_current is not self:
            return False

        delta_x = touch.x - self._touch_start_x
        new_x = self._touch_start_panel_x + delta_x

        if new_x > 0:
            new_x = 0
        elif new_x < -self.panel_width:
            new_x = -self.panel_width

        if not self.is_open and new_x > -self.panel_width * 0.8:
            self.is_open = True
            self.disabled = False
            self.overlay.show()

        self.panel_x = new_x
        return True

    def on_touch_up(self, touch):
        if not self._is_dragging:
            return False

        if touch.grab_current is not self:
            return False

        touch.ungrab(self)
        self._is_dragging = False

        if not self.is_open:
            if self.panel_x > -self.panel_width * 0.5:
                self.open()
            else:
                self.close()
            return True

        current_x = self.panel_x
        delta_x = touch.x - self._touch_start_x
        is_swipe = abs(delta_x) > self._swipe_threshold

        if is_swipe:
            if delta_x > 0:
                self.open()
            else:
                self.close()
        else:
            threshold = -self.panel_width * 0.5
            if current_x > threshold:
                self.open()
            else:
                self.close()

        return True