# screens/settings_screen.py
from io import BytesIO
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.carousel import Carousel
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon, MDLabel
from kivymd.uix.screen import MDScreen

from config.layout_config import layout_config
from config.logger_config import screen_logger
from settings_utils.flag_widget import WavingFlagImage
from state.settings_state import settings_state
from utils.localization import get_text

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False

logger = screen_logger('Settings')


# ============ ДИНАМИЧЕСКАЯ ЗАГРУЗКА АВАТАРОВ ============
_avatar_textures_cache = {}


def get_available_avatars():
    """Динамически находит все ассеты вида avatar_<N>_png в data.Assets."""
    avatars = []
    if not HAS_ASSETS:
        return avatars

    try:
        from data import Assets
        all_assets = Assets.list_assets()
        matched = []
        for name in all_assets:
            low = name.lower()
            if low.startswith("avatar_") and low.endswith("_png"):
                num_part = low[len("avatar_"):-len("_png")]
                if num_part.isdigit():
                    matched.append((int(num_part), low))
        matched.sort(key=lambda x: x)
        avatars = [item[1] for item in matched]
    except Exception as e:
        logger.debug(f"Не удалось получить список ассетов через Assets.list_assets(): {e}")

    if not avatars:
        for i in range(1, 101):
            name = f"avatar_{i}_png"
            if load_asset_as_bytes(name):
                avatars.append(name)
            elif i > 5:
                break

    return avatars


def load_avatar_texture(asset_name):
    """Загружает и кэширует текстуру аватара."""
    if not asset_name:
        return None
    if asset_name in _avatar_textures_cache:
        return _avatar_textures_cache[asset_name]
    if not HAS_ASSETS:
        return None

    try:
        data = load_asset_as_bytes(asset_name)
        if data:
            img = CoreImage(BytesIO(data), ext="png")
            _avatar_textures_cache[asset_name] = img.texture
            return img.texture
    except Exception as e:
        logger.error(f"Ошибка загрузки аватара {asset_name}: {e}")
    return None


# ============ ЕДИНАЯ ПАЛИТРА ПРИЛОЖЕНИЯ ============
class SettingsPalette:
    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]
        return [0.46, 0.70, 0.71, 1]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [0.95, 0.95, 0.95, 1]
        elif theme_id == 'dark':
            return [0.15, 0.15, 0.15, 1]
        return [0, 0, 0, 0.15]

    @staticmethod
    def get_card_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.5]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.5]
        return [0.46, 0.70, 0.71, 0.4]

    @staticmethod
    def get_card_line_width():
        return 1.5

    @staticmethod
    def get_inner_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 1]
        elif theme_id == 'dark':
            return [0.10, 0.10, 0.10, 0.85]
        return [0, 0, 0, 0.12]

    @staticmethod
    def get_inner_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.25]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.25]
        return [0.46, 0.70, 0.71, 0.22]

    @staticmethod
    def get_active_tile_bg(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.15]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.18]
        return [0.46, 0.70, 0.71, 0.22]

    @staticmethod
    def get_active_tile_line(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 0.85]
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 0.85]
        return [0.46, 0.70, 0.71, 0.85]

    @staticmethod
    def get_text_primary(theme_id):
        if theme_id == 'light':
            return [0.1, 0.1, 0.1, 1]
        return [1, 1, 1, 0.95]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id == 'light':
            return [0.4, 0.4, 0.4, 1]
        return [1, 1, 1, 0.6]


