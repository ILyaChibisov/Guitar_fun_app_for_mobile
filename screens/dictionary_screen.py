# screens/dictionary_screen.py
"""
Экран словаря терминов - с единым меню
ПОИСК | ЛЕЙБЛ | МЕНЮ (БУКВЫ + ЯЗЫК справа) | РЕЗУЛЬТАТЫ
С сохранением состояния и позиции скролла
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
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Line, Rectangle
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
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
from screens.base_screen import BaseScreen
from utils.notifications import notify
from utils.screen_state import screen_state

logger = screen_logger('Dictionary')

try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None

# ============ ГЛОБАЛЬНЫЕ ИКОНКИ - ЗАГРУЖАЕМ СРАЗУ ============
_shared_rus_flag_texture = None
_shared_eng_flag_texture = None


def load_shared_icons_sync():
    """Синхронная загрузка иконок - вызывается ДО создания UI"""
    global _shared_rus_flag_texture, _shared_eng_flag_texture

    if _shared_rus_flag_texture is not None:
        return

    if HAS_ASSETS:
        try:
            # Загружаем русский флаг
            rus_data = load_asset_as_bytes('rus_png')
            if rus_data:
                img = CoreImage(BytesIO(rus_data), ext="png")
                _shared_rus_flag_texture = img.texture
                logger.info("✅ Русский флаг загружен синхронно")
            else:
                logger.warning("⚠️ Русский флаг не найден в ассетах")

            # Загружаем английский флаг
            eng_data = load_asset_as_bytes('eng_png')
            if eng_data:
                img = CoreImage(BytesIO(eng_data), ext="png")
                _shared_eng_flag_texture = img.texture
                logger.info("✅ Английский флаг загружен синхронно")
            else:
                logger.warning("⚠️ Английский флаг не найден в ассетах")

        except Exception as e:
            logger.error(f"Ошибка загрузки иконок: {e}")


# ============ СОВРЕМЕННАЯ ПОИСКОВАЯ СТРОКА ============

class SearchBar(MDCard):
    """Поисковая строка в стиле Google с красивой обводкой"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear
        self.current_query = ""
        self._search_timer = None

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [1, 1, 1, 1]
        self.elevation = 0
        self.padding = [dp(12), dp(4), dp(8), dp(4)]
        self.spacing = dp(4)

        # ============ КРАСИВАЯ ОБВОДКА ============
        self.line_color = [0.1, 0.1, 0.1, 0.3]
        self.line_width = 1.6

        # ============ ПОЛЕ ВВОДА (ПРОЗРАЧНОЕ) ============
        self.search_field = MDTextField(
            hint_text="Поиск терминов",
            size_hint_x=1,
            font_size=sp(15),
            height=dp(42),
            on_text_validate=self._on_search,
            mode="fill"
        )

        self.search_field.line_color_normal = [0, 0, 0, 0]
        self.search_field.line_color_focus = [0, 0, 0, 0]
        self.search_field.fill_color_normal = [1, 1, 1, 0]
        self.search_field.fill_color_focus = [1, 1, 1, 0]
        self.search_field.hint_text_color = [0.6, 0.6, 0.6, 1]
        self.search_field.theme_text_color = "Custom"
        self.search_field.text_color = [0.1, 0.1, 0.1, 1]

        self.search_field.bind(text=self._on_text_change)

        # ============ КНОПКА ОЧИСТКИ ============
        self.clear_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[0.5, 0.5, 0.5, 1],
            md_bg_color=[0, 0, 0, 0],
            on_release=self._on_clear,
            opacity=0,
            disabled=True,
            pos_hint={'center_y': 0.5}
        )

        # ============ ИКОНКА ЛУПЫ ============
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

        # Собираем UI
        self.add_widget(self.search_icon)
        self.add_widget(self.search_field)
        self.add_widget(self.clear_btn)

        # Привязываем фокус для изменения обводки
        self.search_field.bind(focus=self._on_focus)

    def _on_text_change(self, instance, text):
        self.current_query = text
        # Управляем видимостью крестика
        if text.strip():
            self.clear_btn.opacity = 1
            self.clear_btn.disabled = False
        else:
            self.clear_btn.opacity = 0
            self.clear_btn.disabled = True

        if self._search_timer:
            Clock.unschedule(self._search_timer)
            self._search_timer = None

        if not text.strip():
            if self.on_clear:
                self.on_clear()
        else:
            self._search_timer = Clock.schedule_once(lambda dt: self._do_search(), 0.5)

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
        self.clear_btn.opacity = 0
        self.clear_btn.disabled = True
        self.current_query = ""
        if self.on_clear:
            self.on_clear()
        self.search_field.focus = True

    def _on_focus(self, instance, value):
        """Обработчик фокуса - меняет цвет обводки"""
        if value:
            self.line_color = [0.1, 0.1, 0.1, 0.3]
            self.line_width = 1.8
        else:
            self.line_color = [0.1, 0.1, 0.1, 0.3]
            self.line_width = 1.5

    def clear(self):
        self.search_field.text = ""
        self.clear_btn.opacity = 0
        self.clear_btn.disabled = True
        self.current_query = ""

    def focus(self):
        self.search_field.focus = True


