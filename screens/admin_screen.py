# screens/admin_screen.py (обновленный)
"""
Экран администратора - горизонтальный скролл парсеров
Иконки из ассетов, все парсеры в один ряд
"""
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from kivy.uix.image import Image
from io import BytesIO

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.behaviors import CircularRippleBehavior

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from utils.notifications import notify

logger = screen_logger('AdminScreen')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None

# Константа для иконки парсера
ASSET_PARSER_PNG = "parser_png"


class ParserCard(CircularRippleBehavior, MDCard):
    """
    Карточка парсера с иконкой из ассетов
    """

    # Цвета для разных парсеров
    PARSER_COLORS = {
        'amdm': ('#2196F3', '#1976D2'),
        'mytabs': ('#9C27B0', '#7B1FA2'),
        'accord_pro': ('#FF9800', '#F57C00'),
        'akkordus': ('#E91E63', '#C2185B'),
        'muzland': ('#4CAF50', '#388E3C'),
        'chordie': ('#FFC107', '#FFA000'),
        'fivelad': ('#FF5722', '#E64A19'),
        'akkordbard': ('#00BCD4', '#0097A7'),
        'domhve': ('#009688', '#00796B'),
        'rushsound': ('#F44336', '#D32F2F'),
    }

    def __init__(self, parser_id, title, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.parser_id = parser_id
        self.title = title
        self.on_click_callback = on_click

        colors = self.PARSER_COLORS.get(parser_id, ('#757575', '#616161'))
        self.bg_color = colors[0]

        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.width = dp(90)
        self.height = dp(110)
        self.radius = [dp(16)]
        self.elevation = 2
        self.ripple_scale = 0.95

        # Фон
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.85)

        # Контент
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(6),
            padding=[dp(8), dp(12), dp(8), dp(12)],
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )

        # Иконка из ассета parser_png
        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        self._load_icon()

        # Название
        self.title_label = MDLabel(
            text=title,
            font_size=sp(10),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(25),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            shorten=True,
            shorten_from="right"
        )

        content.add_widget(self.icon_image)
        content.add_widget(self.title_label)

        self.add_widget(content)
        self.bind(on_release=self._on_click)

        # Анимация при наведении
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _load_icon(self):
        """Загружает иконку из ассета parser_png"""
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(ASSET_PARSER_PNG)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки: {e}")
        # Если не загрузилась, показываем текстовую заглушку
        self.icon_image.text = "🎸"

    def _hex_to_rgba(self, hex_color, alpha=1.0):
        hex_color = hex_color.lstrip('#')
        return [
            int(hex_color[i:i + 2], 16) / 255.0
            for i in (0, 2, 4)
        ] + [alpha]

    def _on_enter(self, *args):
        Animation(elevation=6, duration=0.2).start(self)
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 1.0)

    def _on_leave(self, *args):
        Animation(elevation=2, duration=0.2).start(self)
        self.md_bg_color = self._hex_to_rgba(self.bg_color, 0.85)

    def _on_click(self, instance):
        if self.on_click_callback:
            Animation(opacity=0.7, duration=0.05).start(self)
            Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.1).start(self), 0.05)
            self.on_click_callback(self.parser_id)


class ActionCard(CircularRippleBehavior, MDCard):
    """
    Карточка действия (очистка кэша, статистика)
    """

    def __init__(self, action_id, title, icon, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.action_id = action_id
        self.title = title
        self.icon_name = icon
        self.on_click_callback = on_click

        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.width = dp(120)
        self.height = dp(110)
        self.radius = [dp(16)]
        self.elevation = 2
        self.md_bg_color = [0.2, 0.2, 0.2, 0.85]
        self.line_color = [1, 1, 1, 0.1]
        self.line_width = 1

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=[dp(12), dp(16), dp(12), dp(16)],
            size_hint=(1, 1),
            md_bg_color=[0, 0, 0, 0]
        )

        # Иконка
        self.icon = MDIconButton(
            icon=icon,
            size_hint=(None, None),
            size=(dp(44), dp(44)),
            pos_hint={'center_x': 0.5},
            theme_icon_color="Custom",
            icon_color=[0.9, 0.9, 0.9, 1],
            md_bg_color=[0, 0, 0, 0.2],
            disabled=True
        )

        # Название
        self.title_label = MDLabel(
            text=title,
            font_size=sp(12),
            halign="center",
            bold=True,
            size_hint_y=None,
            height=dp(25),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            shorten=True
        )

        content.add_widget(self.icon)
        content.add_widget(self.title_label)

        self.add_widget(content)
        self.bind(on_release=self._on_click)

    def _on_click(self, instance):
        if self.on_click_callback:
            Animation(opacity=0.7, duration=0.05).start(self)
            Clock.schedule_once(lambda dt: Animation(opacity=1, duration=0.1).start(self), 0.05)
            self.on_click_callback(self.action_id)