# ============ КАРТОЧКА ОДНОЙ ТЕМЫ ============
class ThemeTile(ButtonBehavior, MDBoxLayout):
    def __init__(self, theme_id, title_key, default_title, icon_name, current_theme, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.theme_id = theme_id
        self.title_key = title_key
        self.default_title = default_title
        self.current_theme = current_theme
        self.on_select = on_select
        self.is_active = (theme_id == current_theme)

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = [dp(4), dp(8), dp(4), dp(8)]
        self.spacing = dp(4)

        with self.canvas.before:
            self.bg_color = Color(0, 0, 0, 0)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        with self.canvas.after:
            self.border_color = Color(0, 0, 0, 0)
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(12)),
                width=1.5,
            )

        self.bind(pos=self._sync_canvas, size=self._sync_canvas)

        # Строгое центрирование иконки над надписью
        icon_anchor = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, None), height=dp(26))
        self.icon_widget = MDIcon(
            icon=icon_name,
            font_size=sp(23),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
        )
        icon_anchor.add_widget(self.icon_widget)
        self.add_widget(icon_anchor)

        self.title_label = MDLabel(
            text=get_text(self.title_key, self.default_title),
            font_size=sp(12),
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=dp(18),
            theme_text_color="Custom",
        )
        self.add_widget(self.title_label)

        self.update_visuals(current_theme)

    def _sync_canvas(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(12))

    def on_release(self):
        if self.on_select:
            self.on_select(self.theme_id)

    def update_language(self):
        self.title_label.text = get_text(self.title_key, self.default_title)

    def update_visuals(self, active_theme):
        self.current_theme = active_theme
        self.is_active = (self.theme_id == active_theme)

        if self.is_active:
            self.bg_color.rgba = SettingsPalette.get_active_tile_bg(active_theme)
            self.border_color.rgba = SettingsPalette.get_active_tile_line(active_theme)
            self.border_line.width = 1.5
            self.icon_widget.text_color = SettingsPalette.get_accent(active_theme)
            self.title_label.text_color = SettingsPalette.get_text_primary(active_theme)
            self.title_label.bold = True
        else:
            self.bg_color.rgba = SettingsPalette.get_inner_bg(active_theme)
            self.border_color.rgba = SettingsPalette.get_inner_line(active_theme)
            self.border_line.width = 1.2
            self.icon_widget.text_color = SettingsPalette.get_text_secondary(active_theme)
            self.title_label.text_color = SettingsPalette.get_text_secondary(active_theme)
            self.title_label.bold = False


# ============ БЛОК 1: ВЫБОР ТЕМЫ (3 КАРТОЧКИ) ============
class ModernThemeCard(MDCard):
    def __init__(self, current_theme, on_theme_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.current_theme = current_theme
        self.on_theme_selected = on_theme_selected

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(106)
        self.radius = [dp(16)]
        self.elevation = 0
        self.line_width = SettingsPalette.get_card_line_width()
        self.padding = [dp(12), dp(10), dp(12), dp(10)]
        self.spacing = dp(8)

        header_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20), spacing=dp(6))
        self.header_icon = MDIcon(
            icon="palette-outline",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint=(None, 1),
            width=dp(18),
            theme_text_color="Custom",
        )
        self.header_label = MDLabel(
            text=get_text('theme', 'Тема'),
            font_size=sp(12),
            bold=True,
            valign="middle",
            theme_text_color="Custom",
        )
        header_row.add_widget(self.header_icon)
        header_row.add_widget(self.header_label)
        self.add_widget(header_row)

        tiles_row = MDBoxLayout(orientation='horizontal', size_hint=(1, 1), spacing=dp(8))
        themes_meta = [
            ('green', 'theme_green', 'Зелёная', 'leaf'),
            ('light', 'theme_light', 'Светлая', 'white-balance-sunny'),
            ('dark', 'theme_dark', 'Тёмная', 'weather-night'),
        ]
        self.tiles = []
        for tid, tkey, tdef, ticon in themes_meta:
            tile = ThemeTile(
                theme_id=tid,
                title_key=tkey,
                default_title=tdef,
                icon_name=ticon,
                current_theme=current_theme,
                on_select=self._handle_select,
            )
            tiles_row.add_widget(tile)
            self.tiles.append(tile)

        self.add_widget(tiles_row)
        self.update_visuals(current_theme)

    def _handle_select(self, theme_id):
        self.update_visuals(theme_id)
        if self.on_theme_selected:
            self.on_theme_selected(theme_id)

    def update_language(self):
        self.header_label.text = get_text('theme', 'Тема')
        for tile in self.tiles:
            tile.update_language()

    def update_visuals(self, active_theme):
        self.current_theme = active_theme
        self.md_bg_color = SettingsPalette.get_card_bg(active_theme)
        self.line_color = SettingsPalette.get_card_line(active_theme)
        self.line_width = SettingsPalette.get_card_line_width()
        accent = SettingsPalette.get_accent(active_theme)
        self.header_icon.text_color = accent
        self.header_label.text_color = SettingsPalette.get_text_primary(active_theme)
        for tile in self.tiles:
            tile.update_visuals(active_theme)


