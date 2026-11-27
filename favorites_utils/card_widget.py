# favorites_utils/card_widget.py
import base64
import io

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, PushMatrix, PopMatrix, Rectangle, Rotate, Scale
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from data.favorites import card_assets, pagination_assets
from state.settings_state import settings_state as settings_manager


class MetallicGuitarSongIcon(Widget):
    """Металлизированная иконка акустической гитары с нотками и подсветкой при нажатии."""

    glow_alpha = NumericProperty(0.0)
    icon_scale = NumericProperty(1.0)
    icon_angle = NumericProperty(0.0)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    _textures_loaded = False
    _dark_tex = None
    _light_tex = None
    _mask_tex = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(40)

        if not MetallicGuitarSongIcon._textures_loaded:
            def _load(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            MetallicGuitarSongIcon._dark_tex = _load(card_assets.GUITAR_DARK_B64)
            MetallicGuitarSongIcon._light_tex = _load(card_assets.GUITAR_LIGHT_B64)
            MetallicGuitarSongIcon._mask_tex = _load(card_assets.GUITAR_MASK_B64)
            MetallicGuitarSongIcon._textures_loaded = True

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            glow_alpha=self._redraw,
            icon_scale=self._redraw,
            icon_angle=self._redraw,
            accent_color=self._redraw,
        )

    def _redraw(self, *args):
        self.canvas.clear()
        if self.width <= 2 or self.height <= 2:
            return

        is_light = settings_manager.theme == "light"
        metal_tex = self._light_tex if is_light else self._dark_tex
        mask_tex = self._mask_tex
        if metal_tex is None or mask_tex is None:
            return

        icx, icy = self.center
        ico_s = round(min(self.width, self.height) * 0.78)
        r, g, b, _ = self.accent_color
        ga = float(self.glow_alpha)

        with self.canvas:
            PushMatrix()
            Rotate(angle=float(self.icon_angle), origin=(icx, icy))
            Scale(x=float(self.icon_scale), y=float(self.icon_scale), origin=(icx, icy))

            # Тень-гравировка в нише
            Color(0, 0, 0, 0.26 if is_light else 0.65)
            Rectangle(
                texture=mask_tex,
                pos=(round(icx - ico_s * 0.5), round(icy - ico_s * 0.5 - dp(1.2))),
                size=(ico_s, ico_s),
            )

            # Неоновый ореол при нажатии
            if ga > 0.01:
                halo_s = round(ico_s * 1.14)
                Color(r, g, b, 0.45 * ga)
                Rectangle(
                    texture=mask_tex,
                    pos=(round(icx - halo_s * 0.5), round(icy - halo_s * 0.5)),
                    size=(halo_s, halo_s),
                )

            # Шлифованная металлическая гитарка с нотами
            Color(1, 1, 1, 1)
            Rectangle(
                texture=metal_tex,
                pos=(round(icx - ico_s * 0.5), round(icy - ico_s * 0.5)),
                size=(ico_s, ico_s),
            )

            # Световая тонировка при нажатии
            if ga > 0.01:
                Color(r, g, b, 0.55 * ga)
                Rectangle(
                    texture=mask_tex,
                    pos=(round(icx - ico_s * 0.5), round(icy - ico_s * 0.5)),
                    size=(ico_s, ico_s),
                )

            PopMatrix()


