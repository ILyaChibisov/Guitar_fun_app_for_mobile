# screens/tasks_screen.py
"""
Экран управления задачами для администратора
Работа с сервером + кэширование
"""
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from io import BytesIO
from datetime import datetime
import json
import os
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

logger = screen_logger('Tasks')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class FilterIconButton(MDIconButton):
    """Простая иконка-фильтр статуса"""

    STATUS_ICONS = {
        'all': 'format-list-bulleted',
        'done': 'check-circle',
        'not_done': 'close-circle',
        'in_progress': 'progress-clock',
        'new': 'plus-circle',
        'cancelled': 'cancel',
    }

    STATUS_COLORS = {
        'all': '#757575',
        'done': '#4CAF50',
        'not_done': '#F44336',
        'in_progress': '#FFC107',
        'new': '#2196F3',
        'cancelled': '#9E9E9E',
    }

    def __init__(self, status_id, is_active=False, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.status_id = status_id
        self.is_active = is_active
        self.on_press_callback = on_press

        self.size_hint = (None, None)
        self.size = (dp(36), dp(36))
        self.theme_icon_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0]
        self.ripple_scale = 0

        icon = self.STATUS_ICONS.get(status_id, 'circle')
        color = self.STATUS_COLORS.get(status_id, '#757575')

        self.icon = icon
        self.icon_color = self._hex_to_rgba(color, 1.0 if is_active else 0.4)

        self.bind(on_release=self._on_press)

    def _hex_to_rgba(self, hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [alpha]

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.status_id)

    def set_active(self, active):
        self.is_active = active
        color = self.STATUS_COLORS.get(self.status_id, '#757575')
        self.icon_color = self._hex_to_rgba(color, 1.0 if active else 0.4)


class TaskListItem(MDCard):
    """Компактная карточка задачи в списке"""

    STATUS_COLORS = {
        'done': '#4CAF50',
        'not_done': '#F44336',
        'in_progress': '#FFC107',
        'new': '#2196F3',
        'cancelled': '#9E9E9E',
    }

    def __init__(self, task_data, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.task_data = task_data
        self.task_id = task_data.get('id', 0)
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.padding = [dp(10), dp(4), dp(10), dp(4)]
        self.spacing = dp(10)
        self.radius = [dp(8)] * 4
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.04]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self.clip = True

        self._build_ui()
        self.bind(on_release=self._on_click)

    def _build_ui(self):
        status = self.task_data.get('status', 'new')
        color = self.STATUS_COLORS.get(status, '#757575')

        self.status_dot = MDCard(
            size_hint=(None, None),
            size=(dp(10), dp(10)),
            radius=[dp(5)] * 4,
            md_bg_color=self._hex_to_rgba(color),
            elevation=0,
            pos_hint={'center_y': 0.5}
        )

        title = self.task_data.get('title', 'Без названия')
        self.title_label = MDLabel(
            text=title,
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            size_hint_x=1,
            valign="middle",
            shorten=True,
            shorten_from="right"
        )

        self.arrow_label = MDLabel(
            text="›",
            font_size=sp(20),
            halign="center",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.2],
            size_hint_x=None,
            width=dp(20),
            valign="middle"
        )

        self.add_widget(self.status_dot)
        self.add_widget(self.title_label)
        self.add_widget(self.arrow_label)

    def _hex_to_rgba(self, hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)] + [alpha]

    def _on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.task_id)