# ============ БЛОК 2: КАРТОЧКА АВАТАРА ============
class ModernAvatarCard(MDCard):
    def __init__(self, current_avatar, current_theme, on_avatar_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.current_theme = current_theme
        self.on_avatar_selected = on_avatar_selected
        self.avatars = get_available_avatars()
        self._programmatic = False

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(82)
        self.radius = [dp(16)]
        self.elevation = 0
        self.line_width = SettingsPalette.get_card_line_width()
        self.padding = [dp(14), dp(10), dp(10), dp(10)]
        self.spacing = dp(8)

        # Левая колонка — строго центрированная по вертикали
        left_col = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(0.48, 1))
        title_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(24),
            spacing=dp(6),
        )
        self.header_icon = MDIcon(
            icon="account-music-outline",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint=(None, 1),
            width=dp(18),
            theme_text_color="Custom",
        )
        self.header_label = MDLabel(
            text=get_text('avatar', 'Аватар'),
            font_size=sp(13),
            bold=True,
            valign="middle",
            theme_text_color="Custom",
        )
        title_row.add_widget(self.header_icon)
        title_row.add_widget(self.header_label)
        left_col.add_widget(title_row)
        self.add_widget(left_col)

        # Правая капсула с обводкой в тон карточки
        self.picker_box = MDBoxLayout(
            orientation='horizontal',
            size_hint=(0.52, 1),
            padding=[dp(2), dp(2), dp(2), dp(2)],
        )
        with self.picker_box.canvas.before:
            self.picker_bg_color = Color(*SettingsPalette.get_inner_bg(current_theme))
            self.picker_bg_rect = RoundedRectangle(pos=self.picker_box.pos, size=self.picker_box.size, radius=[dp(12)])
        with self.picker_box.canvas.after:
            self.picker_line_color = Color(*SettingsPalette.get_inner_line(current_theme))
            self.picker_line = Line(
                rounded_rectangle=(self.picker_box.x, self.picker_box.y, self.picker_box.width, self.picker_box.height, dp(12)),
                width=1.2,
            )

        def _sync_picker(inst, val):
            self.picker_bg_rect.pos = inst.pos
            self.picker_bg_rect.size = inst.size
            self.picker_line.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, dp(12))

        self.picker_box.bind(pos=_sync_picker, size=_sync_picker)

        self.left_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, 1),
            width=dp(34),
            theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            on_release=lambda *a: self._step(-1),
        )
        self.carousel = Carousel(
            direction='right',
            loop=True,
            size_hint=(1, 1),
            anim_move_duration=0.20,
        )
        self.carousel.bind(current_slide=self._on_slide_changed)
        self.right_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, 1),
            width=dp(34),
            theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            on_release=lambda *a: self._step(1),
        )

        self.picker_box.add_widget(self.left_btn)
        self.picker_box.add_widget(self.carousel)
        self.picker_box.add_widget(self.right_btn)
        self.add_widget(self.picker_box)

        self.slides = []
        self._build_slides()
        self.set_current(current_avatar, animate=False)
        self.update_visuals(current_theme)

    def _build_slides(self):
        self.carousel.clear_widgets()
        self.slides = []

        if not self.avatars:
            lbl = MDLabel(
                text="—",
                font_size=sp(13),
                halign="center",
                valign="middle",
                theme_text_color="Custom",
                text_color=SettingsPalette.get_text_secondary(self.current_theme),
            )
            self.carousel.add_widget(lbl)
            self.slides.append((None, lbl))
            self.left_btn.disabled = True
            self.right_btn.disabled = True
            return

        for avatar_name in self.avatars:
            slide_box = MDBoxLayout(orientation='vertical', size_hint=(1, 1))
            img_holder = MDBoxLayout(
                size_hint=(None, None),
                size=(dp(52), dp(52)),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
            )
            # Выделение фокусом (halo) убрано

            img = Image(
                size_hint=(None, None),
                size=(dp(46), dp(46)),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                allow_stretch=True,
                keep_ratio=True,
            )
            tex = load_avatar_texture(avatar_name)
            if tex:
                img.texture = tex

            img_holder.add_widget(img)
            slide_box.add_widget(Widget(size_hint_y=1))
            slide_box.add_widget(img_holder)
            slide_box.add_widget(Widget(size_hint_y=1))

            self.carousel.add_widget(slide_box)
            self.slides.append((avatar_name, slide_box))

        has_many = len(self.avatars) > 1
        self.left_btn.disabled = not has_many
        self.right_btn.disabled = not has_many

    def set_current(self, avatar_name, animate=False):
        if not self.avatars:
            return
        target_idx = self.avatars.index(avatar_name) if avatar_name in self.avatars else 0
        _, slide_widget = self.slides[target_idx]

        self._programmatic = True
        if animate:
            self.carousel.load_slide(slide_widget)
        else:
            old_dur = self.carousel.anim_move_duration
            self.carousel.anim_move_duration = 0
            self.carousel.load_slide(slide_widget)
            self.carousel.anim_move_duration = old_dur
        Clock.schedule_once(lambda dt: setattr(self, '_programmatic', False), 0.22)

    def _step(self, direction):
        if len(self.avatars) <= 1:
            return
        if direction > 0:
            self.carousel.load_next(mode='next')
        else:
            self.carousel.load_previous()

    def _on_slide_changed(self, instance, slide):
        if not self.avatars:
            return
        for idx, (avatar_name, slide_widget) in enumerate(self.slides):
            if slide_widget is slide and avatar_name:
                if not self._programmatic and self.on_avatar_selected:
                    self.on_avatar_selected(avatar_name)
                break

    def update_language(self):
        self.header_label.text = get_text('avatar', 'Аватар')

    def update_visuals(self, active_theme):
        self.current_theme = active_theme
        self.md_bg_color = SettingsPalette.get_card_bg(active_theme)
        self.line_color = SettingsPalette.get_card_line(active_theme)
        self.line_width = SettingsPalette.get_card_line_width()
        self.picker_bg_color.rgba = SettingsPalette.get_inner_bg(active_theme)
        self.picker_line_color.rgba = SettingsPalette.get_inner_line(active_theme)

        accent = SettingsPalette.get_accent(active_theme)
        self.header_icon.text_color = accent
        self.header_label.text_color = SettingsPalette.get_text_primary(active_theme)
        self.left_btn.icon_color = accent
        self.right_btn.icon_color = accent


