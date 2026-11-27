# chord_utils/menu_widget.py
import base64
import io

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from state.settings_state import settings_state as settings_manager

try:
    from data.chords import menu_assets
except ImportError:
    from chord_utils.menu_generator import save_chords_menu_assets
    save_chords_menu_assets()
    from data.chords import menu_assets


class ChordHardwareButton(ButtonBehavior, Widget):
    """Студийный триггер-пэд меню аккордов, заполняющий весь слот консоли."""

    icon_type = StringProperty("tonality")
    is_active = BooleanProperty(True)
    is_pressed = BooleanProperty(False)
    glow_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    _textures_loaded = False
    _well_dark = None
    _up_dark = None
    _down_dark = None
    _well_light = None
    _up_light = None
    _down_light = None
    _icon_textures = {}

    def __init__(self, icon_type="tonality", on_press=None, is_active=True, glow_color=None, **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        self.is_active = is_active
        self._callback = on_press
        if glow_color:
            self.glow_color = list(glow_color)
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
            glow_color=self.update_canvas,
        )

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
        self.glow_color = list(color)

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        # Кнопка заполняет весь доступный слот (как на скрине 2)
        btn_w = round(self.width * 0.96)
        btn_h = round(self.height * 0.96)
        bx = round(self.center_x - btn_w * 0.5)
        by = round(self.center_y - btn_h * 0.5)

        is_light = settings_manager.theme == "light"
        pressed = self.is_pressed
        meta = menu_assets.DOWN_META if pressed else menu_assets.UP_META

        well_tex = self._well_light if is_light else self._well_dark
        key_tex = (self._down_light if pressed else self._up_light) if is_light else (self._down_dark if pressed else self._up_dark)

        r, g, b = float(self.glow_color[0]), float(self.glow_color[1]), float(self.glow_color[2])

        with self.canvas:
            # 1. Шахта пэда
            Color(1, 1, 1, 1)
            Rectangle(texture=well_tex, pos=(bx, by), size=(btn_w, btn_h))

            # 2. Клавиша пэда
            Rectangle(texture=key_tex, pos=(bx, by), size=(btn_w, btn_h))

            # 3. Неоновый световод по периметру
            rx_n, ry_n, rw_n, rh_n = meta["rim_box_norm"]
            rim_x = bx + rx_n * btn_w
            rim_y = by + ry_n * btn_h
            rim_w = rw_n * btn_w
            rim_h = rh_n * btn_h
            rim_r = meta["rim_radius_norm"] * min(btn_w, btn_h)

            if pressed:
                Color(r, g, b, 0.36)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(2.5))
                Color(min(1.0, r + 0.2), min(1.0, g + 0.2), min(1.0, b + 0.2), 0.98)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.3))
            elif self.is_active:
                Color(r, g, b, 0.45 if is_light else 0.38)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.15))
            else:
                Color(0.5, 0.5, 0.5, 0.18)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.0))

            # 4. Увеличенная центральная иконка
            ico_tex = self._icon_textures.get(self.icon_type)
            if ico_tex is not None:
                icx = bx + btn_w * 0.5
                icy = by + meta["center_y_norm"] * btn_h
                ico_size = round(min(btn_w, btn_h) * 0.60)

                if is_light:
                    Color(1, 1, 1, 0.65)
                else:
                    Color(0, 0, 0, 0.55)
                Rectangle(
                    texture=ico_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5 - dp(1))),
                    size=(ico_size, ico_size),
                )

                if pressed:
                    Color(r, g, b, 0.28)
                    glow_s = round(ico_size * 1.12)
                    Rectangle(
                        texture=ico_tex,
                        pos=(round(icx - glow_s * 0.5), round(icy - glow_s * 0.5)),
                        size=(glow_s, glow_s),
                    )

                if self.is_active:
                    if is_light:
                        Color(r * 0.82, g * 0.82, b * 0.82, 0.96)
                    else:
                        Color(min(1.0, r + 0.15), min(1.0, g + 0.15), min(1.0, b + 0.15), 0.96)
                else:
                    Color(0.35, 0.38, 0.40, 0.45) if is_light else Color(0.75, 0.78, 0.80, 0.32)

                Rectangle(
                    texture=ico_tex,
                    pos=(round(icx - ico_size * 0.5), round(icy - ico_size * 0.5)),
                    size=(ico_size, ico_size),
                )


