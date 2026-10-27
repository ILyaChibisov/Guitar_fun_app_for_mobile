# screens/components/compact_vertical_slider.py
"""
Вертикальный слайдер с постоянно видимым label (badge) рядом с thumb.
Толстая дорожка и крупный thumb — как в метрономе.
Адаптируется под высоту контейнера.
"""
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from kivymd.uix.slider import MDSlider
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from state.settings_state import settings_state


def get_slider_colors(theme_id):
    if theme_id == 'light':
        return {
            'accent': [0.1, 0.55, 0.3, 1],
            'track_inactive': [0, 0, 0, 0.15],
            'badge_bg': [1, 1, 1, 0.98],
            'badge_text': [0.1, 0.1, 0.1, 1],
            'badge_line': [0.1, 0.55, 0.3, 0.6],
        }
    elif theme_id == 'dark':
        return {
            'accent': [1.0, 0.5, 0.0, 1],
            'track_inactive': [1, 1, 1, 0.2],
            'badge_bg': [0.12, 0.12, 0.12, 0.98],
            'badge_text': [1, 1, 1, 0.95],
            'badge_line': [1.0, 0.5, 0.0, 0.6],
        }
    else:  # green
        return {
            'accent': [0.46, 0.70, 0.71, 1],
            'track_inactive': [1, 1, 1, 0.3],
            'badge_bg': [0.08, 0.08, 0.08, 0.95],
            'badge_text': [1, 1, 1, 0.95],
            'badge_line': [0.46, 0.70, 0.71, 0.6],
        }


class CompactVerticalSlider(FloatLayout):
    value = NumericProperty(0)

    def __init__(self, min_value=0, max_value=10, step=1, initial=0,
                 formatter=None, on_change=None, track_width=dp(48),
                 thumb_size=dp(36), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(64)  # дорожка + место для label

        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.initial = initial
        self.formatter = formatter or (lambda v: str(int(v)))
        self.on_change = on_change
        self.track_width = track_width
        self.thumb_size = thumb_size
        self._value = initial

        # Основной вертикальный слайдер
        self.slider = MDSlider(
            min=self.min_value - 0.01,
            max=self.max_value + 0.01,
            value=self.initial,
            step=self.step,
            size_hint=(None, 1),
            width=self.track_width,
            orientation='vertical',
            pos_hint={'center_x': 0.4, 'center_y': 0.5},  # сдвинут влево
            hint=False,
        )
        self.slider.ripple_scale = 0
        self.slider.bind(value=self._on_slider_value)

        try:
            self.slider.cursor_size = (self.thumb_size, self.thumb_size)
            self.slider.hint_width = self.thumb_size
        except Exception:
            pass

        # Badge (значение)
        self.badge = MDCard(
            size_hint=(None, None),
            size=(dp(40), dp(22)),
            radius=[dp(6)] * 4,
            elevation=2,
            padding=0,
        )
        self.badge_label = MDLabel(
            text=self.formatter(self.initial),
            font_size=sp(11),
            halign='center',
            valign='middle',
            bold=True,
        )
        self.badge.add_widget(self.badge_label)

        self.add_widget(self.slider)
        self.add_widget(self.badge)

        self.update_theme_colors()

        Clock.schedule_once(lambda dt: self._update_badge_position(), 0.05)
        Clock.schedule_once(lambda dt: self._update_badge_position(), 0.2)

    def _on_slider_value(self, instance, value):
        if value < self.min_value:
            self.slider.value = self.min_value
            return
        if value > self.max_value:
            self.slider.value = self.max_value
            return
        rounded = round(value / self.step) * self.step
        if rounded != value:
            self.slider.value = rounded
            return

        self._value = rounded
        self.value = rounded
        self.badge_label.text = self.formatter(rounded)
        self._update_badge_position()

        if self.on_change:
            self.on_change(rounded)

    def set_value(self, new_value):
        new_value = max(self.min_value, min(self.max_value, new_value))
        rounded = round(new_value / self.step) * self.step
        self.slider.value = rounded

    def get_value(self):
        return self._value

    def _update_badge_position(self):
        if not hasattr(self, 'badge') or not self.slider:
            return

        v = self._value
        rng = (self.max_value - self.min_value) or 1
        pct = (v - self.min_value) / rng

        # Позиция thumb внутри слайдера
        pad = self.thumb_size / 2
        track_h = max(self.slider.height - self.thumb_size, dp(1))
        thumb_y_in_slider = pad + pct * track_h

        # Абсолютная позиция badge
        badge_h = self.badge.height
        badge_y = self.slider.y + thumb_y_in_slider - badge_h / 2

        # Ограничиваем Y
        min_y = self.y
        max_y = self.top - badge_h
        badge_y = max(min_y, min(max_y, badge_y))

        # Справа от thumb
        badge_x = self.slider.right + dp(4)

        self.badge.pos = (badge_x, badge_y)

    def update_theme_colors(self):
        c = get_slider_colors(settings_state.theme)
        self.slider.thumb_color_active = c['accent']
        self.slider.thumb_color_inactive = c['accent']
        self.slider.thumb_color_disabled = c['accent']
        self.slider.track_color_active = c['accent'][:3] + [0.7]
        self.slider.track_color_inactive = c['track_inactive']
        self.slider.color = c['accent']

        self.badge.md_bg_color = c['badge_bg']
        self.badge.line_color = c['badge_line']
        self.badge.line_width = 1
        self.badge_label.text_color = c['badge_text']

    def on_size(self, *args):
        Clock.schedule_once(lambda dt: self._update_badge_position(), 0)

    def on_pos(self, *args):
        Clock.schedule_once(lambda dt: self._update_badge_position(), 0)