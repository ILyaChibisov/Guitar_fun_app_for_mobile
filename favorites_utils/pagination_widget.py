# favorites_utils/pagination_widget.py
import base64
import io

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout

from data.favorites import pagination_assets
from state.settings_state import settings_state as settings_manager


class StudioPaginationPad(ButtonBehavior, Widget):
    """Металлический мини-пэд пагинации с подсветкой при нажатии (как в метрономе)."""

    arrow_type = StringProperty("next")  # 'first', 'prev', 'next', 'last'
    enabled_state = BooleanProperty(True)
    is_pressed = BooleanProperty(False)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    _textures_loaded = False
    _up_dark = None
    _down_dark = None
    _up_light = None
    _down_light = None
    _arrow_textures = {}

    def __init__(self, arrow_type="next", on_press=None, width=dp(44), **kwargs):
        super().__init__(**kwargs)
        self.arrow_type = arrow_type
        self._callback = on_press
        self.size_hint = (None, 1)
        self.width = width

        if not StudioPaginationPad._textures_loaded:
            def _load(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            StudioPaginationPad._up_dark = _load(pagination_assets.KEY_UP_DARK_B64)
            StudioPaginationPad._down_dark = _load(pagination_assets.KEY_DOWN_DARK_B64)
            StudioPaginationPad._up_light = _load(pagination_assets.KEY_UP_LIGHT_B64)
            StudioPaginationPad._down_light = _load(pagination_assets.KEY_DOWN_LIGHT_B64)

            for name, b64_str in pagination_assets.ARROWS_PNG_BASE64.items():
                StudioPaginationPad._arrow_textures[name] = _load(b64_str)

            StudioPaginationPad._textures_loaded = True

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            enabled_state=self._redraw,
            is_pressed=self._redraw,
            accent_color=self._redraw,
        )

    def set_enabled(self, enabled):
        self.enabled_state = bool(enabled)

    def on_press(self):
        if not self.enabled_state:
            return
        Clock.unschedule(self._reset_press)
        self.is_pressed = True

    def on_release(self):
        if not self.enabled_state:
            self.is_pressed = False
            return
        Clock.schedule_once(self._reset_press, 0.14)
        if self._callback:
            self._callback()

    def _reset_press(self, dt):
        self.is_pressed = False

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        is_light = settings_manager.theme == "light"
        pressed = self.is_pressed and self.enabled_state
        meta = pagination_assets.DOWN_META if pressed else pagination_assets.UP_META

        if is_light:
            key_tex = self._down_light if pressed else self._up_light
        else:
            key_tex = self._down_dark if pressed else self._up_dark

        kx = round(self.x)
        ky = round(self.y)
        kw = round(self.width)
        kh = round(self.height)

        r, g, b, _ = self.accent_color
        key_alpha = 1.0 if self.enabled_state else 0.55

        with self.canvas:
            # 1. Корпус металлической клавиши
            Color(1, 1, 1, key_alpha)
            Rectangle(texture=key_tex, pos=(kx, ky), size=(kw, kh))

            # 2. Неоновый световод по периметру (загорается только при нажатии)
            rx_n, ry_n, rw_n, rh_n = meta["rim_box_norm"]
            rim_x = kx + rx_n * kw
            rim_y = ky + ry_n * kh
            rim_w = rw_n * kw
            rim_h = rh_n * kh
            rim_r = meta["rim_radius_norm"] * kh

            if pressed:
                Color(r, g, b, 0.32)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(2.4))
                Color(min(1.0, r + 0.18), min(1.0, g + 0.18), min(1.0, b + 0.18), 0.96)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.2))
            else:
                Color(r, g, b, 0.20 if is_light else 0.15)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(0.9))

            # 3. Стрелка внутри пэда
            ico_tex = self._arrow_textures.get(self.arrow_type)
            if ico_tex is not None:
                icx = kx + kw * 0.5
                icy = ky + meta["center_y_norm"] * kh
                ico_s = round(min(kw, kh) * 0.50)

                if pressed:
                    Color(r, g, b, 0.30)
                    gs = round(ico_s * 1.15)
                    Rectangle(
                        texture=ico_tex,
                        pos=(round(icx - gs * 0.5), round(icy - gs * 0.5)),
                        size=(gs, gs),
                    )
                    Color(min(1.0, r + 0.22), min(1.0, g + 0.22), min(1.0, b + 0.22), 0.98)
                else:
                    if not self.enabled_state:
                        Color(0.45, 0.48, 0.50, 0.32)
                    elif is_light:
                        Color(0.20, 0.24, 0.22, 0.88)
                    else:
                        Color(0.84, 0.87, 0.90, 0.82)

                Rectangle(
                    texture=ico_tex,
                    pos=(round(icx - ico_s * 0.5), round(icy - ico_s * 0.5)),
                    size=(ico_s, ico_s),
                )


