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
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from io import BytesIO

from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.app import MDApp

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
                    text = items[btn_index]  # ← ИСПРАВЛЕНО: btn_index вместо btn_idx
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
    """Поисковая строка как в Songs"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self._search_timer = None

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

        self.search_field.bind(text=self._on_text_change)

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

    def _on_text_change(self, instance, text):
        self.clear_btn.opacity = 1 if text else 0
        self.current_query = text

        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if not text.strip():
            if self.on_clear:
                self.on_clear()
        else:
            self._search_timer = Clock.schedule_once(lambda dt: self._do_search(), 0.3)

    def _do_search(self):
        if self.on_search and self.current_query:
            text = self.current_query.strip()
            if text:
                self.on_search(text)

    def _on_search(self, instance):
        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

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

    def get_text(self):
        return self.search_field.text.strip()

    def set_text(self, text):
        self.search_field.text = text
        self.clear_btn.opacity = 1 if text else 0

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        self.search_field.focus = True


class LanguageSelector(MDBoxLayout):
    """Выбор языка - стрелки из ассетов, текст по центру (как в Songs)"""

    def __init__(self, on_language_change=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = [dp(16), dp(4), dp(16), dp(4)]

        self.on_language_change = on_language_change
        self.current_language = 'ru'

        self.languages = [
            {'code': 'ru', 'name': 'Русский'},
            {'code': 'en', 'name': 'English'}
        ]

        self.prev_btn = self._create_arrow_button('left_arrow_png', '◀')
        self.prev_btn.bind(on_release=self.prev_language)

        self.language_label = MDLabel(
            text="Русский",
            font_size=sp(18),
            halign="center",
            valign="middle",
            size_hint_x=None,
            width=dp(120),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True,
            pos_hint={'center_y': 0.5}
        )

        self.next_btn = self._create_arrow_button('right_arrow_png', '▶')
        self.next_btn.bind(on_release=self.next_language)

        self.center_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            width=dp(200),
            height=dp(48),
            spacing=dp(12),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        self.center_container.add_widget(self.prev_btn)
        self.center_container.add_widget(self.language_label)
        self.center_container.add_widget(self.next_btn)

        self.add_widget(MDBoxLayout(size_hint_x=1))
        self.add_widget(self.center_container)
        self.add_widget(MDBoxLayout(size_hint_x=1))

        self._update_display()

    def _create_arrow_button(self, icon_name, fallback_text):
        from kivy.uix.behaviors import ButtonBehavior
        from kivy.uix.image import Image

        class ArrowButton(ButtonBehavior, Image):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.allow_stretch = True
                self.keep_ratio = True

        btn = ArrowButton(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5}
        )

        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    btn.texture = img.texture
                    return btn
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        btn.text = fallback_text
        return btn

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


class TermCard(MDCard):
    """Карточка термина - невидимая, только текст жирный"""

    def __init__(self, term_name, on_click=None, **kwargs):
        super().__init__(**kwargs)
        self.term_name = term_name
        self.on_click_callback = on_click

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(36)
        self.padding = [dp(8), dp(0), dp(8), dp(0)]
        self.radius = [0, 0, 0, 0]
        self.elevation = 0
        self.ripple_behavior = True
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0]
        self.line_color = [0, 0, 0, 0]
        self.line_width = 1  # ← ИСПРАВЛЕНО: было 0, стало 1

        self.term_label = MDLabel(
            text=term_name.capitalize(),
            font_size=sp(16),
            halign="left",
            valign="middle",
            size_hint_x=1,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.9],
            bold=True
        )

        self.add_widget(self.term_label)
        self.bind(on_release=self._on_click)

    def _on_click(self, instance):
        if self.on_click_callback:
            self.on_click_callback(self.term_name)


class DictionaryScreen(BaseScreen):
    """Экран словаря с поиском и алфавитной навигацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dictionary'
        self.bg_image = None
        self.all_terms = {}
        self.terms_by_letter = {}
        self.current_letter = None
        self.is_search_mode = False
        self.search_results = []

        self.init_ui()
        self.load_background()
        self.scan_terms()

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
        """Сканирует все модули словаря"""
        logger.info("📚 Сканирование терминов...")
        self.all_terms.clear()
        self.terms_by_letter.clear()

        try:
            import dicts
            self._scan_module_recursive(dicts, 'dicts')
        except ImportError as e:
            logger.error(f"❌ Пакет dicts не найден: {e}")
            self._add_test_terms()
        except Exception as e:
            logger.error(f"❌ Ошибка сканирования: {e}")
            self._add_test_terms()

        self.all_terms = dict(sorted(self.all_terms.items()))

        for term_name in self.all_terms:
            first_letter = self._get_first_letter(term_name)
            if first_letter:
                if first_letter not in self.terms_by_letter:
                    self.terms_by_letter[first_letter] = []
                self.terms_by_letter[first_letter].append(term_name)

        for letter in self.terms_by_letter:
            self.terms_by_letter[letter].sort()

        logger.info(f"✅ Загружено {len(self.all_terms)} терминов, букв: {len(self.terms_by_letter)}")

        self._update_display()

    def _add_test_terms(self):
        """Добавляет тестовые термины для отладки"""
        test_terms = {
            "аккорд": {"description": "Одновременное звучание трёх и более звуков, образующих гармоническое созвучие."},
            "арпеджио": {"description": "Способ исполнения аккорда, при котором звуки извлекаются последовательно."},
            "баре": {"description": "Приём игры на гитаре, при котором указательный палец прижимает все струны на одном ладу."},
            "бенд": {"description": "Приём изменения высоты звука путём натяжения струны вверх или вниз."},
            "гамма": {"description": "Последовательность звуков в восходящем или нисходящем порядке."},
            "гриф": {"description": "Длинная часть струнного инструмента, на которой расположены лады."},
            "мелодия": {"description": "Одноголосная музыкальная мысль, выразительная последовательность звуков."},
            "минор": {"description": "Лад, характеризующийся мягким, грустным, задумчивым звучанием."},
            "мажор": {"description": "Лад, характеризующийся ярким, весёлым, светлым звучанием."},
            "ритм": {"description": "Организация музыкальных звуков во времени, последовательность длительностей."},
            "темп": {"description": "Скорость исполнения музыкального произведения."},
            "транспонирование": {"description": "Перенос музыкального произведения в другую тональность."},
            "вступление": {"description": "Начальная часть музыкального произведения, предшествующая основной теме."},
            "вибрато": {"description": "Периодическое изменение высоты звука."},
            "глиссандо": {"description": "Плавный переход между звуками."},
            "легато": {"description": "Плавное, связное исполнение звуков."},
            "акцент": {"description": "Выделение звука или аккорда более сильным звучанием."},
            "альтерация": {"description": "Изменение ступеней лада путём повышения или понижения."},
            "атака": {"description": "Начало звука или фразы, способ извлечения звука."},
            "бас": {"description": "Нижний голос в многоголосной музыке, низкий регистр."},
            "блюз": {"description": "Музыкальный стиль, характеризующийся определённой гармонией и ритмом."},
            "гитара": {"description": "Струнный щипковый музыкальный инструмент."},
            "динамика": {"description": "Сила звучания, громкость музыкального исполнения."},
            "диез": {"description": "Знак повышения звука на полтона."},
            "бемоль": {"description": "Знак понижения звука на полтона."},
        }
        for name, data in test_terms.items():
            self.all_terms[name] = data

    def _scan_module_recursive(self, module, module_path):
        """Рекурсивно сканирует модули"""
        try:
            if hasattr(module, '__path__'):
                for module_info in pkgutil.iter_modules(module.__path__, f"{module_path}."):
                    try:
                        sub_module = importlib.import_module(module_info.name)
                        if hasattr(sub_module, '__path__'):
                            self._scan_module_recursive(sub_module, module_info.name)
                        else:
                            self._load_term_module(sub_module)
                    except Exception as e:
                        logger.error(f"Ошибка импорта {module_info.name}: {e}")
        except Exception as e:
            logger.error(f"Ошибка сканирования {module_path}: {e}")

    def _load_term_module(self, module):
        """Загружает термины из модуля"""
        try:
            if hasattr(module, 'TERMS'):
                terms = module.TERMS
                if isinstance(terms, dict):
                    for term_name, term_data in terms.items():
                        if hasattr(term_data, 'to_dict'):
                            self.all_terms[term_name] = term_data.to_dict()
                        else:
                            self.all_terms[term_name] = term_data
                logger.debug(f"Загружено {len(terms)} терминов из {module.__name__}")
        except Exception as e:
            logger.error(f"Ошибка загрузки модуля {module.__name__}: {e}")

    def _get_first_letter(self, term_name):
        """Возвращает первую букву термина для группировки"""
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
        """Инициализирует UI как в Songs"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)

        top_padding = layout_config.get_top_padding()
        main_layout.add_widget(Widget(size_hint_y=None, height=top_padding))
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(8)))

        content_padding = layout_config.get_content_padding()

        content_wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[content_padding[0], 0, content_padding[2], 0]
        )

        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint_y=None,
            adaptive_height=True
        )
        content.bind(minimum_height=content.setter('height'))

        self.search_bar = GoogleSearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        content.add_widget(self.search_bar)

        self.language_selector = LanguageSelector(
            on_language_change=self.on_language_changed
        )
        content.add_widget(self.language_selector)

        self.alphabet_grid = AlphabetGrid(on_letter_press=self.on_letter_press)
        content.add_widget(self.alphabet_grid)

        self.results_container = MDBoxLayout(
            orientation='vertical',
            spacing=dp(2),
            size_hint_y=None,
            adaptive_height=True,
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )
        content.add_widget(self.results_container)

        nav_bar_height = get_navigation_bar_height()
        bottom_nav_height = dp(60)
        total_bottom = bottom_nav_height + nav_bar_height + dp(16)
        content.add_widget(Widget(size_hint_y=None, height=total_bottom))

        scroll.add_widget(content)
        content_wrapper.add_widget(scroll)
        main_layout.add_widget(content_wrapper)

        self.add_widget(main_layout)

        logger.info(f"UI словаря построен, side_padding={content_padding[0]}dp")

    def _update_display(self):
        """Обновляет отображение терминов"""
        self.results_container.clear_widgets()

        if self.is_search_mode:
            self._show_search_results()
            return

        if self.current_letter and self.current_letter in self.terms_by_letter:
            terms = self.terms_by_letter[self.current_letter]
            for term_name in terms:
                card = TermCard(
                    term_name=term_name,
                    on_click=self.on_term_selected
                )
                self.results_container.add_widget(card)
        else:
            for term_name in sorted(self.all_terms.keys())[:50]:
                card = TermCard(
                    term_name=term_name,
                    on_click=self.on_term_selected
                )
                self.results_container.add_widget(card)

    def _show_search_results(self):
        """Показывает результаты поиска"""
        self.results_container.clear_widgets()

        if not self.search_results:
            no_results = MDLabel(
                text="Ничего не найдено",
                halign="center",
                font_size=sp(14),
                theme_text_color="Custom",
                text_color=[1, 1, 1, 0.4],
                size_hint_y=None,
                height=dp(60)
            )
            self.results_container.add_widget(no_results)
            return

        for term_name in self.search_results:
            card = TermCard(
                term_name=term_name,
                on_click=self.on_term_selected
            )
            self.results_container.add_widget(card)

    # ============ ОБРАБОТЧИКИ ============

    def on_language_changed(self, language):
        logger.info(f"🔤 Язык изменён на: {language}")
        self.alphabet_grid.set_language(language)
        self.alphabet_grid.clear_selection()
        self.current_letter = None
        self.clear_search()
        self._update_display()

    def on_letter_press(self, letter):
        logger.info(f"Выбрана буква: {letter}")
        self.current_letter = letter
        self.alphabet_grid.clear_selection()
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.clear()
        self._update_display()
        self._update_top_nav("Словарь")

    def do_search(self, query):
        """Выполняет поиск терминов - точное совпадение по целому слову"""
        logger.info(f"🔍 Поиск: {query}")
        query_lower = query.strip().lower()

        if len(query_lower) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        self.is_search_mode = True
        self.current_letter = None
        self.alphabet_grid.clear_selection()

        query_words = query_lower.split()
        query_phrases = []
        for i in range(len(query_words)):
            for j in range(i + 1, len(query_words) + 1):
                query_phrases.append(' '.join(query_words[i:j]))

        results = []
        for term_name, term_data in self.all_terms.items():
            term_lower = term_name.lower()

            if term_lower == query_lower:
                results.append(term_name)
                continue

            for phrase in query_phrases:
                if phrase == term_lower:
                    results.append(term_name)
                    break
                if phrase in term_lower:
                    results.append(term_name)
                    break

            description = term_data.get('description', '').lower()
            for word in query_words:
                if word in description:
                    results.append(term_name)
                    break

            synonyms = term_data.get('synonyms', [])
            for syn in synonyms:
                syn_lower = syn.lower()
                for word in query_words:
                    if word in syn_lower:
                        results.append(term_name)
                        break
                if term_name in results:
                    break

        seen = set()
        unique_results = []
        for r in results:
            if r not in seen:
                seen.add(r)
                unique_results.append(r)
        self.search_results = unique_results

        self._show_search_results()

        if not self.search_results:
            notify.info("Ничего не найдено")

        self._update_top_nav("Словарь")

    def clear_search(self):
        """Очищает поиск"""
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.clear()
        self._update_display()

    def on_term_selected(self, term_name):
        """Обработчик выбора термина"""
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

    def _update_top_nav(self, title):
        """Обновляет заголовок в TopNav"""
        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title(title)
                app.top_nav._show_back_button()
                app.top_nav.back_btn.on_release = self.go_back
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

    def go_back(self, instance=None):
        """Возврат на предыдущий экран"""
        logger.info("🔙 go_back: возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'

    def on_enter(self):
        """При входе на экран"""
        logger.info("Вход в словарь")
        self._update_top_nav("Словарь")

    def on_leave(self):
        """При выходе с экрана"""
        logger.info("Выход из словаря")
        self.clear_search()
        self.current_letter = None
        self.alphabet_grid.clear_selection()