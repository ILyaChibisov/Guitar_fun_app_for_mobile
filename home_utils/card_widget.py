# home_utils/card_widget.py
import base64
import io

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from config.logger_config import screen_logger
from data.home import home_assets
from state.settings_state import settings_state as settings_manager

logger = screen_logger("HomeCard")

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

    def load_asset_as_bytes(name):
        return None


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


class StudioHomeGridCard(ButtonBehavior, FloatLayout):
    """
    Карточка раздела в студийной рэковой рамке с боковыми винтами,
    родной цветной заливкой и оригинальными PNG-иконками из ассетов.
    """

    GREEN_SECTION_COLORS = {
        "songs": "#E53935",
        "chords": "#43A047",
        "tuner": "#1E88E5",
        "metronome": "#FB8C00",
        "dictionary": "#8E24AA",
        "favorites": "#EC407A",
    }

    LIGHT_SECTION_COLORS = {
        "songs": "#EF9A9A",
        "chords": "#A5D6A7",
        "tuner": "#90CAF9",
        "metronome": "#FFCC80",
        "dictionary": "#CE93D8",
        "favorites": "#F48FB1",
    }

    DARK_SECTION_COLORS = {
        "songs": "#B71C1C",
        "chords": "#1B5E20",
        "tuner": "#0D47A1",
        "metronome": "#E65100",
        "dictionary": "#4A148C",
        "favorites": "#880E4F",
    }

    card_scale = NumericProperty(1.0)
    press_glow = NumericProperty(0.0)
    base_color = ListProperty([0.2, 0.4, 0.3, 1.0])
    glow_color = ListProperty([0.3, 0.9, 0.5, 1.0])

    _textures_loaded = False
    _frame_dark = None
    _frame_light = None

    def __init__(self, section_id, title, icon_asset, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.section_id = section_id
        self.title_text = title
        self.icon_asset = icon_asset
        self.on_click_callback = on_click
        self._current_theme = settings_manager.theme

        self.size_hint = (1, 1)

        if not StudioHomeGridCard._textures_loaded:
            def _load(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            StudioHomeGridCard._frame_dark = _load(home_assets.FRAME_DARK_B64)
            StudioHomeGridCard._frame_light = _load(home_assets.FRAME_LIGHT_B64)
            StudioHomeGridCard._textures_loaded = True

        # Внутренний контейнер с отступами под боковые уши с винтами
        content = MDBoxLayout(
            orientation="vertical",
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
            padding=[dp(14), dp(12), dp(14), dp(12)],
            spacing=0,
            md_bg_color=[0, 0, 0, 0],
        )

        content.add_widget(Widget(size_hint_y=0.35))

        self.icon_image = Image(
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            pos_hint={"center_x": 0.5},
            fit_mode="contain",
            mipmap=True,
        )
        content.add_widget(self.icon_image)

        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        font_size = sp(13) if len(title) > 8 else (sp(14) if len(title) > 6 else sp(15))
        self.title_label = MDLabel(
            text=title,
            font_size=font_size,
            halign="center",
            valign="middle",
            bold=True,
            size_hint=(1, None),
            height=dp(24),
            theme_text_color="Custom",
            shorten=True,
            shorten_from="right",
        )
        content.add_widget(self.title_label)

        content.add_widget(Widget(size_hint_y=0.6))

        self.add_widget(content)

        self._load_icon()
        self._setup_colors()

        self.bind(
            pos=self._redraw,
            size=self._redraw,
            card_scale=self._redraw,
            press_glow=self._redraw,
            base_color=self._redraw,
            glow_color=self._redraw,
        )

    def _load_icon(self):
        if HAS_ASSETS and self.icon_asset:
            try:
                icon_data = load_asset_as_bytes(self.icon_asset)
                if icon_data:
                    img = CoreImage(io.BytesIO(icon_data), ext="png")
                    self.icon_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {self.icon_asset}: {e}")
        self.icon_image.opacity = 0

    def _setup_colors(self):
        theme_id = self._current_theme
        rich_hex = self.GREEN_SECTION_COLORS.get(self.section_id, "#546E7A")
        rich_rgb = _hex_to_rgb(rich_hex)

        if theme_id == "dark":
            hex_col = self.DARK_SECTION_COLORS.get(self.section_id, "#424242")
            rgb = _hex_to_rgb(hex_col)
            self.base_color = rgb + [1.0]
            self.glow_color = [min(1.0, c * 1.45 + 0.18) for c in rich_rgb] + [1.0]
            self.title_label.text_color = [1, 1, 1, 1]
            self.icon_color = [1, 1, 1, 1]
        elif theme_id == "light":
            hex_col = self.LIGHT_SECTION_COLORS.get(self.section_id, "#E0E0E0")
            rgb = _hex_to_rgb(hex_col)
            self.base_color = rgb + [1.0]
            self.glow_color = [max(0.0, c * 0.85) for c in rich_rgb] + [1.0]
            self.title_label.text_color = [0.15, 0.15, 0.15, 1]
            self.icon_color = [
                min(1.0, rich_rgb[0] * 0.7 + 0.3),
                min(1.0, rich_rgb[1] * 0.7 + 0.3),
                min(1.0, rich_rgb[2] * 0.7 + 0.3),
                1.0,
            ]
        else:  # green
            rgb = rich_rgb
            self.base_color = rgb + [1.0]
            self.glow_color = [min(1.0, c + 0.25) for c in rgb] + [1.0]
            self.title_label.text_color = [1, 1, 1, 1]
            self.icon_color = [1, 1, 1, 1]

        if hasattr(self, "icon_image") and self.icon_image:
            self.icon_image.color = self.icon_color

        self._redraw()

    def update_theme(self, theme_id):
        self._current_theme = theme_id
        self._setup_colors()

    def update_language(self, new_title):
        self.title_text = new_title
        self.title_label.text = new_title
        font_size = sp(13) if len(new_title) > 8 else (sp(14) if len(new_title) > 6 else sp(15))
        self.title_label.font_size = font_size

    def on_press(self):
        Animation.cancel_all(self, "card_scale", "press_glow")
        Animation(card_scale=0.965, press_glow=1.0, duration=0.07, t="out_quad").start(self)

    def on_release(self):
        Animation.cancel_all(self, "card_scale", "press_glow")
        (
            Animation(card_scale=1.015, press_glow=1.0, duration=0.09, t="out_quad")
            + Animation(card_scale=1.0, press_glow=0.0, duration=0.22, t="out_cubic")
        ).start(self)

        if self.on_click_callback:
            Clock.schedule_once(self._navigate, 0.11)

    def _navigate(self, dt):
        if self.on_click_callback:
            self.on_click_callback(self.section_id)

    def _redraw(self, *args):
        self.canvas.before.clear()
        self.canvas.after.clear()
        if self.width <= 4 or self.height <= 4:
            return

        is_light = self._current_theme == "light"
        frame_tex = self._frame_light if is_light else self._frame_dark

        cx, cy = self.center
        sc = float(self.card_scale)
        w = self.width * sc
        h = self.height * sc
        x = cx - w * 0.5
        y = cy - h * 0.5

        meta = home_assets.FRAME_META
        bx_n, by_n, bw_n, bh_n = meta["bay_box_norm"]
        bay_x = x + bx_n * w
        bay_y = y + by_n * h
        bay_w = bw_n * w
        bay_h = bh_n * h
        bay_r = meta["bay_radius_norm"] * h

        br, bg, bb, _ = self.base_color
        gr, gg, gb, _ = self.glow_color
        pg = float(self.press_glow)

        with self.canvas.before:
            # 1. Фирменная цветная заливка раздела строго внутри утопленной ниши
            # Убираем отступы dp(1) и делаем заливку чуть больше, чтобы она гарантированно уходила под рамку
            Color(br, bg, bb, 1.0)
            RoundedRectangle(
                pos=(bay_x, bay_y),
                size=(bay_w, bay_h),
                radius=[bay_r],
            )

            # Дополнительная световая вспышка заливки при нажатии
            if pg > 0.01:
                Color(gr, gg, gb, 0.34 * pg)
                RoundedRectangle(
                    pos=(bay_x, bay_y),
                    size=(bay_w, bay_h),
                    radius=[bay_r],
                )

            # 2. Металлическая рамка-консоль с фасками и внутренней тенью ниши
            # (рисуется поверх заливки, перекрывая возможные неровности краев)
            Color(1, 1, 1, 1)
            Rectangle(texture=frame_tex, pos=(x, y), size=(w, h))

        with self.canvas.after:
            # Неоновый световод по периметру ниши при нажатии
            if pg > 0.01:
                Color(gr, gg, gb, 0.36 * pg)
                Line(rounded_rectangle=(bay_x, bay_y, bay_w, bay_h, bay_r), width=dp(2.6))
                Color(min(1.0, gr + 0.2), min(1.0, gg + 0.2), min(1.0, gb + 0.2), 0.96 * pg)
                Line(rounded_rectangle=(bay_x, bay_y, bay_w, bay_h, bay_r), width=dp(1.3))
