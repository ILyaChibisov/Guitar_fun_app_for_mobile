# screens/paywall_screen.py
"""
Экран оплаты подписки (Paywall).

- Загружает тарифы с сервера (GET /subscription/plans).
- Показывает 3 тарифа: 1 / 3 / 12 мес.
- Кнопка «Купить» → POST /subscription/purchase (пока заглушка).
- Кнопка «У меня есть промокод» → переход на экран promo.
"""
import threading
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.animation import Animation
from io import BytesIO

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import (
    MDRaisedButton, MDFlatButton, MDIconButton,
)
from kivymd.uix.behaviors import CircularRippleBehavior

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from state.settings_state import settings_state

logger = screen_logger('Paywall')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


# ============ ЦВЕТА ============

POPULAR_BG = [0.46, 0.70, 0.71, 0.20]
POPULAR_BORDER = [0.46, 0.70, 0.71, 0.9]
NORMAL_BG = [1, 1, 1, 0.05]
NORMAL_BORDER = [1, 1, 1, 0.12]


def _get_text_primary():
    return [1, 1, 1, 0.95] if settings_state.theme != 'light' else [0.15, 0.15, 0.15, 1]


def _get_text_secondary():
    return [1, 1, 1, 0.6] if settings_state.theme != 'light' else [0.45, 0.45, 0.45, 1]


# ============ КАРТОЧКА ТАРИФА ============

class PlanCard(CircularRippleBehavior, MDCard):
    """Карточка одного тарифа."""

    def __init__(self, plan: dict, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.plan = plan
        self.on_click_callback = on_click

        is_popular = bool(plan.get('popular'))
        self._is_popular = is_popular

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(96)
        self.radius = [dp(14)] * 4
        self.elevation = 4 if is_popular else 1
        self.ripple_scale = 0.97
        self.padding = [dp(16), dp(12), dp(16), dp(12)]
        self.spacing = dp(4)
        self.md_bg_color = POPULAR_BG if is_popular else NORMAL_BG
        self.line_color = POPULAR_BORDER if is_popular else NORMAL_BORDER
        self.line_width = 2 if is_popular else 1

        # Верхняя строка: название + метка popular
        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(28),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
        )

        title_label = MDLabel(
            text=plan.get('title', '—'),
            font_size=sp(17),
            bold=True,
            theme_text_color="Custom",
            text_color=_get_text_primary(),
            size_hint_x=None,
            width=dp(140),
        )
        top_row.add_widget(title_label)
        top_row.add_widget(Widget())

        if is_popular:
            badge = MDCard(
                size_hint=(None, None),
                size=(dp(84), dp(22)),
                radius=[dp(6)] * 4,
                elevation=0,
                md_bg_color=[0.46, 0.70, 0.71, 0.9],
                padding=0,
            )
            badge.add_widget(MDLabel(
                text="ВЫГОДНО",
                font_size=sp(9),
                bold=True,
                halign='center',
                valign='middle',
                theme_text_color="Custom",
                text_color=[1, 1, 1, 1],
            ))
            top_row.add_widget(badge)

        # Цена + описание
        info_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
        )
        price_label = MDLabel(
            text=f"{plan.get('price_rub', 0)} ₽",
            font_size=sp(16),
            bold=True,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            size_hint_x=None,
            width=dp(110),
        )
        desc_label = MDLabel(
            text=plan.get('description', ''),
            font_size=sp(11),
            theme_text_color="Custom",
            text_color=_get_text_secondary(),
            size_hint_x=1,
            shorten=True,
            shorten_from='right',
        )
        info_row.add_widget(price_label)
        info_row.add_widget(desc_label)

        # Нижняя строка: дней + скидка
        bottom_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(18),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
        )
        days_label = MDLabel(
            text=f"{plan.get('days', 0)} дней",
            font_size=sp(11),
            theme_text_color="Custom",
            text_color=_get_text_secondary(),
            size_hint_x=1,
        )
        bottom_row.add_widget(days_label)

        discount = int(plan.get('discount_percent', 0) or 0)
        if discount > 0:
            disc_label = MDLabel(
                text=f"−{discount}%",
                font_size=sp(11),
                bold=True,
                halign='right',
                theme_text_color="Custom",
                text_color=[0.95, 0.55, 0.15, 1],
                size_hint_x=None,
                width=dp(50),
            )
            bottom_row.add_widget(disc_label)

        self.add_widget(top_row)
        self.add_widget(info_row)
        self.add_widget(bottom_row)

        self.bind(on_release=self._on_click)

    def _on_click(self, *args):
        Animation(opacity=0.7, duration=0.05).start(self)
        Clock.schedule_once(
            lambda dt: Animation(opacity=1, duration=0.1).start(self), 0.05
        )
        if self.on_click_callback:
            self.on_click_callback(self.plan)


