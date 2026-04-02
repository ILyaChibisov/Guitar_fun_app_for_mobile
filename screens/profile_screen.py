# screens/profile_screen.py
"""
Экран профиля пользователя
"""
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('Profile')


class ProfileScreen(MDScreen):
    """Экран профиля пользователя"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'profile'
        self.user = None
        self.change_password_dialog = None
        self._data_loaded = False

        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Кнопка назад - создаем без параметров в конструкторе
        self.back_btn = MDIconButton(
            pos_hint={'x': 0, 'top': 1},
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            on_release=self.go_back
        )
        self.back_btn.icon = "arrow-left"
        self.back_btn.icon_color = theme.TEXT_SECONDARY
        self.back_btn.theme_icon_color = "Custom"
        self.add_widget(self.back_btn)

        # Основной контейнер
        scroll = ScrollView(size_hint=(1, 1))

        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20),
            size_hint_y=None,
            adaptive_height=True
        )

        # Заголовок
        title = MDLabel(
            text="Личный кабинет",
            font_size=sp(24),
            halign="center",
            size_hint_y=None,
            height=dp(60),
            theme_text_color="Primary",
            bold=True
        )

        # Карточка с аватаром
        avatar_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(150),
            padding=dp(16),
            spacing=dp(8),
            elevation=2,
            radius=[theme.CORNER_RADIUS] * 4,
            md_bg_color=theme.SURFACE
        )

        self.avatar_label = MDLabel(
            text="👤",
            font_size=sp(40),
            halign="center",
            size_hint_y=None,
            height=dp(80),
            theme_text_color="Primary"
        )

        self.username_label = MDLabel(
            text="",
            font_size=sp(20),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Primary",
            bold=True
        )

        avatar_card.add_widget(self.avatar_label)
        avatar_card.add_widget(self.username_label)

        # Карточка с информацией
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(220),
            padding=dp(16),
            spacing=dp(12),
            elevation=2,
            radius=[theme.CORNER_RADIUS] * 4,
            md_bg_color=theme.SURFACE
        )

        info_title = MDLabel(
            text="Информация",
            font_size=sp(16),
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Primary",
            bold=True
        )

        # Email
        email_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        email_icon = MDIconButton(
            size_hint=(None, 1),
            width=dp(40)
        )
        email_icon.icon = "email"
        email_icon.icon_color = theme.TEXT_SECONDARY
        email_icon.theme_icon_color = "Custom"

        self.email_label = MDLabel(text="", font_size=sp(14), theme_text_color="Secondary")
        email_box.add_widget(email_icon)
        email_box.add_widget(self.email_label)

        # Полное имя
        name_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        name_icon = MDIconButton(
            size_hint=(None, 1),
            width=dp(40)
        )
        name_icon.icon = "account"
        name_icon.icon_color = theme.TEXT_SECONDARY
        name_icon.theme_icon_color = "Custom"

        self.fullname_label = MDLabel(text="", font_size=sp(14), theme_text_color="Secondary")
        name_box.add_widget(name_icon)
        name_box.add_widget(self.fullname_label)

        # Роль
        role_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        role_icon = MDIconButton(
            size_hint=(None, 1),
            width=dp(40)
        )
        role_icon.icon = "shield-account"
        role_icon.icon_color = theme.TEXT_SECONDARY
        role_icon.theme_icon_color = "Custom"

        self.role_label = MDLabel(text="", font_size=sp(14), theme_text_color="Secondary")
        role_box.add_widget(role_icon)
        role_box.add_widget(self.role_label)

        # Дата регистрации
        date_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        date_icon = MDIconButton(
            size_hint=(None, 1),
            width=dp(40)
        )
        date_icon.icon = "calendar"
        date_icon.icon_color = theme.TEXT_SECONDARY
        date_icon.theme_icon_color = "Custom"

        self.date_label = MDLabel(text="", font_size=sp(14), theme_text_color="Secondary")
        date_box.add_widget(date_icon)
        date_box.add_widget(self.date_label)

        info_card.add_widget(info_title)
        info_card.add_widget(email_box)
        info_card.add_widget(name_box)
        info_card.add_widget(role_box)
        info_card.add_widget(date_box)

        # Кнопки действий
        actions_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(180),
            padding=dp(16),
            spacing=dp(12),
            elevation=2,
            radius=[theme.CORNER_RADIUS] * 4,
            md_bg_color=theme.SURFACE
        )

        change_password_btn = MDButton(
            size_hint=(1, None),
            height=dp(44),
            on_release=self.show_change_password_dialog,
            style="filled"
        )
        change_password_btn.text = "Сменить пароль"
        change_password_btn.icon = "lock"
        change_password_btn.md_bg_color = theme.PRIMARY
        change_password_btn.theme_text_color = "Custom"
        change_password_btn.text_color = [1, 1, 1, 1]
        change_password_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        # Кнопка админ-панели (видна только администраторам)
        self.admin_btn = MDButton(
            size_hint=(1, None),
            height=dp(44),
            on_release=self.open_admin_panel,
            style="filled"
        )
        self.admin_btn.text = "👑 Админ-панель"
        self.admin_btn.icon = "shield-account"
        self.admin_btn.md_bg_color = theme.PRIMARY_DARK
        self.admin_btn.theme_text_color = "Custom"
        self.admin_btn.text_color = [1, 1, 1, 1]
        self.admin_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.admin_btn.opacity = 0
        self.admin_btn.disabled = True

        logout_btn = MDButton(
            size_hint=(1, None),
            height=dp(44),
            on_release=self.logout,
            style="filled"
        )
        logout_btn.text = "Выйти из аккаунта"
        logout_btn.icon = "logout"
        logout_btn.md_bg_color = [0.9, 0.9, 0.9, 1]
        logout_btn.theme_text_color = "Custom"
        logout_btn.text_color = theme.TEXT_SECONDARY
        logout_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        actions_card.add_widget(change_password_btn)
        actions_card.add_widget(self.admin_btn)
        actions_card.add_widget(logout_btn)

        layout.add_widget(title)
        layout.add_widget(avatar_card)
        layout.add_widget(info_card)
        layout.add_widget(actions_card)

        scroll.add_widget(layout)
        self.add_widget(scroll)

        Clock.schedule_once(self.load_user_data, 0.5)

        logger.info('Экран профиля создан')

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def go_back(self, instance):
        """Возврат на главный экран через bottom_nav"""
        app = MDApp.get_running_app()
        if hasattr(app, 'bottom_nav') and app.bottom_nav:
            app.bottom_nav.switch_tab("home")
        else:
            if hasattr(self, 'manager') and self.manager:
                self.manager.current = 'home'

    def load_user_data(self, dt):
        """Загружает данные пользователя (только один раз)"""
        if self._data_loaded:
            return
        self._data_loaded = True

        if api.user_data:
            self.user = api.user_data
            self.update_ui()
        else:
            api.get_current_user(
                on_success=self.on_user_loaded,
                on_failure=self.on_user_load_failed
            )

    def on_user_loaded(self, user):
        self.user = user
        self.update_ui()

    def on_user_load_failed(self, req, error):
        """Обработчик ошибки загрузки профиля"""
        error_msg = str(error)
        logger.error(f'Ошибка загрузки профиля: {error_msg}')

        if 'Not authenticated' in error_msg or 'Invalid token' in error_msg:
            logger.info('Токен недействителен, очищаем и показываем авторизацию')
            api._clear_tokens()
            notify.warning("Сессия истекла. Пожалуйста, войдите снова.")

            self.go_back(None)

            app = MDApp.get_running_app()
            if hasattr(app, 'home_screen') and app.home_screen:
                app.home_screen.show_auth_modal()
        else:
            notify.error("Не удалось загрузить данные профиля")
            self.go_back(None)

    def update_ui(self):
        """Обновляет интерфейс данными пользователя"""
        if not self.user:
            return

        username = self.user.get('username', 'user')
        email = self.user.get('email', 'не указан')
        full_name = self.user.get('full_name') or 'не указано'
        role = self.user.get('role', 'user')

        role_display = {
            'admin': '👑 Администратор',
            'user': '👤 Пользователь',
            'moderator': '🛡️ Модератор'
        }.get(role, f'👤 {role}')

        self.username_label.text = f"@{username}"
        self.email_label.text = email
        self.fullname_label.text = full_name
        self.role_label.text = role_display

        if api.is_admin():
            self.admin_btn.opacity = 1
            self.admin_btn.disabled = False
        else:
            self.admin_btn.opacity = 0
            self.admin_btn.disabled = True

        created_at = self.user.get('created_at')
        if created_at:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                self.date_label.text = dt.strftime('%d.%m.%Y')
            except:
                self.date_label.text = 'неизвестно'
        else:
            self.date_label.text = 'неизвестно'

    def open_admin_panel(self, instance):
        """Открывает админ-панель"""
        if api.is_admin():
            if hasattr(self, 'manager') and self.manager:
                if 'admin' not in self.manager.screen_names:
                    from screens.admin_screen import AdminScreen
                    self.manager.add_widget(AdminScreen(name='admin'))
                self.manager.current = 'admin'
        else:
            notify.error("У вас нет прав администратора")

    def show_change_password_dialog(self, instance):
        """Показывает диалог смены пароля"""
        if self.change_password_dialog:
            self.change_password_dialog.dismiss()

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            padding=dp(16),
            size_hint_y=None,
            height=dp(200)
        )

        self.old_password = MDTextField(
            hint_text="Текущий пароль",
            mode="filled",
            password=True,
            size_hint_y=None,
            height=dp(56)
        )

        self.new_password = MDTextField(
            hint_text="Новый пароль",
            mode="filled",
            password=True,
            size_hint_y=None,
            height=dp(56)
        )

        self.confirm_password = MDTextField(
            hint_text="Подтвердите новый пароль",
            mode="filled",
            password=True,
            size_hint_y=None,
            height=dp(56)
        )

        content.add_widget(self.old_password)
        content.add_widget(self.new_password)
        content.add_widget(self.confirm_password)

        cancel_btn = MDButton(
            text="Отмена",
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            on_release=lambda x: self.change_password_dialog.dismiss(),
            style="text"
        )

        change_btn = MDButton(
            text="Сменить",
            theme_text_color="Custom",
            text_color=theme.PRIMARY,
            on_release=self.do_change_password,
            style="text"
        )

        self.change_password_dialog = MDDialog(
            title="Смена пароля",
            type="custom",
            content_cls=content,
            buttons=[cancel_btn, change_btn]
        )
        self.change_password_dialog.open()

    def do_change_password(self, instance):
        """Выполняет смену пароля"""
        old = self.old_password.text
        new = self.new_password.text
        confirm = self.confirm_password.text

        if not old or not new:
            notify.warning("Заполните все поля")
            return

        if new != confirm:
            notify.warning("Новые пароли не совпадают")
            return

        if len(new) < 4:
            notify.warning("Пароль должен быть не менее 4 символов")
            return

        if len(new) > 72:
            notify.warning("Пароль слишком длинный (максимум 72 символа)")
            return

        notify.info("Функция смены пароля будет добавлена в следующей версии")
        self.change_password_dialog.dismiss()

    def logout(self, instance):
        """Выход из аккаунта"""

        def on_logout_success(result):
            notify.success("Вы вышли из аккаунта")

            app = MDApp.get_running_app()
            if hasattr(app, 'bottom_nav') and app.bottom_nav:
                app.bottom_nav.switch_tab("home")

            if hasattr(app, 'home_screen') and app.home_screen:
                app.home_screen.check_auth(0)

        def on_logout_failure(req, error):
            notify.error("Ошибка выхода")
            logger.error(f'Ошибка выхода: {error}')

        api.logout(
            on_success=on_logout_success,
            on_failure=on_logout_failure
        )

    def on_pre_enter(self):
        return super().on_pre_enter()

    def on_enter(self):
        return super().on_enter()