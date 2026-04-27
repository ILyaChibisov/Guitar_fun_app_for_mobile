# screens/profile_screen.py
"""
Экран профиля пользователя
"""
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton, MDButton, MDButtonText
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivy.metrics import dp, sp
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('Profile')


def hex_to_rgb(hex_color):
    """Конвертирует hex цвет в RGB список от 0 до 1"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


class ProfileScreen(MDScreen):
    """Экран профиля пользователя"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'profile'
        self.user = None
        self.change_password_dialog = None
        self._data_loaded = False
        self.bg_image = None

        # Фон
        self.md_bg_color = [0, 0, 0, 0]

        # Загружаем фон
        self.load_background()

        self.init_ui()

        logger.info('Экран профиля создан')

    def load_background(self):
        """Загружает фоновое изображение"""
        try:
            from data import load_asset_as_bytes
            from kivy.core.image import Image as CoreImage
            from io import BytesIO

            asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
            bg_data = None
            for name in asset_names:
                bg_data = load_asset_as_bytes(name)
                if bg_data:
                    logger.info(f"Фон загружен из ассета: {name}")
                    break

            if bg_data:
                img = CoreImage(BytesIO(bg_data), ext="jpg")
                with self.canvas.before:
                    Color(1, 1, 1, 1)
                    self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
                return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

        # fallback цвет
        with self.canvas.before:
            Color(0.46, 0.70, 0.71, 1)
            self.bg_image = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def init_ui(self):
        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0
        )

        # Отступ сверху для компенсации верхней панели
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # ============ ВЕРХНЯЯ ПАНЕЛЬ С КНОПКОЙ НАЗАД ============
        nav_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            spacing=dp(12),
            md_bg_color=[0, 0, 0, 0]
        )

        # Кнопка назад
        self.back_btn = MDIconButton(
            icon="arrow-left",
            style="standard",
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],
            on_release=self.go_back
        )

        # Заголовок
        title = MDLabel(
            text="Профиль",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        # Пустой виджет для баланса
        empty_widget = Widget(size_hint_x=None, width=dp(36))

        nav_row.add_widget(self.back_btn)
        nav_row.add_widget(title)
        nav_row.add_widget(empty_widget)

        # ============ ОСНОВНОЙ КОНТЕНТ ============
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0
        )

        content = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(8), dp(16), dp(85)],
            spacing=dp(12),
            size_hint_y=None,
            adaptive_height=True
        )

        # ============ КАРТОЧКА ПРОФИЛЯ (ИМЯ ПОЛЬЗОВАТЕЛЯ) ============
        profile_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(100),
            padding=dp(16),
            spacing=dp(8),
            elevation=2,
            radius=[theme.CORNER_RADIUS] * 4,
            md_bg_color=[0, 0, 0, 0.15],
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        # Имя пользователя (без @)
        self.username_label = MDLabel(
            text="",
            font_size=sp(24),
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )

        # Роль пользователя
        self.role_label = MDLabel(
            text="",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(25),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7]
        )

        profile_card.add_widget(self.username_label)
        profile_card.add_widget(self.role_label)

        # ============ КАРТОЧКА ИНФОРМАЦИИ ============
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(160),
            padding=dp(16),
            spacing=dp(10),
            elevation=2,
            radius=[theme.CORNER_RADIUS] * 4,
            md_bg_color=[0, 0, 0, 0.15],
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        info_title = MDLabel(
            text="📋 Информация",
            font_size=sp(14),
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        # Email
        self.email_label = MDLabel(
            text="",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_y=None,
            height=dp(28)
        )

        # Полное имя
        self.fullname_label = MDLabel(
            text="",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_y=None,
            height=dp(28)
        )

        # Дата регистрации
        self.date_label = MDLabel(
            text="",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
            size_hint_y=None,
            height=dp(28)
        )

        info_card.add_widget(info_title)
        info_card.add_widget(self.email_label)
        info_card.add_widget(self.fullname_label)
        info_card.add_widget(self.date_label)

        # ============ КАРТОЧКА С ДЕЙСТВИЯМИ ============
        actions_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(140),
            padding=dp(16),
            spacing=dp(12),
            elevation=2,
            radius=[theme.CORNER_RADIUS] * 4,
            md_bg_color=[0, 0, 0, 0.15],
            line_color=[1, 1, 1, 0.1],
            line_width=1
        )

        # Кнопка смены пароля
        change_password_btn = MDButton(
            style="outlined",
            theme_bg_color="Custom",
            md_bg_color=[1, 1, 1, 0.1],
            line_color=hex_to_rgb(theme.PRIMARY) + [1],
            line_width=1.5,
            on_release=self.show_change_password_dialog
        )
        change_password_btn.add_widget(MDButtonText(
            text="🔐 Сменить пароль",
            theme_text_color="Custom",
            text_color=hex_to_rgb(theme.PRIMARY) + [1],
            font_style="Label"
        ))

        # Кнопка админ-панели
        self.admin_btn = MDButton(
            style="outlined",
            theme_bg_color="Custom",
            md_bg_color=[1, 1, 1, 0.1],
            line_color=[0.9, 0.7, 0.2, 0.8],
            line_width=1.5,
            on_release=self.open_admin_panel
        )
        self.admin_btn.add_widget(MDButtonText(
            text="👑 Админ-панель",
            theme_text_color="Custom",
            text_color=[0.9, 0.7, 0.2, 0.9],
            font_style="Label"
        ))
        self.admin_btn.opacity = 0
        self.admin_btn.disabled = True

        # Кнопка выхода
        logout_btn = MDButton(
            style="outlined",
            theme_bg_color="Custom",
            md_bg_color=[1, 1, 1, 0.1],
            line_color=[0.9, 0.3, 0.3, 0.7],
            line_width=1.5,
            on_release=self.logout
        )
        logout_btn.add_widget(MDButtonText(
            text="🚪 Выйти из аккаунта",
            theme_text_color="Custom",
            text_color=[0.9, 0.3, 0.3, 0.9],
            font_style="Label"
        ))

        actions_card.add_widget(change_password_btn)
        actions_card.add_widget(self.admin_btn)
        actions_card.add_widget(logout_btn)

        content.add_widget(profile_card)
        content.add_widget(info_card)
        content.add_widget(actions_card)

        scroll.add_widget(content)

        main_layout.add_widget(nav_row)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

    def go_back(self, instance):
        """Возврат на главный экран"""
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_pre_enter(self):
        """Вызывается перед показом экрана - загружаем данные"""
        if not self._data_loaded:
            self.load_user_data()
        return super().on_pre_enter()

    def load_user_data(self, dt=None):
        """Загружает данные пользователя"""
        if self._data_loaded:
            return

        if api.user_data:
            self.user = api.user_data
            self._data_loaded = True
            self.update_ui()
        else:
            api.get_current_user(
                on_success=self.on_user_loaded,
                on_failure=self.on_user_load_failed
            )

    def on_user_loaded(self, user):
        self.user = user
        self._data_loaded = True
        self.update_ui()

    def on_user_load_failed(self, req, error):
        """Обработчик ошибки загрузки профиля"""
        error_msg = str(error)
        logger.error(f'Ошибка загрузки профиля: {error_msg}')

        if 'Not authenticated' in error_msg or 'Invalid token' in error_msg or '401' in error_msg:
            logger.info('Токен недействителен, очищаем')
            api._clear_tokens()
            notify.warning("Сессия истекла. Пожалуйста, войдите снова.")
            self.go_back(None)
        else:
            notify.error("Не удалось загрузить данные профиля")

    def update_ui(self):
        """Обновляет интерфейс данными пользователя"""
        if not self.user:
            return

        username = self.user.get('username', 'Пользователь')
        email = self.user.get('email', 'не указан')
        full_name = self.user.get('full_name') or 'не указано'
        role = self.user.get('role', 'user')

        role_display = {
            'admin': '👑 Администратор',
            'user': '👤 Пользователь',
            'moderator': '🛡️ Модератор'
        }.get(role, f'👤 {role}')

        # Имя пользователя (без @)
        self.username_label.text = username
        self.role_label.text = role_display
        self.email_label.text = f"📧 {email}"
        self.fullname_label.text = f"👤 {full_name}"

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
                self.date_label.text = f"📅 {dt.strftime('%d.%m.%Y')}"
            except:
                self.date_label.text = '📅 неизвестно'
        else:
            self.date_label.text = '📅 неизвестно'

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

        # Кнопки диалога
        cancel_btn = MDButton(
            style="text",
            on_release=lambda x: self.change_password_dialog.dismiss()
        )
        cancel_btn.add_widget(MDButtonText(text="Отмена"))

        change_btn = MDButton(
            style="text",
            on_release=self.do_change_password
        )
        change_btn.add_widget(MDButtonText(text="Сменить"))

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
            self.go_back(None)

        def on_logout_failure(req, error):
            notify.error("Ошибка выхода")
            logger.error(f'Ошибка выхода: {error}')

        api.logout(
            on_success=on_logout_success,
            on_failure=on_logout_failure
        )