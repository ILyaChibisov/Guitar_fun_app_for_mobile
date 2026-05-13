# screens/songs_screen.py
"""
Экран песен с алфавитной навигацией и современным поиском
"""
import time

from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.clock import Clock
from io import BytesIO

from config.theme import theme
from config.logger_config import screen_logger
from config.layout_config import layout_config
from screens.base_screen import BaseScreen
from api.client import api
from utils.notifications import notify

logger = screen_logger('Songs')

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

        if text == '09':
            display_text = '0-9'
            font_size = sp(10)
        else:
            display_text = text
            font_size = sp(13)

        self.label = MDLabel(
            text=display_text,
            font_size=font_size,
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


class GoogleSearchBar(MDCard):
    """Современная поисковая строка - без тени, с placeholder"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear

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
            hint_text="Поиск",
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
    """Выбор языка - стрелки из ассетов, текст по центру"""

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

        # СОЗДАЁМ КНОПКУ ВЛЕВО из ассета
        self.prev_btn = self._create_arrow_button('left_arrow_png', '◀')
        self.prev_btn.bind(on_release=self.prev_language)

        # Название языка (крупно и жирно)
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

        # СОЗДАЁМ КНОПКУ ВПРАВО из ассета
        self.next_btn = self._create_arrow_button('right_arrow_png', '▶')
        self.next_btn.bind(on_release=self.next_language)

        # Контейнер для центрирования всей группы
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

        # Добавляем растягивающиеся отступы для центрирования
        self.add_widget(MDBoxLayout(size_hint_x=1))
        self.add_widget(self.center_container)
        self.add_widget(MDBoxLayout(size_hint_x=1))

        self._update_display()

    def _create_arrow_button(self, icon_name, fallback_text):
        """Создаёт кнопку со стрелкой из ассета"""
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

        # Загружаем иконку из ассета
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    btn.texture = img.texture
                    return btn
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        # Заглушка - текстовая стрелка
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
        import time
        start = time.time()
        logger.info(f"    🔤 AlphabetGrid.set_language({language}) - НАЧАЛО")

        if self.current_language == language:
            logger.info(f"    ⏱ Язык не изменился, выход")
            return

        self.current_language = language
        self.current_selected = None

        mid = time.time()
        logger.info(f"    ⏱ До update_display: {(mid - start) * 1000:.2f}мс")

        self.update_display()

        end = time.time()
        logger.info(f"    ⏱ AlphabetGrid.set_language() - ВСЕГО: {(end - start) * 1000:.2f}мс")


class AlphabetGrid(MDCard):
    """Сетка с буквами - оптимизированная, сохраняет размеры"""

    RU_LETTERS = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И',
                  'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т',
                  'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь',
                  'Э', 'Ю', 'Я', '#', '09']

    EN_LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                  'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                  'U', 'V', 'W', 'X', 'Y', 'Z', '#', '09']

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

        # СОЗДАЁМ КНОПКИ ОДИН РАЗ
        self._create_all_buttons()

        # Устанавливаем начальную высоту
        self._update_height()

    def _create_all_buttons(self):
        """Создаёт все возможные кнопки один раз"""
        # Создаём строки (максимум 5 для русского)
        for i in range(5):
            row = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(6),
                size_hint_y=None,
                height=dp(34)
            )
            self.rows.append(row)
            self.add_widget(row)

        # Создаём кнопки для максимального количества (русский - 35 букв)
        max_buttons = len(self.RU_LETTERS)
        for i in range(max_buttons):
            btn = LetterButton(
                text="",
                is_active=False,
                on_press_callback=self._on_letter_press
            )
            self.buttons.append(btn)

        # Распределяем кнопки по строкам
        self._redistribute_buttons()

    def _redistribute_buttons(self):
        """Распределяет кнопки по строкам в зависимости от языка"""
        # Очищаем все строки
        for row in self.rows:
            row.clear_widgets()

        # Определяем параметры для текущего языка
        if self.current_language == 'ru':
            items = self.RU_LETTERS
            rows_count = 5
        else:
            items = self.EN_LETTERS
            rows_count = 4

        # Показываем/скрываем строки
        for i, row in enumerate(self.rows):
            row.height = dp(34) if i < rows_count else 0
            row.opacity = 1 if i < rows_count else 0

        # Вычисляем количество кнопок в строке
        total_items = len(items)
        items_per_row = (total_items + rows_count - 1) // rows_count

        # Распределяем кнопки
        btn_index = 0
        for row_idx in range(rows_count):
            for col_idx in range(items_per_row):
                if btn_index < total_items:
                    btn = self.buttons[btn_index]
                    # Обновляем текст кнопки
                    text = items[btn_index]
                    btn.btn_text = text
                    display_text = '0-9' if text == '09' else text
                    btn.label.text = display_text
                    btn.opacity = 1
                    btn.disabled = False
                    self.rows[row_idx].add_widget(btn)
                    btn_index += 1
                else:
                    # Добавляем прозрачный spacer для пустых мест
                    spacer = MDBoxLayout(size_hint=(1, 1))
                    self.rows[row_idx].add_widget(spacer)

        # Скрываем оставшиеся неиспользуемые кнопки
        for i in range(btn_index, len(self.buttons)):
            self.buttons[i].opacity = 0
            self.buttons[i].disabled = True

        self._update_height()

    def _update_height(self):
        """Обновляет высоту карточки в зависимости от языка"""
        if self.current_language == 'ru':
            # Русский: 5 строк + отступы
            self.height = dp(34) * 5 + dp(12)  # 170 + 12 = 182dp
        else:
            # Английский: 4 строки + отступы
            self.height = dp(34) * 4 + dp(12)  # 136 + 12 = 148dp

    def _on_letter_press(self, letter):
        """Обработчик нажатия на букву"""
        self.current_selected = letter
        for btn in self.buttons:
            btn.set_active(btn.btn_text == letter)
        if self.on_letter_press:
            if letter == '09':
                self.on_letter_press('0-9')
            else:
                self.on_letter_press(letter)

    def set_language(self, language):
        """БЫСТРАЯ смена языка - просто перераспределяем кнопки"""
        if self.current_language == language:
            return

        self.current_language = language
        self.current_selected = None

        # Очищаем активное состояние у всех кнопок
        for btn in self.buttons:
            btn.set_active(False)

        # Перераспределяем кнопки (без пересоздания!)
        self._redistribute_buttons()

    def clear_selection(self):
        """Снимает выделение со всех кнопок"""
        self.current_selected = None
        for btn in self.buttons:
            btn.set_active(False)

    def on_letter_press_callback(self, letter):
        """Для совместимости со старым кодом"""
        self._on_letter_press(letter)


class SongsScreen(BaseScreen):
    """Экран песен с алфавитной навигацией"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None

        self.init_ui()

        logger.info('Экран песен создан')

    def init_ui(self):
        # Создаём контейнер с отступами
        scroll = MDScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_color=[1, 1, 1, 0.2],
            bar_width=dp(3)
        )

        # Основной контентный контейнер
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),  # УВЕЛИЧЕНО расстояние
            size_hint_y=None,
            adaptive_height=True,
            padding=[0, dp(60), 0, dp(8)]  # УВЕЛИЧЕН отступ сверху до 60dp
        )
        content.bind(minimum_height=content.setter('height'))

        # Поисковая строка
        self.search_bar = GoogleSearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        content.add_widget(self.search_bar)

        # Выбор языка (все элементы на одной линии)
        self.language_selector = LanguageSelector(
            on_language_change=self.on_language_changed
        )
        content.add_widget(self.language_selector)

        # Сетка букв
        self.alphabet_grid = AlphabetGrid(on_letter_press=self.on_letter_press)
        content.add_widget(self.alphabet_grid)

        scroll.add_widget(content)

        # Используем базовый метод для построения UI с правильными отступами
        self.build_ui(content_widget=scroll)

    def on_language_changed(self, language):
        start = time.time()
        logger.info(f"🔤 Язык изменён на: {language}")

        # Измеряем время set_language
        mid1 = time.time()
        self.alphabet_grid.set_language(language)
        mid2 = time.time()
        logger.info(f"  ⏱ set_language() заняло: {(mid2 - mid1) * 1000:.2f}мс")

        # Измеряем время clear_selection
        mid3 = time.time()
        self.alphabet_grid.clear_selection()
        mid4 = time.time()
        logger.info(f"  ⏱ clear_selection() заняло: {(mid4 - mid3) * 1000:.2f}мс")

        # Устанавливаем current_letter
        self.current_letter = None
        end = time.time()
        logger.info(f"  ⏱ ВСЕГО заняло: {(end - start) * 1000:.2f}мс")

    def on_letter_press(self, letter):
        logger.info(f"Выбрана буква/группа: {letter}")
        self.current_letter = letter
        self.alphabet_grid.clear_selection()
        self.search_bar.clear()

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artists_by_letter'):
                artists_screen = self.manager.get_screen('artists_by_letter')
                artists_screen.set_letter(letter)
                self.manager.current = 'artists_by_letter'
            else:
                logger.error("Экран artists_by_letter не найден")
                notify.error("Ошибка навигации")

    def do_search(self, query):
        if len(query) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        logger.info(f"🔍 Поиск: {query}")

        self.alphabet_grid.clear_selection()
        self.current_letter = None

        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('search_results'):
                search_results_screen = self.manager.get_screen('search_results')
                search_results_screen.do_search(query)
                self.manager.current = 'search_results'
            else:
                logger.error("Экран search_results не найден")
                notify.error("Ошибка навигации")

    def clear_search(self):
        self.alphabet_grid.clear_selection()
        self.current_letter = None