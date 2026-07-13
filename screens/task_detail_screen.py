# screens/task_detail_screen.py
"""
Экран детального просмотра и редактирования задачи
Работа с сервером - с красивыми карточками комментариев
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from io import BytesIO
from datetime import datetime
import re

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.behaviors import CircularRippleBehavior
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('TaskDetail')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class CommentCard(MDCard):
    """Красивая карточка комментария"""

    def __init__(self, comment_text, comment_date=None, **kwargs):
        super().__init__(**kwargs)
        self.comment_text = comment_text
        self.comment_date = comment_date

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(60)
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.spacing = dp(4)
        self.radius = [dp(10)] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.06]
        self.line_width = 0.5
        self.clip = True

        self._build_ui()

    def _build_ui(self):
        self.text_label = MDLabel(
            text=self.comment_text,
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            size_hint_y=None,
            adaptive_height=True,
            valign="top",
            line_height=1.4,
            padding=[0, 0, 0, 0]
        )

        date_str = self._format_date(self.comment_date) if self.comment_date else ""

        self.date_label = MDLabel(
            text=date_str,
            font_size=sp(10),
            halign="right",
            valign="bottom",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3],
            size_hint_y=None,
            height=dp(18)
        )

        self.add_widget(self.text_label)
        self.add_widget(self.date_label)

        Clock.schedule_once(lambda dt: self._adjust_height(), 0.05)

    def _adjust_height(self):
        if self.text_label.texture:
            text_height = self.text_label.texture_size[1]
            self.height = text_height + dp(30) + dp(18)
            self.text_label.height = text_height + dp(4)

    def _format_date(self, date_str):
        if not date_str:
            return ""
        try:
            if 'Z' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            elif '.' in date_str:
                parts = date_str.split('.')
                if len(parts) >= 3:
                    dt = datetime.strptime(date_str, '%d.%m.%Y %H:%M')
                else:
                    dt = datetime.strptime(date_str, '%d.%m.%Y')
            else:
                dt = datetime.fromisoformat(date_str)

            now = datetime.now()
            if dt.year == now.year:
                return dt.strftime('%d.%m %H:%M')
            else:
                return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return date_str[:16] if len(date_str) > 16 else date_str


class TaskDetailScreen(BaseScreen):
    """Экран детального просмотра и редактирования задачи"""

    STATUS_OPTIONS = [
        {'id': 'done', 'label': 'Выполнено', 'color': '#4CAF50'},
        {'id': 'not_done', 'label': 'Не выполнено', 'color': '#F44336'},
        {'id': 'in_progress', 'label': 'В работе', 'color': '#FFC107'},
        {'id': 'new', 'label': 'Новая', 'color': '#2196F3'},
        {'id': 'cancelled', 'label': 'Отменена', 'color': '#9E9E9E'},
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'task_detail'
        self.bg_image = None
        self.task_data = None
        self.task_id = None
        self.on_update_callback = None
        self._status_dialog = None
        self._comment_dialog = None
        self._delete_dialog = None
        self._is_saving = False
        self._comment_cards = []
        self._status_display = None

        self.init_ui()
        self.load_background()

        logger.info('Экран детального просмотра задачи создан')

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

    def init_ui(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(6),
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), dp(8)]
        )

        # ============ ВЕРХНЯЯ ПАНЕЛЬ ============
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8)
        )

        self.title_label = MDLabel(
            text="Задача",
            font_size=sp(18),
            halign="left",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right"
        )

        self.refresh_btn = MDIconButton(
            icon="refresh",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.5],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5},
            on_release=self._refresh_task
        )

        self.delete_btn = MDIconButton(
            icon="delete",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_icon_color="Custom",
            icon_color=[0.8, 0.3, 0.3, 0.8],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5},
            on_release=self._confirm_delete
        )

        header.add_widget(self.title_label)
        header.add_widget(self.refresh_btn)
        header.add_widget(self.delete_btn)
        content.add_widget(header)

        # ============ РАЗДЕЛИТЕЛЬ ============
        divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(1),
            md_bg_color=[1, 1, 1, 0.08]
        )
        content.add_widget(divider)

        # ============ СКРОЛЛ (без полосы прокрутки) ============
        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        self.data_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            adaptive_height=True,
            spacing=dp(6),
            padding=[dp(4), dp(8), dp(4), dp(8)]
        )

        self.scroll.add_widget(self.data_container)
        content.add_widget(self.scroll)

        self.build_ui(content_widget=content, use_scroll=False)

    def set_task(self, task_data, on_update_callback):
        """Устанавливает задачу для отображения"""
        self.task_data = task_data
        self.task_id = task_data.get('id')
        self.on_update_callback = on_update_callback
        self._comment_cards = []
        self._render_task()

    def _refresh_task(self, instance):
        if not self.task_id:
            return

        self._show_loading()
        api.get_task(
            task_id=self.task_id,
            on_success=self._on_task_refreshed,
            on_failure=self._on_task_refresh_error,
            force_refresh=True
        )

    def _on_task_refreshed(self, task_data):
        self._hide_loading()
        self.task_data = task_data
        self._render_task()
        notify.success("Задача обновлена")

    def _on_task_refresh_error(self, req, error):
        self._hide_loading()
        notify.error("Ошибка обновления задачи")
        logger.error(f"❌ Ошибка обновления задачи: {error}")

    def _render_task(self):
        self.data_container.clear_widgets()
        self._comment_cards.clear()

        if not self.task_data:
            return

        task = self.task_data
        self.title_label.text = task.get('title', 'Задача')

        # ============ 1. СТАТУС ============
        status_row = self._create_status_row(task)
        self.data_container.add_widget(status_row)

        # ============ 2. ДАТА СОЗДАНИЯ ============
        created_at = task.get('created_at', '')
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = dt.strftime('%d.%m.%Y %H:%M')
            except:
                created_str = created_at
        else:
            created_str = '—'

        created_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(28)
        )
        created_row.add_widget(MDLabel(
            text=f"Создана: {created_str}",
            font_size=sp(12),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle"
        ))
        self.data_container.add_widget(created_row)

        # ============ 3. ВЕРСИЯ И ВРЕМЯ ВЫПОЛНЕНИЯ ============
        info_row = self._create_info_row(task)
        self.data_container.add_widget(info_row)

        # ============ 4. РАЗДЕЛИТЕЛЬ ============
        self.data_container.add_widget(self._create_divider())

        # ============ 5. ОПИСАНИЕ ============
        desc = task.get('description', '')
        if desc:
            desc_label = MDLabel(
                text=desc,
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.85],
                size_hint_y=None,
                adaptive_height=True,
                line_height=1.5,
                padding=[dp(0), dp(4), dp(0), dp(4)]
            )
            self.data_container.add_widget(desc_label)

        # ============ 6. РАЗДЕЛИТЕЛЬ ============
        self.data_container.add_widget(self._create_divider())

        # ============ 7. СЕКЦИЯ КОММЕНТАРИЕВ ============
        comments_label = MDLabel(
            text="Комментарии",
            font_size=sp(15),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.data_container.add_widget(comments_label)

        comments = self._parse_comments(task.get('comment', ''))

        if comments:
            for comment_data in comments:
                card = CommentCard(
                    comment_text=comment_data['text'],
                    comment_date=comment_data['date']
                )
                self.data_container.add_widget(card)
                self._comment_cards.append(card)
        else:
            empty_comments = MDLabel(
                text="Нет комментариев",
                font_size=sp(12),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.3],
                size_hint_y=None,
                height=dp(30),
                halign="center"
            )
            self.data_container.add_widget(empty_comments)
            self._comment_cards.append(empty_comments)

        # ============ 8. КНОПКА ДОБАВИТЬ КОММЕНТАРИЙ ============
        add_comment_btn = MDRaisedButton(
            text="+ Добавить комментарий",
            size_hint=(1, None),
            height=dp(44),
            md_bg_color=[0.46, 0.70, 0.71, 0.15],
            text_color=[0.46, 0.70, 0.71, 1],
            font_size=sp(14),
            on_release=self._show_add_comment_dialog
        )
        self.data_container.add_widget(add_comment_btn)

        self.data_container.add_widget(Widget(size_hint_y=None, height=dp(20)))

    def _parse_comments(self, comment_text):
        if not comment_text:
            return []

        comments = []
        parts = comment_text.split('---')

        for part in parts:
            part = part.strip()
            if not part:
                continue

            date_match = re.match(r'^(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}):\s*(.*)$', part, re.DOTALL)
            if date_match:
                date_str = date_match.group(1)
                text = date_match.group(2).strip()
                comments.append({'date': date_str, 'text': text})
            else:
                comments.append({'date': '', 'text': part})

        return comments

    def _create_status_row(self, task):
        status_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(8)
        )

        status_label = MDLabel(
            text="Статус:",
            font_size=sp(14),
            size_hint_x=None,
            width=dp(70),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            valign="middle"
        )

        status = task.get('status', 'new')
        status_info = self._get_status_info(status)

        self._status_display = MDCard(
            orientation='horizontal',
            size_hint_x=1,
            height=dp(36),
            padding=[dp(12), dp(4), dp(12), dp(4)],
            radius=[dp(8)] * 4,
            md_bg_color=self._hex_to_rgba(status_info['color'], 0.15),
            elevation=0,
            on_release=self._show_status_selector
        )

        status_dot = MDCard(
            size_hint=(None, None),
            size=(dp(10), dp(10)),
            radius=[dp(5)] * 4,
            md_bg_color=self._hex_to_rgba(status_info['color']),
            elevation=0,
            pos_hint={'center_y': 0.5}
        )

        status_text = MDLabel(
            text=status_info['label'],
            font_size=sp(14),
            halign="left",
            theme_text_color="Custom",
            text_color=self._hex_to_rgba(status_info['color']),
            bold=True,
            size_hint_x=1,
            valign="middle",
            padding=[dp(8), 0, 0, 0]
        )

        self._status_display.add_widget(status_dot)
        self._status_display.add_widget(status_text)

        status_row.add_widget(status_label)
        status_row.add_widget(self._status_display)

        return status_row

    def _create_info_row(self, task):
        info_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(32),
            spacing=dp(8)
        )

        version = task.get('version', '—')
        version_label = MDLabel(
            text=f"Версия: {version}",
            font_size=sp(12),
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle"
        )

        completed_at = task.get('completed_at', '')
        if completed_at:
            try:
                dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                completed_str = dt.strftime('%d.%m.%Y %H:%M')
            except:
                completed_str = completed_at
        else:
            completed_str = '—'

        completed_label = MDLabel(
            text=f"Выполнена: {completed_str}",
            font_size=sp(12),
            size_hint_x=0.5,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            valign="middle",
            halign="right"
        )

        info_row.add_widget(version_label)
        info_row.add_widget(completed_label)

        return info_row

    def _create_divider(self):
        return MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(1),
            md_bg_color=[1, 1, 1, 0.06]
        )

    def _get_status_info(self, status_id):
        for s in self.STATUS_OPTIONS:
            if s['id'] == status_id:
                return s
        return self.STATUS_OPTIONS[3]

    def _hex_to_rgba(self, hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [alpha]

    def _show_loading(self):
        self.data_container.clear_widgets()
        loading_label = MDLabel(
            text="Загрузка...",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            size_hint_y=None,
            height=dp(60)
        )
        self.data_container.add_widget(loading_label)

    def _hide_loading(self):
        pass

    # ============ ВЫБОР СТАТУСА ============

    def _show_status_selector(self, instance):
        if self._status_dialog:
            self._status_dialog.dismiss()

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(12),
            size_hint_y=None,
            adaptive_height=True,
            md_bg_color=[1, 1, 1, 1]
        )

        current_status = self.task_data.get('status', 'new')

        for status in self.STATUS_OPTIONS:
            is_active = status['id'] == current_status

            btn = MDRaisedButton(
                text=status['label'],
                size_hint=(1, None),
                height=dp(44),
                md_bg_color=self._hex_to_rgba(status['color'], 0.2) if is_active else [0.92, 0.92, 0.92, 1],
                text_color=self._hex_to_rgba(status['color']) if is_active else [0.2, 0.2, 0.2, 1],
                font_size=sp(15),
                elevation=0 if not is_active else 2,
                on_release=lambda x, s=status['id']: self._select_status(s)
            )

            if is_active:
                btn.text = f"✓ {status['label']}"

            content.add_widget(btn)

        self._status_dialog = MDDialog(
            title="Выберите статус",
            type="custom",
            content_cls=content,
            radius=[theme.CORNER_RADIUS] * 4,
            background_color=[1, 1, 1, 1]
        )
        self._status_dialog.open()

    def _select_status(self, status_id):
        if self._is_saving:
            return

        if status_id == self.task_data.get('status'):
            if self._status_dialog:
                self._status_dialog.dismiss()
                self._status_dialog = None
            return

        if self._status_dialog:
            self._status_dialog.dismiss()
            self._status_dialog = None

        self._is_saving = True

        if self._status_display:
            self._status_display.opacity = 0.5

        completed_at = None
        if status_id == 'done':
            completed_at = datetime.now().isoformat()
            logger.info(f"📝 Установка статуса 'done' с completed_at={completed_at}")

        api.change_task_status(
            task_id=self.task_id,
            status=status_id,
            completed_at=completed_at,
            on_success=self._on_status_changed,
            on_failure=self._on_status_change_error
        )

    def _on_status_changed(self, result):
        self._is_saving = False

        if self._status_display:
            self._status_display.opacity = 1

        logger.info(f"📥 Результат изменения статуса: {result}")

        task = result.get('task')
        if task:
            self.task_data = task
            logger.info(f"📊 Новый статус: {task.get('status')}, completed_at: {task.get('completed_at')}")
            self._render_task()

            if self.on_update_callback:
                self.on_update_callback(task)

            notify.success("Статус обновлён")
        else:
            logger.warning("⚠️ Задача не пришла в ответе, запрашиваем заново")
            self._refresh_task(None)

    def _on_status_change_error(self, req, error):
        self._is_saving = False

        if self._status_display:
            self._status_display.opacity = 1

        notify.error("Ошибка обновления статуса")
        logger.error(f"❌ Ошибка изменения статуса: {error}")

    # ============ ДОБАВЛЕНИЕ КОММЕНТАРИЯ ============

    def _show_add_comment_dialog(self, instance):
        """Показывает диалог добавления комментария"""
        if self._comment_dialog:
            self._comment_dialog.dismiss()

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(12),
            size_hint_y=None,
            adaptive_height=True,
            md_bg_color=[1, 1, 1, 1]
        )

        comment_field = MDTextField(
            hint_text="Введите комментарий...",
            mode="fill",
            size_hint_y=None,
            height=dp(80),
            font_size=sp(14),
            multiline=True
        )
        content.add_widget(comment_field)

        buttons = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            spacing=dp(8)
        )

        cancel_btn = MDRaisedButton(
            text="Отмена",
            size_hint=(0.5, 1),
            md_bg_color=[0.9, 0.9, 0.9, 1],
            text_color=[0.2, 0.2, 0.2, 1],
            on_release=lambda x: self._comment_dialog.dismiss()
        )

        add_btn = MDRaisedButton(
            text="Добавить",
            size_hint=(0.5, 1),
            md_bg_color=[0.46, 0.70, 0.71, 1],
            text_color=[1, 1, 1, 1],
            on_release=lambda x: self._add_comment(comment_field.text)
        )

        buttons.add_widget(cancel_btn)
        buttons.add_widget(add_btn)
        content.add_widget(buttons)

        self._comment_dialog = MDDialog(
            title="Новый комментарий",
            type="custom",
            content_cls=content,
            radius=[theme.CORNER_RADIUS] * 4,
            background_color=[1, 1, 1, 1]
        )
        self._comment_dialog.open()

    def _add_comment(self, text):
        if self._comment_dialog:
            self._comment_dialog.dismiss()
            self._comment_dialog = None

        text = text.strip()
        if not text:
            notify.warning("Введите текст комментария")
            return

        if self._is_saving:
            return

        self._is_saving = True

        api.add_task_comment(
            task_id=self.task_id,
            comment=text,
            on_success=self._on_comment_added,
            on_failure=self._on_comment_error
        )

    def _on_comment_added(self, result):
        """Обработчик успешного добавления комментария - с полным перерендером"""
        self._is_saving = False
        task = result.get('task')
        if task:
            self.task_data = task
            # ПОЛНЫЙ ПЕРЕРЕНДЕР ЭКРАНА
            self._render_task()
            if self.on_update_callback:
                self.on_update_callback(task)
            notify.success("Комментарий добавлен")

    def _on_comment_error(self, req, error):
        self._is_saving = False
        notify.error("Ошибка добавления комментария")
        logger.error(f"❌ Ошибка добавления комментария: {error}")

    # ============ УДАЛЕНИЕ (hard=True) ============

    def _confirm_delete(self, instance):
        """Подтверждение удаления"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(16),
            size_hint_y=None,
            adaptive_height=True,
            md_bg_color=[1, 1, 1, 1]
        )

        icon_label = MDLabel(
            text="⚠️",
            font_size=sp(48),
            halign="center",
            theme_text_color="Custom",
            text_color=[0.8, 0.2, 0.2, 1],
            size_hint_y=None,
            height=dp(56)
        )
        content.add_widget(icon_label)

        label = MDLabel(
            text="Вы уверены, что хотите удалить эту задачу?",
            halign="center",
            theme_text_color="Custom",
            text_color=[0.1, 0.1, 0.1, 0.9],
            size_hint_y=None,
            height=dp(40),
            font_size=sp(15)
        )
        content.add_widget(label)

        label_sub = MDLabel(
            text="Задача будет удалена безвозвратно",
            halign="center",
            theme_text_color="Custom",
            text_color=[0.5, 0.5, 0.5, 0.7],
            size_hint_y=None,
            height=dp(24),
            font_size=sp(12)
        )
        content.add_widget(label_sub)

        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        buttons = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            spacing=dp(8)
        )

        cancel_btn = MDRaisedButton(
            text="Отмена",
            size_hint=(0.5, 1),
            md_bg_color=[0.9, 0.9, 0.9, 1],
            text_color=[0.2, 0.2, 0.2, 1],
            on_release=lambda x: self._delete_dialog.dismiss()
        )

        delete_btn = MDRaisedButton(
            text="Удалить",
            size_hint=(0.5, 1),
            md_bg_color=[0.8, 0.2, 0.2, 1],
            text_color=[1, 1, 1, 1],
            on_release=self._delete_task
        )

        buttons.add_widget(cancel_btn)
        buttons.add_widget(delete_btn)
        content.add_widget(buttons)

        self._delete_dialog = MDDialog(
            title="Удаление задачи",
            type="custom",
            content_cls=content,
            radius=[theme.CORNER_RADIUS] * 4,
            background_color=[1, 1, 1, 1]
        )
        self._delete_dialog.open()

    def _delete_task(self, instance):
        """Удаляет задачу на сервере (hard=True - полное удаление)"""
        if self._delete_dialog:
            self._delete_dialog.dismiss()
            self._delete_dialog = None

        if self._is_saving:
            return

        self._is_saving = True

        # hard=True - ПОЛНОЕ УДАЛЕНИЕ ИЗ БД
        api.delete_task(
            task_id=self.task_id,
            hard=True,
            on_success=self._on_task_deleted,
            on_failure=self._on_delete_error
        )

    def _on_task_deleted(self, result):
        """Обработчик успешного удаления"""
        self._is_saving = False
        notify.success("Задача удалена")
        if self.on_update_callback:
            self.on_update_callback(None)
        self.go_back()

    def _on_delete_error(self, req, error):
        """Ошибка удаления"""
        self._is_saving = False
        notify.error("Ошибка удаления задачи")
        logger.error(f"❌ Ошибка удаления задачи: {error}")

    def go_back(self, instance=None):
        """Возврат в список задач"""
        logger.info("🔙 Возврат в список задач")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.clear_custom_title_widget()
            app.top_nav.update_title('tasks')
            app.top_nav._update_left_button('tasks')

        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'tasks'

    def on_enter(self):
        """При входе на экран"""
        logger.info("🚪 Вход в детальный просмотр задачи")

        title = self.task_data.get('title', 'Задача') if self.task_data else "Задача"

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title(title)
            app.top_nav._update_left_button('task_detail')
            app.top_nav.back_btn.on_release = self.go_back