# ============ БЛОК 3: КАРТОЧКА ЯЗЫКА ============
class ModernLanguageCard(MDCard):
    LANGUAGES = [
        ('ru', 'Русский', 'RU'),
        ('en', 'English', 'EN'),
        ('es', 'Español', 'ES'),
        ('pt', 'Português', 'PT'),
        ('de', 'Deutsch', 'DE'),
        ('fr', 'Français', 'FR'),
        ('it', 'Italiano', 'IT'),
        ('pl', 'Polski', 'PL'),
        ('hu', 'Magyar', 'HU'),
        ('uk', 'Українська', 'UK'),
        ('kk', 'Қазақша', 'KK'),
        ('tr', 'Türkçe', 'TR'),
    ]

    def __init__(self, current_lang, current_theme, on_lang_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.current_theme = current_theme
        self.on_lang_selected = on_lang_selected
        self._programmatic = False

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(82)
        self.radius = [dp(16)]
        self.elevation = 0
        self.line_width = SettingsPalette.get_card_line_width()
        self.padding = [dp(14), dp(10), dp(10), dp(10)]
        self.spacing = dp(8)

        # Левая колонка — строго центрированная по вертикали
        left_col = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(0.48, 1))
        title_row = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(24),
            spacing=dp(6),
        )
        self.header_icon = MDIcon(
            icon="translate",
            font_size=sp(16),
            halign="center",
            valign="middle",
            size_hint=(None, 1),
            width=dp(18),
            theme_text_color="Custom",
        )
        self.header_label = MDLabel(
            text=get_text('language', 'Язык'),
            font_size=sp(13),
            bold=True,
            valign="middle",
            theme_text_color="Custom",
        )
        title_row.add_widget(self.header_icon)
        title_row.add_widget(self.header_label)
        left_col.add_widget(title_row)
        self.add_widget(left_col)

        # Правая капсула с обводкой в тон карточки
        self.picker_box = MDBoxLayout(
            orientation='horizontal',
            size_hint=(0.52, 1),
            padding=[dp(2), dp(2), dp(2), dp(2)],
        )
        with self.picker_box.canvas.before:
            self.picker_bg_color = Color(*SettingsPalette.get_inner_bg(current_theme))
            self.picker_bg_rect = RoundedRectangle(pos=self.picker_box.pos, size=self.picker_box.size, radius=[dp(12)])
        with self.picker_box.canvas.after:
            self.picker_line_color = Color(*SettingsPalette.get_inner_line(current_theme))
            self.picker_line = Line(
                rounded_rectangle=(self.picker_box.x, self.picker_box.y, self.picker_box.width, self.picker_box.height, dp(12)),
                width=1.2,
            )

        def _sync_picker(inst, val):
            self.picker_bg_rect.pos = inst.pos
            self.picker_bg_rect.size = inst.size
            self.picker_line.rounded_rectangle = (inst.x, inst.y, inst.width, inst.height, dp(12))

        self.picker_box.bind(pos=_sync_picker, size=_sync_picker)

        self.left_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, 1),
            width=dp(34),
            theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            on_release=lambda *a: self._step(-1),
        )
        self.carousel = Carousel(
            direction='right',
            loop=True,
            size_hint=(1, 1),
            anim_move_duration=0.20,
        )
        self.carousel.bind(current_slide=self._on_slide_changed)
        self.right_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, 1),
            width=dp(34),
            theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0,
            on_release=lambda *a: self._step(1),
        )

        self.picker_box.add_widget(self.left_btn)
        self.picker_box.add_widget(self.carousel)
        self.picker_box.add_widget(self.right_btn)
        self.add_widget(self.picker_box)

        self.slides = []
        self.title_labels = []
        self._build_slides()
        self.set_current(current_lang, animate=False)
        self.update_visuals(current_theme)

    def _build_slides(self):
        self.carousel.clear_widgets()
        self.slides = []
        self.title_labels = []

        for lang_code, lang_name, short_code in self.LANGUAGES:
            slide_box = MDBoxLayout(
                orientation='vertical',
                size_hint=(1, 1),
                spacing=dp(2),
            )
            slide_box.add_widget(Widget(size_hint_y=1))

            flag_widget = WavingFlagImage(
                lang_code=lang_code,
                flag_width=dp(44),
                flag_height=dp(29),
            )
            slide_box.add_widget(flag_widget)

            name_lbl = MDLabel(
                text=lang_name,
                font_size=sp(12),
                bold=True,
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=dp(16),
                theme_text_color="Custom",
            )
            slide_box.add_widget(name_lbl)
            self.title_labels.append(name_lbl)

            slide_box.add_widget(Widget(size_hint_y=1))

            self.carousel.add_widget(slide_box)
            self.slides.append((lang_code, slide_box))

    def set_current(self, lang_code, animate=False):
        codes = [item[0] for item in self.LANGUAGES]
        target_idx = codes.index(lang_code) if lang_code in codes else 0
        _, slide_widget = self.slides[target_idx]

        self._programmatic = True
        if animate:
            self.carousel.load_slide(slide_widget)
        else:
            old_dur = self.carousel.anim_move_duration
            self.carousel.anim_move_duration = 0
            self.carousel.load_slide(slide_widget)
            self.carousel.anim_move_duration = old_dur
        Clock.schedule_once(lambda dt: setattr(self, '_programmatic', False), 0.22)

    def _step(self, direction):
        if direction > 0:
            self.carousel.load_next(mode='next')
        else:
            self.carousel.load_previous()

    def _on_slide_changed(self, instance, slide):
        for idx, (lang_code, slide_widget) in enumerate(self.slides):
            if slide_widget is slide:
                if not self._programmatic and self.on_lang_selected:
                    self.on_lang_selected(lang_code)
                break

    def update_language(self):
        self.header_label.text = get_text('language', 'Язык')

    def update_visuals(self, active_theme):
        self.current_theme = active_theme
        self.md_bg_color = SettingsPalette.get_card_bg(active_theme)
        self.line_color = SettingsPalette.get_card_line(active_theme)
        self.line_width = SettingsPalette.get_card_line_width()
        self.picker_bg_color.rgba = SettingsPalette.get_inner_bg(active_theme)
        self.picker_line_color.rgba = SettingsPalette.get_inner_line(active_theme)

        accent = SettingsPalette.get_accent(active_theme)
        self.header_icon.text_color = accent
        self.header_label.text_color = SettingsPalette.get_text_primary(active_theme)
        self.left_btn.icon_color = accent
        self.right_btn.icon_color = accent

        primary_text = SettingsPalette.get_text_primary(active_theme)
        for lbl in self.title_labels:
            lbl.text_color = primary_text


