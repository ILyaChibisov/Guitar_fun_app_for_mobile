# screens/settings_screen.py
"""
Экран настроек с выбором темы и языка.
6 языков, карточки в сетке 2x3.

Быстрая смена темы/языка:
  - settings_state.set_* — асинхронная запись файла (без fsync);
  - app.apply_theme/apply_language — только hot-панели + текущий экран;
  - остальные экраны подхватят изменения сами в on_enter (BaseScreen).
"""
import os
import json
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from io import BytesIO

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton

from config.logger_config import screen_logger
from screens.base_screen import BaseScreen
from state.settings_state import settings_state
from utils.localization import get_text

logger = screen_logger('Settings')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


# ============ КЭШ ФЛАГОВ ============
_flag_textures_cache = {}


def load_flag_texture(asset_name):
    """Загружает и кэширует текстуру флага по имени ассета."""
    if asset_name in _flag_textures_cache:
        return _flag_textures_cache[asset_name]

    if not HAS_ASSETS:
        return None

    try:
        data = load_asset_as_bytes(asset_name)
        if data:
            img = CoreImage(BytesIO(data), ext="png")
            _flag_textures_cache[asset_name] = img.texture
            return img.texture
    except Exception as e:
        logger.error(f"Ошибка загрузки флага {asset_name}: {e}")

    return None


# ============================================================
# ЦВЕТА
# ============================================================

class ThemeColors:
    GOLD_ACCENT = [0.8, 0.55, 0.1, 1]

    @staticmethod
    def get_text_secondary(theme_id):
        if theme_id in ('dark', 'green'):
            return [1, 1, 1, 0.9]
        elif theme_id == 'light':
            return [0.35, 0.35, 0.35, 1]
        return [1, 1, 1, 0.9]

    @staticmethod
    def get_accent(theme_id):
        if theme_id == 'light':
            return [0.1, 0.55, 0.3, 1]  # Яркий изумрудный
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]  # Оранжевый
        elif theme_id == 'green':
            return [1, 1, 1, 1]
        else:
            return [0.46, 0.70, 0.71, 1]

    @staticmethod
    def get_card_bg(theme_id):
        if theme_id == 'light':
            return [1, 1, 1, 0.9]
        elif theme_id == 'dark':
            return [1, 1, 1, 0.05]
        else:
            return [1, 1, 1, 0.04]

    @staticmethod
    def get_divider(theme_id):
        if theme_id == 'light':
            return [0, 0, 0, 0.05]
        else:
            return [1, 1, 1, 0.08]


# ============================================================
# ОПЦИЯ ТЕМЫ
# ============================================================

class ThemeOption(MDCard):
    def __init__(self, theme_id, icon_name, label, current_theme_id, is_active=False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.theme_id = theme_id
        self.current_theme_id = current_theme_id
        self.is_active = is_active
        self.on_select_callback = on_select

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.ripple_behavior = False
        self.padding = [0, dp(6), 0, dp(6)]
        self.spacing = dp(2)
        self.radius = [dp(10)]

        self.icon_btn = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_x': 0.5},
            theme_icon_color="Custom",
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0
        )
        self.icon_btn.bind(on_release=self._on_press)

        self.label = MDLabel(
            text=label,
            font_size=sp(12),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(18),
        )

        self.add_widget(self.icon_btn)
        self.add_widget(self.label)

        self.bind(on_release=self._on_press)
        self.bind(on_touch_down=self._on_touch_down_feedback)
        self.update_colors()

    def _on_press(self, *args):
        if self.on_select_callback:
            self.on_select_callback(self.theme_id)

    def _on_touch_down_feedback(self, instance, touch):
        """Мгновенная визуальная реакция на касание — до тяжёлой смены темы."""
        if not self.collide_point(*touch.pos):
            return False
        accent = ThemeColors.get_accent(self.theme_id)
        self.md_bg_color = [*accent[:3], 0.15] if self.theme_id != 'green' else [1, 1, 1, 0.15]
        self.icon_btn.icon_color = accent
        self.label.text_color = accent
        self.label.bold = True
        return False

    def update_colors(self):
        accent = ThemeColors.get_accent(self.current_theme_id)
        text_secondary = ThemeColors.get_text_secondary(self.current_theme_id)

        self.icon_btn.theme_icon_color = "Custom"
        self.label.theme_text_color = "Custom"

        if self.is_active:
            self.md_bg_color = [*accent[:3], 0.15] if self.current_theme_id != 'green' else [1, 1, 1, 0.15]
            self.icon_btn.icon_color = accent
            self.label.text_color = accent
            self.label.bold = True
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.icon_btn.icon_color = text_secondary
            self.label.text_color = text_secondary
            self.label.bold = False

    def set_active(self, active):
        self.is_active = active
        self.update_colors()


