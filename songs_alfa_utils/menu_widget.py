# songs_alfa_utils/menu_widget.py
import base64
import io

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from state.settings_state import settings_state as settings_manager
from utils.localization import get_text

try:
    from data.songs_alfa import menu_assets
except ImportError:
    from songs_alfa_utils.menu_generator import save_songs_alfa_assets
    save_songs_alfa_assets()
    from data.songs_alfa import menu_assets


class _HardwareTextures:
    loaded = False
    well_dark = None
    up_dark = None
    down_dark = None
    well_light = None
    up_light = None
    down_light = None

    @classmethod
    def ensure(cls):
        if cls.loaded:
            return

        def _load(b64_str):
            return CoreImage(io.BytesIO(base64.b64decode(b64_str)), ext="png").texture

        cls.well_dark = _load(menu_assets.WELL_DARK_B64)
        cls.up_dark = _load(menu_assets.KEY_UP_DARK_B64)
        cls.down_dark = _load(menu_assets.KEY_DOWN_DARK_B64)
        cls.well_light = _load(menu_assets.WELL_LIGHT_B64)
        cls.up_light = _load(menu_assets.KEY_UP_LIGHT_B64)
        cls.down_light = _load(menu_assets.KEY_DOWN_LIGHT_B64)
        cls.loaded = True

    @staticmethod
    def get_glow(theme_id):
        if theme_id == "light":
            return [0.08, 0.58, 0.30, 1.0]
        elif theme_id == "dark":
            return [1.0, 0.50, 0.0, 1.0]
        return [0.18, 0.88, 0.28, 1.0]

def _draw_crisp_hardware_key(canvas, x, y, w, h, radius, is_light, pressed, r, g, b):
    """Рисует идеально ровную аппаратную клавишу без искажений растянутых текстур."""
    x, y, w, h = round(x), round(y), round(w), round(h)
    rad = min(radius, min(w, h) * 0.38)

    with canvas:
        # 1. Тёмная посадочная шахта (колодец)
        Color(0.02, 0.03, 0.04, 0.96) if not is_light else Color(0.56, 0.60, 0.58, 0.92)
        RoundedRectangle(pos=(x, y), size=(w, h), radius=[rad])

        # 2. Тело металлической клавиши (при нажатии слегка утапливается вниз)
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

        # 3. Верхний металлический градиент / блик клавиши
        if not pressed:
            Color(1.0, 1.0, 1.0, 0.28 if is_light else 0.09)
            RoundedRectangle(
                pos=(kx + dp(1), ky + kh * 0.48),
                size=(kw - dp(2), kh * 0.48),
                radius=[kr, kr, dp(2), dp(2)],
            )

        # 4. Внутренняя фаска и неоновый световод строго по краю клавиши (100% совпадение углов)
        if pressed:
            Color(r, g, b, 0.34)
            Line(rounded_rectangle=(kx, ky, kw, kh, kr), width=dp(2.2))
            Color(min(1.0, r + 0.2), min(1.0, g + 0.2), min(1.0, b + 0.2), 0.98)
            Line(rounded_rectangle=(kx, ky, kw, kh, kr), width=dp(1.2))
        else:
            Color(r, g, b, 0.38 if is_light else 0.32)
            Line(rounded_rectangle=(kx, ky, kw, kh, kr), width=dp(1.1))

    return kx, ky, kw, kh


class AlfaArrowPad(ButtonBehavior, Widget):
    """Аппаратная клавиша прокрутки алфавита (< / >) по краям верхней ниши."""

    direction = StringProperty("left")
    is_pressed = BooleanProperty(False)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    def __init__(self, direction="left", on_release=None, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        self._callback = on_release
        self.size_hint = (None, 1)
        self.width = dp(36)
        _HardwareTextures.ensure()

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            is_pressed=self.update_canvas,
            accent_color=self.update_canvas,
        )
        self.update_theme_colors()

    def update_theme_colors(self):
        self.accent_color = _HardwareTextures.get_glow(settings_manager.theme)
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

        is_light = settings_manager.theme == "light"
        pressed = self.is_pressed
        c = list(self.accent_color)
        r, g, b = float(c[0]), float(c[1]), float(c[2])

        kx, ky, kw, kh = _draw_crisp_hardware_key(
            self.canvas, self.x, self.y, self.width, self.height,
            radius=dp(8), is_light=is_light, pressed=pressed, r=r, g=g, b=b,
        )

        with self.canvas:
            cx = kx + kw * 0.5
            cy = ky + kh * 0.5
            aw = min(dp(4.2), kw * 0.22)
            ah = min(dp(6.0), kh * 0.25)
            pts = (
                [cx + aw, cy + ah, cx - aw, cy, cx + aw, cy - ah]
                if self.direction == "left"
                else [cx - aw, cy + ah, cx + aw, cy, cx - aw, cy - ah]
            )
            if pressed:
                Color(min(1.0, r + 0.25), min(1.0, g + 0.25), min(1.0, b + 0.25), 1.0)
            else:
                Color(0.18, 0.24, 0.21, 0.94) if is_light else Color(0.88, 0.92, 0.94, 0.92)
            Line(points=pts, width=dp(1.8), cap="round", joint="round")


