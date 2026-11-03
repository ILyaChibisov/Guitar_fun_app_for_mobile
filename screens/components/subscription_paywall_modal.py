# screens/components/subscription_paywall_modal.py
"""
Глобальная модалка «Подписка закончилась».
Показывается поверх любого экрана, когда лимит исчерпан.
Кнопки: «Оформить подписку», «У меня есть промокод», «Выйти из аккаунта».
"""
from kivy.metrics import dp, sp
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('PaywallModal')


class SubscriptionPaywallModal(ModalView):
    """
    Блокирующая модалка, когда подписка закончилась.
    - «Оформить подписку» → paywall.
    - «У меня есть промокод» → promo.
    - «Выйти из аккаунта» → logout + auth modal.
    """

    def __init__(self, can_dismiss=False, on_paywall=None, on_promo=None,
                 on_logout=None, on_dismiss=None, **kwargs):
        super().__init__(
            size_hint=(1, 1),
            auto_dismiss=can_dismiss,
            background_color=(0, 0, 0, 0.6),
            **kwargs,
        )
        self._on_paywall = on_paywall
        self._on_promo = on_promo
        self._on_logout = on_logout
        self._on_dismiss_cb = on_dismiss

        root = FloatLayout()

        card = MDCard(
            orientation='vertical',
            size_hint=(0.9, None),
            height=dp(400),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            padding=[dp(24), dp(24), dp(24), dp(24)],
            spacing=dp(12),
            radius=[dp(20)] * 4,
            elevation=12,
            md_bg_color=[0.12, 0.12, 0.12, 0.98],
            line_color=[0.46, 0.70, 0.71, 0.5],
            line_width=1.5,
        )

        title = MDLabel(
            text="Подписка закончилась",
            font_size=sp(22),
            bold=True,
            halign='center',
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
        )
        card.add_widget(title)

        text = MDLabel(
            text=(
                "Бесплатный период закончился.\n"
                "Оформите подписку или активируйте промокод, "
                "чтобы продолжить пользоваться приложением."
            ),
            font_size=sp(13),
            halign='center',
            size_hint_y=None,
            height=dp(80),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8],
        )
        card.add_widget(text)

        # Кнопка «Оформить подписку»
        pay_btn = MDRaisedButton(
            text="Оформить подписку",
            size_hint=(1, None),
            height=dp(48),
            md_bg_color=theme.PRIMARY,
            text_color=[1, 1, 1, 1],
            font_size=sp(15),
            on_release=lambda *_: self._go_paywall(),
        )
        card.add_widget(pay_btn)

        # Кнопка «У меня есть промокод»
        promo_btn = MDFlatButton(
            text="У меня есть промокод",
            size_hint=(1, None),
            height=dp(40),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            font_size=sp(13),
            on_release=lambda *_: self._go_promo(),
        )
        card.add_widget(promo_btn)

        # Разделитель
        separator = MDLabel(
            text="— или —",
            halign='center',
            font_size=sp(11),
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3],
        )
        card.add_widget(separator)

        # Кнопка «Выйти из аккаунта»
        logout_btn = MDFlatButton(
            text="Выйти из аккаунта",
            size_hint=(1, None),
            height=dp(40),
            theme_text_color="Custom",
            text_color=[0.9, 0.5, 0.5, 1],
            font_size=sp(13),
            on_release=lambda *_: self._do_logout(),
        )
        card.add_widget(logout_btn)

        # Кнопка «Позже» — только в мягком режиме
        if can_dismiss:
            later_btn = MDFlatButton(
                text="Позже",
                size_hint=(1, None),
                height=dp(32),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.4],
                font_size=sp(11),
                on_release=lambda *_: self.dismiss(),
            )
            card.add_widget(later_btn)

        root.add_widget(card)
        self.add_widget(root)

    def _go_paywall(self):
        self.dismiss()
        if self._on_paywall:
            self._on_paywall()

    def _go_promo(self):
        self.dismiss()
        if self._on_promo:
            self._on_promo()

    def _do_logout(self):
        self.dismiss()
        if self._on_logout:
            self._on_logout()

    def on_dismiss(self):
        if self._on_dismiss_cb:
            try:
                self._on_dismiss_cb()
            except Exception as e:
                logger.error(f"on_dismiss callback: {e}")