# screens/settings_screen.py
"""
Экран настроек с выбором темы и языка.
Мгновенно применяет тему глобально и сохраняет всё в JSON.
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from io import BytesIO

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton

from config.logger_config import screen_logger
from screens.base_screen import BaseScreen
from utils.settings_manager import settings_manager

logger = screen_logger('Settings')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


# ============================================================
# ОПЦИЯ ТЕМЫ
# ============================================================

class ThemeOption(MDCard):
    def __init__(self, theme_id, icon_name, label, is_active=False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.theme_id = theme_id
        self.is_active = is_active
        self.on_select_callback = on_select

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.ripple_behavior = True
        self.padding = [0, dp(6), 0, dp(6)]
        self.spacing = dp(2)
        self.radius = [dp(10)]

        icon_color = [0.46, 0.70, 0.71, 1] if is_active else [1, 1, 1, 0.9]

        self.icon_btn = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_x': 0.5},
            theme_icon_color="Custom",
            icon_color=icon_color,
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0
        )
        self.icon_btn.bind(on_release=self._on_press)

        self.label = MDLabel(
            text=label,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1] if is_active else [1, 1, 1, 0.8],
            bold=is_active,
            size_hint_y=None,
            height=dp(18),
        )

        self.add_widget(self.icon_btn)
        self.add_widget(self.label)

        self.bind(on_release=self._on_press)
        self.update_state()

    def _on_press(self, *args):
        if self.on_select_callback:
            self.on_select_callback(self.theme_id)

    def set_active(self, active):
        self.is_active = active
        self.update_state()

    def update_state(self):
        if self.is_active:
            self.md_bg_color = [0.46, 0.70, 0.71, 0.15]
            self.icon_btn.icon_color = [0.46, 0.70, 0.71, 1]
            self.label.text_color = [0.46, 0.70, 0.71, 1]
            self.label.bold = True
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.icon_btn.icon_color = [1, 1, 1, 0.9]
            self.label.text_color = [1, 1, 1, 0.8]
            self.label.bold = False


# ============================================================
# СЕЛЕКТОР ТЕМЫ
# ============================================================

class ThemeSelector(MDCard):
    def __init__(self, current_theme='green', on_theme_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.current_theme = current_theme
        self.on_theme_selected = on_theme_selected

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(76)
        self.radius = [dp(14)]
        self.md_bg_color = [1, 1, 1, 0.04]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.08]
        self.line_width = 1
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = 0

        self.options = []
        themes = [
            ('green', 'palette', 'Зелёная'),
            ('light', 'white-balance-sunny', 'Светлая'),
            ('dark', 'weather-night', 'Тёмная'),
        ]

        for i, (theme_id, icon, label) in enumerate(themes):
            option = ThemeOption(
                theme_id=theme_id,
                icon_name=icon,
                label=label,
                is_active=(theme_id == current_theme),
                on_select=self._on_option_selected,
            )
            self.options.append(option)
            self.add_widget(option)

            if i < len(themes) - 1:
                divider = MDBoxLayout(
                    size_hint_x=None,
                    width=dp(1),
                    md_bg_color=[1, 1, 1, 0.08],
                )
                self.add_widget(divider)

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

class LanguageOption(MDCard):
    def __init__(self, lang_code, lang_text, icon_name, is_active=False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.lang_code = lang_code
        self.is_active = is_active
        self.on_select_callback = on_select

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.md_bg_color = [0, 0, 0, 0]
        self.elevation = 0
        self.ripple_behavior = True
        self.padding = [0, dp(6), 0, dp(6)]
        self.spacing = dp(2)
        self.radius = [dp(10)]

        icon_color = [0.46, 0.70, 0.71, 1] if is_active else [1, 1, 1, 0.9]

        self.icon_btn = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_x': 0.5},
            theme_icon_color="Custom",
            icon_color=icon_color,
            md_bg_color=[0, 0, 0, 0],
            ripple_scale=0
        )
        self.icon_btn.bind(on_release=self._on_press)

        self.label = MDLabel(
            text=lang_text,
            font_size=sp(12),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1] if is_active else [1, 1, 1, 0.8],
            bold=is_active,
            size_hint_y=None,
            height=dp(18),
        )

        self.add_widget(self.icon_btn)
        self.add_widget(self.label)

        self.bind(on_release=self._on_press)
        self.update_state()

    def _on_press(self, *args):
        if self.on_select_callback:
            self.on_select_callback(self.lang_code)

    def set_active(self, active):
        self.is_active = active
        self.update_state()

    def update_state(self):
        if self.is_active:
            self.md_bg_color = [0.46, 0.70, 0.71, 0.15]
            self.icon_btn.icon_color = [0.46, 0.70, 0.71, 1]
            self.label.text_color = [0.46, 0.70, 0.71, 1]
            self.label.bold = True
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.icon_btn.icon_color = [1, 1, 1, 0.9]
            self.label.text_color = [1, 1, 1, 0.8]
            self.label.bold = False


# ============================================================
# СЕЛЕКТОР ЯЗЫКА
# ============================================================

class LanguageSelector(MDCard):
    def __init__(self, current_lang='ru', on_lang_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.current_lang = current_lang
        self.on_lang_selected = on_lang_selected

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(76)
        self.radius = [dp(14)]
        self.md_bg_color = [1, 1, 1, 0.04]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.08]
        self.line_width = 1
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = 0

        self.options = []

        languages = [
            ('ru', 'Русский', 'alpha-r-circle'),
            ('en', 'English', 'alpha-e-circle'),
        ]

        for i, (lang_code, lang_text, icon_name) in enumerate(languages):
            option = LanguageOption(
                lang_code=lang_code,
                lang_text=lang_text,
                icon_name=icon_name,
                is_active=(lang_code == current_lang),
                on_select=self._on_option_selected,
            )
            self.options.append(option)
            self.add_widget(option)

            if i < len(languages) - 1:
                divider = MDBoxLayout(
                    size_hint_x=None,
                    width=dp(1),
                    md_bg_color=[1, 1, 1, 0.08],
                )
                self.add_widget(divider)

    def _on_option_selected(self, lang_code):
        if lang_code == self.current_lang:
            return
        self.current_lang = lang_code
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

        # Берем текущие настройки из менеджера
        self.current_theme = settings_manager.theme
        self.current_language = settings_manager.language

        self.theme_selector = None
        self.lang_selector = None

        self.init_ui()
        self.load_background()

    def load_background(self):
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
                    with self.canvas.before:
                        Color(1, 1, 1, 1)
                        self.bg_image = Rectangle(texture=img.texture, pos=self.pos, size=self.size)
                    self.bind(pos=self._update_bg, size=self._update_bg)
                    return
        except Exception as e:
            logger.error(f'Ошибка загрузки фона: {e}')

    def _update_bg(self, *args):
        if self.bg_image:
            self.bg_image.pos = self.pos
            self.bg_image.size = self.size

    def init_ui(self):
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(8),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(12), dp(16), dp(24)],
        )

        # === ТЕМА ===
        content.add_widget(self._section_header("ТЕМА"))
        self.theme_selector = ThemeSelector(
            current_theme=self.current_theme,
            on_theme_selected=self._on_theme_selected,
        )
        content.add_widget(self.theme_selector)

        content.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # === ЯЗЫК ===
        content.add_widget(self._section_header("ЯЗЫК"))
        self.lang_selector = LanguageSelector(
            current_lang=self.current_language,
            on_lang_selected=self._on_language_selected,
        )
        content.add_widget(self.lang_selector)

        content.add_widget(Widget(size_hint_y=None, height=dp(8)))

        self.build_ui(content_widget=content, use_scroll=True)

    def _section_header(self, text):
        header = MDLabel(
            text=text,
            font_size=sp(12),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 0.9],
            bold=True,
            padding=[dp(4), 0, 0, 0],
        )
        header.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0] - dp(8), val[1])))
        return header

    def _on_theme_selected(self, theme_id):
        logger.info(f"Выбрана тема: {theme_id}")
        self.current_theme = theme_id

        # Мгновенное глобальное применение
        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_theme'):
            app.apply_theme(theme_id)
        else:
            settings_manager.set_theme(theme_id)

    def _on_language_selected(self, lang_code):
        logger.info(f"Выбран язык: {lang_code}")
        self.current_language = lang_code
        settings_manager.set_language(lang_code)

    def on_enter(self):
        logger.info("🚪 Вход в экран настроек")

    def go_back(self, instance=None):
        logger.info("🔙 Возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'