# screens/components/cards.py
"""
Современные карточки для отображения контента
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.metrics import dp, sp
from config.theme import theme
from config.logger_config import get_logger

logger = get_logger('UI')


class Card(ButtonBehavior, BoxLayout):
    """Базовая карточка с тенью и скруглением"""

    background_color = ListProperty([1, 1, 1, 1])
    elevation = NumericProperty(2)  # 1-5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(100)
        self.padding = theme.PADDING
        self.spacing = theme.PADDING_SMALL

        # Рисуем фон с тенью
        with self.canvas.before:
            # Тень
            Color(0, 0, 0, 0.1 * self.elevation)
            self.shadow = RoundedRectangle(
                pos=(self.x + dp(2), self.y - dp(2)),
                size=self.size,
                radius=[theme.CORNER_RADIUS]
            )

            # Основной фон
            Color(*self.background_color)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[theme.CORNER_RADIUS]
            )

        self.bind(pos=self.update_rect, size=self.update_rect)
        logger.debug('Создана карточка')

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.shadow.pos = (self.x + dp(2), self.y - dp(2))
        self.shadow.size = self.size

    def on_press(self):
        """Анимация нажатия"""
        self.opacity = 0.8

    def on_release(self):
        self.opacity = 1.0


class SongCard(Card):
    """Карточка песни с названием и исполнителем"""

    song_title = StringProperty('')
    artist = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.height = dp(120)

        # Контейнер для контента
        content = BoxLayout(orientation='vertical', spacing=dp(4))

        # Название песни
        title_label = Label(
            text=self.song_title,
            font_size=theme.FONT_SIZE_H3,
            bold=True,
            color=theme.TEXT_PRIMARY,
            halign='left',
            size_hint_y=0.6
        )
        title_label.bind(size=title_label.setter('text_size'))

        # Исполнитель
        artist_label = Label(
            text=self.artist,
            font_size=theme.FONT_SIZE_BODY,
            color=theme.TEXT_SECONDARY,
            halign='left',
            size_hint_y=0.4
        )
        artist_label.bind(size=artist_label.setter('text_size'))

        content.add_widget(title_label)
        content.add_widget(artist_label)

        self.add_widget(content)

        self.bind(song_title=lambda x, y: setattr(title_label, 'text', y))
        self.bind(artist=lambda x, y: setattr(artist_label, 'text', y))

        logger.debug(f'Создана карточка песни: {self.song_title}')


class ChordCard(Card):
    """Карточка аккорда"""

    chord_name = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.height = dp(100)

        # Контейнер
        content = BoxLayout()

        # Название аккорда крупно
        name_label = Label(
            text=self.chord_name,
            font_size=theme.FONT_SIZE_H1,
            bold=True,
            color=theme.PRIMARY,
            halign='center'
        )
        name_label.bind(size=name_label.setter('text_size'))

        content.add_widget(name_label)
        self.add_widget(content)

        self.bind(chord_name=lambda x, y: setattr(name_label, 'text', y))
        logger.debug(f'Создана карточка аккорда: {self.chord_name}')


class TermCard(Card):
    """Карточка термина"""

    term = StringProperty('')
    definition = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.height = dp(150)

        # Контейнер
        content = BoxLayout(orientation='vertical', spacing=dp(4))

        # Термин
        term_label = Label(
            text=self.term,
            font_size=theme.FONT_SIZE_H3,
            bold=True,
            color=theme.TEXT_PRIMARY,
            halign='left',
            size_hint_y=0.3
        )
        term_label.bind(size=term_label.setter('text_size'))

        # Определение
        def_label = Label(
            text=self.definition,
            font_size=theme.FONT_SIZE_BODY,
            color=theme.TEXT_SECONDARY,
            halign='left',
            size_hint_y=0.7
        )
        def_label.bind(size=def_label.setter('text_size'))

        content.add_widget(term_label)
        content.add_widget(def_label)

        self.add_widget(content)

        self.bind(term=lambda x, y: setattr(term_label, 'text', y))
        self.bind(definition=lambda x, y: setattr(def_label, 'text', y))

        logger.debug(f'Создана карточка термина: {self.term}')