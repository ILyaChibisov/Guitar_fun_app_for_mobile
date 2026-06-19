# screens/components/bottom_nav.py
"""
Нижняя панель навигации - с Material Design иконками
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.clock import Clock

from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import get_logger
from config.system_bars import get_navigation_bar_height

logger = get_logger('BottomNav')


class NavItem(ButtonBehavior, BoxLayout):
    """Элемент нижней навигации с Material Design иконками"""

    text = StringProperty('')
    active = BooleanProperty(False)

    def __init__(self, icon_name, text, screen_name, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.text = text
        self.screen_name = screen_name

        self.orientation = 'vertical'
        self.size_hint = (1, 1)

        # Центрируем содержимое по вертикали и горизонтали
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # Настройки размеров - УМЕНЬШАЕМ ВСЁ
        if platform == 'android':
            self.spacing = dp(4)
            self.padding = [0, dp(4), 0, dp(4)]
            icon_size = dp(24)
            # Для Android используем sp
            font_size = sp(10)
            label_height = dp(16)
        else:
            self.spacing = dp(2)
            self.padding = [0, dp(2), 0, dp(2)]  # уменьшили padding
            icon_size = dp(22)  # уменьшили иконку

            # Для Windows используем фиксированный размер в пикселях
            # Все пункты одинакового размера, чтобы не было разницы
            font_size = 8  # фиксированный размер в пикселях
            label_height = dp(14)

        # Медно-золотой цвет для активного состояния
        self.copper_gold = [0.85, 0.65, 0.25, 1]

        # Иконка MDIconButton
        self.icon_btn = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(icon_size, icon_size),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            ripple_scale=0
        )
        self.icon_btn.bind(on_release=self._on_child_click)

        # Текст - с уменьшенным шрифтом
        self.text_label = MDLabel(
            text=text,
            font_size=font_size,
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=label_height,
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            bold=False,
            shorten=False
        )
        self.text_label.bind(on_touch_down=self._on_child_touch)

        # Контейнер для вертикального центрирования
        self.add_widget(self.icon_btn)
        self.add_widget(self.text_label)

        self.update_state(self, self.active)
        self.bind(active=self.update_state)

    def _on_child_click(self, instance):
        """Обработчик клика по иконке - передаём родителю"""
        self.on_release()

    def _on_child_touch(self, instance, touch):
        """Обработчик касания по тексту - передаём родителю"""
        if instance.collide_point(*touch.pos):
            self.on_release()
            return True
        return False

    def update_state(self, instance, value):
        """Обновляет состояние иконки при активации"""
        if value:
            self.icon_btn.icon_color = self.copper_gold
            self.text_label.text_color = self.copper_gold
            self.text_label.bold = True
        else:
            self.icon_btn.icon_color = theme.TEXT_SECONDARY
            self.text_label.text_color = theme.TEXT_SECONDARY
            self.text_label.bold = False

    def on_release(self):
        """Обработчик отпускания кнопки"""
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

        # Анимация нажатия
        anim = Animation(opacity=0.6, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)

        # Переход на нужный экран
        if hasattr(self.parent, 'switch_to'):
            self.parent.switch_to(self.screen_name)


class BottomNav(BoxLayout):
    """Нижняя панель навигации - 5 разделов (с Метрономом)"""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.size_hint = (1, None)
        self.pos_hint = {'y': 0}

        nav_bar_height = get_navigation_bar_height()

        if platform == 'android':
            self.nav_height = dp(56)
            bottom_padding = 0
            button_spacing = dp(2)
        else:
            # Для Windows увеличиваем высоту панели
            self.nav_height = dp(58)
            bottom_padding = nav_bar_height + dp(4)
            button_spacing = dp(2)

        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height

        self.padding = [dp(4), dp(2), dp(4), bottom_padding]  # уменьшили padding
        self.spacing = button_spacing
        self.md_bg_color = [0, 0, 0, 0]

        logger.info("=" * 70)
        logger.info(f"📱 BOTTOM NAV - {platform.upper()}")
        logger.info(f"📱 Высота панели: {self.nav_height}dp")
        logger.info(f"📱 Разделы: Песни, Аккорды, Тюнер, Метроном, Избранное")
        logger.info("=" * 70)

        # 5 разделов с Material Design иконками
        self.nav_items = [
            ('music-note', 'Песни', 'songs'),
            ('guitar-pick', 'Аккорды', 'chords'),
            ('tune', 'Тюнер', 'tuner'),
            ('metronome', 'Метроном', 'metronome'),
            ('heart', 'Избранное', 'favorites'),
        ]

        self.items = []
        for icon, text, screen in self.nav_items:
            item = NavItem(icon, text, screen)
            item.active = (screen == 'songs')
            item.size_hint = (1, 1)
            self.add_widget(item)
            self.items.append(item)

        if hasattr(screen_manager, 'add_observer'):
            screen_manager.add_observer(self.on_screen_changed)

    def on_screen_changed(self, screen_name):
        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item.active = (screen == screen_name)

    def switch_to(self, screen_name):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

        if not self.sm or self.sm.current == screen_name:
            return

        # Обновляем активное состояние всех элементов
        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item.active = (screen == screen_name)

        # Определяем направление перехода
        try:
            current_index = next(i for i, (_, _, s) in enumerate(self.nav_items) if s == self.sm.current)
            new_index = next(i for i, (_, _, s) in enumerate(self.nav_items) if s == screen_name)
            direction = 'left' if new_index > current_index else 'right'
        except StopIteration:
            direction = 'left'

        self.sm.transition.direction = direction
        self.sm.current = screen_name

    def switch_tab(self, screen_name):
        self.switch_to(screen_name)

    def reload_config(self):
        nav_bar_height = get_navigation_bar_height()

        if platform == 'android':
            self.nav_height = dp(56)
            bottom_padding = 0
            button_spacing = dp(2)
        else:
            self.nav_height = dp(58)
            bottom_padding = nav_bar_height + dp(4)
            button_spacing = dp(2)

        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height
        self.padding = [dp(4), dp(2), dp(4), bottom_padding]
        self.spacing = button_spacing