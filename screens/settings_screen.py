# screens/settings_screen.py
"""
Экран настроек с выбором темы и языка.
Единственный источник правды — JSON-файл.
Устранена проблема перекрытия кнопок языка.
"""
import os
import json
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from io import BytesIO

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton

from config.logger_config import screen_logger
from screens.base_screen import BaseScreen
from utils.settings_manager import settings_manager
from config.app_config import config

logger = screen_logger('Settings')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# ============ ПУТЬ К ФАЙЛУ ============
_SETTINGS_FILE = os.path.join(config.CACHE_DIR, 'user_settings.json')


def read_language_from_file():
    """Читает язык из JSON-файла. Принудительно сбрасывает буфер."""
    try:
        if os.path.exists(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                lang = data.get('language', 'ru')
                logger.info(f"📖 read_language_from_file: {lang}")
                return lang
        else:
            default = {"theme": "green", "language": "ru", "is_authenticated": False}
            with open(_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=4)
            logger.info("📖 read_language_from_file: файл создан, язык = ru")
            return 'ru'
    except Exception as e:
        logger.error(f"❌ Ошибка чтения языка: {e}")
        return 'ru'


def write_language_to_file(lang_code):
    """Записывает язык в JSON-файл с принудительным сбросом на диск."""
    try:
        data = {}
        if os.path.exists(_SETTINGS_FILE):
            with open(_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data['language'] = lang_code
        with open(_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        logger.info(f"💾 write_language_to_file: {lang_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка записи языка: {e}")


# ============ ЗАГРУЗКА ФЛАГОВ ============
_shared_rus_flag_texture = None
_shared_eng_flag_texture = None


def load_flags_sync():
    global _shared_rus_flag_texture, _shared_eng_flag_texture
    if _shared_rus_flag_texture is not None:
        return
    if HAS_ASSETS:
        try:
            rus_data = load_asset_as_bytes('rus_png')
            if rus_data:
                img = CoreImage(BytesIO(rus_data), ext="png")
                _shared_rus_flag_texture = img.texture
            eng_data = load_asset_as_bytes('eng_png')
            if eng_data:
                img = CoreImage(BytesIO(eng_data), ext="png")
                _shared_eng_flag_texture = img.texture
        except Exception as e:
            logger.error(f"Ошибка загрузки флагов: {e}")


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
            return [0.1, 0.55, 0.3, 1]  # <--- Яркий насыщенный изумрудный
        elif theme_id == 'dark':
            return [1.0, 0.5, 0.0, 1]   # <--- Оранжевый
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
        self.ripple_behavior = True
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
        self.update_colors()

    def _on_press(self, *args):
        if self.on_select_callback:
            self.on_select_callback(self.theme_id)

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
            ('green', 'palette', 'Зелёная'),
            ('light', 'white-balance-sunny', 'Светлая'),
            ('dark', 'weather-night', 'Тёмная'),
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

    def _on_option_selected(self, theme_id):
        if theme_id == self.current_theme:
            return
        self.current_theme = theme_id
        for option in self.options:
            option.set_active(option.theme_id == theme_id)
        if self.on_theme_selected:
            self.on_theme_selected(theme_id)


# ============================================================
# ОПЦИЯ ЯЗЫКА (БЕЗ ПЕРЕКРЫТИЯ)
# ============================================================

class LanguageOption(ButtonBehavior, MDBoxLayout):
    """Опция языка. Используем BoxLayout вместо MDCard, чтобы избежать перекрытий."""

    def __init__(self, lang_code, lang_text, current_theme_id, is_active=False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.lang_code = lang_code
        self.current_theme_id = current_theme_id
        self._is_active = is_active
        self.on_select_callback = on_select

        self.orientation = 'vertical'
        self.size_hint = (0.5, 1)
        self.md_bg_color = [0, 0, 0, 0]
        self.padding = [0, dp(6), 0, dp(6)]
        self.spacing = dp(2)
        self.radius = [dp(10)]

        # Контейнер для флага
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
        if lang_code == 'ru' and _shared_rus_flag_texture:
            self.flag_image.texture = _shared_rus_flag_texture
        elif lang_code == 'en' and _shared_eng_flag_texture:
            self.flag_image.texture = _shared_eng_flag_texture
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
        logger.info(f"🖱️ НАЖАТА ОПЦИЯ: {self.lang_code}")
        if self.on_select_callback:
            self.on_select_callback(self.lang_code)

    def update_colors(self):
        accent = ThemeColors.get_accent(self.current_theme_id)
        text_secondary = ThemeColors.get_text_secondary(self.current_theme_id)

        self.label.theme_text_color = "Custom"

        # Очищаем старый фон
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
# СЕЛЕКТОР ЯЗЫКА
# ============================================================

class LanguageSelector(MDCard):
    def __init__(self, current_lang=None, current_theme='green', on_lang_selected=None, **kwargs):
        super().__init__(**kwargs)

        if current_lang is None:
            current_lang = read_language_from_file()

        self.current_lang = current_lang
        logger.info(f"📥 LanguageSelector создан с языком: {self.current_lang}")

        self.current_theme = current_theme
        self.on_lang_selected = on_lang_selected

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(76)
        self.radius = [dp(14)]
        self.elevation = 0
        self.line_width = 1
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(8)  # Увеличен отступ

        self.options = []
        self.dividers = []

        languages = [
            ('en', 'English'),
            ('ru', 'Русский'),
        ]

        for i, (lang_code, lang_text) in enumerate(languages):
            option = LanguageOption(
                lang_code=lang_code,
                lang_text=lang_text,
                current_theme_id=self.current_theme,
                is_active=(lang_code == self.current_lang),
                on_select=self._on_option_selected,
            )
            self.options.append(option)
            self.add_widget(option)

            if i < len(languages) - 1:
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

        load_flags_sync()

        self.current_theme = settings_manager.theme

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
            self.bg_color_inst.rgba = (0.07, 0.07, 0.07, 1)  # #121212
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

        # Читаем язык из файла
        current_lang = read_language_from_file()
        logger.info(f"🔄 refresh_theme_colors: язык из файла = {current_lang}")

        self.lang_selector.current_theme = self.current_theme
        self.lang_selector.current_lang = current_lang
        self.lang_selector.update_colors()

        for option in self.lang_selector.options:
            option.set_active(option.lang_code == current_lang)

        self.update_screen_background()

    def _on_theme_selected(self, theme_id):
        logger.info(f"Выбрана тема: {theme_id}")
        self.current_theme = theme_id
        settings_manager.set_theme(theme_id)

        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_theme'):
            app.apply_theme(theme_id)

        self.refresh_theme_colors()

    def _on_language_selected(self, lang_code):
        logger.info(f"🎯 _on_language_selected: {lang_code}")
        write_language_to_file(lang_code)
        settings_manager.set_language(lang_code)

        app = MDApp.get_running_app()
        if app and hasattr(app, 'apply_language'):
            app.apply_language(lang_code)

    def on_enter(self):
        logger.info("🚪 Вход в экран настроек")
        self.current_theme = settings_manager.theme

        current_lang = read_language_from_file()
        logger.info(f"📥 on_enter: язык из файла = {current_lang}")

        self.lang_selector.current_lang = current_lang
        self.lang_selector.update_colors()
        for option in self.lang_selector.options:
            option.set_active(option.lang_code == current_lang)

        self.refresh_theme_colors()

    def go_back(self, instance=None):
        logger.info("🔙 Возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'