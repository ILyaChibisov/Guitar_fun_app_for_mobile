# chord_utils/menu_widget.py
import base64
import io

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.core.text import Label as CoreLabel
from kivy.uix.textinput import TextInput
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from utils.localization import get_text


from state.settings_state import settings_state as settings_manager

try:
    from data.chords import menu_assets
except ImportError:
    from chord_utils.menu_generator import save_chords_menu_assets
    save_chords_menu_assets()
    from data.chords import menu_assets


class ChordHardwareButton(ButtonBehavior, Widget):
    """Студийный триггер-пэд меню аккордов в едином стиле с консолью тюнера."""

    icon_type = StringProperty("tonality")
    is_active = BooleanProperty(True)
    is_pressed = BooleanProperty(False)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    _textures_loaded = False
    _well_dark = None
    _up_dark = None
    _down_dark = None
    _well_light = None
    _up_light = None
    _down_light = None
    _icon_textures = {}

    def __init__(self, icon_type="tonality", on_press=None, is_active=True, **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        self.is_active = is_active
        self._callback = on_press
        self.size_hint = (1, 1)

        if not ChordHardwareButton._textures_loaded:
            def _load_b64(b64_str):
                return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

            ChordHardwareButton._well_dark = _load_b64(menu_assets.WELL_DARK_B64)
            ChordHardwareButton._up_dark = _load_b64(menu_assets.KEY_UP_DARK_B64)
            ChordHardwareButton._down_dark = _load_b64(menu_assets.KEY_DOWN_DARK_B64)

            ChordHardwareButton._well_light = _load_b64(menu_assets.WELL_LIGHT_B64)
            ChordHardwareButton._up_light = _load_b64(menu_assets.KEY_UP_LIGHT_B64)
            ChordHardwareButton._down_light = _load_b64(menu_assets.KEY_DOWN_LIGHT_B64)

            for name, b64_str in menu_assets.ICONS_PNG_BASE64.items():
                ChordHardwareButton._icon_textures[name] = _load_b64(b64_str)

            ChordHardwareButton._textures_loaded = True

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            icon_type=self.update_canvas,
            is_active=self.update_canvas,
            is_pressed=self.update_canvas,
            accent_color=self.update_canvas,
        )
        self.update_theme_colors()

    @staticmethod
    def _get_theme_glow(theme_id):
        if theme_id == "light":
            return [0.08, 0.58, 0.30, 1.0]
        elif theme_id == "dark":
            return [1.0, 0.50, 0.0, 1.0]
        return [0.18, 0.88, 0.28, 1.0]

    def update_theme_colors(self):
        self.accent_color = self._get_theme_glow(settings_manager.theme)
        self.update_canvas()

    def on_press(self):
        Clock.unschedule(self._reset_press_state)
        self.is_pressed = True

    def on_release(self):
        Clock.schedule_once(self._reset_press_state, 0.14)
        if self._callback and self.is_active:
            self._callback()

    def _reset_press_state(self, dt):
        self.is_pressed = False

    def set_icon(self, icon_type):
        self.icon_type = icon_type

    def set_color(self, color):
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        btn_w = round(self.width)
        btn_h = round(self.height)
        bx = round(self.x)
        by = round(self.y)

        is_light = settings_manager.theme == "light"
        pressed = self.is_pressed
        meta = menu_assets.DOWN_META if pressed else menu_assets.UP_META

        well_tex = self._well_light if is_light else self._well_dark
        key_tex = (self._down_light if pressed else self._up_light) if is_light else (self._down_dark if pressed else self._up_dark)

        c = list(self.accent_color)
        r, g, b = float(c[0]), float(c[1]), float(c[2])

        with self.canvas:
            # 1. Шахта пэда
            Color(1, 1, 1, 1)
            Rectangle(texture=well_tex, pos=(bx, by), size=(btn_w, btn_h))

            # 2. Клавиша пэда
            Rectangle(texture=key_tex, pos=(bx, by), size=(btn_w, btn_h))

            # 3. Неоновый световод по периметру — точь-в-точь как в тюнере
            rx_n, ry_n, rw_n, rh_n = meta["rim_box_norm"]
            rim_x = bx + rx_n * btn_w
            rim_y = by + ry_n * btn_h
            rim_w = rw_n * btn_w
            rim_h = rh_n * btn_h
            rim_r = meta["rim_radius_norm"] * min(btn_w, btn_h)

            if pressed:
                Color(r, g, b, 0.28)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(2.6))
                Color(min(1.0, r + 0.18), min(1.0, g + 0.18), min(1.0, b + 0.18), 0.95)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.25))
            elif self.is_active:
                Color(r, g, b, 0.22 if is_light else 0.18)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.0))
            else:
                Color(0.5, 0.5, 0.5, 0.12)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(0.9))

            # 4. Центральная иконка (масштаб 0.54 и чистый металлический тон как в тюнере)
            ico_tex = self._icon_textures.get(self.icon_type)
            if ico_tex is not None:
                icx = bx + btn_w * 0.5
                icy = by + meta["center_y_norm"] * btn_h
                ico_size = round(min(btn_w, btn_h) * 0.54)

                # Тень под иконкой
                if is_light:
                    Color(1, 1, 1, 0.70)
                else:
                    Color(0, 0, 0, 0.55)
                Rectangle(
                    texture=ico_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5 - dp(1.1))),
                    size=(ico_size, ico_size),
                )

                # Подсветка при нажатии
                if pressed:
                    Color(r, g, b, 0.26)
                    glow_s = round(ico_size * 1.12)
                    Rectangle(
                        texture=ico_tex,
                        pos=(round(icx - glow_s * 0.5), round(icy - glow_s * 0.5)),
                        size=(glow_s, glow_s),
                    )
                    Color(min(1.0, r + 0.22), min(1.0, g + 0.22), min(1.0, b + 0.22), 0.98)
                elif self.is_active:
                    if is_light:
                        Color(0.22, 0.26, 0.24, 0.85)
                    else:
                        Color(0.84, 0.87, 0.90, 0.84)
                else:
                    if is_light:
                        Color(0.22, 0.26, 0.24, 0.35)
                    else:
                        Color(0.84, 0.87, 0.90, 0.30)

                Rectangle(
                    texture=ico_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5)),
                    size=(ico_size, ico_size),
                )


