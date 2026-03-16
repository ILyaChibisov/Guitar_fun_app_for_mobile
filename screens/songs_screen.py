# screens/songs_screen.py
"""
Экран со списком песен
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle

from config.theme import theme
from config.logger_config import screen_logger
from screens.components.cards import SongCard

logger = screen_logger('Songs')


class SongsScreen(Screen):
    """Экран со списком всех песен"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'songs'

        # Основной контейнер
        main_layout = BoxLayout(orientation='vertical', padding=theme.PADDING)

        # Заголовок
        title = Label(
            text='Песни',
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
            hint_text='🔍 Поиск песен...',
            size_hint=(1, 1),
            background_color=theme.SURFACE,
            foreground_color=theme.TEXT_PRIMARY,
            cursor_color=theme.PRIMARY,
            padding=[theme.PADDING, theme.PADDING_SMALL],
            multiline=False
        )
        search_input.bind(text=self.on_search)

        search_box.add_widget(search_input)

        # Список песен (скроллируемый)
        scroll = ScrollView(size_hint=(1, 0.82))
        self.songs_grid = GridLayout(
            cols=1,
            spacing=theme.PADDING_SMALL,
            size_hint_y=None,
            padding=[0, 0, 0, theme.PADDING]
        )
        self.songs_grid.bind(minimum_height=self.songs_grid.setter('height'))

        # Загружаем тестовые песни
        self.load_test_songs()

        scroll.add_widget(self.songs_grid)

        # Собираем всё вместе
        main_layout.add_widget(title)
        main_layout.add_widget(search_box)
        main_layout.add_widget(scroll)

        self.add_widget(main_layout)

        logger.info('Экран песен создан')

    def load_test_songs(self):
        """Загружает тестовые данные"""
        self.all_songs = [
            ('Полковник', 'Ария'),
            ('Кукушка', 'Кино'),
            ('Выхода нет', 'Сплин'),
            ('Звезда по имени Солнце', 'Кино'),
            ('Группа крови', 'Кино'),
            ('Восьмиклассница', 'Кино'),
            ('Пачка сигарет', 'Кино'),
            ('Прогулка по воде', 'Nautilus Pompilius'),
            ('Я свободен', 'Кипелов'),
            ('Дурак и молния', 'Сплин'),
            ('Орбит без сахара', 'Сплин'),
            ('Моё сердце', 'Сплин'),
            ('Романс', 'Сплин'),
            ('Танцуй', 'Сплин'),
            ('We Will Rock You', 'Queen'),
            ('Bohemian Rhapsody', 'Queen'),
            ('Nothing Else Matters', 'Metallica'),
            ('Enter Sandman', 'Metallica'),
            ('Stairway to Heaven', 'Led Zeppelin'),
            ('Wish You Were Here', 'Pink Floyd')
        ]

        self.display_songs(self.all_songs)
        logger.debug(f'Загружено {len(self.all_songs)} песен')

    def display_songs(self, songs):
        """Отображает список песен"""
        self.songs_grid.clear_widgets()

        for song, artist in songs:
            card = SongCard(song_title=song, artist=artist)
            card.bind(on_press=lambda x, s=song: self.open_song(s))
            self.songs_grid.add_widget(card)

    def on_search(self, instance, value):
        """Фильтрация песен при поиске"""
        if not value:
            self.display_songs(self.all_songs)
            return

        search_term = value.lower()
        filtered = [
            (song, artist) for song, artist in self.all_songs
            if search_term in song.lower() or search_term in artist.lower()
        ]

        self.display_songs(filtered)
        logger.debug(f'Поиск: "{value}" - найдено {len(filtered)} песен')

    def open_song(self, song_name):
        """Открыть песню"""
        logger.info(f'Открываю песню: {song_name}')
        # TODO: переход на экран текста песни