# ============ ЭКРАН ============

class PaywallScreen(BaseScreen):
    """Экран оплаты подписки."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'paywall'
        self.bg_image = None
        self._plans = []
        self._loading = False

        self.init_ui()
        self.load_background()

        logger.info('PaywallScreen создан')

    # ============ ФОН ============

    def load_background(self):
        try:
            if HAS_ASSETS:
                for name in ("background_jpg", "background", "bg", "BACKGROUND_JPG"):
                    data = load_asset_as_bytes(name)
                    if data:
                        img = CoreImage(BytesIO(data), ext="jpg")
                        with self.canvas.before:
                            Color(1, 1, 1, 1)
                            self.bg_image = Rectangle(
                                texture=img.texture, pos=self.pos, size=self.size
                            )
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
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(12),
            size_hint_y=None,
            adaptive_height=True,
            padding=[0, 0, 0, dp(20)],
        )

        # Заголовок
        title = MDLabel(
            text="Подписка GuitarFuns",
            font_size=sp(24),
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=_get_text_primary(),
        )
        content.add_widget(title)

        subtitle = MDLabel(
            text="Безлимитный доступ ко всем функциям приложения",
            font_size=sp(13),
            halign='center',
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=_get_text_secondary(),
        )
        content.add_widget(subtitle)

        # Преимущества
        perks_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(140),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(8),
            radius=[dp(14)] * 4,
            elevation=1,
            md_bg_color=[1, 1, 1, 0.05],
            line_color=[1, 1, 1, 0.12],
            line_width=1,
        )
        for perk in [
            "🎸 Безлимитный доступ к песням и аккордам",
            "📖 Полный словарь терминов",
            "⏱ Без ограничения по времени",
            "🎁 Поддержка проекта",
        ]:
            perks_card.add_widget(MDLabel(
                text=perk,
                font_size=sp(13),
                theme_text_color="Custom",
                text_color=_get_text_primary(),
                size_hint_y=None,
                height=dp(26),
                shorten=True,
                shorten_from='right',
            ))
        content.add_widget(perks_card)

        # Заголовок тарифов
        plans_title = MDLabel(
            text="Выберите тариф",
            font_size=sp(16),
            bold=True,
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=_get_text_primary(),
        )
        content.add_widget(plans_title)

        # Контейнер под карточки тарифов
        self.plans_box = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            adaptive_height=True,
            md_bg_color=[0, 0, 0, 0],
        )
        content.add_widget(self.plans_box)

        # Плейсхолдер
        self._render_placeholder("Загрузка тарифов…")

        # Кнопка «У меня есть промокод»
        self.promo_btn = MDFlatButton(
            text="У меня есть промокод",
            size_hint=(1, None),
            height=dp(42),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            on_release=self._go_to_promo,
        )
        content.add_widget(self.promo_btn)

        # Примечание
        note = MDLabel(
            text="Оплата через защищённый платёжный шлюз.\n"
                 "Подписка автоматически продлевается, если не отменить.",
            font_size=sp(10),
            halign='center',
            size_hint_y=None,
            height=dp(36),
            theme_text_color="Custom",
            text_color=_get_text_secondary(),
        )
        content.add_widget(note)

        self.build_ui(content_widget=content, use_scroll=True)

    # ============ ЗАГРУЗКА ТАРИФОВ ============

    def _render_placeholder(self, text: str):
        self.plans_box.clear_widgets()
        self.plans_box.add_widget(MDLabel(
            text=text,
            halign='center',
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=_get_text_secondary(),
            size_hint_y=None,
            height=dp(60),
        ))

    def load_plans(self):
        if self._loading:
            return
        self._loading = True

        def worker():
            result = api.get_subscription_plans_sync()
            Clock.schedule_once(lambda dt: self._on_plans_loaded(result), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _on_plans_loaded(self, result: dict):
        self._loading = False
        if not isinstance(result, dict):
            self._render_placeholder("Не удалось загрузить тарифы")
            return

        plans = result.get('plans', []) or []
        if not plans:
            self._render_placeholder("Тарифы временно недоступны")
            return

        self._plans = plans
        self.plans_box.clear_widgets()
        for plan in plans:
            card = PlanCard(plan=plan, on_click=self._on_plan_selected)
            self.plans_box.add_widget(card)

    # ============ ПОКУПКА ============

    def _on_plan_selected(self, plan: dict):
        plan_id = plan.get('id')
        title = plan.get('title', 'тариф')
        price = plan.get('price_rub', 0)
        days = plan.get('days', 0)

        # Диалог подтверждения
        def confirm(btn):
            dlg.dismiss()
            self._do_purchase(plan_id)

        dlg = MDDialog(
            title=f"Купить «{title}»?",
            text=(
                f"Будет списано {price} ₽\n"
                f"Подписка будет активна {days} дней."
            ),
            buttons=[
                MDFlatButton(text="Отмена", on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(
                    text=f"Купить за {price} ₽",
                    md_bg_color=theme.PRIMARY,
                    on_release=confirm,
                ),
            ],
        )
        dlg.open()

    def _do_purchase(self, plan_id: str):
        def on_success(res):
            msg = res.get("message", "Подписка активирована")
            notify.success(msg)
            logger.info(f"✅ Покупка: {msg}")

            # Обновляем данные и статус подписки
            self._refresh_after_purchase()

        def on_failure(req, err):
            notify.error(str(err))

        api.purchase_subscription(
            plan_id=plan_id,
            on_success=on_success,
            on_failure=on_failure,
        )

    def _refresh_after_purchase(self):
        """После покупки — обновляем user, статус, профиль, home-плашку."""
        def _on_user(user):
            if user:
                api.user_data = user

            def _on_status(status_data):
                try:
                    app = MDApp.get_running_app()
                    if app and app.screen_manager:
                        if app.screen_manager.has_screen('home'):
                            home = app.screen_manager.get_screen('home')
                            if hasattr(home, 'show_subscription_status'):
                                home.show_subscription_status(status_data)
                        if app.screen_manager.has_screen('profile'):
                            profile = app.screen_manager.get_screen('profile')
                            if hasattr(profile, 'refresh_subscription'):
                                profile.refresh_subscription()
                except Exception as e:
                    logger.debug(f"Ошибка обновления UI после покупки: {e}")

                # Возвращаемся на home через секунду
                Clock.schedule_once(self._go_home, 0.5)

            api.check_subscription(
                on_success=_on_status,
                on_failure=lambda req, err: Clock.schedule_once(self._go_home, 0.3),
            )

        api.get_current_user(
            on_success=_on_user,
            on_failure=lambda req, err: Clock.schedule_once(self._go_home, 0.3),
        )

    # ============ НАВИГАЦИЯ ============

    def _go_to_promo(self, *args):
        if self.manager and self.manager.has_screen('promo'):
            self.manager.current = 'promo'

    def _go_home(self, dt=None):
        if self.manager and self.manager.has_screen('home'):
            self.manager.current = 'home'

    # ============ ЖИЗНЕННЫЙ ЦИКЛ ============

    def on_enter(self):
        super().on_enter()
        self.load_plans()

    def on_leave(self):
        super().on_leave()