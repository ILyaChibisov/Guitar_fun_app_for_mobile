# screens/chords_screen.py
"""
Экран со списком аккордов
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle

from config.theme import theme
from config.logger_config import screen_logger
from screens.components.cards import ChordCard

logger = screen_logger('Chords')


class ChordsScreen(Screen):
    """Экран с библиотекой аккордов"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'chords'

        # Основной контейнер
        main_layout = BoxLayout(orientation='vertical', padding=theme.PADDING)

        # Заголовок
        title = Label(
            text='Аккорды',
            font_size=theme.FONT_SIZE_H1,
            bold=True,
            color=theme.TEXT_PRIMARY,
            size_hint=(1, 0.1),
            halign='left'
        )
        title.bind(size=title.setter('text_size'))

        # Контейнер для содержимого
        content = BoxLayout(orientation='vertical', size_hint=(1, 0.9))

        # Создаём TabbedPanel для категорий
        tabs = TabbedPanel(
            do_default_tab=False,
            tab_width=dp(100),
            background_color=theme.BACKGROUND
        )

        # Основные аккорды
        main_tab = TabbedPanelHeader(text='Основные')
        main_tab.content = self.create_chord_grid([
            'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
        ])

        # Минорные
        minor_tab = TabbedPanelHeader(text='Минорные')
        minor_tab.content = self.create_chord_grid([
            'Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm'
        ])

        # Септаккорды
        seventh_tab = TabbedPanelHeader(text='Септаккорды')
        seventh_tab.content = self.create_chord_grid([
            'C7', 'D7', 'E7', 'F7', 'G7', 'A7', 'B7',
            'Cm7', 'Dm7', 'Em7', 'Fm7', 'Gm7', 'Am7', 'Bm7'
        ])

        # Добавляем вкладки
        tabs.add_widget(main_tab)
        tabs.add_widget(minor_tab)
        tabs.add_widget(seventh_tab)

        content.add_widget(tabs)

        # Собираем всё вместе
        main_layout.add_widget(title)
        main_layout.add_widget(content)

        self.add_widget(main_layout)

        logger.info('Экран аккордов создан')

    def create_chord_grid(self, chords):
        """Создаёт сетку аккордов для вкладки"""
        grid = GridLayout(
            cols=3,
            spacing=theme.PADDING_SMALL,
            padding=theme.PADDING_SMALL,
            size_hint_y=None
        )
        grid.bind(minimum_height=grid.setter('height'))

        for chord in chords:
            card = ChordCard(chord_name=chord, size_hint=(1, None), height=dp(100))
            card.bind(on_press=lambda x, c=chord: self.open_chord(c))
            grid.add_widget(card)

        # Добавляем скролл
        scroll = ScrollView()
        scroll.add_widget(grid)

        return scroll

    def open_chord(self, chord_name):
        """Открыть детальный вид аккорда"""
        logger.info(f'Открываю аккорд: {chord_name}')
        # TODO: переход на экран с аппликатурой