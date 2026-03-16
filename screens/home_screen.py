# screens/home_screen.py
"""
Главный экран с красивым оформлением
Светло-бежевый фон, зелёные акценты
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.utils import rgba

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

        # Устанавливаем цвет фона всего экрана (светло-бежевый)
        with self.canvas.before:
            Color(*rgba(theme.BACKGROUND))
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

        # Основной контейнер с отступами
        main_layout = BoxLayout(
            orientation='vertical',
            padding=theme.PADDING,
            spacing=theme.PADDING_SMALL
        )

        # === Заголовок с приветствием ===
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.12),
            spacing=theme.PADDING
        )

        # Текст приветствия
        welcome_text = BoxLayout(
            orientation='vertical',
            size_hint_x=0.7
        )

        welcome = Label(
            text='Добро пожаловать!',
            font_size=theme.FONT_SIZE_H2,
            bold=True,
            color=theme.TEXT_PRIMARY,
            halign='left',
            size_hint_y=0.6,
            valign='bottom'
        )
        welcome.bind(size=welcome.setter('text_size'))

        subtitle = Label(
            text='Готовы играть? 🎸',
            font_size=theme.FONT_SIZE_BODY,
            color=theme.TEXT_SECONDARY,
            halign='left',
            size_hint_y=0.4,
            valign='top'
        )
        subtitle.bind(size=subtitle.setter('text_size'))

        welcome_text.add_widget(welcome)
        welcome_text.add_widget(subtitle)

        # Дата
        date_label = Label(
            text=self.get_date(),
            font_size=theme.FONT_SIZE_CAPTION,
            color=theme.TEXT_HINT,
            halign='right',
            size_hint_x=0.3,
            valign='top'
        )
        date_label.bind(size=date_label.setter('text_size'))

        header.add_widget(welcome_text)
        header.add_widget(date_label)

        # === Контент (скроллируемый) ===
        scroll = ScrollView(
            size_hint=(1, 0.8),
            bar_width=dp(4),
            bar_color=theme.PRIMARY_LIGHT
        )

        content = BoxLayout(
            orientation='vertical',
            spacing=theme.PADDING,
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter('height'))

        # === Быстрые действия (зелёные кнопки) ===
        quick_actions_title = Label(
            text='Быстрые действия',
            font_size=theme.FONT_SIZE_H3,
            bold=True,
            color=theme.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )
        quick_actions_title.bind(size=quick_actions_title.setter('text_size'))
        content.add_widget(quick_actions_title)

        quick_actions = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(100),
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
                font_size=theme.FONT_SIZE_CAPTION,
                background_color=theme.PRIMARY
            )
            btn.bind(on_press=lambda x, s=screen_name: self.go_to_screen(s))
            quick_actions.add_widget(btn)

        content.add_widget(quick_actions)

        # === Разделитель ===
        content.add_widget(Label(
            text='',
            size_hint_y=None,
            height=dp(10)
        ))

        # === Популярные песни ===
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
        content.add_widget(popular_title)

        # Список популярных песен
        popular_songs = [
            ('Полковник', 'Ария'),
            ('Кукушка', 'Кино'),
            ('Выхода нет', 'Сплин'),
            ('Звезда по имени Солнце', 'Кино'),
            ('Группа крови', 'Кино')
        ]

        for song, artist in popular_songs:
            card = SongCard(song_title=song, artist=artist)
            card.bind(on_press=lambda x, s=song: self.open_song(s))
            content.add_widget(card)

        # === Рекомендуемые аккорды (зелёные названия) ===
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
        content.add_widget(chords_title)

        # Сетка аккордов
        chords_grid = GridLayout(
            cols=3,
            spacing=theme.PADDING_SMALL,
            size_hint_y=None,
            height=dp(200)
        )

        basic_chords = ['C', 'G', 'Am', 'Em', 'F', 'Dm']
        for chord in basic_chords:
            card = ChordCard(
                chord_name=chord,
                size_hint=(1, None),
                height=dp(90)
            )
            card.bind(on_press=lambda x, c=chord: self.open_chord(c))
            chords_grid.add_widget(card)

        content.add_widget(chords_grid)

        # === Недавно просмотренные ===
        recent_title = Label(
            text='Недавние',
            font_size=theme.FONT_SIZE_H3,
            bold=True,
            color=theme.TEXT_PRIMARY,
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )
        recent_title.bind(size=recent_title.setter('text_size'))
        content.add_widget(recent_title)

        recent_items = [
            ('Bohemian Rhapsody', 'Queen'),
            ('Nothing Else Matters', 'Metallica'),
            ('Wish You Were Here', 'Pink Floyd')
        ]

        for song, artist in recent_items:
            card = SongCard(song_title=song, artist=artist)
            card.background_color = theme.CARD_BG_ALT  # Чуть другой оттенок
            card.bind(on_press=lambda x, s=song: self.open_song(s))
            content.add_widget(card)

        # Добавляем контент в скролл
        scroll.add_widget(content)

        # Собираем основной макет
        main_layout.add_widget(header)
        main_layout.add_widget(scroll)

        # === Плавающая кнопка (зелёная) для быстрого доступа к тюнеру ===
        fab = FloatingActionButton(
            text='🎸',
            font_size=sp(24),
            pos_hint={'right': 0.95, 'bottom': 0.05},
            size_hint=(None, None),
            size=(dp(60), dp(60))
        )
        fab.bind(on_press=lambda x: self.go_to_screen('tuner'))

        # Используем FloatLayout для FAB
        root = FloatLayout()
        root.add_widget(main_layout)
        root.add_widget(fab)

        self.add_widget(root)

        logger.info('Главный экран создан в бежевых тонах с зелёными акцентами')

        # Анимация появления
        Clock.schedule_once(self.animate_enter, 0.1)

    def update_rect(self, *args):
        """Обновляет фон при изменении размера"""
        self.rect.pos = self.pos
        self.rect.size = self.size

    def get_date(self):
        """Возвращает текущую дату в красивом формате"""
        from datetime import datetime
        now = datetime.now()
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
        return f"{now.day} {months[now.month - 1]}, {days[now.weekday()]}"

    def animate_enter(self, dt):
        """Анимация появления элементов"""
        # Получаем все дочерние элементы и плавно их появляем
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
        # TODO: перейти на экран текста песни
        # Пока просто показываем, что это работает
        from kivy.animation import Animation
        anim = Animation(opacity=0.5, duration=0.1) + Animation(opacity=1, duration=0.1)
        # Здесь можно добавить временное уведомление

    def open_chord(self, chord_name):
        """Открыть аккорд"""
        logger.info(f'Открываю аккорд: {chord_name}')
        # TODO: перейти на экран с аппликатурой
        pass