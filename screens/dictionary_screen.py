# screens/dictionary_screen.py
"""
Экран словаря музыкальных терминов
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.metrics import dp, sp

from config.theme import theme
from config.logger_config import screen_logger
from screens.components.cards import TermCard

logger = screen_logger('Dictionary')


class DictionaryScreen(Screen):
    """Экран со словарём терминов"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'dictionary'

        # Основной контейнер
        main_layout = BoxLayout(orientation='vertical', padding=theme.PADDING)

        # Заголовок
        title = Label(
            text='Словарь терминов',
            font_size=theme.FONT_SIZE_H1,
            bold=True,
            color=theme.TEXT_PRIMARY,
            size_hint=(1, 0.1),
            halign='left'
        )
        title.bind(size=title.setter('text_size'))

        # Поле поиска
        search_box = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.08),
            spacing=theme.PADDING_SMALL
        )

        search_input = TextInput(
            hint_text='🔍 Поиск терминов...',
            size_hint=(1, 1),
            background_color=theme.SURFACE,
            foreground_color=theme.TEXT_PRIMARY,
            cursor_color=theme.PRIMARY,
            padding=[theme.PADDING, theme.PADDING_SMALL],
            multiline=False
        )
        search_input.bind(text=self.on_search)

        search_box.add_widget(search_input)

        # Список терминов
        scroll = ScrollView(size_hint=(1, 0.82))
        self.terms_grid = GridLayout(
            cols=1,
            spacing=theme.PADDING_SMALL,
            size_hint_y=None,
            padding=[0, 0, 0, theme.PADDING]
        )
        self.terms_grid.bind(minimum_height=self.terms_grid.setter('height'))

        # Загружаем тестовые термины
        self.load_test_terms()

        scroll.add_widget(self.terms_grid)

        # Собираем всё вместе
        main_layout.add_widget(title)
        main_layout.add_widget(search_box)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

        logger.info('Экран словаря создан')

    def load_test_terms(self):
        """Загружает тестовые термины"""
        self.all_terms = [
            ('Аккорд', 'Сочетание трёх и более звуков разной высоты'),
            ('Арпеджио', 'Исполнение звуков аккорда последовательно, а не одновременно'),
            ('Баррэ', 'Приём игры, когда указательный палец зажимает несколько струн на одном ладу'),
            ('Бой', 'Способ ритмической игры аккомпанемента на гитаре'),
            ('Гриф', 'Длинная деревянная часть гитары, на которой расположены лады'),
            ('Лад', 'Расстояние между двумя металлическими порожками на грифе'),
            ('Медиатор', 'Тонкая пластинка для защипывания струн'),
            ('Открытая струна', 'Струна, не прижатая к ладам'),
            ('Перебор', 'Последовательное защипывание струн пальцами'),
            ('Табулатура', 'Способ записи музыки, показывающий позиции пальцев на грифе'),
            ('Тремоло', 'Быстрое повторение одного звука'),
            ('Флажолет', 'Приём извлечения обертонного звука'),
        ]

        self.display_terms(self.all_terms)
        logger.debug(f'Загружено {len(self.all_terms)} терминов')

    def display_terms(self, terms):
        """Отображает список терминов"""
        self.terms_grid.clear_widgets()

        for term, definition in terms:
            card = TermCard(term=term, definition=definition)
            card.bind(on_press=lambda x, t=term: self.open_term(t))
            self.terms_grid.add_widget(card)

    def on_search(self, instance, value):
        """Фильтрация терминов при поиске"""
        if not value:
            self.display_terms(self.all_terms)
            return

        search_term = value.lower()
        filtered = [
            (term, definition) for term, definition in self.all_terms
            if search_term in term.lower() or search_term in definition.lower()
        ]

        self.display_terms(filtered)
        logger.debug(f'Поиск: "{value}" - найдено {len(filtered)} терминов')

    def open_term(self, term):
        """Открыть детальный вид термина"""
        logger.info(f'Открываю термин: {term}')
        # TODO: открыть подробное описание термина