class TasksScreen(BaseScreen):
    """Экран управления задачами - с сервером и кэшированием"""

    FILTER_STATUSES = ['all', 'done', 'not_done', 'in_progress', 'new', 'cancelled']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'tasks'
        self.bg_image = None
        self.tasks = []
        self.filtered_tasks = []
        self.current_filter = 'all'
        self._create_dialog = None
        self._is_loading = False
        self._is_rendering = False

        self.init_ui()
        self.load_background()

        logger.info('Экран задач создан')

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
            spacing=dp(4),
            size_hint=(1, 1),
            padding=[dp(12), dp(4), dp(12), dp(8)]
        )

        # ============ ВЕРХНЯЯ ПАНЕЛЬ ============
        header = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(10)
        )

        self.title_label = MDLabel(
            text="Задачи (0)",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True
        )

        self.create_btn = MDIconButton(
            icon="plus-circle",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5},
            on_release=self._show_create_dialog
        )

        # Кнопка обновления
        self.refresh_btn = MDIconButton(
            icon="refresh",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.6],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5},
            on_release=self._refresh_tasks
        )

        header.add_widget(self.title_label)
        header.add_widget(self.refresh_btn)
        header.add_widget(self.create_btn)
        content.add_widget(header)

        # ============ ФИЛЬТР ============
        filter_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(4),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        self.filter_icons = []
        for status_id in self.FILTER_STATUSES:
            icon = FilterIconButton(
                status_id=status_id,
                is_active=(status_id == self.current_filter),
                on_press=self._on_filter_press
            )
            filter_row.add_widget(icon)
            self.filter_icons.append(icon)

        filter_row.add_widget(Widget(size_hint_x=1))
        content.add_widget(filter_row)

        # ============ РАЗДЕЛИТЕЛЬ ============
        divider = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(1),
            md_bg_color=[1, 1, 1, 0.08]
        )
        content.add_widget(divider)

        # ============ КОНТЕЙНЕР СПИСКА ============
        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=2,
            bar_color=[0.5, 0.5, 0.5, 0.2],
            bar_inactive_color=[0.5, 0.5, 0.5, 0.05],
            bar_margin=dp(2)
        )

        self.tasks_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            adaptive_height=True,
            spacing=dp(2),
            padding=[dp(2), dp(4), dp(2), dp(4)]
        )

        self.scroll.add_widget(self.tasks_container)
        content.add_widget(self.scroll)

        self.build_ui(content_widget=content, use_scroll=False)

    def on_enter(self):
        """При входе на экран"""
        logger.info("🚪 Вход в экран задач")

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            app.top_nav.set_custom_title("Задачи")
            app.top_nav.back_btn.on_release = self.go_back

        # Загружаем задачи
        self.load_tasks()

    def load_tasks(self, force_refresh=False):
        """Загружает задачи с сервера или из кэша"""
        if self._is_loading:
            return

        self._is_loading = True

        # Показываем загрузку только если нет данных
        if not self.tasks:
            self._show_loading()

        api.get_tasks(
            on_success=self._on_tasks_loaded,
            on_failure=self._on_tasks_error,
            force_refresh=force_refresh,
            status=None
        )

    def _on_tasks_loaded(self, tasks):
        """Обработчик успешной загрузки задач"""
        self._is_loading = False
        self._hide_loading()

        self.tasks = tasks
        self._apply_filter()
        self._render_tasks()

        logger.info(f"✅ Загружено {len(tasks)} задач")

    def _on_tasks_error(self, req, error):
        """Обработчик ошибки загрузки"""
        self._is_loading = False
        self._hide_loading()

        if not self.tasks:
            self._show_error("Ошибка загрузки задач")

        logger.error(f"❌ Ошибка загрузки задач: {error}")

    def _refresh_tasks(self, instance):
        """Принудительное обновление задач"""
        self.load_tasks(force_refresh=True)

    def _apply_filter(self):
        """Применяет текущий фильтр"""
        if self.current_filter == 'all':
            self.filtered_tasks = self.tasks.copy()
        else:
            self.filtered_tasks = [t for t in self.tasks if t.get('status') == self.current_filter]

    def _render_tasks(self):
        """Отображает список задач"""
        if self._is_rendering:
            return

        self._is_rendering = True
        self.tasks_container.clear_widgets()

        total = len(self.tasks)
        filtered = len(self.filtered_tasks)

        if self.current_filter == 'all':
            self.title_label.text = f"Задачи ({total})"
        else:
            status_labels = {
                'done': 'Выполнено',
                'not_done': 'Не выполнено',
                'in_progress': 'В работе',
                'new': 'Новые',
                'cancelled': 'Отменены',
            }
            label = status_labels.get(self.current_filter, self.current_filter)
            self.title_label.text = f"{label} ({filtered})"

        if not self.filtered_tasks:
            text = "Нет задач" if self.current_filter == 'all' else "Нет задач с таким статусом"
            empty_label = MDLabel(
                text=text,
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.3],
                size_hint_y=None,
                height=dp(60)
            )
            self.tasks_container.add_widget(empty_label)
            self._is_rendering = False
            return

        # Добавляем задачи порциями для плавности
        self._add_tasks_batch(0)

    def _add_tasks_batch(self, start_index):
        """Добавляет задачи порциями"""
        batch_size = 10
        end_index = min(start_index + batch_size, len(self.filtered_tasks))

        for i in range(start_index, end_index):
            task = self.filtered_tasks[i]
            item = TaskListItem(
                task_data=task,
                on_click=self._open_task_detail
            )
            self.tasks_container.add_widget(item)

        if end_index < len(self.filtered_tasks):
            Clock.schedule_once(lambda dt: self._add_tasks_batch(end_index), 0.05)
        else:
            self._is_rendering = False

    def _on_filter_press(self, status_id):
        """Обработчик нажатия на фильтр"""
        if status_id == self.current_filter:
            return

        self.current_filter = status_id

        for icon in self.filter_icons:
            icon.set_active(icon.status_id == status_id)

        self._apply_filter()
        self._render_tasks()

    def _open_task_detail(self, task_id):
        """Открывает детальный просмотр задачи"""
        logger.info(f"📋 Открытие задачи ID={task_id}")

        task_data = None
        for task in self.tasks:
            if task.get('id') == task_id:
                task_data = task
                break

        if not task_data:
            notify.error("Задача не найдена")
            return

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('task_detail'):
                task_detail = self.manager.get_screen('task_detail')
                task_detail.set_task(task_data, self._on_task_updated)
                self.manager.current = 'task_detail'
            else:
                logger.error("Экран task_detail не найден")
                notify.error("Ошибка навигации")

    def _on_task_updated(self, updated_task):
        """Callback при обновлении задачи"""
        if updated_task is None:
            # Задача удалена, перезагружаем
            self.load_tasks(force_refresh=True)
            return

        # Обновляем задачу в списке
        for i, task in enumerate(self.tasks):
            if task.get('id') == updated_task.get('id'):
                self.tasks[i] = updated_task
                break

        self._apply_filter()
        self._render_tasks()
        logger.info(f"✅ Задача {updated_task.get('id')} обновлена")

    def _show_loading(self):
        """Показывает индикатор загрузки"""
        self.tasks_container.clear_widgets()
        loading_label = MDLabel(
            text="Загрузка...",
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
            size_hint_y=None,
            height=dp(60)
        )
        self.tasks_container.add_widget(loading_label)

    def _hide_loading(self):
        """Скрывает индикатор загрузки"""
        pass

    def _show_error(self, text):
        """Показывает ошибку"""
        self.tasks_container.clear_widgets()
        error_label = MDLabel(
            text=text,
            halign="center",
            font_size=sp(14),
            theme_text_color="Custom",
            text_color=[1, 0.3, 0.3, 0.8],
            size_hint_y=None,
            height=dp(60)
        )
        self.tasks_container.add_widget(error_label)

    # ============ ДИАЛОГ СОЗДАНИЯ ============

    def _show_create_dialog(self, instance):
        """Показывает диалог создания задачи"""
        if self._create_dialog:
            self._create_dialog.dismiss()

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(12),
            size_hint_y=None,
            adaptive_height=True
        )

        self._title_field = MDTextField(
            hint_text="Название задачи *",
            mode="fill",
            size_hint_y=None,
            height=dp(48),
            font_size=sp(14)
        )

        self._desc_field = MDTextField(
            hint_text="Описание задачи",
            mode="fill",
            size_hint_y=None,
            height=dp(70),
            font_size=sp(14),
            multiline=True
        )

        self._version_field = MDTextField(
            hint_text="Версия программы",
            mode="fill",
            size_hint_y=None,
            height=dp(44),
            font_size=sp(14),
            text="1.0.0"
        )

        content.add_widget(self._title_field)
        content.add_widget(self._desc_field)
        content.add_widget(self._version_field)

        buttons = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(48),
            spacing=dp(8)
        )

        cancel_btn = MDRaisedButton(
            text="Отмена",
            size_hint=(0.5, 1),
            on_release=lambda x: self._create_dialog.dismiss()
        )

        save_btn = MDRaisedButton(
            text="Создать",
            size_hint=(0.5, 1),
            on_release=lambda x: self._create_task()
        )

        buttons.add_widget(cancel_btn)
        buttons.add_widget(save_btn)
        content.add_widget(buttons)

        self._create_dialog = MDDialog(
            title="Новая задача",
            type="custom",
            content_cls=content,
            radius=[theme.CORNER_RADIUS] * 4
        )
        self._create_dialog.open()

    def _create_task(self):
        """Создаёт новую задачу на сервере"""
        title = self._title_field.text.strip()
        if not title:
            notify.warning("Введите название задачи")
            return

        task_data = {
            'title': title,
            'description': self._desc_field.text.strip(),
            'version': self._version_field.text.strip() or '1.0.0',
            'status': 'new'
        }

        api.create_task(
            task_data=task_data,
            on_success=self._on_task_created,
            on_failure=self._on_task_create_error
        )

    def _on_task_created(self, result):
        """Обработчик успешного создания задачи"""
        if self._create_dialog:
            self._create_dialog.dismiss()
            self._create_dialog = None

        notify.success("Задача создана")
        self.load_tasks(force_refresh=True)

    def _on_task_create_error(self, req, error):
        """Обработчик ошибки создания"""
        notify.error("Ошибка создания задачи")
        logger.error(f"❌ Ошибка создания задачи: {error}")

    def go_back(self, instance=None):
        """Возврат в админ панель"""
        logger.info("🔙 Возврат в админ панель")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'admin'