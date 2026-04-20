# screens/components/language_selector.py
"""
Компонент выбора языка с флагами
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.core.image import Image as CoreImage
from io import BytesIO

from config.theme import theme
from config.top_nav_config import TopNavConfig
from config.logger_config import get_logger
from utils.kivy_imports import MDBoxLayout, MDIconButton

logger = get_logger('UI')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class LanguageButton(ButtonBehavior, MDBoxLayout):
    """Кнопка выбора языка с флагом"""

    def __init__(self, lang_code, flag_asset, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.lang_code = lang_code
        self.flag_asset = flag_asset
        self.on_press_callback = on_press_callback
        self.is_active = is_active

        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (dp(60), dp(30))
        self.spacing = dp(4)
        self.padding = [dp(4), dp(2), dp(4), dp(2)]

        # Флаг
        self.flag_image = Image(
            size_hint=(None, 1),
            width=dp(20),
            allow_stretch=True,
            keep_ratio=True
        )

        # Название языка
        self.lang_label = Label(
            text=TopNavConfig.LANG_NAMES.get(lang_code, lang_code),
            font_size=sp(8),
            color=theme.TEXT_SECONDARY,
            halign='center',
            valign='middle'
        )

        # Стрелка вниз (используем обычный Label вместо MDIconButton)
        self.arrow = Label(
            text="▼",
            font_size=sp(8),
            color=theme.TEXT_SECONDARY,
            size_hint=(None, 1),
            width=dp(16),
            halign='center',
            valign='middle'
        )

        self.add_widget(self.flag_image)
        self.add_widget(self.lang_label)
        self.add_widget(self.arrow)

        self.bind(on_release=self._on_press)
        self._load_flag()

    def _load_flag(self):
        """Загружает флаг"""
        if HAS_ASSETS and self.flag_asset:
            try:
                flag_data = load_asset_as_bytes(self.flag_asset)
                if flag_data:
                    img = CoreImage(BytesIO(flag_data), ext="png")
                    self.flag_image.texture = img.texture
                    return
            except Exception as e:
                logger.error(f'Ошибка загрузки флага {self.flag_asset}: {e}')

        self.flag_image.text = "🏁"

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.lang_code)


class LanguageSelector(MDBoxLayout):
    """Компонент выбора языка (комбобокс)"""

    def __init__(self, on_language_change=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = TopNavConfig.LANGUAGE_ICON_SIZE
        self.on_language_change = on_language_change
        self.current_lang = TopNavConfig.DEFAULT_LANG
        self.is_open = False

        # Текущая кнопка
        self.current_btn = LanguageButton(
            lang_code=self.current_lang,
            flag_asset=TopNavConfig.FLAG_ASSETS.get(self.current_lang),
            on_press_callback=self._toggle_menu
        )
        self.add_widget(self.current_btn)

        # Меню выбора (скрыто по умолчанию)
        self.menu = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(0),
            spacing=dp(2),
            md_bg_color=[0, 0, 0, 0.8],
            radius=[dp(6)] * 4
        )
        self.menu.opacity = 0
        self.menu.disabled = True

        # Создаём кнопки для каждого языка
        for lang_code in TopNavConfig.LANGUAGES:
            if lang_code != self.current_lang:
                btn = LanguageButton(
                    lang_code=lang_code,
                    flag_asset=TopNavConfig.FLAG_ASSETS.get(lang_code),
                    on_press_callback=self._select_language
                )
                self.menu.add_widget(btn)

        self.add_widget(self.menu)

    def _toggle_menu(self, instance):
        """Открывает/закрывает меню"""
        if self.is_open:
            self._close_menu()
        else:
            self._open_menu()

    def _open_menu(self):
        """Открывает меню"""
        self.is_open = True
        self.menu.height = dp(len(TopNavConfig.LANGUAGES) - 1) * dp(32)
        self.menu.opacity = 1
        self.menu.disabled = False
        anim = Animation(height=dp(60), duration=0.2)
        anim.start(self.menu)

    def _close_menu(self):
        """Закрывает меню"""
        self.is_open = False
        anim = Animation(height=dp(0), duration=0.2)
        anim.start(self.menu)
        self.menu.opacity = 0
        self.menu.disabled = True

    def _select_language(self, lang_code):
        """Выбирает язык"""
        if lang_code == self.current_lang:
            self._close_menu()
            return

        # Обновляем текущий язык
        self.current_lang = lang_code

        # Обновляем текущую кнопку
        self.remove_widget(self.current_btn)
        self.current_btn = LanguageButton(
            lang_code=self.current_lang,
            flag_asset=TopNavConfig.FLAG_ASSETS.get(self.current_lang),
            on_press_callback=self._toggle_menu
        )
        self.add_widget(self.current_btn, index=0)

        self._close_menu()

        # Вызываем callback
        if self.on_language_change:
            self.on_language_change(lang_code)

    def get_current_lang(self):
        """Возвращает текущий язык"""
        return self.current_lang