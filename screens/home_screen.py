# screens/home_screen.py
"""
Главный экран с красивым оформлением
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock

from config.theme import theme
from config.logger_config import screen_logger
from screens.components.buttons import GradientButton, FloatingActionButton
from screens.components.cards import SongCard, ChordCard

logger = screen_logger('Home')


class HomeScreen(Screen):
    """Главный экран с быстрым доступом к функциям"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'home'

        # Основной контейнер
        main_layout = BoxLayout(orientation='vertical', padding=theme.PADDING)

        # Заголовок с приветствием
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.15),
            padding=[0, theme.PADDING, 0, 0]
        )

        welcome = Label(
            text='Добро пожаловать!',
            font_size=theme.FONT_SIZE_H2,
            bold=True,
            color=theme.TEXT_PRIMARY,
            halign='left',
            size_hint_x=0.7
        )
        welcome.bind(size=welcome.setter('text_size'))

        date_label = Label(
            text=self.get_date(),
            font_size=theme.FONT_SIZE_CAPTION,
            color=theme.TEXT_SECONDARY,
            halign='right',
            size_hint_x=0.3
        )
        date_label.bind(size=date_label.setter('text_size'))

        header.add_widget(welcome)
        header.add_widget(date_label)

        # Контент (скроллируемый)
        scroll = ScrollView(size_hint=(1, 0.7))
        content = BoxLayout(orientation='vertical', spacing=theme.PADDING, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Быстрые действия
        quick_actions = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(120),
            spacing=theme.PADDING
        )

        actions = [
            ('🎸', 'Тюнер', 'tuner'),
            ('🎵', 'Песни', 'songs'),
            ('📚', 'Словарь', 'dictionary')
        ]

        for icon, text, screen_name in actions:
            btn = GradientButton(
                text=f'{icon}\n{text}',
                size_hint=(1, 1),
                font_size=theme.FONT_SIZE_CAPTION
            )
            btn.bind(on_press=lambda x, s=screen_name: self.go_to_screen(s))
            quick_actions.add_widget(btn)

        # Популярные песни
        popular_title = Label(
            text='Популярное сегодня',
            font_size=theme.FONT_SIZE_H3,
            bold=True,
            color=theme.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )
        popular_title.bind(size=popular_title.setter('text_size'))

        # Список популярных песен
        popular_songs = [
            ('Полковник', 'Ария'),
            ('Кукушка', 'Кино'),
            ('Выхода нет', 'Сплин')
        ]

        for song, artist in popular_songs:
            card = SongCard(song_title=song, artist=artist)
            card.bind(on_press=lambda x, s=song: self.open_song(s))
            content.add_widget(card)

        # Рекомендуемые аккорды
        chords_title = Label(
            text='Изучите эти аккорды',
            font_size=theme.FONT_SIZE_H3,
            bold=True,
            color=theme.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )
        chords_title.bind(size=chords_title.setter('text_size'))

        content.add_widget(quick_actions)
        content.add_widget(popular_title)
        for song, artist in popular_songs:
            card = SongCard(song_title=song, artist=artist)
            card.bind(on_press=lambda x, s=song: self.open_song(s))
            content.add_widget(card)

        content.add_widget(chords_title)

        # Сетка аккордов
        chords_grid = GridLayout(cols=3, spacing=theme.PADDING_SMALL, size_hint_y=None, height=dp(200))
        for chord in ['C', 'G', 'Am', 'Em', 'F', 'Dm']:
            card = ChordCard(chord_name=chord, size_hint=(1, None), height=dp(80))
            card.bind(on_press=lambda x, c=chord: self.open_chord(c))
            chords_grid.add_widget(card)

        content.add_widget(chords_grid)

        # Добавляем всё на экран
        scroll.add_widget(content)
        main_layout.add_widget(header)
        main_layout.add_widget(scroll)

        # Плавающая кнопка для быстрого доступа к тюнеру
        fab = FloatingActionButton(
            text='🎸',
            pos_hint={'right': 1, 'bottom': 1},
            size_hint=(None, None)
        )
        fab.bind(on_press=lambda x: self.go_to_screen('tuner'))

        # Используем FloatLayout для FAB
        from kivy.uix.floatlayout import FloatLayout
        root = FloatLayout()
        root.add_widget(main_layout)
        root.add_widget(fab)

        self.add_widget(root)

        logger.info('Главный экран создан')

        # Анимация появления
        Clock.schedule_once(self.animate_enter, 0.1)

    def get_date(self):
        """Возвращает текущую дату в красивом формате"""
        from datetime import datetime
        now = datetime.now()
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        return f"{now.day} {months[now.month - 1]}"

    def animate_enter(self, dt):
        """Анимация появления элементов"""
        for child in self.children[0].children:
            if hasattr(child, 'opacity'):
                child.opacity = 0
                anim = Animation(opacity=1, duration=0.5, t='out_quad')
                anim.start(child)

    def go_to_screen(self, screen_name):
        """Переход к другому экрану"""
        logger.info(f'Переход на экран: {screen_name}')
        self.manager.current = screen_name

    def open_song(self, song_name):
        """Открыть песню"""
        logger.info(f'Открываю песню: {song_name}')
        # TODO: реализовать

    def open_chord(self, chord_name):
        """Открыть аккорд"""
        logger.info(f'Открываю аккорд: {chord_name}')
        # TODO: реализовать