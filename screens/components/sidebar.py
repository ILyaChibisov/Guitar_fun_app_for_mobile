# screens/components/sidebar.py
"""
Выдвижная боковая панель (Navigation Drawer)
с аватаром пользователя и пунктами меню
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

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.behaviors import CircularRippleBehavior
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from api.client import api

logger = get_logger('Sidebar')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class SidebarItem(CircularRippleBehavior, MDCard):
    """Пункт меню в боковой панели"""

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
            pos_hint={'center_y': 0.5}
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
                pos_hint={'center_y': 0.5}
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
            self.on_click_callback(self.screen_name)


class SidebarHeader(MDBoxLayout):
    """Шапка боковой панели с аватаром и именем пользователя"""

    def __init__(self, on_profile_click=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(180)
        self.padding = [dp(16), dp(24), dp(16), dp(16)]
        self.spacing = dp(8)
        self.md_bg_color = [0, 0, 0, 0.08]

        self.on_profile_click_callback = on_profile_click

        # Аватар
        avatar_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(70),
            md_bg_color=[0, 0, 0, 0]
        )

        self.avatar = Image(
            size_hint=(None, None),
            size=(dp(64), dp(64)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )

        # Пытаемся загрузить аватар из ассета
        if HAS_ASSETS:
            try:
                avatar_data = load_asset_as_bytes('profile_png')
                if avatar_data:
                    img = CoreImage(BytesIO(avatar_data), ext="png")
                    self.avatar.texture = img.texture
            except:
                pass

        # Если нет аватара - используем иконку
        if not self.avatar.texture:
            self.avatar.text = "👤"
            self.avatar.color = [1, 1, 1, 0.8]

        avatar_container.add_widget(self.avatar)

        # Имя пользователя
        self.username_label = MDLabel(
            text=self._get_username(),
            font_size=sp(18),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )

        # Статус (авторизован/гость)
        self.status_label = MDLabel(
            text=self._get_status_text(),
            font_size=sp(12),
            halign="center",
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 0.8],
            bold=False
        )

        # Клик по шапке для перехода в профиль
        self.bind(on_touch_down=self._on_header_click)

        self.add_widget(avatar_container)
        self.add_widget(self.username_label)
        self.add_widget(self.status_label)

    def _get_username(self):
        """Возвращает имя пользователя"""
        if api.is_authenticated() and api.user_data:
            return api.user_data.get('username', 'Гость')
        return 'Гость'

    def _get_status_text(self):
        """Возвращает статус пользователя"""
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
        """Обновляет информацию о пользователе"""
        self.username_label.text = self._get_username()
        self.status_label.text = self._get_status_text()


class Sidebar(FloatLayout):
    """Выдвижная боковая панель - используем FloatLayout для точного позиционирования"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.is_open = False
        self.anim_duration = 0.25
        self.panel_width = dp(300)

        # ============ НАСТРОЙКИ ПАНЕЛИ ============
        self.size_hint = (None, 1)
        self.width = self.panel_width
        self.height = Window.height

        # ============ СКРЫВАЕМ ПАНЕЛЬ ЗА ЛЕВЫМ КРАЕМ ============
        self.pos = (-self.panel_width, 0)

        # ============ ОСНОВНАЯ КАРТОЧКА ПАНЕЛИ ============
        self.panel_card = MDCard(
            orientation='vertical',
            size_hint=(1, 1),
            radius=[0, 0, 0, 0],
            elevation=4,
            md_bg_color=[0.08, 0.08, 0.08, 0.98],
            padding=[0, 0, 0, 0]
        )

        # Основной контейнер
        self.main_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0,
            md_bg_color=[0, 0, 0, 0]
        )

        # ============ ШАПКА ============
        self.header = SidebarHeader(
            on_profile_click=self._on_profile_click
        )
        self.main_container.add_widget(self.header)

        # ============ ПУНКТЫ МЕНЮ ============
        from kivy.uix.scrollview import ScrollView

        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0]
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
        # 1. Профиль
        self.add_menu_item('account', 'Профиль', 'profile')

        # 2. Авторизация (заглушка)
        self.add_menu_item('login', 'Авторизация', 'auth')

        # 3. Настройки
        self.add_menu_item('cog', 'Settings', 'settings')

        # 4. Помощь
        self.add_menu_item('help-circle', 'Помощь', 'help')

        # 5. Промокод
        self.add_menu_item('ticket-percent', 'Промокод', 'promo')

        # 6. Обратная связь
        self.add_menu_item('chat', 'Обратная связь', 'feedback')

        # 7. Админка (только для админа)
        self.admin_item = self.add_menu_item('shield-account', 'Админка', 'admin', is_admin=True)
        self.admin_item.opacity = 1 if api.is_admin() else 0
        self.admin_item.disabled = not api.is_admin()

        # Разделитель
        self.menu_container.add_widget(
            MDBoxLayout(
                size_hint=(1, None),
                height=dp(1),
                md_bg_color=[1, 1, 1, 0.05],
                padding=[dp(16), 0, dp(16), 0]
            )
        )

        # Версия приложения
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

        self.panel_card.add_widget(self.main_container)
        self.add_widget(self.panel_card)

        # ============ ПРИНУДИТЕЛЬНО СКРЫВАЕМ ============
        self.is_open = False
        self.pos = (-self.panel_width, 0)

        # Привязываемся к изменению размера окна
        Window.bind(on_resize=self._on_window_resize)

        # Дополнительно через 0.1 секунды убеждаемся, что панель скрыта
        Clock.schedule_once(lambda dt: self._ensure_hidden(), 0.1)

        logger.info(f"✅ Sidebar создан, ширина={self.panel_width}dp, позиция=({self.pos[0]}, {self.pos[1]})")
        logger.info("✅ Sidebar скрыт при создании")

    def _ensure_hidden(self):
        """Гарантирует, что панель скрыта"""
        if not self.is_open:
            self.pos = (-self.panel_width, 0)
            logger.info(f"🔒 Sidebar принудительно скрыт: pos=({self.pos[0]}, {self.pos[1]})")

    def _on_window_resize(self, window, width, height):
        """При изменении размера окна обновляем размер и позицию"""
        self.height = height
        if not self.is_open:
            self.pos = (-self.panel_width, 0)

    def add_menu_item(self, icon, title, screen_name, is_admin=False):
        """Добавляет пункт меню"""
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
        logger.info(f"📍 Выбран пункт меню: {screen_name}")

        # Закрываем панель
        self.close()

        # Обрабатываем специальные пункты
        if screen_name == 'auth':
            self._show_auth()
            return

        # Переход на экран
        if self.sm and self.sm.has_screen(screen_name):
            self.sm.current = screen_name
        else:
            logger.warning(f"⚠️ Экран {screen_name} не найден")

    def _on_profile_click(self):
        """Обработчик клика по шапке - переход в профиль"""
        self.close()
        if self.sm and self.sm.has_screen('profile'):
            self.sm.current = 'profile'

    def _show_auth(self):
        """Показывает модальное окно авторизации"""
        app = MDApp.get_running_app()
        if app and hasattr(app, 'open_profile'):
            app.open_profile()

    def open(self):
        """Открывает панель"""
        if self.is_open:
            return

        self.is_open = True
        # Анимация от -panel_width до 0
        anim = Animation(x=0, duration=self.anim_duration, t='out_quad')
        anim.start(self)
        logger.info("📂 Sidebar открыта")

    def close(self):
        """Закрывает панель"""
        if not self.is_open:
            return

        self.is_open = False
        # Анимация от 0 до -panel_width
        anim = Animation(x=-self.panel_width, duration=self.anim_duration, t='in_quad')
        anim.start(self)
        logger.info("📂 Sidebar закрыта")

    def toggle(self):
        """Переключает состояние панели"""
        if self.is_open:
            self.close()
        else:
            self.open()

    def update_user_info(self):
        """Обновляет информацию о пользователе в шапке"""
        if hasattr(self, 'header') and self.header:
            self.header.update_user_info()

        # Обновляем видимость админки
        if hasattr(self, 'admin_item'):
            is_admin = api.is_admin()
            self.admin_item.opacity = 1 if is_admin else 0
            self.admin_item.disabled = not is_admin

    def on_touch_down(self, touch):
        """Обработка касаний - закрытие при клике вне панели"""
        if self.is_open:
            # Если клик вне панели - закрываем
            if not self.collide_point(*touch.pos):
                self.close()
                return True
        return super().on_touch_down(touch)