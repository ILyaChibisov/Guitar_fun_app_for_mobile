# screens/admin_screen.py
"""
Экран администратора
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.metrics import dp
from kivy.clock import Clock
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify
from utils.kivy_imports import MDRaisedButton, MDIconButton, MDProgressBar

logger = screen_logger('Admin')


class UserCard(MDCard):
    """Карточка пользователя для админ-панели"""

    def __init__(self, user, on_role_change=None, on_ban=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.on_role_change = on_role_change
        self.on_ban = on_ban

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(100)
        self.padding = dp(12)
        self.spacing = dp(8)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.md_bg_color = theme.SURFACE
        self.elevation = 1

        # Информация о пользователе
        info_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(8))

        # Аватар
        avatar = MDLabel(text="👤", font_size=dp(24), size_hint_x=0.15)

        # Данные
        data_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.6)
        username = MDLabel(text=user.get('username', ''), font_style="Subtitle1", bold=True)
        email = MDLabel(text=user.get('email', 'нет email'), font_style="Caption", theme_text_color="Secondary")
        data_layout.add_widget(username)
        data_layout.add_widget(email)

        # Роль
        role_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.25)
        role_label = MDLabel(
            text=f"Роль: {user.get('role', 'user')}",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=0.5
        )
        role_layout.add_widget(role_label)

        info_layout.add_widget(avatar)
        info_layout.add_widget(data_layout)
        info_layout.add_widget(role_layout)

        # Кнопки действий
        actions_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(8))

        # Кнопка смены роли
        role_btn = MDRaisedButton(
            text="Сделать админом" if user.get('role') != 'admin' else "Убрать админа",
            size_hint=(0.5, 1),
            md_bg_color=theme.PRIMARY_LIGHT if user.get('role') != 'admin' else theme.PRIMARY_DARK,
            font_size=dp(10)
        )
        role_btn.bind(on_release=lambda x: self._change_role())

        # Кнопка бана
        is_banned = not user.get('is_active', True)
        ban_btn = MDRaisedButton(
            text="Разблокировать" if is_banned else "Заблокировать",
            size_hint=(0.5, 1),
            md_bg_color=[0.8, 0.3, 0.3, 1] if not is_banned else [0.3, 0.7, 0.3, 1],
            font_size=dp(10)
        )
        ban_btn.bind(on_release=lambda x: self._toggle_ban())

        actions_layout.add_widget(role_btn)
        actions_layout.add_widget(ban_btn)

        self.add_widget(info_layout)
        self.add_widget(actions_layout)

    def _change_role(self):
        if self.on_role_change:
            self.on_role_change(self.user)

    def _toggle_ban(self):
        if self.on_ban:
            self.on_ban(self.user)


class AdminScreen(MDScreen):
    """Экран администратора"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'admin'
        self.users = []
        self.stats = {}

        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Верхняя панель
        self.top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(56),
            padding=[dp(8), dp(8), dp(8), dp(8)],
            spacing=dp(8),
            md_bg_color=theme.PRIMARY
        )

        self.back_btn = MDIconButton(
            icon="arrow-left",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=self.go_back
        )

        self.title_label = MDLabel(
            text="👑 Админ-панель",
            font_style="H6",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        self.top_bar.add_widget(self.back_btn)
        self.top_bar.add_widget(self.title_label)

        # Основной контент
        self.main_layout = MDBoxLayout(orientation='vertical')
        self.main_layout.add_widget(self.top_bar)

        # Загружаем данные
        Clock.schedule_once(self.load_data, 0.5)

        self.add_widget(self.main_layout)

        logger.info('Экран администратора создан')

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def go_back(self, instance):
        """Возврат в профиль"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'profile'

    def load_data(self, dt):
        """Загружает данные для админ-панели"""
        self.show_loading()

        # Проверяем права
        if not api.is_admin():
            notify.error("У вас нет прав администратора")
            self.go_back(None)
            return

        # Загружаем статистику и пользователей
        api.get_admin_stats(
            on_success=self.on_stats_loaded,
            on_failure=self.on_load_failed
        )
        api.get_all_users(
            on_success=self.on_users_loaded,
            on_failure=self.on_load_failed
        )

    def on_stats_loaded(self, stats):
        """Обработчик загрузки статистики"""
        self.stats = stats
        self.build_ui()

    def on_users_loaded(self, users):
        """Обработчик загрузки пользователей"""
        self.users = users
        self.build_ui()

    def build_ui(self):
        """Строит интерфейс после загрузки данных"""
        self.main_layout.clear_widgets()
        self.main_layout.add_widget(self.top_bar)

        from kivymd.uix.tab import MDTabs

        tabs = MDTabs(size_hint=(1, 1))

        # Вкладка статистики
        stats_tab = MDFloatLayout()
        stats_layout = MDBoxLayout(orientation='vertical', padding=dp(16), spacing=dp(16))
        stats_tab.add_widget(stats_layout)

        stats_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(200),
            padding=dp(16),
            spacing=dp(8),
            elevation=2,
            radius=[theme.CORNER_RADIUS],
            md_bg_color=theme.SURFACE
        )

        stats_card.add_widget(MDLabel(text="📈 Общая статистика", font_style="H6", bold=True))

        # Данные статистики
        stats_data = self.stats.get('data', {})
        stat_items = [
            f"👥 Всего пользователей: {stats_data.get('total_users', 0)}",
            f"🎸 Всего песен: {stats_data.get('total_songs', 0)}",
            f"❤️ Всего лайков: {stats_data.get('total_likes', 0)}",
            f"⭐ Всего в избранном: {stats_data.get('total_favorites', 0)}",
            f"👁️ Всего просмотров: {stats_data.get('total_views', 0)}",
        ]

        for item in stat_items:
            stats_card.add_widget(MDLabel(text=item, font_style="Body1"))

        stats_layout.add_widget(stats_card)

        # Кнопка сканирования песен
        scan_btn = MDRaisedButton(
            text="🔄 Сканировать новые песни",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=theme.PRIMARY,
            on_release=self.scan_songs
        )
        scan_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        stats_layout.add_widget(scan_btn)

        # Добавляем вкладку статистики
        tabs.add_widget(stats_tab)
        tabs.ids.tab_manager.get_tab(0).text = "📊 Статистика"

        # Вкладка пользователей
        users_tab = MDFloatLayout()
        users_scroll = MDScrollView()
        users_container = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, adaptive_height=True)

        for user in self.users:
            card = UserCard(
                user=user,
                on_role_change=self.change_user_role,
                on_ban=self.toggle_user_ban
            )
            users_container.add_widget(card)

        users_scroll.add_widget(users_container)
        users_tab.add_widget(users_scroll)
        tabs.add_widget(users_tab)
        tabs.ids.tab_manager.get_tab(1).text = "👥 Пользователи"

        self.main_layout.add_widget(tabs)
        self.hide_loading()

    def change_user_role(self, user):
        """Изменяет роль пользователя"""
        new_role = 'admin' if user.get('role') != 'admin' else 'user'

        def on_success(result):
            notify.success(f"Роль пользователя {user['username']} изменена на {new_role}")
            self.load_data(0)

        def on_failure(req, error):
            notify.error(f"Ошибка: {error}")

        api.update_user_role(user['id'], new_role, on_success=on_success, on_failure=on_failure)

    def toggle_user_ban(self, user):
        """Блокирует/разблокирует пользователя"""
        is_active = user.get('is_active', True)

        def on_success(result):
            action = "заблокирован" if is_active else "разблокирован"
            notify.success(f"Пользователь {user['username']} {action}")
            self.load_data(0)

        def on_failure(req, error):
            notify.error(f"Ошибка: {error}")

        if is_active:
            api.ban_user(user['id'], on_success=on_success, on_failure=on_failure)
        else:
            api.unban_user(user['id'], on_success=on_success, on_failure=on_failure)

    def scan_songs(self, instance):
        """Запускает сканирование песен"""

        def on_success(result):
            added = result.get('added', 0)
            skipped = result.get('skipped', 0)
            errors = result.get('errors', 0)
            notify.success(f"Сканирование завершено: +{added} новых, пропущено {skipped}, ошибок {errors}")

        def on_failure(req, error):
            notify.error(f"Ошибка сканирования: {error}")

        api.scan_songs(on_success=on_success, on_failure=on_failure)

    def on_load_failed(self, req, error):
        """Ошибка загрузки"""
        self.hide_loading()
        notify.error(f"Ошибка загрузки: {error}")
        self.go_back(None)

    def show_loading(self):
        """Показывает индикатор загрузки"""
        self.loading = MDProgressBar(value=50, max=100, size_hint=(1, 0.01))
        self.main_layout.add_widget(self.loading)

    def hide_loading(self):
        """Скрывает индикатор загрузки"""
        if hasattr(self, 'loading') and self.loading:
            self.main_layout.remove_widget(self.loading)