class TabsCountLedBox(FloatLayout):
    """Мини-квадратик LED-дисплея микшера с количеством подборов (в стиле номера страницы пагинации)."""

    text = StringProperty("")
    led_color = ListProperty([0.18, 0.95, 0.38, 1.0])

    _disp_dark = None
    _disp_light = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(30), dp(30))
        self.pos_hint = {"center_y": 0.5}

        if TabsCountLedBox._disp_dark is None:
            TabsCountLedBox._disp_dark = CoreImage(
                io.BytesIO(base64.b64decode(pagination_assets.DISP_DARK_B64)), ext="png"
            ).texture
            TabsCountLedBox._disp_light = CoreImage(
                io.BytesIO(base64.b64decode(pagination_assets.DISP_LIGHT_B64)), ext="png"
            ).texture

        self.glow_label = Label(
            text="",
            font_size=sp(14),
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        self.main_label = Label(
            text="",
            font_size=sp(13),
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
            opacity=self._redraw,
            led_color=self._apply_led_colors,
        )

        self._apply_led_colors()

    def _on_text_changed(self, inst, val):
        val_str = str(val) if val else ""
        self.glow_label.text = val_str
        self.main_label.text = val_str
        self.opacity = 1.0 if val_str else 0.0

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
        if self.width <= 4 or self.height <= 4 or self.opacity < 0.05:
            return

        is_light = settings_manager.theme == "light"
        disp_tex = self._disp_light if is_light else self._disp_dark
        r, g, b, _ = self.led_color

        with self.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(texture=disp_tex, pos=self.pos, size=self.size)

            gx_n, gy_n, gw_n, gh_n = pagination_assets.DISP_META["glass_box_norm"]
            gx = self.x + gx_n * self.width
            gy = self.y + gy_n * self.height
            gw = gw_n * self.width
            gh = gh_n * self.height
            gr = pagination_assets.DISP_META["glass_radius_norm"] * self.height

            Color(r, g, b, 0.12)
            Rectangle(pos=(gx, gy), size=(gw, gh))

            Color(r, g, b, 0.55)
            Line(rounded_rectangle=(gx, gy, gw, gh, gr), width=dp(1.0))


class StudioFavoriteSongCard(FloatLayout):
    """Студийная рэковая карточка песни с винтами, LED-счётчиком подборов и анимацией нажатия."""

    CARD_HEIGHT = dp(58)
    TAP_THRESHOLD = dp(15)
    LONG_PRESS_TIME = 0.5
    LONG_PRESS_MOVE_TOLERANCE = dp(10)

    press_glow = NumericProperty(0.0)
    card_scale = NumericProperty(1.0)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    _panel_dark_tex = None
    _panel_light_tex = None
    _panel_green_tex = None

    def __init__(self, song_id=0, artist="", title="", tabs_count=0, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.song_id = song_id
        self.artist = artist
        self.title = title
        self.tabs_count = tabs_count
        self.on_click_callback = on_click

        self._touch_down_pos = None
        self._long_press_event = None
        self._long_press_triggered = False

        self.size_hint_y = None
        self.height = self.CARD_HEIGHT

        if StudioFavoriteSongCard._panel_dark_tex is None:
            StudioFavoriteSongCard._panel_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(card_assets.CARD_DARK_B64)), ext="png"
            ).texture
            StudioFavoriteSongCard._panel_green_tex = CoreImage(
                io.BytesIO(base64.b64decode(card_assets.CARD_GREEN_B64)), ext="png"
            ).texture
            StudioFavoriteSongCard._panel_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(card_assets.CARD_LIGHT_B64)), ext="png"
            ).texture

        # Отступы по бокам увеличены с учётом толстых рамок с винтами
        content = MDBoxLayout(
            orientation="horizontal",
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
            padding=[dp(22), dp(4), dp(22), dp(4)],
            spacing=dp(6),
            md_bg_color=[0, 0, 0, 0],
        )

        self.icon = MetallicGuitarSongIcon()

        text_layout = MDBoxLayout(
            orientation="vertical",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(42),
            spacing=dp(2),
            pos_hint={"center_y": 0.5},
            padding=[0, 0, 0, 0],
        )

        self.artist_label = MDLabel(
            font_size=sp(15),
            size_hint_y=None,
            height=dp(22),
            theme_text_color="Custom",
            bold=True,
            valign="middle",
            halign="center",
            shorten=True,
            shorten_from="right",
        )
        self.title_label = MDLabel(
            font_size=sp(12),
            size_hint_y=None,
            height=dp(18),
            theme_text_color="Custom",
            valign="middle",
            halign="center",
            shorten=True,
            shorten_from="right",
        )

        self.artist_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, inst.height)))
        self.title_label.bind(width=lambda inst, val: setattr(inst, "text_size", (val, inst.height)))

        text_layout.add_widget(self.artist_label)
        text_layout.add_widget(self.title_label)

        # Квадратик LED-дисплея с количеством подборов (как в пагинации)
        self.count_box = TabsCountLedBox()
        self.arrow = MDLabel(
            text="›",
            font_size=sp(22),
            size_hint_x=None,
            width=dp(18),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
        )

        content.add_widget(self.icon)
        content.add_widget(text_layout)
        content.add_widget(self.count_box)
        content.add_widget(self.arrow)
        self.add_widget(content)

        self.artist_label.text = artist
        self.title_label.text = title
        self.count_box.text = str(tabs_count) if tabs_count else "1"


        self.bind(
            pos=self._redraw_frame,
            size=self._redraw_frame,
            press_glow=self._redraw_frame,
            card_scale=self._redraw_frame,
            accent_color=self._redraw_frame,
        )

        self.update_theme_colors()

    @staticmethod
    def _get_theme_palette(theme_id):
        """Палитра цветов в точности как в LED-дисплее пагинации."""
        if theme_id == "light":
            return {
                "accent": [0.06, 0.56, 0.28, 1.0],
                "led": [0.12, 0.85, 0.45, 1.0],
                "artist": [0.06, 0.54, 0.28, 1.0],     # Зелёный для светлой темы
                "secondary": [0.22, 0.28, 0.25, 1.0],
            }
        elif theme_id == "dark":
            return {
                "accent": [1.0, 0.52, 0.04, 1.0],
                "led": [1.0, 0.52, 0.04, 1.0],
                "artist": [1.0, 0.62, 0.14, 1.0],      # Оранжевый для тёмной темы (как в пагинации)
                "secondary": [0.80, 0.83, 0.86, 0.88],
            }
        return {
            "accent": [0.18, 0.95, 0.38, 1.0],
            "led": [0.18, 0.95, 0.38, 1.0],
            "artist": [1.0, 1.0, 1.0, 1.0],
            "secondary": [0.84, 0.92, 0.88, 0.88],
        }

    def update_data(self, song_id, artist, title, tabs_count=1, on_click=None):
        self.song_id = song_id
        self.artist = artist
        self.title = title
        self.tabs_count = tabs_count
        self.on_click_callback = on_click
        self.artist_label.text = artist
        self.title_label.text = title
        self.count_box.text = str(tabs_count) if tabs_count and tabs_count > 1 else ""

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        pal = self._get_theme_palette(theme_id)
        self.accent_color = pal["accent"]
        self.icon.accent_color = pal["accent"]
        self.count_box.led_color = pal["led"]
        self.artist_label.text_color = pal["artist"]
        self.title_label.text_color = pal["secondary"]
        self.arrow.text_color = pal["accent"]
        self._redraw_frame()

    def _redraw_frame(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()
        if self.width <= 4 or self.height <= 4:
            return

        theme_id = settings_manager.theme
        is_light = theme_id == "light"

        if is_light:
            panel_tex = self._panel_light_tex
        elif theme_id == "green":
            panel_tex = self._panel_green_tex
        else:
            panel_tex = self._panel_dark_tex

        cx, cy = self.center
        sc = float(self.card_scale)
        w = self.width * sc
        h = self.height * sc
        x = cx - w * 0.5
        y = cy - h * 0.5

        r, g, b, _ = self.accent_color
        pg = float(self.press_glow)

        meta = card_assets.CARD_META
        rx_n, ry_n, rw_n, rh_n = meta["rim_box_norm"]
        rim_x = x + rx_n * w
        rim_y = y + ry_n * h
        rim_w = rw_n * w
        rim_h = rh_n * h
        rim_r = meta["rim_radius_norm"] * h

        with self.canvas.before:
            Color(1, 1, 1, 1)
            Rectangle(texture=panel_tex, pos=(x, y), size=(w, h))

            if pg > 0.01:
                Color(r, g, b, 0.14 * pg)
                Rectangle(pos=(rim_x, rim_y), size=(rim_w, rim_h))

        with self.canvas.after:
            if pg > 0.01:
                Color(r, g, b, 0.35 * pg)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(2.4))
                Color(min(1.0, r + 0.18), min(1.0, g + 0.18), min(1.0, b + 0.18), 0.95 * pg)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.2))
            else:
                Color(r, g, b, 0.24 if is_light else 0.18)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.0))

    # --- Анимация нажатия и обработка кликов ---
    def _animate_press_down(self):
        Animation.cancel_all(self, "press_glow", "card_scale")
        Animation.cancel_all(self.icon, "glow_alpha", "icon_scale", "icon_angle")
        Animation(press_glow=1.0, card_scale=0.975, duration=0.08, t="out_quad").start(self)
        Animation(glow_alpha=1.0, icon_scale=0.90, icon_angle=-6.0, duration=0.08, t="out_quad").start(
            self.icon
        )

    def _animate_press_release(self, trigger_callback=False):
        Animation.cancel_all(self, "press_glow", "card_scale")
        Animation.cancel_all(self.icon, "glow_alpha", "icon_scale", "icon_angle")

        card_anim = Animation(press_glow=1.0, card_scale=1.01, duration=0.08, t="out_quad") + Animation(
            press_glow=0.0, card_scale=1.0, duration=0.22, t="out_cubic"
        )
        icon_anim = Animation(
            glow_alpha=1.0, icon_scale=1.16, icon_angle=7.0, duration=0.09, t="out_quad"
        ) + Animation(glow_alpha=0.0, icon_scale=1.0, icon_angle=0.0, duration=0.24, t="out_back")

        card_anim.start(self)
        icon_anim.start(self.icon)

        if trigger_callback and self.on_click_callback:
            Clock.schedule_once(
                lambda dt: self.on_click_callback(self.song_id, self.title, self.artist),
                0.11,
            )

    def on_touch_down(self, touch):
        if getattr(self, "disabled", False) or self.opacity < 0.1:
            return False
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        self._touch_down_pos = touch.pos
        self._long_press_triggered = False
        self._long_press_event = Clock.schedule_once(
            self._trigger_long_press, self.LONG_PRESS_TIME
        )
        self._animate_press_down()
        touch.grab(self)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        if getattr(self, "disabled", False) or self.opacity < 0.1:
            return False
        if self._touch_down_pos is None:
            return False

        dx = touch.x - self._touch_down_pos[0]
        dy = touch.y - self._touch_down_pos[1]
        if (
            abs(dx) > self.LONG_PRESS_MOVE_TOLERANCE
            or abs(dy) > self.LONG_PRESS_MOVE_TOLERANCE
        ):
            self._cancel_long_press()
            self._animate_press_release(trigger_callback=False)
            touch.ungrab(self)
            return False
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        if getattr(self, "disabled", False) or self.opacity < 0.1:
            return False
        if self._touch_down_pos is None:
            return False

        self._cancel_long_press()

        dx = touch.x - self._touch_down_pos[0]
        dy = touch.y - self._touch_down_pos[1]
        was_long = self._long_press_triggered
        self._touch_down_pos = None
        self._long_press_triggered = False

        if was_long:
            self._animate_press_release(trigger_callback=False)
            return True

        is_tap = abs(dx) < self.TAP_THRESHOLD and abs(dy) < self.TAP_THRESHOLD
        self._animate_press_release(trigger_callback=is_tap)
        return True

    def _trigger_long_press(self, dt):
        self._long_press_event = None
        if self._touch_down_pos is None:
            return
        self._long_press_triggered = True
        self._animate_press_release(trigger_callback=True)

    def _cancel_long_press(self):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None