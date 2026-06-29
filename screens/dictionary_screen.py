# screens/dictionary_screen.py
"""
Экран словаря терминов - с поиском и алфавитной навигацией
"""
import importlib
import pkgutil
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from io import BytesIO
from kivy.uix.floatlayout import FloatLayout

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.properties import StringProperty, ObjectProperty

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from config.system_bars import get_navigation_bar_height
from screens.base_screen import BaseScreen
from utils.notifications import notify

logger = screen_logger('Dictionary')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# ============ ГЛОБАЛЬНАЯ ИКОНКА ============
_shared_dict_icon_texture = None


def init_shared_dict_icon():
    global _shared_dict_icon_texture
    if _shared_dict_icon_texture is not None:
        return _shared_dict_icon_texture

    if HAS_ASSETS:
        try:
            icon_data = load_asset_as_bytes('dictionary_png')
            if icon_data:
                img = CoreImage(BytesIO(icon_data), ext="png")
                _shared_dict_icon_texture = img.texture
                logger.info("✅ Общая иконка словаря загружена")
                return _shared_dict_icon_texture
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки dictionary_png: {e}")
    return None


# ============ КЛАССЫ ============

class LetterButton(ButtonBehavior, MDBoxLayout):
    """Кнопка буквы для сетки"""

    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.padding = [dp(1), dp(1), dp(1), dp(1)]

        self.main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(4), dp(2), dp(4), dp(2)]
        )

        self.label = MDLabel(
            text=text.upper(),
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            bold=True,
            size_hint=(1, 1),
            text_size=(None, None),
            shorten=False
        )
        self.main_layout.add_widget(self.label)
        self.add_widget(self.main_layout)

        self.is_active = is_active
        self.bind(on_release=self._on_press)
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.label.text_color = [1, 1, 1, 1]
            self.main_layout.md_bg_color = [0.46, 0.70, 0.71, 1]
            self.main_layout.radius = [dp(8), dp(8), dp(8), dp(8)]
        else:
            self.label.text_color = [0.9, 0.95, 0.85, 0.9]
            self.main_layout.md_bg_color = [0.08, 0.22, 0.14, 0.6]
            self.main_layout.radius = [dp(6), dp(6), dp(6), dp(6)]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


class AlphabetGrid(MDCard):
    """Сетка с буквами для словаря"""

    RU_LETTERS = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и',
                  'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т',
                  'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь',
                  'э', 'ю', 'я']

    EN_LETTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                  'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                  'u', 'v', 'w', 'x', 'y', 'z']

    def __init__(self, on_letter_press=None, **kwargs):
        super().__init__(**kwargs)
        self.on_letter_press = on_letter_press
        self.current_language = 'ru'
        self.current_selected = None

        self.orientation = 'vertical'
        self.size_hint = (1, None)
        self.padding = [dp(6), dp(6), dp(6), dp(6)]
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0.06, 0.18, 0.12, 0.92]
        self.line_color = [0.9, 0.9, 0.8, 0.15]
        self.line_width = 1
        self.elevation = 0

        self.rows = []
        self.buttons = []

        self._create_all_buttons()
        self._update_height()

    def _create_all_buttons(self):
        max_rows = 4
        for i in range(max_rows):
            row = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(6),
                size_hint_y=None,
                height=dp(34)
            )
            self.rows.append(row)
            self.add_widget(row)

        max_buttons = max(len(self.RU_LETTERS), len(self.EN_LETTERS))
        for i in range(max_buttons):
            btn = LetterButton(
                text="",
                is_active=False,
                on_press_callback=self._on_letter_press
            )
            self.buttons.append(btn)

        self._redistribute_buttons()

    def _redistribute_buttons(self):
        for row in self.rows:
            row.clear_widgets()

        if self.current_language == 'ru':
            items = self.RU_LETTERS
            rows_count = 4
        else:
            items = self.EN_LETTERS
            rows_count = 3

        for i, row in enumerate(self.rows):
            row.height = dp(34) if i < rows_count else 0
            row.opacity = 1 if i < rows_count else 0

        total_items = len(items)
        items_per_row = (total_items + rows_count - 1) // rows_count

        btn_index = 0
        for row_idx in range(rows_count):
            for col_idx in range(items_per_row):
                if btn_index < total_items:
                    btn = self.buttons[btn_index]
                    text = items[btn_index]
                    btn.btn_text = text
                    btn.label.text = text.upper()
                    btn.opacity = 1
                    btn.disabled = False
                    self.rows[row_idx].add_widget(btn)
                    btn_index += 1
                else:
                    spacer = MDBoxLayout(size_hint=(1, 1))
                    self.rows[row_idx].add_widget(spacer)

        for i in range(btn_index, len(self.buttons)):
            self.buttons[i].opacity = 0
            self.buttons[i].disabled = True

        self._update_height()

    def _update_height(self):
        if self.current_language == 'ru':
            self.height = dp(34) * 4 + dp(12)
        else:
            self.height = dp(34) * 3 + dp(12)

    def _on_letter_press(self, letter):
        self.current_selected = letter
        for btn in self.buttons:
            btn.set_active(btn.btn_text == letter)
        if self.on_letter_press:
            self.on_letter_press(letter)

    def set_language(self, language):
        if self.current_language == language:
            return
        self.current_language = language
        self.current_selected = None
        for btn in self.buttons:
            btn.set_active(False)
        self._redistribute_buttons()

    def clear_selection(self):
        self.current_selected = None
        for btn in self.buttons:
            btn.set_active(False)