class StudioChordsConsole(FloatLayout):
    """Рэковая студийная панель аккордов (dp(74)), идентичная консоли тюнера."""

    _panel_dark_tex = None
    _panel_green_tex = None
    _panel_light_tex = None

    def __init__(self, height=dp(74), **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = height

        if StudioChordsConsole._panel_dark_tex is None:
            StudioChordsConsole._panel_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.PANEL_DARK_B64)), ext="png"
            ).texture
            StudioChordsConsole._panel_green_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.PANEL_GREEN_B64)), ext="png"
            ).texture
            StudioChordsConsole._panel_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.PANEL_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._panel_dark_tex,
                pos=self.pos,
                size=self.size,
            )

        self.inner_container = FloatLayout(size_hint=(None, None))
        self.add_widget(self.inner_container)

        self.bind(pos=self._sync_layout, size=self._sync_layout)
        self.update_theme_colors()

    def _sync_layout(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        bay_x = self.x + self.width * (40.0 / 960.0)
        bay_w = self.width * (880.0 / 960.0)
        bay_y = self.y + self.height * (13.0 / 148.0)
        bay_h = self.height * (122.0 / 148.0)

        self.inner_container.pos = (bay_x + dp(1), bay_y + dp(1))
        self.inner_container.size = (max(dp(10), bay_w - dp(2)), max(dp(10), bay_h - dp(2)))

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        if theme_id == "light":
            self._bg_rect.texture = self._panel_light_tex
        elif theme_id == "green":
            self._bg_rect.texture = self._panel_green_tex
        else:
            self._bg_rect.texture = self._panel_dark_tex


class StudioChordsMenu(MDBoxLayout):
    """Панель аппаратных кнопок аккордов с пропорциями и разделителями как в тюнере."""

    def __init__(
        self,
        tonality_value="A",
        type_value="Major",
        chord_value="A",
        on_tonality_press=None,
        on_type_press=None,
        on_chord_press=None,
        on_variants_press=None,
        on_mode_toggle=None,
        on_rotate_press=None,
        variants_count=1,
        current_mode="finger",
        chord_count=0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (1, 1)
        self.padding = [dp(2), dp(1), dp(2), dp(1)]
        self.spacing = dp(6)

        self.tonality_item = ChordHardwareButton(
            icon_type="tonality",
            on_press=on_tonality_press,
            is_active=True,
        )
        self.type_item = ChordHardwareButton(
            icon_type="type",
            on_press=on_type_press,
            is_active=True,
        )
        self.chord_item = ChordHardwareButton(
            icon_type="chord",
            on_press=on_chord_press,
            is_active=(chord_count > 1),
        )
        self.variants_item = ChordHardwareButton(
            icon_type="variants",
            on_press=on_variants_press,
            is_active=(variants_count > 1),
        )
        self.mode_item = ChordHardwareButton(
            icon_type="finger" if current_mode == "finger" else "notes",
            on_press=on_mode_toggle,
            is_active=True,
        )

        self.rotate_item = None
        if on_rotate_press is not None:
            self.rotate_item = ChordHardwareButton(
                icon_type="rotate_land",
                on_press=on_rotate_press,
                is_active=True,
            )

        self.center_name_box = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(1.6, 1),
            padding=[dp(4), 0, dp(4), 0],
        )
        self.center_name_label = MDLabel(
            text=chord_value or "A",
            font_size=sp(22),
            bold=True,
            halign="center",
            valign="middle",
            size_hint=(1, 1),
            theme_text_color="Custom",
            text_color=[1.0, 0.95, 0.85, 0.95],
        )
        self.center_name_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.center_name_box.add_widget(self.center_name_label)

        self._center_visible = False
        self.bind(pos=self._draw_dividers, size=self._draw_dividers, children=self._draw_dividers)
        self._rebuild_slots()
        self.update_theme_colors()

    def _draw_dividers(self, *args):
        """Рисует студийные вертикальные разделители между пэдами."""
        self.canvas.after.clear()
        if len(self.children) < 2 or self.height <= dp(10):
            return

        is_light = settings_manager.theme == "light"
        ordered = sorted(self.children, key=lambda w: w.x)
        y1 = self.y + dp(5)
        y2 = self.top - dp(5)

        with self.canvas.after:
            for i in range(len(ordered) - 1):
                left_w = ordered[i]
                right_w = ordered[i + 1]
                mid_x = round((left_w.right + right_w.x) * 0.5)

                Color(0.03, 0.04, 0.05, 0.85 if not is_light else 0.35)
                Line(points=[mid_x - dp(0.6), y1, mid_x - dp(0.6), y2], width=dp(1.1))

                Color(1.0, 1.0, 1.0, 0.14 if not is_light else 0.55)
                Line(points=[mid_x + dp(0.7), y1, mid_x + dp(0.7), y2], width=dp(0.9))

    def _rebuild_slots(self):
        self.clear_widgets()
        items_left = [self.tonality_item, self.type_item, self.chord_item]
        items_right = [self.variants_item, self.mode_item]
        if self.rotate_item is not None:
            items_right.append(self.rotate_item)

        for item in items_left:
            self.add_widget(item)
        if self._center_visible:
            self.add_widget(self.center_name_box)
        for item in items_right:
            self.add_widget(item)

        Clock.schedule_once(self._draw_dividers, 0)

    def set_center_chord_name(self, visible, chord_text=""):
        if visible:
            text = (chord_text or "?").strip()
            self.center_name_label.text = text
            fs = 22 if len(text) <= 4 else (18 if len(text) <= 7 else (15 if len(text) <= 10 else 12))
            self.center_name_label.font_size = sp(fs)
        if self._center_visible != visible:
            self._center_visible = visible
            self._rebuild_slots()

    def set_icons_rotation(self, angle):
        pass

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        if theme_id == "dark":
            self.center_name_label.text_color = [1.0, 0.5, 0.0, 1]
        elif theme_id == "light":
            self.center_name_label.text_color = [0.1, 0.55, 0.3, 1]
        else:
            self.center_name_label.text_color = [1.0, 0.95, 0.85, 0.95]

        for btn in (self.tonality_item, self.type_item, self.chord_item,
                    self.variants_item, self.mode_item, self.rotate_item):
            if btn is not None:
                btn.update_theme_colors()
        self._draw_dividers()

    def update_chord(self, chord_count):
        self.chord_item.is_active = chord_count > 1

    def update_variants(self, count):
        self.variants_item.is_active = count > 1

    def update_mode(self, mode):
        is_finger = mode == "finger"
        self.mode_item.set_icon("finger" if is_finger else "notes")

class SearchHardwareButton(ButtonBehavior, Widget):
    """Аппаратная клавиша «Найти» с ровной фаской и симметричными отступами, как в экране песен."""

    text = StringProperty("Найти")
    is_pressed = BooleanProperty(False)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    def __init__(self, text="Найти", on_release=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self._callback = on_release
        self.size_hint = (None, 1)
        self.width = dp(92)

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            text=self.update_canvas,
            is_pressed=self.update_canvas,
            accent_color=self.update_canvas,
        )
        self.update_theme_colors()

    def update_theme_colors(self):
        self.accent_color = ChordHardwareButton._get_theme_glow(settings_manager.theme)
        self.update_canvas()

    def on_press(self):
        Clock.unschedule(self._reset_press)
        self.is_pressed = True

    def on_release(self):
        Clock.schedule_once(self._reset_press, 0.14)
        if self._callback:
            self._callback()

    def _reset_press(self, dt):
        self.is_pressed = False

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        x, y, w, h = round(self.x), round(self.y), round(self.width), round(self.height)
        is_light = settings_manager.theme == "light"
        pressed = self.is_pressed

        c = list(self.accent_color)
        r, g, b = float(c[0]), float(c[1]), float(c[2])
        rad = min(dp(9), min(w, h) * 0.38)

        with self.canvas:
            # 1. Тёмная посадочная шахта
            Color(0.02, 0.03, 0.04, 0.96) if not is_light else Color(0.56, 0.60, 0.58, 0.92)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[rad])

            # 2. Тело металлической клавиши
            kx = x + dp(1.5)
            ky = y + (dp(1.0) if pressed else dp(2.0))
            kw = w - dp(3.0)
            kh = h - dp(3.0)
            kr = max(dp(3), rad - dp(1.5))

            if is_light:
                base_v = 0.80 if pressed else 0.88
                Color(base_v, base_v + 0.01, base_v, 1.0)
            else:
                base_v = 0.16 if pressed else 0.22
                Color(base_v, base_v + 0.015, base_v + 0.025, 1.0)
            RoundedRectangle(pos=(kx, ky), size=(kw, kh), radius=[kr])

            # 3. Верхний световой блик клавиши
            if not pressed:
                Color(1.0, 1.0, 1.0, 0.28 if is_light else 0.09)
                RoundedRectangle(
                    pos=(kx + dp(1), ky + kh * 0.48),
                    size=(kw - dp(2), kh * 0.48),
                    radius=[kr, kr, dp(2), dp(2)],
                )

            # 4. Неоновый световод строго по границе клавиши
            if pressed:
                Color(r, g, b, 0.34)
                Line(rounded_rectangle=(kx, ky, kw, kh, kr), width=dp(2.2))
                Color(min(1.0, r + 0.2), min(1.0, g + 0.2), min(1.0, b + 0.2), 0.98)
                Line(rounded_rectangle=(kx, ky, kw, kh, kr), width=dp(1.2))
            else:
                Color(r, g, b, 0.38 if is_light else 0.32)
                Line(rounded_rectangle=(kx, ky, kw, kh, kr), width=dp(1.1))

            # 5. Надпись «Найти» ровно по центру
            txt_col = (
                (0.12, 0.22, 0.16, 0.96)
                if is_light
                else (min(1.0, r + 0.28), min(1.0, g + 0.28), min(1.0, b + 0.28), 0.98)
            )
            lbl = CoreLabel(text=self.text, font_size=sp(14.5), bold=True, color=txt_col)
            lbl.refresh()
            tex = lbl.texture
            if tex:
                tcx = kx + kw * 0.5
                tcy = ky + kh * 0.5
                Color(1, 1, 1, 1)
                Rectangle(
                    texture=tex,
                    pos=(round(tcx - tex.width * 0.5), round(tcy - tex.height * 0.5)),
                    size=tex.size,
                )


