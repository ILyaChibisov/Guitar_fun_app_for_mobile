# screens/components/bottom_nav.py
"""
Нижняя панель навигации - с Material Design иконками.
Адаптивный шрифт без переносов.
Поддерживает смену темы и языка.
В зелёной теме: неактивные кнопки — мятные (цвет тюнера),
активная — своего цвета, активный тюнер — белый.
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
from utils.settings_manager import settings_manager
from utils.localization import get_text

logger = get_logger('BottomNav')


# ============================================================
# ПАЛИТРА ДЛЯ ЗЕЛЁНОЙ ТЕМЫ
# ============================================================

# Индивидуальные цвета для активной вкладки (кроме тюнера)
GREEN_ACTIVE_COLORS = {
    'songs': [1.0, 0.95, 0.30, 1.0],      # Коралл
    'chords': [0.20, 0.60, 1.0, 1.0],     # Синий
    'metronome': [1.0, 0.55, 0.20, 1.0],  # Оранжевый
    'favorites': [1.0, 0.10, 0.20, 1.0],  # Красный
}

# Цвет для неактивных кнопок (мятный, как тюнер)
GREEN_INACTIVE_COLOR = [0.66, 0.90, 0.85, 0.7]

# Активный тюнер — белый
GREEN_TUNER_ACTIVE = [1, 1, 1, 1]


class NavItem(ButtonBehavior, BoxLayout):
    """Элемент нижней навигации с Material Design иконками"""

    text = StringProperty('')
    active = BooleanProperty(False)

    def __init__(self, icon_name, text_key, screen_name, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.text_key = text_key
        self.text = get_text(text_key, text_key.capitalize())
        self.screen_name = screen_name

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        if platform == 'android':
            icon_size = dp(28)
            label_height = dp(16)
            font_size = sp(11)
        else:
            icon_size = dp(26)
            label_height = dp(15)
            font_size = sp(10)

        from kivy.uix.floatlayout import FloatLayout
        self.inner_layout = FloatLayout(size_hint=(1, 1))

        self.icon_btn = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(icon_size, icon_size),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_x': 0.5, 'center_y': 0.62},
            ripple_scale=0
        )
        self.icon_btn.bind(on_release=self._on_child_click)

        self.text_label = MDLabel(
            text=self.text,
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=label_height,
            theme_text_color="Custom",
            text_color=theme.TEXT_SECONDARY,
            bold=False,
            shorten=True,
            shorten_from="right",
            font_size=font_size,
            pos_hint={'center_x': 0.5, 'y': 0.06}
        )

        self.text_label.bind(width=self._adjust_font_size)
        self.text_label.bind(text=self._adjust_font_size)
        self.text_label.bind(on_touch_down=self._on_child_touch)

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
            self.text_label.font_size = sp(8)
            return

        test_sizes = [12, 11, 10, 9, 8, 7]
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

        self.text_label.font_size = sp(7)

    def _on_child_click(self, instance):
        self.on_release()

    def _on_child_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.on_release()
            return True
        return False

    def update_state(self, instance, value):
        theme_id = settings_manager.theme

        if theme_id == 'light':
            active_color = [0.1, 0.55, 0.3, 1]
            inactive_color = [0.1, 0.55, 0.3, 0.7]
            if value:
                self.icon_btn.icon_color = [0.05, 0.4, 0.2, 1]
                self.text_label.text_color = [0.05, 0.4, 0.2, 1]
                self.text_label.bold = True
            else:
                self.icon_btn.icon_color = inactive_color
                self.text_label.text_color = inactive_color
                self.text_label.bold = False
        elif theme_id == 'dark':
            active_color = [1, 1, 1, 1]
            inactive_color = [1.0, 0.5, 0.0, 0.7]
            if value:
                self.icon_btn.icon_color = active_color
                self.text_label.text_color = active_color
                self.text_label.bold = True
            else:
                self.icon_btn.icon_color = inactive_color
                self.text_label.text_color = inactive_color
                self.text_label.bold = False
        else:  # green
            if value:
                if self.screen_name == 'tuner':
                    active_color = GREEN_TUNER_ACTIVE
                else:
                    active_color = GREEN_ACTIVE_COLORS.get(
                        self.screen_name, [1, 1, 1, 1]
                    )
                self.icon_btn.icon_color = active_color
                self.text_label.text_color = active_color
                self.text_label.bold = True
            else:
                self.icon_btn.icon_color = GREEN_INACTIVE_COLOR
                self.text_label.text_color = GREEN_INACTIVE_COLOR
                self.text_label.bold = False

    def on_release(self):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

        anim = Animation(opacity=0.6, duration=0.05)
        anim += Animation(opacity=1, duration=0.1)
        anim.start(self)

        if hasattr(self.parent, 'switch_to'):
            self._update_top_nav_before_switch(self.screen_name)
            self.parent.switch_to(self.screen_name)

    def _update_top_nav_before_switch(self, screen_name):
        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav'):
            titles = {
                'songs': get_text('songs', 'Песни'),
                'chords': get_text('chords', 'Аккорды'),
                'tuner': get_text('tuner', 'Тюнер'),
                'metronome': get_text('metronome', 'Метроном'),
                'favorites': get_text('favorites', 'Избранное'),
            }
            if screen_name in titles:
                app.top_nav.set_custom_title(titles[screen_name])
                logger.info(f"✅ TopNav обновлён ДО перехода: {titles[screen_name]}")


class BottomNav(BoxLayout):
    """Нижняя панель навигации - 5 разделов"""

    NAV_SCREENS = ['songs', 'chords', 'tuner', 'metronome', 'favorites']

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.sm = screen_manager
        self.size_hint = (1, None)
        self.pos_hint = {'y': 0}

        nav_bar_height = get_navigation_bar_height()
        self.nav_height = dp(52)

        if platform == 'android':
            bottom_padding = 0
        else:
            bottom_padding = nav_bar_height

        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height

        side_padding = dp(4)
        self.padding = [side_padding, dp(2), side_padding, bottom_padding]
        self.spacing = 0
        self.md_bg_color = [0, 0, 0, 0]

        with self.canvas.before:
            self.line_color_inst = Color(1, 1, 1, 0.08)
            self.line = Rectangle(pos=(self.x, self.y + self.height - dp(1)),
                                  size=(self.width, dp(1)))

        self.bind(pos=self._update_line, size=self._update_line)

        self.nav_items = [
            ('guitar-electric', 'songs', 'songs'),
            ('music-note', 'chords', 'chords'),
            ('waveform', 'tuner', 'tuner'),
            ('metronome', 'metronome', 'metronome'),
            ('heart', 'favorites', 'favorites'),
        ]

        self.items = []
        for icon, text_key, screen in self.nav_items:
            item = NavItem(icon, text_key, screen)
            item.active = (screen == 'songs')
            item.size_hint = (1, 1)
            self.add_widget(item)
            self.items.append(item)

        if hasattr(screen_manager, 'add_observer'):
            screen_manager.add_observer(self.on_screen_changed)

        self.update_theme_colors()

    def _update_line(self, *args):
        if hasattr(self, 'line'):
            self.line.pos = (self.x, self.y + self.height - dp(1))
            self.line.size = (self.width, dp(1))

    def update_theme_colors(self):
        theme_id = settings_manager.theme

        if theme_id == 'light':
            self.line_color_inst.rgba = (0.1, 0.55, 0.3, 0.3)
        elif theme_id == 'dark':
            self.line_color_inst.rgba = (1.0, 0.5, 0.0, 0.3)
        else:
            self.line_color_inst.rgba = (1, 1, 1, 0.08)

        for item in self.items:
            item.update_state(item, item.active)

    def update_language(self):
        for item, (_, text_key, _) in zip(self.items, self.nav_items):
            translated_text = get_text(text_key, text_key.capitalize())
            item.text = translated_text
            item.text_label.text = translated_text
            item._adjust_font_size()

    def on_screen_changed(self, screen_name):
        self._update_active_state(screen_name)

    def _update_active_state(self, screen_name):
        if screen_name in self.NAV_SCREENS:
            for item, (_, _, screen) in zip(self.items, self.nav_items):
                item.active = (screen == screen_name)
        else:
            self.clear_active()

    def clear_active(self):
        for item in self.items:
            item.active = False
        logger.debug("🔽 Все иконки BottomNav сброшены")

    def switch_to(self, screen_name):
        app = MDApp.get_running_app()
        if hasattr(app, 'is_auth_blocking') and app.is_auth_blocking:
            return

        if not self.sm or self.sm.current == screen_name:
            return

        self._update_active_state(screen_name)

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
        self.nav_height = dp(52)

        if platform == 'android':
            bottom_padding = 0
        else:
            bottom_padding = nav_bar_height

        self.total_height = self.nav_height + bottom_padding
        self.height = self.total_height

        side_padding = dp(4)
        self.padding = [side_padding, dp(2), side_padding, bottom_padding]
        self.spacing = 0

        self._update_line()