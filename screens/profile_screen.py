# screens/profile_screen.py
"""
Экран профиля пользователя
"""
from kivymd.app import MDApp
from kivy.metrics import dp, sp
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.clock import Clock
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify
from utils.kivy_imports import (
    MDBoxLayout, MDLabel, MDCard, MDTextField, MDDialog, MDScreen, MDRaisedButton
)

logger = screen_logger('Profile')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


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
            if HAS_ASSETS:
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

    def _load_avatar(self):
        """Загружает аватар из ассета profile_png"""
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('profile_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.avatar_image.texture = img.texture
                    return True
            except Exception as e:
                logger.error(f"Ошибка загрузки аватара: {e}")

        # Если не загрузилась, показываем эмодзи
        self.avatar_image.source = ""
        self.avatar_image.text = "👤"
        return False

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

        # ============ ОСНОВНОЙ КОНТЕНТ ============
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0
        )

        content = MDBoxLayout(
            orientation='vertical',
            padding=[dp(16), dp(8), dp(16), dp(85)],
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True
        )

        # ============ АВАТАР И ИМЯ ПОЛЬЗОВАТЕЛЯ ============
        avatar_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(100),
            spacing=dp(8),
            padding=[dp(0), dp(8), dp(0), dp(8)]
        )

        # Аватар
        self.avatar_image = MDLabel(
            text="👤",
            font_size=sp(40),
            halign="center",
            size_hint_y=None,
            height=dp(50),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95]
        )
        # Пытаемся загрузить аватар из ассета
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('profile_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    # Создаем Image виджет для аватара
                    self.avatar_image = Image(
                        size_hint=(None, None),
                        size=(dp(50), dp(50)),
                        pos_hint={'center_x': 0.5},
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    self.avatar_image.texture = img.texture
            except Exception as e:
                logger.error(f"Ошибка загрузки аватара: {e}")

        # Имя пользователя
        self.username_label = MDLabel(
            text="",
            font_size=sp(18),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )

        avatar_box.add_widget(self.avatar_image)
        avatar_box.add_widget(self.username_label)

        # ============ КАРТОЧКА ИНФОРМАЦИИ ============
        info_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(210),
            padding=dp(16),
            spacing=dp(10),
            elevation=2,
            radius=[theme.CORNER_RADIUS] * 4,
            md_bg_color=[1, 1, 1, 0.95],
            line_color=[0.8, 0.8, 0.8, 0.3],
            line_width=1
        )

        # Email
        email_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
            spacing=dp(12)
        )
        email_icon = MDLabel(
            text="📧",
            font_size=sp(16),
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 0.8]
        )
        self.email_label = MDLabel(
            text="",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[0.2, 0.2, 0.2, 0.9],
            valign="middle",
            shorten=True,
            shorten_from="right"
        )
        email_box.add_widget(email_icon)
        email_box.add_widget(self.email_label)

        # Полное имя
        name_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(12)
        )
        name_icon = MDLabel(
            text="👤",
            font_size=sp(16),
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 0.8]
        )
        self.fullname_label = MDLabel(
            text="",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[0.2, 0.2, 0.2, 0.9],
            valign="middle",
            shorten=True,
            shorten_from="right"
        )
        name_box.add_widget(name_icon)
        name_box.add_widget(self.fullname_label)

        # Дата регистрации
        reg_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(12)
        )
        reg_icon = MDLabel(
            text="📅",
            font_size=sp(16),
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 0.8]
        )
        self.date_label = MDLabel(
            text="",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[0.2, 0.2, 0.2, 0.9],
            valign="middle"
        )
        reg_box.add_widget(reg_icon)
        reg_box.add_widget(self.date_label)

        # Подписка
        sub_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(12)
        )
        sub_icon = MDLabel(
            text="⭐",
            font_size=sp(16),
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 0.8]
        )
        self.subscription_label = MDLabel(
            text="Подписка: не активна",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[0.2, 0.2, 0.2, 0.9],
            valign="middle"
        )
        sub_box.add_widget(sub_icon)
        sub_box.add_widget(self.subscription_label)

        # Последний вход
        last_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(12)
        )
        last_icon = MDLabel(
            text="🕐",
            font_size=sp(16),
            size_hint_x=None,
            width=dp(30),
            theme_text_color="Custom",
            text_color=[0.3, 0.3, 0.3, 0.8]
        )
        self.last_login_label = MDLabel(
            text="",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[0.2, 0.2, 0.2, 0.9],
            valign="middle"
        )
        last_box.add_widget(last_icon)
        last_box.add_widget(self.last_login_label)

        info_card.add_widget(email_box)
        info_card.add_widget(name_box)
        info_card.add_widget(reg_box)
        info_card.add_widget(sub_box)
        info_card.add_widget(last_box)

        # ============ КНОПКИ (MDRaisedButton) ============
        primary_color = hex_to_rgb(theme.PRIMARY)
        primary_rgb = [primary_color[0], primary_color[1], primary_color[2], 1]

        # Контейнер для кнопок с отступами
        buttons_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(12),
            padding=[dp(16), dp(0), dp(16), dp(0)]
        )

        # Кнопка смены пароля
        change_password_btn = MDRaisedButton(
            text="Сменить пароль",
            size_hint=(1, None),
            height=dp(48),
            on_release=self.show_change_password_dialog
        )

        # Кнопка админ-панели
        self.admin_btn = MDRaisedButton(
            text="Админ-панель",
            size_hint=(1, None),
            height=dp(48),
            on_release=self.open_admin_panel
        )
        self.admin_btn.opacity = 0
        self.admin_btn.disabled = True

        # Кнопка выхода
        logout_btn = MDRaisedButton(
            text="Выйти из аккаунта",
            size_hint=(1, None),
            height=dp(48),
            on_release=self.logout
        )

        buttons_container.add_widget(change_password_btn)
        buttons_container.add_widget(self.admin_btn)
        buttons_container.add_widget(logout_btn)

        # Вычисляем высоту контейнера
        buttons_container.height = dp(48) * 3 + dp(24)

        content.add_widget(avatar_box)
        content.add_widget(info_card)
        content.add_widget(buttons_container)

        scroll.add_widget(content)

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
        last_login = self.user.get('last_login')
        subscription_days = self.user.get('subscription_days', 0)

        self.username_label.text = username
        self.email_label.text = email
        self.fullname_label.text = full_name

        # Форматируем последний вход
        if last_login:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                self.last_login_label.text = dt.strftime('%d.%m.%Y %H:%M')
            except:
                self.last_login_label.text = 'неизвестно'
        else:
            self.last_login_label.text = 'неизвестно'

        # Форматируем подписку
        if subscription_days > 0:
            self.subscription_label.text = f"Активна • осталось {subscription_days} дн."
        else:
            self.subscription_label.text = "Не активна"

        # Дата регистрации
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

        if api.is_admin():
            self.admin_btn.opacity = 1
            self.admin_btn.disabled = False
        else:
            self.admin_btn.opacity = 0
            self.admin_btn.disabled = True

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

        cancel_btn = MDRaisedButton(
            text="Отмена",
            on_release=lambda x: self.change_password_dialog.dismiss()
        )

        change_btn = MDRaisedButton(
            text="Сменить",
            on_release=self.do_change_password
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
            self.go_back(None)

        def on_logout_failure(req, error):
            notify.error("Ошибка выхода")
            logger.error(f'Ошибка выхода: {error}')

        api.logout(
            on_success=on_logout_success,
            on_failure=on_logout_failure
        )