class StudioSearchBar(FloatLayout):
    """Симметричная студийная рэковая панель поиска аккордов с винтами и нишей."""

    _bg_dark_tex = None
    _bg_green_tex = None
    _bg_light_tex = None

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self.size_hint = (1, None)
        self.height = dp(56)

        if StudioSearchBar._bg_dark_tex is None:
            StudioSearchBar._bg_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.SEARCH_DARK_B64)), ext="png"
            ).texture
            StudioSearchBar._bg_green_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.SEARCH_GREEN_B64)), ext="png"
            ).texture
            StudioSearchBar._bg_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.SEARCH_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._bg_dark_tex,
                pos=self.pos,
                size=self.size,
            )

        # Одинаковые отступы dp(3) сверху, снизу и справа вокруг кнопки «Найти»
        self.inner_box = MDBoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            padding=[dp(10), dp(3), dp(3), dp(3)],
            spacing=dp(4),
        )

        self.search_field = TextInput(
            multiline=False,
            size_hint=(1, 1),
            font_size=sp(16),
            background_color=[0, 0, 0, 0],
            background_normal="",
            background_active="",
            padding=[dp(2), dp(8), dp(2), dp(8)],
            on_text_validate=self._on_search_pressed,
        )
        self.search_field.bind(
            text=self._on_text_change,
            height=self._center_text_vertically,
            line_height=self._center_text_vertically,
        )

        self.clear_wrapper = MDCard(
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            radius=[dp(14)] * 4,
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            pos_hint={"center_y": 0.5},
            opacity=0,
            disabled=True,
        )
        self.clear_btn = MDIconButton(
            icon="close-circle-outline",
            size_hint=(1, 1),
            theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear_pressed,
            ripple_scale=0,
        )
        self.clear_wrapper.add_widget(self.clear_btn)

        self.search_btn = SearchHardwareButton(
            text=get_text("find", "Найти"),
            on_release=self._on_search_pressed,
        )

        self.inner_box.add_widget(self.search_field)
        self.inner_box.add_widget(self.clear_wrapper)
        self.inner_box.add_widget(self.search_btn)
        self.add_widget(self.inner_box)

        self.bind(pos=self._sync_layout, size=self._sync_layout)
        self.update_language()
        self.update_theme_colors()

    def _center_text_vertically(self, *args):
        pad_y = max(0.0, (self.search_field.height - self.search_field.line_height) * 0.5)
        self.search_field.padding = [dp(2), pad_y, dp(2), pad_y]

    def _sync_layout(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        # Симметричная ниша: x = 40..920 (ширина 880), y = 16..96 (высота 80 на холсте 112)
        bay_x = self.x + self.width * (40.0 / 960.0)
        bay_w = self.width * (880.0 / 960.0)
        bay_y = self.y + self.height * (16.0 / 112.0)
        bay_h = self.height * (80.0 / 112.0)

        self.inner_box.pos = (bay_x, bay_y)
        self.inner_box.size = (max(dp(20), bay_w), max(dp(16), bay_h))
        self._center_text_vertically()

    def update_language(self):
        self.search_field.hint_text = get_text("search", "Поиск")
        self.search_btn.text = get_text("find", "Найти")

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        if theme_id == "light":
            self._bg_rect.texture = self._bg_light_tex
            self.search_field.foreground_color = [0.12, 0.16, 0.14, 1]
            self.search_field.hint_text_color = [0.45, 0.50, 0.48, 0.9]
            self.search_field.cursor_color = [0.08, 0.58, 0.30, 1]
            self.clear_btn.icon_color = [0.35, 0.42, 0.38, 0.85]
        elif theme_id == "dark":
            self._bg_rect.texture = self._bg_dark_tex
            self.search_field.foreground_color = [0.95, 0.96, 0.98, 1]
            self.search_field.hint_text_color = [0.62, 0.65, 0.68, 0.75]
            self.search_field.cursor_color = [1.0, 0.50, 0.0, 1]
            self.clear_btn.icon_color = [1.0, 0.55, 0.15, 0.9]
        else:
            self._bg_rect.texture = self._bg_green_tex
            self.search_field.foreground_color = [0.92, 0.98, 0.94, 1]
            self.search_field.hint_text_color = [0.60, 0.74, 0.66, 0.72]
            self.search_field.cursor_color = [0.18, 0.88, 0.28, 1]
            self.clear_btn.icon_color = [0.35, 0.88, 0.48, 0.9]

        self.search_btn.update_theme_colors()

    def _on_text_change(self, instance, text):
        self.current_query = text
        if text.strip():
            self.clear_wrapper.opacity = 1
            self.clear_wrapper.disabled = False
        else:
            self.clear_wrapper.opacity = 0
            self.clear_wrapper.disabled = True

    def _on_search_pressed(self, *args):
        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear_pressed(self, instance):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""
        if self.on_clear:
            self.on_clear()
        self.search_field.focus = False

    def clear(self):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""

    def focus(self):
        self.search_field.focus = True


class GriffSideArrowButton(ButtonBehavior, Widget):
    """Вертикальная клавиша пагинации, встроенная в боковую стойку рамы грифа."""

    direction = StringProperty("left")  # "left" или "right"
    is_active = BooleanProperty(True)
    is_pressed = BooleanProperty(False)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    def __init__(self, direction="left", on_press=None, is_active=True, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        self.is_active = is_active
        self._callback = on_press
        self.size_hint = (None, None)

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            direction=self.update_canvas,
            is_active=self.update_canvas,
            is_pressed=self.update_canvas,
            accent_color=self.update_canvas,
        )
        self.update_theme_colors()

    def update_theme_colors(self):
        self.accent_color = ChordHardwareButton._get_theme_glow(settings_manager.theme)
        self.update_canvas()

    def on_press(self):
        Clock.unschedule(self._reset_press)
        self.is_pressed = True

    def on_release(self):
        Clock.schedule_once(self._reset_press, 0.14)
        if self._callback and self.is_active:
            self._callback()

    def _reset_press(self, dt):
        self.is_pressed = False

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        if not ChordHardwareButton._textures_loaded:
            ChordHardwareButton()

        btn_w = round(self.width)
        btn_h = round(self.height)
        bx = round(self.x)
        by = round(self.y)

        is_light = settings_manager.theme == "light"
        pressed = self.is_pressed
        meta = menu_assets.DOWN_META if pressed else menu_assets.UP_META

        well_tex = ChordHardwareButton._well_light if is_light else ChordHardwareButton._well_dark
        key_tex = (
            (ChordHardwareButton._down_light if pressed else ChordHardwareButton._up_light)
            if is_light
            else (ChordHardwareButton._down_dark if pressed else ChordHardwareButton._up_dark)
        )

        c = list(self.accent_color)
        r, g, b = float(c[0]), float(c[1]), float(c[2])

        with self.canvas:
            Color(1, 1, 1, 1)
            Rectangle(texture=well_tex, pos=(bx, by), size=(btn_w, btn_h))
            Rectangle(texture=key_tex, pos=(bx, by), size=(btn_w, btn_h))

            # Неоновый контур клавиши пагинации
            rx_n, ry_n, rw_n, rh_n = meta["rim_box_norm"]
            rim_x = bx + rx_n * btn_w
            rim_y = by + ry_n * btn_h
            rim_w = rw_n * btn_w
            rim_h = rh_n * btn_h
            rim_r = min(dp(10), min(rim_w, rim_h) * 0.35)

            if pressed:
                Color(r, g, b, 0.34)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(2.4))
                Color(min(1.0, r + 0.2), min(1.0, g + 0.2), min(1.0, b + 0.2), 0.98)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.25))
            elif self.is_active:
                Color(r, g, b, 0.32 if is_light else 0.26)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.1))
            else:
                Color(0.5, 0.5, 0.5, 0.14)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(0.9))

            # Чёткая стрелка-шеврон по центру стойки
            cx = bx + btn_w * 0.5
            cy = by + meta["center_y_norm"] * btn_h
            aw = min(dp(6), btn_w * 0.24)
            ah = min(dp(11), btn_h * 0.12)

            if self.direction == "left":
                pts = [cx + aw, cy + ah, cx - aw, cy, cx + aw, cy - ah]
            else:
                pts = [cx - aw, cy + ah, cx + aw, cy, cx - aw, cy - ah]

            # Тень под стрелкой
            Color(1, 1, 1, 0.65) if is_light else Color(0, 0, 0, 0.60)
            Line(points=[pts[0], pts[1] - dp(1), pts[2], pts[3] - dp(1), pts[4], pts[5] - dp(1)], width=dp(2.1), cap="round", joint="round")

            # Основная линия стрелки
            if pressed:
                Color(min(1.0, r + 0.25), min(1.0, g + 0.25), min(1.0, b + 0.25), 1.0)
            elif self.is_active:
                Color(0.18, 0.24, 0.21, 0.92) if is_light else Color(0.88, 0.92, 0.94, 0.92)
            else:
                Color(0.35, 0.38, 0.40, 0.35) if is_light else Color(0.84, 0.87, 0.90, 0.28)

            Line(points=pts, width=dp(2.1), cap="round", joint="round")


