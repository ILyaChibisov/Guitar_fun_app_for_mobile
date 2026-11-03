# screens/admin_promo_screen.py
"""
Экран управления промокодами (только админ).

- Список промокодов с бейджами статуса (активен / истёк / исчерпан).
- Создание нового промокода (FAB).
- Удаление промокода (долгое нажатие / кнопка).
"""
import threading
from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.animation import Animation
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from io import BytesIO

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import (
    MDRaisedButton, MDFlatButton, MDIconButton,
)
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.behaviors import CircularRippleBehavior

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify
from state.settings_state import settings_state

logger = screen_logger('AdminPromo')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


# ============================================================
# ЦВЕТА ДЛЯ СТАТУСОВ (одинаковые для всех тем — это семантика)
# ============================================================

STATUS_ACTIVE = [0.20, 0.65, 0.32, 1.0]     # зелёный
STATUS_EXPIRED = [0.55, 0.55, 0.55, 1.0]    # серый
STATUS_EXHAUSTED = [0.85, 0.45, 0.10, 1.0]  # оранжевый


def _get_card_bg():
    """Фон карточки под текущую тему."""
    t = settings_state.theme
    if t == 'light':
        return [1, 1, 1, 0.96]
    if t == 'dark':
        return [0.14, 0.14, 0.14, 0.96]
    return [0.10, 0.10, 0.10, 0.92]


def _get_text_primary():
    t = settings_state.theme
    if t == 'light':
        return [0.15, 0.15, 0.15, 1]
    return [1, 1, 1, 0.95]


def _get_text_secondary():
    t = settings_state.theme
    if t == 'light':
        return [0.45, 0.45, 0.45, 1]
    return [1, 1, 1, 0.55]


# ============================================================
# КАРТОЧКА ПРОМОКОДА
# ============================================================

class PromoCard(CircularRippleBehavior, MDCard):
    """Карточка одного промокода."""

    def __init__(self, promo: dict, on_delete=None, **kwargs):
        super().__init__(**kwargs)
        self.promo = promo
        self.on_delete_callback = on_delete

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(108)
        self.radius = [dp(14)] * 4
        self.elevation = 2
        self.ripple_scale = 0.97
        self.padding = [dp(14), dp(10), dp(14), dp(10)]
        self.spacing = dp(4)
        self.md_bg_color = _get_card_bg()
        self.line_color = [1, 1, 1, 0.08]
        self.line_width = 0.6

        # Определяем статус
        status_label, status_color = self._compute_status()

        # ---------- ВЕРХНЯЯ СТРОКА: код + бейдж статуса ----------
        top_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
        )

        code_label = MDLabel(
            text=promo.get('code', '—'),
            font_size=sp(17),
            bold=True,
            theme_text_color="Custom",
            text_color=_get_text_primary(),
            size_hint_x=None,
            width=dp(150),
            shorten=True,
            shorten_from="right",
        )

        badge = MDCard(
            size_hint=(None, None),
            size=(dp(90), dp(24)),
            radius=[dp(8)] * 4,
            elevation=0,
            md_bg_color=status_color[:3] + [0.22],
            line_color=status_color[:3] + [0.55],
            line_width=1,
            padding=0,
        )
        badge_label = MDLabel(
            text=status_label,
            font_size=sp(10),
            bold=True,
            halign='center',
            valign='middle',
            theme_text_color="Custom",
            text_color=status_color,
        )
        badge.add_widget(badge_label)

        top_row.add_widget(code_label)
        top_row.add_widget(Widget())  # распорка
        top_row.add_widget(badge)

        # ---------- СРЕДНЯЯ СТРОКА: дни + активации ----------
        info_row = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(24),
            spacing=dp(12),
            md_bg_color=[0, 0, 0, 0],
        )

        days_label = MDLabel(
            text=f"+{promo.get('days_to_add', 0)} дн.",
            font_size=sp(12),
            bold=True,
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            size_hint_x=None,
            width=dp(80),
        )

        used = promo.get('used_count', 0)
        maxu = promo.get('max_uses', 0)
        uses_label = MDLabel(
            text=f"Активаций: {used}/{maxu}",
            font_size=sp(11),
            theme_text_color="Custom",
            text_color=_get_text_secondary(),
            size_hint_x=1,
        )

        info_row.add_widget(days_label)
        info_row.add_widget(uses_label)

        # ---------- НИЖНЯЯ СТРОКА: дата окончания ----------
        valid_until = promo.get('valid_until')
        until_text = "—"
        if valid_until:
            try:
                dt = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
                until_text = dt.strftime('до %d.%m.%Y %H:%M')
            except Exception:
                until_text = str(valid_until)

        date_label = MDLabel(
            text=until_text,
            font_size=sp(10),
            theme_text_color="Custom",
            text_color=_get_text_secondary(),
            size_hint_y=None,
            height=dp(18),
        )

        self.add_widget(top_row)
        self.add_widget(info_row)
        self.add_widget(date_label)

        # ---------- ДОЛГОЕ НАЖАТИЕ = УДАЛЕНИЕ ----------
        self._long_press_event = None
        self.bind(on_touch_down=self._on_touch_down,
                  on_touch_up=self._on_touch_up)

    # -------- Статус --------

    def _compute_status(self):
        """Возвращает (label, color)."""
        promo = self.promo
        expired = promo.get('expired', False)
        exhausted = promo.get('exhausted', False)
        # сервер возвращает флаги, но если нет — посчитаем локально
        if 'expired' not in promo:
            vu = promo.get('valid_until')
            if vu:
                try:
                    dt = datetime.fromisoformat(vu.replace('Z', '+00:00'))
                    expired = dt < datetime.utcnow()
                except Exception:
                    pass
        if 'exhausted' not in promo:
            exhausted = promo.get('used_count', 0) >= promo.get('max_uses', 0)

        if exhausted:
            return ("Исчерпан", STATUS_EXHAUSTED)
        if expired:
            return ("Истёк", STATUS_EXPIRED)
        return ("Активен", STATUS_ACTIVE)

    # -------- Долгое нажатие --------

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self._long_press_event:
                self._long_press_event.cancel()
            self._long_press_event = Clock.schedule_once(
                lambda dt: self._trigger_delete(), 0.6
            )
        return super().on_touch_down(touch)

    def _on_touch_up(self, instance, touch):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
        return super().on_touch_up(touch)

    def _trigger_delete(self):
        self._long_press_event = None
        if self.on_delete_callback:
            Animation(opacity=0.6, duration=0.1).start(self)
            Clock.schedule_once(
                lambda dt: Animation(opacity=1, duration=0.15).start(self), 0.1
            )
            self.on_delete_callback(self.promo)


