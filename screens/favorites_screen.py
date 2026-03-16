# screens/favorites_screen.py
"""
Экран избранного
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.metrics import dp, sp

from config.theme import theme
from config.logger_config import screen_logger
from screens.components.cards import SongCard, ChordCard

logger = screen_logger('Favorites')


class FavoritesScreen(Screen):
    """Экран с избранными элементами"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'favorites'

        # Основной контейнер
        main_layout = BoxLayout(orientation='vertical', padding=theme.PADDING)

        # Заголовок
        title = Label(
            text='Избранное',
            font_size=theme.FONT_SIZE_H1,
            bold=True,
            color=theme.TEXT_PRIMARY,
            size_hint=(1, 0.1),
            halign='left'
        )
        title.bind(size=title.setter('text_size'))

        # Контейнер для содержимого
        content = BoxLayout(orientation='vertical', size_hint=(1, 0.9))

        # Вкладки для разных типов избранного
        tabs = TabbedPanel(
            do_default_tab=False,
            tab_width=dp(150),
            background_color=theme.BACKGROUND
        )

        # Вкладка с песнями
        songs_tab = TabbedPanelHeader(text='Песни')
        songs_tab.content = self.create_songs_tab()

        # Вкладка с аккордами
        chords_tab = TabbedPanelHeader(text='Аккорды')
        chords_tab.content = self.create_chords_tab()

        tabs.add_widget(songs_tab)
        tabs.add_widget(chords_tab)

        content.add_widget(tabs)

        main_layout.add_widget(title)
        main_layout.add_widget(content)

        self.add_widget(main_layout)

        logger.info('Экран избранного создан')

    def create_songs_tab(self):
        """Создаёт вкладку с избранными песнями"""
        layout = BoxLayout(orientation='vertical', padding=theme.PADDING)

        # Список песен
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=theme.PADDING_SMALL, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        # Тестовые избранные песни
        favorite_songs = [
            ('Полковник', 'Ария'),
            ('Кукушка', 'Кино'),
            ('Wish You Were Here', 'Pink Floyd')
        ]

        if favorite_songs:
            for song, artist in favorite_songs:
                card = SongCard(song_title=song, artist=artist)
                card.bind(on_press=lambda x, s=song: self.open_song(s))
                grid.add_widget(card)
        else:
            # Пустое состояние
            empty_label = Label(
                text='😢 Пока нет избранных песен\n\nДобавляйте песни в избранное\nи они появятся здесь',
                font_size=theme.FONT_SIZE_BODY,
                color=theme.TEXT_SECONDARY,
                size_hint_y=None,
                height=dp(200)
            )
            grid.add_widget(empty_label)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        return layout

    def create_chords_tab(self):
        """Создаёт вкладку с избранными аккордами"""
        layout = BoxLayout(orientation='vertical', padding=theme.PADDING)

        # Сетка аккордов
        scroll = ScrollView()
        grid = GridLayout(cols=3, spacing=theme.PADDING_SMALL, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        # Тестовые избранные аккорды
        favorite_chords = ['C', 'G', 'Am', 'Em', 'F']

        if favorite_chords:
            for chord in favorite_chords:
                card = ChordCard(chord_name=chord, size_hint=(1, None), height=dp(100))
                card.bind(on_press=lambda x, c=chord: self.open_chord(c))
                grid.add_widget(card)
        else:
            empty_label = Label(
                text='😢 Пока нет избранных аккордов',
                font_size=theme.FONT_SIZE_BODY,
                color=theme.TEXT_SECONDARY,
                size_hint_y=None,
                height=dp(200)
            )
            grid.add_widget(empty_label)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        return layout

    def open_song(self, song_name):
        """Открыть песню"""
        logger.info(f'Открываю избранную песню: {song_name}')
        # TODO: открыть песню

    def open_chord(self, chord_name):
        """Открыть аккорд"""
        logger.info(f'Открываю избранный аккорд: {chord_name}')
        # TODO: открыть аккорд