class StudioLetterKey(ButtonBehavior, Widget):
    """Клавиша буквы в алфавитной ленте с подсветкой выбранной буквы."""

    btn_text = StringProperty("А")
    is_selected = BooleanProperty(False)
    is_pressed = BooleanProperty(False)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    def __init__(self, text, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press
        self.size_hint = (None, 1)
        self.width = dp(32)
        _HardwareTextures.ensure()

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            btn_text=self.update_canvas,
            is_selected=self.update_canvas,
            is_pressed=self.update_canvas,
            accent_color=self.update_canvas,
        )
        self.update_theme_colors()

    def update_theme_colors(self):
        self.accent_color = _HardwareTextures.get_glow(settings_manager.theme)
        self.update_canvas()

    def set_selected(self, selected):
        if self.is_selected != selected:
            self.is_selected = selected

    def on_press(self):
        Clock.unschedule(self._reset_press)
        self.is_pressed = True

    def on_release(self):
        Clock.schedule_once(self._reset_press, 0.12)
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)

    def _reset_press(self, dt):
        self.is_pressed = False

    def update_canvas(self, *args):
        self.canvas.clear()
        if self.width <= 4 or self.height <= 4:
            return

        is_light = settings_manager.theme == "light"
        lit = self.is_selected or self.is_pressed
        c = list(self.accent_color)
        r, g, b = float(c[0]), float(c[1]), float(c[2])

        bx = round(self.x + dp(1))
        by = round(self.y + dp(2))
        bw = round(self.width - dp(2))
        bh = round(self.height - dp(4))

        with self.canvas:
            if lit:
                meta = menu_assets.DOWN_META if self.is_pressed else menu_assets.UP_META
                well_tex = _HardwareTextures.well_light if is_light else _HardwareTextures.well_dark
                key_tex = (
                    (_HardwareTextures.down_light if self.is_pressed else _HardwareTextures.up_light)
                    if is_light
                    else (_HardwareTextures.down_dark if self.is_pressed else _HardwareTextures.up_dark)
                )
                Color(1, 1, 1, 1)
                Rectangle(texture=well_tex, pos=(bx, by), size=(bw, bh))
                Rectangle(texture=key_tex, pos=(bx, by), size=(bw, bh))

                rx_n, ry_n, rw_n, rh_n = meta["rim_box_norm"]
                rim_x = bx + rx_n * bw
                rim_y = by + ry_n * bh
                rim_w = rw_n * bw
                rim_h = rh_n * bh
                rim_r = min(dp(7), min(rim_w, rim_h) * 0.35)

                Color(r, g, b, 0.35)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(2.0))
                Color(min(1.0, r + 0.2), min(1.0, g + 0.2), min(1.0, b + 0.2), 0.98)
                Line(rounded_rectangle=(rim_x, rim_y, rim_w, rim_h, rim_r), width=dp(1.1))

                txt_col = (
                    (0.08, 0.45, 0.24, 1.0)
                    if is_light
                    else (min(1.0, r + 0.28), min(1.0, g + 0.28), min(1.0, b + 0.28), 1.0)
                )
            else:
                txt_col = (0.20, 0.24, 0.22, 0.88) if is_light else (0.82, 0.86, 0.88, 0.78)

            lbl = CoreLabel(text=self.btn_text, font_size=sp(14), bold=True, color=txt_col)
            lbl.refresh()
            tex = lbl.texture
            if tex:
                tcx = bx + bw * 0.5
                tcy = by + bh * 0.5
                Color(1, 1, 1, 1)
                Rectangle(
                    texture=tex,
                    pos=(round(tcx - tex.width * 0.5), round(tcy - tex.height * 0.5)),
                    size=tex.size,
                )


class StudioFlagBadge(MDBoxLayout):
    """Металлический бейдж языка RU / EN в ленте алфавита."""

    def __init__(self, flag_type="ru", rus_tex=None, eng_tex=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, 1)
        self.width = dp(34)
        self.padding = [dp(2)] * 4

        tex = rus_tex if flag_type == "ru" else (eng_tex if flag_type == "en" else None)
        anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 1))

        if tex:
            anchor.add_widget(
                Image(texture=tex, size_hint=(None, None), size=(dp(20), dp(20)), allow_stretch=True, keep_ratio=True)
            )
        else:
            anchor.add_widget(
                MDLabel(
                    text="RU" if flag_type == "ru" else "EN",
                    font_size=sp(10),
                    halign="center",
                    valign="middle",
                    bold=True,
                    theme_text_color="Custom",
                    text_color=[0.8, 0.85, 0.85, 0.8],
                )
            )

        self.add_widget(anchor)