# ============ КОМПОНЕНТЫ МЕНЮ ============

class FlagToggle(ButtonBehavior, MDBoxLayout):
    """Кнопка-флаг для переключения языка с подписью (справа)"""

    def __init__(self, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.on_press_callback = on_press
        self.current_language = 'ru'

        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = dp(1)
        self.md_bg_color = [0, 0, 0, 0]

        # Контейнер для флага
        flag_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(28),
            md_bg_color=[0, 0, 0, 0]
        )

        self.flag_image = Image(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )
        flag_container.add_widget(self.flag_image)

        # Подпись
        self.label = MDLabel(
            text="RUS",
            font_size=sp(9),
            halign="center",
            valign="top",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.6],
            bold=True,
            size_hint_y=None,
            height=dp(14)
        )

        self.add_widget(flag_container)
        self.add_widget(self.label)

        # Устанавливаем флаг (иконки уже загружены)
        self._update_flag()

        # Привязываем события
        self.flag_image.bind(on_touch_down=self._on_press)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

    def _on_enter(self, *args):
        self.md_bg_color = [1, 1, 1, 0.05]

    def _on_leave(self, *args):
        self.md_bg_color = [0, 0, 0, 0]

    def _on_press(self, instance, touch):
        if self.collide_point(*touch.pos) and self.on_press_callback:
            self.on_press_callback()
            return True
        return False

    def _update_flag(self):
        if self.current_language == 'ru':
            if _shared_rus_flag_texture:
                self.flag_image.texture = _shared_rus_flag_texture
            else:
                self.flag_image.text = "🇷🇺"
            self.label.text = "RUS"
        else:
            if _shared_eng_flag_texture:
                self.flag_image.texture = _shared_eng_flag_texture
            else:
                self.flag_image.text = "🇬🇧"
            self.label.text = "ENG"

    def set_language(self, language):
        self.current_language = language
        self._update_flag()


class LetterButton(MDBoxLayout):
    """Кнопка буквы в меню (как в аккордах)"""

    def __init__(self, text, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press
        self.is_selected = False

        self.size_hint = (None, 1)
        self.width = dp(32)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]
        self.spacing = 0
        self.md_bg_color = [0, 0, 0, 0]

        # Текст буквы
        self.label = MDLabel(
            text=text.upper(),
            font_size=sp(13),
            halign="center",
            valign="middle",
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.7],
            bold=True,
            size_hint=(1, 1)
        )

        self.add_widget(self.label)

        # Обработчики касаний
        self.bind(on_touch_down=self._on_touch_down)
        self.bind(on_enter=self._on_enter, on_leave=self._on_leave)

        self._update_style()

    def _on_enter(self, *args):
        if not self.is_selected:
            self.md_bg_color = [1, 1, 1, 0.05]
            self.label.text_color = [1, 1, 1, 0.9]

    def _on_leave(self, *args):
        if not self.is_selected:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = [1, 1, 1, 0.7]

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self.on_press_callback:
                self.on_press_callback(self.btn_text)
            return True
        return False

    def set_selected(self, selected):
        self.is_selected = selected
        self._update_style()

    def _update_style(self):
        if self.is_selected:
            self.md_bg_color = [0.0, 0.74, 0.83, 1]
            self.label.text_color = [1, 1, 1, 1]
            self.radius = [dp(6), dp(6), dp(6), dp(6)]
        else:
            self.md_bg_color = [0, 0, 0, 0]
            self.label.text_color = [1, 1, 1, 0.7]
            self.radius = [0, 0, 0, 0]


