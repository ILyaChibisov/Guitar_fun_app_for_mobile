# screens/components/language_selector_dict.py
"""
Выбор языка для словаря - иконки из ассетов
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.core.image import Image as CoreImage
from io import BytesIO

from config.logger_config import get_logger

logger = get_logger('UI')

try:
    from data import load_asset_as_bytes
    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False
    def load_asset_as_bytes(name):
        return None


class LangIconButton(ButtonBehavior, Image):
    """Кнопка-иконка для выбора языка"""

    def __init__(self, lang_code, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.lang_code = lang_code
        self.is_active = is_active
        self.on_press_callback = on_press_callback
        self.size_hint = (None, None)
        self.size = (dp(48), dp(36))
        self.allow_stretch = True
        self.keep_ratio = True

        # Загружаем иконку
        icon_name = 'rus_png' if lang_code == 'ru' else 'eng_png'
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.texture = img.texture
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        self.bind(on_release=self._on_press)
        self.update_style()

    def update_style(self):
        """Обновляет стиль в зависимости от активности"""
        if self.is_active:
            # Активная - рамка зелёная
            self.color = [1, 1, 1, 1]
        else:
            # Неактивная - затемнённая
            self.color = [0.6, 0.6, 0.6, 0.5]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.lang_code)


class DictLanguageSelector(BoxLayout):
    """Выбор языка для словаря - иконки"""

    def __init__(self, on_language_change=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(44)
        self.spacing = dp(12)
        self.padding = [dp(12), dp(4), dp(12), dp(4)]

        self.on_language_change = on_language_change
        self.current_language = 'ru'

        # Кнопка Русский
        self.ru_btn = LangIconButton(
            lang_code='ru',
            is_active=True,
            on_press_callback=self._select_language
        )

        # Кнопка English
        self.en_btn = LangIconButton(
            lang_code='en',
            is_active=False,
            on_press_callback=self._select_language
        )

        self.add_widget(self.ru_btn)
        self.add_widget(self.en_btn)

        # Растягивающийся виджет для центрирования
        self.add_widget(BoxLayout(size_hint_x=1))

    def _select_language(self, lang_code):
        if lang_code == self.current_language:
            return

        self.current_language = lang_code
        self.ru_btn.set_active(lang_code == 'ru')
        self.en_btn.set_active(lang_code == 'en')

        if self.on_language_change:
            self.on_language_change(lang_code)

    def get_current_language(self):
        return self.current_language

    def set_language(self, lang_code):
        if lang_code in ['ru', 'en']:
            self.current_language = lang_code
            self.ru_btn.set_active(lang_code == 'ru')
            self.en_btn.set_active(lang_code == 'en')