class GoogleSearchBar(MDCard):
    """Поисковая строка - поиск ТОЛЬКО по нажатию на лупу или Enter"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 0
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)

        self.line_color = [0.46, 0.70, 0.71, 0.4]
        self.line_width = 1.0

        self.search_field = MDTextField(
            hint_text="Поиск обозначений",
            size_hint_x=1,
            font_size=sp(15),
            height=dp(36),
            on_text_validate=self._on_search,
            mode="fill"
        )

        self.search_field.line_color_normal = [0, 0, 0, 0]
        self.search_field.line_color_focus = [0, 0, 0, 0]
        self.search_field.fill_color_normal = [1, 1, 1, 0]
        self.search_field.fill_color_focus = [1, 1, 1, 0]
        self.search_field.hint_text_color = [0.7, 0.7, 0.7, 1]
        self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]

        self.clear_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            theme_icon_color="Custom",
            icon_color=[0.6, 0.6, 0.6, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear,
            opacity=0
        )

        self.search_icon = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_search,
            pos_hint={'center_y': 0.5}
        )

        self.add_widget(self.search_field)
        self.add_widget(self.clear_btn)
        self.add_widget(self.search_icon)

        self.search_field.bind(text=self._on_text_change)

    def _on_text_change(self, instance, text):
        self.clear_btn.opacity = 1 if text else 0
        self.current_query = text

        if not text.strip():
            if self.on_clear:
                self.on_clear()

    def _on_search(self, instance):
        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear(self, instance):
        self.search_field.text = ""
        self.search_field.focus = True
        self.clear_btn.opacity = 0
        if self.on_clear:
            self.on_clear()

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        self.search_field.focus = True


class LanguageSelector(MDBoxLayout):
    """Выбор языка - системные иконки стрелок, текст по центру (как в Songs)"""

    def __init__(self, on_language_change=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(48)
        self.padding = [0, 0, 0, 0]

        self.on_language_change = on_language_change
        self.current_language = 'ru'

        self.languages = [
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'en', 'name': 'English'}
        ]

        # Используем FloatLayout для точного центрирования
        self.float_layout = FloatLayout(size_hint=(1, 1))

        # --- СИСТЕМНЫЕ ИКОНКИ СТРЕЛОК ---
        self.prev_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.prev_language,
            pos_hint={'center_x': 0.35, 'center_y': 0.5}
        )

        self.language_label = MDLabel(
            text="Русский",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint=(None, None),
            width=dp(120),
            height=dp(48),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        self.next_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 0.9],
            md_bg_color=[0, 0, 0, 0],
            on_release=self.next_language,
            pos_hint={'center_x': 0.65, 'center_y': 0.5}
        )

        self.float_layout.add_widget(self.prev_btn)
        self.float_layout.add_widget(self.language_label)
        self.float_layout.add_widget(self.next_btn)

        self.add_widget(self.float_layout)

        self._update_display()

    def _update_display(self):
        for lang in self.languages:
            if lang['code'] == self.current_language:
                self.language_label.text = lang['name']
                break

    def get_current_language(self):
        return self.current_language

    def prev_language(self, instance):
        current_index = 0 if self.current_language == 'ru' else 1
        new_index = (current_index - 1) % len(self.languages)
        self.current_language = self.languages[new_index]['code']
        self._update_display()
        if self.on_language_change:
            self.on_language_change(self.current_language)

    def next_language(self, instance):
        current_index = 0 if self.current_language == 'ru' else 1
        new_index = (current_index + 1) % len(self.languages)
        self.current_language = self.languages[new_index]['code']
        self._update_display()
        if self.on_language_change:
            self.on_language_change(self.current_language)

    def set_language(self, language):
        if self.current_language == language:
            return
        self.current_language = language
        self._update_display()


# ============ RECYCLEVIEW ДЛЯ РЕЗУЛЬТАТОВ ПОИСКА ============

class SearchTermCard(RecycleDataViewBehavior, MDCard):
    """Карточка термина для RecycleView (результаты поиска)"""

    term_name = StringProperty('')
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.padding = [dp(16), dp(10), dp(12), dp(10)]
        self.spacing = dp(12)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False  # Отключаем для производительности
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self.clip = True
        self._build_ui()

    def _build_ui(self):
        # Иконка
        self.icon = Image(
            size_hint=(None, 1),
            width=dp(30),
            allow_stretch=True,
            keep_ratio=True
        )
        if _shared_dict_icon_texture:
            self.icon.texture = _shared_dict_icon_texture
        else:
            self.icon.text = "📖"

        # Текст
        self.term_label = MDLabel(
            font_size=sp(16),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.95],
            bold=True,
            shorten=True,
            shorten_from="right",
            valign="middle",
            size_hint_x=1
        )

        # Стрелка
        arrow = MDLabel(
            text="›",
            font_size=sp(24),
            size_hint_x=None,
            width=dp(28),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.3]
        )

        self.add_widget(self.icon)
        self.add_widget(self.term_label)
        self.add_widget(arrow)

    def refresh_view_attrs(self, rv, index, data):
        self.term_name = data.get('term_name', '')
        self.on_click = data.get('on_click')
        self.term_label.text = self.term_name.capitalize()
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.on_click:
                self.on_click(self.term_name)
            return True
        return super().on_touch_down(touch)


class TermRecycleView(RecycleView):
    """Виртуализированный список терминов для поиска"""

    def __init__(self, on_term_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_term_click = on_term_click
        self.animate_scroll = False
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]
        self.clip = True

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(60)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(60) * 10,
            orientation='vertical',
            spacing=dp(6)
        )
        self.layout_manager.bind(minimum_height=self.layout_manager.setter('height'))
        self.viewclass = 'SearchTermCard'
        self.add_widget(self.layout_manager)

    def set_terms(self, terms, on_click):
        data = []
        for term in terms:
            data.append({
                'term_name': term,
                'on_click': on_click
            })
        self.data = data
        self.refresh_from_data()

    def clear(self):
        self.data = []
        self.refresh_from_data()


# ============ ОСНОВНОЙ ЭКРАН ============

class DictionaryScreen(BaseScreen):
    """Экран словаря с поиском и алфавитной навигацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dictionary'
        self.bg_image = None

        # Данные терминов
        self.all_terms: dict = {}
        self.terms_by_letter: dict = {}
        self.current_letter: str = None
        self.is_search_mode: bool = False
        self.search_results: list = []
        self._last_query: str = ""

        # UI элементы
        self.search_bar = None
        self.language_selector = None
        self.alphabet_grid = None
        self.hint_label = None
        self.search_recycle_view = None
        self._main_layout = None
        self.top_container = None
        self.keyboard_container = None
        self._keyboard_height = 0
        self.cards_container = None
        self.no_results_label = None

        self.init_ui()
        self.load_background()
        self.scan_terms()

        Clock.schedule_once(lambda dt: init_shared_dict_icon(), 0.1)

        logger.info('Экран словаря создан')

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

    def scan_terms(self):
        """Сканирует все модули словаря из папок ru/ и en/"""
        logger.info("📚 Сканирование терминов...")
        self.all_terms.clear()
        self.terms_by_letter.clear()

        try:
            import dicts

            try:
                from dicts.ru import RU_TERMS_BY_LETTER, get_all_ru_terms
                ru_terms = get_all_ru_terms()
                for term_name, term_data in ru_terms.items():
                    if hasattr(term_data, 'to_dict'):
                        self.all_terms[term_name] = term_data.to_dict()
                    else:
                        self.all_terms[term_name] = term_data

                for letter, terms in RU_TERMS_BY_LETTER.items():
                    if terms:
                        for term_name in terms:
                            first_letter = self._get_first_letter(term_name)
                            if first_letter:
                                if first_letter not in self.terms_by_letter:
                                    self.terms_by_letter[first_letter] = []
                                if term_name not in self.terms_by_letter[first_letter]:
                                    self.terms_by_letter[first_letter].append(term_name)

                logger.info(f"✅ Загружено русских терминов: {len(ru_terms)}")
            except ImportError as e:
                logger.error(f"❌ Ошибка загрузки русских терминов: {e}")

            try:
                from dicts.en import EN_TERMS_BY_LETTER, get_all_en_terms
                en_terms = get_all_en_terms()
                for term_name, term_data in en_terms.items():
                    if hasattr(term_data, 'to_dict'):
                        self.all_terms[term_name] = term_data.to_dict()
                    else:
                        self.all_terms[term_name] = term_data

                for letter, terms in EN_TERMS_BY_LETTER.items():
                    if terms:
                        for term_name in terms:
                            first_letter = self._get_first_letter(term_name)
                            if first_letter:
                                if first_letter not in self.terms_by_letter:
                                    self.terms_by_letter[first_letter] = []
                                if term_name not in self.terms_by_letter[first_letter]:
                                    self.terms_by_letter[first_letter].append(term_name)

                logger.info(f"✅ Загружено английских терминов: {len(en_terms)}")
            except ImportError as e:
                logger.error(f"❌ Ошибка загрузки английских терминов: {e}")

        except ImportError as e:
            logger.error(f"❌ Пакет dicts не найден: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка сканирования: {e}")

        self.all_terms = dict(sorted(self.all_terms.items()))

        for letter in self.terms_by_letter:
            self.terms_by_letter[letter].sort()

        logger.info(f"✅ Всего загружено {len(self.all_terms)} терминов, букв: {len(self.terms_by_letter)}")

    def _get_first_letter(self, term_name):
        if not term_name:
            return None
        clean_name = term_name.lstrip('«»"\'')
        if not clean_name:
            return None
        first_char = clean_name[0].lower()
        if ('а' <= first_char <= 'я') or ('a' <= first_char <= 'z'):
            return first_char
        return None

    def init_ui(self):
        """Инициализирует UI с правильными отступами"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        self._main_layout = main_layout

        # Верхний отступ
        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        content_padding = layout_config.get_content_padding()

        # ============ ВЕРХНЯЯ ЧАСТЬ (поиск + клавиатура) ============
        self.top_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            adaptive_height=True,
            padding=[content_padding[0], 0, content_padding[2], 0]
        )

        self.search_bar = GoogleSearchBar(
            on_search=self.do_search,
            on_clear=self._on_clear_search
        )
        self.top_container.add_widget(self.search_bar)
        self.top_container.add_widget(Widget(size_hint_y=None, height=dp(16)))

        # ============ КЛАВИАТУРА ============
        self.keyboard_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            adaptive_height=True,
            spacing=dp(8)
        )

        self.language_selector = LanguageSelector(
            on_language_change=self.on_language_changed
        )
        self.keyboard_container.add_widget(self.language_selector)

        self.alphabet_grid = AlphabetGrid(on_letter_press=self.on_letter_press)
        self.keyboard_container.add_widget(self.alphabet_grid)

        self.hint_label = MDLabel(
            text="Нажмите на букву для просмотра терминов",
            halign="center",
            font_size=sp(13),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4],
            size_hint_y=None,
            height=dp(32)
        )
        self.keyboard_container.add_widget(self.hint_label)

        self.top_container.add_widget(self.keyboard_container)
        main_layout.add_widget(self.top_container)

        # ============ КОНТЕЙНЕР ДЛЯ РЕЗУЛЬТАТОВ ============
        bottom_padding = layout_config.get_bottom_padding()

        self.cards_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[content_padding[0], dp(4), content_padding[2], bottom_padding]
        )
        self.cards_container.clip = True

        # Контейнер для сообщения "ничего не найдено"
        self.no_results_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(16), dp(16), dp(16), dp(16)]
        )
        self.no_results_label = MDLabel(
            text="",
            halign="center",
            font_size=sp(16),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.4],
            size_hint_y=None,
            height=dp(60),
            opacity=0
        )
        self.no_results_container.add_widget(self.no_results_label)

        self.search_recycle_view = TermRecycleView(on_term_click=self.on_term_selected)
        self.search_recycle_view.bar_width = 0
        self.search_recycle_view.bar_color = [0, 0, 0, 0]
        self.search_recycle_view.bar_inactive_color = [0, 0, 0, 0]
        self.search_recycle_view.clip = True

        self.cards_container.add_widget(self.search_recycle_view)
        main_layout.add_widget(self.cards_container)

        self.add_widget(main_layout)

        Clock.schedule_once(self._save_keyboard_height, 0.5)

        logger.info(f"UI словаря построен, bottom_padding={bottom_padding}dp")

    def _save_keyboard_height(self, dt):
        if self.keyboard_container:
            self._keyboard_height = self.keyboard_container.height
            logger.info(f"📏 Высота клавиатуры: {self._keyboard_height}dp")

    def _show_keyboard(self):
        if self.keyboard_container:
            self.keyboard_container.opacity = 1
            self.keyboard_container.disabled = False
            self.keyboard_container.height = self._keyboard_height

    def _hide_keyboard(self):
        if self.keyboard_container:
            self.keyboard_container.opacity = 0
            self.keyboard_container.disabled = True
            self.keyboard_container.height = 0

    def _show_no_results(self, query):
        """Показывает сообщение 'По вашему запросу ничего не найдено'"""
        self.no_results_label.text = f'По вашему запросу "{query}"\nничего не найдено'
        self.no_results_label.opacity = 1
        self.search_recycle_view.clear()

    def _hide_no_results(self):
        self.no_results_label.opacity = 0
        self.no_results_label.text = ""

    def _show_search_results(self):
        """Показывает результаты поиска в RecycleView"""
        self.hint_label.opacity = 0
        self._hide_no_results()

        if not self.search_results:
            self.search_recycle_view.clear()
            return

        self.search_recycle_view.set_terms(self.search_results, self.on_term_selected)

    def _clear_search_results(self):
        self.search_recycle_view.clear()
        self._hide_no_results()
        self.hint_label.text = "Нажмите на букву для просмотра терминов"
        self.hint_label.opacity = 1

    def _on_clear_search(self):
        logger.info("🧹 Очистка поиска (крестик)")
        self.clear_search()
        self._show_keyboard()

    # ============ ОБРАБОТЧИКИ ============

    def on_language_changed(self, language):
        logger.info(f"🔤 Язык изменён на: {language}")
        self.alphabet_grid.set_language(language)
        self.alphabet_grid.clear_selection()
        self.current_letter = None
        self.clear_search()
        self._clear_search_results()
        self._show_keyboard()

    def on_letter_press(self, letter):
        logger.info(f"Выбрана буква: {letter}")
        self.current_letter = letter
        self.alphabet_grid.clear_selection()
        self.clear_search()
        self._clear_search_results()

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('terms_by_letter'):
                terms_screen = self.manager.get_screen('terms_by_letter')
                terms_screen.set_letter(letter, self)
                self.manager.current = 'terms_by_letter'

    def do_search(self, query):
        """Выполняет поиск терминов с приоритетами"""
        logger.info(f"🔍 Поиск: {query}")
        query_lower = query.strip().lower()
        self._last_query = query

        if len(query_lower) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        self.is_search_mode = True
        self.current_letter = None
        self.alphabet_grid.clear_selection()

        self._hide_keyboard()

        # Разбиваем запрос на слова
        query_words = query_lower.split()

        # Результаты с приоритетами
        exact_matches = []
        prefix_matches = []
        contains_matches = []
        word_matches = []

        for term_name, term_data in self.all_terms.items():
            term_lower = term_name.lower()

            # 1. Точное совпадение (высший приоритет)
            if term_lower == query_lower:
                if term_name not in exact_matches:
                    exact_matches.append(term_name)
                continue

            # 2. Начинается с запроса
            if term_lower.startswith(query_lower):
                if term_name not in prefix_matches:
                    prefix_matches.append(term_name)
                continue

            # 3. Содержит запрос как часть слова
            if query_lower in term_lower:
                if term_name not in contains_matches:
                    contains_matches.append(term_name)
                continue

            # 4. Содержит любое слово из запроса
            for word in query_words:
                if len(word) >= 2 and word in term_lower:
                    if term_name not in word_matches:
                        word_matches.append(term_name)
                    break

        # Объединяем результаты с приоритетами
        results = []
        for r in exact_matches:
            if r not in results:
                results.append(r)
        for r in prefix_matches:
            if r not in results:
                results.append(r)
        for r in contains_matches:
            if r not in results:
                results.append(r)
        for r in word_matches:
            if r not in results:
                results.append(r)

        self.search_results = results

        if not self.search_results:
            self._show_no_results(query)
            self.hint_label.opacity = 0
        else:
            self._show_search_results()

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.clear()
        self._clear_search_results()
        self._hide_no_results()

    def on_term_selected(self, term_name):
        logger.info(f"Выбран термин: {term_name}")

        term_data = self.all_terms.get(term_name)
        if not term_data:
            notify.error("Термин не найден")
            return

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('term_detail'):
                term_detail = self.manager.get_screen('term_detail')
                term_detail.set_term(term_name, term_data, self.name)
                self.manager.current = 'term_detail'

    def on_enter(self):
        logger.info("Вход в словарь")
        self._update_top_nav("Словарь")
        self._show_keyboard()
        # Если был поиск и ничего не найдено - показываем сообщение
        if self.is_search_mode and not self.search_results and self._last_query:
            self._show_no_results(self._last_query)

    def _update_top_nav(self, title):
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title(title)
                app.top_nav._show_back_button()
                app.top_nav.back_btn.on_release = self.go_back
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

    def go_back(self, instance=None):
        logger.info("🔙 go_back: возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_leave(self):
        logger.info("Выход из словаря")
        self.clear_search()
        self.current_letter = None
        self.alphabet_grid.clear_selection()