class AlphabetMenu(MDBoxLayout):
    """Меню с буквами алфавита (скроллится) - слева от флага"""

    RU_LETTERS = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и',
                  'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т',
                  'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь',
                  'э', 'ю', 'я']

    EN_LETTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                  'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                  'u', 'v', 'w', 'x', 'y', 'z']

    def __init__(self, on_letter_press=None, current_language='ru', **kwargs):
        super().__init__(**kwargs)
        self.on_letter_press = on_letter_press
        self.current_language = current_language
        self.current_selection = None

        self.orientation = 'horizontal'
        self.size_hint = (1, 1)
        self.spacing = dp(2)
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.md_bg_color = [0, 0, 0, 0]

        self.scroll = None
        self.container = None
        self.buttons = []

        self._build_ui()

    def _build_ui(self):
        self.scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=0,
            bar_color=[0, 0, 0, 0],
            bar_inactive_color=[0, 0, 0, 0],
            bar_margin=0
        )

        self.container = MDBoxLayout(
            orientation='horizontal',
            size_hint_x=None,
            spacing=dp(3),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )
        self.container.bind(minimum_width=self.container.setter('width'))

        self._populate_items()

        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def _populate_items(self):
        self.container.clear_widgets()
        self.buttons = []

        letters = self.RU_LETTERS if self.current_language == 'ru' else self.EN_LETTERS

        for letter in letters:
            btn = LetterButton(
                text=letter,
                on_press=self._on_letter_press
            )
            if letter == self.current_selection:
                btn.set_selected(True)
            self.buttons.append(btn)
            self.container.add_widget(btn)

        self.container.width = sum(btn.width + dp(3) for btn in self.buttons) + dp(8)

    def _on_letter_press(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)
        if self.on_letter_press:
            self.on_letter_press(letter)

    def set_language(self, language):
        if self.current_language == language and self.buttons:
            return
        self.current_language = language
        self.current_selection = None
        self._populate_items()

    def set_current(self, letter):
        self.current_selection = letter
        for btn in self.buttons:
            btn.set_selected(btn.btn_text == letter)


class DictionaryMenu(MDCard):
    """Единое меню: БУКВЫ (скролл) | ЯЗЫК (флаг с подписью) - флаг справа"""

    def __init__(self,
                 on_language_toggle=None,
                 on_letter_press=None,
                 current_language='ru',
                 **kwargs):
        super().__init__(**kwargs)

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(56)
        self.radius = [dp(16), dp(16), dp(16), dp(16)]
        self.md_bg_color = [0, 0, 0, 0.08]
        self.elevation = 0
        self.line_color = [1, 1, 1, 0.15]
        self.line_width = 0.8
        self.padding = [dp(4), dp(4), dp(4), dp(4)]
        self.spacing = dp(0)

        # 1. БУКВЫ (слева) — занимает всё доступное место
        self.alphabet_menu = AlphabetMenu(
            on_letter_press=on_letter_press,
            current_language=current_language
        )

        # 2. ЯЗЫК (флаг с подписью) - СПРАВА
        self.flag_toggle = FlagToggle(
            on_press=on_language_toggle
        )
        self.flag_toggle.current_language = current_language
        self.flag_toggle._update_flag()

        flag_container = MDBoxLayout(
            size_hint_x=None,
            width=dp(44),
            orientation='vertical'
        )
        flag_container.add_widget(self.flag_toggle)

        # БУКВЫ слева, разделитель, ЯЗЫК справа
        self.add_widget(self.alphabet_menu)
        self.add_widget(self._create_divider())
        self.add_widget(flag_container)

    def _create_divider(self):
        return MDBoxLayout(
            size_hint_x=None,
            width=dp(1),
            md_bg_color=[1, 1, 1, 0.1]
        )

    def set_language(self, language):
        self.flag_toggle.set_language(language)
        self.alphabet_menu.set_language(language)

    def set_current_letter(self, letter):
        self.alphabet_menu.set_current(letter)


# ============ RECYCLEVIEW ДЛЯ РЕЗУЛЬТАТОВ ============

