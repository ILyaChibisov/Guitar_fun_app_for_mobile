# screens/profile_screen.py
"""
Экран профиля пользователя с настройками аккаунта.
Включает: смену логина, смену пароля, удаление аккаунта, выход,
компактную плашку статуса подписки (триал + промокоды)
и кнопку «Оформить подписку» (если подписки нет).

Версия с фиксом: subscription_end_date берётся из ответа
/users/me/subscription (status_data), а не из кэша api.user_data.
"""
from datetime import datetime

from kivymd.app import MDApp
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from state.settings_state import settings_state
from state.subscription_state import subscription_state
from utils.kivy_imports import (
    MDBoxLayout, MDLabel, MDCard, MDTextField, MDDialog,
    MDRaisedButton, MDIconButton, MDFlatButton,
)

logger = screen_logger('Profile')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


# ============ ЦВЕТА ПОДПИСКИ ============

SUB_COLOR_ACTIVE = [0.20, 0.75, 0.35, 1.0]      # зелёный
SUB_COLOR_EXPIRING = [0.95, 0.55, 0.15, 1.0]    # оранжевый (<=3 дней)
SUB_COLOR_INACTIVE = [0.60, 0.60, 0.60, 1.0]    # серый


class AdaptiveMDCard(MDCard):
    """Карточка, которая подстраивает высоту под содержимое"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))


class ProfileScreen(BaseScreen):
    """Экран профиля пользователя"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'profile'
        self.user = None
        self.change_password_dialog = None
        self.username_dialog = None
        self._data_loaded = False
        self.bg_image = None
        self._subscription_status = None

        # Компактная плашка подписки
        self.sub_box = None
        self.sub_line1 = None
        self.sub_line2 = None
        # Кнопка «Оформить подписку»
        self.buy_btn = None

        self._sub_listener_attached = False
        self._last_promos = []

        self.init_ui()
        self.load_background()

        logger.info('Экран профиля создан')

    # ============ ТЕМА / ЯЗЫК ============

    def update_theme_colors(self):
        if not self.sub_box:
            return
        theme_id = settings_state.theme
        if theme_id == 'light':
            self.sub_box.line_color = [0.1, 0.55, 0.3, 0.45]
            self.sub_box.md_bg_color = [1, 1, 1, 0.10]
        elif theme_id == 'dark':
            self.sub_box.line_color = [1.0, 0.5, 0.0, 0.40]
            self.sub_box.md_bg_color = [1, 1, 1, 0.04]
        else:  # green
            self.sub_box.line_color = [0.46, 0.70, 0.71, 0.45]
            self.sub_box.md_bg_color = [1, 1, 1, 0.05]

    def update_language(self):
        pass

    # ============ ФОН ============

    def load_background(self):
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

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    # ============ UI ============

    def init_ui(self):
        content_padding = layout_config.get_content_padding()

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True,
            padding=[content_padding[0], content_padding[1], content_padding[2], content_padding[3]]
        )

        # ============ АВАТАР И ИМЯ ============
        avatar_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(100),
            spacing=dp(8),
            padding=[dp(0), dp(8), dp(0), dp(8)]
        )

        self.avatar_icon = MDIconButton(
            icon="account-circle",
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            pos_hint={'center_x': 0.5},
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0.1],
            disabled=True
        )

        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('profile_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.avatar_icon = Image(
                        size_hint=(None, None),
                        size=(dp(60), dp(60)),
                        pos_hint={'center_x': 0.5},
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    self.avatar_icon.texture = img.texture
            except Exception as e:
                logger.error(f"Ошибка загрузки аватара: {e}")

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

        avatar_box.add_widget(self.avatar_icon)
        avatar_box.add_widget(self.username_label)

        # ============ ПЛАШКА ПОДПИСКИ (компактная) ============
        self.sub_box = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(64),
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(4),
            elevation=0,
            radius=[dp(10)] * 4,
            md_bg_color=[1, 1, 1, 0.05],
            line_color=[0.46, 0.70, 0.71, 0.45],
            line_width=1,
            opacity=0,
        )

        self.sub_line1 = MDLabel(
            text="",
            font_size=sp(13),
            bold=True,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            valign='middle',
            size_hint_y=None,
            height=dp(20),
            shorten=True,
            shorten_from="right",
        )

        self.sub_line2 = MDLabel(
            text="",
            font_size=sp(11),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            valign='middle',
            size_hint_y=None,
            height=dp(16),
            shorten=True,
            shorten_from="right",
        )

        self.sub_box.add_widget(self.sub_line1)
        self.sub_box.add_widget(self.sub_line2)

        # ============ КНОПКА «ОФОРМИТЬ ПОДПИСКУ» ============
        self.buy_btn = MDRaisedButton(
            text="Оформить подписку",
            size_hint=(1, None),
            height=dp(46),
            md_bg_color=theme.PRIMARY,
            text_color=[1, 1, 1, 1],
            font_size=sp(14),
            opacity=0,
            disabled=True,
            on_release=self._go_to_paywall,
        )

        # ============ КАРТОЧКА ИНФОРМАЦИИ ============
        info_card = AdaptiveMDCard(
            orientation='vertical',
            size_hint=(1, None),
            padding=dp(16),
            spacing=dp(10),
            elevation=2,
            radius=[theme.CORNER_RADIUS_SMALL] * 4,
            md_bg_color=[1, 1, 1, 0.95],
            line_color=[0.8, 0.8, 0.8, 0.3],
            line_width=1
        )

        email_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(12))
        email_icon = MDIconButton(icon="email", size_hint=(None, None), size=(dp(24), dp(24)),
                                  theme_icon_color="Custom", icon_color=[0.3, 0.3, 0.3, 0.7], disabled=True)
        self.email_label = MDLabel(text="", font_size=sp(12), theme_text_color="Custom",
                                   text_color=[0.2, 0.2, 0.2, 0.9], valign="middle", shorten=True,
                                   shorten_from="center", size_hint_x=1)
        email_box.add_widget(email_icon)
        email_box.add_widget(self.email_label)

        name_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(12))
        name_icon = MDIconButton(icon="account", size_hint=(None, None), size=(dp(24), dp(24)),
                                 theme_icon_color="Custom", icon_color=[0.3, 0.3, 0.3, 0.7], disabled=True)
        self.fullname_label = MDLabel(text="", font_size=sp(13), theme_text_color="Custom",
                                      text_color=[0.2, 0.2, 0.2, 0.9], valign="middle",
                                      shorten=True, shorten_from="right")
        name_box.add_widget(name_icon)
        name_box.add_widget(self.fullname_label)

        reg_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(12))
        reg_icon = MDIconButton(icon="calendar", size_hint=(None, None), size=(dp(24), dp(24)),
                                theme_icon_color="Custom", icon_color=[0.3, 0.3, 0.3, 0.7], disabled=True)
        self.date_label = MDLabel(text="", font_size=sp(13), theme_text_color="Custom",
                                  text_color=[0.2, 0.2, 0.2, 0.9], valign="middle")
        reg_box.add_widget(reg_icon)
        reg_box.add_widget(self.date_label)

        last_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32), spacing=dp(12))
        last_icon = MDIconButton(icon="clock-outline", size_hint=(None, None), size=(dp(24), dp(24)),
                                 theme_icon_color="Custom", icon_color=[0.3, 0.3, 0.3, 0.7], disabled=True)
        self.last_login_label = MDLabel(text="", font_size=sp(12), theme_text_color="Custom",
                                        text_color=[0.2, 0.2, 0.2, 0.9], valign="middle")
        last_box.add_widget(last_icon)
        last_box.add_widget(self.last_login_label)

        info_card.add_widget(email_box)
        info_card.add_widget(name_box)
        info_card.add_widget(reg_box)
        info_card.add_widget(last_box)

        # ============ КНОПКИ ДЕЙСТВИЙ ============
        buttons_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(12),
            padding=[dp(0), dp(16), dp(0), dp(0)]
        )
        buttons_container.bind(minimum_height=buttons_container.setter('height'))

        change_username_btn = MDRaisedButton(
            text="Сменить логин",
            size_hint=(1, None),
            height=dp(48),
            on_release=self.show_change_username_dialog
        )
        buttons_container.add_widget(change_username_btn)

        change_password_btn = MDRaisedButton(
            text="Сменить пароль",
            size_hint=(1, None),
            height=dp(48),
            on_release=self.show_change_password_dialog
        )
        buttons_container.add_widget(change_password_btn)

        delete_account_btn = MDRaisedButton(
            text="Удалить аккаунт",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=[0.8, 0.2, 0.2, 1],
            on_release=self.confirm_delete_account
        )
        buttons_container.add_widget(delete_account_btn)

        logout_btn = MDRaisedButton(
            text="Выйти из аккаунта",
            size_hint=(1, None),
            height=dp(48),
            on_release=self.logout
        )
        buttons_container.add_widget(logout_btn)

        content.add_widget(avatar_box)
        content.add_widget(self.sub_box)
        content.add_widget(self.buy_btn)
        content.add_widget(info_card)
        content.add_widget(buttons_container)
        content.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.build_ui(content_widget=content, use_scroll=True)

        self.update_theme_colors()

    # ============ НАВИГАЦИЯ ============

    def _go_to_paywall(self, *args):
        if self.manager and self.manager.has_screen('paywall'):
            self.manager.current = 'paywall'
        else:
            notify.warning("Экран оплаты временно недоступен")

    # ============ ПОДПИСКА ============

    def _render_sub_compact(self, user: dict, status_data: dict | None, active_promos: list):
        """
        Плашка подписки + кнопка «Оформить».
        - Админ → скрыто всё.
        - status='exhausted' → красный «Подписка закончилась» + кнопка.
        - status='active'    → зелёный/оранжевый «Осталось N дн.».
        - Активный промокод → вторая строка.
        """
        role = (user or {}).get("role", "user")
        if role == "admin":
            self.sub_box.opacity = 0
            self.buy_btn.opacity = 0
            self.buy_btn.disabled = True
            return

        status = (status_data or {}).get("status")

        end_str = (user or {}).get("subscription_end_date")
        days_left = 0
        end_dt = None
        if end_str:
            try:
                end_dt = datetime.fromisoformat(str(end_str).replace("Z", "+00:00"))
                days_left = max(0, (end_dt - datetime.utcnow()).days)
            except Exception:
                days_left = 0

        now = datetime.utcnow()
        active_code = None
        active_days = 0
        active_valid_until = None
        for p in (active_promos or []):
            vu = p.get("valid_until")
            if not vu:
                continue
            try:
                vu_dt = datetime.fromisoformat(str(vu).replace("Z", "+00:00"))
            except Exception:
                continue
            if vu_dt > now:
                active_code = p.get("code")
                active_days = int(p.get("days_added", 0) or 0)
                active_valid_until = vu_dt
                break

        # --- Плашка ---
        if status == "exhausted" or (days_left <= 0 and not active_code):
            # Подписка закончилась — показываем красную плашку, если есть end_date
            if end_dt:
                self.sub_line1.text = "Подписка закончилась"
                self.sub_line1.text_color = [0.95, 0.30, 0.30, 1.0]
                self.sub_line2.text = f"Истекла {end_dt.strftime('%d.%m.%Y')}"
                self.sub_box.height = dp(50)
                self.sub_box.opacity = 1
            else:
                self.sub_box.opacity = 0
        else:
            if days_left > 0 and end_dt:
                date_str = end_dt.strftime("%d.%m.%Y")
                self.sub_line1.text = f"Активна подписка — осталось {days_left} дн. (до {date_str})"
                if days_left <= 3:
                    self.sub_line1.text_color = SUB_COLOR_EXPIRING
                else:
                    self.sub_line1.text_color = SUB_COLOR_ACTIVE
            elif active_code:
                self.sub_line1.text = f"Активирован промокод «{active_code}»"
                self.sub_line1.text_color = SUB_COLOR_ACTIVE
            else:
                self.sub_line1.text = "Подписка не активна"
                self.sub_line1.text_color = SUB_COLOR_INACTIVE

            if active_code:
                vu_str = active_valid_until.strftime("%d.%m.%Y") if active_valid_until else "—"
                self.sub_line2.text = (
                    f"🎫 Промокод «{active_code}»: +{active_days} дн. "
                    f"(действует до {vu_str})"
                )
                self.sub_box.height = dp(64)
            else:
                self.sub_line2.text = ""
                self.sub_box.height = dp(40)

            self.sub_box.opacity = 1

        # --- Кнопка «Оформить» ---
        if days_left <= 0:
            self.buy_btn.opacity = 1
            self.buy_btn.disabled = False
        else:
            self.buy_btn.opacity = 0
            self.buy_btn.disabled = True

    def _on_sub_snapshot(self, snapshot: dict):
        """Слушатель subscription_state — перерисовывает плашку из снапшота."""
        user = dict(self.user or {})
        end_date = snapshot.get("subscription_end_date")
        if end_date is not None:
            if isinstance(end_date, str):
                user["subscription_end_date"] = end_date
            else:
                try:
                    user["subscription_end_date"] = end_date.isoformat()
                except Exception:
                    pass
        if self.user and "role" in self.user:
            user["role"] = self.user["role"]
        self._render_sub_compact(user, snapshot, self._last_promos)

    def refresh_subscription(self):
        """
        Запрос /users/me/subscription + активные промокоды.
        Рисует плашку по status_data (не по кэшу).
        """

        def _on_status(status_data):
            self._subscription_status = status_data

            end_iso = status_data.get("subscription_end_date")

            if self.user is not None:
                self.user = dict(self.user)
                self.user["subscription_end_date"] = end_iso
            if api.user_data is not None:
                api.user_data = dict(api.user_data)
                api.user_data["subscription_end_date"] = end_iso

            try:
                subscription_state.update_from_response(status_data, self.user)
            except Exception as e:
                logger.warning(f"subscription_state.update: {e}")

            def _on_promos(resp):
                self._last_promos = (resp or {}).get("promocodes", []) if isinstance(resp, dict) else []
                self._render_sub_compact(
                    user={
                        "role": (self.user or {}).get("role", "user"),
                        "subscription_end_date": end_iso,
                    },
                    status_data=status_data,
                    active_promos=self._last_promos,
                )

            api.get_my_active_promos(
                on_success=_on_promos,
                on_failure=lambda req, err: self._render_sub_compact(
                    user={
                        "role": (self.user or {}).get("role", "user"),
                        "subscription_end_date": end_iso,
                    },
                    status_data=status_data,
                    active_promos=[],
                ),
            )

        def _on_fail(req, err):
            logger.warning(f"check_subscription: {err}")
            self._render_sub_compact(self.user or {}, None, [])

        api.check_subscription(on_success=_on_status, on_failure=_on_fail)


    # ============ ЖИЗНЕННЫЙ ЦИКЛ ============

    def on_pre_enter(self):
        if not api.is_authenticated():
            logger.info("Не авторизован, возвращаемся на home")
            if hasattr(self, 'manager') and self.manager:
                self.manager.current = 'home'
            return

        self._data_loaded = False
        self.load_user_data()
        return super().on_pre_enter()

    def on_enter(self):
        super().on_enter()

        # Подписка на изменения subscription_state
        if not self._sub_listener_attached:
            subscription_state.add_listener(self._on_sub_snapshot)
            self._sub_listener_attached = True

        # Сразу отрисовать последний известный снапшот
        if subscription_state.status:
            self._on_sub_snapshot({
                "status": subscription_state.status,
                "days_left": subscription_state.days_left,
                "seconds_left": subscription_state.seconds_left,
                "is_admin": subscription_state.is_admin,
                "subscription_end_date": subscription_state.subscription_end_date,
            })

        self.refresh_subscription()

    def on_leave(self):
        if self._sub_listener_attached:
            subscription_state.remove_listener(self._on_sub_snapshot)
            self._sub_listener_attached = False
        super().on_leave()

    # ============ ЗАГРУЗКА ДАННЫХ ============

    def load_user_data(self, dt=None):
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
        error_msg = str(error)
        logger.error(f'Ошибка загрузки профиля: {error_msg}')

        if 'Not authenticated' in error_msg or 'Invalid token' in error_msg or '401' in error_msg:
            api._clear_tokens()
            notify.warning("Сессия истекла. Пожалуйста, войдите снова.")
            if hasattr(self, 'manager') and self.manager:
                self.manager.current = 'home'
        else:
            notify.error("Не удалось загрузить данные профиля")
            if hasattr(self, 'manager') and self.manager:
                self.manager.current = 'home'

    def update_ui(self):
        if not self.user:
            return

        username = self.user.get('username', 'Пользователь')
        email = self.user.get('email', 'не указан')
        full_name = self.user.get('full_name') or 'не указано'
        last_login = self.user.get('last_login')

        self.username_label.text = username
        self.email_label.text = email
        self.fullname_label.text = full_name

        if last_login:
            try:
                dt = datetime.fromisoformat(str(last_login).replace('Z', '+00:00'))
                self.last_login_label.text = dt.strftime('%d.%m.%Y %H:%M')
            except Exception:
                self.last_login_label.text = 'неизвестно'
        else:
            self.last_login_label.text = 'неизвестно'

        created_at = self.user.get('created_at')
        if created_at:
            try:
                dt = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                self.date_label.text = dt.strftime('%d.%m.%Y')
            except Exception:
                self.date_label.text = 'неизвестно'
        else:
            self.date_label.text = 'неизвестно'

    # ============ СМЕНА ЛОГИНА ============

    def show_change_username_dialog(self, instance):
        if self.username_dialog:
            self.username_dialog.dismiss()

        content = MDBoxLayout(
            orientation='vertical', spacing=dp(12), padding=dp(16),
            size_hint_y=None, height=dp(100)
        )

        self.new_username_field = MDTextField(
            hint_text="Новый логин",
            mode="fill",
            size_hint_y=None,
            height=dp(56)
        )
        content.add_widget(self.new_username_field)

        def do_change(btn):
            new_name = self.new_username_field.text.strip()
            if len(new_name) < 3:
                notify.warning("Логин должен быть не менее 3 символов")
                return

            def on_success(res):
                notify.success("Логин успешно изменен")
                self.username_dialog.dismiss()
                self.username_label.text = new_name
                if api.user_data:
                    api.user_data['username'] = new_name

                app = MDApp.get_running_app()
                if app and hasattr(app, 'sidebar'):
                    app.sidebar.update_user_info()

            def on_failure(req, err):
                notify.error(f"Ошибка: {err}")

            api.change_username(new_name, on_success=on_success, on_failure=on_failure)

        self.username_dialog = MDDialog(
            title="Смена логина",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Отмена", on_release=lambda x: self.username_dialog.dismiss()),
                MDRaisedButton(text="Сменить", on_release=do_change)
            ]
        )
        self.username_dialog.open()

    # ============ СМЕНА ПАРОЛЯ ============

    def show_change_password_dialog(self, instance):
        if self.change_password_dialog:
            self.change_password_dialog.dismiss()

        content = MDBoxLayout(
            orientation='vertical', spacing=dp(12), padding=dp(16),
            size_hint_y=None, height=dp(200)
        )

        self.old_password = MDTextField(
            hint_text="Текущий пароль", mode="fill", password=True,
            size_hint_y=None, height=dp(56)
        )
        self.new_password = MDTextField(
            hint_text="Новый пароль", mode="fill", password=True,
            size_hint_y=None, height=dp(56)
        )
        self.confirm_password = MDTextField(
            hint_text="Подтвердите новый пароль", mode="fill", password=True,
            size_hint_y=None, height=dp(56)
        )

        content.add_widget(self.old_password)
        content.add_widget(self.new_password)
        content.add_widget(self.confirm_password)

        def do_change(btn):
            old = self.old_password.text
            new = self.new_password.text
            confirm = self.confirm_password.text

            if not old or not new:
                notify.warning("Заполните все поля")
                return
            if new != confirm:
                notify.warning("Новые пароли не совпадают")
                return
            if len(new) < 6:
                notify.warning("Пароль должен быть не менее 6 символов")
                return

            def on_success(res):
                notify.success("Пароль успешно изменен")
                self.change_password_dialog.dismiss()

            def on_failure(req, err):
                notify.error(f"Ошибка: {err}")

            api.change_password(old, new, on_success=on_success, on_failure=on_failure)

        self.change_password_dialog = MDDialog(
            title="Смена пароля",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Отмена", on_release=lambda x: self.change_password_dialog.dismiss()),
                MDRaisedButton(text="Сменить", on_release=do_change)
            ]
        )
        self.change_password_dialog.open()

    # ============ УДАЛЕНИЕ АККАУНТА ============

    def confirm_delete_account(self, instance):
        def delete_confirmed(btn_instance):
            dialog.dismiss()

            def on_success(res):
                notify.success("Аккаунт удален")
                app = MDApp.get_running_app()
                if app and hasattr(app, '_on_logout_done'):
                    app._on_logout_done()
                if hasattr(self, 'manager') and self.manager:
                    self.manager.current = 'home'
                    if app:
                        Clock.schedule_once(lambda dt: app.open_profile(), 0.5)

            def on_failure(req, err):
                notify.error(f"Ошибка удаления: {err}")

            api.delete_account(on_success=on_success, on_failure=on_failure)

        dialog = MDDialog(
            title="Удаление аккаунта",
            text="Вы уверены, что хотите навсегда удалить свой аккаунт?\nЭто действие нельзя отменить.",
            buttons=[
                MDFlatButton(text="Отмена", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="Удалить",
                    md_bg_color=[0.8, 0.2, 0.2, 1],
                    on_release=delete_confirmed
                ),
            ],
        )
        dialog.open()

    def logout(self, instance):
        def on_logout_success(result):
            notify.success("Вы вышли из аккаунта")
            api._clear_tokens()
            api.user_data = None

            app = MDApp.get_running_app()
            if app and hasattr(app, '_on_logout_done'):
                app._on_logout_done()

            if hasattr(self, 'manager') and self.manager:
                self.manager.current = 'home'
                if app:
                    Clock.schedule_once(lambda dt: app.open_profile(), 0.5)

        def on_logout_failure(req, error):
            notify.error("Ошибка выхода")
            logger.error(f'Ошибка выхода: {error}')

        api.logout(
            on_success=on_logout_success,
            on_failure=on_logout_failure
        )