class StudioChordsConsole(FloatLayout):
    """Рэковая студийная панель аккордов с изменяемой высотой, винтами и нишей."""

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

        # Границы внутренней утопленной ниши масштабируются пропорционально высоте и ширине панели
        bay_x = self.x + self.width * (48.0 / 960.0)
        bay_w = self.width * (864.0 / 960.0)
        bay_y = self.y + self.height * (16.0 / 148.0)
        bay_h = self.height * (116.0 / 148.0)

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
    """Панель аппаратных кнопок аккордов с плотной посадкой и студийными разделителями."""

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
        # Минимальные отступы и плотный шаг между пэдами (как на скрине 2)
        self.padding = [dp(2), dp(1), dp(2), dp(1)]
        self.spacing = dp(5)

        self.tonality_item = ChordHardwareButton(
            icon_type="tonality",
            on_press=on_tonality_press,
            is_active=True,
            glow_color=[0.68, 0.25, 0.85, 1.0],
        )
        self.type_item = ChordHardwareButton(
            icon_type="type",
            on_press=on_type_press,
            is_active=True,
            glow_color=[0.05, 0.78, 0.88, 1.0],
        )
        self.chord_item = ChordHardwareButton(
            icon_type="chord",
            on_press=on_chord_press,
            is_active=(chord_count > 1),
            glow_color=[1.0, 0.72, 0.10, 1.0],
        )
        self.variants_item = ChordHardwareButton(
            icon_type="variants",
            on_press=on_variants_press,
            is_active=(variants_count > 1),
            glow_color=[0.18, 0.65, 0.98, 1.0],
        )
        self.mode_item = ChordHardwareButton(
            icon_type="finger" if current_mode == "finger" else "notes",
            on_press=on_mode_toggle,
            is_active=True,
            glow_color=[0.95, 0.55, 0.08, 1.0] if current_mode == "finger" else [0.90, 0.32, 0.35, 1.0],
        )

        self.rotate_item = None
        if on_rotate_press is not None:
            self.rotate_item = ChordHardwareButton(
                icon_type="rotate_land",
                on_press=on_rotate_press,
                is_active=True,
                glow_color=[0.20, 0.85, 0.52, 1.0],
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
        """Рисует студийные вертикальные прорези-разделители между пэдами (как на скрине 2)."""
        self.canvas.after.clear()
        if len(self.children) < 2 or self.height <= dp(10):
            return

        is_light = settings_manager.theme == "light"
        # children в Kivy идут справа налево, сортируем слева направо
        ordered = sorted(self.children, key=lambda w: w.x)
        y1 = self.y + dp(4)
        y2 = self.top - dp(4)

        with self.canvas.after:
            for i in range(len(ordered) - 1):
                left_w = ordered[i]
                right_w = ordered[i + 1]
                mid_x = round((left_w.right + right_w.x) * 0.5)

                # Тёмная канавка разделителя
                Color(0.03, 0.04, 0.05, 0.85 if not is_light else 0.35)
                Line(points=[mid_x - dp(0.6), y1, mid_x - dp(0.6), y2], width=dp(1.2))

                # Светлый металлический блик сбоку от канавки
                Color(1.0, 1.0, 1.0, 0.14 if not is_light else 0.55)
                Line(points=[mid_x + dp(0.8), y1, mid_x + dp(0.8), y2], width=dp(1.0))

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
                btn.update_canvas()
        self._draw_dividers()

    def update_chord(self, chord_count):
        self.chord_item.is_active = chord_count > 1

    def update_variants(self, count):
        self.variants_item.is_active = count > 1

    def update_mode(self, mode):
        is_finger = mode == "finger"
        self.mode_item.set_icon("finger" if is_finger else "notes")
        self.mode_item.set_color([0.95, 0.55, 0.08, 1.0] if is_finger else [0.90, 0.32, 0.35, 1.0])