class StudioMixerPageDisplay(FloatLayout):
    """LED-дисплей микшера со светящимся номером страницы."""

    text = StringProperty("1")
    flash_alpha = NumericProperty(0.0)
    led_color = ListProperty([0.18, 0.95, 0.38, 1.0])

    _disp_dark = None
    _disp_light = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(58)

        if StudioMixerPageDisplay._disp_dark is None:
            StudioMixerPageDisplay._disp_dark = CoreImage(
                io.BytesIO(base64.b64decode(pagination_assets.DISP_DARK_B64)), ext="png"
            ).texture
            StudioMixerPageDisplay._disp_light = CoreImage(
                io.BytesIO(base64.b64decode(pagination_assets.DISP_LIGHT_B64)), ext="png"
            ).texture

        # Мягкий задний слой свечения цифр (halo)
        self.glow_label = Label(
            text=self.text,
            font_size=sp(17),
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        # Основная яркая цифра LED-дисплея
        self.main_label = Label(
            text=self.text,
            font_size=sp(16),
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        self.add_widget(self.glow_label)
        self.add_widget(self.main_label)

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            text=self._on_text_changed,
            flash_alpha=self._redraw,
            led_color=self._apply_led_colors,
        )
        self._apply_led_colors()

    def _on_text_changed(self, inst, val):
        self.glow_label.text = str(val)
        self.main_label.text = str(val)

    def pulse(self):
        """Короткий световой импульс дисплея при переключении страницы."""
        Animation.cancel_all(self, "flash_alpha")
        self.flash_alpha = 1.0
        Animation(flash_alpha=0.0, duration=0.26, t="out_cubic").start(self)

    def _apply_led_colors(self, *args):
        r, g, b, _ = self.led_color
        self.glow_label.color = [r, g, b, 0.42]
        self.main_label.color = [
            min(1.0, r + 0.28),
            min(1.0, g + 0.28),
            min(1.0, b + 0.28),
            1.0,
        ]
        self._redraw()

    def _redraw(self, *args):
        self.canvas.before.clear()
        if self.width <= 4 or self.height <= 4:
            return

        is_light = settings_manager.theme == "light"
        disp_tex = self._disp_light if is_light else self._disp_dark
        r, g, b, _ = self.led_color
        fa = float(self.flash_alpha)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(texture=disp_tex, pos=self.pos, size=self.size)

            # Подсветка подложки дисплея в тон темы
            gx_n, gy_n, gw_n, gh_n = pagination_assets.DISP_META["glass_box_norm"]
            gx = self.x + gx_n * self.width
            gy = self.y + gy_n * self.height
            gw = gw_n * self.width
            gh = gh_n * self.height
            gr = pagination_assets.DISP_META["glass_radius_norm"] * self.height

            Color(r, g, b, 0.10 + 0.18 * fa)
            Rectangle(pos=(gx, gy), size=(gw, gh))

            Color(r, g, b, 0.45 + 0.50 * fa)
            Line(rounded_rectangle=(gx, gy, gw, gh, gr), width=dp(1.1))


class StudioPaginationBar(MDBoxLayout):
    """Студийная мини-консоль пагинации в стиле кнопок и дисплея микшера."""

    _panel_dark = None
    _panel_light = None

    def __init__(self, on_page_select=None, **kwargs):
        super().__init__(**kwargs)
        self.on_page_select = on_page_select
        self.current_page_index = 0
        self.total_pages = 1
        self._last_total = None
        self._last_per_page = None

        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.height = dp(40)
        self.padding = [dp(14), dp(4), dp(14), dp(4)]
        self.spacing = dp(3)
        self.md_bg_color = [0, 0, 0, 0]

        if StudioPaginationBar._panel_dark is None:
            StudioPaginationBar._panel_dark = CoreImage(
                io.BytesIO(base64.b64decode(pagination_assets.PANEL_DARK_B64)), ext="png"
            ).texture
            StudioPaginationBar._panel_light = CoreImage(
                io.BytesIO(base64.b64decode(pagination_assets.PANEL_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._panel_dark,
                pos=self.pos,
                size=self.size,
            )
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.jump_back_arrow = StudioPaginationPad(
            arrow_type="first", on_press=self._go_back_10, width=dp(36)
        )
        self.prev_arrow = StudioPaginationPad(
            arrow_type="prev", on_press=self._go_prev_page, width=dp(36)
        )
        self.page_display = StudioMixerPageDisplay()
        self.next_arrow = StudioPaginationPad(
            arrow_type="next", on_press=self._go_next_page, width=dp(36)
        )
        self.jump_forward_arrow = StudioPaginationPad(
            arrow_type="last", on_press=self._go_forward_10, width=dp(36)
        )

        self.add_widget(self.jump_back_arrow)
        self.add_widget(self.prev_arrow)
        self.add_widget(self.page_display)
        self.add_widget(self.next_arrow)
        self.add_widget(self.jump_forward_arrow)

        self._update_width()
        self.update_theme_colors()

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def on_touch_down(self, touch):
        if self.parent is not None and self.parent.height < dp(10):
            return False
        return super().on_touch_down(touch)

    def _update_width(self):
        self.width = (
            self.padding[0]
            + self.padding[2]
            + self.jump_back_arrow.width
            + self.prev_arrow.width
            + self.page_display.width
            + self.next_arrow.width
            + self.jump_forward_arrow.width
            + self.spacing * 4
        )

    def set_total(self, total_items, per_page, current_page=0, on_click=None):
        if on_click:
            self.on_page_select = on_click
        new_total_pages = max(1, (total_items + per_page - 1) // per_page)
        if (
            self._last_total == total_items
            and self._last_per_page == per_page
            and self.total_pages == new_total_pages
        ):
            self.set_current_page(current_page)
            return
        self._last_total = total_items
        self._last_per_page = per_page
        self.total_pages = new_total_pages
        self.current_page_index = max(0, min(current_page, self.total_pages - 1))
        self._apply_page(animate=False)
        self.update_theme_colors()

    def set_current_page(self, page):
        new_page = max(0, min(page, self.total_pages - 1))
        changed = new_page != self.current_page_index
        self.current_page_index = new_page
        self._apply_page(animate=changed)

    def _apply_page(self, animate=False):
        self.page_display.text = str(self.current_page_index + 1)
        digits = len(str(self.total_pages))
        self.page_display.width = dp(54) if digits <= 2 else dp(66)
        if animate:
            self.page_display.pulse()
        at_first = self.current_page_index == 0
        at_last = self.current_page_index >= self.total_pages - 1
        self.jump_back_arrow.set_enabled(not at_first)
        self.prev_arrow.set_enabled(not at_first)
        self.next_arrow.set_enabled(not at_last)
        self.jump_forward_arrow.set_enabled(not at_last)
        self._update_width()

    def _go_back_10(self):
        if self.current_page_index <= 0:
            return
        new_index = max(0, self.current_page_index - 10)
        self.current_page_index = new_index
        self._apply_page(animate=True)
        if self.on_page_select:
            self.on_page_select(new_index)

    def _go_prev_page(self):
        if self.current_page_index <= 0:
            return
        new_index = self.current_page_index - 1
        self.current_page_index = new_index
        self._apply_page(animate=True)
        if self.on_page_select:
            self.on_page_select(new_index)

    def _go_next_page(self):
        if self.current_page_index >= self.total_pages - 1:
            return
        new_index = self.current_page_index + 1
        self.current_page_index = new_index
        self._apply_page(animate=True)
        if self.on_page_select:
            self.on_page_select(new_index)

    def _go_forward_10(self):
        if self.current_page_index >= self.total_pages - 1:
            return
        new_index = min(self.total_pages - 1, self.current_page_index + 10)
        self.current_page_index = new_index
        self._apply_page(animate=True)
        if self.on_page_select:
            self.on_page_select(new_index)

    @staticmethod
    def _get_theme_glow(theme_id):
        if theme_id == "light":
            return [0.12, 0.85, 0.45, 1.0]  # На тёмном стекле LED-дисплея ярко-изумрудный
        elif theme_id == "dark":
            return [1.0, 0.52, 0.04, 1.0]
        return [0.18, 0.95, 0.38, 1.0]

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        is_light = theme_id == "light"
        glow = self._get_theme_glow(theme_id)
        self._bg_rect.texture = self._panel_light if is_light else self._panel_dark
        self.page_display.led_color = glow
        for pad in (
            self.jump_back_arrow,
            self.prev_arrow,
            self.next_arrow,
            self.jump_forward_arrow,
        ):
            pad.accent_color = glow