class StudioGriffCard(FloatLayout):
    """Студийная рэковая рамка для грифа с боковыми кнопками пагинации в стойках."""

    _bg_dark_tex = None
    _bg_green_tex = None
    _bg_light_tex = None

    def __init__(self, on_prev=None, on_next=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)

        if StudioGriffCard._bg_dark_tex is None:
            StudioGriffCard._bg_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.GRIFF_DARK_B64)), ext="png"
            ).texture
            StudioGriffCard._bg_green_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.GRIFF_GREEN_B64)), ext="png"
            ).texture
            StudioGriffCard._bg_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.GRIFF_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._bg_dark_tex,
                pos=self.pos,
                size=self.size,
            )

        self.left_arrow_btn = GriffSideArrowButton(direction="left", on_press=on_prev, is_active=True)
        self.right_arrow_btn = GriffSideArrowButton(direction="right", on_press=on_next, is_active=True)
        self.inner_container = FloatLayout(size_hint=(None, None))

        self.add_widget(self.left_arrow_btn)
        self.add_widget(self.right_arrow_btn)
        self.add_widget(self.inner_container)

        self.bind(pos=self._sync_layout, size=self._sync_layout)
        self.update_theme_colors()

    def _sync_layout(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        # Посадка боковых клавиш пагинации в стойки рамы (x1+10..x1+66 -> 14..70 на холсте 960)
        slot_w = max(dp(18), self.width * (56.0 / 960.0))
        slot_y = self.y + self.height * (56.0 / 540.0)
        slot_h = max(dp(40), self.height * (428.0 / 540.0))

        self.left_arrow_btn.pos = (self.x + self.width * (14.0 / 960.0), slot_y)
        self.left_arrow_btn.size = (slot_w, slot_h)

        self.right_arrow_btn.pos = (self.x + self.width * (890.0 / 960.0), slot_y)
        self.right_arrow_btn.size = (slot_w, slot_h)

        # Центральная ниша под гриф (bay_x1=80/960, bay_y1=18/540)
        bay_x = self.x + self.width * (80.0 / 960.0)
        bay_w = self.width * (800.0 / 960.0)
        bay_y = self.y + self.height * (18.0 / 540.0)
        bay_h = self.height * (504.0 / 540.0)

        self.inner_container.pos = (bay_x, bay_y)
        self.inner_container.size = (max(dp(40), bay_w), max(dp(40), bay_h))

    def set_arrows_active(self, is_active):
        self.left_arrow_btn.is_active = is_active
        self.right_arrow_btn.is_active = is_active

    def update_theme_colors(self):
        theme_id = settings_manager.theme
        if theme_id == "light":
            self._bg_rect.texture = self._bg_light_tex
        elif theme_id == "green":
            self._bg_rect.texture = self._bg_green_tex
        else:
            self._bg_rect.texture = self._bg_dark_tex

        self.left_arrow_btn.update_theme_colors()
        self.right_arrow_btn.update_theme_colors()

