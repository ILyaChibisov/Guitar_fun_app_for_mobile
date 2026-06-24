# screens/components/bottom_nav.py
"""
Нижняя панель навигации - с Material Design иконками
Адаптивный шрифт без переносов
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty
from kivy.metrics import dp, sp
from kivy.utils import platform
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

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
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # ============ АДАПТИВНЫЕ РАЗМЕРЫ ============
        if platform == 'android':
            icon_size = dp(24)
            label_height = dp(14)  # Увеличена с 13
            font_size = sp(9)  # Увеличена с 8
        else:
            icon_size = dp(22)
            label_height = dp(13)  # Увеличена с 12
            font_size = sp(8)  # Увеличена с 7

        # Медно-золотой цвет для активного состояния
        self.copper_gold = [0.85, 0.65, 0.25, 1]

        # Иконка - только допустимые параметры
        self.icon_btn = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(icon_size, icon_size),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_x': 0.5, 'center_y': 0.58},
            ripple_scale=0
        )
        self.icon_btn.bind(on_release=self._on_child_click)

        # ============ ТЕКСТ С АДАПТИВНЫМ ШРИФТОМ ============
        self.text_label = MDLabel(
            text=text,
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=label_height,
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            bold=False,
            shorten=True,
            shorten_from="right",
            font_size=font_size
        )

        self.text_label.bind(width=self._adjust_font_size)
        self.text_label.bind(text=self._adjust_font_size)
        self.text_label.bind(on_touch_down=self._on_child_touch)

        # Используем FloatLayout для точного позиционирования
        from kivy.uix.floatlayout import FloatLayout
        self.inner_layout = FloatLayout(size_hint=(1, 1))

        # Иконка по центру по X, чуть выше центра по Y
        self.icon_btn.pos_hint = {'center_x': 0.5, 'center_y': 0.58}

        # Текст под иконкой
        self.text_label.pos_hint = {'center_x': 0.5, 'y': 0.02}
        self.text_label.size_hint = (1, None)

        self.inner_layout.add_widget(self.icon_btn)
        self.inner_layout.add_widget(self.text_label)

        self.add_widget(self.inner_layout)

        self.update_state(self, self.active)
        self.bind(active=self.update_state)

        Clock.schedule_once(lambda dt: self._adjust_font_size(), 0.1)

    def _adjust_font_size(self, *args):
        if not hasattr(self, 'text_label') or not self.text_label:
            return

        text = self.text_label.text
        if not text:
            return

        available_width = self.text_label.width - dp(2)

        if available_width < dp(14):
            self.text_label.font_size = sp(7)
            return

        test_sizes = [10, 9, 8, 7, 6]  # Увеличены размеры
        for size in test_sizes:
            from kivy.core.text import Label as CoreLabel
            test_label = CoreLabel(
                text=text,
                font_size=sp(size),
                font_name=self.text_label.font_name,
                bold=False
            )
            test_label.refresh()
            text_width = test_label.texture.width

            if text_width <= available_width:
                self.text_label.font_size = sp(size)
                self.text_label.text_size = (available_width, None)
                return

        self.text_label.font_size = sp(6)

    def _on_child_click(self, instance):
        self.on_release()

    def _on_child_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.on_release()
            return True
        return False

    def update_state(self, instance, value):
        if value:
            self.icon_btn.icon_color = self.copper_gold
            self.text_label.text_color = self.copper_gold
            self.text_label.bold = True
        else:
            self.icon_btn.icon_color = theme.TEXT_SECONDARY
            self.text_label.text_color = theme.TEXT_SECONDARY
            self.text_label.bold = False

    def on_release(self):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

        anim = Animation(opacity=0.6, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)

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
            self.nav_height = dp(44)
            bottom_padding = 0
            button_spacing = dp(0)
        else:
            self.nav_height = dp(44)
            bottom_padding = nav_bar_height + dp(2)
            button_spacing = dp(0)

        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height

        side_padding = dp(2)
        self.padding = [side_padding, dp(1), side_padding, bottom_padding]
        self.spacing = button_spacing
        self.md_bg_color = [0, 0, 0, 0]

        # ============ РИСУЕМ РАЗДЕЛИТЕЛЬНУЮ ЛИНИЮ ВВЕРХУ ============
        with self.canvas.before:
            Color(1, 1, 1, 0.08)  # Полупрозрачная белая линия
            self.line = Rectangle(pos=(self.x, self.y + self.height - dp(1)),
                                  size=(self.width, dp(1)))

        self.bind(pos=self._update_line, size=self._update_line)

        logger.info("=" * 70)
        logger.info(f"📱 BOTTOM NAV - {platform.upper()}")
        logger.info(f"📱 Высота панели: {self.nav_height}dp")
        logger.info(f"📱 Боковые отступы: {side_padding}dp")
        logger.info(f"📱 Отступ снизу: {bottom_padding}dp")
        logger.info("=" * 70)

        self.nav_items = [
            ('guitar-electric', 'Песни', 'songs'),
            ('music-note', 'Аккорды', 'chords'),
            ('waveform', 'Тюнер', 'tuner'),
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

    def _update_line(self, *args):
        """Обновляет позицию разделительной линии"""
        if hasattr(self, 'line'):
            self.line.pos = (self.x, self.y + self.height - dp(1))
            self.line.size = (self.width, dp(1))

    def on_screen_changed(self, screen_name):
        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item.active = (screen == screen_name)

    def switch_to(self, screen_name):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

        if not self.sm or self.sm.current == screen_name:
            return

        for item, (_, _, screen) in zip(self.items, self.nav_items):
            item.active = (screen == screen_name)

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
            self.nav_height = dp(44)
            bottom_padding = 0
            button_spacing = dp(0)
        else:
            self.nav_height = dp(44)
            bottom_padding = nav_bar_height + dp(2)
            button_spacing = dp(0)

        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height

        side_padding = dp(2)
        self.padding = [side_padding, dp(1), side_padding, bottom_padding]
        self.spacing = button_spacing

        # Обновляем линию
        self._update_line()