class StudioAlphabetRow(MDBoxLayout):
    """Верхний ярус консоли: алфавит с аппаратными стрелками по краям."""

    RU_LETTERS = [
        "А", "Б", "В", "Г", "Д", "Е", "Ё", "Ж", "З", "И",
        "Й", "К", "Л", "М", "Н", "О", "П", "Р", "С", "Т",
        "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ъ", "Ы", "Ь",
        "Э", "Ю", "Я",
    ]
    EN_LETTERS = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
        "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
        "U", "V", "W", "X", "Y", "Z",
    ]
    DIGITS_LETTERS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#"]

    def __init__(self, on_letter_press=None, current_language="ru", rus_tex=None, eng_tex=None, **kwargs):
        super().__init__(**kwargs)
        self.on_letter_press = on_letter_press
        self.current_language = current_language
        self.current_selection = None
        self._rus_tex = rus_tex
        self._eng_tex = eng_tex
        self._built_language = None

        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.spacing = dp(4)
        self.padding = [dp(3), dp(3), dp(3), dp(3)]

        self.left_arrow = AlfaArrowPad(direction="left", on_release=lambda: self.scroll(-1))
        self.right_arrow = AlfaArrowPad(direction="right", on_release=lambda: self.scroll(1))

        self.scroll_view = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
        )
        self.container = MDBoxLayout(
            orientation="horizontal",
            size_hint_x=None,
            spacing=dp(2),
            padding=[dp(2), 0, dp(2), 0],
        )
        self.container.bind(minimum_width=self.container.setter("width"))
        self.scroll_view.add_widget(self.container)

        self.add_widget(self.left_arrow)
        self.add_widget(self.scroll_view)
        self.add_widget(self.right_arrow)

        self.buttons = []
        self._populate_items()
        self.update_theme_colors()

    def _populate_items(self, force=False):
        if not force and self._built_language == self.current_language and self.buttons:
            return

        self.container.clear_widgets()
        self.buttons = []

        user_lang = settings_manager.language
        if user_lang == "ru":
            groups = [
                ("ru", self.RU_LETTERS, True),
                ("symbols", self.DIGITS_LETTERS, False),
                ("en", self.EN_LETTERS, True),
            ]
        else:
            groups = [
                ("en", self.EN_LETTERS, True),
                ("symbols", self.DIGITS_LETTERS, False),
            ]

        total_width = dp(6)
        for group_type, letters, show_flag in groups:
            if show_flag:
                flag = StudioFlagBadge(flag_type=group_type, rus_tex=self._rus_tex, eng_tex=self._eng_tex)
                self.container.add_widget(flag)
                total_width += flag.width + dp(2)

            for letter in letters:
                btn = StudioLetterKey(text=letter, on_press=self._on_letter_press)
                if letter == self.current_selection:
                    btn.set_selected(True)
                self.buttons.append(btn)
                self.container.add_widget(btn)
                total_width += btn.width + dp(2)

        self.container.width = total_width + dp(6)
        self._built_language = self.current_language

    def scroll(self, direction):
        new_scroll = max(0.0, min(1.0, self.scroll_view.scroll_x + direction * 0.22))
        Animation(scroll_x=new_scroll, duration=0.2, t="out_quad").start(self.scroll_view)

    def _on_letter_press(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)
        if self.on_letter_press:
            self.on_letter_press(letter)

    def set_language(self, language):
        if self.current_language == language and self._built_language == language:
            return
        self.current_language = language
        self.current_selection = None
        self._populate_items(force=True)

    def set_current_letter(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)

    def update_theme_colors(self):
        self.left_arrow.update_theme_colors()
        self.right_arrow.update_theme_colors()
        for btn in self.buttons:
            btn.update_theme_colors()