# ============================================================
# ЭКРАН
# ============================================================

class AdminPromoScreen(BaseScreen):
    """Список промокодов + создание/удаление."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'admin_promo'
        self._promos = []
        self._loading = False
        self._create_dialog = None
        self.bg_image = None

        self.init_ui()
        self.load_background()

        logger.info('AdminPromoScreen создан')

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
        # Контейнер с заголовком + список
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[0, 0, 0, dp(80)],  # место под FAB
        )

        # ---- Верхняя панель: счётчик + обновить ----
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(8),
            md_bg_color=[0, 0, 0, 0],
        )

        self.count_label = MDLabel(
            text="Загрузка…",
            font_size=sp(12),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            valign='middle',
            size_hint_x=1,
        )

        refresh_btn = MDIconButton(
            icon='refresh',
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=lambda *_: self.load_promocodes(),
        )

        header.add_widget(self.count_label)
        header.add_widget(refresh_btn)
        content.add_widget(header)

        # ---- Список карточек ----
        self.list_box = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            adaptive_height=True,
            md_bg_color=[0, 0, 0, 0],
        )

        content.add_widget(self.list_box)

        self.build_ui(content_widget=content, use_scroll=True)

        # ---- FAB «Создать» ----
        self.fab = MDRaisedButton(
            text="+ Создать",
            size_hint=(None, None),
            size=(dp(140), dp(48)),
            pos_hint={'right': 0.96, 'y': 0.12},
            md_bg_color=theme.PRIMARY,
            text_color=[1, 1, 1, 1],
            font_size=sp(14),
            on_release=self._open_create_dialog,
        )
        self.add_widget(self.fab)

    # ============ ЗАГРУЗКА ============

    def load_promocodes(self):
        if self._loading:
            return
        self._loading = True
        self.count_label.text = "Загрузка…"
        self._render_placeholder("Загрузка…")

        def worker():
            result = api.list_promocodes_sync(limit=200, offset=0)
            Clock.schedule_once(lambda dt: self._on_loaded(result), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _on_loaded(self, result: dict):
        self._loading = False

        if not isinstance(result, dict):
            self.count_label.text = "Ошибка загрузки"
            self._render_placeholder("Не удалось загрузить промокоды")
            return

        items = result.get('promocodes', []) or []
        total = result.get('total', len(items))

        self._promos = items
        self.count_label.text = f"Всего: {total}"
        self._render_list()

    def _render_placeholder(self, text: str):
        self.list_box.clear_widgets()
        lbl = MDLabel(
            text=text,
            halign='center',
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.55],
            size_hint_y=None,
            height=dp(60),
        )
        self.list_box.add_widget(lbl)

    def _render_list(self):
        self.list_box.clear_widgets()

        if not self._promos:
            self._render_placeholder("Промокодов пока нет")
            return

        for promo in self._promos:
            card = PromoCard(
                promo=promo,
                on_delete=self._confirm_delete,
            )
            self.list_box.add_widget(card)

    # ============ СОЗДАНИЕ ============

    def _open_create_dialog(self, *args):
        if self._create_dialog:
            return

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(280),
            padding=[dp(8), dp(8), dp(8), dp(8)],
        )

        code_field = MDTextField(
            hint_text="Код (A-Z, 0-9, _, -)",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
        )
        days_field = MDTextField(
            hint_text="Сколько дней начислить (1–3650)",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
            input_filter="int",
        )
        max_uses_field = MDTextField(
            hint_text="Лимит активаций (1–100000)",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
            input_filter="int",
        )
        valid_days_field = MDTextField(
            hint_text="Срок действия кода, дней (1–3650)",
            mode="fill",
            size_hint_y=None,
            height=dp(52),
            input_filter="int",
        )

        content.add_widget(code_field)
        content.add_widget(days_field)
        content.add_widget(max_uses_field)
        content.add_widget(valid_days_field)

        def _do_create(btn):
            code = (code_field.text or "").strip().upper()
            try:
                days = int(days_field.text or 0)
                maxu = int(max_uses_field.text or 0)
                vdays = int(valid_days_field.text or 0)
            except ValueError:
                notify.warning("Введите числа во все поля")
                return

            # Клиентская валидация (сервер всё равно проверит)
            import re
            if not re.fullmatch(r"[A-Z0-9_\-]{3,50}", code):
                notify.warning("Код: 3–50 символов, A-Z, 0-9, _, -")
                return
            if not (1 <= days <= 3650):
                notify.warning("Дни: от 1 до 3650")
                return
            if not (1 <= maxu <= 100000):
                notify.warning("Лимит: от 1 до 100000")
                return
            if not (1 <= vdays <= 3650):
                notify.warning("Срок: от 1 до 3650")
                return

            create_btn.disabled = True
            create_btn.text = "Создание…"

            def _on_success(res):
                create_btn.disabled = False
                create_btn.text = "Создать"
                if self._create_dialog:
                    self._create_dialog.dismiss()
                    self._create_dialog = None
                notify.success(res.get("message", "Промокод создан"))
                self.load_promocodes()

            def _on_failure(req, err):
                create_btn.disabled = False
                create_btn.text = "Создать"
                notify.error(str(err))

            api.create_promo(
                code=code, days_to_add=days,
                max_uses=maxu, valid_days=vdays,
                on_success=_on_success, on_failure=_on_failure,
            )

        create_btn = MDRaisedButton(
            text="Создать",
            md_bg_color=theme.PRIMARY,
            on_release=_do_create,
        )

        self._create_dialog = MDDialog(
            title="Новый промокод",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Отмена",
                    on_release=lambda x: self._close_create_dialog(),
                ),
                create_btn,
            ],
        )
        self._create_dialog.bind(on_dismiss=lambda *_: setattr(self, '_create_dialog', None))
        self._create_dialog.open()

    def _close_create_dialog(self):
        if self._create_dialog:
            self._create_dialog.dismiss()
            self._create_dialog = None

    # ============ УДАЛЕНИЕ ============

    def _confirm_delete(self, promo: dict):
        code = promo.get('code', '—')
        pid = promo.get('id')

        def _do_delete(btn):
            dlg.dismiss()

            def _on_success(res):
                notify.success(f"Промокод {code} удалён")
                self.load_promocodes()

            def _on_failure(req, err):
                notify.error(str(err))

            api.delete_promo(pid, on_success=_on_success, on_failure=_on_failure)

        dlg = MDDialog(
            title="Удалить промокод?",
            text=f"Код: {code}\nЭто действие нельзя отменить.",
            buttons=[
                MDFlatButton(text="Отмена", on_release=lambda x: dlg.dismiss()),
                MDRaisedButton(
                    text="Удалить",
                    md_bg_color=[0.8, 0.2, 0.2, 1],
                    on_release=_do_delete,
                ),
            ],
        )
        dlg.open()

    # ============ ЖИЗНЕННЫЙ ЦИКЛ ============

    def on_enter(self):
        super().on_enter()
        # Проверим, что мы всё ещё админ
        if not api.is_admin():
            notify.error("Доступ только для администратора")
            if self.manager and self.manager.has_screen('home'):
                self.manager.current = 'home'
            return
        self.load_promocodes()

    def on_leave(self):
        # Чистим диалоги, чтобы не висели при выходе
        self._close_create_dialog()
        super().on_leave()