# ============================================================
# СЕЛЕКТОР ТЕМЫ
# ============================================================

class ThemeSelector(MDCard):
    def __init__(self, current_theme='green', on_theme_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.ripple_behavior = False
        self.current_theme = current_theme
        self.on_theme_selected = on_theme_selected

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(76)
        self.radius = [dp(14)]
        self.elevation = 0
        self.line_width = 1
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = 0

        self.options = []
        themes = [
            ('green', 'palette', get_text('theme_green', 'Зелёная')),
            ('light', 'white-balance-sunny', get_text('theme_light', 'Светлая')),
            ('dark', 'weather-night', get_text('theme_dark', 'Тёмная')),
        ]

        self.dividers = []

        for i, (theme_id, icon, label) in enumerate(themes):
            option = ThemeOption(
                theme_id=theme_id,
                icon_name=icon,
                label=label,
                current_theme_id=self.current_theme,
                is_active=(theme_id == current_theme),
                on_select=self._on_option_selected,
            )
            self.options.append(option)
            self.add_widget(option)

            if i < len(themes) - 1:
                div = MDBoxLayout(
                    size_hint_x=None,
                    width=dp(1),
                    md_bg_color=[0, 0, 0, 0]
                )
                self.dividers.append(div)
                self.add_widget(div)

        self.update_colors()

    def update_colors(self):
        bg = ThemeColors.get_card_bg(self.current_theme)
        divider_color = ThemeColors.get_divider(self.current_theme)

        self.md_bg_color = bg
        self.line_color = divider_color

        for div in self.dividers:
            div.md_bg_color = divider_color

        for option in self.options:
            option.current_theme_id = self.current_theme
            option.update_colors()

    def update_language(self):
        """Обновляет подписи тем при смене языка."""
        labels = {
            'green': get_text('theme_green', 'Зелёная'),
            'light': get_text('theme_light', 'Светлая'),
            'dark': get_text('theme_dark', 'Тёмная'),
        }
        for option in self.options:
            new_text = labels.get(option.theme_id)
            if new_text is not None and option.label.text != new_text:
                option.label.text = new_text

    def _on_option_selected(self, theme_id):
        if theme_id == self.current_theme:
            return
        self.current_theme = theme_id
        for option in self.options:
            option.set_active(option.theme_id == theme_id)
        if self.on_theme_selected:
            self.on_theme_selected(theme_id)


# ============================================================
# ОПЦИЯ ЯЗЫКА
# ============================================================

class LanguageOption(ButtonBehavior, MDBoxLayout):
    def __init__(self, lang_code, lang_text, asset_name, current_theme_id, is_active=False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        if hasattr(self, 'ripple_behavior'):
            self.ripple_behavior = False

        self.lang_code = lang_code
        self.current_theme_id = current_theme_id
        self._is_active = is_active
        self.on_select_callback = on_select
        self.asset_name = asset_name

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.height = dp(76)
        self.md_bg_color = [0, 0, 0, 0]
        self.padding = [0, dp(6), 0, dp(6)]
        self.spacing = dp(2)
        self.radius = [dp(10)]

        self.icon_container = MDBoxLayout(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_x': 0.5},
            md_bg_color=[0, 0, 0, 0]
        )

        self.flag_image = Image(
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True
        )

        texture = load_flag_texture(asset_name)
        if texture:
            self.flag_image.texture = texture
        else:
            self.flag_image.source = ''

        self.icon_container.add_widget(self.flag_image)
        self.add_widget(self.icon_container)

        self.label = MDLabel(
            text=lang_text,
            font_size=sp(12),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(18),
        )
        self.add_widget(self.label)

        self.bind(pos=self._update_bg, size=self._update_bg)
        self.update_colors()

    def on_release(self):
        if self.on_select_callback:
            self.on_select_callback(self.lang_code)

    def update_colors(self):
        accent = ThemeColors.get_accent(self.current_theme_id)
        text_secondary = ThemeColors.get_text_secondary(self.current_theme_id)

        self.label.theme_text_color = "Custom"
        self.canvas.before.clear()

        if self._is_active:
            with self.canvas.before:
                if self.current_theme_id == 'green':
                    Color(1, 1, 1, 0.15)
                else:
                    Color(*accent[:3], 0.15)
                self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            self.label.text_color = accent
            self.label.bold = True
            self.icon_container.opacity = 1
        else:
            self.label.text_color = text_secondary
            self.label.bold = False
            self.icon_container.opacity = 0.7

    def _update_bg(self, *args):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def set_active(self, active):
        self._is_active = active
        self.update_colors()


# ============================================================
# СЕЛЕКТОР ЯЗЫКА (СЕТКА 2x3)
# ============================================================

class LanguageSelector(MDGridLayout):
    def __init__(self, current_lang=None, current_theme='green', on_lang_selected=None, **kwargs):
        super().__init__(**kwargs)

        if current_lang is None:
            current_lang = settings_state.language

        self.current_lang = current_lang
        self.current_theme = current_theme
        self.on_lang_selected = on_lang_selected

        self.cols = 2
        self.size_hint = (1, None)
        self.adaptive_height = True
        self.spacing = dp(8)
        self.padding = [0, 0, 0, 0]

        self.options = []
        self.dividers = []

        languages = [
            ('ru', 'Русский', 'rus_png'),
            ('en', 'English', 'eng_png'),
            ('fr', 'Français', 'fra_png'),
            ('it', 'Italiano', 'ita_png'),
            ('es', 'Español', 'spa_png'),
            ('pt', 'Português', 'por_png'),
        ]

        for lang_code, lang_text, asset_name in languages:
            option = LanguageOption(
                lang_code=lang_code,
                lang_text=lang_text,
                asset_name=asset_name,
                current_theme_id=self.current_theme,
                is_active=(lang_code == self.current_lang),
                on_select=self._on_option_selected,
            )
            self.options.append(option)
            self.add_widget(option)

        self.update_colors()

    def update_colors(self):
        for option in self.options:
            option.current_theme_id = self.current_theme
            option.update_colors()

    def _on_option_selected(self, lang_code):
        logger.info(f"📥 _on_option_selected получил: {lang_code}")
        for option in self.options:
            option.set_active(option.lang_code == lang_code)

        if self.on_lang_selected:
            self.on_lang_selected(lang_code)


# ============================================================
# ЭКРАН НАСТРОЕК
# ============================================================

class SettingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        self.bg_image = None
        self.bg_color_inst = None

        self.current_theme = settings_state.theme

        self.theme_selector = None
        self.lang_selector = None
        self.section_headers = []

        self.init_ui()
        self.load_background()

    def load_background(self):
        with self.canvas.before:
            self.bg_color_inst = Color(0, 0, 0, 0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

        try:
            if HAS_ASSETS:
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        break
                if bg_data:
                    img = CoreImage(BytesIO(bg_data), ext="jpg")
                    self.texture = img.texture
                    self.update_screen_background()
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

        self.update_screen_background()

    def _update_rect(self, *args):
        if hasattr(self, 'bg_rect') and self.bg_rect:
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def update_screen_background(self):
        if not self.bg_color_inst:
            return

        if self.current_theme == 'green':
            if hasattr(self, 'texture') and self.texture:
                self.bg_rect.texture = self.texture
                self.bg_color_inst.rgba = (1, 1, 1, 1)
            else:
                self.bg_rect.texture = None
                self.bg_color_inst.rgba = (0.1, 0.3, 0.2, 1)
        elif self.current_theme == 'dark':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.07, 0.07, 0.07, 1)
        elif self.current_theme == 'light':
            self.bg_rect.texture = None
            self.bg_color_inst.rgba = (0.969, 0.976, 0.969, 1)

    def init_ui(self):
        self.content_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(12), dp(16), dp(24)],
        )

        # === ТЕМА ===
        self.section_headers.append(self._section_header("THEME / ТЕМА"))
        self.content_layout.add_widget(self.section_headers[-1])

        self.theme_selector = ThemeSelector(
            current_theme=self.current_theme,
            on_theme_selected=self._on_theme_selected,
        )
        self.content_layout.add_widget(self.theme_selector)

        self.content_layout.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # === ЯЗЫК ===
        self.section_headers.append(self._section_header("LANGUAGE / ЯЗЫК"))
        self.content_layout.add_widget(self.section_headers[-1])

        self.lang_selector = LanguageSelector(
            current_theme=self.current_theme,
            on_lang_selected=self._on_language_selected,
        )
        self.content_layout.add_widget(self.lang_selector)

        self.content_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self.build_ui(content_widget=self.content_layout, use_scroll=True)

    def _section_header(self, text):
        header = MDLabel(
            text=text,
            font_size=sp(12),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=ThemeColors.get_accent(self.current_theme),
            bold=True,
            padding=[dp(4), 0, 0, 0],
        )
        header.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0] - dp(8), val[1])))
        return header

    def refresh_theme_colors(self):
        accent = ThemeColors.get_accent(self.current_theme)

        for header in self.section_headers:
            header.text_color = accent

        self.theme_selector.current_theme = self.current_theme
        self.theme_selector.update_colors()

        current_lang = settings_state.language
        self.lang_selector.current_theme = self.current_theme
        self.lang_selector.current_lang = current_lang
        self.lang_selector.update_colors()

        for option in self.lang_selector.options:
            option.set_active(option.lang_code == current_lang)

        self.update_screen_background()

    def update_language(self):
        """Обновляет подписи экрана при смене языка."""
        logger.info("🌐 SettingsScreen: обновление языка")
        if self.theme_selector:
            self.theme_selector.update_language()

    def _on_theme_selected(self, theme_id):
        if theme_id == self.current_theme:
            return

        self.current_theme = theme_id

        # 1) Состояние: файл запишется сам через 0.3 с (без fsync).
        settings_state.set_theme(theme_id)

        # 2) Мгновенно: hot-панели + текущий экран (это settings).
        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_theme'):
            app.apply_theme(theme_id)

        # 3) Локальный перекрас экрана настроек.
        self.refresh_theme_colors()

        # 4) Отмечаем применённую версию для BaseScreen.
        self._applied_theme_version = settings_state.theme_version

    def _on_language_selected(self, lang_code):
        if lang_code == settings_state.language:
            return

        logger.info(f"🌐 Выбран язык: {lang_code}")

        # 1) Состояние (файл — асинхронно).
        settings_state.set_language(lang_code)

        # 2) Мгновенно: hot-панели + текущий экран.
        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_language'):
            app.apply_language(lang_code)

        # 3) Локально: подписи тем в карточках.
        if self.theme_selector:
            self.theme_selector.update_language()

        self._applied_language_version = settings_state.language_version

    def on_enter(self):
        # Базовый вход: layout + ленивая синхронизация
        super().on_enter()

        self.current_theme = settings_state.theme
        current_lang = settings_state.language

        self.lang_selector.current_lang = current_lang
        self.lang_selector.update_colors()
        for option in self.lang_selector.options:
            option.set_active(option.lang_code == current_lang)

        self.refresh_theme_colors()

    def go_back(self, instance=None):
        if hasattr(self, 'manager') and self.manager:
            prev = getattr(self, '_return_screen', None)
            if prev and self.manager.has_screen(prev):
                self.manager.current = prev
            else:
                self.manager.current = 'home'