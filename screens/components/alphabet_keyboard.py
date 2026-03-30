# screens/components/alphabet_keyboard.py
"""
Максимально компактная клавиатура с буквами (по 5 кнопок в ряду)
"""
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
from kivy.metrics import dp
from kivy.properties import StringProperty
from config.theme import theme


class SuperCompactLetterButton(MDRaisedButton):
    """Супер компактная кнопка буквы"""

    def __init__(self, letter, **kwargs):
        super().__init__(**kwargs)
        self.text = letter
        self.size_hint = (1, 1)
        self.md_bg_color = theme.PRIMARY_LIGHT
        self.theme_text_color = "Custom"
        self.text_color = [1, 1, 1, 1]
        self.font_size = dp(11)
        self.radius = [dp(4)]


class AlphabetKeyboard(MDBoxLayout):
    """Супер компактная клавиатура — по 5 кнопок в ряду"""

    current_language = StringProperty('ru')
    on_letter_press = None

    # Русский алфавит (7 рядов по 5 букв + 1 ряд)
    RUSSIAN_ROWS = [
        ['А', 'Б', 'В', 'Г', 'Д'],
        ['Е', 'Ё', 'Ж', 'З', 'И'],
        ['Й', 'К', 'Л', 'М', 'Н'],
        ['О', 'П', 'Р', 'С', 'Т'],
        ['У', 'Ф', 'Х', 'Ц', 'Ч'],
        ['Ш', 'Щ', 'Ъ', 'Ы', 'Ь'],
        ['Э', 'Ю', 'Я', '0-9', '#']
    ]

    # Английский алфавит (5 рядов по 5-6 букв + 1 ряд)
    ENGLISH_ROWS = [
        ['A', 'B', 'C', 'D', 'E'],
        ['F', 'G', 'H', 'I', 'J'],
        ['K', 'L', 'M', 'N', 'O'],
        ['P', 'Q', 'R', 'S', 'T'],
        ['U', 'V', 'W', 'X', 'Y'],
        ['Z', '0-9', '#']
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(210)  # 7 рядов * 30dp
        self.spacing = dp(2)
        self.padding = [dp(8), dp(2), dp(8), dp(2)]

        self._update_letters()

    def set_language(self, language):
        """Устанавливает язык клавиатуры"""
        self.current_language = language
        self._update_letters()

    def _update_letters(self):
        """Обновляет отображение букв"""
        self.clear_widgets()

        rows = self.RUSSIAN_ROWS if self.current_language == 'ru' else self.ENGLISH_ROWS

        for row in rows:
            row_layout = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(28),
                spacing=dp(4),
                padding=[dp(2), dp(1), dp(2), dp(1)]
            )

            for letter in row:
                btn = SuperCompactLetterButton(letter=letter)
                btn.bind(on_release=lambda x, l=letter: self._on_letter_click(l))
                row_layout.add_widget(btn)

            self.add_widget(row_layout)

    def _on_letter_click(self, letter):
        """Обработчик нажатия на букву"""
        if self.on_letter_press:
            self.on_letter_press(letter)