class StudioFindButton(ButtonBehavior, Widget):
    """Аппаратная клавиша «Найти» в нижнем ярусе консоли песен."""

    text = StringProperty("Найти")
    is_pressed = BooleanProperty(False)
    accent_color = ListProperty([0.18, 0.88, 0.28, 1.0])

    def __init__(self, text="Найти", on_release=None, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self._callback = on_release
        self.size_hint = (None, 1)
        self.width = dp(98)
        _HardwareTextures.ensure()

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas,
            text=self.update_canvas,
            is_pressed=self.update_canvas,
            accent_color=self.update_canvas,
        )
        self.update_theme_colors()

    def update_theme_colors(self):
        self.accent_color = _HardwareTextures.get_glow(settings_manager.theme)
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

        is_light = settings_manager.theme == "light"
        pressed = self.is_pressed
        c = list(self.accent_color)
        r, g, b = float(c[0]), float(c[1]), float(c[2])

        kx, ky, kw, kh = _draw_crisp_hardware_key(
            self.canvas, self.x, self.y, self.width, self.height,
            radius=dp(9), is_light=is_light, pressed=pressed, r=r, g=g, b=b,
        )

        with self.canvas:
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


class StudioSongsHeaderBlock(FloatLayout):
    """Единый двухъярусный рэковый блок экрана песен: верх — алфавит, низ — поиск."""

    _bg_dark_tex = None
    _bg_green_tex = None
    _bg_light_tex = None

    def __init__(
        self,
        on_letter_press=None,
        on_search=None,
        on_clear=None,
        current_language="ru",
        rus_tex=None,
        eng_tex=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self.size_hint = (1, None)
        self.height = dp(104)

        if StudioSongsHeaderBlock._bg_dark_tex is None:
            StudioSongsHeaderBlock._bg_dark_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.HEADER_DARK_B64)), ext="png"
            ).texture
            StudioSongsHeaderBlock._bg_green_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.HEADER_GREEN_B64)), ext="png"
            ).texture
            StudioSongsHeaderBlock._bg_light_tex = CoreImage(
                io.BytesIO(base64.b64decode(menu_assets.HEADER_LIGHT_B64)), ext="png"
            ).texture

        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = Rectangle(
                texture=self._bg_dark_tex,
                pos=self.pos,
                size=self.size,
            )

        # Верхний ярус: алфавит
        self.alphabet_row = StudioAlphabetRow(
            on_letter_press=on_letter_press,
            current_language=current_language,
            rus_tex=rus_tex,
            eng_tex=eng_tex,
        )
        self.add_widget(self.alphabet_row)

        # Нижний ярус: поиск
        # Нижний ярус: поиск (одинаковые отступы dp(3) сверху, снизу и справа вокруг кнопки «Найти»)
        self.search_box = MDBoxLayout(
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

        self.search_btn = StudioFindButton(
            text=get_text("find", "Найти"),
            on_release=self._on_search_pressed,
        )

        self.search_box.add_widget(self.search_field)
        self.search_box.add_widget(self.clear_wrapper)
        self.search_box.add_widget(self.search_btn)
        self.add_widget(self.search_box)

        self.bind(pos=self._sync_layout, size=self._sync_layout)
        self.update_language()
        self.update_theme_colors()

    def _center_text_vertically(self, *args):
        pad_y = max(0.0, (self.search_field.height - self.search_field.line_height) * 0.5)
        self.search_field.padding = [dp(2), pad_y, dp(2), pad_y]

    def _sync_layout(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        # Обе ниши строго одинаковы: x = 40..920 (ширина 880), высота = 80/216
        bay_x = self.x + self.width * (40.0 / 960.0)
        bay_w = self.width * (880.0 / 960.0)
        bay_h = self.height * (80.0 / 216.0)

        # Верхняя ниша (алфавит): y = 116..196 (отступ сверху 20/216)
        top_y = self.y + self.height * (116.0 / 216.0)
        self.alphabet_row.pos = (bay_x, top_y)
        self.alphabet_row.size = (max(dp(40), bay_w), max(dp(20), bay_h))

        # Нижняя ниша (поиск): y = 20..100 (отступ снизу 20/216)
        bot_y = self.y + self.height * (20.0 / 216.0)
        self.search_box.pos = (bay_x, bot_y)
        self.search_box.size = (max(dp(40), bay_w), max(dp(20), bay_h))
        self._center_text_vertically()

    # --- Совместимость с API songs_menu и search_bar ---
    def set_language(self, language):
        self.alphabet_row.set_language(language)

    def set_current_letter(self, letter):
        self.alphabet_row.set_current_letter(letter)

    def update_language(self):
        self.search_field.hint_text = get_text("search", "Поиск")
        self.search_btn.text = get_text("find", "Найти")
        self.alphabet_row.set_language(settings_manager.language)

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

        self.alphabet_row.update_theme_colors()
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
        if self.on_clear:
            self.on_clear()
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""
        self.search_field.focus = False

    def set_text(self, text):
        self.search_field.text = text or ""
        self._on_text_change(None, self.search_field.text)

    def clear(self):
        self.search_field.text = ""
        self.clear_wrapper.opacity = 0
        self.clear_wrapper.disabled = True
        self.current_query = ""