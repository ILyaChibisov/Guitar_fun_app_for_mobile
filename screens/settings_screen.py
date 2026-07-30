# screens/settings_screen.py
"""
Экран настроек с выбором темы и языка (красивый UI, пока без функционала)
"""
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from io import BytesIO

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.app import MDApp

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen

logger = screen_logger('Settings')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class ThemeOption(MDCard):
    """Одна опция темы в горизонтальной карточке (как в меню аккордов)"""

    def __init__(self, theme_id, icon_name, label, is_active=False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.theme_id = theme_id
        self.is_active = is_active
        self.on_select_callback = on_select

        # Карточка как в меню аккордов — вертикальная, без фона
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.md_bg_color = [0, 0, 0, 0]  # Прозрачный фон
        self.elevation = 0
        self.ripple_behavior = True
        self.padding = [dp(4), dp(4), dp(4), dp(4)]  # Минимальные отступы
        self.spacing = dp(2)

        # Иконка (как в меню аккордов — без фона, цветная)
        self.icon = MDIconButton(
            icon=icon_name,
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_x': 0.5},
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.7] if not is_active else [0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],  # Без серого фона!
            disabled=True
        )

        # Название (как в меню аккордов)
        self.label = MDLabel(
            text=label,
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7] if not is_active else [0.46, 0.70, 0.71, 1],
            bold=True if is_active else False,
            size_hint_y=None,
            height=dp(20)
        )

        self.add_widget(self.icon)
        self.add_widget(self.label)

        self.bind(on_release=self._on_press)
        self.update_state()

    def _on_press(self, instance):
        if self.on_select_callback:
            self.on_select_callback(self.theme_id)

    def set_active(self, active):
        self.is_active = active
        self.update_state()

    def update_state(self):
        if self.is_active:
            self.icon.icon_color = [0.46, 0.70, 0.71, 1]
            self.label.text_color = [0.46, 0.70, 0.71, 1]
            self.label.bold = True
            self.md_bg_color = [0.46, 0.70, 0.71, 0.15]  # Лёгкая подсветка фона
            self.radius = [dp(8)]
        else:
            self.icon.icon_color = [1, 1, 1, 0.7]
            self.label.text_color = [1, 1, 1, 0.7]
            self.label.bold = False
            self.md_bg_color = [0, 0, 0, 0]
            self.radius = [0]


class ThemeSelector(MDCard):
    """Горизонтальная карточка выбора темы (как меню аккордов)"""

    def __init__(self, current_theme='green', on_theme_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.current_theme = current_theme
        self.on_theme_selected = on_theme_selected

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)  # Чуть меньше, чтобы влезло
        self.radius = [dp(16)]
        self.md_bg_color = [0, 0, 0, 0.08]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.8
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = 0

        self.options = []

        # Три варианта темы
        themes = [
            ('green', 'weather-sunny', 'Зелёная'),
            ('light', 'white-balance-sunny', 'Светлая'),
            ('dark', 'weather-night', 'Тёмная'),
        ]

        for i, (theme_id, icon, label) in enumerate(themes):
            option = ThemeOption(
                theme_id=theme_id,
                icon_name=icon,
                label=label,
                is_active=(theme_id == current_theme),
                on_select=self._on_option_selected
            )
            self.options.append(option)
            self.add_widget(option)

            # Разделитель между опциями (кроме последней)
            if i < len(themes) - 1:
                divider = MDBoxLayout(
                    size_hint_x=None,
                    width=dp(1),
                    md_bg_color=[1, 1, 1, 0.1]
                )
                self.add_widget(divider)

    def _on_option_selected(self, theme_id):
        if theme_id == self.current_theme:
            return

        self.current_theme = theme_id

        # Обновляем состояние всех опций
        for option in self.options:
            option.set_active(option.theme_id == theme_id)

        if self.on_theme_selected:
            self.on_theme_selected(theme_id)

    def set_current(self, theme_id):
        if theme_id == self.current_theme:
            return
        self.current_theme = theme_id
        for option in self.options:
            option.set_active(option.theme_id == theme_id)


