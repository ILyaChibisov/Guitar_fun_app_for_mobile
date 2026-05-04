# screens/songs_screen.py
"""
Экран песен с алфавитной навигацией и современным поиском
"""
from kivymd.uix.screen import MDScreen
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
from io import BytesIO
from kivy.clock import Clock

from config.theme import theme
from config.logger_config import screen_logger
from api.client import api
from utils.notifications import notify

logger = screen_logger('Songs')

# Попытка импорта ассетов
try:
    from data import load_asset_as_bytes

    HAS_ASSETS = True
except ImportError:
    HAS_ASSETS = False


    def load_asset_as_bytes(name):
        return None


    logger.warning("Модуль data не найден")


# ============ КНОПКА БУКВЫ ============

class LetterButton(ButtonBehavior, MDBoxLayout):
    """Кнопка буквы для сетки - элегантный дизайн"""

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


# ============ СОВРЕМЕННАЯ ПОИСКОВАЯ СТРОКА (ДЛЯ KIVYMD 1.2.0) ============

# ============ СОВРЕМЕННАЯ ПОИСКОВАЯ СТРОКА (ДЛЯ KIVYMD 1.2.0) ============

class GoogleSearchBar(MDCard):
    """Современная поисковая строка без голосового поиска, с лупой справа и аккуратной обводкой"""

    def __init__(self, on_search=None, on_clear=None, **kwargs):
        super().__init__(**kwargs)
        self.on_search = on_search
        self.on_clear = on_clear

        self.orientation = 'horizontal'
        self.size_hint = (1, None)
        self.height = dp(48)
        self.radius = [dp(24), dp(24), dp(24), dp(24)]
        self.md_bg_color = [0.96, 0.96, 0.96, 1]
        self.elevation = 1
        self.padding = [dp(16), dp(6), dp(12), dp(6)]
        self.spacing = dp(8)

        # Тонкая аккуратная обводка
        self.line_color = [0.46, 0.70, 0.71, 0.4]
        self.line_width = 1.0

        # Поле ввода (без подсказки) - используем минимальные параметры
        self.search_field = MDTextField(
            hint_text="",
            size_hint_x=1,
            font_size=sp(15),
            height=dp(36),
            on_text_validate=self._on_search,
            mode="fill"
        )

        # Убираем все линии и фон у поля ввода
        self.search_field.line_color_normal = [0, 0, 0, 0]
        self.search_field.line_color_focus = [0, 0, 0, 0]
        self.search_field.fill_color_normal = [1, 1, 1, 0]
        self.search_field.fill_color_focus = [1, 1, 1, 0]
        self.search_field.hint_text_color = [0.7, 0.7, 0.7, 1]

        # Устанавливаем цвет текста через style
        self.search_field.foreground_color = [0.1, 0.1, 0.1, 1]  # Тёмный текст

        self.search_field.bind(text=self._on_text_change)

        # Кнопка очистки (крестик)
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

        # Кнопка лупы справа
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
        """Показываем/скрываем кнопку очистки при вводе текста"""
        self.clear_btn.opacity = 1 if text else 0

    def _on_search(self, instance):
        """Выполнение поиска"""
        if self.on_search:
            text = self.search_field.text.strip()
            if text:
                self.on_search(text)

    def _on_clear(self, instance):
        """Очистка поля поиска"""
        self.search_field.text = ""
        self.search_field.focus = True
        self.clear_btn.opacity = 0
        if self.on_clear:
            self.on_clear()

    def get_text(self):
        """Получить текст из поля поиска"""
        return self.search_field.text.strip()

    def set_text(self, text):
        """Установить текст в поле поиска"""
        self.search_field.text = text
        self.clear_btn.opacity = 1 if text else 0

    def clear(self):
        """Очистить поле поиска"""
        self.search_field.text = ""
        self.clear_btn.opacity = 0

    def focus(self):
        """Установить фокус на поле поиска"""
        self.search_field.focus = True


# ============ ВЫБОР ЯЗЫКА ============

