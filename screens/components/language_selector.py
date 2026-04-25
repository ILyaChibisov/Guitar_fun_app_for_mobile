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
        self.size = (dp(55), dp(32))
        self.on_language_change = on_language_change
        self.current_lang = 'ru'
        self.popup = None

        # Флаг на главной кнопке
        self.main_flag = Image(
            size_hint=(None, 1),
            width=dp(22),
            allow_stretch=True,
            keep_ratio=True
        )

        # Текст текущего языка
        self.main_text = Label(
            text="RU",
            font_size=sp(10),
            color=[1, 1, 1, 1],
            bold=True,
            size_hint=(None, 1),
            width=dp(28),
            halign='center',
            valign='middle'
        )

        self.add_widget(self.main_flag)
        self.add_widget(self.main_text)

        self._load_main_flag('ru')
        self.bind(on_release=self._open_popup)
        self._create_popup()

    def _load_main_flag(self, lang_code):
        """Загружает флаг для главной кнопки"""
        flag_name = 'rus_png' if lang_code == 'ru' else 'eng_png'
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(flag_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.main_flag.texture = img.texture
                    return
            except Exception as e:
                logger.error(f"Ошибка загрузки флага: {e}")
        # Fallback на эмодзи
        self.main_flag.text = "🇷🇺" if lang_code == 'ru' else "🇬🇧"

    def _create_popup(self):
        """Создаёт Popup с выбором языка, флагами и галочкой"""
        content = BoxLayout(
            orientation='vertical',
            spacing=dp(2),
            padding=dp(6),
            size_hint=(None, None),
            width=dp(180),
            height=dp(100)
        )

        # Кнопка Русский
        ru_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(44),
            spacing=dp(10),
            padding=[dp(12), dp(8), dp(12), dp(8)]
        )

        ru_flag = Image(
            size_hint=(None, 1),
            width=dp(24),
            allow_stretch=True,
            keep_ratio=True
        )

        ru_label = Label(
            text="Русский",
            font_size=sp(12),
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
            height=dp(44),
            spacing=dp(10),
            padding=[dp(12), dp(8), dp(12), dp(8)]
        )

        en_flag = Image(
            size_hint=(None, 1),
            width=dp(24),
            allow_stretch=True,
            keep_ratio=True
        )

        en_label = Label(
            text="English",
            font_size=sp(12),
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

        # Сохраняем ссылки на галочки для обновления
        self.ru_check = ru_check
        self.en_check = en_check

        content.add_widget(ru_box)
        content.add_widget(en_box)

        self.popup = Popup(
            title="",
            content=content,
            size_hint=(None, None),
            size=(dp(180), dp(100)),
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
                        width=dp(20),
                        allow_stretch=True,
                        keep_ratio=True
                    )
            except Exception as e:
                logger.error(f"Ошибка загрузки галочки: {e}")

        # Fallback на текстовую галочку
        return Label(
            text="✓",
            font_size=sp(14),
            color=theme.PRIMARY,
            size_hint=(None, 1),
            width=dp(20),
            halign='center',
            valign='middle'
        )

    def _open_popup(self, instance):
        """Открывает Popup и обновляет галочки"""
        if self.popup:
            self.ru_check.opacity = 1 if self.current_lang == 'ru' else 0
            self.en_check.opacity = 1 if self.current_lang == 'en' else 0
            self.popup.open()

    def _select_language(self, lang_code):
        """Выбирает язык"""
        if lang_code == self.current_lang:
            if self.popup:
                self.popup.dismiss()
            return

        self.current_lang = lang_code
        self.main_text.text = "RU" if lang_code == 'ru' else "EN"
        self._load_main_flag(lang_code)

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
        """Устанавливает текущий язык программно"""
        if lang_code in ['ru', 'en']:
            self.current_lang = lang_code
            self.main_text.text = "RU" if lang_code == 'ru' else "EN"
            self._load_main_flag(lang_code)