class LanguageCard(MDCard):
    """Карточка выбора языка с флагом и названием"""

    def __init__(self, lang_code, lang_name, flag_text, is_active=False, on_select=None, **kwargs):
        super().__init__(**kwargs)
        self.lang_code = lang_code
        self.is_active = is_active
        self.on_select_callback = on_select

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(50)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]
        self.spacing = dp(12)
        self.radius = [dp(12)]
        self.elevation = 2
        self.ripple_behavior = True

        self.md_bg_color = [0, 0, 0, 0.05]
        self.line_color = [0.46, 0.70, 0.71, 0.3]
        self.line_width = 1

        # Флаг (текстовый эмодзи)
        self.flag_label = MDLabel(
            text=flag_text,
            font_size=sp(28),
            halign="center",
            valign="middle",
            size_hint_x=None,
            width=dp(40)
        )

        # Название языка
        self.lang_label = MDLabel(
            text=lang_name,
            font_size=sp(16),
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True,
            valign="middle"
        )

        # Галочка
        self.check_icon = MDIconButton(
            icon="check-circle",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            opacity=1 if is_active else 0
        )

        self.add_widget(self.flag_label)
        self.add_widget(self.lang_label)
        self.add_widget(self.check_icon)

        self.bind(on_release=self._on_press)

    def _on_press(self, instance):
        if self.on_select_callback:
            self.on_select_callback(self.lang_code)

    def set_active(self, active):
        self.is_active = active
        self.check_icon.opacity = 1 if active else 0
        if active:
            self.elevation = 6
            self.line_color = [0.46, 0.70, 0.71, 1]
            self.line_width = 2
        else:
            self.elevation = 2
            self.line_color = [0.46, 0.70, 0.71, 0.2]
            self.line_width = 1


class SettingsScreen(BaseScreen):
    """Экран настроек с выбором темы и языка"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'settings'
        self.bg_image = None

        # Текущие настройки (пока только для UI)
        self.current_theme = 'green'
        self.current_language = 'ru'

        self.lang_cards = []
        self.theme_selector = None

        self.init_ui()
        self.load_background()

        logger.info('Экран настроек создан (с темой и языком)')

    def load_background(self):
        try:
            if HAS_ASSETS:
                asset_names = ["background_jpg", "background", "bg", "BACKGROUND_JPG"]
                bg_data = None
                for name in asset_names:
                    bg_data = load_asset_as_bytes(name)
                    if bg_data:
                        logger.info(f"Фон загружен из ассета: {name}")
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
            spacing=dp(16),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(16), dp(8), dp(16), dp(16)]
        )

        # === РАЗДЕЛ: ТЕМА ===
        section_theme = MDLabel(
            text="ТЕМА",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 0.8],
            bold=True
        )
        content.add_widget(section_theme)

        # Карточка выбора темы (как в меню аккордов)
        self.theme_selector = ThemeSelector(
            current_theme=self.current_theme,
            on_theme_selected=self._on_theme_selected
        )
        content.add_widget(self.theme_selector)

        # === РАЗДЕЛ: ЯЗЫК ===
        section_lang = MDLabel(
            text="ЯЗЫК",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 0.8],
            bold=True
        )
        content.add_widget(section_lang)

        # Список языков
        languages = [
            ('ru', 'Русский', '🇷🇺'),
            ('en', 'English', '🇬🇧'),
            ('de', 'Deutsch', '🇩🇪'),
            ('fr', 'Français', '🇫🇷'),
            ('it', 'Italiano', '🇮🇹'),
            ('pt', 'Português', '🇵🇹'),
            ('zh', '中文', '🇨🇳'),
        ]

        for lang_code, lang_name, flag in languages:
            card = LanguageCard(
                lang_code=lang_code,
                lang_name=lang_name,
                flag_text=flag,
                is_active=(lang_code == self.current_language),
                on_select=self._on_language_selected
            )
            content.add_widget(card)
            self.lang_cards.append(card)

        # === НИЖНИЙ ОТСТУП ===
        content.add_widget(Widget(size_hint_y=None, height=dp(20)))

        self.build_ui(content_widget=content, use_scroll=True)

    def _on_theme_selected(self, theme_id):
        """Обработчик выбора темы (пока только UI)"""
        logger.info(f"Выбрана тема: {theme_id}")
        self.current_theme = theme_id

    def _on_language_selected(self, lang_code):
        """Обработчик выбора языка (пока только UI)"""
        logger.info(f"Выбран язык: {lang_code}")
        self.current_language = lang_code

        # Обновляем галочки
        for card in self.lang_cards:
            card.set_active(card.lang_code == lang_code)

    def on_enter(self):
        logger.info("🚪 Вход в экран настроек")
        # TopNav обновится автоматически через _on_screen_changed

    def go_back(self, instance=None):
        logger.info("🔙 Возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'