class LanguageSelector(MDBoxLayout):
    """Выбор языка с пагинацией, иконкой и текстом из ассетов"""

    def __init__(self, on_language_change=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(44)
        self.spacing = dp(6)
        self.padding = [dp(12), dp(2), dp(12), dp(2)]

        self.on_language_change = on_language_change
        self.current_language = 'ru'

        # Только два языка
        self.languages = [
            {'code': 'ru', 'name': 'Русский', 'icon': 'rus_png'},
            {'code': 'en', 'name': 'English', 'icon': 'eng_png'}
        ]

        # Стрелка влево
        self.prev_btn = MDIconButton(
            icon="chevron-left",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color="#FFFFFF",
            on_release=self.prev_language,
            md_bg_color=[0, 0, 0, 0]
        )

        # Контейнер для иконки и текста
        self.content_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            width=dp(100),
            height=dp(32),
            spacing=dp(6),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        # Иконка языка (сначала)
        self.language_icon = Image(
            size_hint=(None, None),
            size=(dp(20), dp(20)),
            pos_hint={'center_y': 0.5},
            allow_stretch=True,
            keep_ratio=True
        )

        # Текст названия языка (потом)
        self.language_label = MDLabel(
            text="Русский",
            font_size=sp(13),
            halign="left",
            valign="middle",
            size_hint_x=0.7,
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],
            bold=True
        )

        self.content_container.add_widget(self.language_icon)
        self.content_container.add_widget(self.language_label)

        # Стрелка вправо
        self.next_btn = MDIconButton(
            icon="chevron-right",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_icon_color="Custom",
            icon_color="#FFFFFF",
            on_release=self.next_language,
            md_bg_color=[0, 0, 0, 0]
        )

        # Растяжка для центрирования
        self.add_widget(MDBoxLayout(size_hint_x=1))
        self.add_widget(self.prev_btn)
        self.add_widget(self.content_container)
        self.add_widget(self.next_btn)
        self.add_widget(MDBoxLayout(size_hint_x=1))

        # Загружаем первую иконку
        self._update_display()

    def _load_icon(self, icon_name):
        """Загружает иконку из ассетов"""
        if HAS_ASSETS:
            try:
                icon_data = load_asset_as_bytes(icon_name)
                if icon_data:
                    img = CoreImage(BytesIO(icon_data), ext="png")
                    self.language_icon.texture = img.texture
                    return True
            except Exception as e:
                logger.error(f"Ошибка загрузки иконки {icon_name}: {e}")

        # Если не загрузилась, показываем эмодзи
        if icon_name == 'rus_png':
            self.language_icon.text = "🇷🇺"
        elif icon_name == 'eng_png':
            self.language_icon.text = "🇬🇧"
        return False

    def _update_display(self):
        """Обновляет отображение текущего языка"""
        for lang in self.languages:
            if lang['code'] == self.current_language:
                self.language_label.text = lang['name']
                self._load_icon(lang['icon'])
                break

    def get_current_language(self):
        return self.current_language

    def prev_language(self, instance):
        """Предыдущий язык"""
        current_index = 0 if self.current_language == 'ru' else 1
        new_index = (current_index - 1) % len(self.languages)
        self.current_language = self.languages[new_index]['code']
        self._update_display()

        if self.on_language_change:
            self.on_language_change(self.current_language)

    def next_language(self, instance):
        """Следующий язык"""
        current_index = 0 if self.current_language == 'ru' else 1
        new_index = (current_index + 1) % len(self.languages)
        self.current_language = self.languages[new_index]['code']
        self._update_display()

        if self.on_language_change:
            self.on_language_change(self.current_language)

    def set_language(self, language):
        """Устанавливает язык программно"""
        for lang in self.languages:
            if lang['code'] == language:
                self.current_language = language
                self._update_display()
                break


# ============ СЕТКА АЛФАВИТА ============

