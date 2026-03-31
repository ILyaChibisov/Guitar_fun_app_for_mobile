# screens/profile_screen.py
"""
Экран профиля пользователя
"""
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import MDSnackbar
from kivy.metrics import dp
from kivy.clock import Clock
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api

logger = screen_logger('Profile')


def show_snackbar(message):
    """Показывает уведомление"""
    snack = MDSnackbar()
    snack.text = message
    snack.snackbar_x = "10dp"
    snack.snackbar_y = "10dp"
    snack.radius = [theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL,
                    theme.CORNER_RADIUS_SMALL, theme.CORNER_RADIUS_SMALL]
    snack.open()


class ProfileScreen(MDScreen):
    """Экран профиля пользователя"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'profile'
        self.user = None
        self.change_password_dialog = None
        self._data_loaded = False  # Флаг для предотвращения повторной загрузки

        # Устанавливаем цвет фона
        from kivy.graphics import Color, Rectangle
        from kivy.utils import rgba
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Кнопка назад
        self.back_btn = MDIconButton(
            icon="arrow-left",
            pos_hint={'x': 0, 'top': 1},
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            on_release=self.go_back
        )
        self.add_widget(self.back_btn)

        # Основной контейнер
        from kivymd.uix.scrollview import MDScrollView
        scroll = MDScrollView(size_hint=(1, 1))

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
            font_style="H4",
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
            font_style="H1",
            halign="center",
            size_hint_y=None,
            height=dp(80),
            theme_text_color="Primary"
        )

        self.username_label = MDLabel(
            text="",
            font_style="H5",
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
            font_style="H6",
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
        email_icon = MDIconButton(icon="email", size_hint=(None, 1), width=dp(40),
                                  theme_text_color="Custom", text_color=theme.TEXT_SECONDARY)
        self.email_label = MDLabel(text="", font_style="Body1", theme_text_color="Secondary")
        email_box.add_widget(email_icon)
        email_box.add_widget(self.email_label)

        # Полное имя
        name_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        name_icon = MDIconButton(icon="account", size_hint=(None, 1), width=dp(40),
                                 theme_text_color="Custom", text_color=theme.TEXT_SECONDARY)
        self.fullname_label = MDLabel(text="", font_style="Body1", theme_text_color="Secondary")
        name_box.add_widget(name_icon)
        name_box.add_widget(self.fullname_label)

        # Роль
        role_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        role_icon = MDIconButton(icon="shield-account", size_hint=(None, 1), width=dp(40),
                                 theme_text_color="Custom", text_color=theme.TEXT_SECONDARY)
        self.role_label = MDLabel(text="", font_style="Body1", theme_text_color="Secondary")
        role_box.add_widget(role_icon)
        role_box.add_widget(self.role_label)

        # Дата регистрации
        date_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8)
        )
        date_icon = MDIconButton(icon="calendar", size_hint=(None, 1), width=dp(40),
                                 theme_text_color="Custom", text_color=theme.TEXT_SECONDARY)
        self.date_label = MDLabel(text="", font_style="Body1", theme_text_color="Secondary")
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

        change_password_btn = MDRaisedButton(
            text="Сменить пароль",
            icon="lock",
            size_hint=(1, None),
            height=dp(44),
            md_bg_color=theme.PRIMARY,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=self.show_change_password_dialog
        )
        change_password_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4

        # Кнопка админ-панели (видна только администраторам)
        self.admin_btn = MDRaisedButton(
            text="👑 Админ-панель",
            icon="shield-account",
            size_hint=(1, None),
            height=dp(44),
            md_bg_color=theme.PRIMARY_DARK,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            on_release=self.open_admin_panel
        )
        self.admin_btn.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.admin_btn.opacity = 0
        self.admin_btn.disabled = True

        logout_btn = MDRaisedButton(
            text="Выйти из аккаунта",
            icon="logout",
            size_hint=(1, None),
            height=dp(44),
            md_bg_color=[0.9, 0.9, 0.9, 1],
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            on_release=self.logout
        )
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

        # Загружаем данные пользователя (только один раз)
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
        # Защита от повторной загрузки
        if self._data_loaded:
            return
        self._data_loaded = True

        print("🔴 ProfileScreen: load_user_data ВЫЗВАН")
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

        # Проверяем, что ошибка связана с авторизацией
        if 'Not authenticated' in error_msg or 'Invalid token' in error_msg:
            logger.info('Токен недействителен, очищаем и показываем авторизацию')
            api._clear_tokens()
            show_snackbar("🔐 Сессия истекла. Пожалуйста, войдите снова.")

            # Закрываем экран профиля и показываем окно авторизации
            self.go_back(None)

            # Показываем окно авторизации
            app = MDApp.get_running_app()
            if hasattr(app, 'home_screen') and app.home_screen:
                app.home_screen.show_auth_modal()
        else:
            show_snackbar("❌ Не удалось загрузить данные профиля")
            self.go_back(None)

    def update_ui(self):
        """Обновляет интерфейс данными пользователя"""
        if not self.user:
            return

        username = self.user.get('username', 'user')
        email = self.user.get('email', 'не указан')
        full_name = self.user.get('full_name') or 'не указано'
        role = self.user.get('role', 'user')

        # Отображаем роль на русском
        role_display = {
            'admin': '👑 Администратор',
            'user': '👤 Пользователь',
            'moderator': '🛡️ Модератор'
        }.get(role, f'👤 {role}')

        self.username_label.text = f"@{username}"
        self.email_label.text = email
        self.fullname_label.text = full_name
        self.role_label.text = role_display

        # Показываем кнопку админки, если пользователь - администратор
        if api.is_admin():
            self.admin_btn.opacity = 1
            self.admin_btn.disabled = False
        else:
            self.admin_btn.opacity = 0
            self.admin_btn.disabled = True

        # Форматируем дату регистрации
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
                # Проверяем, есть ли экран admin
                if 'admin' not in self.manager.screen_names:
                    from screens.admin_screen import AdminScreen
                    self.manager.add_widget(AdminScreen(name='admin'))
                self.manager.current = 'admin'
        else:
            show_snackbar("❌ У вас нет прав администратора")

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
            mode="round",
            password=True,
            size_hint_y=None,
            height=dp(56)
        )

        self.new_password = MDTextField(
            hint_text="Новый пароль",
            mode="round",
            password=True,
            size_hint_y=None,
            height=dp(56)
        )

        self.confirm_password = MDTextField(
            hint_text="Подтвердите новый пароль",
            mode="round",
            password=True,
            size_hint_y=None,
            height=dp(56)
        )

        content.add_widget(self.old_password)
        content.add_widget(self.new_password)
        content.add_widget(self.confirm_password)

        self.change_password_dialog = MDDialog(
            title="Смена пароля",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(
                    text="Отмена",
                    theme_text_color="Custom",
                    text_color=theme.TEXT_SECONDARY,
                    on_release=lambda x: self.change_password_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Сменить",
                    theme_text_color="Custom",
                    text_color=theme.PRIMARY,
                    on_release=self.do_change_password
                )
            ]
        )
        self.change_password_dialog.open()

    def do_change_password(self, instance):
        """Выполняет смену пароля"""
        old = self.old_password.text
        new = self.new_password.text
        confirm = self.confirm_password.text

        if not old or not new:
            show_snackbar("Заполните все поля")
            return

        if new != confirm:
            show_snackbar("Новые пароли не совпадают")
            return

        if len(new) < 4:
            show_snackbar("Пароль должен быть не менее 4 символов")
            return

        if len(new) > 72:
            show_snackbar("Пароль слишком длинный (максимум 72 символа)")
            return

        # TODO: Отправить запрос на смену пароля
        show_snackbar("Функция смены пароля будет добавлена в следующей версии")
        self.change_password_dialog.dismiss()

    def logout(self, instance):
        """Выход из аккаунта"""

        def on_logout_success(result):
            show_snackbar("👋 Вы вышли из аккаунта")

            # Переключаемся на вкладку "Главная"
            app = MDApp.get_running_app()
            if hasattr(app, 'bottom_nav') and app.bottom_nav:
                app.bottom_nav.switch_tab("home")

            # Обновляем главный экран
            if hasattr(app, 'home_screen') and app.home_screen:
                app.home_screen.check_auth(0)

        def on_logout_failure(req, error):
            show_snackbar("❌ Ошибка выхода")
            logger.error(f'Ошибка выхода: {error}')

        api.logout(
            on_success=on_logout_success,
            on_failure=on_logout_failure
        )

    def on_pre_enter(self):
        """Вызывается перед входом на экран"""
        print("🔴 PROFILE SCREEN: on_pre_enter ВЫЗВАН")
        return super().on_pre_enter()

    def on_enter(self):
        """Вызывается при входе на экран"""
        print("🔴 PROFILE SCREEN: on_enter ВЫЗВАН")
        return super().on_enter()