# ============ ГЛАВНЫЙ ЭКРАН НАСТРОЕК ============
class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_theme = settings_state.theme
        self.bg_color_inst = None
        self.bg_rect = None
        self.texture = None
        self.theme_card = None
        self.avatar_card = None
        self.lang_card = None
        self.load_background()
        self.init_ui()
        logger.info("SettingsScreen создан в единой стилистике приложения")

    def load_background(self):
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        try:
            if HAS_ASSETS:
                bg_data = load_asset_as_bytes("background_jpg")
                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")
                    self.texture = img.texture
        except Exception as e:
            logger.error(f"Ошибка загрузки фона: {e}")
        self.update_screen_background()

    def _update_rect(self, *args):
        if self.bg_rect:
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def update_screen_background(self):
        if not self.bg_color_inst or not self.bg_rect:
            return
        theme_id = settings_state.theme
        if theme_id == 'green':
            if self.texture:
                self.bg_rect.texture = self.texture
                self.bg_color_inst.rgba = (1, 1, 1, 1)
            else:
                self.bg_rect.texture = None
                self.bg_color_inst.rgba = (0.1, 0.3, 0.2, 1)
        elif theme_id == 'dark':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.07, 0.07, 0.07, 1)
        elif theme_id == 'light':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.969, 0.976, 0.969, 1)

    def init_ui(self):
        top_offset = layout_config.get_top_nav_height()
        bottom_offset = layout_config.get_bottom_nav_total_height()

        root_box = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=dp(10),
            padding=[dp(16), top_offset + dp(12), dp(16), bottom_offset + dp(10)],
        )

        # 1. Карточка тем (3 отдельные карточки с отцентрированными иконками)
        self.theme_card = ModernThemeCard(
            current_theme=self.current_theme,
            on_theme_selected=self._on_theme_selected,
        )
        root_box.add_widget(self.theme_card)

        # 2. Карточка выбора аватара
        self.avatar_card = ModernAvatarCard(
            current_avatar=settings_state.avatar,
            current_theme=self.current_theme,
            on_avatar_selected=self._on_avatar_selected,
        )
        root_box.add_widget(self.avatar_card)

        # 3. Карточка выбора языка
        self.lang_card = ModernLanguageCard(
            current_lang=settings_state.language,
            current_theme=self.current_theme,
            on_lang_selected=self._on_language_selected,
        )
        root_box.add_widget(self.lang_card)

        # Свободное пространство снизу
        root_box.add_widget(Widget(size_hint_y=1))
        self.add_widget(root_box)

    def _on_theme_selected(self, theme_id):
        if theme_id == self.current_theme:
            return
        logger.info(f"🎨 Выбрана тема: {theme_id}")
        self.current_theme = theme_id
        settings_state.set_theme(theme_id)
        self.refresh_theme_colors()

        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_theme'):
            app.apply_theme(theme_id)

    def _on_avatar_selected(self, avatar_name):
        logger.info(f"🖼️ Выбран аватар: {avatar_name}")
        settings_state.set_avatar(avatar_name)

    def _on_language_selected(self, lang_code):
        if lang_code == settings_state.language:
            return
        logger.info(f"🌐 Выбран язык: {lang_code}")
        settings_state.set_language(lang_code)
        self.update_language()

        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_language'):
            app.apply_language(lang_code)

    def update_language(self):
        if self.theme_card:
            self.theme_card.update_language()
        if self.avatar_card:
            self.avatar_card.update_language()
        if self.lang_card:
            self.lang_card.update_language()

    def on_enter(self):
        super().on_enter()
        self.current_theme = settings_state.theme

        if self.avatar_card:
            self.avatar_card.set_current(settings_state.avatar, animate=False)
        if self.lang_card:
            self.lang_card.set_current(settings_state.language, animate=False)

        self.update_language()
        self.refresh_theme_colors()

        app = MDApp.get_running_app()
        if app and hasattr(app, 'top_nav') and app.top_nav:
            app.top_nav.set_custom_back_callback(self.go_back)

    def refresh_theme_colors(self):
        self.update_screen_background()
        if self.theme_card:
            self.theme_card.update_visuals(self.current_theme)
        if self.avatar_card:
            self.avatar_card.update_visuals(self.current_theme)
        if self.lang_card:
            self.lang_card.update_visuals(self.current_theme)

    def go_back(self):
        if self.manager:
            self.manager.current = 'home'