class AlphabetGrid(MDCard):
    """Сетка с буквами - элегантный дизайн для зелёного фона"""

    # Русский алфавит (33 буквы) + символы
    RU_LETTERS = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И',
                  'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т',
                  'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь',
                  'Э', 'Ю', 'Я', '#', '09']

    # Английский алфавит (26 букв) + символы
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
        self.height = dp(170)
        self.padding = [dp(6), dp(6), dp(6), dp(6)]
        self.radius = [dp(16), dp(16), dp(16), dp(16)]

        self.md_bg_color = [0.06, 0.18, 0.12, 0.92]
        self.line_color = [0.9, 0.9, 0.8, 0.15]
        self.line_width = 1
        self.elevation = 3

        self.rows = []
        self.buttons = []

        for i in range(4):
            row = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(6),
                size_hint_y=None,
                height=dp(34)
            )
            self.rows.append(row)
            self.add_widget(row)

        self.update_display()

    def set_language(self, language):
        self.current_language = language
        self.current_selected = None
        self.update_display()

    def update_display(self):
        if self.current_language == 'ru':
            items = self.RU_LETTERS[:]
            rows_count = 5
            self.height = dp(182)
        else:
            items = self.EN_LETTERS[:]
            rows_count = 4
            self.height = dp(148)

        while len(self.rows) > rows_count:
            old_row = self.rows.pop()
            self.remove_widget(old_row)

        while len(self.rows) < rows_count:
            row = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(6),
                size_hint_y=None,
                height=dp(34)
            )
            self.rows.append(row)
            self.add_widget(row)

        for row in self.rows:
            row.clear_widgets()

        self.buttons.clear()

        total_items = len(items)
        items_per_row = (total_items + rows_count - 1) // rows_count

        for row_idx in range(rows_count):
            start_idx = row_idx * items_per_row
            end_idx = min(start_idx + items_per_row, total_items)
            row_items = items[start_idx:end_idx]

            for item in row_items:
                btn = LetterButton(
                    text=item,
                    is_active=(item == self.current_selected),
                    on_press_callback=self.on_letter_press_callback
                )
                self.buttons.append(btn)
                self.rows[row_idx].add_widget(btn)

            max_per_row = items_per_row
            for _ in range(max_per_row - len(row_items)):
                spacer = MDBoxLayout(size_hint=(1, 1))
                self.rows[row_idx].add_widget(spacer)

    def on_letter_press_callback(self, letter):
        self.current_selected = letter
        for btn in self.buttons:
            btn.set_active(btn.btn_text == letter)
        if self.on_letter_press:
            if letter == '09':
                self.on_letter_press('0-9')
            else:
                self.on_letter_press(letter)

    def clear_selection(self):
        self.current_selected = None
        for btn in self.buttons:
            btn.set_active(False)


# ============ ГЛАВНЫЙ ЭКРАН ============

class SongsScreen(MDScreen):
    """Экран песен с алфавитной навигацией и современным поиском"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.bg_image = None

        self.md_bg_color = [0, 0, 0, 0]

        self.init_ui()
        self.load_background()

        logger.info('Экран песен создан')

    def load_background(self):
        """Загружает фоновое изображение"""
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
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.widget import Widget

        scroll = ScrollView(size_hint=(1, 1))

        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(2), dp(12), dp(8)],
            spacing=dp(6),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # Современная поисковая строка
        self.search_bar = GoogleSearchBar(
            on_search=self.do_search,
            on_clear=self.clear_search
        )
        main_layout.add_widget(self.search_bar)

        # Выбор языка
        self.language_selector = LanguageSelector(
            on_language_change=self.on_language_changed
        )
        main_layout.add_widget(self.language_selector)

        # Сетка с буквами
        self.alphabet_grid = AlphabetGrid(on_letter_press=self.on_letter_press)
        main_layout.add_widget(self.alphabet_grid)

        scroll.add_widget(main_layout)
        self.add_widget(scroll)

    def on_language_changed(self, language):
        """Обработчик смены языка"""
        logger.info(f"Язык изменён на: {language}")
        self.alphabet_grid.set_language(language)
        self.alphabet_grid.clear_selection()
        self.current_letter = None

    def on_letter_press(self, letter):
        """Обработчик нажатия на букву - переходим на экран исполнителей"""
        logger.info(f"Выбрана буква/группа: {letter}")
        self.current_letter = letter
        self.alphabet_grid.clear_selection()

        # Очищаем поисковую строку
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
        """Поиск - переход на экран результатов"""
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
        """Очищает поиск"""
        self.alphabet_grid.clear_selection()
        self.current_letter = None