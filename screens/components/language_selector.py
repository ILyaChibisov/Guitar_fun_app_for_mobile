# screens/components/language_selector.py
"""
Компонент выбора языка - Popup с флагами из ассетов и галочкой из ассета
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp
from kivy.core.image import Image as CoreImage
from io import BytesIO
from kivy.core.window import Window

from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('UI')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


class LanguageSelector(ButtonBehavior, BoxLayout):
    """Выбор языка с Popup окном, флагами и галочкой из ассета"""

    def __init__(self, on_language_change=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (dp(50), dp(32))
        self.on_language_change = on_language_change
        self.current_lang = 'ru'
        self.popup = None

        # Только текст, без иконки
        self.main_text = Label(
            text="RU",
            font_size=sp(12),
            color=[1, 1, 1, 1],
            bold=True,
            size_hint=(1, 1),
            halign='center',
            valign='middle'
        )

        self.add_widget(self.main_text)
        self.bind(on_release=self._open_popup)
        self._create_popup()

    def _create_popup(self):
        """Создаёт Popup с выбором языка, флагами и галочкой"""
        content = BoxLayout(
            orientation='vertical',
            spacing=dp(8),
            padding=dp(12),
            size_hint=(None, None),
            width=dp(200),
            height=dp(130)
        )

        # Кнопка Русский
        ru_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            spacing=dp(15),
            padding=[dp(20), dp(12), dp(20), dp(12)]
        )

        ru_flag = Image(
            size_hint=(None, 1),
            width=dp(28),
            allow_stretch=True,
            keep_ratio=True
        )

        ru_label = Label(
            text="Русский",
            font_size=sp(14),
            color=[1, 1, 1, 1],
            halign='left',
            valign='middle',
            size_hint_x=1
        )

        ru_check = self._create_check_icon()
        ru_check.opacity = 1 if self.current_lang == 'ru' else 0

        ru_box.add_widget(ru_flag)
        ru_box.add_widget(ru_label)
        ru_box.add_widget(ru_check)

        # Загружаем флаг
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('rus_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    ru_flag.texture = img.texture
            except:
                ru_flag.text = "🇷🇺"

        ru_box.bind(on_touch_down=lambda x, touch, code='ru': self._select_language(code) if ru_box.collide_point(
            *touch.pos) else None)

        # Кнопка English
        en_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(52),
            spacing=dp(15),
            padding=[dp(20), dp(12), dp(20), dp(12)]
        )

        en_flag = Image(
            size_hint=(None, 1),
            width=dp(28),
            allow_stretch=True,
            keep_ratio=True
        )

        en_label = Label(
            text="English",
            font_size=sp(14),
            color=[1, 1, 1, 1],
            halign='left',
            valign='middle',
            size_hint_x=1
        )

        en_check = self._create_check_icon()
        en_check.opacity = 1 if self.current_lang == 'en' else 0

        en_box.add_widget(en_flag)
        en_box.add_widget(en_label)
        en_box.add_widget(en_check)

        # Загружаем флаг
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('eng_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    en_flag.texture = img.texture
            except:
                en_flag.text = "🇬🇧"

        en_box.bind(on_touch_down=lambda x, touch, code='en': self._select_language(code) if en_box.collide_point(
            *touch.pos) else None)

        self.ru_check = ru_check
        self.en_check = en_check

        content.add_widget(ru_box)
        content.add_widget(en_box)

        self.popup = Popup(
            title="",
            content=content,
            size_hint=(None, None),
            width=dp(200),
            height=dp(130),
            background_color=[0.08, 0.08, 0.08, 0.95],
            separator_color=[0, 0, 0, 0],
            auto_dismiss=True
        )

    def _create_check_icon(self):
        """Создаёт иконку галочки из ассета или текстовую"""
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes('check_png')
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    return Image(
                        texture=img.texture,
                        size_hint=(None, 1),
                        width=dp(24),
                        allow_stretch=True,
                        keep_ratio=True
                    )
            except Exception as e:
                logger.error(f"Ошибка загрузки галочки: {e}")

        return Label(
            text="✓",
            font_size=sp(16),
            color=theme.PRIMARY,
            size_hint=(None, 1),
            width=dp(24),
            halign='center',
            valign='middle'
        )

    def _open_popup(self, instance):
        """Открывает Popup в правом верхнем углу"""
        if self.popup:
            # Обновляем галочки
            self.ru_check.opacity = 1 if self.current_lang == 'ru' else 0
            self.en_check.opacity = 1 if self.current_lang == 'en' else 0

            # Получаем координаты кнопки
            button_pos = self.to_window(0, 0)
            button_top = button_pos[1] + self.height
            button_right = button_pos[0] + self.width

            # Устанавливаем размер Popup
            self.popup.width = dp(200)
            self.popup.height = dp(160)

            # Позиционируем Popup: привязываем к правому краю кнопки
            popup_x = button_right - self.popup.width
            popup_y = button_top + dp(5)

            # Открываем и устанавливаем позицию
            self.popup.open()
            self.popup.pos = (popup_x, popup_y)

    def _select_language(self, lang_code):
        if lang_code == self.current_lang:
            if self.popup:
                self.popup.dismiss()
            return

        self.current_lang = lang_code
        self.main_text.text = "RU" if lang_code == 'ru' else "EN"

        self.ru_check.opacity = 1 if self.current_lang == 'ru' else 0
        self.en_check.opacity = 1 if self.current_lang == 'en' else 0

        if self.popup:
            self.popup.dismiss()

        if self.on_language_change:
            logger.info(f"🌐 Язык изменён на: {lang_code}")
            self.on_language_change(lang_code)

    def get_current_lang(self):
        return self.current_lang

    def set_current_lang(self, lang_code):
        if lang_code in ['ru', 'en']:
            self.current_lang = lang_code
            self.main_text.text = "RU" if lang_code == 'ru' else "EN"