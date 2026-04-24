# screens/songs_screen.py
"""
Экран песен с алфавитной навигацией и поиском (заглушка)
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

from config.theme import theme
from config.logger_config import screen_logger
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
    """Кнопка буквы для сетки"""

    def __init__(self, text, is_active=False, on_press_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.btn_text = text
        self.on_press_callback = on_press_callback
        self.size_hint = (1, 1)
        self.padding = [dp(2), dp(2), dp(2), dp(2)]

        self.main_layout = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(4), dp(4), dp(4), dp(4)]
        )

        # Все кнопки одинакового размера, текст 09 или 0-9
        if text == '09':
            display_text = '0-9'
            font_size = sp(12)
        else:
            display_text = text
            font_size = sp(15)

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
            self.label.text_color = [1, 1, 1, 1]  # Белый цвет для неактивных кнопок
            self.main_layout.md_bg_color = [0, 0, 0, 0]
            self.main_layout.radius = [0, 0, 0, 0]

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def _on_press(self, instance):
        if self.on_press_callback:
            self.on_press_callback(self.btn_text)


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


class AlphabetGrid(MDCard):
    """Сетка с буквами - равномерное распределение по рядам с прозрачным фоном"""

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
        self.height = dp(180)
        self.padding = [dp(0), dp(0), dp(0), dp(0)]
        self.radius = [theme.CORNER_RADIUS_SMALL]

        # Делаем фон полупрозрачным, чуть темнее (20% вместо 15%)
        self.theme_bg_color = "Custom"
        self.md_bg_color = [0, 0, 0, 0.2]  # Чёрный с прозрачностью 20% (темнее)
        self.line_color = [1, 1, 1, 0.1]
        self.line_width = 1
        self.elevation = 2

        self.rows = []
        self.buttons = []

        # Создаём 4 ряда
        for i in range(4):
            row = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(6),
                size_hint_y=None,
                height=dp(40)
            )
            self.rows.append(row)
            self.add_widget(row)

        self.update_display()

    def set_language(self, language):
        """Устанавливает язык клавиатуры"""
        self.current_language = language
        self.current_selected = None
        self.update_display()

    def update_display(self):
        """Обновляет сетку с буквами - равномерное распределение по рядам"""
        # Выбираем набор букв
        if self.current_language == 'ru':
            items = self.RU_LETTERS  # 35 элементов
            rows_count = 5
            self.height = dp(200)
        else:
            items = self.EN_LETTERS  # 28 элементов
            rows_count = 4
            self.height = dp(160)

        # Сначала удаляем старые ряды, если их количество изменилось
        while len(self.rows) > rows_count:
            old_row = self.rows.pop()
            self.remove_widget(old_row)

        # Добавляем новые ряды, если нужно
        while len(self.rows) < rows_count:
            row = MDBoxLayout(
                orientation='horizontal',
                spacing=dp(6),
                size_hint_y=None,
                height=dp(40)
            )
            self.rows.append(row)
            self.add_widget(row)

        # Очищаем все ряды
        for row in self.rows:
            row.clear_widgets()

        self.buttons.clear()

        # Равномерно распределяем по рядам
        total_items = len(items)
        items_per_row = (total_items + rows_count - 1) // rows_count  # Округление вверх

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

            # Добавляем пустые места для выравнивания
            max_per_row = items_per_row
            for _ in range(max_per_row - len(row_items)):
                spacer = MDBoxLayout(size_hint=(1, 1))
                self.rows[row_idx].add_widget(spacer)

    def on_letter_press_callback(self, letter):
        self.current_selected = letter
        for btn in self.buttons:
            btn.set_active(btn.btn_text == letter)
        if self.on_letter_press:
            # Если нажали 09, передаём '0-9' для API
            if letter == '09':
                self.on_letter_press('0-9')
            else:
                self.on_letter_press(letter)

    def clear_selection(self):
        """Снимает выделение со всех букв"""
        self.current_selected = None
        for btn in self.buttons:
            btn.set_active(False)


class SongsScreen(MDScreen):
    """Экран песен с алфавитной навигацией и поиском (заглушка)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'
        self.current_letter = None
        self.bg_image = None

        # Делаем фон экрана прозрачным
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

    def on_text_change(self, instance, value):
        """Показывает/скрывает кнопку очистки при вводе текста"""
        self.clear_search_btn.opacity = 1 if value else 0

    def init_ui(self):
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.widget import Widget

        scroll = ScrollView(size_hint=(1, 1))

        # Основной контейнер
        main_layout = MDBoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(2), dp(12), dp(8)],
            spacing=dp(6),
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # Отступ сверху (чтобы не перекрывать верхние иконки)
        top_spacer = Widget(size_hint_y=None, height=dp(65))
        main_layout.add_widget(top_spacer)

        # Поисковая строка
        self.search_card = MDCard(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(46),
            radius=[dp(24), dp(24), dp(24), dp(24)],
            md_bg_color=[0, 0, 0, 0],
            elevation=0,
            padding=[dp(0), dp(0), dp(0), dp(0)]
        )

        self.search_field = MDTextField(
            hint_text="Поиск исполнителей и песен",
            mode="filled",
            size_hint_x=0.99,
            font_size=dp(46),
            height=dp(48),
            radius=[dp(24), dp(24), dp(24), dp(24)],
            on_text_validate=self.do_search,
            theme_line_color="Custom",
            line_color_normal=[0, 0, 0, 0],
            line_color_focus=[0, 0, 0, 0],
            theme_bg_color="Custom",
            fill_color_normal=[0, 0, 0, 0],
            fill_color_focus=[0, 0, 0, 0],
            text_color_normal=[0, 0, 0, 0],
            text_color_focus=[0, 0, 0, 0],
            hint_text_color=[0.5, 0.5, 0.5, 1]
        )

        # Кнопка очистки
        self.clear_search_btn = MDIconButton(
            icon="close-circle",
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            theme_icon_color="Custom",
            icon_color=theme.TEXT_SECONDARY,
            on_release=self.clear_search,
            opacity=0,
            md_bg_color=[0, 0, 0, 0]
        )

        # Кнопка поиска
        self.search_btn = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_icon_color="Custom",
            icon_color=theme.PRIMARY,
            on_release=self.do_search,
            md_bg_color=[0, 0, 0, 0]
        )

        self.search_card.add_widget(self.search_field)
        self.search_card.add_widget(self.clear_search_btn)
        self.search_card.add_widget(self.search_btn)
        main_layout.add_widget(self.search_card)

        # Выбор языка с иконками и пагинацией
        self.language_selector = LanguageSelector(
            on_language_change=self.on_language_changed
        )
        main_layout.add_widget(self.language_selector)

        # Сетка с буквами (теперь с прозрачным фоном)
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
        logger.info(f"Выбрана буква: {letter}")
        self.current_letter = letter
        self.alphabet_grid.clear_selection()

        # Очищаем поле поиска при выборе буквы
        self.search_field.text = ""
        self.clear_search_btn.opacity = 0

        # Переход на экран исполнителей по букве
        if hasattr(self, 'manager') and self.manager:
            if self.manager.has_screen('artists_by_letter'):
                artists_screen = self.manager.get_screen('artists_by_letter')
                artists_screen.set_letter(letter)
                self.manager.current = 'artists_by_letter'
            else:
                logger.error("Экран artists_by_letter не найден")
                notify.error("Ошибка навигации")

    def do_search(self, instance):
        """Поиск - пока заглушка"""
        query = self.search_field.text.strip()
        if len(query) < 2:
            notify.warning("Введите минимум 2 символа для поиска")
            return

        logger.info(f"🔍 Поиск (заглушка): {query}")
        notify.info(f"Поиск '{query}' будет доступен в следующей версии")

    def clear_search(self, instance):
        """Очищает поле поиска"""
        self.search_field.text = ""
        self.clear_search_btn.opacity = 0