class SearchTermCard(RecycleDataViewBehavior, MDCard):
    """Карточка термина с иконкой из Material Design"""
    term_name = StringProperty('')
    on_click = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(44)
        self.padding = [dp(10), dp(4), dp(10), dp(4)]
        self.spacing = dp(8)
        self.radius = [theme.CORNER_RADIUS_SMALL] * 4
        self.elevation = 0
        self.ripple_behavior = False
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.06]
        self.line_color = [1, 1, 1, 0.05]
        self.line_width = 0.5
        self.clip = True
        self._build_ui()

    def _build_ui(self):
        # Иконка из Material Design
        self.icon = MDIconButton(
            icon="book-open-variant",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color=[0.46, 0.70, 0.71, 1],
            md_bg_color=[0, 0, 0, 0],
            pos_hint={'center_y': 0.5}
        )

        # Текст
        self.term_label = MDLabel(
            font_size=sp(15),
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
            font_size=sp(22),
            size_hint_x=None,
            width=dp(24),
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
    """RecycleView с встроенной прокруткой"""

    def __init__(self, on_term_click=None, **kwargs):
        super().__init__(**kwargs)
        self.on_term_click = on_term_click
        self.animate_scroll = False
        self.size_hint = (1, 1)
        self.clip = True
        self.bar_width = 0
        self.bar_color = [0, 0, 0, 0]
        self.bar_inactive_color = [0, 0, 0, 0]

        self.layout_manager = RecycleBoxLayout(
            default_size=(None, dp(48)),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=dp(48) * 50,
            orientation='vertical',
            spacing=dp(2)
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

    def get_scroll_position(self):
        """Возвращает текущую позицию скролла (0-1)"""
        return self.scroll_y

    def set_scroll_position(self, position):
        """Устанавливает позицию скролла (0-1)"""
        if 0 <= position <= 1:
            self.scroll_y = position


# ============ ОСНОВНОЙ ЭКРАН ============

class DictionaryScreen(BaseScreen):
    """Экран словаря с поиском и меню БУКВЫ | ЯЗЫК справа"""

    RU_LETTERS = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и',
                  'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т',
                  'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь',
                  'э', 'ю', 'я']

    EN_LETTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
                  'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
                  'u', 'v', 'w', 'x', 'y', 'z']

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
        self.current_language: str = 'ru'
        self._saved_scroll_position: float = 1.0  # для сохранения позиции скролла

        # UI элементы
        self.search_bar = None
        self._main_label = None
        self._result_label = None
        self.dictionary_menu = None
        self._hint_timer = None
        self.search_recycle_view = None

        # ============ ЗАГРУЖАЕМ ИКОНКИ СИНХРОННО ПЕРЕД СОЗДАНИЕМ UI ============
        load_shared_icons_sync()

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

    def init_ui(self):
        """Инициализирует UI с RecycleView вместо ScrollView"""
        main_layout = MDBoxLayout(orientation='vertical', spacing=0, size_hint=(1, 1))

        # ============ ЗОНА 1: ВЕРХНИЙ ОТСТУП + ПОИСК + ЛЕЙБЛЫ ============
        top_padding = layout_config.get_top_padding()
        content_padding = layout_config.get_content_padding()
        padding = content_padding

        # Контейнер верхней зоны с фиксированной высотой
        top_zone = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=top_padding + dp(48) + dp(4) + dp(24) + dp(2) + dp(56) + dp(20),
            spacing=0,
            padding=[0, 0, 0, 0]
        )

        # Верхний отступ
        top_zone.add_widget(Widget(size_hint_y=None, height=top_padding))

        # Поиск
        search_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(48),
            padding=[padding[0], 0, padding[2], 0]
        )
        self.search_bar = SearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        search_container.add_widget(self.search_bar)
        top_zone.add_widget(search_container)

        # Отступ после поиска
        top_zone.add_widget(Widget(size_hint_y=None, height=dp(4)))

        # Основной лейбл
        self._main_label = MDLabel(
            text="Поиск по алфавиту",
            font_size=sp(14),
            halign="center",
            size_hint_y=None,
            height=dp(24),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 0.5],
        )
        top_zone.add_widget(self._main_label)

        # Отступ
        top_zone.add_widget(Widget(size_hint_y=None, height=dp(2)))

        # Меню
        menu_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(56),
            md_bg_color=[0, 0, 0, 0],
            padding=[padding[0], 0, padding[2], 0]
        )
        self.dictionary_menu = DictionaryMenu(
            on_language_toggle=self._toggle_language,
            on_letter_press=self.on_letter_press,
            current_language=self.current_language
        )
        menu_container.add_widget(self.dictionary_menu)
        top_zone.add_widget(menu_container)

        # Лейбл с результатами
        self._result_label = MDLabel(
            text="",
            font_size=sp(13),
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Custom",
            text_color=[0.46, 0.70, 0.71, 1],
            opacity=0,
            bold=True
        )
        top_zone.add_widget(self._result_label)

        main_layout.add_widget(top_zone)

        # ============ ЗОНА 2: RECYCLEVIEW С КАРТОЧКАМИ ============
        # Занимает всё оставшееся место
        bottom_padding = layout_config.get_bottom_padding()

        wrapper = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            spacing=0,
            padding=[padding[0], dp(4), padding[2], bottom_padding]
        )

        # Используем RecycleView с встроенной прокруткой
        self.search_recycle_view = TermRecycleView(
            on_term_click=self.on_term_selected
        )
        wrapper.add_widget(self.search_recycle_view)

        main_layout.add_widget(wrapper)

        self.clear_widgets()
        self.add_widget(main_layout)

        logger.info(f"UI словаря построен с RecycleView")

    # ============ УПРАВЛЕНИЕ ============

    def _toggle_language(self):
        """Переключение языка"""
        if self.current_language == 'ru':
            self.current_language = 'en'
            self._show_temporary_hint("Выбран английский язык", 1.2)
        else:
            self.current_language = 'ru'
            self._show_temporary_hint("Выбран русский язык", 1.2)

        self.dictionary_menu.set_language(self.current_language)

        # Сохраняем состояние перед сменой языка
        self.save_current_state()

        self.current_letter = None
        self.clear_search()

        logger.info(f"🔤 Язык изменён на: {self.current_language}")

    def _show_hint(self, text):
        """Показывает подсказку в основном лейбле"""
        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None
        if self._main_label:
            self._main_label.text = text

    def _show_temporary_hint(self, text, duration=1.5):
        """Показывает временную подсказку"""
        if self._main_label:
            self._main_label.text = text
            if hasattr(self, '_hint_timer') and self._hint_timer:
                Clock.unschedule(self._hint_timer)
            self._hint_timer = Clock.schedule_once(lambda dt: self._restore_hint(), duration)

    def _restore_hint(self):
        """Восстанавливает стандартную подсказку"""
        if hasattr(self, '_hint_timer'):
            self._hint_timer = None
        if self.is_search_mode:
            self._main_label.text = "Результаты поиска"
        else:
            self._main_label.text = "Поиск по алфавиту"

    def _show_result_label(self, text):
        """Показывает лейбл с информацией о результатах"""
        if self._result_label:
            self._result_label.text = text
            self._result_label.opacity = 1

    def _hide_result_label(self):
        """Скрывает лейбл с результатами"""
        if self._result_label:
            self._result_label.text = ""
            self._result_label.opacity = 0

    def _show_letter_terms(self, letter):
        """Показывает термины для выбранной буквы"""
        terms = self.terms_by_letter.get(letter, [])
        if terms:
            self.search_recycle_view.set_terms(terms, self.on_term_selected)
            self._show_result_label(f"Термины на букву {letter.upper()}")
        else:
            self.search_recycle_view.clear()
            self._show_result_label(f"Нет терминов на букву {letter.upper()}")

    # ============ ПОИСК ============

    def do_search(self, query):
        logger.info(f"🔍 Поиск: {query}")
        query_lower = query.strip().lower()
        self._last_query = query

        if len(query_lower) < 2:
            self._show_temporary_hint("Введите минимум 2 символа", 1.5)
            return

        self.is_search_mode = True
        self.current_letter = None
        self.dictionary_menu.set_current_letter(None)
        self._show_hint("Результаты поиска")

        query_words = query_lower.split()

        exact_matches = []
        prefix_matches = []
        contains_matches = []
        word_matches = []

        for term_name, term_data in self.all_terms.items():
            term_lower = term_name.lower()

            if term_lower == query_lower:
                if term_name not in exact_matches:
                    exact_matches.append(term_name)
                continue

            if term_lower.startswith(query_lower):
                if term_name not in prefix_matches:
                    prefix_matches.append(term_name)
                continue

            if query_lower in term_lower:
                if term_name not in contains_matches:
                    contains_matches.append(term_name)
                continue

            for word in query_words:
                if len(word) >= 2 and word in term_lower:
                    if term_name not in word_matches:
                        word_matches.append(term_name)
                    break

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
            self.search_recycle_view.clear()
            self._hide_result_label()
            self._show_hint(f'По запросу "{query}" ничего не найдено')
        else:
            self.search_recycle_view.set_terms(self.search_results, self.on_term_selected)
            self._show_result_label(f"Найдено терминов: {len(self.search_results)}")

    def clear_search(self):
        self.is_search_mode = False
        self.search_results = []
        self.search_bar.clear()
        self.search_recycle_view.clear()
        self._last_query = ""
        self._hide_result_label()
        self.current_letter = None
        self.dictionary_menu.set_current_letter(None)
        self._show_hint("Поиск по алфавиту")

    # ============ ОБРАБОТЧИКИ ============

    def on_letter_press(self, letter):
        """Обработчик выбора буквы - показывает термины прямо на экране"""
        logger.info(f"Выбрана буква: {letter}")

        # Сохраняем состояние перед сменой буквы
        self.save_current_state()

        self.current_letter = letter
        self.dictionary_menu.set_current_letter(letter)
        self.is_search_mode = False
        self.search_bar.clear()
        self._last_query = ""

        # Показываем термины для буквы
        self._show_letter_terms(letter)

    def on_term_selected(self, term_name):
        logger.info(f"Выбран термин: {term_name}")

        term_data = self.all_terms.get(term_name)
        if not term_data:
            self._show_temporary_hint("Термин не найден", 1.5)
            return

        # ✅ СОХРАНЯЕМ СОСТОЯНИЕ ПЕРЕД ПЕРЕХОДОМ
        self.save_current_state()

        # ✅ СОХРАНЯЕМ, ЧТО ПРИШЛИ ИЗ dictionary
        screen_state.set_previous_screen('dictionary')

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('term_detail'):
                term_detail = self.manager.get_screen('term_detail')
                term_detail.set_term(term_name, term_data, self.name)
                self.manager.current = 'term_detail'

    # ============ ЗАГРУЗКА ТЕРМИНОВ ============

    def scan_terms(self):
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

    # ============ СОХРАНЕНИЕ СОСТОЯНИЯ ============

    def save_current_state(self):
        """Сохраняет текущее состояние экрана словаря"""
        logger.info("=" * 50)
        logger.info("💾 СОХРАНЕНИЕ СОСТОЯНИЯ DictionaryScreen")

        # Сохраняем позицию скролла
        scroll_position = 1.0
        if self.search_recycle_view:
            scroll_position = self.search_recycle_view.get_scroll_position()
            logger.info(f"📜 Текущая позиция скролла: {scroll_position:.2f}")

        state = {
            'current_letter': self.current_letter,
            'is_search_mode': self.is_search_mode,
            'current_language': self.current_language,
            'search_query': self._last_query,
            'search_results': self.search_results[:50],
            'scroll_position': scroll_position,
        }

        logger.info(f"📦 Сохраняем: letter={state.get('current_letter')}, "
                    f"search_mode={state.get('is_search_mode')}, "
                    f"scroll={state.get('scroll_position', 1.0):.2f}")

        screen_state.save_screen_state('dictionary', state)
        logger.info("=" * 50)

    def restore_state(self):
        """Восстанавливает состояние экрана словаря"""
        logger.info("=" * 50)
        logger.info("📂 ВОССТАНОВЛЕНИЕ СОСТОЯНИЯ DictionaryScreen")

        state = screen_state.get_screen_state('dictionary', max_age=300)

        if not state:
            logger.info("❌ Нет сохранённого состояния")
            logger.info("=" * 50)
            return False

        try:
            logger.info(f"📦 Получено состояние: {list(state.keys())}")

            self.current_letter = state.get('current_letter')
            self.is_search_mode = state.get('is_search_mode', False)
            self.current_language = state.get('current_language', 'ru')
            self._last_query = state.get('search_query', '')
            self.search_results = state.get('search_results', [])
            scroll_position = state.get('scroll_position', 1.0)

            # Восстанавливаем язык
            if self.dictionary_menu:
                self.dictionary_menu.set_language(self.current_language)

            # Восстанавливаем отображение
            if self.is_search_mode and self.search_results:
                # Результаты поиска
                self.search_recycle_view.set_terms(self.search_results, self.on_term_selected)
                self._show_result_label(f"Найдено терминов: {len(self.search_results)}")
                if self._last_query:
                    self._show_hint(f"Результаты поиска: {self._last_query}")
                self._main_label.text = f"Результаты поиска: {self._last_query}"
                logger.info(f"🔍 Восстановлены результаты поиска: {len(self.search_results)} терминов")

            elif self.current_letter:
                # Термины по букве
                terms = self.terms_by_letter.get(self.current_letter, [])
                if terms:
                    self.search_recycle_view.set_terms(terms, self.on_term_selected)
                    self._show_result_label(f"Термины на букву {self.current_letter.upper()}")
                    if self.dictionary_menu:
                        self.dictionary_menu.set_current_letter(self.current_letter)
                    logger.info(f"📖 Восстановлена буква {self.current_letter}: {len(terms)} терминов")
                else:
                    self.search_recycle_view.clear()
                    self._show_result_label(f"Нет терминов на букву {self.current_letter.upper()}")
                    logger.info(f"📖 Буква {self.current_letter} — терминов нет")
            else:
                # Пустое состояние
                self.search_recycle_view.clear()
                self._show_hint("Поиск по алфавиту")
                self._hide_result_label()
                logger.info("📄 Пустое состояние")

            # ============ ВОССТАНАВЛИВАЕМ ПОЗИЦИЮ СКРОЛЛА ============
            def restore_scroll(dt):
                if self.search_recycle_view:
                    self.search_recycle_view.set_scroll_position(scroll_position)
                    logger.info(f"📜 Восстановлена позиция скролла: {scroll_position:.2f}")

            Clock.schedule_once(restore_scroll, 0.1)
            Clock.schedule_once(restore_scroll, 0.2)
            Clock.schedule_once(restore_scroll, 0.3)

            logger.info("✅ Восстановление завершено")
            logger.info("=" * 50)
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка восстановления состояния: {e}")
            import traceback
            traceback.print_exc()
            logger.info("=" * 50)
            return False

    # ============ ЖИЗНЕННЫЙ ЦИКЛ ============

    def on_pre_leave(self):
        """Вызывается перед тем, как экран будет покинут"""
        logger.info("🚪 on_pre_leave: сохранение состояния перед выходом")
        self.save_current_state()
        return super().on_pre_leave()

    def on_enter(self):
        logger.info("🚪 Вход в словарь")

        try:
            app = MDApp.get_running_app()
            if app and hasattr(app, 'top_nav'):
                app.top_nav.set_custom_title("Словарь")
                app.top_nav.back_btn.on_release = self.go_back
        except Exception as e:
            logger.error(f"Ошибка обновления TopNav: {e}")

        # Пробуем восстановить состояние
        restored = self.restore_state()
        logger.info(f"📊 Результат восстановления: {restored}")

        if not restored:
            self._show_hint("Поиск по алфавиту")
            self._hide_result_label()
            self.search_recycle_view.clear()
            self.current_letter = None
            if self.dictionary_menu:
                self.dictionary_menu.set_current_letter(None)
            logger.info("📄 Показано начальное состояние")

    def on_leave(self):
        logger.info("🚪 Выход из словаря")

        # Сохраняем состояние перед выходом
        self.save_current_state()

        self.clear_search()
        self.current_letter = None
        if self.dictionary_menu:
            self.dictionary_menu.set_current_letter(None)

        if hasattr(self, '_hint_timer') and self._hint_timer:
            Clock.unschedule(self._hint_timer)
            self._hint_timer = None

    def go_back(self, instance=None):
        logger.info("🔙 Возврат на home")
        if hasattr(self, 'manager') and self.manager:
            self.manager.current = 'home'