class AdminScreen(BaseScreen):
    """Экран администратора с горизонтальным скроллом парсеров"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'admin'
        self.bg_image = None
        self.init_ui()
        self.load_background()
        logger.info('Экран администратора создан')

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
        # Вертикальный контейнер для всего контента
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(12), dp(8), dp(12), dp(16)]
        )

        # ============ ЗАГОЛОВОК ============
        header_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(60),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            radius=[dp(16), dp(16), dp(16), dp(16)],
            md_bg_color=[0, 0, 0, 0.15],
            elevation=0,
            line_color=[1, 1, 1, 0.05],
            line_width=1
        )

        title_label = MDLabel(
            text="Админ панель",
            font_size=sp(22),
            halign="center",
            bold=True,
            size_hint_y=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1]
        )
        header_card.add_widget(title_label)
        content.add_widget(header_card)

        # ============ ВСЕ ПАРСЕРЫ ============
        section_title = MDLabel(
            text="Парсеры",
            font_size=sp(14),
            bold=True,
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8]
        )
        content.add_widget(section_title)

        # Горизонтальный скролл для парсеров
        scroll_parsers = ScrollView(
            size_hint=(1, None),
            height=dp(130),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=dp(4),
            bar_color=[1, 1, 1, 0.3],
            bar_inactive_color=[1, 1, 1, 0.1]
        )

        parsers_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_x=None,
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )
        parsers_layout.bind(minimum_width=parsers_layout.setter('width'))

        # Все парсеры
        all_parsers = [
            ('amdm', 'AmDm'),
            ('mytabs', 'MyTabs'),
            ('accord_pro', 'Akkords.Pro'),
            ('akkordus', 'Akkordus'),
            ('muzland', 'Muzland'),
            ('chordie', 'Chordie'),
            ('fivelad', '5Lad'),
            ('akkordbard', 'AkkordBard'),
            ('domhve', 'Domhve'),
            ('rushsound', 'RushSound'),
        ]

        for parser_id, title in all_parsers:
            card = ParserCard(
                parser_id=parser_id,
                title=title,
                on_click=self.on_parser_selected
            )
            parsers_layout.add_widget(card)

        scroll_parsers.add_widget(parsers_layout)
        content.add_widget(scroll_parsers)

        # ============ ДЕЙСТВИЯ ============
        content.add_widget(Widget(size_hint_y=None, height=dp(4)))

        actions_title = MDLabel(
            text="Действия",
            font_size=sp(14),
            bold=True,
            size_hint_y=None,
            height=dp(28),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.8]
        )
        content.add_widget(actions_title)

        # Горизонтальный скролл для действий
        scroll_actions = ScrollView(
            size_hint=(1, None),
            height=dp(130),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=dp(4),
            bar_color=[1, 1, 1, 0.3],
            bar_inactive_color=[1, 1, 1, 0.1]
        )

        actions_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(12),
            size_hint_x=None,
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )
        actions_layout.bind(minimum_width=actions_layout.setter('width'))

        # Очистка кэша
        clear_cache_card = ActionCard(
            action_id='clear_cache',
            title='Очистить кэш',
            icon='delete',
            on_click=self.on_action_selected
        )
        actions_layout.add_widget(clear_cache_card)

        # Статистика (заглушка)
        stats_card = ActionCard(
            action_id='statistics',
            title='Статистика',
            icon='chart-line',
            on_click=self.on_action_selected
        )
        actions_layout.add_widget(stats_card)

        scroll_actions.add_widget(actions_layout)
        content.add_widget(scroll_actions)

        # Нижний отступ
        content.add_widget(Widget(size_hint_y=None, height=dp(20)))

        # Строим UI
        self.build_ui(content_widget=content, use_scroll=True)

    def on_parser_selected(self, parser_id):
        """Обработчик выбора парсера"""
        logger.info(f"Выбран парсер: {parser_id}")

        navigation_map = {
            'amdm': 'amdm_parser',
            'mytabs': 'mytabs_parser',
            'accord_pro': 'accord_pro_parser',
            'akkordus': 'akkordus_parser',
            'muzland': 'muzland_parser',
            'chordie': 'chordie_parser',
            'fivelad': 'fivelad_parser',
            'akkordbard': 'akkordbard_parser',
            'domhve': 'domhve_parser',
            'rushsound': 'rushsound_parser',
        }

        screen_name = navigation_map.get(parser_id)
        if screen_name and hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen(screen_name):
                self.manager.current = screen_name
            else:
                logger.error(f"Экран {screen_name} не найден")
                notify.error("Ошибка навигации")

    def on_action_selected(self, action_id):
        """Обработчик выбора действия"""
        logger.info(f"Выбрано действие: {action_id}")

        if action_id == 'clear_cache':
            self.clear_cache()
        elif action_id == 'statistics':
            self.show_statistics()

    def clear_cache(self):
        """Очищает кэш API"""
        try:
            from api import api
            api.clear_cache()
            logger.info("Кэш очищен")
            notify.success("Кэш очищен")
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            notify.error("Ошибка очистки кэша")

    def show_statistics(self):
        """Показывает статистику (заглушка)"""
        notify.info("Статистика будет доступна в следующей версии")

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в админ панель")

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из админ панели")